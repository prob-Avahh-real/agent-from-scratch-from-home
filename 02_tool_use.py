"""阶段 2: Tool use —— LLM 能调用 Python 函数"""                                                                    
import json                                                                                                         
import os                                                                                                           
import requests                                                                                                     
                                                                                                                         
API_KEY = os.environ["ZHIPU_API_KEY"]                                                                               
URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"                                                       
MODEL = "glm-4-flash"                                                                                               

"""=== 第一步：定义一个实际的 Python 函数 ==="""                                                                          
def get_weather(city: str) -> str:                                                                                  
    """模拟天气查询（真实场景可以接 API）"""                                                                        
    # weather = {
        # "北京": "晴，25度",
        # "杭州": "多云，26°C",                                                     
        # "上海": "多云，28°C",                                                                                       
        # "深圳": "雨，30°C",                                                                                         
    # }

    weather = {                                                                                                         
         "北京": "晴，25°C",                                                                                             
         "上海": "多云，28°C",                                                                                           
         "深圳": "雨，30°C",                                                                                             
         "杭州": "多云转晴，27°C",                                                                                       
    }
                                                                                                               
    return weather.get(city, f"未找到 {city} 的天气")                                                               

"""=== 第二步：把函数"翻译"成 LLM 能看懂的工具描述 ==="""                                                                 
tools = [                                                                                                           
    {                                                                                                               
        "type": "function",                                                                                         
        "function": {                                                                                               
            "name": "get_weather",                                                                                  
            "description": "查询指定城市的天气",                                                                    
            "parameters": {                                                                                         
                "type": "object",                                                                                   
                "properties": {                                                                                     
                    "city": {                                                                                       
                        "type": "string",                                                                           
                        "description": "城市名，比如 杭州、上海、深圳",                                             
                    }                                                                                               
                },                                                                                                  
                "required": ["city"],                                                                               
            },                                                                                                      
        },                                                                                                          
    }                                                                                                               
]                                                                                                                   

"""=== 第三步：发请求，让 LLM 决定要不要调工具 ==="""                                                                     
def chat(messages: list[dict]) -> dict:                                                                             
    """返回完整的 message 对象，不只是文本（因为可能是 tool_calls）"""                                              
    resp = requests.post(                                                                                           
        URL,                                                                                                        
        headers={"Authorization": f"Bearer {API_KEY}"},                                                             
        json={"model": MODEL, "messages": messages, "tools": tools},                                                
        timeout=30,                                                                                                 
    )                                                                                                               
    resp.raise_for_status()                                                                                         
    return resp.json()["choices"][0]["message"]                                                                     

"""=== 第四步：主循环 —— 执行工具 + 把结果塞回去 ==="""                                                                   
def run(user_input: str) -> str:                                                                                    
    messages = [                                                                                                    
        {"role": "system", "content": "你是助手，能查天气就查。"},                                                  
        {"role": "user", "content": user_input},                                                                    
    ]                                                                                                               
                                                                                                                         
    # 第一次调用                                                                                                    
    msg = chat(messages)                                                                                            
    messages.append(msg)  # 记住 LLM 的回复（可能是 tool_calls）                                                    
                                                                                                                         
    # 如果 LLM 决定调工具                                                                                           
    if msg.get("tool_calls"):                                                                                       
        for call in msg["tool_calls"]:                                                                              
            fn_name = call["function"]["name"]                                                                      
            args = json.loads(call["function"]["arguments"])                                                        
                                                                                                                         
            # 实际执行函数                                                                                          
            if fn_name == "get_weather":                                                                            
                result = get_weather(**args)                                                                         
            else:                                                                                                   
                result = f"未知工具: {fn_name}"                                                                     
                                                                                                                         
            # 把工具结果塞回 messages                                                                               
            messages.append(                                                                                        
                {                                                                                                   
                "role": "tool",                                                                                 
                "tool_call_id": call["id"],                                                                     
                "content": result,                                                                              
                }                                                                                                     
            )                                                                                                       
                                                                                                                         
        # 第二次调用：让 LLM 基于工具结果生成最终回复                                                               
        final = chat(messages)                                                                                      
        return final["content"]                                                                                     
                                                                                                                         
    # LLM 没调工具，直接返回文本                                                                                    
    return msg["content"]                                                                                           
           
# def main():
    # print(run("杭州今天天气怎么样？"))


if __name__ == "__main__":                                                                                                 
    # main()
    print(run("杭州今天天气怎么样?"))


