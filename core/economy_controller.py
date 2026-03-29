"""经济控制层 - 管理 AI 调用成本与资源使用"""

import hashlib
import json
import math
import threading
from collections import OrderedDict
from dataclasses import asdict, dataclass
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


class LRUAccessTracker:
    """LRU 访问追踪器 - 维护访问顺序"""

    def __init__(self):
        self._order: OrderedDict[str, None] = OrderedDict()

    def touch(self, key: str):
        """标记 key 被访问，将其移到末尾"""
        if key in self._order:
            self._order.move_to_end(key)
        else:
            self._order[key] = None

    def get_lru_key(self) -> str | None:
        """获取最久未访问的 key"""
        return next(iter(self._order)) if self._order else None

    def remove(self, key: str):
        """移除 key"""
        self._order.pop(key, None)

    def __contains__(self, key: str) -> bool:
        return key in self._order

    def __len__(self) -> int:
        return len(self._order)


class FrequencyWeightCache:
    """高级缓存 - LRU + 访问频率加权 + TTL 自动过期

    淘汰策略评分公式:
    score = remaining_ttl_hours * (1 + log2(access_count + 1)) / (1 + hours_since_last_access)

    特性:
    - LRU: 最近最少使用优先淘汰
    - Frequency加权: 访问频率高的条目更持久
    - TTL: 支持不同 TTL，可动态延长
    - 相似匹配: 支持模糊匹配相似查询
    """

    def __init__(
        self,
        max_size: int = 100,
        default_ttl_hours: int = 24,
        freq_boost_threshold: int = 3,
        freq_boost_multiplier: float = 2.0,
    ):
        self.max_size = max_size
        self.default_ttl_hours = default_ttl_hours
        self.freq_boost_threshold = freq_boost_threshold  # 访问多少次开始 boost
        self.freq_boost_multiplier = freq_boost_multiplier  # boost 倍数

        self._cache: dict[str, dict] = {}
        self._access_tracker = LRUAccessTracker()

    def _calculate_eviction_score(self, entry: dict, now: datetime) -> float:
        """计算淘汰评分 (分数越低越容易被淘汰)
        """
        # 剩余 TTL
        created = datetime.fromisoformat(entry["created_at"])
        age_hours = (now - created).total_seconds() / 3600
        remaining_ttl = max(0, entry.get("ttl_hours", self.default_ttl_hours) - age_hours)

        # 访问次数 (使用对数平滑)
        access_count = entry.get("access_count", 0)
        freq_factor = 1 + math.log2(access_count + 1)
        if access_count >= self.freq_boost_threshold:
            freq_factor *= self.freq_boost_multiplier

        # 距离上次访问的小时数
        last_access = datetime.fromisoformat(entry["last_access"])
        hours_since_access = (now - last_access).total_seconds() / 3600

        # 综合评分
        if remaining_ttl <= 0:
            return float("-inf")  # 已过期，立即淘汰

        return remaining_ttl * freq_factor / (1 + hours_since_access)

    def _select_eviction_candidates(self, count: int = 1) -> list[str]:
        """选择要淘汰的条目"""
        if len(self._cache) <= self.max_size - count:
            return []

        now = datetime.now()
        scored = [
            (key, self._calculate_eviction_score(entry, now))
            for key, entry in self._cache.items()
        ]
        # 按分数升序排列，最低分先淘汰
        scored.sort(key=lambda x: x[1])

        return [key for key, _ in scored[:count]]

    def get(self, key: str) -> str | None:
        """获取缓存值，触发 LRU 更新
        """
        entry = self._cache.get(key)
        if not entry:
            return None

        # 检查 TTL 是否过期
        created = datetime.fromisoformat(entry["created_at"])
        age_hours = (datetime.now() - created).total_seconds() / 3600
        if age_hours > entry.get("ttl_hours", self.default_ttl_hours):
            # 已过期，删除
            del self._cache[key]
            self._access_tracker.remove(key)
            return None

        # 更新访问信息
        entry["last_access"] = datetime.now().isoformat()
        entry["access_count"] = entry.get("access_count", 0) + 1
        self._access_tracker.touch(key)

        return entry["result"]

    def set(self, key: str, value: str, ttl_hours: int | None = None):
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl_hours: 有效时长（小时），None 时使用默认值

        """
        now = datetime.now()
        ttl = ttl_hours or self.default_ttl_hours

        # 如果 key 已存在，保留原有访问次数
        existing = self._cache.get(key)
        if existing:
            access_count = existing.get("access_count", 0)
        else:
            access_count = 0

        # 检查是否需要淘汰
        evict_keys = self._select_eviction_candidates(1)
        for ek in evict_keys:
            del self._cache[ek]
            self._access_tracker.remove(ek)

        self._cache[key] = {
            "result": value,
            "created_at": now.isoformat(),
            "last_access": now.isoformat(),
            "access_count": access_count,
            "ttl_hours": ttl,
        }
        self._access_tracker.touch(key)

    def extend_ttl(self, key: str, additional_hours: int) -> bool:
        """延长 TTL（对热门内容）
        """
        entry = self._cache.get(key)
        if not entry:
            return False

        entry["ttl_hours"] = min(
            entry.get("ttl_hours", self.default_ttl_hours) + additional_hours,
            168,  # 最多 7 天
        )
        return True

    def invalidate(self, key: str) -> bool:
        """删除指定缓存"""
        if key in self._cache:
            del self._cache[key]
            self._access_tracker.remove(key)
            return True
        return False

    def clear_expired(self) -> int:
        """清理所有过期缓存，返回清理数量"""
        now = datetime.now()
        expired_keys = []

        for key, entry in self._cache.items():
            created = datetime.fromisoformat(entry["created_at"])
            age_hours = (now - created).total_seconds() / 3600
            if age_hours > entry.get("ttl_hours", self.default_ttl_hours):
                expired_keys.append(key)

        for key in expired_keys:
            del self._cache[key]
            self._access_tracker.remove(key)

        return len(expired_keys)

    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        total_requests = sum(e.get("access_count", 0) for e in self._cache.values())

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "total_requests": total_requests,
            "avg_access": total_requests / len(self._cache) if self._cache else 0,
        }

    def to_dict(self) -> dict:
        """导出缓存数据（用于持久化）"""
        return self._cache

    @classmethod
    def from_dict(cls, data: dict, **kwargs) -> "FrequencyWeightCache":
        """从数据加载缓存"""
        cache = cls(**kwargs)
        cache._cache = data
        for key in data:
            cache._access_tracker.touch(key)
        return cache


class EconomyController:
    """经济控制器 - 限制 AI 调用成本"""

    def __init__(self):
        self.usage_file = Config.KNOWLEDGE_DIR / "usage_stats.json"
        self.cache_file = Config.KNOWLEDGE_DIR / "ai_cache.json"
        self.stats = self._load_stats()
        self._check_and_reset()
        # 高级缓存实例
        self._advanced_cache: FrequencyWeightCache | None = None
        # 线程安全锁
        self._cache_lock = threading.RLock()
        # 指标上报端点（可选，通过 set_metrics_endpoint 设置）
        self._metrics_endpoint: str | None = None
        # 自动加载缓存
        self._auto_load_cache()

    def _auto_load_cache(self):
        """自动加载缓存（若文件存在）"""
        dump_file = str(self.cache_file).replace(".json", "_dump.json")
        if self.cache_file.exists():
            loaded = self.load_cache(dump_file)
            if loaded > 0:
                print(f"[Cache] Restored {loaded} entries from cache dump")

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
            encoding="utf-8",
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

    @property
    def advanced_cache(self) -> FrequencyWeightCache:
        """获取高级缓存实例（延迟加载）"""
        if self._advanced_cache is None:
            cache_data = {}
            if self.cache_file.exists():
                try:
                    cache_data = json.loads(self.cache_file.read_text(encoding="utf-8"))
                except Exception:
                    pass
            self._advanced_cache = FrequencyWeightCache.from_dict(
                cache_data,
                max_size=100,
                default_ttl_hours=Config.AI_CACHE_HOURS,
            )
        return self._advanced_cache

    def check_quota(self, estimated_tokens: int = 1000) -> dict:
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
                "quota_remaining": self._get_quota_remaining(),
            }

        # 检查每日 Token 上限
        if self.stats.daily_tokens + estimated_tokens >= 100000:  # max_tokens_per_day
            return {
                "allowed": False,
                "reason": "每日 Token 上限即将耗尽 (100000)",
                "quota_remaining": self._get_quota_remaining(),
            }

        return {
            "allowed": True,
            "reason": "",
            "quota_remaining": self._get_quota_remaining(),
        }

    def _get_quota_remaining(self) -> dict:
        """获取剩余配额"""
        return {
            "hourly_calls": max(0, 50 - self.stats.hourly_calls),
            "daily_tokens": max(0, 100000 - self.stats.daily_tokens),
            "daily_calls": self.stats.daily_calls,
        }

    def record_call(self, tokens_used: int = 0):
        """记录一次调用"""
        self._check_and_reset()
        self.stats.hourly_calls += 1
        self.stats.daily_calls += 1
        self.stats.daily_tokens += tokens_used
        self._save_stats()

    def record_cache_hit(self):
        """记录缓存命中（线程安全）"""
        with self._cache_lock:
            self.stats.cache_hits += 1
            self._save_stats()

    def record_cache_miss(self):
        """记录缓存未命中（线程安全）"""
        with self._cache_lock:
            self.stats.cache_misses += 1
            self._save_stats()

    def get_cache_key(self, prompt: str, context: str = "") -> str:
        """生成缓存键"""
        content = f"{context}:{prompt}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def get_cached_result(self, cache_key: str) -> str | None:
        """获取缓存结果（使用高级缓存，线程安全）"""
        with self._cache_lock:
            result = self.advanced_cache.get(cache_key)
            if result:
                self.record_cache_hit()
                # 热门内容延长 TTL
                self.advanced_cache.extend_ttl(cache_key, additional_hours=2)
                self._persist_cache()
            else:
                self.record_cache_miss()
            return result

    def save_cache(self, cache_key: str, result: str):
        """保存缓存结果（使用高级缓存，线程安全）"""
        with self._cache_lock:
            self.advanced_cache.set(
                cache_key,
                result,
                ttl_hours=Config.AI_CACHE_HOURS,
            )
            self._persist_cache()
            self.record_cache_miss()
            # 自动持久化到 dump 文件
            self._auto_dump_cache()

    def _persist_cache(self):
        """持久化缓存到磁盘（线程安全）"""
        with self._cache_lock:
            self.cache_file.write_text(
                json.dumps(self.advanced_cache.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    def clear_expired_cache(self) -> int:
        """清理过期缓存，返回清理数量（线程安全）"""
        with self._cache_lock:
            count = self.advanced_cache.clear_expired()
            if count > 0:
                self._persist_cache()
                self._auto_dump_cache()
            return count

    def _auto_dump_cache(self):
        """自动持久化缓存到 dump 文件"""
        dump_file = str(self.cache_file).replace(".json", "_dump.json")
        self.dump_cache(dump_file)

    def set_metrics_endpoint(self, endpoint: str | None):
        """设置指标上报端点

        Args:
            endpoint: 监控 URL，设置为 None 则禁用上报
        """
        self._metrics_endpoint = endpoint

    def dump_cache(self, path: str = "cache_dump.json") -> bool:
        """导出缓存到 JSON 文件

        Args:
            path: 导出文件路径

        Returns:
            bool: 是否成功
        """

        with self._cache_lock:
            cache_data = self.advanced_cache.to_dict()

            # 序列化为扩展格式
            dump_data = {}
            for key, entry in cache_data.items():
                created = datetime.fromisoformat(entry["created_at"])
                ttl_hours = entry.get("ttl_hours", self.advanced_cache.default_ttl_hours)
                expire_at = created + timedelta(hours=ttl_hours)

                dump_data[key] = {
                    "value": entry["result"],
                    "expire_at": expire_at.isoformat(),
                    "access_count": entry.get("access_count", 0),
                    "created_at": entry["created_at"],
                    "last_access": entry["last_access"],
                    "ttl_hours": ttl_hours,
                }

            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(dump_data, f, ensure_ascii=False, indent=2)
                return True
            except Exception:
                return False

    def load_cache(self, path: str = "cache_dump.json") -> int:
        """从 JSON 文件加载缓存

        Args:
            path: 导入文件路径

        Returns:
            int: 加载的条目数量（已过滤过期）
        """
        import os

        if not os.path.exists(path):
            return 0

        try:
            with open(path, "r", encoding="utf-8") as f:
                dump_data = json.load(f)
        except Exception:
            return 0

        now = datetime.now()
        loaded = 0

        with self._cache_lock:
            for key, entry in dump_data.items():
                # 过滤已过期
                expire_at = datetime.fromisoformat(entry["expire_at"])
                if expire_at <= now:
                    continue

                # 恢复缓存
                self.advanced_cache.set(
                    key,
                    entry["value"],
                    ttl_hours=entry.get("ttl_hours", self.advanced_cache.default_ttl_hours),
                )
                # 恢复访问次数
                if key in self.advanced_cache._cache:
                    self.advanced_cache._cache[key]["access_count"] = entry.get("access_count", 0)
                loaded += 1

            if loaded > 0:
                self._persist_cache()

        return loaded

    def prewarm_cache(
        self,
        keys: list[str],
        loader: callable[[str], str],
        show_progress: bool = True,
        ttl_hours: int | None = None,
    ) -> dict:
        """预热缓存 - 批量加载高频 key

        Args:
            keys: 需要预热的 key 列表
            loader: 加载函数，输入 key，返回缓存值
            show_progress: 是否显示进度条
            ttl_hours: 自定义 TTL 小时数

        Returns:
            {
                "success": int,  # 成功数量
                "failed": list[str],  # 失败的 key
                "skipped": int  # 跳过的数量（已存在）
            }
        """
        import threading

        result = {"success": 0, "failed": [], "skipped": 0}
        total = len(keys)
        ttl = ttl_hours or Config.AI_CACHE_HOURS

        # 进度显示函数（线程安全）
        def progress_callback(current: int, key: str, status: str):
            if show_progress:
                pct = current / total * 100
                bar_len = 20
                filled = int(bar_len * current / total)
                bar = "#" * filled + "-" * (bar_len - filled)
                # 使用 ASCII 避免编码问题
                status_emoji = {"OK": "[+]", "FAIL": "[x]", "ERR": "[!]", "空值": "[-]"}.get(status, "[?]")
                print(
                    f"\r[{bar}] {current}/{total} ({pct:.0f}%) {status_emoji}",
                    end="",
                    flush=True,
                )

        # 线程安全的结果更新
        lock = threading.Lock()

        def safe_save(key: str, value: str):
            try:
                self.advanced_cache.set(key, value, ttl_hours=ttl)
                with lock:
                    result["success"] += 1
                progress_callback(
                    result["success"] + len(result["failed"]) + result["skipped"],
                    key,
                    "OK",
                )
            except Exception:
                with lock:
                    result["failed"].append(key)
                progress_callback(
                    result["success"] + len(result["failed"]) + result["skipped"],
                    key,
                    "FAIL",
                )

        # 过滤已存在的 key
        keys_to_load = []
        for key in keys:
            if self.advanced_cache.get(key) is None:
                keys_to_load.append(key)
            else:
                result["skipped"] += 1

        if not keys_to_load:
            print("\r[Prewarm] All keys already exist")
            return result

        print(f"Prewarming {len(keys_to_load)} cache entries...")

        # 串行加载（避免并发过高）
        for i, key in enumerate(keys_to_load, 1):
            try:
                value = loader(key)
                if value:
                    safe_save(key, value)
                else:
                    result["failed"].append(key)
                    progress_callback(i, key, "空值")
            except Exception:
                result["failed"].append(key)
                progress_callback(i, key, "ERR")

        # 最终持久化
        self._persist_cache()

        if show_progress:
            print()  # 换行
            print(
                f"Prewarm done: {result['success']} OK, "
                f"{result['skipped']} skipped, "
                f"{len(result['failed'])} failed"
            )

        # 自动上报指标（如果有配置端点）
        if hasattr(self, "_metrics_endpoint") and self._metrics_endpoint:
            self.report_metrics(self._metrics_endpoint)

        return result

    def estimate_tokens(self, text: str) -> int:
        """估算文本的 Token 数量（粗略估计：1 token ≈ 4 字符）"""
        return len(text) // 4 + 1

    def get_metrics_json(self) -> dict:
        """获取结构化缓存指标 JSON

        Returns:
            {
                "total_requests": int,
                "cache_hits": int,
                "cache_misses": int,
                "hit_rate": float,
                "current_size": int,
                "max_size": int,
                "total_access": int,
                "avg_access": float,
                "expired_count": int,
                "timestamp": str
            }
        """
        with self._cache_lock:
            self._check_and_reset()
            cache_stats = self.advanced_cache.get_stats()
            total = self.stats.cache_hits + self.stats.cache_misses
            hit_rate = self.stats.cache_hits / total if total > 0 else 0.0

            return {
                "total_requests": total,
                "cache_hits": self.stats.cache_hits,
                "cache_misses": self.stats.cache_misses,
                "hit_rate": round(hit_rate, 4),
                "current_size": cache_stats.get("size", 0),
                "max_size": cache_stats.get("max_size", 100),
                "total_access": cache_stats.get("total_requests", 0),
                "avg_access": round(cache_stats.get("avg_access", 0), 2),
                "expired_count": len([
                    k for k, e in self.advanced_cache.to_dict().items()
                    if datetime.fromisoformat(e["created_at"])
                    .replace(tzinfo=None) + timedelta(hours=e.get("ttl_hours", 24))
                    < datetime.now()
                ]),
                "timestamp": datetime.now().isoformat(),
            }

    def report_metrics(self, endpoint: str) -> dict:
        """上报缓存指标到监控端点

        Args:
            endpoint: 监控 URL

        Returns:
            {"success": bool, "status_code": int, "response": str}
        """
        import urllib.error
        import urllib.request

        metrics = self.get_metrics_json()
        try:
            data = json.dumps(metrics).encode("utf-8")
            req = urllib.request.Request(
                endpoint,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return {
                    "success": True,
                    "status_code": resp.status,
                    "response": resp.read().decode("utf-8"),
                }
        except urllib.error.HTTPError as e:
            return {
                "success": False,
                "status_code": e.code,
                "response": str(e),
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": 0,
                "response": str(e),
            }

    def get_stats_summary(self) -> dict:
        """获取统计摘要"""
        self._check_and_reset()
        cache_stats = self.advanced_cache.get_stats()
        return {
            "当前周期": {
                "小时": self.stats.last_reset_hour,
                "日期": self.stats.last_reset_date,
            },
            "调用统计": {
                "本小时调用": self.stats.hourly_calls,
                "本日调用": self.stats.daily_calls,
                "本日Token": f"{self.stats.daily_tokens:,}",
            },
            "缓存统计": {
                "命中次数": self.stats.cache_hits,
                "未命中次数": self.stats.cache_misses,
                "命中率": f"{self.stats.cache_hit_rate:.1%}",
                "缓存条目": cache_stats.get("size", 0),
                "总访问": cache_stats.get("total_requests", 0),
            },
            "剩余配额": self._get_quota_remaining(),
            "成本估计": {
                "今日消耗": f"~${self.stats.daily_tokens * 0.0000015:.4f}",
                "缓存节省": f"~${self.stats.cache_hits * 1000 * 0.0000015:.4f}",
            },
        }


class SmartCache:
    """智能缓存 - 支持相似度匹配（已废弃，使用 FrequencyWeightCache 替代）"""

    def __init__(self, similarity_threshold: float = 0.85):
        import warnings
        warnings.warn(
            "SmartCache is deprecated, use EconomyController.advanced_cache instead",
            DeprecationWarning,
            stacklevel=2,
        )
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

    def find_similar(self, prompt: str, context: str = "") -> str | None:
        """查找相似的历史查询结果"""
        return self.controller.get_cached_result(
            self.controller.get_cache_key(prompt, context),
        )

    def save_with_prompt(self, prompt: str, context: str, result: str):
        """保存结果，同时记录原始 prompt 用于相似度匹配"""
        cache_key = self.controller.get_cache_key(prompt, context)
        self.controller.save_cache(cache_key, result)
