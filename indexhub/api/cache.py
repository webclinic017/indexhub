from expiringdict import ExpiringDict


CACHE = ExpiringDict(max_len=20, max_age_seconds=3000)
