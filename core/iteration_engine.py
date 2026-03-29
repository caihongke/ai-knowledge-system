"""IterationEngine - 迭代优化引擎
负责差距分析和改进方案生成
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.models import CreationSession, IterationRecord
from core.story_analyzer import AnalysisReport


@dataclass
class GapAnalysis:
    """差距分析结果"""

    dimensions: list[str]  # 分析维度
    current_scores: dict[str, float]
    target_scores: dict[str, float]
    gaps: dict[str, float]  # 差距值
    priority: list[tuple]   # (维度, 差距) 排序


@dataclass
class ImprovementPlan:
    """改进方案"""

    strategies: list[dict[str, Any]]  # 策略列表
    expected_improvement: dict[str, float]
    components_needed: list[str]
    estimated_effort: str  # 工作量估计
    risk_level: str  # 低/中/高


class IterationEngine:
    """迭代优化引擎

    核心流程：
    1. 差距分析 (当前 vs 目标)
    2. 根因诊断
    3. 策略生成
    4. 方案排序
    5. 执行跟踪
    """

    # 行业标准目标值
    INDUSTRY_STANDARDS = {
        "short": {
            "hook_score": 8.0,
            "conflict_density": 0.8,  # 每千字0.8个冲突点
            "structure_compliance": 85.0,
            "emotion_variance": 3.0,  # 情绪波动幅度
        },
        "long": {
            "hook_score": 7.0,
            "conflict_density": 0.5,
            "structure_compliance": 80.0,
            "cliffhanger_quality": 8.0,  # 断章质量
        },
    }

    # 改进策略库
    IMPROVEMENT_STRATEGIES = {
        "hook_score": [
            {
                "name": "悬念强化",
                "action": "在开头加入反常识观点或悬念",
                "effort": "低",
                "impact": "高",
            },
            {
                "name": "冲突前置",
                "action": "将核心冲突提前到前30秒/300字",
                "effort": "中",
                "impact": "高",
            },
        ],
        "conflict_density": [
            {
                "name": "冲突注入",
                "action": "每15秒/每章设置一个冲突点",
                "effort": "中",
                "impact": "高",
            },
        ],
        "structure_compliance": [
            {
                "name": "结构梳理",
                "action": "使用三幕式模板重新规划",
                "effort": "高",
                "impact": "中",
            },
        ],
    }

    def __init__(self, track: str = "short"):
        self.track = track
        self.standards = self.INDUSTRY_STANDARDS.get(track, self.INDUSTRY_STANDARDS["short"])

    def analyze_gap(
        self,
        report: AnalysisReport,
        custom_targets: dict[str, float] | None = None,
    ) -> GapAnalysis:
        """分析创作与目标的差距

        Args:
            report: 拉片分析报告
            custom_targets: 自定义目标（覆盖默认值）

        Returns:
            GapAnalysis 差距分析

        """
        targets = custom_targets or self.standards

        # 提取当前分数
        current = {
            "hook_score": report.hook_score,
            "conflict_density": report.conflict_density,
            "structure_compliance": report.structure_compliance,
        }

        # 计算差距
        gaps = {}
        for dim in targets.keys():
            if dim in current:
                gaps[dim] = targets[dim] - current[dim]

        # 按差距大小排序（差距大的优先）
        priority = sorted(gaps.items(), key=lambda x: -x[1] if x[1] > 0 else float("-inf"))

        return GapAnalysis(
            dimensions=list(targets.keys()),
            current_scores=current,
            target_scores=targets,
            gaps=gaps,
            priority=priority,
        )

    def generate_improvement_plan(
        self,
        gap: GapAnalysis,
        max_strategies: int = 3,
    ) -> ImprovementPlan:
        """生成改进方案

        Args:
            gap: 差距分析结果
            max_strategies: 最大策略数量

        Returns:
            ImprovementPlan 改进方案

        """
        strategies = []
        components_needed = []

        # 选择前N个需要改进的维度
        for dim, gap_value in gap.priority[:max_strategies]:
            if gap_value <= 0:  # 已达到目标，跳过
                continue

            # 获取该维度的改进策略
            dim_strategies = self.IMPROVEMENT_STRATEGIES.get(dim, [])

            for s in dim_strategies:
                strategy = {
                    "dimension": dim,
                    "name": s["name"],
                    "action": s["action"],
                    "effort": s["effort"],
                    "impact": s["impact"],
                    "gap_to_address": gap_value,
                }
                strategies.append(strategy)

                # 识别需要的组件
                if "人设" in s["action"]:
                    components_needed.append("character")
                elif "桥段" in s["action"]:
                    components_needed.append("scene")
                elif "爽点" in s["action"]:
                    components_needed.append("payoff")

        # 计算预期改进
        expected_improvement = {}
        for dim in gap.dimensions:
            if dim in gap.gaps and gap.gaps[dim] > 0:
                # 预期改进 = 当前 + 差距的60%
                expected_improvement[dim] = gap.current_scores[dim] + gap.gaps[dim] * 0.6

        # 评估风险
        high_effort_count = sum(1 for s in strategies if s["effort"] == "高")
        risk_level = "高" if high_effort_count >= 2 else "中" if high_effort_count == 1 else "低"

        # 工作量估计
        effort_levels = [s["effort"] for s in strategies]
        if "高" in effort_levels:
            estimated_effort = "2-3天"
        elif "中" in effort_levels:
            estimated_effort = "1-2天"
        else:
            estimated_effort = "半天-1天"

        return ImprovementPlan(
            strategies=strategies,
            expected_improvement=expected_improvement,
            components_needed=list(set(components_needed)),
            estimated_effort=estimated_effort,
            risk_level=risk_level,
        )

    def create_iteration_record(
        self,
        session_id: str,
        trigger: str,
        gap: GapAnalysis,
        plan: ImprovementPlan,
    ) -> IterationRecord:
        """创建迭代记录

        Args:
            session_id: 项目ID
            trigger: 触发原因
            gap: 差距分析
            plan: 改进方案

        Returns:
            IterationRecord

        """
        return IterationRecord(
            iteration_id=f"iter_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            trigger=trigger,
            gap_analysis=gap.gaps,
            improvement_plan=[s["name"] for s in plan.strategies],
            created_at=datetime.now().isoformat(),
        )

    def suggest_iteration_cycle(
        self,
        session: CreationSession,
        force: bool = False,
    ) -> dict[str, Any]:
        """建议迭代周期

        规则：
        - 短视频：完成即分析
        - 网文：每10章/每卷结束分析

        Args:
            session: 创作会话
            force: 强制分析

        Returns:
            建议结果

        """
        if session.track == "short":
            # 短视频：有草稿即可分析
            if session.drafts or force:
                return {
                    "should_iterate": True,
                    "reason": "剧本已完成，建议立即分析",
                    "next_step": "运行: akm 分析 拉片 {项目ID}",
                }

        else:  # long
            # 网文：每卷结束或强制
            iterations_count = len(session.iterations)
            volumes_count = len(session.outline.get("volumes", []))

            if force or (volumes_count > 0 and iterations_count < volumes_count):
                return {
                    "should_iterate": True,
                    "reason": f"第{iterations_count + 1}卷完成，建议进行分析",
                    "next_step": "运行: akm 分析 拉片 {项目ID}",
                }

        return {
            "should_iterate": False,
            "reason": "暂未达到迭代节点",
            "progress": f"已完成 {len(session.drafts)} 个草稿 / {len(session.iterations)} 次迭代",
        }

    def track_improvement(
        self,
        previous_report: AnalysisReport,
        current_report: AnalysisReport,
    ) -> dict[str, Any]:
        """跟踪改进效果

        Args:
            previous_report: 上次分析报告
            current_report: 本次分析报告

        Returns:
            改进追踪结果

        """
        improvements = {}

        metrics = [
            ("hook_score", previous_report.hook_score, current_report.hook_score),
            ("conflict_density", previous_report.conflict_density, current_report.conflict_density),
            ("structure_compliance", previous_report.structure_compliance, current_report.structure_compliance),
        ]

        for name, prev, curr in metrics:
            delta = curr - prev
            improvements[name] = {
                "previous": prev,
                "current": curr,
                "delta": delta,
                "improved": delta > 0,
            }

        # 计算总体改进率
        total_delta = sum(imp["delta"] for imp in improvements.values())
        avg_improvement = total_delta / len(improvements)

        return {
            "improvements": improvements,
            "average_improvement": avg_improvement,
            "iteration_success": avg_improvement > 0,
            "recommendation": "继续优化" if avg_improvement > 0 else "调整策略",
        }

    def generate_personal_report(
        self,
        sessions: list[CreationSession],
        reports: list[AnalysisReport],
    ) -> str:
        """生成个人创作报告

        Args:
            sessions: 所有创作会话
            reports: 所有分析报告

        Returns:
            报告文本

        """
        if not sessions:
            return "暂无创作数据"

        # 统计
        total_works = len(sessions)
        published = sum(1 for s in sessions if s.status == "published")
        avg_hook = sum(r.hook_score for r in reports) / len(reports) if reports else 0
        avg_structure = sum(r.structure_compliance for r in reports) / len(reports) if reports else 0

        # 标签统计
        all_tags = []
        for s in sessions:
            all_tags.append(s.genre)

        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        top_genres = sorted(tag_counts.items(), key=lambda x: -x[1])[:3]

        report = f"""# 个人创作报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 一、创作统计

