{{ config(materialized='table', tags=['audit', 'summary', 'log_tasks']) }}

SELECT
    task_name,
    DATE(execution_date) AS execution_day,
    dag_status,
    COUNT(DISTINCT dag_run_id) AS total_dag_runs,
    COUNT(DISTINCT task_id) AS total_tasks,
    SUM(CASE WHEN task_status = 'success' THEN 1 ELSE 0 END) AS successful_tasks,
    SUM(CASE WHEN task_status = 'failed' THEN 1 ELSE 0 END) AS failed_tasks,
    SUM(rows_processed) AS total_rows_processed,
    SUM(rows_inserted) AS total_rows_inserted,
    SUM(rows_scraped) AS total_rows_scraped,
    SUM(discord_posts_sent) AS total_discord_posts_sent,
    SUM(discord_posts_failed) AS total_discord_posts_failed,
    AVG(duration_seconds) AS avg_dag_duration_seconds,
    MIN(start_date) AS first_start_time,
    MAX(end_date) AS last_end_time
FROM {{ source('audit_layer', 'master_job_elt_audit') }}
WHERE dag_id = 'master_job_elt'
GROUP BY task_name, DATE(execution_date), dag_status
