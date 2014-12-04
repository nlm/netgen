{%- for zone in zones -%}
##################################################
Zone {{ zone.name }} vrf {{ zone.vrf }}
##################################################
{%- for subnet in zone.subnets %}
Subnet {{ subnet.name }} is {{ subnet.network }}
{%- for host in subnet.hosts %}
  {{ host.name }} has address {{ host.address }}
{%- endfor %}
{%- endfor %}
{%- endfor %}