| 指标 | 数值 |
|------|------|
| 总作品数 | {total_works} |
| 已发布 | {published} |
| 创作中 | {total_works - published} |
| 平均Hook得分 | {avg_hook:.1f}/10 |
| 平均结构完整度 | {avg_structure:.0f}% |

## 二、擅长类型

"""

        for genre, count in top_genres:
            report += f"- {genre}: {count} 部作品\n"

        report += f"""

## 三、能力雷达

- Hook设计: {'█' * int(avg_hook/2)} {avg_hook:.1f}/10
- 冲突构建: {'█' * int((sum(r.conflict_density for r in reports)/len(reports)*10) if reports else 0)} {reports[0].conflict_density:.2f if reports else 0}/1.0
- 结构把控: {'█' * int(avg_structure/10)} {avg_structure:.0f}%

## 四、改进建议

基于近期创作数据分析：

"""

        # 找出最弱的维度
        weak_areas = []
        if avg_hook < 7:
            weak_areas.append("Hook设计需要加强，建议多参考爆款开头")
        if avg_structure < 70:
            weak_areas.append("结构把控有待提升，建议使用三幕式模板")

        if weak_areas:
            for area in weak_areas:
                report += f"- {area}\n"
        else:
            report += "- 整体表现良好，继续保持！\n"

        report += f"""

