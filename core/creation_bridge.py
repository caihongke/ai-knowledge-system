"""CreationBridge - 创作系统与知识库的数据沉淀通道
打通创作→知识库的循环
"""

from datetime import datetime

from core.models import AnalysisReport, CreationSession, Note
from core.spaced_repetition import SpacedRepetition
from core.storage import Storage


class CreationBridge:
    """创作数据沉淀桥

    核心功能：
    1. 创作经验→知识库笔记
    2. 组件积累→知识库标签
    3. 拉片报告→复习计划
    4. 迭代记录→学习路径
    """

    def __init__(self):
        self.storage = Storage()
        self.review = SpacedRepetition()

    def export_creation_to_knowledge(
        self,
        session: CreationSession,
        analysis: AnalysisReport | None = None,
    ) -> list[str]:
        """将创作沉淀到知识库

        Args:
            session: 创作会话
            analysis: 分析报告（可选）

        Returns:
            创建的笔记ID列表

        """
        note_ids = []

        # 1. 沉淀创作经验
        experience_note = self._create_experience_note(session, analysis)
        note_ids.append(experience_note.id)

        # 2. 沉淀可复用组件
        for component in session.outline.get("components_used", []):
            component_note = self._create_component_note(component, session)
            note_ids.append(component_note.id)

        # 3. 沉淀教训/反思
        if analysis and analysis.improvement_suggestions:
            lesson_note = self._create_lesson_note(session, analysis)
            note_ids.append(lesson_note.id)

        return note_ids

    def _create_experience_note(
        self,
        session: CreationSession,
        analysis: AnalysisReport | None,
    ) -> Note:
        """创建创作经验笔记"""
        title = f"创作经验: {session.title}"

        content_lines = [
            f"# 创作经验: {session.title}",
            "",
            f"**类型**: {session.track} ({session.genre})",
            f"**平台**: {session.platform}",
            f"**创作时间**: {session.created_at}",
            "",
            "## 核心数据",
        ]

        if analysis:
            content_lines.extend([
                f"- Hook得分: {analysis.hook_score:.1f}/10",
                f"- 冲突密度: {analysis.conflict_density:.2f}",
                f"- 结构完整度: {analysis.structure_compliance:.0f}%",
            ])

        content_lines.extend([
            "",
            "## 使用的工业化组件",
        ])

        for comp in session.outline.get("components_used", []):
            content_lines.append(f"- {comp['name']} ({comp['id']})")

        content_lines.extend([
            "",
            "## 关键决策",
            "- Hook选择: ",
            "- 冲突设计: ",
            "- 情绪节奏: ",
        ])

        content = "\n".join(content_lines)

        note = self.storage.add_note(
            title=title,
            content=content,
            tags=["创作经验", session.track, session.genre, session.platform],
        )

        return note

    def _create_component_note(
        self,
        component: dict,
        session: CreationSession,
    ) -> Note:
        """创建组件经验笔记"""
        title = f"组件验证: {component['name']}"

        content = f"""# 组件验证: {component['name']}

**组件ID**: {component['id']}
**应用作品**: {session.title}
**应用时间**: {component['applied_at']}

## 使用效果

[待填写: 该组件在本次创作中的实际效果]

## 适用场景

- 类型: {session.genre}
- 平台: {session.platform}
- 目标效果:

## 优化建议

[待填写: 如何更好地使用这个组件]

---
*自动生成于创作沉淀流程*
"""

        note = self.storage.add_note(
            title=title,
            content=content,
            tags=["组件验证", component["id"], session.genre],
        )

        return note

    def _create_lesson_note(
        self,
        session: CreationSession,
        analysis: AnalysisReport,
    ) -> Note:
        """创建教训/反思笔记"""
        title = f"创作反思: {session.title}"

        content_lines = [
            f"# 创作反思: {session.title}",
            "",
            "## 改进建议（来自拉片分析）",
            "",
        ]

        for i, suggestion in enumerate(analysis.improvement_suggestions, 1):
            content_lines.append(f"{i}. {suggestion}")

        content_lines.extend([
            "",
            "## 复盘",
            "",
            "### 做得好的",
            "- ",
            "",
            "### 需要改进的",
            "- ",
            "",
            "### 下次要注意的",
            "- ",
        ])

        content = "\n".join(content_lines)

        note = self.storage.add_note(
            title=title,
            content=content,
            tags=["创作反思", session.track, "复盘"],
        )

        return note

    def generate_component_library_note(self) -> Note:
        """生成个人组件库索引笔记
        """
        # 搜索所有组件验证笔记
        results = self.storage.search_notes("组件验证")

        content_lines = [
            "# 个人组件库索引",
            "",
            "## 已验证组件",
            "",
        ]

        for result in results:
            note = result["note"]
            content_lines.append(f"- [{note.title}]({note.file_path})")

        content_lines.extend([
            "",
            "## 按类型分类",
            "",
            "### 人设组件",
            "[列出所有人设组件]",
            "",
            "### 桥段组件",
            "[列出所有桥段组件]",
            "",
            "### 爽点组件",
            "[列出所有爽点组件]",
            "",
            "## 使用统计",
            f"- 总计: {len(results)} 个已验证组件",
        ])

        content = "\n".join(content_lines)

        note = self.storage.add_note(
            title="个人组件库索引",
            content=content,
            tags=["组件库", "索引", "创作资源"],
        )

        return note

    def schedule_creation_review(self, session: CreationSession) -> str:
        """为创作设置复习计划

        创作经验的复习策略：
        - 1天后: 快速回顾
        - 3天后: 深入反思
        - 7天后: 提炼模式
        - 30天后: 系统复盘
        """
        # 找到对应的笔记
        notes = self.storage.list_notes()
        creation_notes = [
            n for n in notes
            if n.title.startswith("创作经验:") and session.title in n.title
        ]

        if not creation_notes:
            return "未找到对应的创作经验笔记"

        note = creation_notes[0]

        # 设置艾宾浩斯复习计划
        review_dates = [1, 3, 7, 30]  # 天数

        for days in review_dates:
            review_date = self._add_days(note.created_at, days)
            self.review.schedule_review(note.id, review_date)

        return f"已为笔记 {note.id} 设置复习计划"

    def _add_days(self, date_str: str, days: int) -> str:
        """日期加法"""
        from datetime import timedelta
        date = datetime.fromisoformat(date_str)
        new_date = date + timedelta(days=days)
        return new_date.strftime("%Y-%m-%d")

    def get_creation_stats(self) -> dict:
        """获取创作统计数据"""
        notes = self.storage.list_notes()

        creation_notes = [n for n in notes if "创作经验" in n.tags]
        reflection_notes = [n for n in notes if "创作反思" in n.tags]
        component_notes = [n for n in notes if "组件验证" in n.tags]

        # 类型分布
        genre_counts = {}
        for n in creation_notes:
            for tag in n.tags:
                if tag not in ["创作经验", "short", "long"]:
                    genre_counts[tag] = genre_counts.get(tag, 0) + 1

        return {
            "total_creations": len(creation_notes),
            "total_reflections": len(reflection_notes),
            "total_component_tests": len(component_notes),
            "genre_distribution": genre_counts,
            "knowledge_accumulation": len(creation_notes) * 3,  # 每创作产生约3条知识
        }


# 便捷函数
def quick_export(session: CreationSession) -> list[str]:
    """快速导出创作到知识库"""
    bridge = CreationBridge()
    return bridge.export_creation_to_knowledge(session)


if __name__ == "__main__":
    # 测试
    bridge = CreationBridge()
    stats = bridge.get_creation_stats()
    print(f"创作统计: {stats}")
