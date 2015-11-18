{%- for zone in zones -%}
{%- for subnet in zone.subnets %}
{%- if with_hosts %}
{%- if subnet.hosts %}
{%- for host in subnet.hosts %}
{{ host.name }};{{ host.address }};{{ subnet.network.netmask }}
{%- endfor %}
{%- endif %}
{%- endif %}
{%- endfor %}
{%- endfor %}
