"""存储层 - 知识库的读写操作"""

import json
from datetime import datetime

from core.config import Config
from core.models import Note


class Storage:
    """知识库存储管理"""

    def __init__(self):
        Config.ensure_dirs()

    # --- 索引读写 ---

    def load_index(self) -> list[Note]:
        """加载笔记索引"""
        if not Config.INDEX_FILE.exists():
            return []
        data = json.loads(Config.INDEX_FILE.read_text(encoding="utf-8"))
        return [Note.from_dict(item) for item in data]

    def save_index(self, notes: list[Note]) -> None:
        """保存笔记索引"""
        data = [note.to_dict() for note in notes]
        Config.INDEX_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # --- CRUD ---

    def add_note(self, title: str, tags: list[str], category: str, content: str = "") -> Note:
        """新建笔记：创建 Markdown 文件 + 更新索引"""
        note_id = Note.generate_id()
        file_name = f"{note_id}.md"
        file_path = Config.NOTES_DIR / file_name

        # 写入 Markdown 文件
        md_content = f"# {title}\n\n{content}\n"
        file_path.write_text(md_content, encoding="utf-8")

        # 创建笔记对象
        note = Note(
            id=note_id,
            title=title,
            tags=tags,
            category=category,
            file_path=f"notes/{file_name}",
        )

        # 更新索引
        notes = self.load_index()
        notes.append(note)
        self.save_index(notes)

        return note

    def get_note(self, note_id: str) -> Note | None:
        """按 ID 获取笔记"""
        notes = self.load_index()
        for note in notes:
            if note.id == note_id:
                return note
        return None

    def get_note_content(self, note: Note) -> str:
        """读取笔记的 Markdown 内容"""
        file_path = Config.KNOWLEDGE_DIR / note.file_path
        if file_path.exists():
            return file_path.read_text(encoding="utf-8")
        return ""

    def update_note(self, note_id: str, **kwargs) -> Note | None:
        """更新笔记元数据"""
        notes = self.load_index()
        for i, note in enumerate(notes):
            if note.id == note_id:
                for key, value in kwargs.items():
                    if hasattr(note, key):
                        setattr(note, key, value)
                note.updated_at = datetime.now().isoformat(timespec="seconds")
                self.save_index(notes)
                return note
        return None

    def delete_note(self, note_id: str) -> bool:
        """删除笔记：删除文件 + 更新索引"""
        notes = self.load_index()
        target = None
        for note in notes:
            if note.id == note_id:
                target = note
                break

        if not target:
            return False

        # 删除 Markdown 文件
        file_path = Config.KNOWLEDGE_DIR / target.file_path
        if file_path.exists():
            file_path.unlink()

        # 更新索引
        notes = [n for n in notes if n.id != note_id]
        self.save_index(notes)
        return True

    # --- 查询 ---

    def list_notes(
        self,
        tag: str = "",
        category: str = "",
    ) -> list[Note]:
        """列出笔记，支持按标签和分类筛选"""
        notes = self.load_index()
        if tag:
            notes = [n for n in notes if tag in n.tags]
        if category:
            notes = [n for n in notes if n.category == category]
        return notes

    def search_notes(self, keyword: str) -> list[dict]:
        """全文检索：搜索标题和内容"""
        results = []
        keyword_lower = keyword.lower()
        for note in self.load_index():
            # 搜索标题
            if keyword_lower in note.title.lower():
                results.append({"note": note, "match": "title"})
                continue
            # 搜索内容
            content = self.get_note_content(note)
            if keyword_lower in content.lower():
                results.append({"note": note, "match": "content"})
        return results

    def get_all_tags(self) -> dict:
        """获取所有标签及其计数"""
        tag_count = {}
        for note in self.load_index():
            for tag in note.tags:
                tag_count[tag] = tag_count.get(tag, 0) + 1
        return dict(sorted(tag_count.items(), key=lambda x: x[1], reverse=True))
