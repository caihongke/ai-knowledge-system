"""场景配置 - 全场景适配"""

from typing import Any


# 场景配置矩阵
SCENARIO_CONFIGS = {
    "novel_long": {
        "name": "网文长篇",
        "description": "80-100万字长篇小说",
        "rules": {
            "five_iron_laws": "required",  # 五大铁律必须开启
            "causality_lock": "strict",    # 因果锁严格模式
            "secret_pressure": "normal",   # 秘密压力正常
            "rhythm_redline": "normal",    # 节奏红线正常
            "industrial": "strict",        # 工业化严格
        },
        "params": {
            "gold_chapters": 3,
            "max_word_count": 3000,
            "min_word_count": 1500,
            "small_climax_interval": 5,
            "big_climax_interval": 30,
        },
        "milestones": {
            10: "黄金3章验证",
            30: "第一幕完成验证",
            50: "中期验证",
            80: "第二幕完成验证",
            150: "大结局验证",
        },
    },
    "short_drama": {
        "name": "短剧短篇",
        "description": "3-5分钟短视频",
        "rules": {
            "five_iron_laws": "required",
            "causality_lock": "loose",      # 宽松模式
            "secret_pressure": "loose",     # 短剧无需秘密压力
            "rhythm_redline": "strict",     # 节奏极严格
            "industrial": "normal",
        },
        "params": {
            "gold_seconds": 10,
            "min_climax_per_episode": 3,
            "climax_interval_seconds": 30,
            "max_duration_seconds": 300,
        },
        "milestones": {
            1: "单集完读率",
            5: "前5集留存",
            10: "黄金10集验证",
        },
    },
    "single_original": {
        "name": "单人原创",
        "description": "个人创作者使用",
        "rules": {
            "five_iron_laws": "required",
            "causality_lock": "normal",
            "secret_pressure": "normal",
            "rhythm_redline": "normal",
            "industrial": "loose",
        },
        "params": {
            "ai_enhance": False,
            "auto_review": False,
        },
    },
    "team_collaboration": {
        "name": "团队协作",
        "description": "多人协作创作",
        "rules": {
            "five_iron_laws": "required",
            "causality_lock": "strict",
            "secret_pressure": "strict",
            "rhythm_redline": "normal",
            "industrial": "strict",
        },
        "params": {
            "version_control": True,
            "quality_gate": True,
            "review_required": True,
        },
    },
    "ai_assisted": {
        "name": "AI辅助创作",
        "description": "AI生成+人工审核",
        "rules": {
            "five_iron_laws": "required",
            "causality_lock": "normal",
            "secret_pressure": "normal",
            "rhythm_redline": "normal",
            "industrial": "strict",
            "style_check": "enabled",       # AI风格检测
            "plagiarism_check": "enabled",  # 查重
            "closed_loop": "required",      # 封闭创作
        },
        "params": {
            "ai_enhance": True,
            "auto_review": True,
            "max_iteration_rounds": 5,
        },
    },
}


def get_scenario_config(scenario: str) -> dict:
    """获取场景配置"""
    return SCENARIO_CONFIGS.get(scenario, SCENARIO_CONFIGS["novel_long"])


def list_scenarios() -> list[dict]:
    """列出所有可用场景"""
    return [
        {"id": k, "name": v["name"], "description": v["description"]}
        for k, v in SCENARIO_CONFIGS.items()
    ]


def validate_scenario(scenario: str) -> bool:
    """验证场景是否有效"""
    return scenario in SCENARIO_CONFIGS