{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}

    {%- if target.name == 'prod' -%}
        {# Production: use schema name directly (e.g., 'base', 'intermediate', 'mart') #}
        {{ custom_schema_name | trim }}

    {%- else -%}
        {# Dev: prefix with 'dev_' (e.g., 'dev_base', 'dev_intermediate', 'dev_mart') #}
        dev_{{ custom_schema_name | trim }}

    {%- endif -%}
{%- endmacro %}
