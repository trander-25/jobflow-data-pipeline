{{ config(
    materialized='table',
    schema='reports',
    tags=['report', 'work_model']
) }}

SELECT
    wm.work_model_id,
    wm.work_model_normalized,
    wm.work_model_group,
    wm.work_model_sort_order,
    COUNT(DISTINCT f.url) AS job_count,
    COUNT(DISTINCT f.company_id) AS num_companies,
    COUNT(DISTINCT f.location_id) AS num_locations,
    ROUND(AVG(f.salary_avg_million), 1) AS avg_salary,
    ROUND(COUNT(DISTINCT f.url) * 100.0 / NULLIF((SELECT COUNT(DISTINCT url) FROM {{ ref('fct_jobs') }}), 0), 2) AS pct_of_total_jobs,
    COUNT(DISTINCT f.source_platform) AS num_platforms,
    ROW_NUMBER() OVER (ORDER BY COUNT(DISTINCT f.url) DESC) AS demand_rank,
    ROUND(AVG(AVG(f.salary_avg_million)) OVER (), 1) AS market_avg_salary,
    ROUND(AVG(f.salary_avg_million) - AVG(AVG(f.salary_avg_million)) OVER (), 1) AS salary_vs_market,
    CASE
        WHEN AVG(f.salary_avg_million) > AVG(AVG(f.salary_avg_million)) OVER () THEN 'Above Average'
        WHEN AVG(f.salary_avg_million) < AVG(AVG(f.salary_avg_million)) OVER () THEN 'Below Average'
        ELSE 'At Market'
    END AS salary_positioning
FROM {{ ref('dim_work_model') }} wm
LEFT JOIN {{ ref('fct_jobs') }} f
    ON wm.work_model_id = f.work_model_id
GROUP BY wm.work_model_id, wm.work_model_normalized, wm.work_model_group, wm.work_model_sort_order
