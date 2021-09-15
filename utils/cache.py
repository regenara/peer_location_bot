from typing import (Any,
                    Callable,
                    Dict,
                    List,
                    Union)


class Cache:
    def __init__(self):
        from config import Config

        self._redis = Config.redis

    @staticmethod
    def get_key(func: Callable, **kwargs) -> str:
        key = f'{func.__qualname__}'
        if kwargs:
            key += f':{".".join([str(value) for value in kwargs.values()])}'
        return key

    @staticmethod
    def serialization(value: Any) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        if isinstance(value, (list, tuple)):
            return [entity.to_dict() for entity in value]
        return value.to_dict() if value else None

    @staticmethod
    def deserialization(cls, value: Union[Dict[str, Any], List[Dict[str, Any]]]):
        if isinstance(value, list):
            return [cls.from_dict(obj) for obj in value]
        return cls.from_dict(value)

    @staticmethod
    def deserialization_user_data(values: List[Dict[str, Any]]) -> List[Any]:
        from db_models.campuses import Campus
        from db_models.peers import Peer
        from db_models.users import User
        return [cls.from_dict(value) for cls, value in zip((Campus, Peer, User), values)]

    async def set(self, key: str, value: Any, ttl: int = None):
        await self._redis.set(key=key, value=value, ttl=ttl)

    async def get(self, key: str) -> Any:
        return await self._redis.get(key=key)

    async def delete(self, key: str):
        await self._redis.delete(key=key)


def del_cache(keys: List[str], without_sub_key: List[int] = None):
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs) -> Any:
            cls = args[0]
            sub_key = tuple(kwargs.values())[0]
            for i, key in enumerate(keys):
                if i not in (without_sub_key or []):
                    key = f'{key}:{sub_key}'
                await Cache().delete(key=key)
            return await func(cls, **kwargs)
        return wrapper
    return decorator


def cache(ttl: int = None, serialization: bool = False, deserialization: bool = False, is_user_data: bool = False):
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs) -> Any:
            cls = args[0]
            key = Cache.get_key(func=func, **kwargs)
            value = await Cache().get(key=key)
            if not value:
                value = await func(cls, **kwargs)
                save_data = value
                if serialization:
                    save_data = Cache.serialization(value=value)
                await Cache().set(key=key, value=save_data, ttl=ttl)
                return value
            if deserialization:
                return Cache.deserialization(cls=cls, value=value)
            if is_user_data:
                return Cache.deserialization_user_data(values=value)
            return value
        return wrapper
    return decorator
