{{ config(
    materialized='table',
    schema='reports',
    tags=['report', 'education']
) }}

SELECT
    e.education_id,
    e.education_requirement,
    e.education_sort_order,
    COUNT(f.job_id) AS job_count,
    COUNT(DISTINCT f.company_id) AS num_companies,
    COUNT(DISTINCT f.location_id) AS num_locations,
    ROUND(AVG(f.salary_avg_million), 1) AS avg_salary,
    ROUND(100.0 * COUNT(f.job_id) / NULLIF((SELECT COUNT(*) FROM {{ ref('fct_jobs') }}), 0), 2) AS pct_of_total_jobs,
    ARRAY_JOIN(ARRAY_AGG(DISTINCT f.source_platform), ', ') AS source_platforms,
    ROW_NUMBER() OVER (ORDER BY COUNT(f.job_id) DESC) AS demand_rank,
    ROUND(AVG(AVG(f.salary_avg_million)) OVER (), 1) AS market_avg_salary,
    ROUND(AVG(f.salary_avg_million) - AVG(AVG(f.salary_avg_million)) OVER (), 1) AS salary_vs_market
FROM {{ ref('dim_education') }} e
LEFT JOIN {{ ref('fct_jobs') }} f
    ON e.education_id = f.education_id
GROUP BY e.education_id, e.education_requirement, e.education_sort_order
