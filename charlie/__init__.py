"""查理编剧体系 - 人机协同全能创作系统
Charlie Screenwriting System - Human-AI Collaborative Creation

核心特性：
- 100% 继承五大铁律 (不可变基准)
- 规则可插拔 (创意区与风控区分离)
- 全场景适配 (网文长篇/短剧短篇/单人原创/团队协作/AI辅助)
- 百万字不崩 (里程碑自检+预警监控)
"""

from charlie.engine import (
    CreativeEngine,
    ReviewEngine,
    ReviewReport,
    IterationEngine,
    LongFormMonitor,
)

from charlie.rules import (
    FiveIronLaws,
    quick_check_five_laws,
    CausalityLock,
    quick_check_causality,
    SecretPressure,
    quick_check_secret_pressure,
    RhythmRedline,
    quick_check_rhythm,
    IndustrialRules,
    quick_check_industrial,
)

from charlie.scenarios import (
    get_scenario_config,
    list_scenarios,
    validate_scenario,
)

__version__ = "1.0.0"

__all__ = [
    # 版本
    "__version__",
    # 引擎层
    "CreativeEngine",
    "ReviewEngine",
    "ReviewReport",
    "IterationEngine",
    "LongFormMonitor",
    # 规则层
    "FiveIronLaws",
    "quick_check_five_laws",
    "CausalityLock",
    "quick_check_causality",
    "SecretPressure",
    "quick_check_secret_pressure",
    "RhythmRedline",
    "quick_check_rhythm",
    "IndustrialRules",
    "quick_check_industrial",
    # 场景层
    "get_scenario_config",
    "list_scenarios",
    "validate_scenario",
]


# 便捷入口
def create(scenario: str = "novel_long"):
    """创建指定场景的创作引擎"""
    config = get_scenario_config(scenario)
    return {
        "creative": CreativeEngine(scenario),
        "review": ReviewEngine(scenario),
        "iteration": IterationEngine(scenario),
        "monitor": LongFormMonitor(),
        "config": config,
    }


def review(story_data: dict, scenario: str = "novel_long") -> dict:
    """快速审查入口"""
    engine = ReviewEngine(scenario)
    return engine.quick_review(story_data)


def checkpoint(chapter: int, story_data: dict, all_chapters: list = None) -> dict:
    """里程碑检查入口"""
    monitor = LongFormMonitor()
    return monitor.get_progress_report(chapter, story_data, all_chapters)