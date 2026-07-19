from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "AppReviewInsights"
    debug: bool = True
    secret_key: str = "change-this-to-a-random-secret"

    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_name: str = "app_review_insights"
    db_user: str = "root"
    db_password: str = "your_password"

    volc_api_url: str = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    volc_model_name: str = ""
    volc_api_key: str = ""

    ai_timeout: int = 60
    ai_max_retries: int = 3
    ai_temperature: float = 0.3
    ai_max_tokens: int = 4096

    collection_max_pages: int = 10
    collection_page_size: int = 50
    collection_rate_limit: float = 1.0

    workflow_max_reflection_rounds: int = 3
    workflow_max_retry_per_step: int = 2
    workflow_total_steps: int = 7

    cors_origins: str = "*"
    db_pool_size: int = 10
    db_pool_overflow: int = 20

    ai_cost_per_token: float = 0.000001
    ai_backoff_base: int = 2
    classifier_batch_size: int = 20

    collection_http_timeout: int = 10
    itunes_rss_url: str = "https://itunes.apple.com/us/rss/customerreviews/page={page}/id={appId}/sortby=mostrecent/json?limit=20"
    default_country: str = "us"

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
