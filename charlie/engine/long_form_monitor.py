"""长篇监控 - 百万字不崩"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CheckpointReport:
    """里程碑报告"""
    checkpoint: int
    name: str
    passed: bool
    score: float
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


@dataclass
class WarningSignal:
    """预警信号"""
    chapter: int
    type: str
    severity: str
    message: str
    suggestion: str


class LongFormMonitor:
    """长篇监控 - 百万字不崩"""

    CHECKPOINTS = {
        10: {"name": "黄金3章验证", "checks": ["hook_score", "five_laws"]},
        30: {"name": "第一幕完成", "checks": ["protagonist_goal", "first_villain"]},
        50: {"name": "中期验证", "checks": ["first_climax", "villain_counter"]},
        80: {"name": "第二幕完成", "checks": ["identity_upgrade", "final_villain"]},
        150: {"name": "大结局验证", "checks": ["causality_closed", "theme_crescendo"]},
    }

    WARNING_THRESHOLDS = {
        "water_content": 2000,
        "climax_density": 0.5,
        "conflict_gap": 3,
    }

    def check_checkpoint(self, chapter: int, story_data: dict, all_chapters: list = None) -> CheckpointReport:
        """检查里程碑"""
        target_ch = 0
        target_info = None
        for ch, info in self.CHECKPOINTS.items():
            if ch <= chapter and ch > target_ch:
                target_ch = ch
                target_info = info

        if not target_info:
            return CheckpointReport(chapter, "未到里程碑", True, 100)

        # 简化检查
        from charlie.rules import quick_check_five_laws
        result = quick_check_five_laws(story_data)

        return CheckpointReport(
            checkpoint=target_ch,
            name=target_info["name"],
            passed=result["passed"],
            score=result["score"],
            errors=result.get("errors", []),
        )

    def check_warnings(self, chapter: int, chapter_data: dict, recent: list = None) -> list:
        """检查预警信号"""
        warnings = []
        word_count = chapter_data.get("word_count", 0)
        if word_count > self.WARNING_THRESHOLDS["water_content"]:
            warnings.append(WarningSignal(chapter, "water", "medium",
                f"字数{word_count}偏高", "建议精简"))
        return warnings

    def get_progress_report(self, chapter: int, story_data: dict, all_chapters: list = None) -> dict:
        """进度报告"""
        report = self.check_checkpoint(chapter, story_data, all_chapters)
        return {
            "current_chapter": chapter,
            "milestone": {"name": report.name, "passed": report.passed, "score": report.score},
            "warnings": [],
            "health_score": report.score,
            "status": "healthy" if report.score >= 80 else "warning",
        }


def quick_monitor(chapter: int, story_data: dict, all_chapters: list = None) -> dict:
    """便捷入口"""
    return LongFormMonitor().get_progress_report(chapter, story_data, all_chapters)