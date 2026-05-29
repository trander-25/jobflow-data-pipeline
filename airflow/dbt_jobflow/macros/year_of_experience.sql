{% macro extract_experience(description_col) %}

CASE
    WHEN regexp_like({{ description_col }},
        '(?i)(tối thiểu|ít nhất|từ|from)?\s*\d+\s*(-|–|đến|to)\s*\d+\+?\s*(năm|years?)')
    THEN
        regexp_extract(
            {{ description_col }},
            '(?i)(tối thiểu|ít nhất|từ|from)?\s*((\d+)\s*(-|–|đến|to)\s*(\d+\+?))\s*(năm|years?)',
            2
        )

    WHEN regexp_like({{ description_col }},
        '(?i)\d+\s*\+\s*(năm|years|year?)')
    THEN
        regexp_extract(
            {{ description_col }},
            '(?i)((\d+)\s*\+)\s*(năm|years?)',
            1
        )

    WHEN regexp_like({{ description_col }},
        '(?i)(dưới|below|less than)\s*\d+\s*(năm|years?)')
    THEN
        concat(
            regexp_extract(
                {{ description_col }},
                '(?i)(dưới|below|less than)\s*(\d+)\s*(năm|years?)',
                2
            ),
            '-'
        )

    WHEN regexp_like({{ description_col }},
        '(?i)(tối thiểu|ít nhất|trên|at least|minimum)\s*\d+\s*(năm|years?)')
    THEN
        concat(
            regexp_extract(
                {{ description_col }},
                '(?i)(tối thiểu|ít nhất|trên|at least|minimum)\s*(\d+)\s*(năm|years?)',
                2
            ),
            '+'
        )

    WHEN regexp_like({{ description_col }},
        '(?i)\d+\s*(năm|years?)')
    THEN
        regexp_extract(
            {{ description_col }},
            '(?i)(\d+)\s*(năm|years?)',
            1
        )

    ELSE 'Unknown'
END

{% endmacro %}

{% macro yoe_normalized(col) %}

CASE
    WHEN {{ col }} IS NULL THEN NULL
    WHEN lower({{ col }}) = 'unknown' THEN NULL

    WHEN regexp_like(
        regexp_replace(lower({{ col }}), '[–—]', '-'),
        '^[0-9]+$'
    ) THEN CAST({{ col }} AS DOUBLE)

    WHEN regexp_like(lower({{ col }}),'^[0-9]+\+$'
    ) THEN
        CAST(regexp_extract(lower({{ col }}), '^([0-9]+)', 1) AS DOUBLE)

    WHEN regexp_like(
        regexp_replace(lower({{ col }}), '[–—]', '-'),
        '^[0-9]+-$'
    ) THEN
        CAST(
            regexp_extract(
                regexp_replace(lower({{ col }}), '[–—]', '-'),
                '^([0-9]+)',
                1
            ) AS DOUBLE
        ) / 2

    WHEN regexp_like(
        regexp_replace(lower({{ col }}), '[–—]', '-'),
        '^[0-9]+-[0-9]+\+?$'
    ) THEN
        (
            CAST(
                regexp_extract(
                    regexp_replace(lower({{ col }}), '[–—]', '-'),
                    '^([0-9]+)',
                    1
                ) AS DOUBLE
            )
            +
            CAST(
                regexp_extract(
                    regexp_replace(lower({{ col }}), '[–—]', '-'),
                    '-([0-9]+)',
                    1
                ) AS DOUBLE
            )
        ) / 2

    ELSE NULL
END

{% endmacro %}

{% macro yoe_band(yoe_col) %}
CASE
    WHEN {{ yoe_col }} IS NULL THEN 'Unknown'
    WHEN {{ yoe_col }} < 1 THEN '0-1 year'
    WHEN {{ yoe_col }} < 3 THEN '1-3 years'
    WHEN {{ yoe_col }} < 5 THEN '3-5 years'
    WHEN {{ yoe_col }} < 8 THEN '5-8 years'
    ELSE '8+ years'
END
{% endmacro %}

{% macro yoe_level(yoe_col) %}
CASE
    WHEN {{ yoe_col }} IS NULL THEN 'Unknown'
    WHEN {{ yoe_col }} < 1 THEN 'Intern / Fresher'
    WHEN {{ yoe_col }} < 3 THEN 'Junior'
    WHEN {{ yoe_col }} < 5 THEN 'Mid-level'
    WHEN {{ yoe_col }} < 8 THEN 'Senior'
    ELSE 'Lead / Principal'
END
{% endmacro %}
