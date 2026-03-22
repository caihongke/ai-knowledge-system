"""项目配置管理 - 统一管理路径、常量和环境变量"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Config:
    """全局配置"""

    # 项目根目录
    ROOT_DIR = Path(__file__).parent.parent

    # 知识库路径
    KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
    NOTES_DIR = KNOWLEDGE_DIR / "notes"
    INDEX_FILE = KNOWLEDGE_DIR / "index.json"
    REVIEW_FILE = KNOWLEDGE_DIR / "review_schedule.json"

    # 日志与报告
    LOGS_DIR = ROOT_DIR / "logs"
    REPORTS_DIR = ROOT_DIR / "reports"
    STEPS_DIR = ROOT_DIR / "steps"

    # 飞书配置（从环境变量读取）
    FEISHU_APP_ID = os.getenv("APP_ID", "")
    FEISHU_APP_SECRET = os.getenv("APP_SECRET", "")

    # Claude API（从环境变量读取）
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

    # AI 调用限制
    AI_MONTHLY_LIMIT = 100  # 每月最大调用次数
    AI_CACHE_HOURS = 24     # AI 建议缓存有效期（小时）

    # 间隔复习 - 艾宾浩斯间隔天数
    REVIEW_INTERVALS = [1, 2, 4, 7, 15, 30]

    @classmethod
    def ensure_dirs(cls):
        """确保所有必要目录存在"""
        cls.NOTES_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        cls.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def summary(cls) -> dict:
        """返回配置摘要（不含敏感信息）"""
        return {
            "root_dir": str(cls.ROOT_DIR),
            "notes_dir": str(cls.NOTES_DIR),
            "index_file": str(cls.INDEX_FILE),
            "feishu_configured": bool(cls.FEISHU_APP_ID and cls.FEISHU_APP_SECRET),
            "ai_configured": bool(cls.ANTHROPIC_API_KEY),
            "ai_monthly_limit": cls.AI_MONTHLY_LIMIT,
            "review_intervals": cls.REVIEW_INTERVALS,
        }
