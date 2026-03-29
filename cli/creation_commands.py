# -*- coding: utf-8 -*-
"""
Creation Commands - CLI for creation system
"""

import typer
from rich.console import Console
from rich.panel import Panel

from core.creation_agents import ScriptShortAgent, ScriptLongAgent
from core.component_engine import ComponentEngine

console = Console()

# Create typers with English names (Chinese names cause issues in some Python versions)
script_short = typer.Typer(help="Short video script creation (3-5 min)")
script_long = typer.Typer(help="Novel creation (100w+ words)")
component = typer.Typer(help="Component library management")

@script_short.command("create")
def short_create(
    title: str,
    platform: str = "douyin",
    genre: str = "drama"
):
    """Create new short video project"""
    agent = ScriptShortAgent()
    session = agent.create_project(title, platform, genre)
    console.print(f"Created short script: {session.id}")

@script_long.command("create")
def long_create(
    title: str,
    platform: str = "qidian",
    genre: str = "fantasy",
    words: int = 100
):
    """Create new novel project"""
    agent = ScriptLongAgent()
    session = agent.create_project(title, platform, genre, words)
    console.print(f"Created novel: {session.id}")

@component.command("list")
def comp_list():
    """List available components"""
    engine = ComponentEngine()
    for cat, comps in engine.component_library.items():
        console.print(f"{cat}: {len(comps)} components")

def register_creation_commands(app: typer.Typer):
    """Register creation commands with the main app"""
    app.add_typer(script_short, name="script-short", help="Short video scripts")
    app.add_typer(script_long, name="script-long", help="Novels")
    app.add_typer(component, name="component", help="Components")
