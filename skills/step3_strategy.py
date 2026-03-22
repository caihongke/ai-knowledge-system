#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
七步法第3步 - 策略规划
功能：WBS分解、排期、风险识别
输出保存到：/steps/step3/
"""

import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.storage import Storage
from core.models import Note


def main():
    """Step 3: 策略规划主函数"""
    if len(sys.argv) < 2:
        print("用法: python step3_strategy.py [WBS清单]")
        print("示例: python step3_strategy.py '任务1,任务2,任务3'")
        sys.exit(1)

    wbs_input = " ".join(sys.argv[1:])
    tasks = [t.strip() for t in wbs_input.split(",") if t.strip()]
    timestamp = datetime.now().strftime("%Y%m%d")

    output_dir = Path("steps/step3")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成策略清单
    wbs_content = "\n".join([f"{i+1}. {task}\n   - 负责人: 待定\n   - 截止时间: 待定\n   - 依赖: 无" for i, task in enumerate(tasks)])

    strategy = f"""# 策略清单_{timestamp}

## WBS工作分解结构
{wbs_content}

## 排期计划
| 任务 | 开始日期 | 结束日期 | 状态 |
|------|----------|----------|------|
{chr(10).join([f"| {t} | - | - | 未开始 |" for t in tasks])}

## 风险识别
| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| 进度延期 | 中 | 高 | 预留缓冲时间 |
| 资源不足 | 低 | 中 | 提前准备备选方案 |
| 需求变更 | 高 | 中 | 明确变更流程 |

## 关键路径
1. 任务1 → 任务2 → 任务3

## 下一步
请运行 `/step4-resource [策略清单]` 配置资源。
"""

    # 保存策略清单
    strategy_path = output_dir / f"策略清单_{timestamp}.md"
    with open(strategy_path, "w", encoding="utf-8") as f:
        f.write(strategy)

    # 同步到知识库
    storage = Storage()
    note = Note(
        id=f"step3-{timestamp}",
        title=f"策略清单_{timestamp}",
        content=strategy,
        tags=["step3", "策略", "WBS"],
        source="七步法"
    )
    storage.add_note(note)

    print(f"[OK] 策略清单已生成: {strategy_path}")
    print(f"[OK] 已同步到知识库，ID: {note.id}")
    print(f"\n共分解出 {len(tasks)} 个任务，请完善排期和风险信息。")


if __name__ == "__main__":
    main()
