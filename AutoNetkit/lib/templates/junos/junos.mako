system {
    host-name ${hostname};
    root-authentication {
        encrypted-password "$1$NzaHcpA7$5McU2mGx8OG.hWkTbyDtA1"; ## SECRET-DATA
    }
    services {
        ssh {
            root-login allow;
        }
        telnet;
    }
    syslog {
        user * {
            any emergency;
        }
        file messages {
            any notice;
            authorization info;
        }
        file interactive-commands {
            interactive-commands any;
        }
    }
}

interfaces {
    % for i in interfaces:
    ${i['id']} {
        unit 0 {          
	        description "${i['description']}";
            family inet {      
                address ${i['ip']}/${i['prefixlen']};
            }
        }
    }
    %endfor 
}            

routing-options {
    aggregate {
        route 
		%for n in network_list:  
		${n};
		%endfor  
    }
    router-id ${router_id};
    autonomous-system ${asn};
} 
     
protocols {
	ospf {
	        area 0.0.0.0 {
			% for i in ospf_interfaces:
				  % if 'passive' in i:   
				interface ${i['id']}  {
						passive;   
					}
				% else:
				interface ${i['id']};
			  % endif                
			%endfor
	    }
	}            
	bgp {                  
		export adverts;
		% for groupname, group_data in bgp_groups.items():   
			group ${groupname} {
				type ${group_data['type']};      
				% for neighbor in group_data['neighbors']: 
				   % if 'peer_as' in neighbor:      
				   neighbor  ${neighbor['id']} {
						peer-as ${neighbor['peer_as']};
				   }
				   % else:          
				   local-address ${router_id};
				   neighbor  ${neighbor['id']};
				   % endif
				% endfor
			}
		% endfor
	}           
}                  

policy-options {
    policy-statement adverts {
        term 1 {
            from protocol [ aggregate direct ];
            then accept;
        }
    }
}