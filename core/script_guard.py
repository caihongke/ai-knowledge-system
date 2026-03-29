"""ScriptGuard - 五大铁律风控系统
负责剧本和网文创作的硬性约束校验
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CheckResult(Enum):
    """校验结果状态"""

    PASSED = "passed"      # 通过
    WARNING = "warning"    # 警告（可继续）
    BLOCKED = "blocked"    # 阻断（必须整改）


@dataclass
class Violation:
    """违规记录"""

    rule_id: str
    rule_name: str
    severity: str  # "block" | "warn"
    message: str
    location: str | None = None  # 违规位置
    suggestion: str | None = None


@dataclass
class ValidationResult:
    """校验结果"""

    passed: bool
    status: CheckResult
    violations: list[Violation] = field(default_factory=list)
    can_proceed: bool = False  # 是否可以继续创作
    requires_human_review: bool = False  # 是否需要人工审核
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "status": self.status.value,
            "can_proceed": self.can_proceed,
            "requires_human_review": self.requires_human_review,
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "rule_name": v.rule_name,
                    "severity": v.severity,
                    "message": v.message,
                    "location": v.location,
                    "suggestion": v.suggestion,
                }
                for v in self.violations
            ],
            "metadata": self.metadata,
        }


class ScriptGuard:
    """AI风控校验系统 - 五大铁律

    IR-001: 价值观安全 - 阻断级
    IR-002: 版权合规 - 阻断级
    IR-003: 平台规则 - 警告级（可自动修复）
    IR-004: 逻辑自洽 - 警告级
    IR-005: 人设稳定 - 阻断级
    """

    # 敏感词库（价值观安全）
    SENSITIVE_KEYWORDS = {
        "violence": ["血腥", "暴力", "虐杀", "残忍", "血腥画面"],
        "discrimination": ["歧视", "种族", "性别歧视", "地域黑"],
        "illegal": ["毒品", "赌博", "诈骗", "黑客", "入侵"],
        "porn": ["色情", "淫秽", "性暗示"],
        "political": ["政治", "政权", "反动"],
    }

    # 平台规则配置
    PLATFORM_RULES = {
        "douyin": {
            "name": "抖音",
            "max_duration": 300,  # 5分钟
            "max_title_length": 50,
            "forbidden_topics": ["医疗", "金融投资", "迷信"],
            "required_labels": ["内容分级"],
        },
        "kuaishou": {
            "name": "快手",
            "max_duration": 600,  # 10分钟
            "max_title_length": 60,
            "forbidden_topics": ["医疗", "赌博"],
        },
        "bilibili": {
            "name": "B站",
            "max_duration": 1800,  # 30分钟
            "min_resolution": "1080p",
            "forbidden_topics": [],
        },
        "novel": {
            "name": "网文平台",
            "max_chapter_words": 5000,
            "forbidden_topics": ["淫秽", "暴力血腥"],
            "required_meta": ["章节标题", "字数", "更新时间"],
        },
    }

    def __init__(self, track: str = "short"):
        """初始化ScriptGuard

        Args:
            track: "short" (短视频) | "long" (网文长篇)

        """
        self.track = track
        self.violation_history: list[Violation] = []
        self.character_profiles: dict[str, dict] = {}  # 人设档案
        self.world_settings: dict[str, Any] = {}  # 世界观设定

    def validate(self, content: dict, checkpoint: str = "draft") -> ValidationResult:
        """执行五大铁律校验

        Args:
            content: 创作内容
                {
                    "text": "内容文本",
                    "title": "标题",
                    "characters": [{"name": "", "profile": ""}],
                    "plot_points": [],
                    "platform": "douyin|kuaishou|bilibili|novel"
                }
            checkpoint: 检查节点 ("outline"|"draft"|"final")

        Returns:
            ValidationResult: 校验结果

        """
        violations = []

        # IR-001: 价值观安全
        v1 = self._check_value_safety(content.get("text", ""))
        if v1:
            violations.append(v1)

        # IR-002: 版权合规（简版，实际需对接查重API）
        v2 = self._check_copyright(content.get("text", ""))
        if v2:
            violations.append(v2)

        # IR-003: 平台规则
        v3_list = self._check_platform_rules(
            content.get("text", ""),
            content.get("platform", "douyin"),
            content.get("metadata", {}),
        )
        violations.extend(v3_list)

        # IR-004: 逻辑自洽（仅在checkpoint=draft或final时检查）
        if checkpoint in ["draft", "final"]:
            v4_list = self._check_logic_consistency(content)
            violations.extend(v4_list)

        # IR-005: 人设稳定（网文或完整剧本检查）
        if checkpoint in ["draft", "final"] and content.get("characters"):
            v5_list = self._check_character_consistency(
                content.get("characters", []),
                content.get("text", ""),
            )
            violations.extend(v5_list)

        # 分析违规严重性
        has_block = any(v.severity == "block" for v in violations)
        has_warn = any(v.severity == "warn" for v in violations)

        # 记录历史
        self.violation_history.extend(violations)

        # 生成结果
        if has_block:
            return ValidationResult(
                passed=False,
                status=CheckResult.BLOCKED,
                violations=violations,
                can_proceed=False,
                requires_human_review=True,
                metadata={
                    "checkpoint": checkpoint,
                    "track": self.track,
                    "timestamp": datetime.now().isoformat(),
                    "block_reason": "触碰铁律，必须人工整改",
                },
            )
        if has_warn:
            return ValidationResult(
                passed=True,
                status=CheckResult.WARNING,
                violations=violations,
                can_proceed=True,
                requires_human_review=False,
                metadata={
                    "checkpoint": checkpoint,
                    "track": self.track,
                    "timestamp": datetime.now().isoformat(),
                },
            )
        return ValidationResult(
            passed=True,
            status=CheckResult.PASSED,
            violations=[],
            can_proceed=True,
            requires_human_review=False,
            metadata={
                "checkpoint": checkpoint,
                "track": self.track,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def _check_value_safety(self, text: str) -> Violation | None:
        """IR-001: 价值观安全检查"""
        found_keywords = []

        for category, keywords in self.SENSITIVE_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    found_keywords.append(f"{category}:{kw}")

        if found_keywords:
            return Violation(
                rule_id="IR-001",
                rule_name="价值观安全",
                severity="block",
                message=f"检测到敏感内容: {', '.join(found_keywords[:5])}",
                suggestion="请修改相关内容，确保符合公序良俗",
            )
        return None

    def _check_copyright(self, text: str) -> Violation | None:
        """IR-002: 版权合规检查（简化版）"""
        # 检查常见抄袭特征
        red_flags = [
            (r"原文如下", "疑似直接复制原文"),
            (r"摘自", "未标注引用来源"),
            (r"【作者】", "可能未经授权使用他人作品"),
        ]

        for pattern, reason in red_flags:
            if re.search(pattern, text):
                return Violation(
                    rule_id="IR-002",
                    rule_name="版权合规",
                    severity="block",
                    message=f"检测到版权风险: {reason}",
                    suggestion="确保内容为原创或已获得授权",
                )

        # TODO: 对接查重API进行深度检测
        return None

    def _check_platform_rules(
        self,
        text: str,
        platform: str,
        metadata: dict,
    ) -> list[Violation]:
        """IR-003: 平台规则检查"""
        violations = []
        rules = self.PLATFORM_RULES.get(platform, self.PLATFORM_RULES["douyin"])

        # 检查违禁话题
        for topic in rules.get("forbidden_topics", []):
            if topic in text:
                violations.append(Violation(
                    rule_id="IR-003",
                    rule_name="平台规则",
                    severity="warn",
                    message=f"内容包含平台违禁话题: {topic}",
                    suggestion=f"请删除或修改与{topic}相关的内容",
                ))

        # 网文平台检查
        if platform == "novel":
            word_count = len(text)
            max_words = rules.get("max_chapter_words", 5000)
            if word_count > max_words:
                violations.append(Violation(
                    rule_id="IR-003",
                    rule_name="平台规则",
                    severity="warn",
                    message=f"章节字数超限: {word_count}/{max_words}",
                    suggestion=f"建议拆分为多个章节，每章不超过{max_words}字",
                ))

        # 短视频平台检查
        if platform in ["douyin", "kuaishou"]:
            duration = metadata.get("duration", 0)
            max_duration = rules.get("max_duration", 300)
            if duration > max_duration:
                violations.append(Violation(
                    rule_id="IR-003",
                    rule_name="平台规则",
                    severity="warn",
                    message=f"视频时长超限: {duration}s/{max_duration}s",
                    suggestion=f"请剪辑至{max_duration}秒以内",
                ))

        return violations

    def _check_logic_consistency(self, content: dict) -> list[Violation]:
        """IR-004: 逻辑自洽检查"""
        violations = []
        text = content.get("text", "")
        _ = content.get("plot_points", [])  # Reserved for future logic consistency checks

        # 检查时间线一致性
        time_markers = re.findall(r"(\d+)年|(\d+)月|(\d+)日|第(\d+)章", text)
        if len(time_markers) > 5:
            # 检查是否有明显的时间倒退
            # 简化实现：仅检查标记数量
            pass

        # 检查因果逻辑
        causal_patterns = ["因为...所以", "由于...因此", "既然...就"]
        for pattern in causal_patterns:
            matches = re.findall(pattern.replace("...", ".*?"), text)
            # 如果因果表述过多，可能存在逻辑堆砌问题
            if len(matches) > 10:
                violations.append(Violation(
                    rule_id="IR-004",
                    rule_name="逻辑自洽",
                    severity="warn",
                    message="因果逻辑表述过于频繁，可能存在强行解释",
                    suggestion="尝试用行动和对话展现因果，减少直接陈述",
                ))
                break

        return violations

    def _check_character_consistency(
        self,
        characters: list[dict],
        text: str,
    ) -> list[Violation]:
        """IR-005: 人设稳定检查"""
        violations = []

        for char in characters:
            name = char.get("name", "")
            profile = char.get("profile", "")

            # 解析人设关键词
            traits = self._extract_character_traits(profile)

            # 在文本中搜索角色行为
            _ = [m.start() for m in re.finditer(name, text)]  # Reserved for OOC detection

            # 检查是否有OOC（Out Of Character）行为
            # 简化实现：检查角色是否做了与其性格明显矛盾的事
            if "冷静" in traits and f"{name}冲动" in text:
                violations.append(Violation(
                    rule_id="IR-005",
                    rule_name="人设稳定",
                    severity="block",
                    message=f"角色'{name}'人设冲突：设定为'冷静'，但出现'冲动'行为",
                    location=f"{name}冲动",
                    suggestion="修改行为描写，或调整人设设定",
                ))

            if "善良" in traits and f"{name}残忍" in text:
                violations.append(Violation(
                    rule_id="IR-005",
                    rule_name="人设稳定",
                    severity="block",
                    message=f"角色'{name}'人设冲突：设定为'善良'，但出现'残忍'行为",
                    suggestion="修改行为描写，或调整人设设定",
                ))

        return violations

    def _extract_character_traits(self, profile: str) -> list[str]:
        """从人设描述中提取性格特征词"""
        trait_keywords = [
            "冷静", "冲动", "善良", "残忍", "聪明", "愚蠢",
            "勇敢", "懦弱", "乐观", "悲观", "正直", "狡猾",
        ]
        return [t for t in trait_keywords if t in profile]

    def register_character(self, character_id: str, profile: dict):
        """注册角色人设（用于长期跟踪）"""
        self.character_profiles[character_id] = {
            "profile": profile,
            "registered_at": datetime.now().isoformat(),
            "version": 1,
        }

    def update_world_setting(self, setting: dict):
        """更新世界观设定"""
        self.world_settings.update(setting)

    def get_violation_report(self) -> dict:
        """生成违规统计报告"""
        if not self.violation_history:
            return {"status": "clean", "message": "无违规记录"}

        rule_counts = {}
        severity_counts = {"block": 0, "warn": 0}

        for v in self.violation_history:
            rule_counts[v.rule_id] = rule_counts.get(v.rule_id, 0) + 1
            severity_counts[v.severity] = severity_counts.get(v.severity, 0) + 1

        return {
            "status": "has_violations",
            "total": len(self.violation_history),
            "by_rule": rule_counts,
            "by_severity": severity_counts,
            "recent": [
                {
                    "rule": v.rule_name,
                    "message": v.message[:50] + "..." if len(v.message) > 50 else v.message,
                }
                for v in self.violation_history[-5:]
            ],
        }


# 便捷函数
def quick_check(text: str, track: str = "short") -> bool:
    """快速检查，返回是否通过"""
    guard = ScriptGuard(track=track)
    result = guard.validate({"text": text}, checkpoint="outline")
    return result.passed


if __name__ == "__main__":
    # 测试示例
    guard = ScriptGuard(track="short")

    # 测试内容
    test_content = {
        "text": "这是一个测试剧本，主角是一个冷静的年轻人。",
        "title": "测试剧本",
        "characters": [
            {"name": "李明", "profile": "性格冷静，处事果断"},
        ],
        "platform": "douyin",
        "metadata": {"duration": 180},
    }

    result = guard.validate(test_content, checkpoint="draft")
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
