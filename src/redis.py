from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from langgraph.store.redis.aio import AsyncRedisStore


async def get_redis_integration(redis_url: str) -> tuple[AsyncRedisStore, AsyncRedisSaver]:
    """Initialize Redis store and checkpointer for LangGraph"""
    async with (
        AsyncRedisStore.from_conn_string(redis_url) as store,
        AsyncRedisSaver.from_conn_string(redis_url) as checkpointer,
    ):
        return store, checkpointer
