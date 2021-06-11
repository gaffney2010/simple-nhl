import os
import pickle
from typing import Any, Optional

from constants import *


def _transform_key(key: str) -> str:
    """Make it safe to save"""
    return os.path.join(DATA_DIR, key.replace("/", "") + ".data")


class Cacher(object):
    """A strategy for how to read and write locally."""

    def try_to_read(self, key: str) -> Optional[Any]:
        """Returns data if found, otherwise None."""
        raise NotImplementedError

    def write(self, key: str, value: Any) -> None:
        """Write value by key locally."""
        raise NotImplementedError


class NoCacher(Cacher):
    """Empty cache, doesn't save or load."""

    def try_to_read(self, key: str) -> Optional[Any]:
        return None

    def write(self, key: str, value: Any) -> None:
        pass


class BasicCacher(Cacher):
    """Implements a write-aside with a TTL for expiration."""

    def try_to_read(self, key: str) -> Optional[Any]:
        """Try to read locally."""
        tkey = _transform_key(key)
        if os.path.exists(tkey):
            with open(tkey, "rb") as f:
                return pickle.load(f)

    def write(self, key: str, value: Any) -> None:
        """Write if file doesn't already exist, and set ttl."""
        tkey = _transform_key(key)
        with open(tkey, "wb") as f:
            pickle.dump(value, f)


def memoize(key: str, cacher: Cacher):
    def real_memoize(func):
        def func_with_memo(*args, **kwargs):
            cached_value = cacher.try_to_read(key)
            if cached_value is not None:
                return cached_value
            result = func(*args, **kwargs)
            cacher.write(key, result)
            return result

        return func_with_memo

    return real_memoize
