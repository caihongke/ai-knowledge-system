# -*- coding: utf-8 -*-
"""AI 知识引擎 - 集成 Ollama 的智能分析

结合本地规则引擎和 Ollama 大模型，提供增强的知识库分析能力。
"""

import json
from typing import Optional
from dataclasses import dataclass, asdict

from core.storage import Storage
from core.spaced_repetition import SpacedRepetition
from core.ollama_client import OllamaClient, OllamaMessage
from core.economy_controller import EconomyController, SmartCache


@dataclass
class LearningAnalysis:
    """学习分析报告"""
    status: str  # "ok" | "empty" | "offline"
    summary: str
    knowledge_map: dict
    review_health: dict
    suggestions: list[dict]
    ai_insights: Optional[str] = None  # AI 深度洞察
    ai_available: bool = False


class AIEngine:
    """AI 增强的学习引擎"""

    def __init__(self):
        self.storage = Storage()
        self.review = SpacedRepetition()
        self.ollama = OllamaClient()
        self.economy = EconomyController()
        self.smart_cache = SmartCache(similarity_threshold=0.85)
        self._ai_available = None

    @property
    def ai_available(self) -> bool:
        """检查 AI 是否可用"""
        if self._ai_available is None:
            self._ai_available = self.ollama.is_available()
        return self._ai_available

    def analyze(self) -> LearningAnalysis:
        """
        综合分析知识库，优先使用 AI，降级到规则引擎
        """
        notes = self.storage.list_notes()

        if not notes:
            return LearningAnalysis(
                status="empty",
                summary="知识库为空，开始学习之旅吧！",
                knowledge_map={},
                review_health={},
                suggestions=[{
                    "topic": "开始使用",
                    "reason": "添加第一条笔记，建立你的知识库",
                    "priority": "高"
                }],
                ai_available=False
            )

        # 基础统计（规则引擎部分）
        all_tags = {}
        for note in notes:
            for tag in note.tags:
                all_tags[tag] = all_tags.get(tag, 0) + 1

        stats = self.review.get_stats()

        # 尝试 AI 增强分析
        ai_insights = None
        if self.ai_available:
            ai_insights = self._ai_analyze_knowledge(notes, all_tags, stats)

        # 生成建议
        suggestions = self._generate_suggestions(all_tags, ai_insights)

        return LearningAnalysis(
            status="ok",
            summary=self._generate_summary(notes, all_tags, ai_insights),
            knowledge_map=dict(sorted(all_tags.items(), key=lambda x: -x[1])[:10]),
            review_health=stats,
            suggestions=suggestions,
            ai_insights=ai_insights,
            ai_available=self.ai_available
        )

    def _ai_analyze_knowledge(self, notes, tags, stats) -> Optional[str]:
        """使用 AI 分析知识库结构和盲点（带经济控制）"""
        try:
            # 构建知识库摘要
            tag_summary = ", ".join([f"{k}({v})" for k, v in list(tags.items())[:15]])
            recent_notes = sorted(notes, key=lambda n: n.updated_at, reverse=True)[:5]
            recent_titles = ", ".join([n.title for n in recent_notes])

            prompt = f"""作为学习分析专家，请分析以下知识库状态：

知识领域分布: {tag_summary}
最近学习内容: {recent_titles}
复习状态: 学习中 {stats.get('in_progress', 0)} / 已掌握 {stats.get('mastered', 0)} / 今日待复习 {stats.get('due_today', 0)}

请用2-3句话分析：
1. 知识结构的均衡性
2. 当前学习状态
3. 一个具体的改进建议

回答简洁，不要分点。"""

            # 检查配额
            estimated_tokens = self.economy.estimate_tokens(prompt) + 500
            quota_check = self.economy.check_quota(estimated_tokens)

            if not quota_check["allowed"]:
                return f"[成本控制] {quota_check['reason']}"

            # 尝试从缓存获取（相似度匹配）
            context = "knowledge_analysis"
            cached = self.smart_cache.find_similar(prompt, context)
            if cached:
                return cached

            # 执行 AI 调用
            result = self.ollama.generate(prompt, system="你是专业的学习顾问，善于发现知识结构问题。")

            # 记录调用并缓存结果
            self.economy.record_call(estimated_tokens)
            self.smart_cache.save_with_prompt(prompt, context, result)

            return result
        except Exception:
            return None

    def _generate_summary(self, notes, tags, ai_insights) -> str:
        """生成总结文本"""
        if ai_insights:
            return ai_insights
        return f"知识库共有 {len(notes)} 条笔记，覆盖 {len(tags)} 个领域"

    def _generate_suggestions(self, tags, ai_insights) -> list[dict]:
        """生成学习建议"""
        suggestions = []

        # 薄弱领域建议
        weak_areas = [tag for tag, count in tags.items() if count == 1]
        if weak_areas:
            suggestions.append({
                "topic": f"深化: {weak_areas[0]}",
                "reason": "该领域只有一条笔记，建议补充更多相关内容",
                "priority": "中"
            })

        # 新增领域建议
        if len(tags) < 3:
            suggestions.append({
                "topic": "拓展新领域",
                "reason": "知识库领域较少，尝试学习全新主题",
                "priority": "高"
            })

        # 如果没有建议，给一个通用的
        if not suggestions:
            suggestions.append({
                "topic": "整理与连接",
                "reason": "尝试在不同笔记间建立链接，形成知识网络",
                "priority": "中"
            })

        return suggestions[:3]  # 最多3条

    def ask_knowledge_base(self, question: str) -> str:
        """
        基于知识库内容回答问题（RAG 简化版，带经济控制）
        """
        if not self.ai_available:
            return "[错误] Ollama 服务未启动，无法使用 AI 问答功能"

        # 检查配额
        estimated_tokens = self.economy.estimate_tokens(question) + 2000
        quota_check = self.economy.check_quota(estimated_tokens)
        if not quota_check["allowed"]:
            return f"[成本控制] {quota_check['reason']}"

        # 尝试缓存
        cached = self.smart_cache.find_similar(question, "qa")
        if cached:
            return f"[缓存命中] {cached}"

        # 搜索相关笔记
        keywords = self._extract_keywords(question)
        related_notes = []

        for keyword in keywords:
            results = self.storage.search_notes(keyword)
            for r in results:
                note = r["note"]
                if note not in [n["note"] for n in related_notes]:
                    content = self.storage.get_note_content(note)[:500]  # 取前500字
                    related_notes.append({"note": note, "content": content, "match": r["match"]})

        if not related_notes:
            # 没有相关笔记，直接回答
            result = self.ollama.generate(
                question,
                system="你是AI学习助手，基于已有知识回答问题。"
            )
            self.economy.record_call(estimated_tokens)
            self.smart_cache.save_with_prompt(question, "qa", result)
            return result

        # 构建上下文
        context = []
        for i, item in enumerate(related_notes[:3], 1):
            context.append(f"【笔记{i}】{item['note'].title}\n{item['content'][:800]}")

        prompt = f"""基于以下知识库内容回答问题：

{chr(10).join(context)}

---
用户问题: {question}

请基于上述笔记内容回答，如果笔记中没有相关信息，请明确说明。回答要简洁。"""

        result = self.ollama.generate(prompt, system="你是知识库助手，基于提供的笔记内容回答问题。")
        self.economy.record_call(estimated_tokens)
        self.smart_cache.save_with_prompt(question, "qa", result)
        return result

    def summarize_note(self, note_id: str) -> str:
        """
        为单条笔记生成 AI 总结（带经济控制）
        """
        note = self.storage.get_note(note_id)
        if not note:
            return "[错误] 笔记不存在"

        content = self.storage.get_note_content(note)
        if not content:
            return "[错误] 笔记内容为空"

        if not self.ai_available:
            return "[错误] Ollama 服务未启动，无法使用总结功能"

        # 检查配额
        estimated_tokens = self.economy.estimate_tokens(content) + 500
        quota_check = self.economy.check_quota(estimated_tokens)
        if not quota_check["allowed"]:
            return f"[成本控制] {quota_check['reason']}"

        # 尝试缓存
        cache_key = f"summary:{note_id}"
        cached = self.economy.get_cached_result(cache_key)
        if cached:
            return f"[缓存命中] {cached}"

        prompt = f"""请对以下内容进行总结：

标题: {note.title}
标签: {', '.join(note.tags)}

内容:
{content[:3000]}

请提供：
1. 核心要点（3-5条）
2. 关键概念解释
3. 可以延伸学习的方向"""

        result = self.ollama.generate(prompt, system="你是学习助手，善于提炼笔记要点。")
        self.economy.record_call(estimated_tokens)
        self.economy.save_cache(cache_key, result)
        return result

    def suggest_connections(self, note_id: str) -> list[dict]:
        """
        为笔记推荐相关连接
        """
        target_note = self.storage.get_note(note_id)
        if not target_note:
            return []

        # 基于标签找相关笔记
        all_notes = self.storage.list_notes()
        connections = []

        for note in all_notes:
            if note.id == note_id:
                continue

            shared_tags = set(note.tags) & set(target_note.tags)
            if shared_tags:
                connections.append({
                    "note_id": note.id,
                    "title": note.title,
                    "shared_tags": list(shared_tags),
                    "strength": len(shared_tags)
                })

        # 按关联强度排序
        connections.sort(key=lambda x: -x["strength"])
        return connections[:5]

    def get_economy_stats(self) -> dict:
        """获取经济控制统计"""
        return self.economy.get_stats_summary()

    def _extract_keywords(self, text: str) -> list[str]:
        """从问题中提取关键词（简单实现）"""
        # 停用词
        stopwords = {"的", "了", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这", "那", "什么", "怎么", "哪些", "吗", "呢"}

        # 分词（简单按空格和标点分割）
        import re
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text)

        # 过滤停用词和短词
        keywords = [w for w in words if w not in stopwords and len(w) >= 2]

        # 去重并保持顺序
        seen = set()
        result = []
        for w in keywords:
            if w not in seen:
                seen.add(w)
                result.append(w)

        return result[:5]  # 最多5个关键词


if __name__ == "__main__":
    engine = AIEngine()
    result = engine.analyze()
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
