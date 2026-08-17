import time
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Callable
from collections import defaultdict
import bisect

logger = logging.getLogger("taskforge.redis")

class MemorySortedSet:
    """Emulates Redis Sorted Set (ZSET) with score ordering using binary insertion."""
    def __init__(self):
        # List of tuples (score, member) maintained in sorted order
        self.elements: List[Tuple[float, str]] = []
        self.member_scores: Dict[str, float] = {}

    def zadd(self, mapping: Dict[str, float]) -> int:
        added = 0
        for member, score in mapping.items():
            if member in self.member_scores:
                self.zrem(member)
            bisect.insort(self.elements, (score, member))
            self.member_scores[member] = score
            added += 1
        return added

    def zrem(self, *members: str) -> int:
        removed = 0
        for m in members:
            if m in self.member_scores:
                score = self.member_scores.pop(m)
                idx = bisect.bisect_left(self.elements, (score, m))
                if idx < len(self.elements) and self.elements[idx] == (score, m):
                    self.elements.pop(idx)
                    removed += 1
        return removed

    def zrangebyscore(self, min_score: float, max_score: float, start: int = 0, num: Optional[int] = None) -> List[str]:
        res = []
        for score, member in self.elements:
            if min_score <= score <= max_score:
                res.append(member)
        if num is not None:
            return res[start:start + num]
        return res[start:]

    def zpopmin(self, count: int = 1) -> List[Tuple[str, float]]:
        res = []
        for _ in range(min(count, len(self.elements))):
            if self.elements:
                score, member = self.elements.pop(0)
                self.member_scores.pop(member, None)
                res.append((member, score))
        return res

    def zcard(self) -> int:
        return len(self.elements)

    def zscore(self, member: str) -> Optional[float]:
        return self.member_scores.get(member)


class MemoryRedisClient:
    """In-memory full emulation of Redis data structures & operations."""
    def __init__(self):
        self.hashes: Dict[str, Dict[str, str]] = defaultdict(dict)
        self.sorted_sets: Dict[str, MemorySortedSet] = defaultdict(MemorySortedSet)
        self.lists: Dict[str, List[str]] = defaultdict(list)
        self.strings: Dict[str, str] = {}
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.is_emulated = True

    def ping(self) -> bool:
        return True

    # --- HASHES (HSET, HGET, HGETALL, HDEL) ---
    def hset(self, key: str, mapping: Optional[Dict[str, Any]] = None, key_arg: Optional[str] = None, val_arg: Optional[Any] = None) -> int:
        if mapping:
            for k, v in mapping.items():
                self.hashes[key][str(k)] = str(v)
            return len(mapping)
        elif key_arg and val_arg is not None:
            self.hashes[key][str(key_arg)] = str(val_arg)
            return 1
        return 0

    def hget(self, key: str, field: str) -> Optional[str]:
        return self.hashes[key].get(str(field))

    def hgetall(self, key: str) -> Dict[str, str]:
        return dict(self.hashes.get(key, {}))

    def hdel(self, key: str, *fields: str) -> int:
        count = 0
        if key in self.hashes:
            for f in fields:
                if str(f) in self.hashes[key]:
                    del self.hashes[key][str(f)]
                    count += 1
        return count

    # --- SORTED SETS (ZADD, ZRANGEBYSCORE, ZREM, ZPOPMIN, ZCARD) ---
    def zadd(self, key: str, mapping: Dict[str, float]) -> int:
        return self.sorted_sets[key].zadd(mapping)

    def zrem(self, key: str, *members: str) -> int:
        if key in self.sorted_sets:
            return self.sorted_sets[key].zrem(*members)
        return 0

    def zrangebyscore(self, key: str, min_score: float, max_score: float, start: int = 0, num: Optional[int] = None) -> List[str]:
        if key in self.sorted_sets:
            return self.sorted_sets[key].zrangebyscore(min_score, max_score, start, num)
        return []

    def zpopmin(self, key: str, count: int = 1) -> List[Tuple[str, float]]:
        if key in self.sorted_sets:
            return self.sorted_sets[key].zpopmin(count)
        return []

    def zcard(self, key: str) -> int:
        if key in self.sorted_sets:
            return self.sorted_sets[key].zcard()
        return 0

    def zscore(self, key: str, member: str) -> Optional[float]:
        if key in self.sorted_sets:
            return self.sorted_sets[key].zscore(member)
        return None

    # --- LISTS (LPUSH, RPUSH, LPOP, RPOP, LRANGE, LLEN) ---
    def lpush(self, key: str, *values: str) -> int:
        for v in values:
            self.lists[key].insert(0, str(v))
        return len(self.lists[key])

    def rpush(self, key: str, *values: str) -> int:
        for v in values:
            self.lists[key].append(str(v))
        return len(self.lists[key])

    def lpop(self, key: str) -> Optional[str]:
        if self.lists.get(key):
            return self.lists[key].pop(0)
        return None

    def rpop(self, key: str) -> Optional[str]:
        if self.lists.get(key):
            return self.lists[key].pop()
        return None

    def lrange(self, key: str, start: int, stop: int) -> List[str]:
        lst = self.lists.get(key, [])
        if stop == -1:
            return lst[start:]
        return lst[start:stop + 1]

    def llen(self, key: str) -> int:
        return len(self.lists.get(key, []))

    # --- GENERIC (KEYS, DELETE, FLUSHDB) ---
    def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if k in self.hashes: del self.hashes[k]; count += 1
            if k in self.sorted_sets: del self.sorted_sets[k]; count += 1
            if k in self.lists: del self.lists[k]; count += 1
            if k in self.strings: del self.strings[k]; count += 1
        return count

    def keys(self, pattern: str = "*") -> List[str]:
        all_k = set(self.hashes.keys()) | set(self.sorted_sets.keys()) | set(self.lists.keys()) | set(self.strings.keys())
        if pattern == "*":
            return list(all_k)
        prefix = pattern.rstrip("*")
        return [k for k in all_k if k.startswith(prefix)]

    def flushdb(self) -> bool:
        self.hashes.clear()
        self.sorted_sets.clear()
        self.lists.clear()
        self.strings.clear()
        return True

    # --- PUB/SUB ---
    def publish(self, channel: str, message: str) -> int:
        subs = self.subscribers.get(channel, [])
        for callback in subs:
            try:
                callback(message)
            except Exception:
                pass
        return len(subs)


def get_redis_client():
    """Returns a connected live Redis client if available, or the embedded Redis engine."""
    from app.core.config import settings
    try:
        import redis
        client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD or None,
            decode_responses=True,
            socket_timeout=1.0
        )
        client.ping()
        client.is_emulated = False
        print("[Redis] Connected to live Redis instance at localhost:6379")
        return client
    except Exception:
        print("[Redis] Live Redis server not detected. Initialized embedded high-performance Redis engine.")
        return MemoryRedisClient()

redis_client = get_redis_client()
