{{ config(
    materialized='table',
    schema='reports',
    tags=['report', 'job_category']
) }}

SELECT
    jc.job_category_id,
    ROW_NUMBER() OVER (ORDER BY COUNT(f.job_id) DESC) AS demand_rank,
    jc.job_category,
    COUNT(f.job_id) AS num_positions,
    COUNT(DISTINCT f.company_id) AS num_companies,
    COUNT(DISTINCT f.location_id) AS num_locations,
    ROUND(100.0 * COUNT(f.job_id) / NULLIF((SELECT COUNT(*) FROM {{ ref('fct_jobs') }}), 0), 2) AS pct_of_all_jobs,
    ROUND(AVG(f.salary_avg_million), 1) AS avg_salary,
    MIN(f.salary_min_million) AS min_salary,
    MAX(f.salary_max_million) AS max_salary,
    COUNT(DISTINCT CASE WHEN f.work_model_normalized = 'Remote' THEN f.url END) AS remote_positions,
    COUNT(DISTINCT CASE WHEN f.work_model_normalized = 'Hybrid' THEN f.url END) AS hybrid_positions
FROM {{ ref('dim_job_category') }} jc
LEFT JOIN {{ ref('fct_jobs') }} f
    ON jc.job_category_id = f.job_category_id
GROUP BY jc.job_category_id, jc.job_category
