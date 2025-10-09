'''
-----------------------------------------------------------------------------
Project:     brok@CMU
File:        caching.py
Purpose:     Implements lightweight time-aware caching utilities using Python’s
             built-in functools.lru_cache. The `timed_lru_cache` decorator adds
             automatic cache expiration based on a specified TTL (time-to-live),
             improving performance for repeated web requests and computations.

Course:      95-888 Data Focused Python (Fall 2025, Section B1)
Team:        Pink Team
Members:     Meghana Dhruv (meghanad), Yiying Lu (yiyinglu),
             Shreya Verma (shreyave), Mengzhang Yin (mengzhay),
             Malikah Nathani (mnathani)
-----------------------------------------------------------------------------
'''


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
