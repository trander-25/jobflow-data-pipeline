{{ config(
    materialized='table',
    tags=['silver_layer', 'intermediate', 'unified']
) }}

WITH source_jobs AS (
    SELECT * FROM {{ ref('int_topcv_jobs') }}
    UNION ALL
    SELECT * FROM {{ ref('int_itviec_jobs') }}
),

exploded_locations AS (
    SELECT
        source_platform,
        url,
        logo_url,
        title,
        company,
        work_model,
        work_arrangement,
        job_category,
        salary,
        salary_min_million,
        salary_max_million,
        education_requirement,
        descriptions,
        requirements,
        year_of_experiences,
        tags,
        posted_to_discord,
        job_posted_date,
        job_posted_timestamp,
        trim(location_value) AS working_location
    FROM source_jobs
    CROSS JOIN UNNEST(SPLIT(working_location, '-')) AS t(location_value)
    WHERE location_value NOT LIKE '%nÆ¡i khÃ¡c%'
),

standardized AS (
    SELECT
        {{ job_surrogate_key('exploded_locations.source_platform', 'exploded_locations.url') }} AS job_id,
        exploded_locations.source_platform,
        exploded_locations.url,
        cl.logo_id,
        exploded_locations.title AS job_title,
        exploded_locations.company AS company_name,
        TRIM(vcm.city_en) AS job_location,
        exploded_locations.job_category,
        CASE
            WHEN LOWER(TRIM(exploded_locations.work_model)) IN ('hybrid', 'lai') THEN 'Hybrid'
            WHEN LOWER(TRIM(exploded_locations.work_model)) IN ('remote', 'tá»« xa') THEN 'Remote'
            WHEN LOWER(TRIM(exploded_locations.work_model)) IN ('at office', 'táº¡i vÄƒn phÃ²ng', 'on-site', 'on site') THEN 'On-Site'
            ELSE TRIM(exploded_locations.work_model)
        END AS work_model_normalized,
        CASE
            WHEN LOWER(TRIM(exploded_locations.work_arrangement)) IN ('toÃ n thá»i gian', 'full-time', 'full time', 'fulltime') THEN 'Full-time'
            WHEN LOWER(TRIM(exploded_locations.work_arrangement)) IN ('bÃ¡n thá»i gian', 'part-time', 'part time') THEN 'Part-time'
            WHEN LOWER(TRIM(exploded_locations.work_arrangement)) IN ('thá»±c táº­p', 'internship', 'intern') THEN 'Internship'
            ELSE TRIM(exploded_locations.work_arrangement)
        END AS work_arrangement_normalized,
        exploded_locations.salary,
        exploded_locations.salary_min_million,
        exploded_locations.salary_max_million,
        {{ salary_value('exploded_locations.salary_min_million', 'exploded_locations.salary_max_million') }} AS salary_avg_million,
        {{ salary_bench(salary_value('exploded_locations.salary_min_million', 'exploded_locations.salary_max_million')) }} AS salary_band,
        exploded_locations.education_requirement,
        exploded_locations.descriptions,
        exploded_locations.requirements,
        exploded_locations.year_of_experiences AS year_of_experiences_raw,
        {{ yoe_normalized('exploded_locations.year_of_experiences') }} AS year_of_experiences_normalized,
        {{ yoe_band(yoe_normalized('exploded_locations.year_of_experiences')) }} AS year_of_experiences,
        {{ yoe_level(yoe_normalized('exploded_locations.year_of_experiences')) }} AS experiences_level,
        exploded_locations.tags,
        exploded_locations.posted_to_discord,
        exploded_locations.job_posted_date,
        exploded_locations.job_posted_timestamp,
        CAST(CURRENT_TIMESTAMP AS TIMESTAMP) AS dbt_load_timestamp
    FROM exploded_locations
    LEFT JOIN {{ ref('vn_city_mapping') }} vcm
        ON REGEXP_LIKE(exploded_locations.working_location, vcm.pattern)
    LEFT JOIN {{ source('job_raw', 'company_logos') }} cl
        ON exploded_locations.logo_url = cl.logo_url
)

SELECT *
FROM standardized
