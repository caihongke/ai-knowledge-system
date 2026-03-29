#!/usr/bin/env python3
"""七步法第2步 - 蓝图设计
功能：路径规划、里程碑设定、交付物定义
输出保存到：/steps/step2/
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.storage import Storage


def main():
    """Step 2: 蓝图设计主函数"""
    if len(sys.argv) < 2:
        print("用法: python step2_blueprint.py [目标]")
        print("示例: python step2_blueprint.py '完成Python基础学习'")
        sys.exit(1)

    goal = " ".join(sys.argv[1:])
    timestamp = datetime.now().strftime("%Y%m%d")

    output_dir = Path("steps/step2")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成蓝图
    blueprint = f"""# 蓝图设计_{timestamp}

## 目标
{goal}

## 路径规划
1. **阶段一：准备期** (第1-3天)
   - 任务：环境搭建、资源收集
   - 交付物：环境就绪确认单

2. **阶段二：执行期** (第4-20天)
   - 任务：核心内容学习/实践
   - 交付物：阶段性成果

3. **阶段三：收尾期** (第21-30天)
   - 任务：总结、复盘、归档
   - 交付物：结项报告

## 里程碑
- [ ] M1: 准备工作完成 (Day 3)
- [ ] M2: 中期检查通过 (Day 10)
- [ ] M3: 核心目标达成 (Day 20)
- [ ] M4: 项目正式结项 (Day 30)

## 交付物清单
1. 阶段报告（每阶段一份）
2. 问题日志
3. 结项报告
4. 复盘清单

## 下一步
请运行 `/step3-strategy [WBS清单]` 进行任务分解。
"""

    # 保存蓝图
    blueprint_path = output_dir / f"蓝图_{timestamp}.md"
    with open(blueprint_path, "w", encoding="utf-8") as f:
        f.write(blueprint)

    # 同步到知识库
    storage = Storage()
    note = storage.add_note(
        title=f"蓝图设计_{timestamp}",
        tags=["step2", "蓝图", "规划"],
        category="七步法",
        content=blueprint,
    )

    print(f"[OK] 蓝图已生成: {blueprint_path}")
    print(f"[OK] 已同步到知识库，ID: {note.id}")


if __name__ == "__main__":
    main()
