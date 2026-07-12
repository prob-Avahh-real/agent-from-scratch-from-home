"""阶段 4: 长期记忆 —— 跨 session 持久化对话历史"""                                                                 
import json                                                                                                         
import os                                                                                                           
import requests                                                                                                     
                                                                                                                         
API_KEY = os.environ["ZHIPU_API_KEY"]                                                                                                           
URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"                                                       
MODEL = "glm-4-flash"                                                                                               
MAX_ITER = 5                                                                                                        
MEMORY_FILE = "memory.json"  # 存对话历史                                                                           
                                                                                                                         
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
                                                                                                                         
def chat(messages: list[dict]) -> dict:                                                                             
    resp = requests.post(                                                                                           
        URL,                                                                                                        
        headers={"Authorization": f"Bearer {API_KEY}"},                                                             
        json={"model": MODEL, "messages": messages, "tools": TOOLS},                                                
        timeout=30,                                                                                                 
    )                                                                                                               
    resp.raise_for_status()                                                                                         
    return resp.json()["choices"][0]["message"]                                                                     
                                                                                                                         
def load_memory() -> list[dict]:                                                                                    
    """启动时读历史"""                                                                                              
    if os.path.exists(MEMORY_FILE):                                                                                 
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:                                                         
            data = json.load(f)                                                                                     
            print(f"[记忆] 加载了 {len(data)} 条历史消息")                                                          
            return data                                                                                             
    return []                                                                                                       
                                                                                                                         
def save_memory(messages: list[dict]) -> None:                                                                      
    """每次对话后保存"""                                                                                            
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:                                                             
        json.dump(messages, f, ensure_ascii=False, indent=2)                                                        
                                                                                                                         
def run(messages: list[dict], user_input: str) -> str:                                                              
    messages.append({"role": "user", "content": user_input})                                                        
                                                                                                                         
    for i in range(MAX_ITER):                                                                                       
        msg = chat(messages)                                                                                        
        messages.append(msg)                                                                                        
                                                                                                                         
        if not msg.get("tool_calls"):                                                                               
            save_memory(messages)                                                                                   
            return msg["content"]                                                                                   
                                                                                                                         
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
                                                                                                                         
    # 第一句（首次运行）                                                                                            
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
        reply = run(messages, user_input)                                                                           
        print(f"\n助手: {reply}")

