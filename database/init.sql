CREATE DATABASE IF NOT EXISTS app_review_insights DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE app_review_insights;

CREATE TABLE analysis_sessions (
    id                  VARCHAR(64) PRIMARY KEY,
    app_id              VARCHAR(64) NOT NULL,
    app_name            VARCHAR(255),
    app_url             TEXT NOT NULL,
    user_goal           TEXT,
    status              VARCHAR(32) DEFAULT 'created',
    current_step        INT DEFAULT 0,
    ai_model            VARCHAR(128),
    total_tokens        INT DEFAULT 0,
    total_cost          DECIMAL(10,6) DEFAULT 0,
    total_prompt_tokens INT DEFAULT 0,
    total_completion_tokens INT DEFAULT 0,
    ai_call_count       INT DEFAULT 0,
    ai_fail_count       INT DEFAULT 0,
    ai_retry_count      INT DEFAULT 0,
    started_at          DATETIME,
    finished_at         DATETIME,
    duration_seconds    INT DEFAULT 0,
    error_message       TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE reviews_raw (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id      VARCHAR(64) NOT NULL,
    app_id          VARCHAR(64) NOT NULL,
    review_id       VARCHAR(128) NOT NULL,
    author          VARCHAR(255),
    rating          TINYINT NOT NULL,
    title           TEXT,
    content         TEXT NOT NULL,
    version         VARCHAR(64),
    country         VARCHAR(8) DEFAULT 'us',
    reviewed_at     DATETIME,
    collected_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    source          VARCHAR(32) DEFAULT 'rss',
    INDEX idx_session (session_id),
    INDEX idx_app_id (app_id),
    UNIQUE KEY uk_review_session (review_id, session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE reviews_cleaned (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id      VARCHAR(64) NOT NULL,
    raw_id          BIGINT NOT NULL,
    content_clean   TEXT,
    language        VARCHAR(16),
    is_duplicate    TINYINT DEFAULT 0,
    duplicate_group VARCHAR(64),
    is_noise        TINYINT DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id),
    FOREIGN KEY (raw_id) REFERENCES reviews_raw(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE classifications (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id      VARCHAR(64) NOT NULL,
    cleaned_id      BIGINT NOT NULL,
    topic           VARCHAR(128) NOT NULL,
    subtopic        VARCHAR(128),
    sentiment       VARCHAR(16),
    ai_labeled      TINYINT DEFAULT 1,
    confidence      DECIMAL(5,2),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id),
    INDEX idx_topic (topic),
    FOREIGN KEY (cleaned_id) REFERENCES reviews_cleaned(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE findings (
    id                   BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id           VARCHAR(64) NOT NULL,
    title                VARCHAR(255) NOT NULL,
    description          TEXT,
    source_review_ids    JSON,
    sample_count         INT DEFAULT 0,
    confidence           VARCHAR(32),
    conflicting_evidence TEXT,
    conclusion_type      VARCHAR(32),
    is_confirmed         TINYINT DEFAULT 0,
    created_at           DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE prd_versions (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id  VARCHAR(64) NOT NULL,
    version_no  VARCHAR(32) NOT NULL,
    name        VARCHAR(128),
    priority    INT DEFAULT 0,
    status      VARCHAR(32) DEFAULT 'planned',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE prd_requirements (
    id                BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id        VARCHAR(64) NOT NULL,
    version_id        BIGINT NOT NULL,
    req_id            VARCHAR(32) NOT NULL,
    title             VARCHAR(255) NOT NULL,
    description       TEXT,
    priority          VARCHAR(16) DEFAULT 'medium',
    source_finding_ids JSON,
    status            VARCHAR(32) DEFAULT 'draft',
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id),
    FOREIGN KEY (version_id) REFERENCES prd_versions(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE test_cases (
    id                BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id        VARCHAR(64) NOT NULL,
    case_id           VARCHAR(32) NOT NULL,
    req_id            VARCHAR(32) NOT NULL,
    title             VARCHAR(255) NOT NULL,
    preconditions     TEXT,
    steps             JSON,
    expected_result   TEXT,
    source_review_ids JSON,
    status            VARCHAR(32) DEFAULT 'draft',
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE workflow_logs (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id      VARCHAR(64) NOT NULL,
    step            VARCHAR(64) NOT NULL,
    status          VARCHAR(32),
    input_summary   TEXT,
    output_summary  TEXT,
    error_message   TEXT,
    started_at      DATETIME,
    finished_at     DATETIME,
    INDEX idx_session (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ai_call_logs (
    id                BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id        VARCHAR(64) NOT NULL,
    step              VARCHAR(64),
    task              VARCHAR(64),
    model             VARCHAR(128),
    prompt_snapshot   TEXT,
    response_snapshot TEXT,
    prompt_tokens     INT DEFAULT 0,
    completion_tokens INT DEFAULT 0,
    total_tokens      INT DEFAULT 0,
    cost              DECIMAL(10,6) DEFAULT 0,
    status            VARCHAR(32),
    error_message     TEXT,
    retry_count       INT DEFAULT 0,
    duration_ms       INT DEFAULT 0,
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id),
    INDEX idx_task (task)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
