# """阶段 5.1: 流式输出 —— 逐字显示回复"""
import json
import os
import requests

# API_KEY=***
API_KEY = os.environ["ZHIPU_API_KEY"]
URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL = "glm-4-flash"
MAX_ITER = 5
MEMORY_FILE = "memory.json"

def get_weather(city: str) -> str:
    weather = {
        "北京": "晴，25°C",
        "上海": "雨，22°C",
        "深圳": "多云，30°C",
    }
    return weather.get(city, f"未找到 {city} 的天气")

TOOL_FUNCS = {"get_weather": get_weather}
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名"}
                },
                "required": ["city"],
            },
        },
    }
]

def chat_stream(messages: list[dict]) -> dict:
    """stream=True，逐字返回，最后组装成完整消息"""
    resp = requests.post(
        URL,
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"model": MODEL, "messages": messages, "tools": TOOLS, "stream": True},
        timeout=30,
        stream=True,  # requests 库的用法：逐行读响应
    )
    resp.raise_for_status()

    collected = {"role": "assistant", "content": "", "tool_calls": []}
    tool_call_buf = {}  # 因为 tool_calls 是分片到达的

    for line in resp.iter_lines(decode_unicode=True):
        if not line or line == "data: [DONE]":
            continue

        # 去掉 "data: " 前缀
        if line.startswith("data: "):
            line = line[6:]

        try:
            chunk = json.loads(line)
        except json.JSONDecodeError:
            continue

        delta = chunk["choices"][0]["delta"]

        # 逐字打印文本
        if "content" in delta and delta["content"]:
            print(delta["content"], end="", flush=True)

        # 累积 tool_calls（分片到达）
        if "tool_calls" in delta:
            for tc in delta["tool_calls"]:
                idx = tc["index"]
                if idx not in tool_call_buf:
                    tool_call_buf[idx] = {
                        "id": "",
                        "function": {"name": "", "arguments": ""},
                    }
                if "id" in tc:
                    tool_call_buf[idx]["id"] = tc["id"]
                if "function" in tc:
                    if "name" in tc["function"]:
                        tool_call_buf[idx]["function"]["name"] += tc["function"]["name"]
                    if "arguments" in tc["function"]:
                        tool_call_buf[idx]["function"]["arguments"] += tc["function"][
                            "arguments"
                        ]

    # 组装 tool_calls
    if tool_call_buf:
        collected["tool_calls"] = [
            {"id": buf["id"], "type": "function", "function": buf["function"]}
            for buf in tool_call_buf.values()
        ]

    # 清理 content（有 tool_calls 时 content 通常是空的）
    if not collected["content"]:
        del collected["content"]

    return collected

def load_memory() -> list[dict]:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"[记忆] 加载了 {len(data)} 条历史消息")
            return data
    return []

def save_memory(messages: list[dict]) -> None:
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

def run(messages: list[dict], user_input: str) -> str:
    messages.append({"role": "user", "content": user_input})

    for i in range(MAX_ITER):
        msg = chat_stream(messages)
        messages.append(msg)

        if not msg.get("tool_calls"):
            save_memory(messages)
            return ""

        print("\n")  # tool_calls 后面换行
        for call in msg["tool_calls"]:
            fn_name = call["function"]["name"]
            args = json.loads(call["function"]["arguments"])
            print(f"  [{fn_name}({args})]", end=" ")

            func = TOOL_FUNCS.get(fn_name)
            result = func(**args) if func else f"未知工具: {fn_name}"
            print(f"-> {result}")

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": result,
                }
            )

    return "达到最大迭代次数"

if __name__ == "__main__":
    messages = load_memory()
    if not messages:
        messages.append(
            {"role": "system", "content": "你是助手，能用工具就用工具。"}
        )

    print("=" * 50)
    print("输入 'exit' 退出")
    print("=" * 50)

    while True:
        user_input = input("\n你: ").strip()
        if not user_input or user_input == "exit":
            print("Bye!")
            break
        print("助手: ", end="", flush=True)
        reply = run(messages, user_input)
        print()  # 最后换行

