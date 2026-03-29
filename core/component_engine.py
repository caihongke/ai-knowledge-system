"""ComponentEngine - 工业化组件引擎
支持人设、桥段、爽点等组件的按需加载和组合
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Component:
    """组件定义"""

    id: str
    name: str
    category: str  # character / scene / payoff
    tags: list[str] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    usage_examples: list[str] = field(default_factory=list)
    compatible_with: list[str] = field(default_factory=list)
    conflicts_with: list[str] = field(default_factory=list)


class ComponentEngine:
    """工业化组件引擎

    核心原则：
    1. 按需加载，避免全量堆叠
    2. 同类型组件最多3个
    3. 冲突标签不能共存
    4. 双赛道组件隔离
    """

    # 组件类型限制
    TYPE_LIMITS = {
        "character": 3,  # 人设组件最多3个
        "scene": 3,      # 桥段组件最多3个
        "payoff": 2,     # 爽点组件最多2个
    }

    # 冲突标签映射
    CONFLICTING_TAGS = {
        "悲剧": ["喜剧", "爽文"],
        "暗黑": ["治愈", "轻松"],
        "慢热": ["快节奏", "爽点密集"],
    }

    def __init__(self, track: str = "short"):
        """初始化组件引擎

        Args:
            track: "short" | "long"

        """
        self.track = track
        self.active_components: dict[str, Component] = {}
        self.component_library: dict[str, list[Component]] = {
            "character": [],
            "scene": [],
            "payoff": [],
        }
        self._load_library()

    def _load_library(self):
        """加载组件库"""
        base_path = Path("creation/components")

        # 加载人设组件
        char_path = base_path / "characters"
        if char_path.exists():
            for f in char_path.glob("*.json"):
                with open(f, encoding="utf-8") as fp:
                    data = json.load(fp)
                    self.component_library["character"].append(
                        Component(category="character", **data),
                    )

        # 加载桥段组件
        scene_path = base_path / "scenes"
        if scene_path.exists():
            for f in scene_path.glob("*.json"):
                with open(f, encoding="utf-8") as fp:
                    data = json.load(fp)
                    self.component_library["scene"].append(
                        Component(category="scene", **data),
                    )

        # 加载爽点组件
        payoff_path = base_path / "payoffs"
        if payoff_path.exists():
            for f in payoff_path.glob("*.json"):
                with open(f, encoding="utf-8") as fp:
                    data = json.load(fp)
                    self.component_library["payoff"].append(
                        Component(category="payoff", **data),
                    )

    def load_component(self, component_id: str) -> dict:
        """按需加载组件

        Args:
            component_id: 组件ID

        Returns:
            组件配置字典

        Raises:
            ComponentNotFoundError: 组件不存在
            ComponentConflictError: 组件冲突
            TypeLimitExceededError: 超出类型限制

        """
        # 查找组件
        component = self._find_component(component_id)
        if not component:
            raise ComponentNotFoundError(f"组件 {component_id} 不存在")

        # 检查类型限制
        category = component.category
        current_count = len([
            c for c in self.active_components.values()
            if c.category == category
        ])
        if current_count >= self.TYPE_LIMITS.get(category, 3):
            raise TypeLimitExceededError(
                f"{category}类型组件已达上限({self.TYPE_LIMITS[category]}个)，"
                f"请先卸载现有组件",
            )

        # 检查冲突
        conflicts = self._check_conflicts(component)
        if conflicts:
            raise ComponentConflictError(
                f"组件 {component_id} 与以下组件冲突: {', '.join(conflicts)}",
            )

        # 激活组件
        self.active_components[component_id] = component

        return {
            "id": component.id,
            "name": component.name,
            "category": component.category,
            "params": component.params,
            "description": component.description,
            "usage_examples": component.usage_examples,
        }

    def unload_component(self, component_id: str):
        """卸载组件"""
        if component_id in self.active_components:
            del self.active_components[component_id]
            return True
        return False

    def clear_all(self):
        """清空所有激活组件"""
        self.active_components.clear()

    def get_active_components(self) -> list[dict]:
        """获取当前激活的组件列表"""
        return [
            {
                "id": c.id,
                "name": c.name,
                "category": c.category,
                "tags": c.tags,
            }
            for c in self.active_components.values()
        ]

    def suggest_components(self, genre: str, target_effect: str) -> list[dict]:
        """基于类型和目标效果推荐组件

        Args:
            genre: 类型/题材
            target_effect: 目标效果 (如 "爽感", "泪点", "悬念")

        Returns:
            推荐组件列表

        """
        suggestions = []

        for category, components in self.component_library.items():
            for comp in components:
                # 匹配标签
                score = 0
                if genre in comp.tags:
                    score += 2
                if target_effect in comp.tags:
                    score += 3

                # 检查兼容性
                if self._check_compatibility(comp):
                    score += 1

                if score > 0:
                    suggestions.append({
                        "component": comp,
                        "score": score,
                        "reason": f"匹配标签: {', '.join(set(comp.tags) & {genre, target_effect})}",
                    })

        # 按分数排序
        suggestions.sort(key=lambda x: -x["score"])

        return [
            {
                "id": s["component"].id,
                "name": s["component"].name,
                "category": s["component"].category,
                "score": s["score"],
                "reason": s["reason"],
            }
            for s in suggestions[:5]  # 最多返回5个
        ]

    def _find_component(self, component_id: str) -> Component | None:
        """查找组件"""
        for components in self.component_library.values():
            for comp in components:
                if comp.id == component_id:
                    return comp
        return None

    def _check_conflicts(self, new_component: Component) -> list[str]:
        """检查组件冲突"""
        conflicts = []

        # 检查显式冲突
        for active_id, active_comp in self.active_components.items():
            if new_component.id in active_comp.conflicts_with:
                conflicts.append(active_id)
            if active_comp.id in new_component.conflicts_with:
                conflicts.append(active_id)

        # 检查标签冲突
        for tag in new_component.tags:
            if tag in self.CONFLICTING_TAGS:
                conflicting_tags = self.CONFLICTING_TAGS[tag]
                for active_id, active_comp in self.active_components.items():
                    if any(t in conflicting_tags for t in active_comp.tags):
                        conflicts.append(active_id)

        return list(set(conflicts))

    def _check_compatibility(self, component: Component) -> bool:
        """检查组件与当前激活组件的兼容性"""
        # 检查显式兼容性
        if component.compatible_with:
            for active_id in self.active_components.keys():
                if active_id not in component.compatible_with:
                    return False

        # 检查是否有冲突
        conflicts = self._check_conflicts(component)
        return len(conflicts) == 0

    def get_usage_guide(self, component_id: str) -> str:
        """获取组件使用指南"""
        component = self._find_component(component_id)
        if not component:
            return f"组件 {component_id} 不存在"

        guide = f"""
