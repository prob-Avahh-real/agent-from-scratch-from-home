"""阶段 1: 裸调 OpenAI API，理解 request/response 结构"""
import os
import requests
import sys
import time
import random
                                                                                                                         
# API_KEY = os.environ["OPENAI_API_KEY"]  # 从环境变量读，不要写死在代码里                                            
# URL = "https://api.openai.com/v1/chat/completions"                                                                  
# MODEL = "gpt-4o-mini"                                                                                               

API_KEY = os.environ["ZHIPU_API_KEY"]                                                                               
URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"                                                       
MODEL = "glm-4-flash"  # 免费；想更好用 glm-4-plus
                                                                                                                         
def chat(messages: list[dict]) -> str:
    delay = 1
    for attempt in range(6):
        """发一次请求，返回 assistant 的回复文本"""                                                                     
        resp = requests.post(                                                                                           
            URL,                                                                                                        
            headers={"Authorization": f"Bearer {API_KEY}"},                                                             
            json={"model": MODEL, "messages": messages},                                                                
            timeout=30,                                                                                                 
        )                                                                                                               
        
        if resp.status_code != 429:
            resp.raise_for_status()  # 4xx/5xx 直接抛异常，方便看到错误                                                     
            return resp.json()["choices"][0]["message"]["content"]                                                          
        
        time.sleep(delay + random.uniform(0, 0.5)) 
        delay = min(delay * 2, 60)
    
    raise RuntimeError("429 too many requests, still failing after retries")

                                                                                                                
def main():                                                                                                  
    messages = [                                                                                                    
        {"role": "system", "content": "你是一个简洁的助手，回答控制在两句话以内。"},                                
        {"role": "user", "content": "用一句话解释什么是 LLM。"},                                                    
    ]                                                                                                               
    print("User:", messages[-1]["content"])                                                                         
    print("Assistant:", chat(messages)) 

if __name__=='__main__':
    main()

                       
                                                     
