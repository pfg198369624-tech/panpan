import json
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models.review import ReviewRaw
from app.core.config import settings

logger = logging.getLogger(__name__)


class Importer:
    def import_json(self, db: Session, session_id: str, content: str) -> int:
        try:
            data = json.loads(content)
            if isinstance(data, dict) and "reviews" in data:
                data = data["reviews"]
            if not isinstance(data, list):
                data = [data]
        except Exception as e:
            logger.error(f"Failed to parse JSON: {e}")
            return 0

        return self._save_reviews(db, session_id, data, "import_json")

    def import_csv(self, db: Session, session_id: str, content: str) -> int:
        import csv
        import io

        reader = csv.DictReader(io.StringIO(content))
        data = []
        for row in reader:
            data.append(row)
        return self._save_reviews(db, session_id, data, "import_csv")

    def _save_reviews(self, db: Session, session_id: str, data: list, source: str) -> int:
        total = 0
        for item in data:
            review_id = item.get("review_id", "")
            if not review_id:
                continue

            existing = db.query(ReviewRaw).filter(
                ReviewRaw.review_id == review_id,
                ReviewRaw.session_id == session_id,
            ).first()
            if existing:
                continue

            from datetime import datetime
            reviewed_at = None
            try:
                reviewed_at = datetime.fromisoformat(item.get("reviewed_at", "").replace("Z", "+00:00"))
            except Exception:
                pass

            review = ReviewRaw(
                session_id=session_id,
                app_id=item.get("app_id", ""),
                review_id=review_id,
                author=item.get("author", ""),
                rating=int(item.get("rating", 0)),
                title=item.get("title", ""),
                content=item.get("content", ""),
                version=item.get("version", ""),
                country=item.get("country", settings.default_country),
                reviewed_at=reviewed_at,
                source=source,
            )
            db.add(review)
            total += 1

        db.commit()
        return total


importer = Importer()
