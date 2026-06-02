{{ config(
    materialized='incremental',
    unique_key='job_id',
    incremental_strategy='merge',
    tags=['vector_db', 'embedding']
) }}

WITH job_content AS (
    SELECT
        job_id,
        MAX(descriptions) AS descriptions,
        MAX(requirements) AS requirements
    FROM {{ ref('int_jobs_unified') }}
    GROUP BY job_id
),

gold_jobs AS (
    SELECT
        f.job_id,
        MAX(f.source_platform) AS source_platform,
        MAX(f.url) AS url,
        MAX(f.job_title) AS job_title,
        MAX(f.company_name) AS company_name,
        ARRAY_JOIN(
            ARRAY_SORT(
                ARRAY_DISTINCT(
                    ARRAY_AGG(f.job_location) FILTER (
                        WHERE f.job_location IS NOT NULL
                            AND TRIM(f.job_location) <> ''
                    )
                )
            ),
            ', '
        ) AS job_locations,
        MAX(f.job_category) AS job_category,
        MAX(f.work_model_normalized) AS work_model_normalized,
        MAX(f.work_arrangement_normalized) AS work_arrangement_normalized,
        MAX(f.year_of_experiences_raw) AS year_of_experiences_raw,
        MAX(f.year_of_experiences_normalized) AS year_of_experiences_normalized,
        MAX(f.year_of_experiences) AS year_of_experiences,
        MAX(f.experiences_level) AS experiences_level,
        MAX(f.salary) AS salary,
        MAX(f.salary_min_million) AS salary_min_million,
        MAX(f.salary_max_million) AS salary_max_million,
        MAX(f.salary_avg_million) AS salary_avg_million,
        MAX(f.salary_band) AS salary_band,
        MAX(f.education_requirement) AS education_requirement,
        MAX(f.tags) AS tags,
        MAX(f.job_posted_date) AS job_posted_date,
        MAX(f.job_posted_timestamp) AS job_posted_timestamp,
        MAX(f.dbt_load_timestamp) AS dbt_load_timestamp,
        MAX(c.descriptions) AS descriptions,
        MAX(c.requirements) AS requirements
    FROM {{ ref('fct_jobs') }} f
    LEFT JOIN job_content c
        ON f.job_id = c.job_id
    {% if is_incremental() %}
    WHERE NOT EXISTS (
        SELECT 1
        FROM {{ this }} existing
        WHERE existing.job_id = f.job_id
    )
    {% endif %}
    GROUP BY f.job_id
)

SELECT
    job_id,
    source_platform,
    url,
    job_title,
    company_name,
    job_locations,
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
    job_posted_date,
    job_posted_timestamp,
    dbt_load_timestamp,
    CONCAT(
        'Job Title: ', COALESCE(job_title, ''), '. ',
        'Company: ', COALESCE(company_name, ''), '. ',
        'Source Platform: ', COALESCE(source_platform, ''), '. ',
        'Location: ', COALESCE(job_locations, ''), '. ',
        'Category: ', COALESCE(job_category, ''), '. ',
        'Experience Level: ', COALESCE(experiences_level, ''), '. ',
        'Years of Experience: ', COALESCE(CAST(year_of_experiences AS VARCHAR), ''), '. ',
        'Work Type: ', COALESCE(work_arrangement_normalized, ''), '. ',
        'Work Model: ', COALESCE(work_model_normalized, ''), '. ',
        'Education: ', COALESCE(education_requirement, ''), '. ',
        'Salary: ', COALESCE(salary, ''), '. ',
        'Salary Band: ', COALESCE(salary_band, ''), '. ',
        'Requirements: ', COALESCE(requirements, ''), '. ',
        'Description: ', COALESCE(descriptions, ''), '. ',
        'Tags: ', COALESCE(tags, '')
    ) AS embedding_text
FROM gold_jobs
WHERE TRIM(COALESCE(job_title, '') || COALESCE(company_name, '') || COALESCE(descriptions, '') || COALESCE(requirements, '')) <> ''
