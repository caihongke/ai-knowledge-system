#!/usr/bin/env python3
"""多智能体协同系统 - 健康监控模块
功能：自检与自愈、健康日志、飞书告警、日报生成
"""

import argparse
import shutil
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

# 项目根目录
BASE_DIR = Path(__file__).parent.resolve()
LOGS_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports"
STEPS_DIR = BASE_DIR / "steps"
HEALTH_LOG = LOGS_DIR / "health.log"
MAX_LOG_SIZE = 1 * 1024 * 1024  # 1MB日志轮转阈值
RETRY_TIMES = 3

# 关键文件清单
CRITICAL_FILES = [
    "CLAUDE.md",
    "feishu_upload.py",
    "agents.yaml",
]
COMMAND_FILES = [
    f".claude/commands/step{i}-{name}.md"
    for i, name in enumerate(
        ["", "diag", "blueprint", "strategy", "resource", "execute", "monitor", "review"],
        start=0,
    )
    if i >= 1
] + [".claude/commands/save_report.md"]

STEP_NAMES = {
    1: "问题诊断",
    2: "蓝图拆解",
    3: "策略路径",
    4: "资源保障",
    5: "执行推进",
    6: "监控调整",
    7: "验收复盘",
}


# ============================================================
# 配置加载
# ============================================================

def load_config():
    """从agents.yaml加载告警配置，失败则返回默认值"""
    config = {
        "feishu_webhook_url": "",
        "health_log_path": "logs/health.log",
        "daily_report_path": "reports/",
    }
    yaml_path = BASE_DIR / "agents.yaml"
    if not yaml_path.exists():
        return config

    try:
        import yaml
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        alerting = data.get("alerting", {})
        config["feishu_webhook_url"] = alerting.get("feishu_webhook_url", "")
        config["health_log_path"] = alerting.get("health_log_path", config["health_log_path"])
        config["daily_report_path"] = alerting.get("daily_report_path", config["daily_report_path"])
    except ImportError:
        # 无pyyaml，手动提取webhook URL
        try:
            text = yaml_path.read_text(encoding="utf-8")
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("feishu_webhook_url:"):
                    val = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                    if val:
                        config["feishu_webhook_url"] = val
        except Exception:
            pass
    except Exception:
        pass
    return config


# ============================================================
# 健康检查函数
# ============================================================

def check_disk_space():
    """检查磁盘可用空间"""
    usage = shutil.disk_usage(str(BASE_DIR))
    free_gb = usage.free / (1024 ** 3)
    total_gb = usage.total / (1024 ** 3)
    usage_pct = (usage.used / usage.total) * 100
    alert = free_gb < 0.5
    level = "ERROR" if alert else ("WARN" if free_gb < 2 else "OK")
    return {
        "check": "disk_space",
        "level": level,
        "free_gb": round(free_gb, 2),
        "total_gb": round(total_gb, 2),
        "usage_percent": round(usage_pct, 1),
        "message": f"磁盘空间: {round(free_gb,1)}GB可用 / {round(total_gb,1)}GB总计 ({round(usage_pct,1)}%已用)",
    }


def check_workspace_integrity():
    """验证关键文件完整性"""
    results = []
    for rel_path in CRITICAL_FILES + COMMAND_FILES:
        full_path = BASE_DIR / rel_path
        exists = full_path.exists()
        size = full_path.stat().st_size if exists else 0
        level = "OK" if (exists and size > 0) else "ERROR"
        results.append({
            "check": "file_integrity",
            "level": level,
            "file": rel_path,
            "exists": exists,
            "size": size,
            "message": f"{'✓' if level == 'OK' else '✗'} {rel_path} ({'OK' if level == 'OK' else '缺失或为空'})",
        })
    return results


def check_step_outputs():
    """检查各步骤产出物时间戳"""
    results = []
    now = datetime.now()
    for step_num, step_name in STEP_NAMES.items():
        step_dir = STEPS_DIR / f"step{step_num}"
        if not step_dir.exists():
            results.append({
                "check": "step_output",
                "level": "INFO",
                "step": step_num,
                "name": step_name,
                "message": f"Step{step_num}({step_name}): 尚未执行（目录不存在）",
                "latest_file": None,
                "last_modified": None,
                "stale": False,
            })
            continue

        # 查找最新的.md文件
        md_files = list(step_dir.glob("*.md"))
        if not md_files:
            results.append({
                "check": "step_output",
                "level": "INFO",
                "step": step_num,
                "name": step_name,
                "message": f"Step{step_num}({step_name}): 目录存在但无产出文件",
                "latest_file": None,
                "last_modified": None,
                "stale": False,
            })
            continue

        latest = max(md_files, key=lambda f: f.stat().st_mtime)
        mtime = datetime.fromtimestamp(latest.stat().st_mtime)
        age_hours = (now - mtime).total_seconds() / 3600
        stale = age_hours > 24

        level = "WARN" if stale else "OK"
        results.append({
            "check": "step_output",
            "level": level,
            "step": step_num,
            "name": step_name,
            "message": f"Step{step_num}({step_name}): 最新产出 {latest.name}，更新于 {mtime.strftime('%m-%d %H:%M')}{'（>24h，已过期）' if stale else ''}",
            "latest_file": str(latest.name),
            "last_modified": mtime.isoformat(),
            "stale": stale,
        })
    return results


