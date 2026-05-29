{{ config(
    materialized='table',
    tags=['gold_layer', 'dimension'],
    indexes=[
        {'columns': ['company_id'], 'type': 'btree'}
    ]
) }}

SELECT
    company_id,
    company_name,
    source_platform,
    logo_id,
    CAST(CURRENT_TIMESTAMP AS TIMESTAMP) AS dbt_load_timestamp
FROM (
    SELECT
        {{ company_surrogate_key('source_platform', 'company_name') }} AS company_id,
        company_name,
        source_platform,
        logo_id,
        ROW_NUMBER() OVER (
            PARTITION BY source_platform, company_name
            ORDER BY job_posted_timestamp DESC
        ) AS row_num
    FROM {{ ref('int_jobs_unified') }}
    WHERE company_name IS NOT NULL
        AND job_category IS NOT NULL
        AND job_category != 'Others'
) companies
WHERE row_num = 1
