"""因果锁规则 - 章节因果链管理"""

from dataclasses import dataclass
from typing import Any


@dataclass
class CausalityNode:
    """因果节点"""
    chapter: int
    cause: str       # 原因
    effect: str      # 结果
    lock_type: str   # lock_type: "plot" / "character" / "emotion"
    strength: float  # 0-1


class CausalityLock:
    """因果锁规则

    核心原则：
    1. A事件必须导致B事件
    2. 反派行动必须有后果
    3. 金手指使用必须有代价
    4. 情感线必须有起伏
    """

    # 规则定义
    RULES = {
        "enabled": True,
        "strictness": "normal",  # loose / normal / strict
        "rules": [
            ("A事件必须导致B事件", "每章", "plot"),
            ("反派行动必须有后果", "每次", "character"),
            ("金手指使用必须有代价", "每次", "system"),
            ("情感线必须有起伏", "每10章", "emotion"),
        ],
    }

    @staticmethod
    def check_chapter_causality(chapters: list[dict]) -> dict:
        """检查章节因果链完整性

        Args:
            chapters: 章节列表，每章包含 cause, effect, lock_type

        Returns:
            检查结果
        """
        errors = []
        warnings = []

        for i, chapter in enumerate(chapters):
            ch_num = chapter.get("chapter", i + 1)

            # 检查是否有因果
            if not chapter.get("cause"):
                errors.append(f"第{ch_num}章: 缺少原因")

            if not chapter.get("effect"):
                errors.append(f"第{ch_num}章: 缺少结果")

            # 检查是否与上章因果相连
            if i > 0:
                prev_effect = chapters[i-1].get("effect", "")
                curr_cause = chapter.get("cause", "")

                # 简单检查：上章结果是否与本章原因有关联
                if prev_effect and curr_cause:
                    # 提取关键词检查关联（简化版）
                    prev_keywords = set(prev_effect.split())
                    curr_keywords = set(curr_cause.split())
                    overlap = prev_keywords & curr_keywords

                    if len(overlap) < 2:
                        warnings.append(
                            f"第{ch_num}章: 与第{i}章因果关联较弱 "
                            f"(上章结果: '{prev_effect[:20]}...', 本章原因: '{curr_cause[:20]}...')"
                        )

        return {
            "passed": len(errors) == 0,
            "score": max(0, 100 - len(errors) * 20 - len(warnings) * 5),
            "errors": errors,
            "warnings": warnings,
            "chapter_count": len(chapters),
        }

    @staticmethod
    def check_villain_consequence(villain_actions: list[dict]) -> dict:
        """检查反派行动后果

        Args:
            villain_actions: 反派行动列表，每项包含 action, consequence
        """
        errors = []

        for action in villain_actions:
            if not action.get("consequence"):
                errors.append(f"反派行动'{action.get('action', '未知')}'没有后果")

        return {
            "passed": len(errors) == 0,
            "score": max(0, 100 - len(errors) * 25),
            "errors": errors,
            "warnings": [],
        }

    @staticmethod
    def check_system_cost(system_uses: list[dict]) -> dict:
        """检查金手指使用代价

        Args:
            system_uses: 金手指使用记录，每项包含 use, cost
        """
        errors = []
        warnings = []

        for use in system_uses:
            if not use.get("cost"):
                warnings.append(f"金手指'{use.get('use', '未知')}'未设置明确代价")

        return {
            "passed": len(errors) == 0,
            "score": max(0, 100 - len(errors) * 30 - len(warnings) * 10),
            "errors": errors,
            "warnings": warnings,
        }

    @staticmethod
    def check_emotion_wave(emotion_events: list[dict]) -> dict:
        """检查情感线起伏

        Args:
            emotion_events: 情感事件列表，按时间顺序
        """
        errors = []
        warnings = []

        if len(emotion_events) < 2:
            warnings.append("情感事件过少，无法形成起伏")
            return {
                "passed": True,
                "score": 50,
                "errors": errors,
                "warnings": warnings,
            }

        # 检查是否有波峰波谷
        has_high = any(e.get("value", 5) > 7 for e in emotion_events)
        has_low = any(e.get("value", 5) < 4 for e in emotion_events)

        if not has_high:
            warnings.append("情感线缺少高潮")
        if not has_low:
            warnings.append("情感线缺少低谷")

        return {
            "passed": len(errors) == 0,
            "score": 100 if (has_high and has_low) else 60,
            "errors": errors,
            "warnings": warnings,
        }

    @classmethod
    def run_all(cls, story_data: dict) -> dict:
        """运行全部因果锁检查"""
        results = {
            "chapter_causality": cls.check_chapter_causality(
                story_data.get("chapters", [])
            ),
            "villain_consequence": cls.check_villain_consequence(
                story_data.get("villain_actions", [])
            ),
            "system_cost": cls.check_system_cost(
                story_data.get("system_uses", [])
            ),
            "emotion_wave": cls.check_emotion_wave(
                story_data.get("emotion_events", [])
            ),
        }

        # 汇总
        all_errors = []
        all_warnings = []
        total_score = 0

        for name, r in results.items():
            all_errors.extend(r.get("errors", []))
            all_warnings.extend(r.get("warnings", []))
            total_score += r.get("score", 0)

        avg_score = total_score / len(results)

        return {
            "passed": all(r.get("passed", False) for r in results.values()),
            "score": avg_score,
            "errors": all_errors,
            "warnings": all_warnings,
            "sub_results": results,
        }


def quick_check_causality(story_data: dict) -> dict:
    """快速检查因果锁"""
    return CausalityLock.run_all(story_data)