"""秘密压力曲线 - 核心秘密管理"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Secret:
    """秘密定义"""
    id: str
    name: str           # 秘密名称
    content: str        # 秘密内容（密级）
    reveal_chapter: int # 揭示章节（0=不揭示）
    pressure_curve: list[tuple[int, float]]  # (章节, 压力值)


class SecretPressure:
    """秘密压力曲线规则

    核心原则：
    1. 核心秘密不暴露：全书不能在任何章节明确揭示核心秘密
    2. 秘密分阶段解锁：每30章为一个阶段逐步释放
    3. 秘密压力递增：随着情节推进，秘密的压力应该递增
    """

    # 规则定义
    RULES = {
        "enabled": True,
        "rules": [
            ("核心秘密不暴露", "全书"),
            ("秘密分阶段解锁", "每30章"),
            ("秘密压力递增", "按比例"),
        ],
    }

    # 秘密分类与压力阈值
    SECRET_TYPES = {
        "core": {
            "description": "核心秘密",
            "max_reveal_chapter": 999,  # 接近大结局
            "pressure_growth": "exponential",  # 指数增长
        },
        "major": {
            "description": "主要秘密",
            "max_reveal_chapter": 80,
            "pressure_growth": "linear",
        },
        "minor": {
            "description": "次要秘密",
            "max_reveal_chapter": 30,
            "pressure_growth": "linear",
        },
    }

    @staticmethod
    def check_secret_not_exposed(story_content: str, secrets: list[dict]) -> dict:
        """检查核心秘密是否暴露

        Args:
            story_content: 故事全文
            secrets: 秘密列表
        """
        errors = []

        for secret in secrets:
            secret_type = secret.get("type", "minor")
            content = secret.get("content", "")

            if secret_type == "core":
                # 核心秘密：不应该在文中明确揭示
                if content in story_content:
                    errors.append(f"核心秘密'{secret.get('name')}'可能在正文中暴露")

                # 检查关键词
                for keyword in secret.get("keywords", []):
                    if keyword in story_content:
                        errors.append(f"核心秘密关键词'{keyword}'可能暴露")

        return {
            "passed": len(errors) == 0,
            "score": max(0, 100 - len(errors) * 30),
            "errors": errors,
            "warnings": [],
        }

    @staticmethod
    def check_phase_unlock(chapters: int, secrets: list[dict]) -> dict:
        """检查秘密分阶段解锁

        Args:
            chapters: 当前章节数
            secrets: 秘密列表
        """
        warnings = []

        for secret in secrets:
            reveal_chapter = secret.get("reveal_chapter", 0)

            if reveal_chapter > 0:
                # 计算应该在哪一阶段揭示
                expected_phase = (reveal_chapter // 30) + 1
                actual_phase = chapters // 30 + 1

                if actual_phase > expected_phase + 1:
                    warnings.append(
                        f"秘密'{secret.get('name')}'应在第{expected_phase*30}章前揭示，"
                        f"当前第{chapters}章尚未揭示"
                    )

        return {
            "passed": len(warnings) == 0,
            "score": 100 if len(warnings) == 0 else max(0, 100 - len(warnings) * 15),
            "errors": [],
            "warnings": warnings,
        }

    @staticmethod
    def check_pressure_curve(chapters: int, secrets: list[dict]) -> dict:
        """检查秘密压力曲线

        Args:
            chapters: 当前章节数
            secrets: 秘密列表
        """
        errors = []
        warnings = []

        for secret in secrets:
            pressure_curve = secret.get("pressure_curve", [])

            if not pressure_curve:
                warnings.append(f"秘密'{secret.get('name')}'未设置压力曲线")
                continue

            # 检查压力是否递增（简化版）
            prev_pressure = 0
            for ch, pressure in pressure_curve:
                if ch <= chapters and pressure < prev_pressure:
                    warnings.append(
                        f"秘密'{secret.get('name')}'在第{ch}章压力应该递增但下降了"
                    )
                prev_pressure = pressure

        return {
            "passed": len(errors) == 0,
            "score": 100 if len(errors) == 0 else max(0, 100 - len(errors) * 20),
            "errors": errors,
            "warnings": warnings,
        }

    @classmethod
    def run_all(cls, story_data: dict) -> dict:
        """运行全部秘密压力检查"""
        story_content = story_data.get("full_content", "")
        chapters = story_data.get("chapters", 0)
        secrets = story_data.get("secrets", [])

        results = {
            "secret_not_exposed": cls.check_secret_not_exposed(story_content, secrets),
            "phase_unlock": cls.check_phase_unlock(chapters, secrets),
            "pressure_curve": cls.check_pressure_curve(chapters, secrets),
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


def quick_check_secret_pressure(story_data: dict) -> dict:
    """快速检查秘密压力"""
    return SecretPressure.run_all(story_data)