"""审查引擎 - 风控区规则检验"""

from dataclasses import dataclass, field
from typing import Any
from charlie.rules import (
    FiveIronLaws,
    CausalityLock,
    SecretPressure,
    RhythmRedline,
    IndustrialRules,
)


@dataclass
class ReviewReport:
    """审查报告"""
    passed: bool
    level: str           # SAFE / NORMAL / WARNING / FATAL
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    sub_reports: dict[str, Any] = field(default_factory=dict)


class ReviewEngine:
    """审查引擎 - 规则检验

    工作流程：
    1. 先执行五大铁律（必须通过）
    2. 执行扩展规则（可配置）
    3. 风险分层评估
    """

    def __init__(self, scenario: str = "novel_long"):
        self.scenario = scenario
        self.five_laws = FiveIronLaws()

    def review(self, content: str = "", story_data: dict = None) -> ReviewReport:
        """执行完整审查

        Args:
            content: 作品内容文本
            story_data: 故事结构数据

        Returns:
            ReviewReport 审查报告
        """
        story_data = story_data or {}

        # 阶段1：五大铁律检验（必须通过）
        iron_result = self.five_laws.run_all(story_data)

        if not iron_result.passed:
            return ReviewReport(
                passed=False,
                level="FATAL",
                errors=iron_result.errors,
                suggestions=self._generate_suggestions(iron_result.errors),
                metrics={"five_laws_score": iron_result.score},
            )

        # 阶段2：扩展规则检验
        sub_reports = {
            "causality": CausalityLock.run_all(story_data),
            "secret_pressure": SecretPressure.run_all(story_data),
            "rhythm": RhythmRedline.run_all(story_data, self.scenario),
            "industrial": IndustrialRules.run_all(story_data, self.scenario),
        }

        # 收集所有错误和警告
        all_errors = []
        all_warnings = []
        total_score = 0

        for name, report in sub_reports.items():
            all_errors.extend(report.get("errors", []))
            all_warnings.extend(report.get("warnings", []))
            total_score += report.get("score", 0)

        avg_score = total_score / len(sub_reports) if sub_reports else 100

        # 阶段3：风险分层
        level = self._assess_risk_level(all_errors, all_warnings, iron_result.score)

        passed = level in ["SAFE", "NORMAL"]

        return ReviewReport(
            passed=passed,
            level=level,
            errors=all_errors,
            warnings=all_warnings,
            suggestions=self._generate_suggestions(all_errors + all_warnings),
            metrics={
                "five_laws_score": iron_result.score,
                "expansion_score": avg_score,
                "total_score": (iron_result.score + avg_score) / 2,
            },
            sub_reports=sub_reports,
        )

    def _assess_risk_level(self, errors: list[str], warnings: list[str], iron_score: float) -> str:
        """风险分层评估

        Returns:
            SAFE: 五小铁律全绿，无错误
            NORMAL: 有警告但无错误
            WARNING: 有少量错误但可修复
            FATAL: 五大铁律未通过或有严重错误
        """
        if iron_score < 80:
            return "FATAL"

        if errors:
            if len(errors) <= 2:
                return "WARNING"
            else:
                return "FATAL"

        if warnings:
            if len(warnings) <= 3:
                return "NORMAL"
            else:
                return "WARNING"

        return "SAFE"

    def _generate_suggestions(self, issues: list[str]) -> list[str]:
        """根据问题生成修改建议"""
        suggestions = []

        # 分类生成建议
        for issue in issues:
            if "铁律1" in issue or "主角" in issue:
                suggestions.append("建议强化主角的主动性和独立目标")
            elif "铁律2" in issue or "反派" in issue:
                suggestions.append("建议为反派增加独立行动线和动机")
            elif "铁律3" in issue or "因果" in issue:
                suggestions.append("建议检查章节因果链的连贯性")
            elif "铁律4" in issue or "代价" in issue:
                suggestions.append("建议为主角获得增加代价机制")
            elif "铁律5" in issue or "主题" in issue:
                suggestions.append("建议强化核心主题的贯穿")
            elif "爽点" in issue:
                suggestions.append("建议增加打脸爽点密度")
            elif "钩子" in issue:
                suggestions.append("建议在章节结尾增加悬念钩子")
            else:
                suggestions.append(f"需要处理: {issue}")

        return suggestions

    def quick_review(self, story_data: dict) -> dict:
        """快速审查 - 返回简化结果"""
        report = self.review(story_data=story_data)
        return {
            "passed": report.passed,
            "level": report.level,
            "score": report.metrics.get("total_score", 0),
            "error_count": len(report.errors),
            "warning_count": len(report.warnings),
            "errors": report.errors[:5],  # 只返回前5个
        }


def quick_review(story_data: dict, scenario: str = "novel_long") -> dict:
    """便捷审查入口"""
    engine = ReviewEngine(scenario)
    return engine.quick_review(story_data)