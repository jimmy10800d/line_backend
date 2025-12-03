# 工作流程處理器
# Workflow Handler
"""
工作流程指令處理器
==================

處理工作流程相關指令：
- /create workflow [name] - 建立工作流程
- /list workflows - 列出工作流程
- /run [workflow] - 執行工作流程
- /edit workflow [name] - 編輯工作流程
- /delete workflow [name] - 刪除工作流程
"""

from typing import Optional

from src.commands.parser import CommandType, ParsedCommand
from src.commands.handlers.base import CommandHandler, CommandResult, register_handler
from src.services.logging_service import get_logger
from src.services.workflow_service import (
    get_workflow_service,
    get_workflow_runner,
    WorkflowStep,
)

logger = get_logger(__name__)


# =============================================================================
# 建立工作流程處理器
# =============================================================================


@register_handler(CommandType.CREATE_WORKFLOW)
class CreateWorkflowHandler(CommandHandler):
    """
    建立工作流程處理器
    
    指令格式：/create workflow [name]
    """
    
    async def handle(self, user_id: str, command: ParsedCommand) -> CommandResult:
        """處理建立工作流程指令"""
        from src.models.base import get_session
        
        # 取得工作流程名稱
        name = command.parameters.get("name", "").strip()
        
        if not name:
            return CommandResult(
                success=False,
                message="請提供工作流程名稱。\n用法：/create workflow [名稱]",
            )
        
        # 檢查名稱長度
        if len(name) > 50:
            return CommandResult(
                success=False,
                message="工作流程名稱不能超過 50 個字元。",
            )
        
        try:
            async with get_session() as db:
                service = get_workflow_service()
                
                workflow = await service.create_workflow(
                    db=db,
                    user_id=user_id,
                    name=name,
                )
                
                return CommandResult(
                    success=True,
                    message=f"✅ 已建立工作流程「{name}」！\n\n📝 下一步：\n- 使用 /edit workflow {name} 添加步驟\n- 使用 /list workflows 查看所有工作流程",
                    data={"workflow_id": workflow.id, "workflow_name": name},
                )
        except ValueError as e:
            return CommandResult(
                success=False,
                message=f"❌ {str(e)}",
            )
        except Exception as e:
            logger.error(f"建立工作流程失敗：{e}", extra={"user_id": user_id})
            return CommandResult(
                success=False,
                message="❌ 建立工作流程時發生錯誤，請稍後再試。",
            )


# =============================================================================
# 列出工作流程處理器
# =============================================================================


@register_handler(CommandType.LIST_WORKFLOWS)
class ListWorkflowsHandler(CommandHandler):
    """
    列出工作流程處理器
    
    指令格式：/list workflows
    """
    
    async def handle(self, user_id: str, command: ParsedCommand) -> CommandResult:
        """處理列出工作流程指令"""
        from src.models.base import get_session
        
        try:
            async with get_session() as db:
                service = get_workflow_service()
                
                workflows = await service.list_workflows(db, user_id)
                
                if not workflows:
                    return CommandResult(
                        success=True,
                        message="📋 您尚未建立任何工作流程。\n\n💡 提示：使用 /create workflow [名稱] 建立新的工作流程。",
                        data={"workflows": []},
                    )
                
                # 格式化輸出
                lines = ["📋 您的工作流程：\n"]
                for i, wf in enumerate(workflows, 1):
                    status = "✅" if wf.is_active else "⏸️"
                    step_count = len(wf.steps) if wf.steps else 0
                    lines.append(f"{i}. {status} {wf.name}")
                    if wf.description:
                        lines.append(f"   📝 {wf.description}")
                    lines.append(f"   📦 {step_count} 個步驟")
                
                lines.append(f"\n共 {len(workflows)} 個工作流程")
                
                return CommandResult(
                    success=True,
                    message="\n".join(lines),
                    data={"workflows": [{"name": wf.name, "is_active": wf.is_active} for wf in workflows]},
                )
        except Exception as e:
            logger.error(f"列出工作流程失敗：{e}", extra={"user_id": user_id})
            return CommandResult(
                success=False,
                message="❌ 取得工作流程時發生錯誤，請稍後再試。",
            )


