"""分析系统CLI命令
story-analyzer 和 iteration-engine 的命令接口
"""

from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.creation_agents import ScriptLongAgent, ScriptShortAgent
from core.creation_bridge import CreationBridge
from core.iteration_engine import IterationEngine
from core.story_analyzer import StoryAnalyzer

console = Console()

# 创建命令组
analysis_cmd = typer.Typer(name="分析", help="拉片分析与迭代优化")
report_cmd = typer.Typer(name="报告", help="创作报告生成")


# ==================== 分析命令 ====================

@analysis_cmd.command("拉片")
def analyze_work(
    project_id: str = typer.Argument(..., help="项目ID"),
    source: str = typer.Option("自有作品", "--来源", "-s", help="作品来源: 自有作品/竞品作品"),
):
    """对作品进行拉片分析"""
    # 判断项目类型
    track = "short" if project_id.startswith("short_") else "long"

    # 加载项目
    if track == "short":
        agent = ScriptShortAgent()
    else:
        agent = ScriptLongAgent()

    session = agent._load_session(project_id)
    if not session:
        console.print(f"[red]✗[/red] 项目 {project_id} 不存在")
        return

    # 获取内容
    if not session.drafts:
        console.print("[red]✗[/red] 项目没有草稿，先生成草稿")
        return

    content = session.drafts[-1].content

    # 分析
    analyzer = StoryAnalyzer()
    report = analyzer.analyze(
        content=content,
        title=session.title,
        content_type=track,
        source=source,
    )

    # 显示结果
    console.print(Panel.fit(
        f"[cyan]作品:[/cyan] {session.title}\n"
        f"[cyan]类型:[/cyan] {track}\n"
        f"[cyan]来源:[/cyan] {source}",
        title="拉片分析",
        border_style="blue",
    ))

    # 核心指标
    table = Table(title="核心指标")
    table.add_column("指标", style="cyan")
    table.add_column("得分", style="green")
    table.add_column("评价", style="yellow")

    # Hook评分
    hook_eval = "优秀" if report.hook_score >= 8 else "良好" if report.hook_score >= 6 else "需改进"
    table.add_row("Hook吸引力", f"{report.hook_score:.1f}/10", hook_eval)

    # 冲突密度
    density_eval = "密集" if report.conflict_density >= 0.6 else "适中" if report.conflict_density >= 0.4 else "稀疏"
    table.add_row("冲突密度", f"{report.conflict_density:.2f}/千字", density_eval)

    # 结构完整度
    structure_eval = "完整" if report.structure_compliance >= 80 else "基本完整" if report.structure_compliance >= 60 else "需完善"
    table.add_row("结构完整度", f"{report.structure_compliance:.0f}%", structure_eval)

    console.print(table)

    # 情绪曲线
    console.print("\n[cyan]情绪曲线:[/cyan]")
    for i, val in enumerate(report.emotion_curve):
        bar = "█" * int(val)
        console.print(f"  节点{i:2d}: {bar} {val:.1f}")

    # 改进建议
    console.print("\n[cyan]改进建议:[/cyan]")
    for suggestion in report.improvement_suggestions:
        console.print(f"  • {suggestion}")

    # 导出报告
    output_path = analyzer.export_report(report)
    console.print(f"\n[green]✓[/green] 分析报告已保存: {output_path}")

    # 提示下一步
    console.print(f"\n[yellow]下一步:[/yellow] 运行 [cyan]分析 迭代 {project_id}[/cyan]")


