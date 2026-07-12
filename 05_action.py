"""阶段 5: 能动工具 —— agent 能读文件、写文件、执行命令"""
import json
import os
import subprocess
import requests

API_KEY=os.environ["ZHIPU_API_KEY"]
URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL = "glm-4-flash"
MAX_ITER = 8
MEMORY_FILE = "memory.json"

# === 沙箱：限制 agent 只能动 sandbox/ 目录 ===
SANDBOX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sandbox")
os.makedirs(SANDBOX, exist_ok=True)

# === 工具：读文件 ===
def read_file(path: str) -> str:
    full = os.path.join(SANDBOX, path)
    if not os.path.exists(full):
        return f"文件不存在: {path}"
    try:
        with open(full, "r", encoding="utf-8") as f:
            return f.read()[:2000]  # 限制长度，避免爆 token
    except Exception as e:
        return f"读取失败: {e}"

# === 工具：写文件（需确认）===
def write_file(path: str, content: str) -> str:
    full = os.path.join(SANDBOX, path)
    print(f"\n⚠️  即将写入: {full}")
    print(f"   内容预览: {content[:200]}")
    if input("   确认? (y/N): ").strip().lower() != "y":
        return "用户拒绝写入"
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return f"已写入 {path}（{len(content)} 字）"

# === 工具：执行 shell 命令（需确认）===
def run_command(cmd: str) -> str:
    print(f"\n⚠️  即将执行命令: {cmd}")
    if input("   确认? (y/N): ").strip().lower() != "y":
        return "用户拒绝执行"
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=10
        )
        out = (result.stdout + result.stderr).strip()
        return out[:2000] if out else f"命令已执行（退出码 {result.returncode}）"
    except subprocess.TimeoutExpired:
        return "命令超时（10s）"
    except Exception as e:
        return f"执行失败: {e}"

TOOL_FUNCS = {
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取 sandbox 目录下的文件内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "相对路径"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "写入文件到 sandbox 目录（会询问用户确认）",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "相对路径"},
                    "content": {"type": "string", "description": "文件内容"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "执行 shell 命令（会询问用户确认）",
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd": {"type": "string", "description": "shell 命令"}
                },
                "required": ["cmd"],
            },
        },
    },
]

def chat(messages):
    resp = requests.post(
        URL,
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"model": MODEL, "messages": messages, "tools": TOOLS},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_memory(messages):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

def run(messages, user_input):
    messages.append({"role": "user", "content": user_input})

    for i in range(MAX_ITER):
        msg = chat(messages)
        messages.append(msg)

        if not msg.get("tool_calls"):
            save_memory(messages)
            return msg["content"]

        for call in msg["tool_calls"]:
            fn = call["function"]["name"]
            args = json.loads(call["function"]["arguments"])
            func = TOOL_FUNCS.get(fn)
            result = func(**args) if func else f"未知工具: {fn}"
            messages.append(
                {"role": "tool", "tool_call_id": call["id"], "content": result}
            )

    return "达到最大迭代次数"

if __name__ == "__main__":
    messages = load_memory()
    if not messages:
        messages.append(
            {"role": "system", "content": "你是助手，能用工具就用。危险操作前会等用户确认。"}
        )

    print(f"沙箱目录: {SANDBOX}\n输入 'exit' 退出\n")

    while True:
        u = input("你: ").strip()
        if not u or u == "exit":
            break
        print(f"\n助手: {run(messages, u)}")
