import time
from functools import lru_cache

def _window(ttl=3600):
    return int(time.time() // ttl)

def timed_lru_cache(ttl=3600, maxsize=32):
    def wrap(fn):
        @lru_cache(maxsize=maxsize)
        def inner(window, *args, **kwargs):
            return fn(*args, **kwargs)
        def caller(*args, **kwargs):
            return inner(_window(ttl), *args, **kwargs)
        caller.cache_clear = inner.cache_clear
        return caller
    return wrap
