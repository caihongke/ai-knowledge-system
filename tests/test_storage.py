"""存储模块功能测试"""

import sys

from core.config import Config
from core.storage import Storage


def run_tests():
    s = Storage()
    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            print(f"  [PASS] {name}")
            passed += 1
        else:
            print(f"  [FAIL] {name}")
            failed += 1

    # ====== 1. 新建笔记 ======
    print("1. 测试 add_note")
    note = s.add_note("测试笔记", ["python", "test"], "study", "这是测试内容")
    check("返回 Note 对象", note is not None and note.title == "测试笔记")
    check("tags 正确", note.tags == ["python", "test"])
    check("category 正确", note.category == "study")
    check("MD 文件已创建", (Config.KNOWLEDGE_DIR / note.file_path).exists())
    note_id = note.id

    # ====== 2. 按 ID 获取 ======
    print("2. 测试 get_note")
    fetched = s.get_note(note_id)
    check("能按 ID 查到", fetched is not None)
    check("title 一致", fetched.title == "测试笔记")

    # ====== 3. 读取内容 ======
    print("3. 测试 get_note_content")
    content = s.get_note_content(fetched)
    check("内容包含标题", "# 测试笔记" in content)
    check("内容包含正文", "这是测试内容" in content)

    # ====== 4. 更新笔记 ======
    print("4. 测试 update_note")
    updated = s.update_note(note_id, title="更新后的标题", tags=["python", "test", "updated"])
    check("更新成功", updated is not None)
    check("title 已更新", updated.title == "更新后的标题")
    check("tags 已更新", "updated" in updated.tags)

    # ====== 5. 列出笔记 ======
    print("5. 测试 list_notes")
    all_notes = s.list_notes()
    check("列表非空", len(all_notes) > 0)
    filtered = s.list_notes(tag="updated")
    check("按标签筛选有效", len(filtered) > 0)
    filtered2 = s.list_notes(category="study")
    check("按分类筛选有效", len(filtered2) > 0)
    empty = s.list_notes(tag="不存在的标签")
    check("不存在标签返回空", len(empty) == 0)

    # ====== 6. 全文检索 ======
    print("6. 测试 search_notes")
    results = s.search_notes("更新后")
    check("能搜索到标题匹配", len(results) > 0 and results[0]["match"] == "title")
    results2 = s.search_notes("测试内容")
    check("能搜索到内容匹配", len(results2) > 0 and results2[0]["match"] == "content")
    results3 = s.search_notes("完全不存在的关键词xyz")
    check("无匹配返回空", len(results3) == 0)

    # ====== 7. 获取所有标签 ======
    print("7. 测试 get_all_tags")
    tags = s.get_all_tags()
    check("返回 dict", isinstance(tags, dict))
    check("包含 python 标签", "python" in tags)

    # ====== 8. 删除笔记 ======
    print("8. 测试 delete_note")
    md_path = Config.KNOWLEDGE_DIR / fetched.file_path
    deleted = s.delete_note(note_id)
    check("删除成功", deleted is True)
    check("MD 文件已删除", not md_path.exists())
    check("索引中已移除", s.get_note(note_id) is None)
    check("重复删除返回 False", s.delete_note(note_id) is False)

    # ====== 结果汇总 ======
    print()
    print(f"========== 结果: {passed} 通过, {failed} 失败 ==========")
    return failed


if __name__ == "__main__":
    sys.exit(1 if run_tests() else 0)
