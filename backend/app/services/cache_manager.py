import json
from datetime import datetime
from pathlib import Path


class CacheManager:
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            cache_dir = str(Path(__file__).parent.parent.parent / "cached_data")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def save(self, app_id: str, reviews: list):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{app_id}_{timestamp}.json"
        data = {
            "__cache_meta__": {
                "app_id": app_id,
                "collected_at": timestamp,
                "source": "iTunes RSS Feed",
                "count": len(reviews),
                "is_cached": True,
                "note": "此文件为缓存数据，仅在网络不可用时作为回退。在线模式下优先使用实时采集。",
            },
            "reviews": reviews,
        }
        filepath = self.cache_dir / filename
        filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(filepath)
