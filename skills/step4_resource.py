#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
七步法第4步 - 资源配置
功能：人力、时间、物资、预算配置
输出保存到：/steps/step4/
"""

import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.storage import Storage
from core.models import Note


def main():
    """Step 4: 资源配置主函数"""
    if len(sys.argv) < 2:
        print("用法: python step4_resource.py [策略清单路径]")
        print("示例: python step4_resource.py steps/step3/策略清单_20260321.md")
        sys.exit(1)

    strategy_file = sys.argv[1]
    timestamp = datetime.now().strftime("%Y%m%d")

    output_dir = Path("steps/step4")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成资源清单
    resource = f"""# 资源清单_{timestamp}

## 人力资源
| 角色 | 姓名 | 职责 | 投入比例 |
|------|------|------|----------|
| 项目负责人 | 待定 | 总体协调 | 50% |
| 执行人员 | 待定 | 具体执行 | 100% |
| 顾问支持 | 待定 | 咨询指导 | 20% |

## 时间资源
| 阶段 | 计划工时 | 实际工时 | 备注 |
|------|----------|----------|------|
| 准备期 | 8h | - | 待记录 |
| 执行期 | 40h | - | 待记录 |
| 收尾期 | 8h | - | 待记录 |

## 物资/工具资源
- [ ] 开发/学习环境
- [ ] 参考书籍/文档
- [ ] 在线课程/订阅
- [ ] 软件工具许可

## 预算
| 项目 | 预算 | 实际 | 差异 |
|------|------|------|------|
| 工具/软件 | 0 | 0 | 0 |
| 学习资源 | 0 | 0 | 0 |
| 其他 | 0 | 0 | 0 |
| **合计** | **0** | **0** | **0** |

## 依赖文件
基于: {strategy_file}

## 下一步
请运行 `/step5-execute [资源清单]` 开始执行。
"""

    # 保存资源清单
    resource_path = output_dir / f"资源清单_{timestamp}.md"
    with open(resource_path, "w", encoding="utf-8") as f:
        f.write(resource)

    # 同步到知识库
    storage = Storage()
    note = Note(
        id=f"step4-{timestamp}",
        title=f"资源清单_{timestamp}",
        content=resource,
        tags=["step4", "资源", "配置"],
        source="七步法"
    )
    storage.add_note(note)

    print(f"[OK] 资源清单已生成: {resource_path}")
    print(f"[OK] 已同步到知识库，ID: {note.id}")
    print(f"\n请完善资源配置信息。")


if __name__ == "__main__":
    main()
