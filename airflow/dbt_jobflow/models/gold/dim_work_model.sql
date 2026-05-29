{{ config(
    materialized='table',
    tags=['gold_layer', 'dimension']
) }}

SELECT
    work_model_id,
    work_model_normalized,
    CASE work_model_normalized
        WHEN 'Remote' THEN 'Offsite'
        WHEN 'Hybrid' THEN 'Mixed'
        WHEN 'On-Site' THEN 'Office'
        ELSE 'Other'
    END AS work_model_group,
    CASE work_model_normalized
        WHEN 'On-Site' THEN 1
        WHEN 'Hybrid' THEN 2
        WHEN 'Remote' THEN 3
        ELSE 99
    END AS work_model_sort_order,
    CAST(CURRENT_TIMESTAMP AS TIMESTAMP) AS dbt_load_timestamp
FROM (
    SELECT DISTINCT
        {{ dimension_surrogate_key('work_model_normalized') }} AS work_model_id,
        work_model_normalized
    FROM {{ ref('int_jobs_unified') }}
    WHERE work_model_normalized IS NOT NULL
        AND job_category IS NOT NULL
        AND job_category != 'Others'
) work_models
