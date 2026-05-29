{{ config(
    materialized='table',
    tags=['gold_layer', 'dimension']
) }}

SELECT
    education_id,
    education_requirement,
    CASE education_requirement
        WHEN 'College' THEN 1
        WHEN 'Bachelor' THEN 2
        WHEN 'Master' THEN 3
        WHEN 'PhD' THEN 4
        WHEN 'Unknown' THEN 99
        ELSE 98
    END AS education_sort_order,
    CASE
        WHEN education_requirement = 'Unknown' THEN false
        ELSE true
    END AS is_specified,
    CAST(CURRENT_TIMESTAMP AS TIMESTAMP) AS dbt_load_timestamp
FROM (
    SELECT DISTINCT
        {{ dimension_surrogate_key('education_requirement') }} AS education_id,
        education_requirement
    FROM {{ ref('int_jobs_unified') }}
    WHERE education_requirement IS NOT NULL
        AND job_category IS NOT NULL
        AND job_category != 'Others'
) education
