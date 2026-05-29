{{ config(
    materialized='table',
    schema='reports',
    tags=['report', 'platform']
) }}

SELECT
    source_platform,
    COUNT(*) AS total_job_postings,
    COUNT(DISTINCT company_id) AS unique_companies,
    COUNT(DISTINCT location_id) AS unique_locations,
    COUNT(DISTINCT job_title) AS unique_job_titles,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN posted_to_discord THEN url END) / NULLIF(COUNT(*), 0), 2) AS pct_discord_posted,
    COUNT(DISTINCT CASE WHEN work_model_normalized = 'Remote' THEN url END) AS remote_jobs_count,
    COUNT(DISTINCT CASE WHEN work_model_normalized = 'Hybrid' THEN url END) AS hybrid_jobs_count,
    COUNT(DISTINCT CASE WHEN work_model_normalized = 'On-Site' THEN url END) AS onsite_jobs_count,
    COUNT(DISTINCT CASE WHEN work_arrangement_normalized = 'Full-time' THEN url END) AS fulltime_jobs_count,
    ROUND(AVG(salary_avg_million), 1) AS avg_salary,
    COUNT(DISTINCT CASE WHEN salary_avg_million IS NOT NULL THEN url END) AS salaried_positions_count,
    MIN(job_posted_date) AS earliest_job_date,
    MAX(job_posted_date) AS latest_job_date
FROM {{ ref('fct_jobs') }}
GROUP BY source_platform
