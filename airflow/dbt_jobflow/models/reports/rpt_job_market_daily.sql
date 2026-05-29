{{ config(
    materialized='table',
    schema='reports',
    tags=['report', 'daily_market']
) }}

SELECT
    job_posted_date,
    source_platform,
    COUNT(*) AS daily_job_postings,
    COUNT(DISTINCT company_id) AS unique_companies_posting,
    COUNT(DISTINCT location_id) AS unique_locations,
    COUNT(DISTINCT CASE WHEN posted_to_discord THEN url END) AS discord_posted_count,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN posted_to_discord THEN url END) / NULLIF(COUNT(*), 0), 2) AS pct_posted_to_discord,
    ROUND(AVG(salary_avg_million), 1) AS avg_salary_offered,
    MAX(salary_max_million) AS max_salary_offered,
    MIN(salary_min_million) AS min_salary_offered,
    COUNT(DISTINCT CASE WHEN work_model_normalized = 'Remote' THEN url END) AS remote_jobs,
    COUNT(DISTINCT CASE WHEN work_model_normalized = 'Hybrid' THEN url END) AS hybrid_jobs,
    COUNT(DISTINCT CASE WHEN work_model_normalized = 'On-Site' THEN url END) AS onsite_jobs,
    COUNT(DISTINCT CASE WHEN work_arrangement_normalized = 'Full-time' THEN url END) AS fulltime_jobs
FROM {{ ref('fct_jobs') }}
GROUP BY job_posted_date, source_platform
