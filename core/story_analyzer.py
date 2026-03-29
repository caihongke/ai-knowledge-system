# -*- coding: utf-8 -*-
"""
StoryAnalyzer - 拉片分析Agent
负责剧本和网文的标准化拉片分析
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

from core.models import AnalysisReport


@dataclass
class EmotionalNode:
    """情绪节点"""
    position: float  # 0-1 位置
    value: float     # 0-10 情绪值
    trigger: str     # 触发事件
    technique: str   # 手法


@dataclass
class ConflictPoint:
    """冲突点"""
    position: float
    conflict_type: str
    intensity: str   # 低/中/高/极高
    participants: List[str]
    resolution: str


class StoryAnalyzer:
    """
    拉片分析Agent

    核心功能：
    1. Hook吸引力评分
    2. 冲突密度分析
    3. 15节点情绪曲线
    4. 结构完整度评估
    5. 工业化组件识别
    """

    # 情绪关键词库
    EMOTION_KEYWORDS = {
        "high": ["激动", "兴奋", "愤怒", "恐惧", "狂喜", "震惊", "热血沸腾"],
        "medium": ["紧张", "焦虑", "期待", "疑惑", "感动", "欣慰"],
        "low": ["平静", "悲伤", "失落", "无聊", "疲倦", "无奈"]
    }

    # 冲突类型定义
    CONFLICT_TYPES = [
        "人与自我", "人与人", "人与社会", "人与自然", "人与命运"
    ]

    def __init__(self):
        self.report_template = Path("creation/analysis/templates/拉片分析报告模板.md")

    def analyze(
        self,
        content: str,
        title: str,
        content_type: str = "short",  # short/long
        source: str = "自有作品"
    ) -> AnalysisReport:
        """
        执行完整拉片分析

        Args:
            content: 作品内容文本
            title: 作品标题
            content_type: 类型 short/long
            source: 来源 自有作品/竞品作品

        Returns:
            AnalysisReport 分析报告
        """
        # 1. Hook分析
        hook_score = self._analyze_hook(content)

        # 2. 冲突密度
        conflicts = self._analyze_conflicts(content)
        conflict_density = len(conflicts) / max(len(content) / 1000, 1)

        # 3. 情绪曲线
        emotion_curve = self._analyze_emotion_curve(content)

        # 4. 结构完整度
        structure_score = self._analyze_structure(content, content_type)

        # 5. 生成改进建议
        suggestions = self._generate_suggestions(
            hook_score, conflicts, emotion_curve, structure_score
        )

        return AnalysisReport(
            source=source,
            source_title=title,
            hook_score=hook_score,
            conflict_density=conflict_density,
            emotion_curve=[e.value for e in emotion_curve],
            structure_compliance=structure_score,
            improvement_suggestions=suggestions,
            created_at=datetime.now().isoformat(),
            analyzer="story-analyzer"
        )

    def _analyze_hook(self, content: str) -> float:
        """
        分析Hook吸引力

        评分维度：
        - 好奇心激发 (0-3分)
        - 情感共鸣 (0-3分)
        - 信息密度 (0-2分)
        - 独特性 (0-2分)
        """
        # 提取开头（前300字或前3分钟）
        hook_text = content[:500]

        score = 5.0  # 基础分

        # 好奇心指标
        curiosity_markers = ["?", "为什么", "怎么回事", "竟然", "居然"]
        for marker in curiosity_markers:
            if marker in hook_text:
                score += 0.5

        # 冲突指标
        if any(word in hook_text for word in ["冲突", "对抗", "矛盾", "危机"]):
            score += 1.0

        # 数字/数据（增加可信度）
        if re.search(r'\d+', hook_text):
            score += 0.5

        return min(score, 10.0)

    def _analyze_conflicts(self, content: str) -> List[ConflictPoint]:
        """分析冲突点"""
        conflicts = []

        # 冲突标记词
        conflict_markers = [
            "冲突", "对抗", "矛盾", "争吵", "战斗", "争执",
            "误解", "背叛", "陷害", "报复", "挑战"
        ]

        content_length = len(content)

        for marker in conflict_markers:
            for match in re.finditer(marker, content):
                pos = match.start() / content_length

                # 判断冲突强度
                context = content[max(0, match.start()-50):min(len(content), match.end()+50)]
                intensity = self._judge_intensity(context)

                conflicts.append(ConflictPoint(
                    position=pos,
                    conflict_type=self._classify_conflict(context),
                    intensity=intensity,
                    participants=[],  # 需要NLP提取
                    resolution=""
                ))

        return conflicts

    def _judge_intensity(self, context: str) -> str:
        """判断冲突强度"""
        high_markers = ["生死", "决战", "毁灭", "拼命", "极致"]
        if any(m in context for m in high_markers):
            return "极高"

        medium_markers = ["激烈", "严重", "重大", "激烈"]
        if any(m in context for m in medium_markers):
            return "高"

        low_markers = ["小", "轻微", "误会", "口角"]
        if any(m in context for m in low_markers):
            return "低"

        return "中"

    def _classify_conflict(self, context: str) -> str:
        """分类冲突类型"""
        if any(w in context for w in ["内心", "纠结", "挣扎", "矛盾"]):
            return "人与自我"
        elif any(w in context for w in ["社会", "规则", "制度", "道德"]):
            return "人与社会"
        elif any(w in context for w in ["命运", "天命", "宿命", "注定"]):
            return "人与命运"
        else:
            return "人与人"

    def _analyze_emotion_curve(self, content: str) -> List[EmotionalNode]:
        """
        分析15节点情绪曲线

        将内容分为15段，分析每段的情绪值
        """
        content_length = len(content)
        segment_size = content_length // 15

        curve = []
        for i in range(15):
            start = i * segment_size
            end = start + segment_size if i < 14 else content_length
            segment = content[start:end]

            # 计算情绪值
            emotion_value = self._calculate_emotion_value(segment)

            # 识别触发事件（简化：取前20字）
            trigger = segment[:20].replace("\n", " ")

            curve.append(EmotionalNode(
                position=i / 14,
                value=emotion_value,
                trigger=trigger,
                technique=""
            ))

        return curve

    def _calculate_emotion_value(self, text: str) -> float:
        """计算段落情绪值"""
        value = 5.0  # 中性基线

        # 高潮标记
        for word in self.EMOTION_KEYWORDS["high"]:
            value += text.count(word) * 0.5

        # 低谷标记
        for word in self.EMOTION_KEYWORDS["low"]:
            value -= text.count(word) * 0.3

        # 限制在0-10范围
        return max(0, min(10, value))

    def _analyze_structure(self, content: str, content_type: str) -> float:
        """
        分析结构完整度

        短视频(3-5分钟): Hook -> 发展 -> 高潮 -> 结局
        网文(章): 承接 -> 发展 -> 钩子
        """
        score = 0.0

        if content_type == "short":
            # 检查短视频结构
            checks = {
                "有明确开头": bool(content[:100]),
                "有发展部分": len(content) > 200,
                "有高潮迹象": any(w in content for w in ["高潮", "终于", "关键时刻"]),
                "有结局/收尾": any(w in content[-200:] for w in ["结局", "最后", "总之", "所以"])
            }
            score = sum(checks.values()) / len(checks) * 100

        else:  # long
            # 检查网文章节结构
            checks = {
                "有承接": any(w in content[:100] for w in ["上回", "接着", "随后"]),
                "有发展": len(content) > 500,
                "有钩子": any(w in content[-100:] for w in ["?", "悬念", "究竟", "难道"])
            }
            score = sum(checks.values()) / len(checks) * 100

        return score

    def _generate_suggestions(
        self,
        hook_score: float,
        conflicts: List[ConflictPoint],
        emotion_curve: List[EmotionalNode],
        structure_score: float
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []

        # Hook建议
        if hook_score < 6:
            suggestions.append(f"[高优先级] Hook吸引力不足({hook_score:.1f}/10)，建议增加悬念或冲突")
        elif hook_score < 8:
            suggestions.append(f"[中优先级] Hook有提升空间，可加入数据或反常识观点")

        # 冲突建议
        if len(conflicts) < 3:
            suggestions.append("[高优先级] 冲突密度偏低，建议每15秒/每章设置一个冲突点")

        # 情绪曲线建议
        high_points = sum(1 for e in emotion_curve if e.value > 7)
        if high_points < 3:
            suggestions.append("[中优先级] 情绪高潮点较少，建议增加情感爆发场景")

        # 结构建议
        if structure_score < 70:
            suggestions.append(f"[高优先级] 结构完整度不足({structure_score:.0f}%)，检查起承转合")

        return suggestions if suggestions else ["整体表现良好，继续保持"]

    def compare_with_benchmark(
        self,
        report: AnalysisReport,
        benchmark: AnalysisReport
    ) -> Dict[str, Any]:
        """
        与对标作品对比分析
        """
        comparison = {
            "dimensions": {},
            "gaps": [],
            "advantages": []
        }

        # 对比各维度
        dimensions = [
            ("Hook设计", report.hook_score, benchmark.hook_score),
            ("冲突密度", report.conflict_density, benchmark.conflict_density),
            ("结构完整度", report.structure_compliance, benchmark.structure_compliance)
        ]

        for name, current, target in dimensions:
            diff = current - target
            comparison["dimensions"][name] = {
                "current": current,
                "target": target,
                "diff": diff
            }

            if diff < -1:
                comparison["gaps"].append(f"{name}落后{abs(diff):.1f}分")
            elif diff > 1:
                comparison["advantages"].append(f"{name}领先{diff:.1f}分")

        return comparison

    def export_report(
        self,
        report: AnalysisReport,
        output_path: Optional[str] = None
    ) -> str:
        """
        导出标准化分析报告
        """
        if not output_path:
            output_path = f"creation/analysis/reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        content = f"""# 拉片分析报告

