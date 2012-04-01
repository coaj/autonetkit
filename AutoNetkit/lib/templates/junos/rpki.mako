#! /bin/bash
hostname ${hostname}
% for i in sorted(interfaces, key = lambda x: x['id']):
  % if not "lo" in i['id']:
echo -e "auto eth0 \n iface eth0 inet static \n address ${i['ip']} \n netmask ${i['netmask']}" >> /etc/network/interfaces
  % endif
ifup eth0
% endfor
% if len(static_routes):
    % for i in sorted(static_routes, key = lambda x: x['network']):
route add -net ${i['network']}/${i['prefixlen']} gw ${i['ip']};
    % endfor
% endif
