{%- for zone in zones %}
- "zone": "{{ "%s"|format(zone.name) }}"
  "vrf": "{{ "%s"|format(zone.vrf) }}"
  "network": "{{ "%s"|format(zone.network) }}"
  "address": "{{ "%s"|format(zone.network.network_address) }}"
  "prefixlen": {{ "%d"|format(zone.network.prefixlen) }}
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
      "status": "{{ "%s"|format(subnet.status) }}"
      {%- if subnet.hosts %}
      "hosts":
        {%- for host in subnet.hosts %}
        - "name": "{{ host.name }}"
          "address": "{{ "%s"|format(host.address) }}"
          "prefixlen": {{ "%d"|format(subnet.network.prefixlen) }}
          "netmask": "{{ "%s"|format(subnet.network.netmask) }}"
          "status": "{{ "%s"|format(host.status) }}"
        {%- endfor %}
      {%- endif %}
    {%- endfor %}
  {%- endif %}
{%- endfor %}