@analysis_cmd.command("迭代")
def analyze_iteration(
    project_id: str = typer.Argument(..., help="项目ID"),
    target_hook: float | None = typer.Option(None, "--目标-hook", help="目标Hook得分"),
    target_structure: float | None = typer.Option(None, "--目标结构", help="目标结构完整度"),
):
    """生成迭代优化方案"""
    track = "short" if project_id.startswith("short_") else "long"

    # 加载项目
    if track == "short":
        agent = ScriptShortAgent()
    else:
        agent = ScriptLongAgent()

    session = agent._load_session(project_id)
    if not session or not session.drafts:
        console.print("[red]✗[/red] 项目不存在或无草稿")
        return

    # 获取上次的分析结果
    content = session.drafts[-1].content
    analyzer = StoryAnalyzer()
    report = analyzer.analyze(content, session.title, track)

    # 差距分析
    engine = IterationEngine(track=track)

    custom_targets = {}
    if target_hook:
        custom_targets["hook_score"] = target_hook
    if target_structure:
        custom_targets["structure_compliance"] = target_structure

    gap = engine.analyze_gap(report, custom_targets or None)

    # 显示差距
    console.print(Panel.fit(
        f"[cyan]作品:[/cyan] {session.title}\n"
        f"[cyan]当前迭代:[/cyan] 第{len(session.iterations) + 1}轮",
        title="迭代分析",
        border_style="blue",
    ))

    table = Table(title="差距分析")
    table.add_column("维度", style="cyan")
    table.add_column("当前", style="green")
    table.add_column("目标", style="blue")
    table.add_column("差距", style="red")

    for dim, current in gap.current_scores.items():
        target = gap.target_scores.get(dim, 0)
        gap_val = gap.gaps.get(dim, 0)
        gap_str = f"-{gap_val:.1f}" if gap_val > 0 else "✓"
        table.add_row(dim, f"{current:.1f}", f"{target:.1f}", gap_str)

    console.print(table)

    # 生成改进方案
    plan = engine.generate_improvement_plan(gap)

    console.print("\n[cyan]改进策略:[/cyan]")
    for i, strategy in enumerate(plan.strategies, 1):
        console.print(f"\n  {i}. [green]{strategy['name']}[/green] ({strategy['effort']})")
        console.print(f"     行动: {strategy['action']}")
        console.print(f"     影响: {strategy['impact']}")

    console.print(f"\n[cyan]预计工作量:[/cyan] {plan.estimated_effort}")
    console.print(f"[cyan]风险等级:[/cyan] {plan.risk_level}")

    # 记录迭代
    record = engine.create_iteration_record(
        session_id=project_id,
        trigger="拉片分析后优化",
        gap=gap,
        plan=plan,
    )

    session.iterations.append(record)
    agent._save_session(session)

    console.print(f"\n[green]✓[/green] 迭代记录已保存 (ID: {record.iteration_id})")


@analysis_cmd.command("对比")
def analyze_compare(
    project_id: str = typer.Argument(..., help="项目ID"),
    benchmark_id: str = typer.Argument(..., help="对标作品项目ID"),
):
    """与对标作品对比分析"""
    console.print("[yellow]对比分析功能开发中...[/yellow]")
    console.print(f"项目: {project_id}")
    console.print(f"对标: {benchmark_id}")


# ==================== 报告命令 ====================

@report_cmd.command("个人")
def report_personal():
    """生成个人创作报告"""
    from pathlib import Path

    # 收集所有创作项目
    sessions = []
    reports = []

    # 加载短视频项目
    short_dir = Path("creation/short/projects")
    if short_dir.exists():
        for project_dir in short_dir.iterdir():
            if project_dir.is_dir():
                agent = ScriptShortAgent()
                session = agent._load_session(project_dir.name)
                if session:
                    sessions.append(session)

    # 加载网文项目
    long_dir = Path("creation/long/projects")
    if long_dir.exists():
        for project_dir in long_dir.iterdir():
            if project_dir.is_dir():
                agent = ScriptLongAgent()
                session = agent._load_session(project_dir.name)
                if session:
                    sessions.append(session)

    if not sessions:
        console.print("[yellow]暂无创作数据，请先创建项目[/yellow]")
        return

    # 生成报告
    engine = IterationEngine()

    # 模拟一些报告数据
    for session in sessions:
        if session.drafts:
            analyzer = StoryAnalyzer()
            report = analyzer.analyze(
                session.drafts[-1].content,
                session.title,
                session.track,
            )
            reports.append(report)

    report_text = engine.generate_personal_report(sessions, reports)

    # 保存报告
    report_path = f"reports/个人创作报告_{datetime.now().strftime('%Y%m%d')}.md"
    Path(report_path).parent.mkdir(exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    console.print(Panel.fit(
        report_text[:1000] + "...",
        title="个人创作报告",
        border_style="green",
    ))

    console.print(f"\n[green]✓[/green] 报告已保存: {report_path}")


@report_cmd.command("沉淀")
def report_export(
    project_id: str = typer.Argument(..., help="项目ID"),
):
    """将创作沉淀到知识库"""
    track = "short" if project_id.startswith("short_") else "long"

    if track == "short":
        agent = ScriptShortAgent()
    else:
        agent = ScriptLongAgent()

    session = agent._load_session(project_id)
    if not session:
        console.print("[red]✗[/red] 项目不存在")
        return

    # 导出到知识库
    bridge = CreationBridge()
    note_ids = bridge.export_creation_to_knowledge(session)

    console.print(f"[green]✓[/green] 已创建 {len(note_ids)} 条知识库笔记:")
    for note_id in note_ids:
        console.print(f"  • {note_id}")

    # 设置复习计划
    review_result = bridge.schedule_creation_review(session)
    console.print(f"\n[green]✓[/green] {review_result}")


# 便捷函数
def register_analysis_commands(app: typer.Typer):
    """注册分析命令到主CLI"""
    app.add_typer(analysis_cmd)
    app.add_typer(report_cmd)


if __name__ == "__main__":
    test_app = typer.Typer()
    register_analysis_commands(test_app)
    test_app()
