# 天氣處理器
# Weather Handler
"""
天氣查詢處理器
==============

提供天氣查詢功能：
- 使用 OpenWeatherMap API
- 支援中英文城市名稱
- 格式化天氣資訊回覆
"""

from typing import Dict, Any, List, Optional

import httpx

from src.config import settings
from src.commands.parser import CommandType, ParsedCommand
from src.commands.handlers.base import BaseHandler, HandlerResult
from src.services.logging_service import get_logger

logger = get_logger(__name__)


# 城市名稱中英文對照
CITY_MAPPING = {
    "台北": "Taipei",
    "台中": "Taichung",
    "高雄": "Kaohsiung",
    "台南": "Tainan",
    "新竹": "Hsinchu",
    "桃園": "Taoyuan",
    "基隆": "Keelung",
    "嘉義": "Chiayi",
    "花蓮": "Hualien",
    "台東": "Taitung",
    "宜蘭": "Yilan",
    "屏東": "Pingtung",
    "彰化": "Changhua",
    "雲林": "Yunlin",
    "南投": "Nantou",
    "苗栗": "Miaoli",
    "新北": "New Taipei",
    "東京": "Tokyo",
    "大阪": "Osaka",
    "紐約": "New York",
    "倫敦": "London",
    "巴黎": "Paris",
}

# 天氣圖示對照
WEATHER_ICONS = {
    "01d": "☀️",  # 晴天（日）
    "01n": "🌙",  # 晴天（夜）
    "02d": "⛅",  # 少雲
    "02n": "☁️",  # 少雲
    "03d": "☁️",  # 多雲
    "03n": "☁️",  # 多雲
    "04d": "☁️",  # 陰天
    "04n": "☁️",  # 陰天
    "09d": "🌧️",  # 陣雨
    "09n": "🌧️",  # 陣雨
    "10d": "🌦️",  # 雨天
    "10n": "🌧️",  # 雨天
    "11d": "⛈️",  # 雷雨
    "11n": "⛈️",  # 雷雨
    "13d": "❄️",  # 雪
    "13n": "❄️",  # 雪
    "50d": "🌫️",  # 霧
    "50n": "🌫️",  # 霧
}


class WeatherHandler(BaseHandler):
    """
    天氣查詢處理器
    
    使用 OpenWeatherMap API 查詢天氣資訊。
    """
    
    # OpenWeatherMap API 基礎 URL
    API_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    
    @property
    def supported_commands(self) -> List[CommandType]:
        """支援的指令類型"""
        return [CommandType.WEATHER]
    
    async def validate(self, command: ParsedCommand) -> Optional[str]:
        """
        驗證指令參數
        
        Args:
            command: 已解析的指令
        
        Returns:
            錯誤訊息，如果驗證通過則返回 None
        """
        city = command.parameters.get("city", "").strip()
        
        if not city:
            return "請提供要查詢的城市名稱。例如：weather 台北"
        
        return None
    
    async def handle(
        self,
        user_id: str,
        command: ParsedCommand,
    ) -> HandlerResult:
        """
        處理天氣查詢指令
        
        Args:
            user_id: 用戶 ID
            command: 已解析的指令
        
        Returns:
            HandlerResult: 處理結果
        """
        city = command.parameters.get("city", "").strip()
        
        logger.info(
            "Querying weather",
            extra={"user_id": user_id, "city": city},
        )
        
        try:
            # 查詢天氣
            weather_data = await self._fetch_weather(city)
            
            if weather_data is None:
                return HandlerResult.error_result(
                    message=f"找不到城市「{city}」的天氣資訊。請確認城市名稱是否正確。",
                    error_code="CITY_NOT_FOUND",
                )
            
            # 格式化回覆
            message = self._format_weather_message(weather_data)
            
            return HandlerResult.success_result(
                message=message,
                data=weather_data,
            )
            
        except Exception as e:
            logger.error(
                "Weather query error",
                extra={"user_id": user_id, "city": city, "error": str(e)},
            )
            
            return HandlerResult.error_result(
                message="查詢天氣時發生錯誤，請稍後再試。",
                error_code="WEATHER_API_ERROR",
            )
    
    async def _fetch_weather(self, city: str) -> Optional[Dict[str, Any]]:
        """
        從 OpenWeatherMap API 取得天氣資料
        
        Args:
            city: 城市名稱
        
        Returns:
            天氣資料字典，如果查詢失敗則返回 None
        """
        # 轉換中文城市名稱
        query_city = CITY_MAPPING.get(city, city)
        
        # 檢查 API Key
        api_key = settings.weather_api_key
        if not api_key:
            logger.warning("Weather API key not configured")
            # 返回模擬資料供測試使用
            return self._get_mock_weather(city)
        
        params = {
            "q": query_city,
            "appid": api_key,
            "units": "metric",
            "lang": "zh_tw",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.API_BASE_URL, params=params)
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            return response.json()
    
    def _get_mock_weather(self, city: str) -> Dict[str, Any]:
        """
        取得模擬天氣資料（用於沒有 API Key 的情況）
        
        Args:
            city: 城市名稱
        
        Returns:
            模擬的天氣資料
        """
        return {
            "weather": [{"description": "晴天", "icon": "01d"}],
            "main": {
                "temp": 25.0,
                "feels_like": 26.5,
                "humidity": 65,
                "temp_min": 22.0,
                "temp_max": 28.0,
            },
            "wind": {"speed": 3.5},
            "name": CITY_MAPPING.get(city, city),
        }
    
    def _format_weather_message(self, weather_data: Dict[str, Any]) -> str:
        """
        格式化天氣資訊為回覆訊息
        
        Args:
            weather_data: 天氣資料
        
        Returns:
            格式化的訊息
        """
        city = weather_data.get("name", "未知")
        weather = weather_data.get("weather", [{}])[0]
        main = weather_data.get("main", {})
        wind = weather_data.get("wind", {})
        
        # 取得天氣圖示
        icon_code = weather.get("icon", "01d")
        icon = WEATHER_ICONS.get(icon_code, "🌡️")
        
        # 天氣描述
        description = weather.get("description", "未知")
        
        # 溫度資訊
        temp = main.get("temp", 0)
        feels_like = main.get("feels_like", 0)
        temp_min = main.get("temp_min", 0)
        temp_max = main.get("temp_max", 0)
        humidity = main.get("humidity", 0)
        
        # 風速
        wind_speed = wind.get("speed", 0)
        
        # 組合訊息
        message = f"""
{icon} {city} 天氣資訊

🌡️ 目前溫度：{temp:.1f}°C
🤔 體感溫度：{feels_like:.1f}°C
📈 最高溫度：{temp_max:.1f}°C
📉 最低溫度：{temp_min:.1f}°C
💧 濕度：{humidity}%
💨 風速：{wind_speed} m/s

{description}
        """.strip()
        
        return message


# =============================================================================
# 處理器註冊
# =============================================================================

def get_weather_handler() -> WeatherHandler:
    """取得天氣處理器實例"""
    return WeatherHandler()

