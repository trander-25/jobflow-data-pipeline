{{ config(
    materialized='table',
    tags=['gold_layer', 'fact']
) }}

SELECT
    job_id,
    {{ dimension_surrogate_key('job_category') }} AS job_category_id,
    {{ company_surrogate_key('source_platform', 'company_name') }} AS company_id,
    {{ dimension_surrogate_key('work_model_normalized') }} AS work_model_id,
    {{ dimension_surrogate_key('job_location') }} AS location_id,
    {{ dimension_surrogate_key('education_requirement') }} AS education_id,
    {{ dimension_surrogate_key('salary_band') }} AS salary_band_id,
    source_platform,
    url,
    logo_id,
    job_title,
    company_name,
    job_location,
    job_category,
    work_model_normalized,
    work_arrangement_normalized,
    year_of_experiences_raw,
    year_of_experiences_normalized,
    year_of_experiences,
    experiences_level,
    salary,
    salary_min_million,
    salary_max_million,
    salary_avg_million,
    salary_band,
    education_requirement,
    tags,
    posted_to_discord,
    job_posted_date,
    job_posted_timestamp,
    dbt_load_timestamp
FROM {{ ref('int_jobs_unified') }}
WHERE job_category IS NOT NULL
    AND job_category != 'Others'
