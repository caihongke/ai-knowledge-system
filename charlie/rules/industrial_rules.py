"""工业化规则 - 防崩防烂质量门禁"""

from dataclasses import dataclass
from typing import Any


class IndustrialRules:
    """工业化规则

    核心原则：
    1. 双赛道不混淆：网文vs短剧风格明确区分
    2. 无同质化：避免与现有爆款高度相似
    3. 结构可落地：从大纲到正文可执行
    4. 质量门禁：关键节点必须通过审核
    """

    # 规则定义
    RULES = {
        "enabled": True,
        "rules": [
            ("双赛道不混淆", "赛道"),
            ("无同质化", "差异化"),
            ("结构可落地", "执行"),
            ("质量门禁", "关键节点"),
        ],
    }

    # 赛道特征定义
    SCENARIO_FEATURES = {
        "novel_long": {
            "name": "网文长篇",
            "word_count": "80-100万字",
            "pace": "日更4000字",
            "features": [
                "系统激活→任务推进→打脸升级",
                "黄金3章定生死",
                "伏笔贯穿全文",
                "多层次冲突（个人→公司→世家）",
            ],
            "banned": [
                "开后宫无底线",
                "反社会价值观",
                "抄袭已有 IP",
            ],
        },
        "short_drama": {
            "name": "短剧短篇",
            "duration": "3-5分钟",
            "pace": "快节奏反转",
            "features": [
                "黄金10秒吸引",
                "每30秒一个爽点",
                "强情绪价值",
                "结尾强钩子",
            ],
            "banned": [
                "拖沓节奏",
                "无聊日常",
                "低俗擦边",
            ],
        },
    }

    @staticmethod
    def check_scenario_consistency(story_data: dict, scenario: str) -> dict:
        """检查赛道一致性

        Args:
            story_data: 故事数据
            scenario: 目标赛道
        """
        errors = []
        warnings = []

        features = IndustrialRules.SCENARIO_FEATURES.get(scenario, {})
        story_features = story_data.get("features", [])

        # 检查核心特征是否存在
        required_features = [
            "系统激活" if scenario == "novel_long" else "黄金10秒",
            "打脸升级" if scenario == "novel_long" else "快节奏反转",
        ]

        for rf in required_features:
            if rf not in story_features and rf not in str(story_data.get("outline", "")):
                warnings.append(f"缺少赛道核心特征: {rf}")

        return {
            "passed": len(errors) == 0,
            "score": max(0, 100 - len(errors) * 25 - len(warnings) * 10),
            "errors": errors,
            "warnings": warnings,
        }

    @staticmethod
    def check_novelty(story_data: dict, existing_works: list[str] = None) -> dict:
        """检查同质化

        Args:
            story_data: 故事数据
            existing_works: 已有的相似作品（可选）
        """
        errors = []
        warnings = []

        # 获取核心设定
        core_elements = story_data.get("core_elements", {})

        # 检查典型同质化特征
        common_patterns = [
            ("系统+分手+打脸", "经典套路，可适度使用但需差异化"),
            ("重生+2008+比特币", "已被用烂，建议创新"),
            ("神豪+无限消费", "同质化严重，需在人设/系统上创新"),
        ]

        story_str = str(core_elements).lower()

        for pattern, advice in common_patterns:
            if pattern.split("+")[0] in story_str:
                warnings.append(f"检测到常见套路'{pattern.split('+')[0]}': {advice}")

        return {
            "passed": len(errors) == 0,
            "score": 100 if len(warnings) == 0 else max(0, 100 - len(warnings) * 15),
            "errors": errors,
            "warnings": warnings,
        }

    @staticmethod
    def check_struct_feasibility(story_data: dict) -> dict:
        """检查结构可落地性

        Args:
            story_data: 故事数据
        """
        errors = []
        warnings = []

        # 检查必要元素
        required = [
            ("大纲", story_data.get("outline")),
            ("人设", story_data.get("characters")),
            ("结构", story_data.get("structure")),
        ]

        for name, value in required:
            if not value:
                errors.append(f"缺少必要元素: {name}")

        # 检查结构完整性
        structure = story_data.get("structure", {})
        acts = structure.get("acts", [])

        if len(acts) < 3 and story_data.get("scenario") == "novel_long":
            warnings.append("网文长篇建议三幕结构完整")

        return {
            "passed": len(errors) == 0,
            "score": max(0, 100 - len(errors) * 30 - len(warnings) * 10),
            "errors": errors,
            "warnings": warnings,
        }

    @staticmethod
    def check_quality_gate(story_data: dict, gate: str) -> dict:
        """检查质量门禁

        Args:
            story_data: 故事数据
            gate: 门禁节点 (outline/draft/manuscript)
        """
        errors = []

        if gate == "outline":
            # 大纲阶段检查
            if not story_data.get("outline"):
                errors.append("缺少大纲")
            if not story_data.get("theme", {}).get("core"):
                errors.append("缺少核心主题")
            if not story_data.get("protagonist", {}).get("short_term_goal"):
                errors.append("缺少主角短期目标")

        elif gate == "draft":
            # 草稿阶段检查
            if not story_data.get("chapters"):
                errors.append("缺少章节内容")
            # 可以添加更多草稿阶段检查

        elif gate == "manuscript":
            # 成稿阶段检查（最严格）
            # 运行完整五大铁律
            from charlie.rules.five_iron_laws import quick_check_five_laws
            iron_result = quick_check_five_laws(story_data)
            if not iron_result["passed"]:
                errors.extend(iron_result["errors"])

        return {
            "passed": len(errors) == 0,
            "score": max(0, 100 - len(errors) * 20),
            "errors": errors,
            "warnings": [],
        }

    @classmethod
    def run_all(cls, story_data: dict, scenario: str = "novel_long") -> dict:
        """运行全部工业化规则检查"""
        results = {
            "scenario_consistency": cls.check_scenario_consistency(story_data, scenario),
            "novelty": cls.check_novelty(story_data),
            "struct_feasibility": cls.check_struct_feasibility(story_data),
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


def quick_check_industrial(story_data: dict, scenario: str = "novel_long") -> dict:
    """快速检查工业化规则"""
    return IndustrialRules.run_all(story_data, scenario)