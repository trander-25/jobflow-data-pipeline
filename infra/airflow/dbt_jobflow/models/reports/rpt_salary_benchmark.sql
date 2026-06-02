{{ config(
    materialized='table',
    schema='reports',
    tags=['report', 'salary']
) }}

SELECT
    sb.salary_band_id,
    sb.salary_band,
    sb.salary_band_sort_order,
    sb.lower_bound_vnd,
    sb.upper_bound_vnd,
    COUNT(f.job_id) AS num_positions,
    COUNT(DISTINCT CASE WHEN f.salary_avg_million IS NOT NULL THEN f.url END) AS salaried_positions,
    ROUND(AVG(f.salary_avg_million), 1) AS avg_salary,
    approx_percentile(f.salary_avg_million, 0.25) AS salary_q1,
    approx_percentile(f.salary_avg_million, 0.50) AS salary_median,
    approx_percentile(f.salary_avg_million, 0.75) AS salary_q3,
    MIN(f.salary_min_million) AS min_salary,
    MAX(f.salary_max_million) AS max_salary,
    COUNT(DISTINCT CASE WHEN f.work_model_normalized = 'Remote' THEN f.url END) AS remote_positions,
    COUNT(DISTINCT CASE WHEN f.work_model_normalized = 'Hybrid' THEN f.url END) AS hybrid_positions,
    COUNT(DISTINCT CASE WHEN f.work_model_normalized = 'On-Site' THEN f.url END) AS onsite_positions
FROM {{ ref('dim_salary_band') }} sb
LEFT JOIN {{ ref('fct_jobs') }} f
    ON sb.salary_band_id = f.salary_band_id
GROUP BY sb.salary_band_id, sb.salary_band, sb.salary_band_sort_order, sb.lower_bound_vnd, sb.upper_bound_vnd
