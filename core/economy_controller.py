# -*- coding: utf-8 -*-
"""经济控制层 - 管理 AI 调用成本与资源使用"""

import json
import hashlib
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List
from datetime import datetime, timedelta

from core.config import Config


@dataclass
class UsageStats:
    """使用统计"""
    hourly_calls: int = 0
    daily_tokens: int = 0
    daily_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    last_reset_hour: str = ""
    last_reset_date: str = ""

    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0


class EconomyController:
    """经济控制器 - 限制 AI 调用成本"""

    def __init__(self):
        self.usage_file = Config.KNOWLEDGE_DIR / "usage_stats.json"
        self.cache_file = Config.KNOWLEDGE_DIR / "ai_cache.json"
        self.stats = self._load_stats()
        self._check_and_reset()

    def _load_stats(self) -> UsageStats:
        """加载使用统计"""
        if self.usage_file.exists():
            try:
                data = json.loads(self.usage_file.read_text(encoding="utf-8"))
                return UsageStats(**data)
            except Exception:
                pass
        return UsageStats()

    def _save_stats(self):
        """保存使用统计"""
        self.usage_file.write_text(
            json.dumps(asdict(self.stats), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def _check_and_reset(self):
        """检查并重置周期统计"""
        now = datetime.now()
        current_hour = now.strftime("%Y-%m-%d-%H")
        current_date = now.strftime("%Y-%m-%d")

        if self.stats.last_reset_hour != current_hour:
            self.stats.hourly_calls = 0
            self.stats.last_reset_hour = current_hour

        if self.stats.last_reset_date != current_date:
            self.stats.daily_tokens = 0
            self.stats.daily_calls = 0
            self.stats.cache_hits = 0
            self.stats.cache_misses = 0
            self.stats.last_reset_date = current_date

        self._save_stats()

    def check_quota(self, estimated_tokens: int = 1000) -> Dict:
        """检查配额状态

        Returns:
            {
                "allowed": bool,
                "reason": str,
                "quota_remaining": dict
            }
        """
        self._check_and_reset()

        # 检查每小时调用次数
        if self.stats.hourly_calls >= 50:  # max_calls_per_hour
            return {
                "allowed": False,
                "reason": "每小时调用次数已达上限 (50)",
                "quota_remaining": self._get_quota_remaining()
            }

        # 检查每日 Token 上限
        if self.stats.daily_tokens + estimated_tokens >= 100000:  # max_tokens_per_day
            return {
                "allowed": False,
                "reason": "每日 Token 上限即将耗尽 (100000)",
                "quota_remaining": self._get_quota_remaining()
            }

        return {
            "allowed": True,
            "reason": "",
            "quota_remaining": self._get_quota_remaining()
        }

    def _get_quota_remaining(self) -> Dict:
        """获取剩余配额"""
        return {
            "hourly_calls": max(0, 50 - self.stats.hourly_calls),
            "daily_tokens": max(0, 100000 - self.stats.daily_tokens),
            "daily_calls": self.stats.daily_calls
        }

    def record_call(self, tokens_used: int = 0):
        """记录一次调用"""
        self._check_and_reset()
        self.stats.hourly_calls += 1
        self.stats.daily_calls += 1
        self.stats.daily_tokens += tokens_used
        self._save_stats()

    def record_cache_hit(self):
        """记录缓存命中"""
        self.stats.cache_hits += 1
        self._save_stats()

    def record_cache_miss(self):
        """记录缓存未命中"""
        self.stats.cache_misses += 1
        self._save_stats()

    def get_cache_key(self, prompt: str, context: str = "") -> str:
        """生成缓存键"""
        content = f"{context}:{prompt}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def get_cached_result(self, cache_key: str) -> Optional[str]:
        """获取缓存结果"""
        if not self.cache_file.exists():
            return None

        try:
            cache = json.loads(self.cache_file.read_text(encoding="utf-8"))
            entry = cache.get(cache_key)
            if not entry:
                return None

            # 检查缓存是否过期（默认24小时）
            cached_time = datetime.fromisoformat(entry["timestamp"])
            if datetime.now() - cached_time > timedelta(hours=Config.AI_CACHE_HOURS):
                return None

            self.record_cache_hit()
            return entry["result"]
        except Exception:
            return None

    def save_cache(self, cache_key: str, result: str):
        """保存缓存结果"""
        cache = {}
        if self.cache_file.exists():
            try:
                cache = json.loads(self.cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        # 限制缓存大小（最多保留100条）
        if len(cache) >= 100:
            # 删除最旧的条目
            oldest_key = min(cache.keys(), key=lambda k: cache[k]["timestamp"])
            del cache[oldest_key]

        cache[cache_key] = {
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

        self.cache_file.write_text(
            json.dumps(cache, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        self.record_cache_miss()

    def estimate_tokens(self, text: str) -> int:
        """估算文本的 Token 数量（粗略估计：1 token ≈ 4 字符）"""
        return len(text) // 4 + 1

    def get_stats_summary(self) -> Dict:
        """获取统计摘要"""
        self._check_and_reset()
        return {
            "当前周期": {
                "小时": self.stats.last_reset_hour,
                "日期": self.stats.last_reset_date
            },
            "调用统计": {
                "本小时调用": self.stats.hourly_calls,
                "本日调用": self.stats.daily_calls,
                "本日Token": f"{self.stats.daily_tokens:,}"
            },
            "缓存统计": {
                "命中次数": self.stats.cache_hits,
                "未命中次数": self.stats.cache_misses,
                "命中率": f"{self.stats.cache_hit_rate:.1%}"
            },
            "剩余配额": self._get_quota_remaining(),
            "成本估计": {
                "今日消耗": f"~${self.stats.daily_tokens * 0.0000015:.4f}",  # 按 $1.5/M tokens 估算
                "缓存节省": f"~${self.stats.cache_hits * 1000 * 0.0000015:.4f}"
            }
        }


class SmartCache:
    """智能缓存 - 支持相似度匹配"""

    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold
        self.controller = EconomyController()

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的相似度（简化版 Jaccard 相似度）"""
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())

        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0

    def find_similar(self, prompt: str, context: str = "") -> Optional[str]:
        """查找相似的历史查询结果"""
        if not self.controller.cache_file.exists():
            return None

        try:
            cache = json.loads(self.controller.cache_file.read_text(encoding="utf-8"))
            full_prompt = f"{context}:{prompt}"

            for key, entry in cache.items():
                cached_prompt = entry.get("prompt", "")
                similarity = self._calculate_similarity(full_prompt, cached_prompt)

                if similarity >= self.threshold:
                    self.controller.record_cache_hit()
                    return entry["result"]

            return None
        except Exception:
            return None

    def save_with_prompt(self, prompt: str, context: str, result: str):
        """保存结果，同时记录原始 prompt 用于相似度匹配"""
        cache_key = self.controller.get_cache_key(prompt, context)

        cache = {}
        if self.controller.cache_file.exists():
            try:
                cache = json.loads(self.controller.cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        # 限制缓存大小
        if len(cache) >= 100:
            oldest_key = min(cache.keys(), key=lambda k: cache[k]["timestamp"])
            del cache[oldest_key]

        cache[cache_key] = {
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "prompt": f"{context}:{prompt}"
        }

        self.controller.cache_file.write_text(
            json.dumps(cache, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        self.controller.record_cache_miss()