## 五、下阶段目标

1. Hook得分提升至 {min(avg_hook + 1, 10):.0f}/10
2. 结构完整度达到 {min(avg_structure + 10, 100):.0f}%
3. 完成 {total_works + 1} 部作品

---
*报告由IterationEngine自动生成*
"""

        return report


# 便捷函数
def quick_improve(content: str, title: str, track: str = "short") -> dict:
    """快速改进建议"""
    from core.story_analyzer import StoryAnalyzer

    # 分析
    analyzer = StoryAnalyzer()
    report = analyzer.analyze(content, title, track)

    # 迭代
    engine = IterationEngine(track=track)
    gap = engine.analyze_gap(report)
    plan = engine.generate_improvement_plan(gap)

    return {
        "gaps": gap.gaps,
        "strategies": [s["name"] for s in plan.strategies],
        "estimated_effort": plan.estimated_effort,
        "top_priority": gap.priority[0] if gap.priority else None,
    }


if __name__ == "__main__":
    # 测试
    engine = IterationEngine(track="short")

    # 模拟报告
    from core.models import AnalysisReport
    report = AnalysisReport(
        source="测试",
        source_title="测试作品",
        hook_score=6.0,
        conflict_density=0.3,
        structure_compliance=60.0,
    )

    gap = engine.analyze_gap(report)
    print(f"差距分析: {gap.gaps}")

    plan = engine.generate_improvement_plan(gap)
    print(f"改进策略: {[s['name'] for s in plan.strategies]}")
