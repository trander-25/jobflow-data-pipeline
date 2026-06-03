{%macro location_normalization(column_name) %}
    trim(
        replace(
            replace(
                lower({{ column_name }}),
                '(mới)',
            ''),
            '&',
        '-')
    )
{%endmacro %}
