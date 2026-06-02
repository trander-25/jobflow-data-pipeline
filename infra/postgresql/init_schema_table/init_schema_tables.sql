\set ON_ERROR_STOP on

\getenv db_job DB_JOB
\connect :db_job

CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE IF NOT EXISTS staging.topcv_data_job (
    id SERIAL PRIMARY KEY,
    title VARCHAR(256),
    company TEXT,
    logo_url TEXT,
    url TEXT UNIQUE NOT NULL,
    job_category VARCHAR(256),
    working_location VARCHAR(256),
    salary VARCHAR(256),
    descriptions TEXT,
    requirements TEXT,
    experiences TEXT,
    level_of_education VARCHAR(256),
    work_model VARCHAR(256),
    posted_to_discord BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staging.itviec_data_job (
    id SERIAL PRIMARY KEY,
    title VARCHAR(256),
    company TEXT,
    logo_url TEXT,
    url TEXT UNIQUE NOT NULL,
    job_category VARCHAR(256),
    working_location VARCHAR(256),
    work_model VARCHAR(256),
    tags TEXT,
    descriptions TEXT,
    requirements_and_experiences TEXT,
    posted_to_discord BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit.master_job_elt_audit (
    audit_id SERIAL PRIMARY KEY,
    dag_run_id VARCHAR(250) NOT NULL,
    dag_id VARCHAR(250) NOT NULL DEFAULT 'master_job_elt',
    execution_date TIMESTAMP NOT NULL,
    logical_date TIMESTAMP,
    run_type VARCHAR(50),
    dag_status VARCHAR(50) NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    duration_seconds INTEGER,
    task_id VARCHAR(250),
    task_name VARCHAR(250),
    task_status VARCHAR(50),
    task_start_date TIMESTAMP,
    task_end_date TIMESTAMP,
    task_duration_seconds INTEGER,
    task_retry_count INTEGER DEFAULT 0,
    task_group VARCHAR(250),
    task_type VARCHAR(100),
    data_source VARCHAR(50),
    layer VARCHAR(50),
    rows_processed INTEGER DEFAULT 0,
    rows_inserted INTEGER DEFAULT 0,
    rows_updated INTEGER DEFAULT 0,
    rows_deleted INTEGER DEFAULT 0,
    rows_scraped INTEGER DEFAULT 0,
    rows_posted_discord INTEGER DEFAULT 0,
    dbt_models_run INTEGER DEFAULT 0,
    dbt_models_success INTEGER DEFAULT 0,
    dbt_models_failed INTEGER DEFAULT 0,
    dbt_command TEXT,
    error_message TEXT,
    error_type VARCHAR(250),
    log_url TEXT,
    exception_traceback TEXT,
    discord_posts_sent INTEGER DEFAULT 0,
    discord_posts_failed INTEGER DEFAULT 0,
    discord_channel_id VARCHAR(100),
    executor VARCHAR(100),
    operator VARCHAR(250),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_dag_run UNIQUE (dag_run_id, task_id, execution_date)
);

CREATE TABLE IF NOT EXISTS staging.company_logos(
    logo_id TEXT DEFAULT NULL PRIMARY KEY,
    logo_url TEXT,
    logo_path TEXT DEFAULT NULL,
    is_downloaded BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NULL
);
