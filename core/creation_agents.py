# -*- coding: utf-8 -*-
"""
Creation Agents - 创作类Agent实现
script-short: 短视频剧本创作
script-long: 网文长篇创作
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import asdict

from core.models import CreationSession, Character, PlotPoint, DraftVersion
from core.script_guard import ScriptGuard, ValidationResult
from core.component_engine import ComponentEngine


class ScriptShortAgent:
    """
    短视频剧本创作Agent
    负责3-5分钟短视频剧本的完整创作流程
    """

    def __init__(self):
        self.track = "short"
        self.guard = ScriptGuard(track=self.track)
        self.components = ComponentEngine(track=self.track)
        self.template_path = Path("creation/short/templates/短视频剧本模板.md")

    def create_project(self, title: str, platform: str, genre: str, **kwargs) -> CreationSession:
        """
        创建新剧本项目

        Args:
            title: 剧本标题
            platform: 目标平台 (douyin/kuaishou/bilibili)
            genre: 类型/题材
            **kwargs: 其他参数

        Returns:
            CreationSession对象
        """
        session_id = f"short_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        session = CreationSession(
            id=session_id,
            track=self.track,
            title=title,
            platform=platform,
            genre=genre,
            target_audience=kwargs.get("target_audience", ""),
            outline={},
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        # 保存项目
        self._save_session(session)

        return session

    def generate_outline(self, session_id: str, concept: str) -> Dict[str, Any]:
        """
        生成剧本大纲

        Args:
            session_id: 项目ID
            concept: 核心创意

        Returns:
            大纲字典
        """
        session = self._load_session(session_id)
        if not session:
            return {"error": "项目不存在"}

        # 基于模板生成大纲结构
        outline = {
            "concept": concept,
            "hook_candidates": self._generate_hooks(concept),
            "emotion_curve": self._design_emotion_curve(),
            "conflict_points": self._design_conflicts(),
            "scenes": [],
            "punchline": {},
            "components_used": []
        }

        session.outline = outline
        session.updated_at = datetime.now().isoformat()
        self._save_session(session)

        return outline

    def _generate_hooks(self, concept: str) -> List[Dict]:
        """生成3个备选Hook"""
        hooks = [
            {
                "id": "A",
                "type": "悬念型",
                "content": f"你知道吗？{concept[:10]}...",
                "predicted_retention": "75%"
            },
            {
                "id": "B",
                "type": "冲突型",
                "content": f"当我{concept[:10]}时，所有人都震惊了...",
                "predicted_retention": "70%"
            },
            {
                "id": "C",
                "type": "共鸣型",
                "content": f"有没有人和我一样，经历过{concept[:10]}？",
                "predicted_retention": "65%"
            }
        ]
        return hooks

    def _design_emotion_curve(self) -> List[Dict]:
        """设计15节点情绪曲线"""
        # 标准情绪曲线模板
        base_curve = [5, 7, 6, 8, 7, 6, 8, 9, 7, 6, 8, 9, 8, 9, 10]
        return [
            {"node": i, "value": v, "timestamp": f"{i*15}-{(i+1)*15}s"}
            for i, v in enumerate(base_curve)
        ]

    def _design_conflicts(self) -> List[Dict]:
        """设计冲突点（每15秒一个）"""
        return [
            {"time": "15s", "type": "误解", "intensity": "中"},
            {"time": "30s", "type": "对抗", "intensity": "高"},
            {"time": "45s", "type": "转折", "intensity": "高"},
            {"time": "60s", "type": "高潮", "intensity": "极高"},
        ]

    def apply_component(self, session_id: str, component_id: str) -> Dict:
        """
        应用工业化组件

        Args:
            session_id: 项目ID
            component_id: 组件ID

        Returns:
            应用结果
        """
        session = self._load_session(session_id)
        if not session:
            return {"error": "项目不存在"}

        try:
            component = self.components.load_component(component_id)

            # 记录使用的组件
            if "components_used" not in session.outline:
                session.outline["components_used"] = []

            session.outline["components_used"].append({
                "id": component_id,
                "name": component["name"],
                "applied_at": datetime.now().isoformat()
            })

            self._save_session(session)

            return {
                "success": True,
                "component": component,
                "message": f"已应用组件: {component['name']}"
            }

        except Exception as e:
            return {"error": str(e)}

    def generate_draft(self, session_id: str, hook_choice: str = "A") -> Dict:
        """
        生成完整剧本草稿

        Args:
            session_id: 项目ID
            hook_choice: 选择的Hook (A/B/C)

        Returns:
            草稿内容
        """
        session = self._load_session(session_id)
        if not session:
            return {"error": "项目不存在"}

        # 获取选中的Hook
        hooks = session.outline.get("hook_candidates", [])
        selected_hook = next((h for h in hooks if h["id"] == hook_choice), hooks[0] if hooks else None)

        # 构建剧本内容
        draft_content = self._build_script_content(session, selected_hook)

        # 风控校验
        validation = self.guard.validate({
            "text": draft_content,
            "title": session.title,
            "platform": session.platform
        }, checkpoint="draft")

        if not validation.can_proceed:
            return {
                "error": "风控校验未通过",
                "violations": [v.to_dict() for v in validation.violations],
                "requires_action": "请根据违规提示修改内容"
            }

        # 保存草稿
        draft = DraftVersion(
            version=len(session.drafts) + 1,
            content=draft_content,
            created_at=datetime.now().isoformat(),
            change_summary=f"选择Hook {hook_choice}，生成初版剧本"
        )
        session.drafts.append(draft)
        session.status = "draft"
        self._save_session(session)

        return {
            "success": True,
            "draft_version": draft.version,
            "content_preview": draft_content[:500] + "...",
            "validation": validation.to_dict()
        }

    def _build_script_content(self, session: CreationSession, hook: Dict) -> str:
        """构建完整剧本内容"""
        content = f"""# {session.title}