> 作品: {report.source_title}
> 来源: {report.source}
> 分析时间: {report.created_at}
> 分析师: {report.analyzer}

## 一、核心指标

### Hook吸引力
**评分**: {report.hook_score:.1f} / 10

{'⚠️ 需要改进' if report.hook_score < 6 else '✓ 表现良好'}

### 冲突密度
**密度**: {report.conflict_density:.2f} 个冲突点/千字

### 情绪曲线
```
情绪值(0-10)
"""

        # 绘制ASCII情绪曲线
        for i, val in enumerate(report.emotion_curve):
            bar = "█" * int(val)
            content += f"{i:2d} | {bar} {val:.1f}\n"

        content += f"""```

### 结构完整度
**评分**: {report.structure_compliance:.0f}%

## 二、改进建议

"""

        for i, suggestion in enumerate(report.improvement_suggestions, 1):
            content += f"{i}. {suggestion}\n"

        content += """
## 三、可复用元素

[分析识别出的优秀桥段、台词、节奏模板]

---
*本报告由StoryAnalyzer自动生成*
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_path


# 便捷函数
def quick_analyze(content: str, title: str) -> dict:
    """快速分析，返回结果字典"""
    analyzer = StoryAnalyzer()
    report = analyzer.analyze(content, title)
    return {
        "hook_score": report.hook_score,
        "conflict_density": report.conflict_density,
        "structure_compliance": report.structure_compliance,
        "suggestions": report.improvement_suggestions
    }


if __name__ == "__main__":
    # 测试
    test_content = """
    第一章：逆袭开始

    李峰怎么也没想到，自己会被最信任的人背叛。

    那天，天空阴沉，他站在公司楼下，手里攥着被撕碎的合同。
    三年的努力，一夜之间化为泡影。

    "为什么？"他喃喃自语。

    就在这时，一个陌生的号码打来...
    """

    analyzer = StoryAnalyzer()
    report = analyzer.analyze(test_content, "测试作品", "long")
    print(f"Hook评分: {report.hook_score}")
    print(f"冲突密度: {report.conflict_density}")
    print(f"建议: {report.improvement_suggestions}")
