{{ config(
    materialized='table',
    tags=['gold_layer', 'dimension']
) }}

SELECT
    job_category_id,
    job_category,
    CAST(CURRENT_TIMESTAMP AS TIMESTAMP) AS dbt_load_timestamp
FROM (
    SELECT DISTINCT
        {{ dimension_surrogate_key('job_category') }} AS job_category_id,
        job_category
    FROM {{ ref('int_jobs_unified') }}
    WHERE job_category IS NOT NULL
        AND job_category != 'Others'
) categories
