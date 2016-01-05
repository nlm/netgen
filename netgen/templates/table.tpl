{%- for zone in zones -%}
{# ,-----------------------------------------------------------------------------, #}
╔═════════════════════════════════════════════════════════════════════════════╗
║ {{ "%-75s"|format('Zone ' + zone.name + ' vrf ' + zone.vrf) }} ║
{%- if zone.subnets %}
{%- for subnet in zone.subnets %}
╟─────────────────────────────────────────────────────────────────────────────╢
║ {{ "%-75s"|format('Subnet ' + subnet.name + ' is ' + subnet.network.__str__() + ' vlan ' + (subnet.vlan or 0).__str__()) }} ║
{%- if subnet.hosts %}
╟─────────────────────────────────────────────────────────────────────────────╢
{%- for host in subnet.hosts %}
║ {{ "%-54s %17s/%-02d"|format(host.name, host.address.__str__(), subnet.network.prefixlen) }} ║
{%- endfor %}
{%- endif %}
{%- endfor %}
{%- endif %}
{%- endfor %}
╚═════════════════════════════════════════════════════════════════════════════╝
