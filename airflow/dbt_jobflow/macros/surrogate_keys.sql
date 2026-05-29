{% macro md5_surrogate_key(expression) %}
    TO_HEX(MD5(TO_UTF8({{ expression }})))
{% endmacro %}

{% macro job_surrogate_key(source_platform, url) %}
    {{ md5_surrogate_key("CONCAT(" ~ source_platform ~ ", '|', " ~ url ~ ")") }}
{% endmacro %}

{% macro company_surrogate_key(source_platform, company_name) %}
    {{ md5_surrogate_key("CONCAT(" ~ source_platform ~ ", '|', " ~ company_name ~ ")") }}
{% endmacro %}

{% macro dimension_surrogate_key(column_name) %}
    {{ md5_surrogate_key(column_name) }}
{% endmacro %}