# =============================================================================
# 執行工作流程處理器
# =============================================================================


@register_handler(CommandType.RUN_WORKFLOW)
class RunWorkflowHandler(CommandHandler):
    """
    執行工作流程處理器
    
    指令格式：/run [workflow_name]
    """
    
    async def handle(self, user_id: str, command: ParsedCommand) -> CommandResult:
        """處理執行工作流程指令"""
        from src.models.base import get_session
        
        # 取得工作流程名稱
        name = command.parameters.get("name", "").strip()
        
        if not name:
            return CommandResult(
                success=False,
                message="請提供工作流程名稱。\n用法：/run [工作流程名稱]",
            )
        
        try:
            async with get_session() as db:
                service = get_workflow_service()
                runner = get_workflow_runner()
                
                # 取得工作流程
                workflow = await service.get_workflow_by_name(db, user_id, name)
                
                if not workflow:
                    return CommandResult(
                        success=False,
                        message=f"❌ 找不到工作流程「{name}」。\n使用 /list workflows 查看所有工作流程。",
                    )
                
                # 檢查是否有步驟
                if not workflow.steps:
                    return CommandResult(
                        success=False,
                        message=f"⚠️ 工作流程「{name}」沒有任何步驟。\n請先使用 /edit workflow {name} 添加步驟。",
                    )
                
                # 執行工作流程
                result = await runner.run(workflow, user_id)
                
                if result["status"] == "success":
                    step_count = len(result.get("step_results", []))
                    return CommandResult(
                        success=True,
                        message=f"✅ 工作流程「{name}」執行完成！\n\n已執行 {step_count} 個步驟。",
                        data=result,
                    )
                else:
                    return CommandResult(
                        success=False,
                        message=f"❌ {result['message']}",
                        data=result,
                    )
        except Exception as e:
            logger.error(f"執行工作流程失敗：{e}", extra={"user_id": user_id})
            return CommandResult(
                success=False,
                message="❌ 執行工作流程時發生錯誤，請稍後再試。",
            )


# =============================================================================
# 編輯工作流程處理器
# =============================================================================


@register_handler(CommandType.EDIT_WORKFLOW)
class EditWorkflowHandler(CommandHandler):
    """
    編輯工作流程處理器
    
    指令格式：/edit workflow [name]
    
    此處理器提供編輯選項的互動式選單。
    """
    
    async def handle(self, user_id: str, command: ParsedCommand) -> CommandResult:
        """處理編輯工作流程指令"""
        from src.models.base import get_session
        
        # 取得工作流程名稱
        name = command.parameters.get("name", "").strip()
        
        if not name:
            return CommandResult(
                success=False,
                message="請提供工作流程名稱。\n用法：/edit workflow [名稱]",
            )
        
        try:
            async with get_session() as db:
                service = get_workflow_service()
                
                # 取得工作流程
                workflow = await service.get_workflow_by_name(db, user_id, name)
                
                if not workflow:
                    return CommandResult(
                        success=False,
                        message=f"❌ 找不到工作流程「{name}」。\n使用 /list workflows 查看所有工作流程。",
                    )
                
                # 顯示工作流程詳情和編輯選項
                status = "啟用中" if workflow.is_active else "已停用"
                steps = workflow.steps or []
                
                lines = [
                    f"📝 工作流程：{name}",
                    f"狀態：{status}",
                    f"版本：v{workflow.version}",
                    "",
                    "📦 步驟：",
                ]
                
                if steps:
                    for step in steps:
                        lines.append(f"  {step['order']}. {step['action']}")
                else:
                    lines.append("  （尚無步驟）")
                
                lines.extend([
                    "",
                    "💡 可用操作：",
                    "• 新增步驟：/add step [workflow] [action]",
                    "• 移除步驟：/remove step [workflow] [step_number]",
                    "• 切換狀態：/toggle workflow [name]",
                    "• 刪除流程：/delete workflow [name]",
                ])
                
                return CommandResult(
                    success=True,
                    message="\n".join(lines),
                    data={
                        "workflow_id": workflow.id,
                        "workflow_name": name,
                        "is_active": workflow.is_active,
                        "steps": steps,
                    },
                )
        except Exception as e:
            logger.error(f"編輯工作流程失敗：{e}", extra={"user_id": user_id})
            return CommandResult(
                success=False,
                message="❌ 取得工作流程資訊時發生錯誤，請稍後再試。",
            )


