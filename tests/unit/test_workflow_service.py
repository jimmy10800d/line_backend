# 工作流程服務單元測試
# Workflow Service Unit Tests
"""
工作流程服務測試
================

測試工作流程的 CRUD 操作和業務邏輯。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.commands.parser import CommandType, ParsedCommand


# =============================================================================
# WorkflowService 測試
# =============================================================================


class TestWorkflowService:
    """工作流程服務測試"""

    @pytest.fixture
    def workflow_service(self):
        """建立 WorkflowService 實例"""
        from src.services.workflow_service import WorkflowService
        return WorkflowService()

    @pytest.fixture
    def mock_db_session(self):
        """Mock 資料庫 session"""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.add = MagicMock()
        session.delete = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_create_workflow(self, workflow_service, mock_db_session):
        """測試建立工作流程"""
        # Mock: 查詢時回傳 None（不存在）
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        result = await workflow_service.create_workflow(
            db=mock_db_session,
            user_id="U123",
            name="早安提醒",
            description="每天早上的提醒流程",
        )
        
        assert result is not None
        assert result.name == "早安提醒"
        assert result.user_id == "U123"

    @pytest.mark.asyncio
    async def test_create_workflow_duplicate_name(self, workflow_service, mock_db_session):
        """測試建立重複名稱的工作流程"""
        # 模擬已存在的工作流程
        mock_db_session.execute.return_value.scalar_one_or_none = MagicMock(
            return_value=MagicMock(name="早安提醒")
        )
        
        with pytest.raises(ValueError, match="已存在"):
            await workflow_service.create_workflow(
                db=mock_db_session,
                user_id="U123",
                name="早安提醒",
            )

    @pytest.mark.asyncio
    async def test_get_workflow_by_name(self, workflow_service, mock_db_session):
        """測試透過名稱取得工作流程"""
        mock_workflow = MagicMock()
        mock_workflow.name = "早安提醒"
        mock_workflow.status = "active"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_workflow
        mock_db_session.execute.return_value = mock_result
        
        result = await workflow_service.get_workflow_by_name(
            db=mock_db_session,
            user_id="U123",
            name="早安提醒",
        )
        
        assert result is not None
        assert result.name == "早安提醒"

    @pytest.mark.asyncio
    async def test_get_workflow_not_found(self, workflow_service, mock_db_session):
        """測試取得不存在的工作流程"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        result = await workflow_service.get_workflow_by_name(
            db=mock_db_session,
            user_id="U123",
            name="不存在",
        )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_list_workflows(self, workflow_service, mock_db_session):
        """測試列出所有工作流程"""
        mock_workflows = [
            MagicMock(name="早安提醒", status="active"),
            MagicMock(name="每日報告", status="active"),
            MagicMock(name="週報", status="inactive"),
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_workflows
        mock_db_session.execute.return_value = mock_result
        
        result = await workflow_service.list_workflows(
            db=mock_db_session,
            user_id="U123",
        )
        
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_list_workflows_empty(self, workflow_service, mock_db_session):
        """測試列出空的工作流程列表"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result
        
        result = await workflow_service.list_workflows(
            db=mock_db_session,
            user_id="U123",
        )
        
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_update_workflow(self, workflow_service, mock_db_session):
        """測試更新工作流程"""
        mock_workflow = MagicMock()
        mock_workflow.name = "早安提醒"
        
        result = await workflow_service.update_workflow(
            db=mock_db_session,
            workflow=mock_workflow,
            name="早安流程",
            description="更新後的描述",
        )
        
        assert result.name == "早安流程"

    @pytest.mark.asyncio
    async def test_delete_workflow(self, workflow_service, mock_db_session):
        """測試刪除工作流程"""
        mock_workflow = MagicMock()
        mock_workflow.id = 1
        mock_workflow.name = "舊流程"
        
        await workflow_service.delete_workflow(
            db=mock_db_session,
            workflow=mock_workflow,
        )
        
        mock_db_session.delete.assert_called_once_with(mock_workflow)
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_toggle_workflow_status(self, workflow_service, mock_db_session):
        """測試切換工作流程狀態"""
        mock_workflow = MagicMock()
        mock_workflow.is_active = True
        
        result = await workflow_service.toggle_status(
            db=mock_db_session,
            workflow=mock_workflow,
        )
        
        assert result.is_active == False

    @pytest.mark.asyncio
    async def test_add_step_to_workflow(self, workflow_service, mock_db_session):
        """測試新增步驟到工作流程"""
        mock_workflow = MagicMock()
        mock_workflow.steps = []
        
        result = await workflow_service.add_step(
            db=mock_db_session,
            workflow=mock_workflow,
            action="weather",
            parameters={"city": "台北"},
        )
        
        assert len(mock_workflow.steps) == 1

    @pytest.mark.asyncio
    async def test_remove_step_from_workflow(self, workflow_service, mock_db_session):
        """測試從工作流程移除步驟"""
        # 使用字典格式的步驟（符合實際資料結構）
        step1 = {"order": 1, "action": "weather", "parameters": {}}
        step2 = {"order": 2, "action": "remind", "parameters": {}}
        step3 = {"order": 3, "action": "todo", "parameters": {}}
        
        mock_workflow = MagicMock()
        mock_workflow.steps = [step1, step2, step3]
        
        result = await workflow_service.remove_step(
            db=mock_db_session,
            workflow=mock_workflow,
            step_order=2,
        )
        
        # 驗證步驟被移除（剩餘 2 個步驟，重新編號）
        assert len(mock_workflow.steps) == 2
        assert mock_workflow.steps[0]["order"] == 1
        assert mock_workflow.steps[1]["order"] == 2  # 重新編號


# =============================================================================
# WorkflowStep 測試
# =============================================================================


class TestWorkflowStep:
    """工作流程步驟測試"""

    def test_step_creation(self):
        """測試建立工作流程步驟"""
        from src.services.workflow_service import WorkflowStep
        
        step = WorkflowStep(
            order=1,
            action="weather",
            parameters={"city": "台北"},
        )
        
        assert step.order == 1
        assert step.action == "weather"
        assert step.parameters["city"] == "台北"

    def test_step_to_dict(self):
        """測試步驟轉換為字典"""
        from src.services.workflow_service import WorkflowStep
        
        step = WorkflowStep(
            order=1,
            action="weather",
            parameters={"city": "台北"},
        )
        
        result = step.to_dict()
        
        assert result["order"] == 1
        assert result["action"] == "weather"


# =============================================================================
# WorkflowRunner 測試
# =============================================================================


class TestWorkflowRunner:
    """工作流程執行器測試"""

    @pytest.fixture
    def workflow_runner(self):
        """建立 WorkflowRunner 實例"""
        from src.services.workflow_service import WorkflowRunner
        return WorkflowRunner()

    @pytest.mark.asyncio
    async def test_run_workflow_single_step(self, workflow_runner):
        """測試執行單步驟工作流程"""
        mock_workflow = MagicMock()
        mock_workflow.name = "早安提醒"
        mock_workflow.steps = [
            MagicMock(action="weather", parameters={"city": "台北"}),
        ]
        
        with patch.object(workflow_runner, '_execute_step', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {"status": "success", "data": {"temp": 25}}
            
            result = await workflow_runner.run(
                workflow=mock_workflow,
                user_id="U123",
            )
            
            assert result["status"] == "success"
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_workflow_multiple_steps(self, workflow_runner):
        """測試執行多步驟工作流程"""
        mock_workflow = MagicMock()
        mock_workflow.name = "每日報告"
        mock_workflow.steps = [
            MagicMock(action="weather", parameters={"city": "台北"}),
            MagicMock(action="todo", parameters={"action": "list"}),
        ]
        
        with patch.object(workflow_runner, '_execute_step', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {"status": "success"}
            
            result = await workflow_runner.run(
                workflow=mock_workflow,
                user_id="U123",
            )
            
            assert result["status"] == "success"
            assert mock_exec.call_count == 2

    @pytest.mark.asyncio
    async def test_run_workflow_step_failure(self, workflow_runner):
        """測試工作流程步驟執行失敗"""
        mock_workflow = MagicMock()
        mock_workflow.name = "測試流程"
        mock_workflow.steps = [
            MagicMock(action="invalid_action", parameters={}),
        ]
        
        with patch.object(workflow_runner, '_execute_step', new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = Exception("執行失敗")
            
            result = await workflow_runner.run(
                workflow=mock_workflow,
                user_id="U123",
            )
            
            assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_run_inactive_workflow(self, workflow_runner):
        """測試執行停用的工作流程"""
        mock_workflow = MagicMock()
        mock_workflow.name = "停用流程"
        mock_workflow.status = "inactive"
        
        result = await workflow_runner.run(
            workflow=mock_workflow,
            user_id="U123",
        )
        
        assert result["status"] == "error"
        assert "停用" in result["message"]
