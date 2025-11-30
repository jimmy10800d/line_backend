# LINE 自動化流程引擎 - 資料庫遷移腳本
# LINE Workflow Automation Engine - Database Migration Script
"""
資料庫遷移腳本
==============

此腳本負責建立和遷移資料庫結構。

使用方式：
    python scripts/migrate_db.py

功能：
1. 建立所有資料表
2. 建立索引
3. 初始化預設資料（如有需要）
"""

import asyncio
import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import engine, logger, settings
from src.models.base import Base
# 匯入所有模型以確保它們被註冊
from src.models.user import User
from src.models.workflow import Workflow
from src.models.execution_log import ExecutionLog
from src.models.integration import Integration
from src.models.schedule import Schedule


async def create_tables() -> None:
    """
    建立所有資料表
    
    使用 SQLAlchemy 的 create_all 方法建立所有已註冊的模型對應的資料表。
    如果資料表已存在，則跳過。
    """
    logger.info("開始建立資料表...")
    
    async with engine.begin() as conn:
        # 建立所有資料表
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("資料表建立完成！")


async def drop_tables() -> None:
    """
    刪除所有資料表
    
    警告：此操作會刪除所有資料！僅用於開發環境重置。
    """
    if settings.is_production:
        logger.error("不允許在生產環境刪除資料表！")
        return
    
    logger.warning("開始刪除所有資料表...")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    logger.warning("所有資料表已刪除！")


async def init_default_data() -> None:
    """
    初始化預設資料
    
    建立系統運行所需的預設資料，例如預設用戶。
    """
    from src.config import async_session_factory
    
    logger.info("檢查預設資料...")
    
    async with async_session_factory() as session:
        # 檢查是否已有用戶
        from sqlalchemy import select
        result = await session.execute(select(User).limit(1))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            logger.info(f"已存在用戶：{existing_user.line_user_id}")
        else:
            logger.info("尚無用戶資料，系統將在首次 LINE 訊息時自動建立用戶。")
        
        await session.commit()
    
    logger.info("預設資料檢查完成！")


async def migrate() -> None:
    """
    執行完整的資料庫遷移
    
    包含：
    1. 建立資料表
    2. 初始化預設資料
    """
    logger.info("=" * 50)
    logger.info("LINE 自動化流程引擎 - 資料庫遷移")
    logger.info("=" * 50)
    logger.info(f"環境：{settings.app_env}")
    logger.info(f"資料庫：{settings.database_url}")
    logger.info("=" * 50)
    
    try:
        # 建立資料表
        await create_tables()
        
        # 初始化預設資料
        await init_default_data()
        
        logger.info("=" * 50)
        logger.info("資料庫遷移完成！")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"資料庫遷移失敗：{e}")
        raise


def main() -> None:
    """
    主函數入口
    
    解析命令列參數並執行對應操作。
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="LINE 自動化流程引擎 - 資料庫遷移工具")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="重置資料庫（刪除所有資料表後重建，僅限開發環境）"
    )
    
    args = parser.parse_args()
    
    if args.reset:
        if settings.is_production:
            print("錯誤：不允許在生產環境重置資料庫！")
            sys.exit(1)
        
        confirm = input("警告：此操作將刪除所有資料！確定要繼續嗎？(yes/no): ")
        if confirm.lower() != "yes":
            print("操作已取消。")
            sys.exit(0)
        
        async def reset_and_migrate():
            await drop_tables()
            await create_tables()
            await init_default_data()
        
        asyncio.run(reset_and_migrate())
    else:
        asyncio.run(migrate())


if __name__ == "__main__":
    main()