# ============================================================
# 日志与告警
# ============================================================

def write_health_log(entries):
    """写入健康日志，超1MB自动轮转"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # 日志轮转
    if HEALTH_LOG.exists() and HEALTH_LOG.stat().st_size > MAX_LOG_SIZE:
        rotated = LOGS_DIR / "health.log.1"
        if rotated.exists():
            rotated.unlink()
        HEALTH_LOG.rename(rotated)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    for entry in entries:
        level = entry.get("level", "INFO")
        msg = entry.get("message", "")
        lines.append(f"[{timestamp}] [{level}] {msg}")

    with open(HEALTH_LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def send_feishu_alert(message, webhook_url):
    """通过飞书Webhook机器人发送告警"""
    if not webhook_url:
        return False

    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "AI Platform 健康告警"},
                "template": "red",
            },
            "elements": [
                {"tag": "markdown", "content": message},
            ],
        },
    }

    for i in range(RETRY_TIMES):
        try:
            resp = requests.post(webhook_url, json=payload, timeout=10)
            result = resp.json()
            if result.get("code") == 0 or result.get("StatusCode") == 0:
                return True
            print(f"飞书告警发送失败（第{i+1}次）: {result}")
        except Exception as e:
            print(f"飞书告警请求异常（第{i+1}次）: {e}")
        time.sleep(1)
    return False


# ============================================================
# 主流程
# ============================================================

def run_health_check(send_alerts=True):
    """运行完整健康检查"""
    config = load_config()
    all_entries = []

    # 1. 磁盘空间
    disk = check_disk_space()
    all_entries.append(disk)

    # 2. 工作区完整性
    integrity = check_workspace_integrity()
    all_entries.extend(integrity)

    # 3. 步骤产出检查
    steps = check_step_outputs()
    all_entries.extend(steps)

    # 写入日志
    write_health_log(all_entries)

    # 统计
    errors = [e for e in all_entries if e["level"] == "ERROR"]
    warns = [e for e in all_entries if e["level"] == "WARN"]
    oks = [e for e in all_entries if e["level"] == "OK"]
    infos = [e for e in all_entries if e["level"] == "INFO"]

    # 构建摘要
    summary_lines = [
        "# 系统健康检查报告",
        f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**状态**: {'正常' if not errors and not warns else '异常'}",
        "",
        "| 级别 | 数量 |",
        "|------|------|",
        f"| OK | {len(oks)} |",
        f"| INFO | {len(infos)} |",
        f"| WARN | {len(warns)} |",
        f"| ERROR | {len(errors)} |",
        "",
    ]

    if errors or warns:
        summary_lines.append("## 异常项")
        for e in errors + warns:
            summary_lines.append(f"- **[{e['level']}]** {e['message']}")
        summary_lines.append("")

    summary_lines.append("## 详细结果")
    for e in all_entries:
        summary_lines.append(f"- [{e['level']}] {e['message']}")

    summary = "\n".join(summary_lines)

    # 发送告警
    if send_alerts and (errors or warns):
        webhook_url = config.get("feishu_webhook_url", "")
        if webhook_url:
            alert_msg = f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            alert_msg += f"**ERROR**: {len(errors)} / **WARN**: {len(warns)}\n\n"
            for e in (errors + warns)[:5]:
                alert_msg += f"- [{e['level']}] {e['message']}\n"
            if len(errors) + len(warns) > 5:
                alert_msg += f"\n...共{len(errors)+len(warns)}项异常，请运行 `/health-check` 查看详情"
            send_feishu_alert(alert_msg, webhook_url)

    print(summary)
    return {"summary": summary, "errors": len(errors), "warns": len(warns)}


def generate_daily_report():
    """生成每日汇总日报"""
    now = datetime.now()
    yesterday = now - timedelta(days=1)

    report_lines = [
        "# 主Agent日报",
        f"**生成时间**: {now.strftime('%Y-%m-%d %H:%M')}",
        f"**统计周期**: {yesterday.strftime('%Y-%m-%d')} ~ {now.strftime('%Y-%m-%d')}",
        "",
    ]

    # 1. 步骤执行统计
    report_lines.append("## 步骤执行情况")
    report_lines.append("| 步骤 | 名称 | 产出文件数 | 最近更新 | 状态 |")
    report_lines.append("|------|------|-----------|---------|------|")

    total_files = 0
    active_steps = 0
    for step_num, step_name in STEP_NAMES.items():
        step_dir = STEPS_DIR / f"step{step_num}"
        if not step_dir.exists():
            report_lines.append(f"| {step_num} | {step_name} | 0 | - | 未启动 |")
            continue

        md_files = list(step_dir.glob("*.md"))
        count = len(md_files)
        total_files += count

        if md_files:
            latest = max(md_files, key=lambda f: f.stat().st_mtime)
            mtime = datetime.fromtimestamp(latest.stat().st_mtime)
            status = "活跃" if (now - mtime).total_seconds() < 86400 else "停滞"
            if status == "活跃":
                active_steps += 1
            report_lines.append(f"| {step_num} | {step_name} | {count} | {mtime.strftime('%m-%d %H:%M')} | {status} |")
        else:
            report_lines.append(f"| {step_num} | {step_name} | 0 | - | 空目录 |")

    report_lines.append("")

    # 2. 健康日志统计
    report_lines.append("## 健康日志统计")
    error_count = 0
    warn_count = 0
    total_checks = 0

    if HEALTH_LOG.exists():
        try:
            with open(HEALTH_LOG, encoding="utf-8") as f:
                for line in f:
                    # 仅统计24h内的日志
                    if line.startswith("["):
                        try:
                            ts_str = line[1:20]
                            ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                            if ts >= yesterday:
                                total_checks += 1
                                if "[ERROR]" in line:
                                    error_count += 1
                                elif "[WARN]" in line:
                                    warn_count += 1
                        except ValueError:
                            pass
        except Exception:
            pass

    if total_checks > 0:
        fail_rate = round((error_count + warn_count) / total_checks * 100, 1)
        report_lines.append(f"- 过去24h检查总次数: **{total_checks}**")
        report_lines.append(f"- ERROR: **{error_count}** / WARN: **{warn_count}**")
        report_lines.append(f"- 异常率: **{fail_rate}%**")
    else:
        report_lines.append("- 过去24h无健康检查记录")
    report_lines.append("")

    # 3. 磁盘空间
    disk = check_disk_space()
    report_lines.append("## 磁盘空间")
    report_lines.append(f"- {disk['message']}")
    report_lines.append("")

    # 4. 优化建议
    report_lines.append("## 优化建议")
    suggestions = []

    if active_steps == 0:
        suggestions.append("所有步骤均不活跃，建议启动新项目或继续推进当前项目")
    for step_num, step_name in STEP_NAMES.items():
        step_dir = STEPS_DIR / f"step{step_num}"
        if step_dir.exists():
            md_files = list(step_dir.glob("*.md"))
            if md_files:
                latest = max(md_files, key=lambda f: f.stat().st_mtime)
                age_days = (now - datetime.fromtimestamp(latest.stat().st_mtime)).days
                if age_days > 7:
                    suggestions.append(f"Step{step_num}({step_name}) 已{age_days}天未更新，建议检查是否需要推进")

    if disk["usage_percent"] > 80:
        suggestions.append(f"磁盘使用率{disk['usage_percent']}%，建议清理不必要的文件")

    if error_count > 5:
        suggestions.append(f"过去24h出现{error_count}次ERROR，建议排查系统问题")

    if not suggestions:
        suggestions.append("系统运行正常，暂无优化建议")

    for s in suggestions:
        report_lines.append(f"- {s}")

    report = "\n".join(report_lines)

    # 保存日报
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / f"daily_{now.strftime('%Y%m%d')}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    print(f"\n日报已保存至: {report_file}")
    return report


# ============================================================
# CLI入口
# ============================================================

def main():
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="AI Platform 健康监控")
    parser.add_argument("action", choices=["check", "report"], help="check=健康检查, report=日报生成")
    parser.add_argument("--no-alert", action="store_true", help="不发送飞书告警")
    args = parser.parse_args()

    if args.action == "check":
        run_health_check(send_alerts=not args.no_alert)
    elif args.action == "report":
        generate_daily_report()


if __name__ == "__main__":
    main()
