{{ config(materialized='table', tags=['audit', 'task_performance']) }}

SELECT
    task_name,
    task_group,
    data_source,
    layer,
    COUNT(*) AS execution_count,
    SUM(CASE WHEN task_status = 'success' THEN 1 ELSE 0 END) AS success_count,
    SUM(CASE WHEN task_status = 'failed' THEN 1 ELSE 0 END) AS failure_count,
    ROUND(100.0 * SUM(CASE WHEN task_status = 'success' THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct,
    AVG(task_duration_seconds) AS avg_duration_seconds,
    MIN(task_duration_seconds) AS min_duration_seconds,
    MAX(task_duration_seconds) AS max_duration_seconds,
    AVG(rows_processed) AS avg_rows_processed,
    MAX(execution_date) AS last_execution_date
FROM {{ source('audit_layer', 'master_job_elt_audit') }}
WHERE dag_id = 'master_job_elt'
GROUP BY task_name, task_group, data_source, layer
