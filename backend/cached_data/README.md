# Cached Data

This directory contains cached App Store review data for offline use.

## Format

Each file contains review data with a `__cache_meta__` header describing its origin:

```json
{
  "__cache_meta__": {
    "app_id": "839285684",
    "collected_at": "2025-07-18T10:00:00Z",
    "source": "iTunes RSS Feed",
    "count": 500,
    "is_cached": true,
    "note": "此文件为缓存数据，仅在网络不可用时作为回退。在线模式下优先使用实时采集。"
  },
  "reviews": [...]
}
```

## Note

Cached data is clearly labeled and does NOT replace the ability to process unseen inputs
when the required network and model configuration are available.
