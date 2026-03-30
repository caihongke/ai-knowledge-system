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


@charlie_app.command("audit")
def full_audit(
    data_file: str = typer.Option("story_data.json", "--file", "-f", help="故事数据文件"),
    scenario: str = typer.Option("novel_long", "--scenario", "-s", help="场景类型"),
):
    """全量审计（五大铁律+所有扩展规则）"""
    if not CHARLIE_AVAILABLE:
        console.print("[red]Charlie not available[/red]")
        return

    import json
    from pathlib import Path

    data_path = Path(data_file)
    if not data_path.exists():
        console.print(f"[red]File not found:[/red] {data_file}")
        return

    with open(data_path, encoding="utf-8") as f:
        story_data = json.load(f)

    console.print(f"\n[bold]Full Audit:[/bold] {story_data.get('title', 'Unknown')}")
    console.print(f"Scenario: {scenario}\n")

    # 五大铁律
    result = charlie.quick_check_five_laws(story_data)
    console.print(f"[bold]Five Iron Laws:[/bold]")
    console.print(f"  Passed: {'[green]YES[/green]' if result['passed'] else '[red]NO[/red]'}")
    console.print(f"  Score: [cyan]{result['score']:.0f}[/cyan]")

    # 扩展规则
    console.print(f"\n[bold]Expansion Rules:[/bold]")
    rules = [
        ("Causality", charlie.quick_check_causality),
        ("Secret Pressure", charlie.quick_check_secret_pressure),
        ("Rhythm", lambda d: charlie.quick_check_rhythm(d, scenario)),
        ("Industrial", lambda d: charlie.quick_check_industrial(d, scenario)),
    ]

    for name, fn in rules:
        r = fn(story_data)
        status = "OK" if r["passed"] else "WARN" if r.get("warnings") else "FAIL"
        console.print(f"  {name}: {status} ({r['score']:.0f})")

    console.print("\n[green]Audit complete![/green]")


@charlie_app.command("template")
def generate_template(
    output: str = typer.Option("story_template.json", "--output", "-o", help="输出文件"),
    scenario: str = typer.Option("novel_long", "--scenario", "-s", help="场景类型"),
):
    """生成故事数据模板"""
    if not CHARLIE_AVAILABLE:
        console.print("[red]Charlie not available[/red]")
        return

    import json

    # 根据场景生成不同模板
    if scenario == "novel_long":
        template = {
            "title": "作品标题",
            "scenario": "novel_long",
            "protagonist": {
                "name": "主角名",
                "short_term_goal": "短期目标",
                "mid_term_goal": "中期目标",
                "goal_depends_on_system": False,
                "has_active_response": True,
            },
            "villains": [
                {
                    "name": "反派名",
                    "motivation": "动机",
                    "action_line": "行动线",
                    "has_arc": True,
                    "consequence": "结局",
                }
            ],
            "causality": {"chapter_lock": True, "final_summary": True},
            "foreshadowing": ["伏笔1", "伏笔2"],
            "foreshadowing回收": [],
            "cost_mechanism": {
                "protagonist": True,
                "villain": True,
                "system": True,
                "emotion": True,
            },
            "theme": {
                "core": "核心主题",
                "slogan": "主题Slogan",
                "all_serve": True,
                "climax升华": True,
            },
        }
    else:
        template = {"scenario": scenario, "note": "Short drama template not implemented"}

    with open(output, "w", encoding="utf-8") as f:
        json.dump(template, f, ensure_ascii=False, indent=2)

    console.print(f"[green]Template saved to:[/green] {output}")


@charlie_app.command("rules")
def show_rules(
    rule_type: str = typer.Option(None, "--type", "-t", help="规则类型: five_laws/causality/secret/rhythm/industrial"),
):
    """查看规则说明"""
    if not CHARLIE_AVAILABLE:
        console.print("[red]Charlie not available[/red]")
        return

    console.print("\n[bold]Charlie Rules Reference[/bold]\n")

    rules_doc = {
        "five_laws": {
            "name": "五大铁律（不可变基准）",
            "rules": [
                "1. 主角主动驱动：主角必须有独立目标",
                "2. 反派非工具人：反派必须有独立行动线",
                "3. 因果闭环：章节必须有因果锁",
                "4. 代价守恒：获得必须付出",
                "5. 主题统一：全书围绕核心主题",
            ],
        },
        "causality": {
            "name": "因果锁规则",
            "rules": [
                "- A事件必须导致B事件",
                "- 反派行动必须有后果",
                "- 金手指使用必须有代价",
                "- 情感线必须有起伏",
            ],
        },
        "secret": {
            "name": "秘密压力曲线",
            "rules": [
                "- 核心秘密不暴露",
                "- 秘密分阶段解锁（每30章）",
                "- 秘密压力递增",
            ],
        },
        "rhythm": {
            "name": "节奏红线",
            "rules": [
                "- 黄金3章定生死",
                "- 章章有爽点",
                "- 每5章一小高潮",
                "- 每30章一大高潮",
            ],
        },
        "industrial": {
            "name": "工业化规则",
            "rules": [
                "- 双赛道不混淆",
                "- 无同质化",
                "- 结构可落地",
                "- 质量门禁",
            ],
        },
    }

    if rule_type and rule_type in rules_doc:
        r = rules_doc[rule_type]
        console.print(f"[cyan]{r['name']}[/cyan]")
        for line in r['rules']:
            console.print(f"  {line}")
    else:
        for key, r in rules_doc.items():
            console.print(f"[cyan]{r['name']}[/cyan]")
            for line in r['rules'][:2]:
                console.print(f"  {line}")
            console.print()


def register_charlie_commands(app: typer.Typer):
    """注册到主CLI"""
    app.add_typer(charlie_app, name="charlie")