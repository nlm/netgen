{%- for zone in zones -%}
; Zone {{ zone.name }} vrf {{ zone.vrf }}
@ IN SOA ( FIXME )
{%- for subnet in zone.subnets %}
; Subnet {{ zone.name }}{{ subnet.name }}
{%- for host in subnet.hosts %}
{{ host.name }} IN A {{ host.address }}
{%- endfor %}
{%- endfor %}
{%- endfor %}
