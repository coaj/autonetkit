system {
    host-name ${hostname}; 
    root-authentication {
        encrypted-password "$1$SGUyJfYE$r5hIy2IU4IamO1ye3u70v0";
    }                      
    services {
        finger;
        ftp;
        rlogin;
        rsh;
        ssh;
        telnet;
        xnm-clear-text;
    }          
    login {
        message "Welcome to the cloud\npassword is Clouds\nConfiguration generated by AutoNetkit ${ank_version} ";
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
apply-groups [ global member0 ];
system {
    login {
        user admin {
            uid 2000;
            class super-user;
            authentication {
                encrypted-password "$1$gjXXNjz2$lYyNylLyk0ByxPg8aPZyg1";
            }
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
			% if 'net_ent_title' in i:  
			family iso {
				address ${i['net_ent_title']}
			}   
			% elif igp_protocol == 'isis':
			family iso;
			% endif
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
	% if igp_protocol == 'ospf':
	ospf {
	        area 0.0.0.0 {
			% for i in igp_interfaces:
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
	% elif igp_protocol == 'isis':
	isis {               
		level 2 wide-metrics-only;
		level 1 disable;
		% for i in igp_interfaces:   
		% if i['id'].startswith('lo'):
		interface ${i['id']};
		% else:
		interface ${i['id']}  {
			point-to-point;   
			% if 'weight' in i:
			level 2 metric ${i['weight']};
			% endif
		}                        
		% endif
		%endfor    
	}                      
	% endif    
	% if bgp_groups:         
	bgp {                  
		export adverts;
		% for groupname, group_data in bgp_groups.items():   
			group ${groupname} {
				type ${group_data['type']};    
			    local-address ${router_id};
			    % for neighbor in group_data['neighbors']: 
				   % if 'peer_as' in neighbor:      
				   neighbor  ${neighbor['id']} {
						peer-as ${neighbor['peer_as']};
				   }
				   % else:          
				   neighbor  ${neighbor['id']};
				   % endif
				% endfor
			}
		% endfor
	}
	% endif           
}                  

policy-options {
    policy-statement adverts {
        term 1 {
            from protocol [ aggregate direct ];
            then accept;
        }
    }
}