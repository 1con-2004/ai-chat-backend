import os
import time
import asyncio
import hashlib
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AIChatPartner Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SuggestionRequest(BaseModel):
    message: str
    context: Optional[str] = None

class SuggestionResponse(BaseModel):
    suggestions: List[str]
    model_used: str
    response_time_ms: int

# 硅基流动客户端配置
silicon_client = AsyncOpenAI(
    api_key=os.getenv("SILICON_API_KEY", "sk-jpkihphqhqzxyyegluyiafujwphldkjvhkgpopfoynihjcvc"),
    base_url=os.getenv("SILICON_BASE_URL", "https://api.siliconflow.cn/v1")
)

AI_CONFIG = {
    "model": os.getenv("SILICON_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
    "max_tokens": 120,
    "temperature": 0.8,
    "top_p": 0.9,
    "timeout": 8.0
}

CHAT_REPLY_PROMPT_TEMPLATE = """你是微信聊天助手。用户收到消息："{message}"

生成3条不同风格的中文回复：
1. 正式礼貌的回复（5-15字）
2. 轻松随意的回复（5-15字）
3. 幽默风趣的回复（5-15字）

要求：
- 直接给出回复内容，不要编号或说明
- 每行一条
- 符合中文聊天习惯
- 风格差异明显

回复："""

async def generate_ai_suggestions(message: str, context: Optional[str] = None) -> List[str]:
    """调用硅基流动API生成回复建议"""
    start_time = time.time()
    
    try:
        prompt = CHAT_REPLY_PROMPT_TEMPLATE.format(message=message)
        if context:
            prompt += f"\n[对话背景: {context[:100]}]"
        
        response = await asyncio.wait_for(
            silicon_client.chat.completions.create(
                model=AI_CONFIG["model"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=AI_CONFIG["max_tokens"],
                temperature=AI_CONFIG["temperature"],
                top_p=AI_CONFIG["top_p"]
            ),
            timeout=AI_CONFIG["timeout"]
        )
        
        content = response.choices[0].message.content.strip()
        suggestions = [
            line.strip() 
            for line in content.split('\n') 
            if line.strip() and len(line.strip()) > 1
        ]
        
        # 过滤和验证建议
        filtered_suggestions = []
        for suggestion in suggestions[:5]:
            if len(suggestion) <= 30 and not any(skip in suggestion for skip in ["1.", "2.", "3.", "回复：", "建议："]):
                filtered_suggestions.append(suggestion)
        
        if len(filtered_suggestions) < 3:
            filtered_suggestions.extend(get_fallback_suggestions(message)[:3-len(filtered_suggestions)])
        
        elapsed_time = (time.time() - start_time) * 1000
        logger.info(f"AI生成耗时: {elapsed_time:.0f}ms, 生成数量: {len(filtered_suggestions)}")
        
        return filtered_suggestions[:3]
        
    except asyncio.TimeoutError:
        logger.warning("硅基流动API超时，使用智能备选方案")
        return get_smart_fallback_suggestions(message)
    except Exception as e:
        logger.error(f"硅基流动API调用失败: {e}")
        return get_smart_fallback_suggestions(message)

def get_smart_fallback_suggestions(message: str) -> List[str]:
    """智能备选建议生成"""
    message_lower = message.lower()
    
    # 基于内容特征的智能匹配
    if any(word in message for word in ["谢谢", "感谢", "thank"]):
        return ["不客气😊", "应该的", "互相帮忙嘛"]
    elif any(word in message for word in ["你好", "hi", "hello", "早", "晚上好"]):
        return ["你好", "嗨", "早上好呀"]
    elif any(word in message for word in ["？", "?", "怎么", "为什么", "什么"]):
        return ["让我想想", "这个问题不错", "有道理哦"]
    elif any(word in message for word in ["哈哈", "😄", "😂", "笑", "有趣"]):
        return ["哈哈哈", "确实很有意思", "笑死我了"]
    elif any(word in message for word in ["累", "忙", "辛苦", "疲惫"]):
        return ["注意休息", "别太累了", "早点睡"]
    elif any(word in message for word in ["吃", "饭", "食物", "饿"]):
        return ["我也饿了", "好吃吗", "一起吃饭吧"]
    else:
        # 基于消息哈希的确定性备选
        msg_hash = hashlib.md5(message.encode()).hexdigest()
        hash_index = int(msg_hash[:2], 16) % 5
        
        fallback_pools = [
            ["收到", "好的", "明白了"],
            ["确实", "是的", "有道理"],
            ["嗯嗯", "没问题", "OK"],
            ["理解", "知道了", "懂了"],
            ["好吧", "这样啊", "原来如此"]
        ]
        
        return fallback_pools[hash_index]

def get_fallback_suggestions(message: str) -> List[str]:
    """基础备选建议"""
    return ["好的", "收到", "明白"]

@app.get("/")
async def health_check():
    """健康检查接口"""
    return {
        "status": "ok",
        "service": "AIChatPartner Backend",
        "model": AI_CONFIG["model"],
        "version": "1.0.0"
    }

@app.post("/getReplySuggestions", response_model=SuggestionResponse)
async def get_reply_suggestions(request: SuggestionRequest):
    """获取AI回复建议的主接口"""
    start_time = time.time()
    
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="消息内容不能为空")
    
    try:
        suggestions = await generate_ai_suggestions(request.message.strip(), request.context)
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return SuggestionResponse(
            suggestions=suggestions,
            model_used=AI_CONFIG["model"],
            response_time_ms=response_time_ms
        )
        
    except Exception as e:
        logger.error(f"处理请求失败: {e}")
        # 降级处理：返回智能备选建议
        suggestions = get_smart_fallback_suggestions(request.message)
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return SuggestionResponse(
            suggestions=suggestions,
            model_used="fallback",
            response_time_ms=response_time_ms
        )

@app.get("/health")
async def detailed_health():
    """详细健康检查"""
    try:
        # 测试API连通性
        test_start = time.time()
        response = await asyncio.wait_for(
            silicon_client.chat.completions.create(
                model=AI_CONFIG["model"],
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            ),
            timeout=5.0
        )
        test_time = (time.time() - test_start) * 1000
        
        return {
            "status": "healthy",
            "ai_service": "available",
            "model": AI_CONFIG["model"],
            "test_response_time_ms": int(test_time),
            "timestamp": int(time.time())
        }
    except Exception as e:
        return {
            "status": "degraded",
            "ai_service": "unavailable", 
            "error": str(e),
            "fallback_mode": True,
            "timestamp": int(time.time())
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7950)