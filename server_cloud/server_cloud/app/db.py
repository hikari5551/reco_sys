from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import DATABASE_URL

# =========================================================
# 数据库连接
# =========================================================
# 默认使用 SQLite，优点是轻量、免安装、适合毕业设计部署。
# 后续如果数据量增大，可以把 DATABASE_URL 改成 PostgreSQL。
# =========================================================

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    # 所有数据表模型的基类。
    pass


def get_db():
    # FastAPI 依赖函数：每次请求创建一个数据库会话，用完自动关闭。
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