# =============================================================================
# 刪除工作流程處理器
# =============================================================================


@register_handler(CommandType.DELETE_WORKFLOW)
class DeleteWorkflowHandler(CommandHandler):
    """
    刪除工作流程處理器
    
    指令格式：/delete workflow [name]
    """
    
    async def handle(self, user_id: str, command: ParsedCommand) -> CommandResult:
        """處理刪除工作流程指令"""
        from src.models.base import get_session
        
        # 取得工作流程名稱
        name = command.parameters.get("name", "").strip()
        
        if not name:
            return CommandResult(
                success=False,
                message="請提供工作流程名稱。\n用法：/delete workflow [名稱]",
            )
        
        try:
            async with get_session() as db:
                service = get_workflow_service()
                
                # 取得工作流程
                workflow = await service.get_workflow_by_name(db, user_id, name)
                
                if not workflow:
                    return CommandResult(
                        success=False,
                        message=f"❌ 找不到工作流程「{name}」。\n使用 /list workflows 查看所有工作流程。",
                    )
                
                # 刪除工作流程
                await service.delete_workflow(db, workflow)
                
                return CommandResult(
                    success=True,
                    message=f"🗑️ 已刪除工作流程「{name}」。",
                    data={"deleted_workflow": name},
                )
        except Exception as e:
            logger.error(f"刪除工作流程失敗：{e}", extra={"user_id": user_id})
            return CommandResult(
                success=False,
                message="❌ 刪除工作流程時發生錯誤，請稍後再試。",
            )


# =============================================================================
# 切換工作流程狀態處理器
# =============================================================================


@register_handler(CommandType.TOGGLE_WORKFLOW)
class ToggleWorkflowHandler(CommandHandler):
    """
    切換工作流程狀態處理器
    
    指令格式：/toggle workflow [name]
    """
    
    async def handle(self, user_id: str, command: ParsedCommand) -> CommandResult:
        """處理切換工作流程狀態指令"""
        from src.models.base import get_session
        
        # 取得工作流程名稱
        name = command.parameters.get("name", "").strip()
        
        if not name:
            return CommandResult(
                success=False,
                message="請提供工作流程名稱。\n用法：/toggle workflow [名稱]",
            )
        
        try:
            async with get_session() as db:
                service = get_workflow_service()
                
                # 取得工作流程
                workflow = await service.get_workflow_by_name(db, user_id, name)
                
                if not workflow:
                    return CommandResult(
                        success=False,
                        message=f"❌ 找不到工作流程「{name}」。\n使用 /list workflows 查看所有工作流程。",
                    )
                
                # 切換狀態
                workflow = await service.toggle_status(db, workflow)
                
                status = "啟用" if workflow.is_active else "停用"
                emoji = "✅" if workflow.is_active else "⏸️"
                
                return CommandResult(
                    success=True,
                    message=f"{emoji} 工作流程「{name}」已{status}。",
                    data={"workflow_name": name, "is_active": workflow.is_active},
                )
        except Exception as e:
            logger.error(f"切換工作流程狀態失敗：{e}", extra={"user_id": user_id})
            return CommandResult(
                success=False,
                message="❌ 切換工作流程狀態時發生錯誤，請稍後再試。",
            )


# =============================================================================
# 新增步驟處理器
# =============================================================================


