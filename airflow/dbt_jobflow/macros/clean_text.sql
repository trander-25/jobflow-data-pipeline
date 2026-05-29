{% macro lower_and_trim(column_name) %}
    lower(trim({{ column_name }}))
{% endmacro %}

{% macro initcap_and_trim(column_name) %}
    regexp_replace(lower(trim({{ column_name }})), '\b(\w)', x -> UPPER(x[1]))
{% endmacro %}

{% macro upper_and_trim(column_name) %}
    upper(trim({{ column_name }}))
{% endmacro %}
