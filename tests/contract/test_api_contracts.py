# API 契約測試
# API Contract Tests
"""
API 契約測試
============

使用 OpenAPI 規格驗證 API 端點：
1. 請求格式驗證
2. 回應格式驗證
3. 狀態碼驗證
"""

import pytest
from fastapi.testclient import TestClient


class TestWebhookContract:
    """Webhook 端點契約測試"""
    
    def test_webhook_endpoint_exists(self, test_client: TestClient):
        """測試 Webhook 端點存在"""
        # 即使沒有正確的簽名，端點應該存在並返回錯誤而非 404
        response = test_client.post("/webhook")
        assert response.status_code != 404
    
    def test_webhook_requires_json_body(self, test_client: TestClient):
        """測試 Webhook 需要 JSON body"""
        response = test_client.post(
            "/webhook",
            content="not json",
            headers={
                "Content-Type": "text/plain",
                "X-Line-Signature": "test",
            },
        )
        # 應該返回 422 或 400
        assert response.status_code in [400, 415, 422]
    
    def test_webhook_accepts_valid_json(self, test_client: TestClient):
        """測試 Webhook 接受有效 JSON"""
        import json
        import hmac
        import hashlib
        import base64
        
        body = {"destination": "U123", "events": []}
        body_str = json.dumps(body)
        signature = base64.b64encode(
            hmac.new(
                b"test_secret",
                body_str.encode(),
                hashlib.sha256,
            ).digest()
        ).decode()
        
        response = test_client.post(
            "/webhook",
            content=body_str,
            headers={
                "Content-Type": "application/json",
                "X-Line-Signature": signature,
            },
        )
        
        assert response.status_code == 200


class TestHealthContract:
    """健康檢查端點契約測試"""
    
    def test_health_returns_json(self, test_client: TestClient):
        """測試健康檢查返回 JSON"""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("application/json")
    
    def test_health_response_structure(self, test_client: TestClient):
        """測試健康檢查回應結構"""
        response = test_client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy", "degraded"]
    
    def test_health_includes_app_info(self, test_client: TestClient):
        """測試健康檢查包含應用程式資訊"""
        response = test_client.get("/health")
        data = response.json()
        
        assert "app" in data or "version" in data


class TestRootContract:
    """根端點契約測試"""
    
    def test_root_returns_json(self, test_client: TestClient):
        """測試根端點返回 JSON"""
        response = test_client.get("/")
        
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("application/json")
    
    def test_root_includes_links(self, test_client: TestClient):
        """測試根端點包含連結"""
        response = test_client.get("/")
        data = response.json()
        
        assert "docs" in data or "message" in data


class TestOpenAPIContract:
    """OpenAPI 規格契約測試"""
    
    def test_openapi_spec_available(self, test_client: TestClient):
        """測試 OpenAPI 規格可用"""
        response = test_client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        
        # 驗證 OpenAPI 基本結構
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
    
    def test_openapi_info_complete(self, test_client: TestClient):
        """測試 OpenAPI info 完整"""
        response = test_client.get("/openapi.json")
        data = response.json()
        
        info = data.get("info", {})
        assert "title" in info
        assert "version" in info
    
    def test_openapi_paths_defined(self, test_client: TestClient):
        """測試 OpenAPI 路徑已定義"""
        response = test_client.get("/openapi.json")
        data = response.json()
        
        paths = data.get("paths", {})
        
        # 驗證關鍵路徑存在
        assert "/" in paths or "/health" in paths


class TestAPIDocsContract:
    """API 文檔契約測試"""
    
    def test_swagger_ui_available(self, test_client: TestClient):
        """測試 Swagger UI 可用"""
        response = test_client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_redoc_available(self, test_client: TestClient):
        """測試 ReDoc 可用"""
        response = test_client.get("/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