## {component.name} 使用指南

**组件ID**: {component.id}
**类型**: {component.category}
**标签**: {', '.join(component.tags)}

**描述**:
{component.description}

**参数配置**:
```json
{json.dumps(component.params, ensure_ascii=False, indent=2)}
```

**使用示例**:
"""
        for i, example in enumerate(component.usage_examples, 1):
            guide += f"\n{i}. {example}\n"

        return guide


class ComponentNotFoundError(Exception):
    """组件不存在错误"""



class ComponentConflictError(Exception):
    """组件冲突错误"""



class TypeLimitExceededError(Exception):
    """类型限制超出错误"""



# 便捷函数
def create_character_component(
    name: str,
    archetype: str,
    traits: list[str],
    arc_type: str,
) -> Component:
    """创建人设组件"""
    return Component(
        id=f"char-{name}",
        name=name,
        category="character",
        tags=[archetype] + traits,
        params={
            "archetype": archetype,
            "traits": traits,
            "arc_type": arc_type,
            "complexity": "medium",
        },
        description=f"{archetype}类型人设，具有{', '.join(traits)}特征",
    )


def create_scene_component(
    name: str,
    scene_type: str,
    tension_curve: list[float],
    emotion_trigger: str,
) -> Component:
    """创建桥段组件"""
    return Component(
        id=f"scene-{name}",
        name=name,
        category="scene",
        tags=[scene_type, emotion_trigger],
        params={
            "type": scene_type,
            "tension_curve": tension_curve,
            "emotion_trigger": emotion_trigger,
            "duration_estimate": "3-5分钟",
        },
        description=f"{scene_type}桥段，情绪触发点: {emotion_trigger}",
    )


def create_payoff_component(
    name: str,
    payoff_type: str,
    setup_chapters: int,
    intensity: str,
) -> Component:
    """创建爽点组件"""
    return Component(
        id=f"payoff-{name}",
        name=name,
        category="payoff",
        tags=[payoff_type, intensity],
        params={
            "type": payoff_type,
            "setup_chapters": setup_chapters,
            "intensity": intensity,
            "reader_satisfaction": "high" if intensity == "高" else "medium",
        },
        description=f"{payoff_type}爽点，铺垫{setup_chapters}章，强度{intensity}",
    )


if __name__ == "__main__":
    # 测试示例
    engine = ComponentEngine(track="short")

    # 创建示例组件
    comp1 = create_character_component(
        "美强惨女主",
        "大女主",
        ["美貌", "实力强", "身世惨"],
        "逆袭成长",
    )

    print(f"组件创建: {comp1.name}")
    print(f"参数: {json.dumps(comp1.params, ensure_ascii=False, indent=2)}")
