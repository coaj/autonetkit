${qemu}
-hda ${rpki_server_info.img_image} 
-hdb ${rpki_server_info.iso_image}         
	% for mac in rpki_server_info.mac_addresses: 
-net nic,macaddr=${mac},model=e1000 
	% endfor
-net vde,sock=${rpki_server_info.switch_socket} 
-enable-kvm 
-serial telnet:127.0.0.1:${rpki_server_info.telnet_port},server,nowait,nodelay 
-monitor unix:${rpki_server_info.monitor_socket},server,nowait 
-m 512 m  
-nographic 
-localtime 
${seabios}
-name ${rpki_server_info.router_name} &
