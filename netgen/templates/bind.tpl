{%- set dns_domain = params.get('dns_domain', '') %}
{%- for zone in zones -%}
; Zone {{ zone.name }} vrf {{ zone.vrf }}
{%- for subnet in zone.subnets %}
; Subnet {{ zone.name }}{{ subnet.name }}
{%- for host in subnet.hosts %}
{{ host.name }}{{ dns_domain }} IN A {{ host.address }}
{%- endfor %}
{%- endfor %}
{%- endfor %}
