{%- set dns_domain = params.get('dns_domain', '') %}
{%- for zone in zones -%}
; Zone {{ zone.name }} vrf {{ zone.vrf }}
{%- for subnet in zone.subnets %}
; Subnet {{ subnet.name }}
{%- for host in subnet.hosts %}
{{ host.address.reverse_pointer }}. IN PTR {{ host.name }}{{ dns_domain }}
{%- endfor %}
{%- endfor %}
{%- endfor %}
