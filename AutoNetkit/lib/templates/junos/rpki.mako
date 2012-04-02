#! /bin/bash
hostname ${hostname}
% for i in sorted(interfaces, key = lambda x: x['id']):
  % if not "lo" in i['id']:
ifconfig eth0 ${i['ip']}/${i['prefixlen']}
  % endif
% endfor
% if len(static_routes):
    % for i in sorted(static_routes, key = lambda x: x['network']):
route add -net ${i['network']}/${i['prefixlen']} gw ${i['ip']};
    % endfor
% endif