@register_handler(CommandType.ADD_STEP)
class AddStepHandler(CommandHandler):
    """
    新增步驟處理器
    
    指令格式：/add step [workflow] [action]
    """
    
    async def handle(self, user_id: str, command: ParsedCommand) -> CommandResult:
        """處理新增步驟指令"""
        from src.models.base import get_session
        
        workflow_name = command.parameters.get("workflow_name", "").strip()
        action = command.parameters.get("action", "").strip()
        
        if not workflow_name or not action:
            return CommandResult(
                success=False,
                message="請提供工作流程名稱和動作。\n用法：/add step [工作流程名稱] [動作]",
            )
        
        try:
            async with get_session() as db:
                service = get_workflow_service()
                
                # 取得工作流程
                workflow = await service.get_workflow_by_name(db, user_id, workflow_name)
                
                if not workflow:
                    return CommandResult(
                        success=False,
                        message=f"❌ 找不到工作流程「{workflow_name}」。",
                    )
                
                # 新增步驟
                workflow = await service.add_step(
                    db=db,
                    workflow=workflow,
                    action=action,
                    parameters=command.parameters.get("action_params", {}),
                )
                
                step_count = len(workflow.steps)
                
                return CommandResult(
                    success=True,
                    message=f"✅ 已新增步驟「{action}」到工作流程「{workflow_name}」。\n\n目前共 {step_count} 個步驟。",
                    data={
                        "workflow_name": workflow_name,
                        "action": action,
                        "step_count": step_count,
                    },
                )
        except Exception as e:
            logger.error(f"新增步驟失敗：{e}", extra={"user_id": user_id})
            return CommandResult(
                success=False,
                message="❌ 新增步驟時發生錯誤，請稍後再試。",
            )


# =============================================================================
# 移除步驟處理器
# =============================================================================


@register_handler(CommandType.REMOVE_STEP)
class RemoveStepHandler(CommandHandler):
    """
    移除步驟處理器
    
    指令格式：/remove step [workflow] [step_number]
    """
    
    async def handle(self, user_id: str, command: ParsedCommand) -> CommandResult:
        """處理移除步驟指令"""
        from src.models.base import get_session
        
        workflow_name = command.parameters.get("workflow_name", "").strip()
        step_order_str = command.parameters.get("step_order", "")
        
        if not workflow_name:
            return CommandResult(
                success=False,
                message="請提供工作流程名稱。\n用法：/remove step [工作流程名稱] [步驟編號]",
            )
        
        try:
            step_order = int(step_order_str)
        except (ValueError, TypeError):
            return CommandResult(
                success=False,
                message="請提供有效的步驟編號。\n用法：/remove step [工作流程名稱] [步驟編號]",
            )
        
        try:
            async with get_session() as db:
                service = get_workflow_service()
                
                # 取得工作流程
                workflow = await service.get_workflow_by_name(db, user_id, workflow_name)
                
                if not workflow:
                    return CommandResult(
                        success=False,
                        message=f"❌ 找不到工作流程「{workflow_name}」。",
                    )
                
                # 檢查步驟是否存在
                steps = workflow.steps or []
                if step_order < 1 or step_order > len(steps):
                    return CommandResult(
                        success=False,
                        message=f"❌ 步驟編號 {step_order} 不存在。工作流程共 {len(steps)} 個步驟。",
                    )
                
                # 移除步驟
                workflow = await service.remove_step(db, workflow, step_order)
                
                step_count = len(workflow.steps)
                
                return CommandResult(
                    success=True,
                    message=f"✅ 已從工作流程「{workflow_name}」移除步驟 {step_order}。\n\n剩餘 {step_count} 個步驟。",
                    data={
                        "workflow_name": workflow_name,
                        "removed_step": step_order,
                        "remaining_steps": step_count,
                    },
                )
        except Exception as e:
            logger.error(f"移除步驟失敗：{e}", extra={"user_id": user_id})
            return CommandResult(
                success=False,
                message="❌ 移除步驟時發生錯誤，請稍後再試。",
            )
