#!/usr/bin/env python3
"""七步法第5步 - 执行管理
功能：每日待办、问题日志、变更记录
输出保存到：/steps/step5/
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import Note
from core.storage import Storage


def main():
    """Step 5: 执行管理主函数"""
    if len(sys.argv) < 2:
        print("用法: python step5_execute.py [资源清单路径]")
        print("示例: python step5_execute.py steps/step4/资源清单_20260321.md")
        sys.exit(1)

    resource_file = sys.argv[1]
    timestamp = datetime.now().strftime("%Y%m%d")

    output_dir = Path("steps/step5")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成每日待办
    todo = f"""# 每日待办_{timestamp}

## 今日任务
- [ ] 任务1:
- [ ] 任务2:
- [ ] 任务3:

## 昨日完成
- [ ]

## 阻塞问题
| 问题 | 优先级 | 状态 | 备注 |
|------|--------|------|------|
| | 高 | 待解决 | |

## 变更记录
| 时间 | 变更内容 | 影响 | 批准人 |
|------|----------|------|--------|
| | | | |

## 执行统计
- 计划任务数: 3
- 完成任务数: 0
- 完成率: 0%

## 依赖文件
基于: {resource_file}

---
**提示**: 每天更新此文件，记录实际执行情况。
"""

    # 保存每日待办
    todo_path = output_dir / f"每日待办_{timestamp}.md"
    with open(todo_path, "w", encoding="utf-8") as f:
        f.write(todo)

    # 同步到知识库
    storage = Storage()
    note = Note(
        id=f"step5-{timestamp}",
        title=f"每日待办_{timestamp}",
        content=todo,
        tags=["step5", "执行", "待办"],
        source="七步法",
    )
    storage.add_note(note)

    print(f"[OK] 每日待办已生成: {todo_path}")
    print(f"[OK] 已同步到知识库，ID: {note.id}")
    print("\n请每天更新任务完成情况。")


if __name__ == "__main__":
    main()
