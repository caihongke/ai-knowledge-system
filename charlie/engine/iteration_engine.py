"""迭代引擎 - 人机协同进化"""

from dataclasses import dataclass, field
from typing import Any, Optional
from .review_engine import ReviewEngine, ReviewReport


@dataclass
class IterationResult:
    """迭代结果"""
    success: bool
    rounds: int
    final_content: str = ""
    history: list[dict] = field(default_factory=list)


class IterationEngine:
    """迭代引擎 - 人机协同进化

    工作流程：
    1. 审查当前版本
    2. 生成修改建议
    3. 自动/人工修复
    4. 循环直到通过或达到最大轮次
    """

    def __init__(self, scenario: str = "novel_long"):
        self.scenario = scenario
        self.review_engine = ReviewEngine(scenario)

    def iterate(
        self,
        content: str,
        story_data: dict,
        max_rounds: int = 5,
        auto: bool = False,
    ) -> IterationResult:
        """执行迭代改进

        Args:
            content: 作品内容
            story_data: 故事数据
            max_rounds: 最大迭代轮次
            auto: 是否自动修复

        Returns:
            IterationResult 迭代结果
        """
        results = []
        current_content = content

        for round_num in range(max_rounds):
            # 1. 审查当前版本
            report = self.review_engine.review(content=current_content, story_data=story_data)

            if report.passed and report.level in ["SAFE", "NORMAL"]:
                # 通过审查，迭代结束
                return IterationResult(
                    success=True,
                    rounds=round_num + 1,
                    final_content=current_content,
                    history=results,
                )

            # 2. 记录当前状态
            results.append({
                "round": round_num + 1,
                "level": report.level,
                "errors": report.errors,
                "warnings": report.warnings,
                "suggestions": report.suggestions,
            })

            # 3. 生成修复
            if auto:
                current_content = self._auto_fix(current_content, report, story_data)
            else:
                # 人工模式：返回修改建议，不直接修改
                break

        # 未完全通过，但达到最大轮次
        return IterationResult(
            success=False,
            rounds=len(results),
            final_content=current_content,
            history=results,
        )

    def _auto_fix(self, content: str, report: ReviewReport, story_data: dict) -> str:
        """自动修复 - AI辅助修改

        这是一个占位实现，实际可接入AI模型进行自动修复
        """
        fixed = content

        # 根据错误类型进行简单修复
        for error in report.errors:
            if "缺少爽点" in error:
                # 在章节中插入爽点
                fixed += "\n\n[建议插入：打脸/逆袭/系统奖励等爽点场景]"

            elif "缺少钩子" in error:
                # 添加结尾钩子
                fixed += "\n\n[建议添加：悬念结尾]"

            elif "冲突" in error and "不足" in error:
                fixed += "\n\n[建议增加：冲突场景]"

        # 添加修改标记
        fix_log = f"""

---

## 迭代{round(len(story_data.get('iterations', [])) + 1)} 自动修复

修复的问题：
{chr(10).join(f"- {e}" for e in report.errors[:5])}

建议：
{chr(10).join(f"- {s}" for s in report.suggestions[:3])}

"""
        return fixed + fix_log

    def batch_review(
        self,
        chapters: list[dict],
        story_data: dict,
    ) -> dict:
        """批量审查章节

        Args:
            chapters: 章节列表
            story_data: 故事数据

        Returns:
            审查汇总结果
        """
        results = []
        passed_count = 0

        for ch in chapters:
            ch_num = ch.get("chapter", 0)
            ch_content = ch.get("content", "")

            report = self.review_engine.review(
                content=ch_content,
                story_data={**story_data, "current_chapter": ch_num},
            )

            results.append({
                "chapter": ch_num,
                "passed": report.passed,
                "level": report.level,
                "errors": len(report.errors),
                "warnings": len(report.warnings),
            })

            if report.passed:
                passed_count += 1

        return {
            "total_chapters": len(chapters),
            "passed": passed_count,
            "failed": len(chapters) - passed_count,
            "pass_rate": passed_count / len(chapters) * 100 if chapters else 0,
            "chapter_results": results,
        }


def quick_iterate(
    story_data: dict,
    max_rounds: int = 3,
    auto: bool = False,
) -> dict:
    """便捷迭代入口"""
    engine = IterationEngine()
    content = story_data.get("full_content", "")

    result = engine.iterate(
        content=content,
        story_data=story_data,
        max_rounds=max_rounds,
        auto=auto,
    )

    return {
        "success": result.success,
        "rounds": result.rounds,
        "history": result.history,
    }