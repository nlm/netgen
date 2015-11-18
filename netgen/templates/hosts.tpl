{%- for zone in zones -%}
{%- for subnet in zone.subnets %}
{%- for host in subnet.hosts %}
{{ host.address }} {{ host.name }}
{%- endfor %}
{%- endfor %}
{%- endfor %}
