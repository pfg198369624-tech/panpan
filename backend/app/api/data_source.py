from fastapi import APIRouter
from app.core.config import settings
from app.schemas.api_response import ApiResponse
import os

router = APIRouter(prefix="/api/data-source", tags=["data-source"])


@router.get("/info")
async def get_data_source_info():
    cached_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cached_data")
    cached_files = []
    if os.path.isdir(cached_dir):
        for f in os.listdir(cached_dir):
            if f.endswith(".json"):
                cached_files.append(f)

    return ApiResponse(data={
        "primary_source": {
            "name": "Apple iTunes RSS Feed",
            "endpoint": settings.itunes_rss_url,
            "limitations": [
                "Apple 已半废弃此端点，约 40% 概率返回空结果（采集器内置 3 次自动重试）",
                "最多返回约 50 条最近评论（仅 1 页数据）",
                "仅支持美区 App Store（country=us）",
                "只有最近评论，无法获取历史数据",
            ],
            "advantages": [
                "Apple 官方接口，结构化 JSON 响应",
                "无需鉴权，直接可调用",
            ],
        },
        "secondary_source": {
            "name": "用户上传 JSON/CSV 文件",
            "format": "JSON 为数组或 {reviews: [...]} 格式；CSV 首行为列名",
            "use_case": "当 RSS 不可用时作为主数据源，或补充更多评论",
            "fields": {
                "required": ["review_id", "content", "rating"],
                "optional": ["author", "title", "version", "reviewed_at", "app_id", "country"],
            },
        },
        "cached_data": {
            "path": "backend/cached_data/",
            "files": cached_files,
            "note": "缓存文件由在线采集生成，文件头部含 __cache_meta__ 标注。在线模式优先使用实时数据。",
        },
        "data_usage": {
            "note": "所有 AI 分析基于真实用户评论，不编造数据。数据不足时会在 findings 中透明标注置信度为 low/uncertain。",
            "traceability": "每条分类、发现、需求、测试用例均可追溯到原始评论。",
        },
    })
