# -*- coding: utf-8 -*-
"""
创作系统CLI命令
与七步法框架整合
"""

import typer
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from core.creation_agents import ScriptShortAgent, ScriptLongAgent
from core.component_engine import ComponentEngine, ComponentNotFoundError
from core.script_guard import ScriptGuard

console = Console()

# 创建命令组
script_short_cmd = typer.Typer(name="短剧本", help="短视频剧本创作(3-5分钟)")
script_long_cmd = typer.Typer(name="网文", help="网文长篇创作(100万字+)")
component_cmd = typer.Typer(name="组件", help="工业化组件管理")


# ==================== 短剧本命令 ====================

@script_short_cmd.command("新建")
def short_create(
    title: str = typer.Argument(..., help="剧本标题"),
    platform: str = typer.Option("douyin", "--平台", "-p", help="目标平台: douyin/kuaishou/bilibili"),
    genre: str = typer.Option("剧情", "--类型", "-g", help="类型/题材")
):
    """创建新的短视频剧本项目"""
    agent = ScriptShortAgent()
    session = agent.create_project(title, platform, genre)

    console.print(Panel.fit(
        f"[green]✓[/green] 剧本项目已创建\n"
        f"[cyan]项目ID:[/cyan] {session.id}\n"
        f"[cyan]标题:[/cyan] {title}\n"
        f"[cyan]平台:[/cyan] {platform}\n"
        f"[cyan]类型:[/cyan] {genre}",
        title="短剧本 - 新建项目",
        border_style="green"
    ))

    console.print(f"\n[yellow]下一步:[/yellow] 运行 [cyan]短剧本 大纲 {session.id} "概念描述"[/cyan]")


@script_short_cmd.command("大纲")
def short_outline(
    project_id: str = typer.Argument(..., help="项目ID"),
    concept: str = typer.Argument(..., help="核心创意描述")
):
    """生成剧本大纲"""
    agent = ScriptShortAgent()
    outline = agent.generate_outline(project_id, concept)

    if "error" in outline:
        console.print(f"[red]✗[/red] {outline['error']}")
        return

    # 显示Hook选项
    table = Table(title="黄金3秒Hook设计")
    table.add_column("选项", style="cyan")
    table.add_column("类型", style="magenta")
    table.add_column("内容", style="green")
    table.add_column("预计完播率", style="yellow")

    for hook in outline.get("hook_candidates", []):
        table.add_row(hook["id"], hook["type"], hook["content"], hook["predicted_retention"])

    console.print(table)

    # 显示冲突设计
    console.print("\n[cyan]冲突密度设计:[/cyan]")
    for conflict in outline.get("conflict_points", []):
        console.print(f"  • {conflict['time']}: {conflict['type']}冲突，强度{conflict['intensity']}")

    console.print(f"\n[yellow]下一步:[/yellow] 运行 [cyan]短剧本 草稿 {project_id} --hook A[/cyan]")


@script_short_cmd.command("草稿")
def short_draft(
    project_id: str = typer.Argument(..., help="项目ID"),
    hook: str = typer.Option("A", "--hook", "-h", help="选择的Hook (A/B/C)")
):
    """生成剧本草稿"""
    agent = ScriptShortAgent()
    result = agent.generate_draft(project_id, hook)

    if "error" in result:
        console.print(f"[red]✗[/red] {result['error']}")
        if "violations" in result:
            console.print("\n[red]违规详情:[/red]")
            for v in result["violations"]:
                console.print(f"  • [{v['rule_id']}] {v['message']}")
        return

    console.print(Panel.fit(
        f"[green]✓[/green] 草稿已生成 (版本{result['draft_version']})\n\n"
        f"[cyan]内容预览:[/cyan]\n{result['content_preview']}",
        title="短剧本 - 草稿生成",
        border_style="green"
    ))


@script_short_cmd.command("列表")
def short_list():
    """列出所有短剧本项目"""
    import os
    from pathlib import Path

    projects_dir = Path("creation/short/projects")
    if not projects_dir.exists():
        console.print("[yellow]暂无项目[/yellow]")
        return

    table = Table(title="短视频剧本项目")
    table.add_column("项目ID", style="cyan")
    table.add_column("标题", style="green")
    table.add_column("平台", style="magenta")
    table.add_column("状态", style="yellow")

    for project_dir in sorted(projects_dir.iterdir()):
        if project_dir.is_dir():
            session_file = project_dir / "session.json"
            if session_file.exists():
                import json
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                table.add_row(
                    data.get("id", "")[:20] + "...",
                    data.get("title", "未知"),
                    data.get("platform", "-"),
                    data.get("status", "draft")
                )

    console.print(table)


# ==================== 网文命令 ====================

@script_long_cmd.command("新建")
def long_create(
    title: str = typer.Argument(..., help="作品标题"),
    platform: str = typer.Option("起点", "--平台", "-p", help="目标平台"),
    genre: str = typer.Option("玄幻", "--类型", "-g", help="类型/题材"),
    words: int = typer.Option(100, "--字数", "-w", help="预计总字数(万字)")
):
    """创建新的网文项目"""
    agent = ScriptLongAgent()
    session = agent.create_project(title, platform, genre, words)

    console.print(Panel.fit(
        f"[green]✓[/green] 网文项目已创建\n"
        f"[cyan]项目ID:[/cyan] {session.id}\n"
        f"[cyan]标题:[/cyan] {title}\n"
        f"[cyan]平台:[/cyan] {platform}\n"
        f"[cyan]类型:[/cyan] {genre}\n"
        f"[cyan]目标字数:[/cyan] {words}万字",
        title="网文 - 新建项目",
        border_style="green"
    ))


