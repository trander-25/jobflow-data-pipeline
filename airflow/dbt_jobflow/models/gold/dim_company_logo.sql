{{ config(
    materialized='table',
    tags=['gold_layer', 'dimension']
) }}

SELECT DISTINCT
    logo_id,
    logo_path
FROM {{ source('job_raw', 'company_logos') }}
