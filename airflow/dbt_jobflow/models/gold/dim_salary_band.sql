{{ config(
    materialized='table',
    tags=['gold_layer', 'dimension']
) }}

SELECT
    salary_band_id,
    salary_band,
    CASE salary_band
        WHEN 'Below 10M VND' THEN 1
        WHEN '10-20M VND' THEN 2
        WHEN '20-30M VND' THEN 3
        WHEN '30-40M VND' THEN 4
        WHEN '40-50M VND' THEN 5
        WHEN '50-60M VND' THEN 6
        WHEN '60-70M VND' THEN 7
        WHEN '70-80M VND' THEN 8
        WHEN '80-90M VND' THEN 9
        WHEN '90-100M VND' THEN 10
        WHEN 'Above 100M VND' THEN 11
        WHEN 'Not Specified' THEN 99
        ELSE 98
    END AS salary_band_sort_order,
    CASE salary_band
        WHEN 'Below 10M VND' THEN 0
        WHEN '10-20M VND' THEN 10000000
        WHEN '20-30M VND' THEN 20000000
        WHEN '30-40M VND' THEN 30000000
        WHEN '40-50M VND' THEN 40000000
        WHEN '50-60M VND' THEN 50000000
        WHEN '60-70M VND' THEN 60000000
        WHEN '70-80M VND' THEN 70000000
        WHEN '80-90M VND' THEN 80000000
        WHEN '90-100M VND' THEN 90000000
        WHEN 'Above 100M VND' THEN 100000000
        ELSE NULL
    END AS lower_bound_vnd,
    CASE salary_band
        WHEN 'Below 10M VND' THEN 10000000
        WHEN '10-20M VND' THEN 20000000
        WHEN '20-30M VND' THEN 30000000
        WHEN '30-40M VND' THEN 40000000
        WHEN '40-50M VND' THEN 50000000
        WHEN '50-60M VND' THEN 60000000
        WHEN '60-70M VND' THEN 70000000
        WHEN '70-80M VND' THEN 80000000
        WHEN '80-90M VND' THEN 90000000
        WHEN '90-100M VND' THEN 100000000
        ELSE NULL
    END AS upper_bound_vnd,
    CASE
        WHEN salary_band = 'Not Specified' THEN false
        ELSE true
    END AS is_salary_specified,
    CAST(CURRENT_TIMESTAMP AS TIMESTAMP) AS dbt_load_timestamp
FROM (
    SELECT DISTINCT
        {{ dimension_surrogate_key('salary_band') }} AS salary_band_id,
        salary_band
    FROM {{ ref('int_jobs_unified') }}
    WHERE salary_band IS NOT NULL
        AND job_category IS NOT NULL
        AND job_category != 'Others'
) salary_bands
