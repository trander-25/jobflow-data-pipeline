{{ config(
    materialized='table',
    schema='reports',
    tags=['report', 'location', 'salary']
) }}

SELECT
    l.location_id,
    ROW_NUMBER() OVER (ORDER BY AVG(f.salary_avg_million) DESC NULLS LAST) AS salary_rank,
    l.job_location,
    l.country,
    COUNT(DISTINCT f.url) AS total_jobs,
    COUNT(DISTINCT f.company_id) AS num_companies,
    COUNT(DISTINCT f.source_platform) AS num_platforms,
    ROUND(100.0 * COUNT(DISTINCT f.url) / NULLIF((SELECT COUNT(DISTINCT url) FROM {{ ref('fct_jobs') }}), 0), 2) AS pct_of_total_jobs,
    ROUND(AVG(f.salary_avg_million), 1) AS avg_salary_by_location,
    MAX(f.salary_max_million) AS highest_salary,
    MIN(f.salary_min_million) AS lowest_salary,
    COUNT(DISTINCT CASE WHEN f.work_model_normalized = 'Remote' THEN f.url END) AS remote_jobs,
    COUNT(DISTINCT CASE WHEN f.work_model_normalized = 'Hybrid' THEN f.url END) AS hybrid_jobs,
    COUNT(DISTINCT CASE WHEN f.work_model_normalized = 'On-Site' THEN f.url END) AS onsite_jobs,
    COUNT(DISTINCT CASE WHEN f.work_arrangement_normalized = 'Full-time' THEN f.url END) AS fulltime_jobs,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN f.work_model_normalized = 'Remote' THEN f.url END) / NULLIF(COUNT(DISTINCT f.url), 0), 2) AS pct_remote,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN f.work_model_normalized = 'Hybrid' THEN f.url END) / NULLIF(COUNT(DISTINCT f.url), 0), 2) AS pct_hybrid,
    ARRAY_JOIN(ARRAY_AGG(DISTINCT f.education_requirement), ', ') AS education_requirements
FROM {{ ref('dim_location') }} l
LEFT JOIN {{ ref('fct_jobs') }} f
    ON l.location_id = f.location_id
GROUP BY l.location_id, l.job_location, l.country
