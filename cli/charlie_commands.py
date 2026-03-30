"""查理编剧体系 CLI 命令"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

# 修复编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

console = Console()

# 尝试导入查理体系
try:
    import charlie
    CHARLIE_AVAILABLE = True
except ImportError:
    CHARLIE_AVAILABLE = False
    console.print("[yellow]Warning: charlie module not found[/yellow]")

charlie_app = typer.Typer(
    name="charlie",
    help="Charlie - 查理编剧体系 CLI",
    no_args_is_help=True,
)


@charlie_app.command("scenarios")
def list_scenarios():
    """列出所有可用场景"""
    if not CHARLIE_AVAILABLE:
        console.print("[red]Charlie not available[/red]")
        return

    scenarios = charlie.list_scenarios()

    table = Table(title="Charlie Scenes")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description", style="white")

    for s in scenarios:
        table.add_row(s["id"], s["name"], s["description"])

    console.print(table)


@charlie_app.command("config")
def show_config(
    scenario: str = typer.Option("novel_long", "--scenario", "-s", help="场景类型"),
):
    """查看场景配置"""
    if not CHARLIE_AVAILABLE:
        console.print("[red]Charlie not available[/red]")
        return

    config = charlie.get_scenario_config(scenario)

    console.print(f"\n[cyan]Scenario:[/cyan] {scenario}")
    console.print(f"[cyan]Name:[/cyan] {config['name']}")
    console.print(f"[cyan]Description:[/cyan] {config['description']}\n")

    console.print("[bold]Rules:[/bold]")
    for k, v in config["rules"].items():
        console.print(f"  - {k}: [green]{v}[/green]")

    console.print("\n[bold]Milestones:[/bold]")
    for ch, name in config["milestones"].items():
        console.print(f"  Chapter {ch}: {name}")


@charlie_app.command("init")
def init_project(
    title: str = typer.Argument(..., help="项目标题"),
    scenario: str = typer.Option("novel_long", "--scenario", "-s", help="场景类型"),
):
    """初始化新项目"""
    if not CHARLIE_AVAILABLE:
        console.print("[red]Charlie not available[/red]")
        return

    console.print(f"\n[green]Initializing project:[/green] {title}")
    console.print(f"[green]Scenario:[/green] {scenario}")

    # 创建项目结构
    project_dir = Path("projects") / title.replace(" ", "_")
    project_dir.mkdir(parents=True, exist_ok=True)

    # 生成基础档案
    story_data = {
        "title": title,
        "scenario": scenario,
        "protagonist": {},
        "villains": [],
        "causality": {},
        "foreshadowing": [],
        "foreshadowing回收": [],
        "cost_mechanism": {},
        "theme": {},
    }

    console.print(f"\n[green]Project created:[/green] {project_dir}")
    console.print("[yellow]Next: Use 'charlie review' to check story data[/yellow]")


@charlie_app.command("review")
def review_story(
    data_file: Optional[str] = typer.Argument(None, help="故事数据JSON文件"),
    scenario: str = typer.Option("novel_long", "--scenario", "-s", help="场景类型"),
):
    """审查故事数据"""
    if not CHARLIE_AVAILABLE:
        console.print("[red]Charlie not available[/red]")
        return

    import json

    # 读取数据
    if data_file:
        with open(data_file, encoding="utf-8") as f:
            story_data = json.load(f)
    else:
        # 使用示例数据
        story_data = {
            "protagonist": {
                "short_term_goal": "赚500万为母治病",
                "mid_term_goal": "证明寒门能出头",
                "goal_depends_on_system": False,
                "has_active_response": True,
            },
            "villains": [
                {
                    "motivation": "维护家族利益",
                    "has_arc": True,
                    "consequence": "被主角收购",
                }
            ],
            "causality": {"chapter_lock": True, "final_summary": True},
            "foreshadowing": ["母亲尿毒症", "系统秘密"],
            "foreshadowing回收": ["第80章换肾"],
            "cost_mechanism": {
                "protagonist": True,
                "villain": True,
                "system": True,
                "emotion": True,
            },
            "theme": {
                "core": "我命由我不由系统",
                "slogan": "我命由我不由系统",
                "all_serve": True,
                "climax升华": True,
            },
        }

    # 执行五大铁律检查
    result = charlie.quick_check_five_laws(story_data)

    console.print(f"\n[bold]Five Iron Laws Check[/bold] (scenario: {scenario})")
    console.print(f"Passed: {'[green]Yes[/green]' if result['passed'] else '[red]No[/red]'}")
    console.print(f"Score: [cyan]{result['score']:.0f}[/cyan]")

    if result.get("errors"):
        console.print("\n[bold red]Errors:[/bold red]")
        for e in result["errors"]:
            console.print(f"  - {e}")

    if result.get("warnings"):
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for w in result["warnings"]:
            console.print(f"  - {w}")

    # 扩展规则检查
    console.print("\n[bold]Expansion Rules[/bold]")

    # 因果锁
    causality = charlie.quick_check_causality(story_data)
    console.print(f"  Causality: {'[green]OK[/green]' if causality['passed'] else '[red]Fail[/red]'} ({causality['score']:.0f})")

    # 秘密压力
    secret = charlie.quick_check_secret_pressure(story_data)
    console.print(f"  Secret: {'[green]OK[/green]' if secret['passed'] else '[yellow]Warning[/yellow]'} ({secret['score']:.0f})")

    # 节奏红线
    rhythm = charlie.quick_check_rhythm(story_data, scenario)
    console.print(f"  Rhythm: {'[green]OK[/green]' if rhythm['passed'] else '[yellow]Warning[/yellow]'} ({rhythm['score']:.0f})")

    # 工业化规则
    industrial = charlie.quick_check_industrial(story_data, scenario)
    console.print(f"  Industrial: {'[green]OK[/green]' if industrial['passed'] else '[yellow]Warning[/yellow]'} ({industrial['score']:.0f})")


@charlie_app.command("checkpoint")
def check_milestone(
    chapter: int = typer.Argument(..., help="当前章节"),
    data_file: Optional[str] = typer.Option(None, "--file", "-f", help="故事数据文件"),
):
    """里程碑检查"""
    if not CHARLIE_AVAILABLE:
        console.print("[red]Charlie not available[/red]")
        return

    import json

    if data_file:
        with open(data_file, encoding="utf-8") as f:
            story_data = json.load(f)
    else:
        story_data = {}

    result = charlie.checkpoint(chapter, story_data)

    console.print(f"\n[bold]Milestone Check[/bold] - Chapter {chapter}")
    console.print(f"Milestone: [cyan]{result['milestone']['name']}[/cyan]")
    console.print(f"Status: {'[green]PASSED[/green]' if result['milestone']['passed'] else '[red]FAILED[/red]'}")
    console.print(f"Score: [cyan]{result['milestone']['score']:.0f}[/cyan]")
    console.print(f"Health: [cyan]{result['health_score']:.0f}[/cyan] - {result['status']}")


@charlie_app.command("create")
def create_content(
    title: str = typer.Argument(..., help="作品标题"),
    prompt: str = typer.Argument(..., help="创作提示词"),
    scenario: str = typer.Option("novel_long", "--scenario", "-s", help="场景类型"),
    chapters: int = typer.Option(3, "--chapters", "-c", help="章节数"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出文件"),
):
    """创作内容（创意区）"""
    if not CHARLIE_AVAILABLE:
        console.print("[red]Charlie not available[/red]")
        return

    console.print(f"\n[green]Creating:[/green] {title}")
    console.print(f"[green]Prompt:[/green] {prompt}")

    try:
        content = charlie.quick_create(title, prompt, scenario, chapters)

        if output:
            Path(output).write_text(content, encoding="utf-8")
            console.print(f"[green]Saved to:[/green] {output}")
        else:
            console.print("\n[bold]Generated Content:[/bold]")
            console.print(content[:500] + "..." if len(content) > 500 else content)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


def register_charlie_commands(app: typer.Typer):
    """注册到主CLI"""
    app.add_typer(charlie_app, name="charlie")