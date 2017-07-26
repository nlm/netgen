
{%- for zone in zones %}
The {{ (zone.name + '-' + zone.vrf)|colored('blue', style='bold') }} supernet is {{ zone.network|colored('yellow') }}
  {%- if zone.subnets %}
  {%- for subnet in zone.subnets %}
  The {{ subnet.name|colored('green', style='bold') }} subnet is {{ subnet.network|colored('yellow') }} in the vlan {{ subnet.vlan|int|colored('red') }} in the vrf {{ zone.vrf|colored('cyan') }}
  {%- if subnet.hosts %}
  {%- for host in subnet.hosts %}
    Host {{ host.name|colored('magenta') }} ip is {{ host.address }}{{ ('/' + subnet.network.prefixlen|string)|colored('grey') }}
  {%- endfor %}
  {%- endif %}
  {%- endfor %}
  {%- endif %}
{%- endfor %}
