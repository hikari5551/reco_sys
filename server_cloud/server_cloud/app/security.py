from fastapi import Header, HTTPException
from app.config import API_KEY

# =========================================================
# 接口鉴权
# =========================================================
# 客户端请求受保护接口时，需要在请求头中携带：
# X-API-Key: 你的密钥
# =========================================================


def require_api_key(x_api_key: str | None = Header(default=None)):
    # 如果仍是默认密钥，为了本地调试不强制拦截。
    # 正式上线时请修改 .env 中的 API_KEY。
    if not API_KEY or API_KEY == "change-this-long-random-key":
        return True

    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")

    return True
