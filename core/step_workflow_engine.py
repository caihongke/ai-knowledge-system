# -*- coding: utf-8 -*-
"""
Step Workflow Engine - 七步法工作流引擎
实现状态管理、流转控制、人机协同
"""

import json
# import yaml
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field, asdict
from threading import Timer
import uuid


class StepStatus(Enum):
    """步骤状态枚举"""
    PENDING = "pending"                    # 未开始
    IN_PROGRESS = "in_progress"           # 进行中
    PENDING_REVIEW = "pending_review"     # 待审核
    UNDER_REVIEW = "under_review"         # 审核中
    COMPLETED = "completed"               # 已完成
    ARCHIVED = "archived"                 # 已归档
    PAUSED = "paused"                     # 已暂停
    TERMINATED = "terminated"             # 已终止


class StepType(Enum):
    """步骤类型"""
    STEP1_DIAG = "step1_diag"
    STEP2_BLUEPRINT = "step2_blueprint"
    STEP3_STRATEGY = "step3_strategy"
    STEP4_RESOURCE = "step4_resource"
    STEP5_EXECUTE = "step5_execute"
    STEP6_MONITOR = "step6_monitor"
    STEP7_REVIEW = "step7_review"



class StepJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


@dataclass
class StepTransition:
    """状态转换定义"""
    trigger: str
    from_status: StepStatus
    to_status: StepStatus
    condition: Optional[str] = None
    timeout: Optional[int] = None  # 分钟
    auto_trigger: bool = False


@dataclass
class StepInstance:
    """步骤实例"""
    id: str
    step_type: StepType
    status: StepStatus
    project_id: str
    input_data: Dict = field(default_factory=dict)
    output_data: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    revision_count: int = 0
    max_revisions: int = 5

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class Notification:
    """通知定义"""
    id: str
    type: str
    recipient: str
    title: str
    content: str
    priority: str  # low, normal, high, urgent
    created_at: str
    read: bool = False
    action_required: bool = False
    action_deadline: Optional[str] = None


