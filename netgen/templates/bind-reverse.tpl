{%- for zone in zones -%}
; Zone {{ zone.name }} vrf {{ zone.vrf }}
{%- for subnet in zone.subnets %}
; Subnet {{ zone.name }}{{ subnet.name }}
{%- for host in subnet.hosts %}
{{ host.address.reverse_pointer }}. IN PTR {{ host.name }}.pv.ocshq.com.
{%- endfor %}
{%- endfor %}
{%- endfor %}
