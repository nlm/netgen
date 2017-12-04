
{%- for zone in zones %}
The {{ (zone.name + '-' + zone.vrf)|colored('blue', style='bold') }} supernet is {{ zone.network|colored('yellow') }}
  {%- if zone.subnets %}
  {%- for subnet in zone.subnets %}
    {%- if subnet.status == 'active' %}
    {%- set flag = '' %}
    {%- elif subnet.status == 'reserved' %}
    {%- set flag = '?' %}
    {%- set color = 'yellow' %}
    {%- elif subnet.status == 'deprecated' %}
    {%- set flag = '!' %}
    {%- set color = 'red' %}
    {%- endif %}
  The {{ flag|colored(color) }}{{ subnet.name|colored('green', style='bold') }} subnet is {{ subnet.network|colored('yellow') }} in the vlan {{ subnet.vlan|int|colored('red') }} in the vrf {{ zone.vrf|colored('cyan') }}
  {%- if subnet.hosts %}
  {%- for host in subnet.hosts %}
    {%- if host.status == 'active' %}
    {%- set flag = '' %}
    {%- set color = 'green' %}
    {%- elif host.status == 'reserved' %}
    {%- set color = 'yellow' %}
    {%- set flag = '?' %}
    {%- elif host.status == 'deprecated' %}
    {%- set flag = '!' %}
    {%- set color = 'red' %}
    {%- endif %}
    Host {{ flag|colored(color) }}{{ host.name|colored('magenta') }} ip is {{ host.address }}{{ ('/' + subnet.network.prefixlen|string)|colored('grey') }}
  {%- endfor %}
  {%- endif %}
  {%- endfor %}
  {%- endif %}
{%- endfor %}
