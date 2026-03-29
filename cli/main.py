# -*- coding: utf-8 -*-
"""AI自学知识管理系统 - CLI 入口"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from core.storage import Storage
from core.spaced_repetition import SpacedRepetition

# 修复 Windows GBK 编码问题
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

app = typer.Typer(
    name="akm",
    help="AI Knowledge Manager - 你的AI自学知识管理助手",
    no_args_is_help=True,
)

console = Console(force_terminal=True)
storage = Storage()
review_engine = SpacedRepetition()

# --- 子命令组 ---

kb_app = typer.Typer(help="知识库管理：笔记的增删改查与检索")
review_app = typer.Typer(help="间隔复习：基于艾宾浩斯遗忘曲线的复习提醒")
learn_app = typer.Typer(help="AI学习：智能学习路径推荐")
sync_app = typer.Typer(help="云端同步：将知识库同步到飞书")

app.add_typer(kb_app, name="笔记")
app.add_typer(review_app, name="复习")
app.add_typer(learn_app, name="学习")
app.add_typer(sync_app, name="同步")

# --- 系统子命令组 ---
sys_app = typer.Typer(help="系统管理：成本监控、健康检查")
app.add_typer(sys_app, name="系统")


# --- kb 命令：真实实现 ---

@kb_app.command("添加")
def kb_add(
    title: str = typer.Argument(help="笔记标题"),
    tags: str = typer.Option("", "--tags", "-t", help="标签，逗号分隔"),
    category: str = typer.Option("default", "--category", "-c", help="分类"),
    content: str = typer.Option("", "--content", help="笔记内容（可选，不填则打开编辑器）"),
):
    """新建一条笔记"""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    if not content:
        # 打开临时文件让用户编辑
        editor = os.environ.get("EDITOR", "notepad" if os.name == "nt" else "vim")
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False, encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            tmp_path = f.name
        try:
            subprocess.run([editor, tmp_path], check=True)
            with open(tmp_path, encoding="utf-8") as f:
                content = f.read()
            # 去掉自动生成的标题行（存储层会加）
            lines = content.split("\n")
            if lines and lines[0].strip() == f"# {title}":
                content = "\n".join(lines[1:]).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            content = ""
        finally:
            os.unlink(tmp_path)

    note = storage.add_note(title, tag_list, category, content)
    review_engine.register(note.id)
    console.print(f"[green][OK][/green] 笔记已创建: [bold]{note.title}[/bold] (ID: {note.id})")
    if tag_list:
        console.print(f"  标签: {', '.join(tag_list)}")


@kb_app.command("列表")
def kb_list(
    tag: str = typer.Option("", "--tag", help="按标签筛选"),
    category: str = typer.Option("", "--category", help="按分类筛选"),
):
    """列出所有笔记"""
    notes = storage.list_notes(tag=tag, category=category)
    if not notes:
        console.print("[yellow]暂无笔记[/yellow]")
        return

    table = Table(title="知识库笔记")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("标题", style="bold")
    table.add_column("标签", style="green")
    table.add_column("分类", style="magenta")
    table.add_column("更新时间", style="dim")

    for note in notes:
        table.add_row(
            note.id,
            note.title,
            ", ".join(note.tags),
            note.category,
            note.updated_at[:10],
        )
    console.print(table)
    console.print(f"共 {len(notes)} 条笔记")


@kb_app.command("查看")
def kb_show(note_id: str = typer.Argument(help="笔记ID")):
    """查看笔记详情"""
    note = storage.get_note(note_id)
    if not note:
        console.print(f"[red][ERR] 笔记不存在: {note_id}[/red]")
        raise typer.Exit(1)

    content = storage.get_note_content(note)
    console.print(f"[dim]ID: {note.id} | 分类: {note.category} | 标签: {', '.join(note.tags)}[/dim]")
    console.print(f"[dim]创建: {note.created_at} | 更新: {note.updated_at}[/dim]")
    console.print("-" * 50)
    console.print(Markdown(content))


@kb_app.command("搜索")
def kb_search(keyword: str = typer.Argument(help="搜索关键词")):
    """全文检索笔记"""
    results = storage.search_notes(keyword)
    if not results:
        console.print(f"[yellow]未找到包含 \"{keyword}\" 的笔记[/yellow]")
        return

    table = Table(title=f"搜索结果: \"{keyword}\"")
    table.add_column("ID", style="cyan")
    table.add_column("标题", style="bold")
    table.add_column("匹配位置", style="green")
    table.add_column("标签")

    for r in results:
        note = r["note"]
        table.add_row(note.id, note.title, r["match"], ", ".join(note.tags))
    console.print(table)
    console.print(f"共 {len(results)} 条结果")


@kb_app.command("编辑")
def kb_edit(note_id: str = typer.Argument(help="笔记ID")):
    """编辑笔记"""
    note = storage.get_note(note_id)
    if not note:
        console.print(f"[red][ERR] 笔记不存在: {note_id}[/red]")
        raise typer.Exit(1)

    from core.config import Config
    file_path = Config.KNOWLEDGE_DIR / note.file_path
    editor = os.environ.get("EDITOR", "notepad" if os.name == "nt" else "vim")
    try:
        subprocess.run([editor, str(file_path)], check=True)
        storage.update_note(note_id)  # 刷新 updated_at
        console.print(f"[green][OK][/green] 笔记已更新: {note.title}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        console.print(f"[red][ERR] 无法打开编辑器: {e}[/red]")


@kb_app.command("删除")
def kb_delete(note_id: str = typer.Argument(help="笔记ID")):
    """删除笔记"""
    note = storage.get_note(note_id)
    if not note:
        console.print(f"[red][ERR] 笔记不存在: {note_id}[/red]")
        raise typer.Exit(1)

    confirm = typer.confirm(f"确定删除笔记 \"{note.title}\" ({note_id})?")
    if not confirm:
        console.print("已取消")
        return

    storage.delete_note(note_id)
    review_engine.unregister(note_id)
    console.print(f"[green][OK][/green] 笔记已删除: {note.title}")


@kb_app.command("标签")
def kb_tags():
    """查看所有标签"""
    tags = storage.get_all_tags()
    if not tags:
        console.print("[yellow]暂无标签[/yellow]")
        return

    table = Table(title="标签统计")
    table.add_column("标签", style="green")
    table.add_column("笔记数", style="cyan", justify="right")

    for tag, count in tags.items():
        table.add_row(tag, str(count))
    console.print(table)


# --- review 子命令 ---

@review_app.command("今日")
def review_today():
    """查看今日待复习笔记"""
    due_ids = review_engine.get_today_reviews()
    if not due_ids:
        console.print("[green]今日无待复习笔记，继续保持！[/green]")
        return

    table = Table(title="今日待复习")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("标题", style="bold")
    table.add_column("已复习次数", justify="right")
    table.add_column("标签", style="green")

    for nid in due_ids:
        note = storage.get_note(nid)
        info = review_engine.get_note_info(nid)
        if note and info:
            table.add_row(
                nid, note.title,
                str(info["review_count"]),
                ", ".join(note.tags),
            )
    console.print(table)
    console.print(f"共 {len(due_ids)} 条待复习")


@review_app.command("完成")
def review_done(note_id: str = typer.Argument(help="笔记ID")):
    """标记笔记复习完成"""
    note = storage.get_note(note_id)
    if not note:
        console.print(f"[red][ERR] 笔记不存在: {note_id}[/red]")
        raise typer.Exit(1)

    next_date = review_engine.mark_done(note_id)
    if next_date == "mastered":
        console.print(f"[green][OK][/green] {note.title} — 已掌握！无需继续复习")
    elif next_date:
        console.print(f"[green][OK][/green] {note.title} — 下次复习: {next_date}")
    else:
        console.print(f"[yellow]该笔记不在复习计划中[/yellow]")


@review_app.command("统计")
def review_stats():
    """复习统计"""
    stats = review_engine.get_stats()

    table = Table(title="复习统计")
    table.add_column("指标", style="bold")
    table.add_column("数值", justify="right", style="cyan")
    table.add_row("纳入复习总数", str(stats["total"]))
    table.add_row("今日待复习", str(stats["due_today"]))
    table.add_row("学习中", str(stats["in_progress"]))
    table.add_row("已掌握", str(stats["mastered"]))
    console.print(table)


# --- learn 子命令 ---

@learn_app.command("建议")
def learn_suggest():
    """生成学习路径建议（AI 增强版）"""
    from core.ai_engine import AIEngine
    engine = AIEngine()
    result = engine.analyze()

    # 显示 AI 状态
    if result.ai_available:
        console.print("[dim][AI 模式: 已启用 Ollama 智能分析][/dim]\n")
    else:
        console.print("[dim][规则模式: Ollama 未运行，使用本地规则引擎][/dim]\n")

    if result.status == "empty":
        console.print("[yellow]知识库为空[/yellow]")
        console.print(result.summary)
    else:
        console.print(f"[bold]{result.summary}[/bold]\n")

        # 知识覆盖图
        if result.knowledge_map:
            km_table = Table(title="知识覆盖度")
            km_table.add_column("领域", style="green")
            km_table.add_column("笔记数", justify="right", style="cyan")
            km_table.add_column("状态")
            for tag, count in result.knowledge_map.items():
                status = "[green]强项[/green]" if count >= 3 else "[yellow]薄弱[/yellow]" if count == 1 else "一般"
                km_table.add_row(tag, str(count), status)
            console.print(km_table)

        # 复习健康度
        rh = result.review_health
        if rh:
            console.print(f"\n复习状态: 学习中 {rh.get('in_progress', 0)} / 已掌握 {rh.get('mastered', 0)} / 今日待复习 {rh.get('due_today', 0)}")

    # AI 深度洞察（如果有）
    if result.ai_insights:
        console.print(f"\n[bold cyan]AI 洞察:[/bold cyan]")
        console.print(result.ai_insights)

    # 学习建议
    if result.suggestions:
        console.print()
        sg_table = Table(title="学习建议")
        sg_table.add_column("#", style="dim", justify="right")
        sg_table.add_column("推荐主题", style="bold")
        sg_table.add_column("理由")
        sg_table.add_column("优先级", justify="center")
        for i, s in enumerate(result.suggestions, 1):
            p = s["priority"]
            p_style = "[red]高[/red]" if p == "高" else "[yellow]中[/yellow]" if p == "中" else "[dim]低[/dim]"
            sg_table.add_row(str(i), s["topic"], s["reason"], p_style)
        console.print(sg_table)


@learn_app.command("问答")
def learn_ask(
    question: str = typer.Argument(..., help="问题内容"),
):
    """基于知识库问答（需要 Ollama）"""
    from core.ai_engine import AIEngine
    engine = AIEngine()

    if not engine.ai_available:
        console.print("[red][错误] Ollama 服务未启动[/red]")
        console.print("请运行: ollama serve")
        console.print("或访问 https://ollama.com 安装 Ollama")
        raise typer.Exit(1)

    with console.status("[cyan]AI 思考中..."):
        answer = engine.ask_knowledge_base(question)

    console.print(f"\n[bold green]Q:[/bold green] {question}")
    console.print(f"[bold blue]A:[/bold blue] {answer}\n")


@learn_app.command("总结")
def learn_summary(
    note_id: str = typer.Argument(..., help="笔记ID"),
):
    """AI 总结笔记要点（需要 Ollama）"""
    from core.ai_engine import AIEngine
    engine = AIEngine()

    if not engine.ai_available:
        console.print("[red][错误] Ollama 服务未启动[/red]")
        console.print("请运行: ollama serve")
        raise typer.Exit(1)

    with console.status("[cyan]AI 分析中..."):
        summary = engine.summarize_note(note_id)

    console.print(f"\n{summary}\n")


@learn_app.command("状态")
def learn_status():
    """查看 AI/Ollama 服务状态"""
    from core.ollama_client import OllamaHelper
    from core.config import Config

    cfg = Config.summary()

    console.print("\n[bold]AI 服务状态[/bold]\n")

    # Ollama 状态
    status = OllamaHelper.get_status()
    table = Table()
    table.add_column("服务", style="bold")
    table.add_column("状态")
    table.add_column("配置")

    ollama_status = "[green]在线[/green]" if status["available"] else "[red]离线[/red]"
    table.add_row(
        "Ollama",
        ollama_status,
        f"{status['host']} / {cfg['ollama_model']}"
    )

    # 已安装模型
    if status["installed_models"]:
        table.add_row(
            "已安装模型",
            f"{status['model_count']} 个",
            ", ".join(status["installed_models"][:3])
        )

    console.print(table)

    if not status["available"]:
        console.print("\n[yellow]提示:[/yellow] Ollama 未运行，learn ask/summary 命令不可用")
        console.print("        learn suggest 将使用规则引擎降级运行")
    else:
        recommended = OllamaHelper.recommend_model()
        console.print(f"\n[dim]推荐模型: {recommended}[/dim]")

    console.print()


# --- sync 子命令 ---

@sync_app.command("飞书")
def sync_feishu(
    force: bool = typer.Option(False, "--force", "-f", help="强制同步所有笔记（忽略增量）"),
):
    """同步知识库到飞书（增量同步，仅上传新增/修改的笔记）"""
    try:
        from feishu_upload import get_token, upload
    except ImportError:
        console.print("[red][ERR] feishu_upload 模块不可用[/red]")
        raise typer.Exit(1)

    notes = storage.list_notes()
    if not notes:
        console.print("[yellow]知识库为空，无需同步[/yellow]")
        return

    token = get_token()
    if not token:
        console.print("[red][ERR] 飞书 Token 获取失败，请检查 .env 凭证[/red]")
        raise typer.Exit(1)
    console.print("[green][OK][/green] 飞书 Token 获取成功")

    # 加载同步记录
    from core.config import Config
    sync_file = Config.KNOWLEDGE_DIR / "sync_record.json"
    import json
    sync_record = {}
    if sync_file.exists():
        sync_record = json.loads(sync_file.read_text(encoding="utf-8"))

    synced = 0
    skipped = 0
    failed_count = 0

    for note in notes:
        last_synced = sync_record.get(note.id, {}).get("synced_at", "")
        if not force and last_synced and last_synced >= note.updated_at:
            skipped += 1
            continue

        content = storage.get_note_content(note)
        if not content:
            skipped += 1
            continue

        ft, url = upload(token, content, note.title)
        if ft:
            sync_record[note.id] = {
                "synced_at": note.updated_at,
                "file_token": ft,
            }
            synced += 1
            console.print(f"  [green]✓[/green] {note.title}")
        else:
            failed_count += 1
            console.print(f"  [red]✗[/red] {note.title}")

    # 保存同步记录
    sync_file.write_text(json.dumps(sync_record, ensure_ascii=False, indent=2), encoding="utf-8")

    console.print(f"\n同步完成: [green]{synced} 上传[/green] / [dim]{skipped} 跳过[/dim] / [red]{failed_count} 失败[/red]")


@sync_app.command("导出")
def sync_export(
    output: str = typer.Option("./export", "--output", "-o", help="导出目录"),
):
    """导出知识库为本地备份"""
    import shutil
    from core.config import Config
    out_path = Path(output)
    out_path.mkdir(parents=True, exist_ok=True)

    notes = storage.list_notes()
    if not notes:
        console.print("[yellow]知识库为空[/yellow]")
        return

    # 复制所有笔记文件
    for note in notes:
        src = Config.KNOWLEDGE_DIR / note.file_path
        if src.exists():
            shutil.copy2(src, out_path / src.name)

    # 复制索引
    shutil.copy2(Config.INDEX_FILE, out_path / "index.json")

    console.print(f"[green][OK][/green] 已导出 {len(notes)} 条笔记到 {out_path.resolve()}")


# --- 系统命令 ---

@sys_app.command("成本")
def sys_cost():
    """查看 AI 调用成本与配额使用情况"""
    from core.economy_controller import EconomyController

    controller = EconomyController()
    stats = controller.get_stats_summary()

    console.print("\n[bold]AI 成本控制面板[/bold]\n")

    # 配额使用情况
    quota_table = Table(title="配额使用")
    quota_table.add_column("指标", style="bold")
    quota_table.add_column("已用", justify="right")
    quota_table.add_column("上限", justify="right")
    quota_table.add_column("剩余", justify="right", style="cyan")

    remaining = stats["剩余配额"]
    quota_table.add_row(
        "本小时调用",
        str(stats["调用统计"]["本小时调用"]),
        "50",
        str(remaining["hourly_calls"])
    )
    quota_table.add_row(
        "本日调用",
        str(stats["调用统计"]["本日调用"]),
        "-",
        "-"
    )
    quota_table.add_row(
        "本日 Token",
        stats["调用统计"]["本日Token"],
        "100,000",
        f"{remaining['daily_tokens']:,}"
    )

    console.print(quota_table)

    # 缓存统计
    cache_table = Table(title="缓存效率")
    cache_table.add_column("指标", style="bold")
    cache_table.add_column("数值", justify="right", style="green")

    cache_stats = stats["缓存统计"]
    cache_table.add_row("命中次数", str(cache_stats["命中次数"]))
    cache_table.add_row("未命中次数", str(cache_stats["未命中次数"]))
    cache_table.add_row("命中率", cache_stats["命中率"])

    console.print(f"\n")
    console.print(cache_table)

    # 成本估算
    cost = stats["成本估计"]
    console.print(f"\n[dim]今日成本: {cost['今日消耗']} (缓存节省: {cost['缓存节省']})[/dim]")

    # 状态提示
    hourly_pct = stats["调用统计"]["本小时调用"] / 50 * 100
    if hourly_pct >= 90:
        console.print(f"\n[red]警告: 本小时调用接近上限 ({hourly_pct:.0f}%)[/red]")
    elif hourly_pct >= 70:
        console.print(f"\n[yellow]注意: 本小时调用较高 ({hourly_pct:.0f}%)[/yellow]")
    else:
        console.print(f"\n[green]配额充足 ({hourly_pct:.0f}% 已用)[/green]")

    console.print()


if __name__ == "__main__":
    app()
