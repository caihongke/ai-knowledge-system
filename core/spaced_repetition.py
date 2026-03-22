"""间隔复习引擎 - 基于艾宾浩斯遗忘曲线"""

import json
from datetime import datetime, timedelta
from typing import List, Optional

from core.config import Config


class SpacedRepetition:
    """管理笔记的间隔复习计划"""

    def __init__(self):
        self.schedule = self._load()

    def _load(self) -> dict:
        if Config.REVIEW_FILE.exists():
            return json.loads(Config.REVIEW_FILE.read_text(encoding="utf-8"))
        return {}

    def _save(self):
        Config.REVIEW_FILE.write_text(
            json.dumps(self.schedule, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def register(self, note_id: str):
        """注册新笔记到复习计划"""
        if note_id in self.schedule:
            return
        now = datetime.now().isoformat(timespec="seconds")
        self.schedule[note_id] = {
            "review_count": 0,
            "next_review": (datetime.now() + timedelta(days=Config.REVIEW_INTERVALS[0])).strftime("%Y-%m-%d"),
            "created_at": now,
            "last_reviewed": None,
        }
        self._save()

    def unregister(self, note_id: str):
        """从复习计划中移除笔记"""
        if note_id in self.schedule:
            del self.schedule[note_id]
            self._save()

    def get_today_reviews(self) -> List[str]:
        """获取今日待复习的笔记 ID 列表"""
        today = datetime.now().strftime("%Y-%m-%d")
        return [
            nid for nid, info in self.schedule.items()
            if info["next_review"] <= today
        ]

    def mark_done(self, note_id: str) -> Optional[str]:
        """标记复习完成，返回下次复习日期。若已掌握返回 None"""
        if note_id not in self.schedule:
            return None

        info = self.schedule[note_id]
        info["review_count"] += 1
        info["last_reviewed"] = datetime.now().isoformat(timespec="seconds")

        intervals = Config.REVIEW_INTERVALS
        idx = info["review_count"]
        if idx < len(intervals):
            next_date = (datetime.now() + timedelta(days=intervals[idx])).strftime("%Y-%m-%d")
            info["next_review"] = next_date
        else:
            info["next_review"] = "mastered"

        self._save()
        return info["next_review"]

    def get_stats(self) -> dict:
        """复习统计"""
        today = datetime.now().strftime("%Y-%m-%d")
        total = len(self.schedule)
        due_today = sum(1 for info in self.schedule.values() if info["next_review"] <= today and info["next_review"] != "mastered")
        mastered = sum(1 for info in self.schedule.values() if info["next_review"] == "mastered")
        in_progress = total - mastered
        return {
            "total": total,
            "due_today": due_today,
            "mastered": mastered,
            "in_progress": in_progress,
        }

    def get_note_info(self, note_id: str) -> Optional[dict]:
        """获取笔记的复习信息"""
        return self.schedule.get(note_id)