## 基础信息
- 平台: {session.platform}
- 类型: {session.genre}
- 预计时长: 3-5分钟

## 黄金3秒Hook
**选择**: Hook {hook['id']} ({hook['type']})
**内容**: {hook['content']}
**预计完播率**: {hook['predicted_retention']}

## 15节点情绪坐标
"""
        # 添加情绪曲线
        for point in session.outline.get("emotion_curve", []):
            content += f"- 节点{point['node']} ({point['timestamp']}): 情绪值{point['value']}/10\n"

        content += "\n## 冲突设计\n"
        for conflict in session.outline.get("conflict_points", []):
            content += f"- {conflict['time']}: {conflict['type']}冲突，强度{conflict['intensity']}\n"

        content += """
## 场景详情
[此处展开详细场景设计]

## 结尾Punchline
[设计反转/悬念/共鸣结尾]
"""

        return content

    def _save_session(self, session: CreationSession):
        """保存会话到文件"""
        save_dir = Path(f"creation/short/projects/{session.id}")
        save_dir.mkdir(parents=True, exist_ok=True)

        with open(save_dir / "session.json", 'w', encoding='utf-8') as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)

    def _load_session(self, session_id: str) -> Optional[CreationSession]:
        """从文件加载会话"""
        session_path = Path(f"creation/short/projects/{session_id}/session.json")
        if not session_path.exists():
            return None

        with open(session_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 简化加载，实际应完整解析
            return CreationSession(
                id=data["id"],
                track=data["track"],
                title=data["title"],
                status=data["status"],
                outline=data.get("outline", {}),
                platform=data.get("platform", "douyin"),
                genre=data.get("genre", ""),
                created_at=data.get("created_at", ""),
                updated_at=data.get("updated_at", "")
            )


class ScriptLongAgent:
    """
    网文长篇创作Agent
    负责100万字+网文的创作管理
    """

    def __init__(self):
        self.track = "long"
        self.guard = ScriptGuard(track=self.track)
        self.components = ComponentEngine(track=self.track)

    def create_project(self, title: str, platform: str, genre: str, total_words: int = 100) -> CreationSession:
        """
        创建网文项目

        Args:
            title: 作品标题
            platform: 平台 (起点/晋江/番茄等)
            genre: 类型
            total_words: 预计总字数(万字)
        """
        session_id = f"long_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        session = CreationSession(
            id=session_id,
            track=self.track,
            title=title,
            platform=platform,
            genre=genre,
            word_count_target=total_words * 10000,
            outline={
                "volumes": [],  # 分卷规划
                "world_setting": {},
                "main_plot": {},
                "side_plots": []
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        self._save_session(session)
        return session

    def design_world(self, session_id: str, world_concept: str) -> Dict:
        """
        设计世界观

        Args:
            session_id: 项目ID
            world_concept: 世界观概念
        """
        session = self._load_session(session_id)
        if not session:
            return {"error": "项目不存在"}

        world_setting = {
            "concept": world_concept,
            "map": {},
            "factions": [],
            "rules": {
                "power_system": "",
                "social_structure": "",
                "special_mechanics": []
            },
            "history": []
        }

        session.outline["world_setting"] = world_setting
        self._save_session(session)

        return {"success": True, "world_setting": world_setting}

    def create_character(self, session_id: str, name: str, profile: str, **kwargs) -> Dict:
        """
        创建角色

        Args:
            session_id: 项目ID
            name: 角色名
            profile: 人物小传
            **kwargs: 其他属性
        """
        session = self._load_session(session_id)
        if not session:
            return {"error": "项目不存在"}

        char_id = f"char_{len(session.characters) + 1}"
        character = Character(
            id=char_id,
            name=name,
            profile=profile,
            traits=kwargs.get("traits", []),
            arc=kwargs.get("arc", ""),
            relationships=kwargs.get("relationships", {})
        )

        session.characters.append(character)
        self._save_session(session)

        return {
            "success": True,
            "character_id": char_id,
            "character": character.to_dict()
        }

    def plan_volumes(self, session_id: str, volumes: List[Dict]) -> Dict:
        """
        规划分卷结构

        Args:
            session_id: 项目ID
            volumes: 分卷列表
                [{"name": "第一卷:觉醒", "words": 150000, "key_event": "..."}, ...]
        """
        session = self._load_session(session_id)
        if not session:
            return {"error": "项目不存在"}

        session.outline["volumes"] = volumes
        self._save_session(session)

        return {
            "success": True,
            "volumes": volumes,
            "total_words": sum(v.get("words", 0) for v in volumes)
        }

    def _save_session(self, session: CreationSession):
        """保存会话"""
        save_dir = Path(f"creation/long/projects/{session.id}")
        save_dir.mkdir(parents=True, exist_ok=True)

        with open(save_dir / "session.json", 'w', encoding='utf-8') as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)

    def _load_session(self, session_id: str) -> Optional[CreationSession]:
        """加载会话"""
        session_path = Path(f"creation/long/projects/{session_id}/session.json")
        if not session_path.exists():
            return None

        with open(session_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return CreationSession(
                id=data["id"],
                track=data["track"],
                title=data["title"],
                status=data["status"],
                outline=data.get("outline", {}),
                platform=data.get("platform", "起点"),
                genre=data.get("genre", ""),
                word_count_target=data.get("word_count_target", 0),
                created_at=data.get("created_at", ""),
                updated_at=data.get("updated_at", "")
            )


# 便捷入口函数
def create_short_script(title: str, platform: str, genre: str) -> str:
    """创建短视频剧本项目，返回项目ID"""
    agent = ScriptShortAgent()
    session = agent.create_project(title, platform, genre)
    return session.id


def create_long_novel(title: str, platform: str, genre: str, total_words: int = 100) -> str:
    """创建网文项目，返回项目ID"""
    agent = ScriptLongAgent()
    session = agent.create_project(title, platform, genre, total_words)
    return session.id


if __name__ == "__main__":
    # 测试
    print("ScriptShortAgent 和 ScriptLongAgent 已加载")
    print("使用 create_short_script() 或 create_long_novel() 创建项目")
