{%- for zone in zones -%}
; Zone {{ zone.name }} vrf {{ zone.vrf }}
{%- for subnet in zone.subnets %}
; Subnet {{ zone.name }}{{ subnet.name }}
{%- for host in subnet.hosts %}
{{ host.name }}.pv.ocshq.com. IN A {{ host.address }}
{%- endfor %}
{%- endfor %}
{%- endfor %}
