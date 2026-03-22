"""数据模型定义"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List


@dataclass
class Note:
    """知识库笔记"""

    id: str                              # 唯一标识，格式: 20260322_143000
    title: str                           # 笔记标题
    tags: List[str] = field(default_factory=list)  # 标签列表
    category: str = "default"            # 分类
    created_at: str = ""                 # 创建时间 ISO格式
    updated_at: str = ""                 # 更新时间 ISO格式
    file_path: str = ""                  # Markdown 文件相对路径

    def __post_init__(self):
        now = datetime.now().isoformat(timespec="seconds")
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Note":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @staticmethod
    def generate_id() -> str:
        """生成基于时间戳的唯一ID"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
