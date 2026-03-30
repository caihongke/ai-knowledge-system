"""创作引擎 - 创意区完全开放"""

from dataclasses import dataclass
from typing import Any


@dataclass
class CreationInputs:
    """创作输入"""
    title: str
    input_prompt: str
    scenario: str
    chapters: int
    genre: str
    ai_enhance: bool = False


@dataclass
class GenerationResult:
    """生成结果"""
    content: str
    metadata: dict
    warnings: list


class CreativeZone:
    """创意区 - 完全开放的创作空间"""

    def __init__(self, scenario: str):
        self.scenario = scenario

    def free_create(self, inputs: CreationInputs) -> str:
        """自由创作 - 不受任何规则限制"""
        if inputs.scenario == "novel_long":
            return self._create_novel(inputs)
        return f"# {inputs.title}\n\n[Creative content here]"

    def _create_novel(self, inputs: CreationInputs) -> str:
        content = f"# {inputs.title}\n"
        for i in range(1, inputs.chapters + 1):
            content += f"\n---\n## 第{i}章\n\n[创作第{i}章内容]\n"
        return content


class CreativeEngine:
    """创作引擎"""

    def __init__(self, scenario: str = "novel_long"):
        self.scenario = scenario
        self.creative_zone = CreativeZone(scenario)

    def generate(self, inputs: CreationInputs) -> GenerationResult:
        content = self.creative_zone.free_create(inputs)
        return GenerationResult(
            content=content,
            metadata={"scenario": self.scenario, "chapters": inputs.chapters},
            warnings=[],
        )


def quick_create(title: str, prompt: str, scenario: str = "novel_long", chapters: int = 3) -> str:
    """快速创作"""
    engine = CreativeEngine(scenario)
    inputs = CreationInputs(title=title, input_prompt=prompt, scenario=scenario,
                            chapters=chapters, genre="", ai_enhance=False)
    return engine.generate(inputs).content