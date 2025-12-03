# Weather 處理器單元測試
# Weather Handler Unit Tests
"""
天氣處理器測試
==============

使用 TDD 方法測試天氣查詢功能：
1. 城市查詢
2. 錯誤處理
3. API 整合
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.commands.parser import CommandType, ParsedCommand
from src.commands.handlers.weather import WeatherHandler


class TestWeatherHandler:
    """天氣處理器測試"""
    
    @pytest.fixture
    def handler(self) -> WeatherHandler:
        """建立處理器實例"""
        return WeatherHandler()
    
    @pytest.fixture
    def mock_weather_api(self):
        """Mock 天氣 API"""
        with patch('src.commands.handlers.weather.httpx.AsyncClient') as mock_client, \
             patch('src.commands.handlers.weather.settings') as mock_settings:
            mock_settings.weather_api_key = "fake_api_key"  # 設置假 API key
            
            client = MagicMock()
            client.__aenter__ = AsyncMock(return_value=client)
            client.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = client
            yield client
    
    # =========================================================================
    # 基本功能測試
    # =========================================================================
    
    def test_supported_commands(self, handler: WeatherHandler):
        """測試支援的指令類型"""
        assert CommandType.WEATHER in handler.supported_commands
    
    def test_can_handle_weather(self, handler: WeatherHandler):
        """測試能否處理天氣指令"""
        assert handler.can_handle(CommandType.WEATHER)
    
    def test_cannot_handle_other_commands(self, handler: WeatherHandler):
        """測試不處理其他指令"""
        assert not handler.can_handle(CommandType.HELP)
    
    # =========================================================================
    # 天氣查詢測試
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_query_weather_taipei(
        self, handler: WeatherHandler, mock_weather_api
    ):
        """測試查詢台北天氣"""
        # 設定 Mock 回應
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"description": "晴天", "icon": "01d"}],
            "main": {"temp": 25.5, "humidity": 60},
            "name": "Taipei",
        }
        mock_weather_api.get = AsyncMock(return_value=mock_response)
        
        command = ParsedCommand(
            command_type=CommandType.WEATHER,
            raw_text="weather 台北",
            parameters={"city": "台北"},
        )
        
        result = await handler.handle("U123", command)
        
        assert result.success is True
        assert "台北" in result.message or "Taipei" in result.message
        assert "25" in result.message or "晴" in result.message
    
    @pytest.mark.asyncio
    async def test_query_weather_with_english_city(
        self, handler: WeatherHandler, mock_weather_api
    ):
        """測試查詢英文城市名稱"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"description": "cloudy", "icon": "03d"}],
            "main": {"temp": 20.0, "humidity": 70},
            "name": "Tokyo",
        }
        mock_weather_api.get = AsyncMock(return_value=mock_response)
        
        command = ParsedCommand(
            command_type=CommandType.WEATHER,
            raw_text="weather Tokyo",
            parameters={"city": "Tokyo"},
        )
        
        result = await handler.handle("U123", command)
        
        assert result.success is True
        assert "Tokyo" in result.message
    
    # =========================================================================
    # 錯誤處理測試
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_query_weather_city_not_found(
        self, handler: WeatherHandler, mock_weather_api
    ):
        """測試查詢不存在的城市"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "city not found"}
        mock_weather_api.get = AsyncMock(return_value=mock_response)
        
        command = ParsedCommand(
            command_type=CommandType.WEATHER,
            raw_text="weather NotExistCity",
            parameters={"city": "NotExistCity"},
        )
        
        result = await handler.handle("U123", command)
        
        assert result.success is False
        assert "找不到" in result.message or "not found" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_query_weather_api_error(
        self, handler: WeatherHandler, mock_weather_api
    ):
        """測試 API 錯誤"""
        mock_weather_api.get = AsyncMock(side_effect=Exception("API Error"))
        
        command = ParsedCommand(
            command_type=CommandType.WEATHER,
            raw_text="weather 台北",
            parameters={"city": "台北"},
        )
        
        result = await handler.handle("U123", command)
        
        assert result.success is False
        assert "錯誤" in result.message or "error" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_query_weather_missing_city(self, handler: WeatherHandler):
        """測試缺少城市參數"""
        command = ParsedCommand(
            command_type=CommandType.WEATHER,
            raw_text="weather",
            parameters={},
        )
        
        # 驗證錯誤
        error = await handler.validate(command)
        assert error is not None
        assert "城市" in error or "city" in error.lower()
    
    # =========================================================================
    # 格式化測試
    # =========================================================================
    
    def test_format_weather_message(self, handler: WeatherHandler):
        """測試格式化天氣訊息"""
        weather_data = {
            "weather": [{"description": "晴天", "icon": "01d"}],
            "main": {"temp": 25.5, "humidity": 60},
            "name": "Taipei",
        }
        
        message = handler._format_weather_message(weather_data)
        
        assert "Taipei" in message
        assert "25" in message
        assert "晴天" in message or "%" in message

