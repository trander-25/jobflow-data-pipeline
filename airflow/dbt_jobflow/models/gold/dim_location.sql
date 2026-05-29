{{ config(
    materialized='table',
    tags=['gold_layer', 'dimension'],
    indexes=[
        {'columns': ['location_id'], 'type': 'btree'}
    ]
) }}

SELECT
    location_id,
    job_location,
    'Vietnam' AS country,
    CASE
        WHEN job_location IS NULL OR trim(job_location) = '' THEN true
        ELSE false
    END AS is_unknown_location,
    CAST(CURRENT_TIMESTAMP AS TIMESTAMP) AS dbt_load_timestamp
FROM (
    SELECT DISTINCT
        {{ dimension_surrogate_key('job_location') }} AS location_id,
        job_location
    FROM {{ ref('int_jobs_unified') }}
    WHERE job_location IS NOT NULL
        AND job_category IS NOT NULL
        AND job_category != 'Others'
) locations