@script_long_cmd.command("世界观")
def long_world(
    project_id: str = typer.Argument(..., help="项目ID"),
    concept: str = typer.Argument(..., help="世界观概念")
):
    """设计世界观"""
    agent = ScriptLongAgent()
    result = agent.design_world(project_id, concept)

    if "error" in result:
        console.print(f"[red]✗[/red] {result['error']}")
        return

    console.print(Panel.fit(
        f"[green]✓[/green] 世界观已设计\n\n"
        f"[cyan]概念:[/cyan] {result['world_setting']['concept']}\n"
        f"[cyan]势力数量:[/cyan] {len(result['world_setting']['factions'])}\n"
        f"[cyan]规则体系:[/cyan] {', '.join(result['world_setting']['rules'].keys())}",
        title="网文 - 世界观",
        border_style="green"
    ))


@script_long_cmd.command("角色")
def long_character(
    project_id: str = typer.Argument(..., help="项目ID"),
    name: str = typer.Argument(..., help="角色名"),
    profile: str = typer.Argument(..., help="人物小传")
):
    """创建角色"""
    agent = ScriptLongAgent()
    result = agent.create_character(project_id, name, profile)

    if "error" in result:
        console.print(f"[red]✗[/red] {result['error']}")
        return

    console.print(f"[green]✓[/green] 角色创建成功: {name} (ID: {result['character_id']})")


@script_long_cmd.command("分卷")
def long_volumes(
    project_id: str = typer.Argument(..., help="项目ID")
):
    """规划分卷结构"""
    agent = ScriptLongAgent()

    # 默认5卷结构
    volumes = [
        {"name": "第一卷:觉醒", "words": 150000, "key_event": "主角获得金手指", "emotion": "憋屈→爆发"},
        {"name": "第二卷:崛起", "words": 200000, "key_event": "建立势力", "emotion": "上升"},
        {"name": "第三卷:转折", "words": 200000, "key_event": "重大挫折", "emotion": "低谷"},
        {"name": "第四卷:突破", "words": 250000, "key_event": "实力质变", "emotion": "高潮"},
        {"name": "第五卷:巅峰", "words": 200000, "key_event": "最终决战", "emotion": "大高潮"}
    ]

    result = agent.plan_volumes(project_id, volumes)

    table = Table(title="分卷规划")
    table.add_column("卷名", style="cyan")
    table.add_column("字数", style="magenta")
    table.add_column("核心事件", style="green")
    table.add_column("情绪基调", style="yellow")

    for v in result.get("volumes", []):
        table.add_row(v["name"], f"{v['words']//10000}万字", v["key_event"], v["emotion"])

    console.print(table)
    console.print(f"\n[cyan]总计:[/cyan] {result.get('total_words', 0)//10000}万字")


# ==================== 组件命令 ====================

@component_cmd.command("列表")
def component_list(
    category: Optional[str] = typer.Option(None, "--分类", "-c", help="分类筛选: character/scene/payoff")
):
    """列出可用组件"""
    engine = ComponentEngine()

    categories = ["character", "scene", "payoff"] if not category else [category]

    for cat in categories:
        table = Table(title=f"{cat.upper()} 组件")
        table.add_column("ID", style="cyan")
        table.add_column("名称", style="green")
        table.add_column("标签", style="magenta")

        for comp in engine.component_library.get(cat, []):
            table.add_row(comp.id, comp.name, ", ".join(comp.tags[:3]))

        console.print(table)
        console.print()


@component_cmd.command("加载")
def component_load(
    component_id: str = typer.Argument(..., help="组件ID")
):
    """加载组件到当前项目"""
    engine = ComponentEngine()

    try:
        result = engine.load_component(component_id)
        console.print(Panel.fit(
            f"[green]✓[/green] 组件已加载\n"
            f"[cyan]名称:[/cyan] {result['name']}\n"
            f"[cyan]分类:[/cyan] {result['category']}",
            title="组件加载",
            border_style="green"
        ))
    except Exception as e:
        console.print(f"[red]✗[/red] 加载失败: {e}")


@component_cmd.command("推荐")
def component_suggest(
    genre: str = typer.Argument(..., help="类型/题材"),
    effect: str = typer.Argument(..., help="目标效果")
):
    """推荐适合的组件组合"""
    engine = ComponentEngine()
    suggestions = engine.suggest_components(genre, effect)

    table = Table(title=f"推荐组件 - {genre} / {effect}")
    table.add_column("ID", style="cyan")
    table.add_column("名称", style="green")
    table.add_column("分类", style="magenta")
    table.add_column("推荐理由", style="yellow")

    for s in suggestions:
        table.add_row(s["id"], s["name"], s["category"], s["reason"])

    console.print(table)


# 便捷函数：注册到主CLI
def register_creation_commands(app: typer.Typer):
    """将创作命令注册到主CLI"""
    app.add_typer(script_short_cmd, name="短剧本")
    app.add_typer(script_long_cmd, name="网文")
    app.add_typer(component_cmd, name="组件")


if __name__ == "__main__":
    # 测试模式
    test_app = typer.Typer()
    register_creation_commands(test_app)
    test_app()
