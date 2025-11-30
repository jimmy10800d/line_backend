# 處理器註冊
# Handler Registry
"""
處理器註冊模組
==============

負責註冊所有處理器到系統中。
在應用程式啟動時呼叫 register_all_handlers() 來初始化。
"""

from src.commands.handlers.base import register_handler


def register_all_handlers() -> None:
    """
    註冊所有處理器
    
    在應用程式啟動時呼叫此函式。
    """
    # 內建處理器在 base.py 中已經註冊（Help, Status, History）
    
    # 匯入並註冊天氣處理器
    from src.commands.handlers.weather import WeatherHandler
    register_handler(WeatherHandler())
    
    # 匯入並註冊提醒處理器
    from src.commands.handlers.remind import RemindHandler
    register_handler(RemindHandler())
    
    # 未來可以在這裡添加更多處理器
    # from src.commands.handlers.todo import TodoHandler
    # register_handler(TodoHandler())

