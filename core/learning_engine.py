"""本地规则引擎 - 基于知识库数据生成学习建议（无需 API Key）"""

from collections import Counter

from core.spaced_repetition import SpacedRepetition
from core.storage import Storage

# 预定义学习路径图谱：标签 -> 推荐进阶方向
LEARNING_GRAPH = {
    "python": ["数据结构与算法", "Python 进阶（装饰器/生成器/元类）", "Web 框架（Flask/FastAPI）"],
    "机器学习": ["深度学习基础", "PyTorch/TensorFlow 实战", "数据预处理与特征工程"],
    "深度学习": ["Transformer 架构", "计算机视觉", "自然语言处理"],
    "git": ["Git 分支策略", "CI/CD 流水线", "GitHub Actions"],
    "web": ["RESTful API 设计", "数据库（SQL/NoSQL）", "前端基础（HTML/CSS/JS）"],
    "数据库": ["SQL 优化", "ORM 框架", "Redis 缓存"],
    "算法": ["动态规划", "图论", "LeetCode 刷题计划"],
    "ai": ["Prompt Engineering", "RAG 应用开发", "Agent 框架"],
    "docker": ["Kubernetes 入门", "微服务架构", "云原生部署"],
    "linux": ["Shell 脚本编程", "系统管理", "网络基础"],
}


class LearningEngine:
    """基于规则的学习路径推荐引擎"""

    def __init__(self):
        self.storage = Storage()
        self.review = SpacedRepetition()

    def analyze(self) -> dict:
        """分析知识库，生成学习建议"""
        notes = self.storage.list_notes()

        if not notes:
            return {
                "status": "empty",
                "summary": "知识库为空，建议从基础开始。",
                "suggestions": [
                    {"topic": "Python 基础", "reason": "编程入门首选语言", "priority": "高"},
                    {"topic": "Git 版本控制", "reason": "开发必备工具", "priority": "高"},
                    {"topic": "Markdown 写作", "reason": "提升笔记效率", "priority": "中"},
                ],
                "knowledge_map": {},
                "review_health": {},
            }

        # 1. 统计标签频率（知识覆盖度）
        tag_counter = Counter()
        category_counter = Counter()
        for note in notes:
            for tag in note.tags:
                tag_counter[tag.lower()] += 1
            category_counter[note.category] += 1

        # 2. 复习健康度
        stats = self.review.get_stats()

        # 3. 识别知识薄弱区（只有 1 条笔记的标签）
        weak_areas = [tag for tag, count in tag_counter.items() if count == 1]

        # 4. 识别知识强项（>= 3 条笔记的标签）
        strong_areas = [tag for tag, count in tag_counter.items() if count >= 3]

        # 5. 生成推荐
        suggestions = self._generate_suggestions(tag_counter, weak_areas, strong_areas, stats)

        return {
            "status": "ok",
            "summary": f"知识库共 {len(notes)} 条笔记，覆盖 {len(tag_counter)} 个标签领域。",
            "knowledge_map": dict(tag_counter.most_common()),
            "strong_areas": strong_areas,
            "weak_areas": weak_areas,
            "categories": dict(category_counter),
            "review_health": stats,
            "suggestions": suggestions,
        }

    def _generate_suggestions(self, tag_counter, weak_areas, strong_areas, review_stats) -> list[dict]:
        """基于规则生成学习建议"""
        suggestions = []

        # 规则 1：基于强项推荐进阶
        for tag in strong_areas:
            tag_lower = tag.lower()
            if tag_lower in LEARNING_GRAPH:
                for topic in LEARNING_GRAPH[tag_lower][:1]:
                    suggestions.append({
                        "topic": topic,
                        "reason": f"你在「{tag}」领域已有 {tag_counter[tag_lower]} 条笔记，建议进阶",
                        "priority": "高",
                    })

        # 规则 2：基于已有标签推荐相关领域
        for tag in list(tag_counter.keys())[:5]:
            tag_lower = tag.lower()
            if tag_lower in LEARNING_GRAPH:
                for topic in LEARNING_GRAPH[tag_lower]:
                    # 避免重复推荐
                    if not any(s["topic"] == topic for s in suggestions):
                        suggestions.append({
                            "topic": topic,
                            "reason": f"与你已学的「{tag}」相关",
                            "priority": "中",
                        })
                        break

        # 规则 3：薄弱区加固
        for tag in weak_areas[:2]:
            suggestions.append({
                "topic": f"深入学习: {tag}",
                "reason": f"「{tag}」仅 1 条笔记，建议补充更多内容",
                "priority": "中",
            })

        # 规则 4：复习提醒
        if review_stats.get("due_today", 0) > 0:
            suggestions.insert(0, {
                "topic": "完成今日复习",
                "reason": f"有 {review_stats['due_today']} 条笔记待复习，优先处理",
                "priority": "高",
            })

        # 规则 5：如果无法匹配图谱，给通用建议
        if not suggestions:
            existing = set(tag_counter.keys())
            for tag, topics in LEARNING_GRAPH.items():
                if tag not in existing:
                    suggestions.append({
                        "topic": topics[0],
                        "reason": f"「{tag}」是热门技术领域，值得探索",
                        "priority": "低",
                    })
                    if len(suggestions) >= 3:
                        break

        return suggestions[:5]
