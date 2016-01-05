{%- for zone in zones %}
{
  "zone": "{{ "%s"|format(zone.name) }}",
  "vrf": "{{ "%s"|format(zone.vrf) }}",
  {%- if zone.subnets %}
  "subnets": [
    {%- for subnet in zone.subnets %}
    {
      "name": "{{ subnet.name }}",
      "network": "{{ "%s"|format(subnet.network) }}",
      "address": "{{ "%s"|format(subnet.network.network_address) }}",
      "prefixlen": {{ "%d"|format(subnet.network.prefixlen) }},
      "netmask": "{{ "%s"|format(subnet.network.netmask) }}",
      {%- if subnet.hosts %}
      "hosts": [
        {%- for host in subnet.hosts %}
        {
          "name": "{{ host.name }}",
          "address": "{{ "%s"|format(host.address) }}",
          "prefixlen": {{ "%d"|format(subnet.network.prefixlen) }},
          "netmask": "{{ "%s"|format(subnet.network.netmask) }}"
        }{% if not loop.last %},{% endif %}
        {%- endfor %}
      ],
      {%- endif %}
      "vlan": {{ "%d"|format(subnet.vlan or 0) }}
    },
    {%- endfor %}
  ],
  {%- endif %}
  "ipv": "{{ "%d"|format(ipv) }}"
}{% if not loop.last %},{% endif %}
{%- endfor %}
