"""
数据库初始化脚本
用法: python init_db.py
自动从 .env 读取数据库配置，创建数据库和所有表
"""
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import Base
import app.models  # noqa: 加载所有 ORM 模型


def init_database():
    # 先连接 MySQL（不指定数据库），创建数据库
    root_url = f"mysql+pymysql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}"
    engine_root = create_engine(root_url)

    db_name = settings.db_name
    with engine_root.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
        conn.commit()
    engine_root.dispose()

    # 连接目标数据库，创建所有表
    engine = create_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)

    # 验证表是否创建成功
    with engine.connect() as conn:
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result]

    engine.dispose()
    return tables


if __name__ == "__main__":
    print(f"连接数据库: {settings.db_host}:{settings.db_port}")
    print(f"数据库名:   {settings.db_name}")
    tables = init_database()
    print(f"成功创建 {len(tables)} 张表:")
    for t in tables:
        print(f"  - {t}")
