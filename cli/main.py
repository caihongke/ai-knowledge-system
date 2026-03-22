"""AI自学知识管理系统 - CLI 入口"""

import os
import subprocess
import tempfile
from pathlib import Path

import sys

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

app.add_typer(kb_app, name="kb")
app.add_typer(review_app, name="review")
app.add_typer(learn_app, name="learn")
app.add_typer(sync_app, name="sync")


# --- kb 命令：真实实现 ---

@kb_app.command("add")
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


@kb_app.command("list")
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


@kb_app.command("show")
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


@kb_app.command("search")
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


@kb_app.command("edit")
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


@kb_app.command("delete")
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


@kb_app.command("tags")
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

@review_app.command("today")
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


@review_app.command("done")
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


@review_app.command("stats")
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

@learn_app.command("suggest")
def learn_suggest():
    """生成学习路径建议（基于知识库分析）"""
    from core.learning_engine import LearningEngine
    engine = LearningEngine()
    result = engine.analyze()

    if result["status"] == "empty":
        console.print("[yellow]知识库为空[/yellow]")
        console.print(result["summary"])
    else:
        console.print(f"\n[bold]{result['summary']}[/bold]\n")

        # 知识覆盖图
        if result["knowledge_map"]:
            km_table = Table(title="知识覆盖度")
            km_table.add_column("领域", style="green")
            km_table.add_column("笔记数", justify="right", style="cyan")
            km_table.add_column("状态")
            for tag, count in result["knowledge_map"].items():
                status = "[green]强项[/green]" if count >= 3 else "[yellow]薄弱[/yellow]" if count == 1 else "一般"
                km_table.add_row(tag, str(count), status)
            console.print(km_table)

        # 复习健康度
        rh = result["review_health"]
        if rh:
            console.print(f"\n复习状态: 学习中 {rh.get('in_progress', 0)} / 已掌握 {rh.get('mastered', 0)} / 今日待复习 {rh.get('due_today', 0)}")

    # 学习建议
    if result["suggestions"]:
        console.print()
        sg_table = Table(title="学习建议")
        sg_table.add_column("#", style="dim", justify="right")
        sg_table.add_column("推荐主题", style="bold")
        sg_table.add_column("理由")
        sg_table.add_column("优先级", justify="center")
        for i, s in enumerate(result["suggestions"], 1):
            p = s["priority"]
            p_style = "[red]高[/red]" if p == "高" else "[yellow]中[/yellow]" if p == "中" else "[dim]低[/dim]"
            sg_table.add_row(str(i), s["topic"], s["reason"], p_style)
        console.print(sg_table)


# --- sync 子命令 ---

@sync_app.command("feishu")
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


@sync_app.command("export")
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


if __name__ == "__main__":
    app()
