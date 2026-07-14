# -*- coding: utf-8 -*-
import redis
from app import app
from datetime import datetime

# Initialize raw redis client for rate limiting
redis_client = None
try:
    redis_url = app.config.get('SOCKET_MESSAGE_QUEUE', 'redis://:@redis:6379/0')
    # Connect to the Redis instance shared with Celery & Socket.io
    redis_client = redis.StrictRedis.from_url(redis_url)
except Exception as e:
    print("[RateLimiter] Redis connection failed, bypassing rate-limiter:", e)

def check_and_incr_ai_rate_limit(user_id):
    """
    Rate Limiter for LLM diagnostics.
    Limits:
    - 3 requests per minute (prevents rapid spamming)
    - 15 requests per hour (prevents batch workflow abuse)
    - 50 requests per day (caps cost per Premium user per day)
    Returns: (is_allowed, error_message)
    """
    if not redis_client:
        # Default allow if Redis is unavailable to preserve user experience
        return True, "Redis offline, bypass"

    now = datetime.now()
    min_key = f"limiter:ai:{user_id}:min:{now.strftime('%Y%m%d%H%M')}"
    hour_key = f"limiter:ai:{user_id}:hour:{now.strftime('%Y%m%d%H')}"
    day_key = f"limiter:ai:{user_id}:day:{now.strftime('%Y%m%d')}"

    try:
        # 1. Check minute limit
        min_count = redis_client.get(min_key)
        if min_count and int(min_count) >= 3:
            return False, "您每分钟最多可进行 3 次 AI 诊断，请稍后再试。"

        # 2. Check hour limit
        hour_count = redis_client.get(hour_key)
        if hour_count and int(hour_count) >= 15:
            return False, "您每小时最多可进行 15 次 AI 诊断，请稍后再试。"

        # 3. Check day limit
        day_count = redis_client.get(day_key)
        if day_count and int(day_count) >= 50:
            return False, "您每天最多可使用 50 次 AI 自动诊断，额度已耗尽。"

        # Atomically increment and set TTL to prevent Redis memory leak
        pipe = redis_client.pipeline()
        pipe.incr(min_key)
        pipe.expire(min_key, 60)
        
        pipe.incr(hour_key)
        pipe.expire(hour_key, 3600)
        
        pipe.incr(day_key)
        pipe.expire(day_key, 86400)
        pipe.execute()

        return True, "Allowed"
    except Exception as e:
        print("[RateLimiter] Error communicating with Redis:", e)
        return True, "Error bypass"
