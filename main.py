from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time

app = FastAPI()

# 配置 CORS 中间件，允许所有来源的请求（用于测试）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定义请求体的数据模型
class SuggestionRequest(BaseModel):
    message: str

@app.get("/")
def read_root():
    """
    根路径，用于健康检查
    """
    return {"message": "AI聊天助手后端API正在运行", "status": "ok"}

@app.post("/getReplySuggestions")
def get_suggestions(request: SuggestionRequest):
    """
    这是一个"假的"AI 端点。
    它接收一条消息，然后总是返回固定的三条建议。
    """
    print(f"收到消息: {request.message}")

    # 模拟AI思考的延迟
    time.sleep(1) 

    return {
        "suggestions": [
            "哈哈，真有趣！😂",
            "收到啦，谢谢！",
            f"关于 '{request.message}' 这一点，我觉得..."
        ]
    }