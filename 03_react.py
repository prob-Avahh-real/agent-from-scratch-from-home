"""阶段 3: ReAct 循环 —— 多轮推理 + 多工具"""                                                                       
import json                                                                                                         
import os                                                                                                           
import requests                                                                                                     
                                                                                                                         
API_KEY = os.environ["ZHIPU_API_KEY"]                                                                                        
URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"                                                       
MODEL = "glm-4-flash"                                                                                               
MAX_ITER = 5  # 最多调 5 次工具，防死循环                                                                           

"""=== 工具们 ==="""                                                                                                      
def get_weather(city: str) -> str:                                                                                  
    weather = {                                                                                                     
        "北京": "晴，25°C，适宜出门",                                                                               
        "上海": "雨，22°C，建议带伞",                                                                               
        "深圳": "多云，30°C",                                                                                       
        "杭州": "多云转晴，27°C",                                                                                   
    }                                                                                                               
    return weather.get(city, f"未找到 {city} 的天气")                                                               
                                                                                                                         
def get_time(city: str) -> str:                                                                                     
    times = {                                                                                                       
        "北京": "15:00",                                                                                            
        "上海": "15:00",                                                                                            
        "纽约": "02:00",                                                                                            
        "伦敦": "08:00",                                                                                            
    }                                                                                                               
    return f"{city} 当前时间: {times.get(city, '未知')}"                                                            
                                                                                                                         
TOOL_FUNCS = {                                                                                                      
    "get_weather": get_weather,                                                                                     
    "get_time": get_time,                                                                                           
}                                                                                                                   
                                                                                                                         
TOOLS = [                                                                                                           
    {                                                                                                               
        "type": "function",                                                                                         
        "function": {                                                                                               
            "name": "get_weather",                                                                                  
            "description": "查询指定城市的天气",                                                                    
            "parameters": {                                                                                         
                "type": "object",                                                                                   
                "properties": {                                                                                     
                    "city": {"type": "string", "description": "城市名"},                                            
                },                                                                                                  
                "required": ["city"],                                                                               
            },                                                                                                      
        },                                                                                                          
    },                                                                                                              
    {                                                                                                               
        "type": "function",                                                                                         
        "function": {                                                                                               
            "name": "get_time",                                                                                     
            "description": "查询指定城市当前时间",                                                                  
            "parameters": {                                                                                         
                "type": "object",                                                                                   
                "properties": {                                                                                     
                    "city": {"type": "string", "description": "城市名"},                                            
                },                                                                                                  
                "required": ["city"],                                                                               
            },                                                                                                      
        },                                                                                                          
    },                                                                                                              
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
                                                                                                                         
def run(user_input: str) -> str:                                                                                    
    messages = [                                                                                                    
        {"role": "system", "content": "你是助手，能用工具就用工具。"},                                              
        {"role": "user", "content": user_input},                                                                    
    ]                                                                                                               
                                                                                                                         
    for i in range(MAX_ITER):                                                                                       
        print(f"\n--- 第 {i+1} 轮 ---")                                                                             
        msg = chat(messages)                                                                                        
        messages.append(msg)                                                                                        
                                                                                                                         
        # 没有 tool_calls → 任务结束                                                                                
        if not msg.get("tool_calls"):                                                                               
            print("LLM 直接给出最终答案")                                                                           
            return msg["content"]                                                                                   
                                                                                                                         
        # 执行所有 tool_calls                                                                                       
        for call in msg["tool_calls"]:                                                                              
            fn_name = call["function"]["name"]                                                                      
            args = json.loads(call["function"]["arguments"])                                                        
            print(f"  调用工具: {fn_name}({args})")                                                                 
                                                                                                                         
            func = TOOL_FUNCS.get(fn_name)                                                                          
            if func is None:                                                                                        
                result = f"未知工具: {fn_name}"                                                                     
            else:                                                                                                   
                result = func(**args)                                                                                 
                                                                                                                         
            print(f"  工具结果: {result}")                                                                          
            messages.append(                                                                                        
                {                                                                                                   
                    "role": "tool",                                                                                 
                    "tool_call_id": call["id"],                                                                     
                    "content": result,                                                                              
                }                                                                                                   
            )                                                                                                       
                                                                                                                         
    return "达到最大迭代次数，任务未完成"                                                                           
                                                                                                                         
if __name__ == "__main__":                                                                                                  
    print(run("北京和上海今天哪个更适合出门？顺便告诉我北京现在几点了")) 