class StepWorkflowEngine:
    """
    七步法工作流引擎

    核心功能：
    1. 状态机管理
    2. 流程控制
    3. 人机协同
    4. 超时监控
    5. 通知管理
    """

    # 状态转换规则
    TRANSITIONS = [
        # 启动转换
        StepTransition("start", StepStatus.PENDING, StepStatus.IN_PROGRESS),

        # AI完成转换
        StepTransition("ai_complete", StepStatus.IN_PROGRESS, StepStatus.PENDING_REVIEW,
                      timeout=5),  # 5分钟超时检查

        # 错误转换
        StepTransition("error", StepStatus.IN_PROGRESS, StepStatus.PAUSED),

        # 审核转换
        StepTransition("human_review", StepStatus.PENDING_REVIEW, StepStatus.UNDER_REVIEW,
                      timeout=1440),  # 24小时提醒
        StepTransition("request_revision", StepStatus.PENDING_REVIEW, StepStatus.IN_PROGRESS),

        # 审核完成转换
        StepTransition("approve", StepStatus.UNDER_REVIEW, StepStatus.COMPLETED),
        StepTransition("reject", StepStatus.UNDER_REVIEW, StepStatus.IN_PROGRESS),

        # 完成转换
        StepTransition("archive", StepStatus.COMPLETED, StepStatus.ARCHIVED),

        # 暂停恢复转换
        StepTransition("resume", StepStatus.PAUSED, StepStatus.IN_PROGRESS),
        StepTransition("terminate", StepStatus.PAUSED, StepStatus.TERMINATED),
    ]

    # 步骤依赖关系
    STEP_DEPENDENCIES = {
        StepType.STEP2_BLUEPRINT: [StepType.STEP1_DIAG],
        StepType.STEP3_STRATEGY: [StepType.STEP2_BLUEPRINT],
        StepType.STEP4_RESOURCE: [StepType.STEP3_STRATEGY],
        StepType.STEP5_EXECUTE: [StepType.STEP4_RESOURCE],
        StepType.STEP6_MONITOR: [StepType.STEP5_EXECUTE],  # 可与STEP5并行
        StepType.STEP7_REVIEW: [StepType.STEP5_EXECUTE],
    }

    # 步骤超时配置（分钟）
    STEP_TIMEOUTS = {
        StepType.STEP1_DIAG: 60,
        StepType.STEP2_BLUEPRINT: 120,
        StepType.STEP3_STRATEGY: 90,
        StepType.STEP4_RESOURCE: 60,
        StepType.STEP5_EXECUTE: 1440,  # 执行阶段可以很长
        StepType.STEP6_MONITOR: 30,    # 检查间隔
        StepType.STEP7_REVIEW: 90,
    }

    def __init__(self, storage_path: str = "data/workflow"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.active_steps: Dict[str, StepInstance] = {}
        self.timers: Dict[str, Timer] = {}
        self.notification_handlers: List[Callable] = []
        self.status_change_handlers: List[Callable] = []

        self._load_active_steps()

    def create_step(self, step_type: StepType, project_id: str,
                   input_data: Dict, **kwargs) -> StepInstance:
        """
        创建新步骤实例

        Args:
            step_type: 步骤类型
            project_id: 项目ID
            input_data: 输入数据

        Returns:
            StepInstance: 步骤实例
        """
        # 检查依赖
        if not self._check_dependencies(step_type, project_id):
            raise DependencyError(f"前置步骤未完成: {self.STEP_DEPENDENCIES.get(step_type)}")

        step_id = f"{step_type.value}-{uuid.uuid4().hex[:8]}"

        step = StepInstance(
            id=step_id,
            step_type=step_type,
            status=StepStatus.PENDING,
            project_id=project_id,
            input_data=input_data,
            max_revisions=kwargs.get('max_revisions', 5),
            metadata={
                'created_by': kwargs.get('created_by', 'system'),
                'priority': kwargs.get('priority', 'normal'),
            }
        )

        self.active_steps[step_id] = step
        self._save_step(step)

        return step

    def start_step(self, step_id: str) -> StepInstance:
        """启动步骤"""
        step = self._get_step(step_id)
        if not step:
            raise StepNotFoundError(f"步骤不存在: {step_id}")

        self._transition(step, "start")
        step.started_at = datetime.now().isoformat()

        # 设置超时检查
        self._schedule_timeout(step)

        self._save_step(step)
        return step

    def complete_ai_work(self, step_id: str, output_data: Dict) -> StepInstance:
        """AI完成工作"""
        step = self._get_step(step_id)
        if not step:
            raise StepNotFoundError(f"步骤不存在: {step_id}")

        step.output_data = output_data
        self._transition(step, "ai_complete")

        # 发送通知
        self._send_notification(
            type="step_complete",
            recipient=step.metadata.get('created_by', 'user'),
            title=f"步骤 {step.step_type.value} 已完成",
            content=f"AI已完成产出，等待审核",
            priority="normal",
            action_required=True,
            action_deadline=(datetime.now() + timedelta(hours=24)).isoformat()
        )

        self._save_step(step)
        return step

    def submit_for_review(self, step_id: str) -> StepInstance:
        """提交审核"""
        step = self._get_step(step_id)
        self._transition(step, "human_review")
        self._save_step(step)
        return step

    def review_step(self, step_id: str, decision: str, feedback: str = "") -> StepInstance:
        """
        审核步骤

        Args:
            step_id: 步骤ID
            decision: approve/reject/request_revision
            feedback: 反馈内容
        """
        step = self._get_step(step_id)

        if decision == "approve":
            self._transition(step, "approve")
            step.completed_at = datetime.now().isoformat()

        elif decision == "reject":
            if step.revision_count >= step.max_revisions:
                raise MaxRevisionError(f"已达到最大修订次数: {step.max_revisions}")
            self._transition(step, "reject")
            step.revision_count += 1
            step.metadata['last_feedback'] = feedback

        elif decision == "request_revision":
            if step.revision_count >= step.max_revisions:
                raise MaxRevisionError(f"已达到最大修订次数: {step.max_revisions}")
            self._transition(step, "request_revision")
            step.revision_count += 1
            step.metadata['last_feedback'] = feedback

        self._save_step(step)
        return step

    def archive_step(self, step_id: str) -> StepInstance:
        """归档步骤"""
        step = self._get_step(step_id)
        self._transition(step, "archive")

        # 从活跃列表移除
        if step_id in self.active_steps:
            del self.active_steps[step_id]

        self._save_step(step)
        return step

    def pause_step(self, step_id: str, reason: str) -> StepInstance:
        """暂停步骤"""
        step = self._get_step(step_id)

        # 取消定时器
        if step_id in self.timers:
            self.timers[step_id].cancel()
            del self.timers[step_id]

        step.metadata['pause_reason'] = reason
        step.metadata['paused_at'] = datetime.now().isoformat()

        self._save_step(step)
        return step

    def resume_step(self, step_id: str) -> StepInstance:
        """恢复步骤"""
        step = self._get_step(step_id)
        self._transition(step, "resume")

        # 重新设置超时
        self._schedule_timeout(step)

        self._save_step(step)
        return step

    def terminate_step(self, step_id: str, reason: str) -> StepInstance:
        """终止步骤"""
        step = self._get_step(step_id)

        # 取消定时器
        if step_id in self.timers:
            self.timers[step_id].cancel()
            del self.timers[step_id]

        step.metadata['terminate_reason'] = reason
        step.metadata['terminated_at'] = datetime.now().isoformat()

        self._transition(step, "terminate")
        self._save_step(step)
        return step

    def get_step_status(self, step_id: str) -> Optional[Dict]:
        """获取步骤状态"""
        step = self._get_step(step_id)
        if not step:
            return None

        return {
            "id": step.id,
            "type": step.step_type.value,
            "status": step.status.value,
            "project_id": step.project_id,
            "progress": self._calculate_progress(step),
            "revision_count": step.revision_count,
            "max_revisions": step.max_revisions,
            "created_at": step.created_at,
            "started_at": step.started_at,
            "completed_at": step.completed_at,
            "next_action": self._get_next_action(step),
        }

    def get_project_steps(self, project_id: str) -> List[Dict]:
        """获取项目的所有步骤"""
        steps = []
        for step in self.active_steps.values():
            if step.project_id == project_id:
                steps.append(self.get_step_status(step.id))
        return sorted(steps, key=lambda x: x['created_at'])

    def on_status_change(self, handler: Callable[[StepInstance, StepStatus, StepStatus], None]):
        """注册状态变更处理器"""
        self.status_change_handlers.append(handler)

    def on_notification(self, handler: Callable[[Notification], None]):
        """注册通知处理器"""
        self.notification_handlers.append(handler)

    def _transition(self, step: StepInstance, trigger: str):
        """执行状态转换"""
        old_status = step.status

        # 查找转换规则
        transition = None
        for t in self.TRANSITIONS:
            if t.trigger == trigger and t.from_status == old_status:
                transition = t
                break

        if not transition:
            raise InvalidTransitionError(
                f"无效的状态转换: {old_status.value} -> {trigger}"
            )

        # 执行转换
        step.status = transition.to_status

        # 触发回调
        for handler in self.status_change_handlers:
            try:
                handler(step, old_status, transition.to_status)
            except Exception as e:
                print(f"状态变更处理器错误: {e}")

        # 记录日志
        print(f"步骤 {step.id}: {old_status.value} -> {transition.to_status.value}")

    def _schedule_timeout(self, step: StepInstance):
        """设置超时检查"""
        timeout = self.STEP_TIMEOUTS.get(step.step_type, 60)

        def check_timeout():
            if step.id in self.active_steps:
                # 检查是否超时
                if step.status == StepStatus.IN_PROGRESS:
                    # AI处理超时
                    self._send_notification(
                        type="timeout_warning",
                        recipient="system",
                        title=f"步骤 {step.step_type.value} 处理超时",
                        content=f"AI处理时间超过 {timeout} 分钟",
                        priority="high"
                    )
                elif step.status == StepStatus.PENDING_REVIEW:
                    # 等待审核超时
                    self._send_notification(
                        type="review_reminder",
                        recipient=step.metadata.get('created_by', 'user'),
                        title=f"请审核步骤 {step.step_type.value} 的产出",
                        content=f"产出已完成，等待审核超过 {timeout} 分钟",
                        priority="normal",
                        action_required=True
                    )

        timer = Timer(timeout * 60, check_timeout)
        timer.start()
        self.timers[step.id] = timer

    def _send_notification(self, **kwargs):
        """发送通知"""
        notification = Notification(
            id=str(uuid.uuid4()),
            created_at=datetime.now().isoformat(),
            **kwargs
        )

        for handler in self.notification_handlers:
            try:
                handler(notification)
            except Exception as e:
                print(f"通知处理器错误: {e}")

    def _check_dependencies(self, step_type: StepType, project_id: str) -> bool:
        """检查前置依赖是否完成"""
        dependencies = self.STEP_DEPENDENCIES.get(step_type, [])
        if not dependencies:
            return True

        # 检查每个依赖步骤是否已完成
        for dep_type in dependencies:
            found = False
            for step in self.active_steps.values():
                if (step.step_type == dep_type and
                    step.project_id == project_id and
                    step.status in [StepStatus.COMPLETED, StepStatus.ARCHIVED]):
                    found = True
                    break
            if not found:
                return False

        return True

    def _calculate_progress(self, step: StepInstance) -> float:
        """计算步骤进度"""
        progress_map = {
            StepStatus.PENDING: 0.0,
            StepStatus.IN_PROGRESS: 30.0,
            StepStatus.PENDING_REVIEW: 70.0,
            StepStatus.UNDER_REVIEW: 80.0,
            StepStatus.COMPLETED: 100.0,
            StepStatus.ARCHIVED: 100.0,
            StepStatus.PAUSED: 50.0,
            StepStatus.TERMINATED: 0.0,
        }
        return progress_map.get(step.status, 0.0)

    def _get_next_action(self, step: StepInstance) -> Optional[Dict]:
        """获取下一步行动建议"""
        actions = {
            StepStatus.PENDING: {
                "action": "start",
                "description": "启动步骤",
                "command": f"/step-start {step.id}"
            },
            StepStatus.PENDING_REVIEW: {
                "action": "review",
                "description": "审核AI产出",
                "command": f"/step-review {step.id}"
            },
            StepStatus.COMPLETED: {
                "action": "archive",
                "description": "归档并沉淀知识",
                "command": f"/step-archive {step.id}"
            },
        }
        return actions.get(step.status)

    def _get_step(self, step_id: str) -> Optional[StepInstance]:
        """获取步骤实例"""
        return self.active_steps.get(step_id)

    def _save_step(self, step: StepInstance):
        """保存步骤到存储"""
        step_path = self.storage_path / f"{step.id}.json"
        with open(step_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(step), f, ensure_ascii=False, indent=2, cls=StepJSONEncoder)

    def _load_active_steps(self):
        """加载活跃的步骤"""
        for step_file in self.storage_path.glob("*.json"):
            try:
                with open(step_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    step = StepInstance(**data)
                    # 只加载非终态的步骤
                    if step.status not in [StepStatus.ARCHIVED, StepStatus.TERMINATED]:
                        self.active_steps[step.id] = step
                        # 恢复超时检查
                        if step.status in [StepStatus.IN_PROGRESS, StepStatus.PENDING_REVIEW]:
                            self._schedule_timeout(step)
            except Exception as e:
                print(f"加载步骤失败 {step_file}: {e}")


# 异常类
class StepNotFoundError(Exception):
    """步骤不存在"""
    pass


class DependencyError(Exception):
    """依赖错误"""
    pass


class InvalidTransitionError(Exception):
    """无效状态转换"""
    pass


class MaxRevisionError(Exception):
    """超过最大修订次数"""
    pass


# 使用示例
if __name__ == "__main__":
    engine = StepWorkflowEngine()

    # 创建步骤
    step = engine.create_step(
        step_type=StepType.STEP1_DIAG,
        project_id="proj-001",
        input_data={"requirement": "我想学习Python编程"}
    )

    print(f"创建步骤: {step.id}")

    # 启动步骤
    engine.start_step(step.id)
    print(f"启动步骤，状态: {engine.get_step_status(step.id)['status']}")

    # 模拟AI完成
    engine.complete_ai_work(step.id, {"report": "诊断报告内容"})
    print(f"AI完成，状态: {engine.get_step_status(step.id)['status']}")
