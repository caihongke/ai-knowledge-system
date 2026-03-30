"""五大铁律 - 查理体系核心基准
100%继承，不允许绕过
"""

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class CheckResult:
    """检查结果"""
    passed: bool
    score: float  # 0-100
    errors: list[str]
    warnings: list[str]
    details: dict[str, Any]


def evaluate_rule(check_fn: Callable, story_data: dict) -> tuple[bool, str]:
    """执行单条规则检查"""
    try:
        result = check_fn(story_data)
        if isinstance(result, bool):
            return result, ""
        elif isinstance(result, tuple):
            return result[0], result[1] if len(result) > 1 else ""
        return result, ""
    except Exception as e:
        return False, str(e)


class FiveIronLaws:
    """五大铁律 - 查理体系核心基准

    这是查理编剧体系的根基，100%继承：
    1. 主角主动驱动：主角必须有独立目标，不能被动等待系统/金手指推动
    2. 反派非工具人：反派必须有独立行动线和完整动机
    3. 因果闭环：章节必须有因果锁，全书必须因果回收
    4. 代价守恒：主角获得必须付出，爽点必须有代价
    5. 主题统一：全书必须围绕一个核心主题展开
    """

    @staticmethod
    def check_protagonist_driven(story_data: dict) -> CheckResult:
        """铁律1：主角主动驱动

        规则：
        - 主角必须有明确短期目标
        - 主角必须有明确中期目标
        - 目标不依赖系统奖励
        - 面临目标受阻时有主动应对
        """
        rules = [
            ("主角有明确短期目标", lambda d: d.get("protagonist", {}).get("short_term_goal")),
            ("主角有明确中期目标", lambda d: d.get("protagonist", {}).get("mid_term_goal")),
            ("目标不依赖系统奖励", lambda d: not d.get("protagonist", {}).get("goal_depends_on_system", True)),
            ("面临阻碍有主动应对", lambda d: d.get("protagonist", {}).get("has_active_response", False)),
        ]

        errors = []
        passed_count = 0

        for rule_name, check_fn in rules:
            result, msg = evaluate_rule(check_fn, story_data)
            if result:
                passed_count += 1
            else:
                errors.append(f"铁律1: {rule_name} - {msg or '未满足'}")

        score = passed_count / len(rules) * 100

        return CheckResult(
            passed=passed_count == len(rules),
            score=score,
            errors=errors if passed_count < len(rules) else [],
            warnings=[],
            details={"rules_checked": len(rules), "passed": passed_count},
        )

    @staticmethod
    def check_villain_not_tool(story_data: dict) -> CheckResult:
        """铁律2：反派非工具人

        规则：
        - 反派有独立行动线
        - 反派有明确动机
        - 反派有成长弧线
        - 反派结局有因果
        """
        villain = story_data.get("villains", [{}])[0] if story_data.get("villains") else {}

        rules = [
            ("反派有独立行动线", lambda d: d.get("villains") and any(v.get("action_line") for v in d.get("villains", []))),
            ("反派有明确动机", lambda d: villain.get("motivation")),
            ("反派有成长弧线", lambda d: villain.get("has_arc", False)),
            ("反派结局有因果", lambda d: villain.get("consequence")),
        ]

        errors = []
        passed_count = 0

        for rule_name, check_fn in rules:
            result, msg = evaluate_rule(check_fn, story_data)
            if result:
                passed_count += 1
            else:
                errors.append(f"铁律2: {rule_name} - {msg or '未满足'}")

        score = passed_count / len(rules) * 100

        return CheckResult(
            passed=passed_count == len(rules),
            score=score,
            errors=errors if passed_count < len(rules) else [],
            warnings=[],
            details={"rules_checked": len(rules), "passed": passed_count},
        )

    @staticmethod
    def check_causality_closed(story_data: dict) -> CheckResult:
        """铁律3：因果闭环

        规则：
        - 每章有因果链
        - 有伏笔埋入
        - 有伏笔回收
        - 终极结局有因果汇总
        """
        rules = [
            ("每章有因果链", lambda d: d.get("causality", {}).get("chapter_lock", False)),
            ("有伏笔埋入", lambda d: d.get("foreshadowing") and len(d.get("foreshadowing", [])) > 0),
            ("有伏笔回收", lambda d: d.get("foreshadowing回收") and len(d.get("foreshadowing回收", [])) > 0),
            ("终极结局有因果汇总", lambda d: d.get("causality", {}).get("final_summary", False)),
        ]

        errors = []
        passed_count = 0

        for rule_name, check_fn in rules:
            result, msg = evaluate_rule(check_fn, story_data)
            if result:
                passed_count += 1
            else:
                errors.append(f"铁律3: {rule_name} - {msg or '未满足'}")

        score = passed_count / len(rules) * 100

        return CheckResult(
            passed=passed_count == len(rules),
            score=score,
            errors=errors if passed_count < len(rules) else [],
            warnings=[],
            details={"rules_checked": len(rules), "passed": passed_count},
        )

    @staticmethod
    def check_cost_conservation(story_data: dict) -> CheckResult:
        """铁律4：代价守恒

        规则：
        - 主角有代价机制
        - 反派代价对称
        - 系统/金手指有代价
        - 情感线有代价
        """
        rules = [
            ("主角有代价机制", lambda d: d.get("cost_mechanism", {}).get("protagonist", False)),
            ("反派代价对称", lambda d: d.get("cost_mechanism", {}).get("villain", False)),
            ("系统/金手指有代价", lambda d: d.get("cost_mechanism", {}).get("system", False)),
            ("情感线有代价", lambda d: d.get("cost_mechanism", {}).get("emotion", False)),
        ]

        errors = []
        passed_count = 0

        for rule_name, check_fn in rules:
            result, msg = evaluate_rule(check_fn, story_data)
            if result:
                passed_count += 1
            else:
                errors.append(f"铁律4: {rule_name} - {msg or '未满足'}")

        score = passed_count / len(rules) * 100

        return CheckResult(
            passed=passed_count == len(rules),
            score=score,
            errors=errors if passed_count < len(rules) else [],
            warnings=[],
            details={"rules_checked": len(rules), "passed": passed_count},
        )

    @staticmethod
    def check_theme_unity(story_data: dict) -> CheckResult:
        """铁律5：主题统一

        规则：
        - 有明确核心主题
        - 有主题Slogan
        - 所有情节服务主题
        - 结局升华主题
        """
        rules = [
            ("有明确核心主题", lambda d: d.get("theme", {}).get("core")),
            ("有主题Slogan", lambda d: d.get("theme", {}).get("slogan")),
            ("所有情节服务主题", lambda d: d.get("theme", {}).get("all_serve", False)),
            ("结局升华主题", lambda d: d.get("theme", {}).get("climax升华", False)),
        ]

        errors = []
        passed_count = 0

        for rule_name, check_fn in rules:
            result, msg = evaluate_rule(check_fn, story_data)
            if result:
                passed_count += 1
            else:
                errors.append(f"铁律5: {rule_name} - {msg or '未满足'}")

        score = passed_count / len(rules) * 100

        return CheckResult(
            passed=passed_count == len(rules),
            score=score,
            errors=errors if passed_count < len(rules) else [],
            warnings=[],
            details={"rules_checked": len(rules), "passed": passed_count},
        )

    @classmethod
    def run_all(cls, story_data: dict) -> CheckResult:
        """运行全部五大铁律检查"""
        results = [
            cls.check_protagonist_driven(story_data),
            cls.check_villain_not_tool(story_data),
            cls.check_causality_closed(story_data),
            cls.check_cost_conservation(story_data),
            cls.check_theme_unity(story_data),
        ]

        all_errors = []
        all_warnings = []
        total_score = 0

        for r in results:
            all_errors.extend(r.errors)
            all_warnings.extend(r.warnings)
            total_score += r.score

        avg_score = total_score / len(results)

        all_passed = all(r.passed for r in results)

        return CheckResult(
            passed=all_passed,
            score=avg_score,
            errors=all_errors,
            warnings=all_warnings,
            details={
                "sub_results": [
                    {"law": f"铁律{i+1}", "passed": r.passed, "score": r.score}
                    for i, r in enumerate(results)
                ]
            },
        )


# 便捷函数
def quick_check_five_laws(story_data: dict) -> dict:
    """快速检查五大铁律，返回结果字典"""
    result = FiveIronLaws.run_all(story_data)
    return {
        "passed": result.passed,
        "score": result.score,
        "errors": result.errors,
        "warnings": result.warnings,
        "details": result.details,
    }