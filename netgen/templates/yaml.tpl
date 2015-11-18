{%- for zone in zones %}
- "zone": "{{ "%s"|format(zone.name) }}"
  "vrf": "{{ "%s"|format(zone.vrf) }}"
  "ipv": {{ "%d"|format(ipv) }}
  {%- if zone.subnets %}
  "subnets":
    {%- for subnet in zone.subnets %}
    - "name": "{{ subnet.name }}"
      "network": "{{ "%s"|format(subnet.network) }}"
      "address": "{{ "%s"|format(subnet.network.network_address) }}"
      "prefixlen": {{ "%d"|format(subnet.network.prefixlen) }}
      "netmask": "{{ "%s"|format(subnet.network.netmask) }}"
      {%- if subnet.vlan %}
      "vlan": {{ "%d"|format(subnet.vlan) }}
      {%- endif %}
      {%- if with_hosts %}
      {%- if subnet.hosts %}
      "hosts":
        {%- for host in subnet.hosts %}
        - "name": "{{ host.name }}"
          "address": "{{ "%s"|format(host.address) }}"
          "prefixlen": {{ "%d"|format(subnet.network.prefixlen) }}
          "netmask": "{{ "%s"|format(subnet.network.netmask) }}"
        {%- endfor %}
      {%- endif %}
      {%- endif %}
    {%- endfor %}
  {%- endif %}
{%- endfor %}
