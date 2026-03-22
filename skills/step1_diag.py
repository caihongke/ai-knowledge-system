#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
七步法第1步 - 诊断与定义
功能：需求分析、SWOT分析、目标定义
输出保存到：/steps/step1/
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.storage import Storage
from core.models import Note


def main():
    """Step 1: 诊断与定义主函数"""
    if len(sys.argv) < 2:
        print("用法: python step1_diag.py [需求描述]")
        print("示例: python step1_diag.py '我想学习Python编程'")
        sys.exit(1)

    requirement = " ".join(sys.argv[1:])
    timestamp = datetime.now().strftime("%Y%m%d")

    # 确保输出目录存在
    output_dir = Path("steps/step1")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成诊断报告
    report = f"""# 诊断报告_{timestamp}

## 需求描述
{requirement}

## 分析流程
1. **信息收集**（5W1H）
   - What: {requirement}
   - Why: 待补充
   - Who: 待补充
   - When: 待补充
   - Where: 待补充
   - How: 待补充

2. **SWOT分析**
   - 优势 (Strengths): 待分析
   - 劣势 (Weaknesses): 待分析
   - 机会 (Opportunities): 待分析
   - 威胁 (Threats): 待分析

3. **SMART目标定义**
   - Specific: 待定义
   - Measurable: 待定义
   - Achievable: 待定义
   - Relevant: 待定义
   - Time-bound: 待定义

## 下一步行动
请运行 `/step2-blueprint [本报告路径]` 继续流程。
"""

    # 保存报告
    report_path = output_dir / f"诊断报告_{timestamp}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    # 同时保存到知识库
    storage = Storage()
    note = Note(
        id=f"step1-{timestamp}",
        title=f"诊断报告_{timestamp}",
        content=report,
        tags=["step1", "诊断", "需求分析"],
        source="七步法"
    )
    storage.add_note(note)

    print(f"[OK] 诊断报告已生成: {report_path}")
    print(f"[OK] 已同步到知识库，ID: {note.id}")
    print(f"\n请补充完善 5W1H 和 SWOT 分析内容后，继续执行 step2。")


if __name__ == "__main__":
    main()
