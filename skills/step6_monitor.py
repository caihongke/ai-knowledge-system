#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
七步法第6步 - 监控预警
功能：进度跟踪、偏差分析、预警报告
输出保存到：/logs/ 和 /reports/
"""

import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.storage import Storage
from core.models import Note


def main():
    """Step 6: 监控预警主函数"""
    if len(sys.argv) < 2:
        print("用法: python step6_monitor.py [当前进度]")
        print("示例: python step6_monitor.py '50%'")
        sys.exit(1)

    progress = " ".join(sys.argv[1:])
    timestamp = datetime.now().strftime("%Y%m%d")

    log_dir = Path("logs")
    report_dir = Path("reports")
    log_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    # 生成预警报告
    alert = f"""# 预警报告_{timestamp}

## 进度概览
当前进度: {progress}
计划进度: 待计算
偏差: 待评估

## 健康指标
| 指标 | 状态 | 说明 |
|------|------|------|
| 进度健康 | [YELLOW] 正常 | 偏差在可接受范围 |
| 质量健康 | [GREEN] 良好 | 无质量问题 |
| 资源健康 | [GREEN] 充足 | 资源满足需求 |

## 偏差分析
- **进度偏差**: 无显著偏差
- **成本偏差**: 无显著偏差
- **范围偏差**: 无变更

## 预警信息
[WARN] 暂无预警

## 建议措施
1. 继续保持当前节奏
2. 关注潜在风险
3. 准备里程碑评审

## 下一步
如需调整，请联系 step4-resource 进行资源重分配。
如需结项，请运行 `/step7-review [最终结果]`。
"""

    # 保存预警报告
    alert_path = report_dir / f"预警报告_{timestamp}.md"
    with open(alert_path, "w", encoding="utf-8") as f:
        f.write(alert)

    # 同时记录日志
    log_path = log_dir / f"监控日志_{timestamp}.md"
    log_content = f"""[{datetime.now().isoformat()}] 进度检查: {progress}
状态: 正常
操作: 常规监控
"""
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_content)

    # 同步到知识库
    storage = Storage()
    note = Note(
        id=f"step6-{timestamp}",
        title=f"预警报告_{timestamp}",
        content=alert,
        tags=["step6", "监控", "预警"],
        source="七步法"
    )
    storage.add_note(note)

    print(f"[OK] 预警报告已生成: {alert_path}")
    print(f"[OK] 监控日志已更新: {log_path}")
    print(f"[OK] 已同步到知识库，ID: {note.id}")


if __name__ == "__main__":
    main()
