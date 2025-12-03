# 工作流程服務
# Workflow Service
"""
工作流程服務
============

提供工作流程的 CRUD 操作和執行邏輯：
- 建立、讀取、更新、刪除工作流程
- 工作流程步驟管理
- 工作流程執行
- 版本控制
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.workflow import Workflow
from src.services.logging_service import get_logger

logger = get_logger(__name__)


# =============================================================================
# 資料結構
# =============================================================================


@dataclass
class WorkflowStep:
    """工作流程步驟"""
    
    order: int
    """步驟順序"""
    
    action: str
    """執行動作（對應 CommandType）"""
    
    parameters: Dict[str, Any] = field(default_factory=dict)
    """動作參數"""
    
    description: Optional[str] = None
    """步驟描述"""
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "order": self.order,
            "action": self.action,
            "parameters": self.parameters,
            "description": self.description,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowStep":
        """從字典建立"""
        return cls(
            order=data.get("order", 0),
            action=data.get("action", ""),
            parameters=data.get("parameters", {}),
            description=data.get("description"),
        )


@dataclass
class WorkflowResult:
    """工作流程執行結果"""
    
    status: str
    """狀態：success, error, partial"""
    
    message: str
    """結果訊息"""
    
    step_results: List[Dict[str, Any]] = field(default_factory=list)
    """各步驟執行結果"""
    
    data: Dict[str, Any] = field(default_factory=dict)
    """附加資料"""


# =============================================================================
# 工作流程服務
# =============================================================================


class WorkflowService:
    """
    工作流程服務
    
    提供工作流程的業務邏輯操作。
    """
    
    async def create_workflow(
        self,
        db: AsyncSession,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        steps: Optional[List[WorkflowStep]] = None,
    ) -> Workflow:
        """
        建立新的工作流程
        
        Args:
            db: 資料庫 session
            user_id: 使用者 ID
            name: 工作流程名稱
            description: 描述
            steps: 步驟列表
        
        Returns:
            Workflow: 建立的工作流程
        
        Raises:
            ValueError: 如果名稱已存在
        """
        # 檢查名稱是否已存在
        existing = await self.get_workflow_by_name(db, user_id, name)
        if existing:
            raise ValueError(f"工作流程「{name}」已存在")
        
        # 建立工作流程
        workflow = Workflow(
            user_id=user_id,
            name=name,
            description=description or "",
            trigger={"type": "manual", "value": ""},
            steps=[s.to_dict() for s in (steps or [])],
            is_active=True,
            version=1,
        )
        
        db.add(workflow)
        await db.commit()
        await db.refresh(workflow)
        
        logger.info(f"建立工作流程：{name}", extra={"user_id": user_id})
        
        return workflow
    
    async def get_workflow_by_name(
        self,
        db: AsyncSession,
        user_id: str,
        name: str,
    ) -> Optional[Workflow]:
        """
        透過名稱取得工作流程
        
        Args:
            db: 資料庫 session
            user_id: 使用者 ID
            name: 工作流程名稱
        
        Returns:
            Optional[Workflow]: 工作流程，不存在則為 None
        """
        result = await db.execute(
            select(Workflow).where(
                Workflow.user_id == user_id,
                Workflow.name == name,
            )
        )
        return result.scalar_one_or_none()
    
    async def get_workflow_by_id(
        self,
        db: AsyncSession,
        workflow_id: int,
    ) -> Optional[Workflow]:
        """
        透過 ID 取得工作流程
        
        Args:
            db: 資料庫 session
            workflow_id: 工作流程 ID
        
        Returns:
            Optional[Workflow]: 工作流程，不存在則為 None
        """
        result = await db.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        return result.scalar_one_or_none()
    
    async def list_workflows(
        self,
        db: AsyncSession,
        user_id: str,
        include_inactive: bool = True,
    ) -> List[Workflow]:
        """
        列出使用者的所有工作流程
        
        Args:
            db: 資料庫 session
            user_id: 使用者 ID
            include_inactive: 是否包含停用的工作流程
        
        Returns:
            List[Workflow]: 工作流程列表
        """
        query = select(Workflow).where(Workflow.user_id == user_id)
        
        if not include_inactive:
            query = query.where(Workflow.is_active == True)
        
        query = query.order_by(Workflow.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def update_workflow(
        self,
        db: AsyncSession,
        workflow: Workflow,
        name: Optional[str] = None,
        description: Optional[str] = None,
        steps: Optional[List[WorkflowStep]] = None,
    ) -> Workflow:
        """
        更新工作流程
        
        Args:
            db: 資料庫 session
            workflow: 工作流程物件
            name: 新名稱
            description: 新描述
            steps: 新步驟列表
        
        Returns:
            Workflow: 更新後的工作流程
        """
        if name:
            workflow.name = name
        if description is not None:
            workflow.description = description
        if steps is not None:
            workflow.steps = [s.to_dict() for s in steps]
        
        workflow.version += 1
        workflow.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(workflow)
        
        logger.info(f"更新工作流程：{workflow.name}", extra={"workflow_id": workflow.id})
        
        return workflow
    
    async def delete_workflow(
        self,
        db: AsyncSession,
        workflow: Workflow,
    ) -> None:
        """
        刪除工作流程
        
        Args:
            db: 資料庫 session
            workflow: 工作流程物件
        """
        workflow_name = workflow.name
        await db.delete(workflow)
        await db.commit()
        
        logger.info(f"刪除工作流程：{workflow_name}")
    
    async def toggle_status(
        self,
        db: AsyncSession,
        workflow: Workflow,
    ) -> Workflow:
        """
        切換工作流程狀態
        
        Args:
            db: 資料庫 session
            workflow: 工作流程物件
        
        Returns:
            Workflow: 更新後的工作流程
        """
        workflow.is_active = not workflow.is_active
        workflow.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(workflow)
        
        status = "啟用" if workflow.is_active else "停用"
        logger.info(f"工作流程「{workflow.name}」已{status}")
        
        return workflow
    
    async def add_step(
        self,
        db: AsyncSession,
        workflow: Workflow,
        action: str,
        parameters: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
    ) -> Workflow:
        """
        新增步驟到工作流程
        
        Args:
            db: 資料庫 session
            workflow: 工作流程物件
            action: 動作類型
            parameters: 動作參數
            description: 步驟描述
        
        Returns:
            Workflow: 更新後的工作流程
        """
        steps = workflow.steps or []
        new_order = len(steps) + 1
        
        new_step = WorkflowStep(
            order=new_order,
            action=action,
            parameters=parameters or {},
            description=description,
        )
        
        steps.append(new_step.to_dict())
        workflow.steps = steps
        workflow.version += 1
        workflow.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(workflow)
        
        logger.info(f"新增步驟到工作流程「{workflow.name}」：{action}")
        
        return workflow
    
    async def remove_step(
        self,
        db: AsyncSession,
        workflow: Workflow,
        step_order: int,
    ) -> Workflow:
        """
        從工作流程移除步驟
        
        Args:
            db: 資料庫 session
            workflow: 工作流程物件
            step_order: 要移除的步驟順序
        
        Returns:
            Workflow: 更新後的工作流程
        """
        steps = workflow.steps or []
        
        # 移除指定步驟
        steps = [s for s in steps if s.get("order") != step_order]
        
        # 重新編號
        for i, step in enumerate(steps, 1):
            step["order"] = i
        
        workflow.steps = steps
        workflow.version += 1
        workflow.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(workflow)
        
        logger.info(f"從工作流程「{workflow.name}」移除步驟 {step_order}")
        
        return workflow


# =============================================================================
# 工作流程執行器
# =============================================================================


class WorkflowRunner:
    """
    工作流程執行器
    
    負責執行工作流程中的步驟。
    """
    
    def __init__(self):
        """初始化執行器"""
        self._action_handlers: Dict[str, callable] = {}
    
    async def run(
        self,
        workflow: Workflow,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        執行工作流程
        
        Args:
            workflow: 工作流程物件
            user_id: 使用者 ID
            context: 執行上下文
        
        Returns:
            Dict: 執行結果
        """
        # 檢查工作流程是否啟用
        if hasattr(workflow, 'is_active') and not workflow.is_active:
            return {
                "status": "error",
                "message": f"工作流程「{workflow.name}」已停用",
            }
        
        if hasattr(workflow, 'status') and workflow.status == "inactive":
            return {
                "status": "error",
                "message": f"工作流程「{workflow.name}」已停用",
            }
        
        steps = workflow.steps or []
        step_results = []
        
        logger.info(f"開始執行工作流程：{workflow.name}", extra={"user_id": user_id})
        
        try:
            for step_data in steps:
                step = WorkflowStep.from_dict(step_data) if isinstance(step_data, dict) else step_data
                
                result = await self._execute_step(
                    step=step,
                    user_id=user_id,
                    context=context,
                )
                step_results.append(result)
                
                # 如果步驟失敗，停止執行
                if result.get("status") == "error":
                    return {
                        "status": "error",
                        "message": f"步驟 {step.order} 執行失敗",
                        "step_results": step_results,
                    }
            
            logger.info(f"工作流程「{workflow.name}」執行完成")
            
            return {
                "status": "success",
                "message": f"工作流程「{workflow.name}」執行完成",
                "step_results": step_results,
            }
            
        except Exception as e:
            logger.error(f"工作流程執行錯誤：{e}")
            return {
                "status": "error",
                "message": f"執行錯誤：{str(e)}",
                "step_results": step_results,
            }
    
    async def _execute_step(
        self,
        step: WorkflowStep,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        執行單一步驟
        
        Args:
            step: 步驟物件
            user_id: 使用者 ID
            context: 執行上下文
        
        Returns:
            Dict: 步驟執行結果
        """
        from src.commands.handlers.base import get_handler
        from src.commands.parser import CommandType, ParsedCommand
        
        try:
            # 將 action 轉換為 CommandType
            command_type = CommandType(step.action)
        except ValueError:
            return {
                "status": "error",
                "message": f"未知的動作類型：{step.action}",
                "step": step.order,
            }
        
        # 取得處理器
        handler = get_handler(command_type)
        if not handler:
            return {
                "status": "error",
                "message": f"找不到處理器：{step.action}",
                "step": step.order,
            }
        
        # 建立 ParsedCommand
        command = ParsedCommand(
            command_type=command_type,
            raw_text=f"{step.action} {step.parameters}",
            parameters=step.parameters,
        )
        
        # 執行處理器
        result = await handler.handle(user_id, command)
        
        return {
            "status": "success" if result.success else "error",
            "message": result.message,
            "step": step.order,
            "data": result.data,
        }


# =============================================================================
# 單例
# =============================================================================


_workflow_service: Optional[WorkflowService] = None
_workflow_runner: Optional[WorkflowRunner] = None


def get_workflow_service() -> WorkflowService:
    """取得 WorkflowService 單例"""
    global _workflow_service
    if _workflow_service is None:
        _workflow_service = WorkflowService()
    return _workflow_service


def get_workflow_runner() -> WorkflowRunner:
    """取得 WorkflowRunner 單例"""
    global _workflow_runner
    if _workflow_runner is None:
        _workflow_runner = WorkflowRunner()
    return _workflow_runner
