{{ config(
    materialized='table',
    schema='reports',
    tags=['report', 'company', 'hiring']
) }}

SELECT
    c.company_id,
    ROW_NUMBER() OVER (ORDER BY COUNT(DISTINCT f.url) DESC) AS company_rank,
    c.company_name,
    c.source_platform,
    c.logo_id,
    COUNT(DISTINCT f.url) AS total_job_postings,
    COUNT(DISTINCT f.job_location) AS num_locations,
    COUNT(DISTINCT CASE WHEN f.posted_to_discord THEN f.url END) AS discord_postings,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN f.posted_to_discord THEN f.url END) / NULLIF(COUNT(DISTINCT f.url), 0), 2) AS pct_discord_posted,
    MIN(f.job_posted_date) AS first_posting_date,
    MAX(f.job_posted_date) AS last_posting_date,
    DATE_DIFF('day', MIN(f.job_posted_date), MAX(f.job_posted_date)) + 1 AS active_days_range,
    ROUND(AVG(f.salary_avg_million), 1) AS avg_salary_offered,
    COUNT(DISTINCT f.job_title) AS unique_job_titles,
    ARRAY_JOIN(ARRAY_AGG(DISTINCT f.work_model_normalized), ', ') AS work_models_offered
FROM {{ ref('dim_company') }} c
LEFT JOIN {{ ref('fct_jobs') }} f
    ON c.company_id = f.company_id
GROUP BY c.company_id, c.company_name, c.source_platform, c.logo_id
