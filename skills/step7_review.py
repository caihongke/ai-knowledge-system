#!/usr/bin/env python3
"""七步法第7步 - 验收与复盘
功能：效果评估、复盘总结、知识归档
输出保存到：/logs/ 和 /reports/（对 /steps/ 只读）
"""

import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.storage import Storage


def main():
    """Step 7: 验收与复盘主函数"""
    if len(sys.argv) < 2:
        print("用法: python step7_review.py [最终结果]")
        print("示例: python step7_review.py '项目按时完成，达成预期目标'")
        sys.exit(1)

    result = " ".join(sys.argv[1:])
    timestamp = datetime.now().strftime("%Y%m%d")
    project_name = f"项目_{timestamp}"

    log_dir = Path("logs")
    report_dir = Path("reports")
    archive_dir = Path(f"archive/{project_name}_{timestamp}")
    log_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    # 生成结项报告
    report = f"""# 结项报告_{timestamp}

## 项目信息
- 项目名称: {project_name}
- 结项日期: {timestamp}
- 最终结果: {result}

## 效果评估
| 目标 | 计划 | 实际 | 完成率 |
|------|------|------|--------|
| 目标1 | 100% | 100% | [OK] 100% |
| 目标2 | 100% | 100% | [OK] 100% |
| 目标3 | 100% | 100% | [OK] 100% |

**总体完成率: 100%**

## 复盘总结

### 成功经验 (3条)
1. 经验1:
2. 经验2:
3. 经验3:

### 失败教训 (3条)
1. 教训1:
2. 教训2:
3. 教训3:

### 意外事件
- 无

## 知识归档
所有过程文档已归档至: `{archive_dir}`

## 结项确认
- [ ] 所有交付物已验收
- [ ] 文档已归档
- [ ] 复盘已完成
- [ ] 经验已提炼

**状态: 已结项**
"""

    # 生成复盘清单
    checklist = f"""# 复盘清单_{timestamp}

## 项目检查清单

### 启动阶段
- [ ] 需求已明确
- [ ] SWOT分析已完成
- [ ] SMART目标已定义

### 规划阶段
- [ ] 蓝图已设计
- [ ] WBS已分解
- [ ] 资源已配置

### 执行阶段
- [ ] 每日待办已更新
- [ ] 问题已记录
- [ ] 变更已跟踪

### 监控阶段
- [ ] 进度已跟踪
- [ ] 偏差已分析
- [ ] 预警已处理

### 收尾阶段
- [ ] 效果已评估
- [ ] 经验已总结
- [ ] 知识已归档

## 未来项目建议
1. 提前识别风险
2. 保持文档同步
3. 定期复盘调整

---
生成时间: {timestamp}
"""

    # 保存报告
    report_path = report_dir / f"结项报告_{timestamp}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    checklist_path = report_dir / f"复盘清单_{timestamp}.md"
    with open(checklist_path, "w", encoding="utf-8") as f:
        f.write(checklist)

    # 归档步骤文档（只读复制）
    steps_dir = Path("steps")
    if steps_dir.exists():
        for step_dir in steps_dir.glob("step*"):
            if step_dir.is_dir():
                dest = archive_dir / step_dir.name
                shutil.copytree(step_dir, dest, dirs_exist_ok=True)

    # 同步到知识库
    storage = Storage()
    note = storage.add_note(
        title=f"结项报告_{timestamp}",
        tags=["step7", "结项", "复盘"],
        category="七步法",
        content=report,
    )

    print(f"[OK] 结项报告已生成: {report_path}")
    print(f"[OK] 复盘清单已生成: {checklist_path}")
    print(f"[OK] 项目文档已归档: {archive_dir}")
    print(f"[OK] 已同步到知识库，ID: {note.id}")
    print("\n[DONE] 七步法流程已完成！")


if __name__ == "__main__":
    main()
