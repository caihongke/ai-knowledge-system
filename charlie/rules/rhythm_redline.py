"""节奏红线 - 工业化节奏管理"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ChapterMetrics:
    """单章指标"""
    chapter: int
    word_count: int
    hook_score: float      # 0-10
    climax_count: int      # 爽点数量
    conflict_count: int    # 冲突数量
    has_cliffhanger: bool  # 是否有钩子


class RhythmRedline:
    """节奏红线规则

    核心原则：
    1. 黄金3章定生死（网文）/ 黄金10秒定生死（短剧）
    2. 章章有爽点
    3. 每N章一小高潮
    4. 长篇阶段自检
    """

    # 规则定义 - 可配置
    RULES = {
        "enabled": True,
        "scenario_configs": {
            "novel_long": {
                "gold_chapters": 3,
                "min_climax_per_chapter": 1,
                "small_climax_interval": 5,
                "big_climax_interval": 30,
                "max_word_count": 3000,
                "min_word_count": 1500,
            },
            "short_drama": {
                "gold_seconds": 10,
                "min_climax_per_episode": 3,
                "climax_interval_seconds": 30,
                "max_duration_seconds": 300,
            },
        },
    }

    # 长篇专用规则
    LONG_FORM_RULES = {
        "milestone_checks": {
            10: {"name": "黄金3章验证", "checks": ["hook>8", "five_laws_pass"]},
            30: {"name": "第一幕完成", "checks": ["goal_established", "first_villain"]},
            50: {"name": "中期验证", "checks": ["first_climax", "conflict_escalation"]},
            80: {"name": "第二幕完成", "checks": ["identity_upgrade", "final_villain_appears"]},
            150: {"name": "大结局验证", "checks": ["all_causality_closed", "theme_crescendo"]},
        },
    }

    @staticmethod
    def check_gold_chapters(chapters: list[dict], scenario: str = "novel_long") -> dict:
        """检查黄金章是否达标

        Args:
            chapters: 前N章的内容
            scenario: 场景类型
        """
        config = RhythmRedline.RULES["scenario_configs"].get(scenario, {})
        gold_count = config.get("gold_chapters", 3)

        errors = []
        warnings = []

        for i in range(min(gold_count, len(chapters))):
            ch = chapters[i]
            ch_num = ch.get("chapter", i + 1)

            # 检查Hook
            if ch.get("hook_score", 10) < 7:
                errors.append(f"第{ch_num}章 Hook不足7分")

            # 检查爽点
            if ch.get("climax_count", 0) < 1:
                errors.append(f"第{ch_num}章 缺少核心爽点")

        return {
            "passed": len(errors) == 0,
            "score": max(0, 100 - len(errors) * 25),
            "errors": errors,
            "warnings": warnings,
        }

    @staticmethod
    def check_chapter_climax(chapter: ChapterMetrics) -> dict:
        """检查单章爽点密度

        Args:
            chapter: 章节指标
        """
        errors = []
        warnings = []

        # 爽点检查
        if chapter.climax_count < 1:
            errors.append(f"第{chapter.chapter}章 缺少爽点")

        # 字数检查
        if chapter.word_count > 3000:
            warnings.append(f"第{chapter.chapter}章 字数偏多({chapter.word_count})")
        elif chapter.word_count < 1500:
            warnings.append(f"第{chapter.chapter}章 字数偏少({chapter.word_count})")

        # 钩子检查
        if not chapter.has_cliffhanger:
            warnings.append(f"第{chapter.chapter}章 缺少结尾钩子")

        return {
            "passed": len(errors) == 0,
            "score": max(0, 100 - len(errors) * 30 - len(warnings) * 10),
            "errors": errors,
            "warnings": warnings,
        }

    @staticmethod
    def check_climax_interval(chapters: list[dict], interval: int = 5) -> dict:
        """检查高潮间隔

        Args:
            chapters: 章节列表
            interval: 小高潮间隔章数
        """
        errors = []
        warnings = []

        last_climax = 0
        for i, ch in enumerate(chapters):
            if ch.get("has_climax", False):
                if last_climax > 0:
                    gap = i + 1 - last_climax
                    if gap > interval * 1.5:
                        warnings.append(
                            f"第{i+1}章与上次高潮间隔{gap}章，超过{interval}章间隔"
                        )
                last_climax = i + 1

        return {
            "passed": len(errors) == 0,
            "score": 100 if len(warnings) == 0 else max(0, 100 - len(warnings) * 10),
            "errors": errors,
            "warnings": warnings,
        }

    @staticmethod
    def check_milestone(chapter: int, story_data: dict) -> dict:
        """检查里程碑

        Args:
            chapter: 当前章节
            story_data: 故事数据
        """
        milestones = RhythmRedline.LONG_FORM_RULES["milestone_checks"]

        for milestone_ch, milestone_info in milestones.items():
            if chapter >= milestone_ch:
                # 检查是否通过该里程碑
                checks = milestone_info.get("checks", [])
                # 这里简化处理，实际需要对应检查函数
                pass

        return {
            "passed": True,
            "score": 100,
            "errors": [],
            "warnings": [],
        }

    @classmethod
    def run_all(cls, story_data: dict, scenario: str = "novel_long") -> dict:
        """运行全部节奏红线检查"""
        chapters = story_data.get("chapters", [])

        results = {
            "gold_chapters": cls.check_gold_chapters(chapters[:5], scenario),
            "climax_interval": cls.check_climax_interval(chapters, 5),
        }

        # 汇总
        all_errors = []
        all_warnings = []
        total_score = 0

        for name, r in results.items():
            all_errors.extend(r.get("errors", []))
            all_warnings.extend(r.get("warnings", []))
            total_score += r.get("score", 0)

        avg_score = total_score / len(results) if results else 0

        return {
            "passed": all(r.get("passed", False) for r in results.values()),
            "score": avg_score,
            "errors": all_errors,
            "warnings": all_warnings,
            "sub_results": results,
        }


def quick_check_rhythm(story_data: dict, scenario: str = "novel_long") -> dict:
    """快速检查节奏"""
    return RhythmRedline.run_all(story_data, scenario)