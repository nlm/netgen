
{%- for zone in zones %}
The {{ zone.name }}-{{ zone.vrf }} supernet is {{ zone.network }}
  {%- if zone.subnets %}
  {%- for subnet in zone.subnets %}
  The {{ subnet.name }} subnet is {{ subnet.network }} in the vlan {{ subnet.vlan|int }} in the vrf {{ zone.vrf }}
  {%- if subnet.hosts %}
  {%- for host in subnet.hosts %}
    Host {{ host.name }} ip is {{ host.address }}/{{ subnet.network.prefixlen }}
  {%- endfor %}
  {%- endif %}
  {%- endfor %}
  {%- endif %}
{%- endfor %}
