import re
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models.review import ReviewRaw, ReviewCleaned

logger = logging.getLogger(__name__)


class Cleaner:
    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text

    def is_noise(self, text: str) -> bool:
        if not text or len(text) < 3:
            return True
        if re.match(r'^[\s\W]+$', text):
            return True
        return False

    def detect_language(self, text: str) -> str:
        try:
            from langdetect import detect
            lang = detect(text)
            return lang
        except Exception:
            return "unknown"

    def deduplicate(self, db: Session, session_id: str):
        from sqlalchemy import func
        groups = db.query(
            ReviewRaw.content,
            func.count(ReviewRaw.id).label("cnt"),
        ).filter(
            ReviewRaw.session_id == session_id
        ).group_by(ReviewRaw.content).having(func.count(ReviewRaw.id) > 1).all()

        from difflib import SequenceMatcher
        all_reviews = db.query(ReviewRaw).filter(ReviewRaw.session_id == session_id).all()
        group_id = 0
        marked = set()

        for i, r1 in enumerate(all_reviews):
            if r1.id in marked:
                continue
            group_id += 1
            for j, r2 in enumerate(all_reviews):
                if i >= j or r2.id in marked:
                    continue
                ratio = SequenceMatcher(None, r1.content or "", r2.content or "").ratio()
                if ratio > 0.95:
                    marked.add(r2.id)

        return marked

    async def clean(self, db: Session, session_id: str) -> int:
        raw_reviews = db.query(ReviewRaw).filter(ReviewRaw.session_id == session_id).all()
        if not raw_reviews:
            return 0

        total = 0
        for raw in raw_reviews:
            existing = db.query(ReviewCleaned).filter(
                ReviewCleaned.raw_id == raw.id
            ).first()
            if existing:
                continue

            cleaned_text = self.clean_text(raw.content or "")
            is_noise_flag = self.is_noise(cleaned_text)
            lang = self.detect_language(cleaned_text) if not is_noise_flag else "unknown"

            cleaned = ReviewCleaned(
                session_id=session_id,
                raw_id=raw.id,
                content_clean=cleaned_text,
                language=lang,
                is_noise=1 if is_noise_flag else 0,
            )
            db.add(cleaned)
            total += 1

        db.commit()

        dupes = self.deduplicate(db, session_id)
        if dupes:
            for raw_id in dupes:
                db.query(ReviewCleaned).filter(
                    ReviewCleaned.raw_id == raw_id
                ).update({"is_duplicate": 1})
            db.commit()

        return total


cleaner = Cleaner()
