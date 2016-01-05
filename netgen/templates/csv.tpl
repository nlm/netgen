{%- for zone in zones -%}
{%- for subnet in zone.subnets %}
{%- if subnet.hosts %}
{%- for host in subnet.hosts %}
{{ host.name }};{{ host.address }};{{ subnet.network.netmask }}
{%- endfor %}
{%- endif %}
{%- endfor %}
{%- endfor %}
