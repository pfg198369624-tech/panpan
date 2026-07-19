import re
import time
import json
import logging
import asyncio
import httpx
from typing import Optional
from sqlalchemy.orm import Session
from app.models.review import ReviewRaw
from app.core.config import settings

logger = logging.getLogger(__name__)


class Collector:
    def __init__(self):
        self.max_pages = settings.collection_max_pages
        self.page_size = settings.collection_page_size
        self.rate_limit = settings.collection_rate_limit
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }

    def extract_app_id(self, url: str) -> str:
        match = re.search(r'/id(\d+)', url)
        if match:
            return match.group(1)
        match = re.search(r'[?&]id=(\d+)', url)
        if match:
            return match.group(1)
        raise ValueError(f"Cannot extract app ID from URL: {url}")

    async def collect(self, db: Session, session_id: str, app_url: str) -> dict:
        app_id = self.extract_app_id(app_url)
        total = 0
        pages_fetched = 0
        pages_empty = 0
        pages_errored = 0
        first_review_date = None
        last_review_date = None
        data_notes = []

        data_notes.append(f"数据来源: Apple iTunes RSS Feed (US App Store)")
        data_notes.append(f"限制: Apple RSS 最多返回约 50 条最近评论（1 页）")

        async with httpx.AsyncClient(timeout=settings.collection_http_timeout) as client:
            try:
                await client.head(
                    "https://itunes.apple.com",
                    headers=self.headers,
                    follow_redirects=True,
                    timeout=5,
                )
            except Exception as e:
                err = f"无法连接 Apple iTunes 服务器: {str(e)[:100]}"
                logger.warning(f"{err} (app_id={app_id})")
                data_notes.append(err)
                return {
                    "count": 0, "pages_fetched": 0, "pages_empty": 0,
                    "pages_errored": 1, "first_review_date": None,
                    "last_review_date": None, "data_notes": data_notes,
                }

            for page in range(1, self.max_pages + 1):
                if pages_errored >= 3:
                    data_notes.append("连续多页失败，提前终止采集")
                    break

                url = settings.itunes_rss_url.format(appId=app_id, page=page)
                page_ok = False

                for retry in range(3):
                    try:
                        resp = await client.get(url, headers=self.headers, follow_redirects=True)
                        if resp.status_code != 200:
                            pages_errored += 1
                            data_notes.append(f"第{page}页: HTTP {resp.status_code}（重试 {retry+1}/3）")
                            await asyncio.sleep(1)
                            continue

                        data = resp.json()
                        feed = data.get("feed", {})
                        entries = feed.get("entry", [])

                        if isinstance(entries, dict):
                            entries = [entries]

                        if not entries:
                            if retry < 2:
                                logger.info(f"第{page}页空结果，重试第{retry+2}次...（RSS 间歇性返回空）")
                                await asyncio.sleep(1)
                                continue
                            pages_empty += 1
                            data_notes.append(f"第{page}页: 无评论数据（重试3次后仍为空）")
                            page_ok = True
                            break

                        pages_fetched += 1
                        for entry in entries:
                            review_id = entry.get("id", {}).get("label", "")
                            if not review_id:
                                continue

                            existing = db.query(ReviewRaw).filter(
                                ReviewRaw.review_id == review_id,
                                ReviewRaw.session_id == session_id,
                            ).first()
                            if existing:
                                continue

                            author = entry.get("author", {}).get("name", {}).get("label", "")
                            rating = int(entry.get("im:rating", {}).get("label", 0))
                            title = entry.get("title", {}).get("label", "")
                            content = entry.get("content", {}).get("label", "")
                            version = entry.get("im:version", {}).get("label", "")
                            reviewed_at = entry.get("updated", {}).get("label", "")

                            from datetime import datetime
                            parsed_date = None
                            try:
                                parsed_date = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
                                if first_review_date is None or parsed_date < first_review_date:
                                    first_review_date = parsed_date
                                if last_review_date is None or parsed_date > last_review_date:
                                    last_review_date = parsed_date
                            except Exception:
                                pass

                            review = ReviewRaw(
                                session_id=session_id,
                                app_id=app_id,
                                review_id=review_id,
                                author=author,
                                rating=rating,
                                title=title,
                                content=content,
                                version=version,
                                country=settings.default_country,
                                reviewed_at=parsed_date,
                                source="rss",
                            )
                            db.add(review)
                            total += 1

                        db.commit()
                        time.sleep(self.rate_limit)
                        page_ok = True
                        break

                    except httpx.TimeoutException:
                        pages_errored += 1
                        logger.warning(f"Timeout on page {page}（重试 {retry+1}/3）")
                        if retry < 2:
                            await asyncio.sleep(1)
                        else:
                            data_notes.append(f"第{page}页: 请求超时（重试3次）")
                        continue
                    except Exception as e:
                        pages_errored += 1
                        logger.error(f"Collection error on page {page}: {e}")
                        if retry < 2:
                            await asyncio.sleep(1)
                        else:
                            data_notes.append(f"第{page}页: 错误 - {str(e)[:100]}（重试3次）")
                        continue

                if not page_ok and total == 0:
                    break

        result = {
            "count": total,
            "pages_fetched": pages_fetched,
            "pages_empty": pages_empty,
            "pages_errored": pages_errored,
            "first_review_date": str(first_review_date) if first_review_date else None,
            "last_review_date": str(last_review_date) if last_review_date else None,
            "data_notes": data_notes,
        }

        if total == 0:
            logger.warning(
                f"采集结果: app_id={app_id}, session={session_id}, "
                f"总计=0, 空页={pages_empty}, 错误页={pages_errored}. "
                f"US App Store RSS 未返回评论数据。"
            )

        return result


collector = Collector()
