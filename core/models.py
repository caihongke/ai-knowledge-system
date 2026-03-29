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



# ==================== 创作系统模型 ====================

from typing import Optional, Dict, Any


@dataclass
class DraftVersion:
    """草稿版本"""
    version: int
    content: str
    created_at: str
    change_summary: str = ""


@dataclass
class Character:
    """角色设定"""
    id: str
    name: str
    profile: str  # 人物小传
    traits: List[str] = field(default_factory=list)  # 性格特征
    arc: Optional[str] = None  # 成长弧线
    relationships: Dict[str, str] = field(default_factory=dict)  # 人物关系

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "profile": self.profile,
            "traits": self.traits,
            "arc": self.arc,
            "relationships": self.relationships
        }


@dataclass
class PlotPoint:
    """剧情节点"""
    id: str
    position: float  # 位置 (0-1 表示全剧进度)
    description: str
    emotion_value: float = 0.5  # 情绪值 (0-1)
    conflict_level: str = "中"  # 低/中/高
    characters_involved: List[str] = field(default_factory=list)


@dataclass
class AnalysisReport:
    """拉片分析报告"""
    source: str  # 自有作品 | 竞品作品
    source_title: str

    # 核心指标
    hook_score: float = 0.0  # Hook吸引力 (0-10)
    conflict_density: float = 0.0  # 冲突密度 (每15秒/章)
    emotion_curve: List[float] = field(default_factory=list)  # 15节点情绪坐标
    structure_compliance: float = 0.0  # 结构完整度 (0-100%)

    # 改进建议
    improvement_suggestions: List[str] = field(default_factory=list)

    # 元数据
    created_at: str = ""
    analyzer: str = "story-analyzer"


@dataclass
class IterationRecord:
    """迭代记录"""
    iteration_id: str
    trigger: str  # 触发原因
    gap_analysis: Dict[str, float] = field(default_factory=dict)
    improvement_plan: List[str] = field(default_factory=list)
    changes_made: List[str] = field(default_factory=list)
    created_at: str = ""


@dataclass
class CreationSession:
    """创作会话记录"""
    id: str
    track: str  # "short" | "long"
    title: str
    status: str = "draft"  # draft | reviewing | published | archived

    # 创作数据
    outline: Dict[str, Any] = field(default_factory=dict)
    drafts: List[DraftVersion] = field(default_factory=list)
    characters: List[Character] = field(default_factory=list)
    plot_points: List[PlotPoint] = field(default_factory=list)

    # 拉片数据
    analysis: Optional[AnalysisReport] = None

    # 迭代记录
    iterations: List[IterationRecord] = field(default_factory=list)

    # 元数据
    platform: str = "douyin"  # 目标平台
    target_audience: str = ""
    genre: str = ""  # 类型/题材
    word_count_target: int = 0

    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "track": self.track,
            "title": self.title,
            "status": self.status,
            "outline": self.outline,
            "drafts": [
                {
                    "version": d.version,
                    "change_summary": d.change_summary,
                    "created_at": d.created_at
                }
                for d in self.drafts
            ],
            "characters": [c.to_dict() for c in self.characters],
            "analysis": self.analysis.__dict__ if self.analysis else None,
            "iterations": len(self.iterations),
            "platform": self.platform,
            "genre": self.genre,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
