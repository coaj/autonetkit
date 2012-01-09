"""
.. module:: AutoNetkit.autonetkit

.. moduleauthor:: Simon Knight

Main functions for AutoNetkit

"""
import pprint   
import AutoNetkit as ank
import cPickle as pickle
from itertools import groupby
from AutoNetkit import deprecated 
from collections import namedtuple

# NetworkX Modules
import networkx as nx   
pp = pprint.PrettyPrinter(indent=4)       

# AutoNetkit Modules
import logging
LOG = logging.getLogger("ANK")

#TODO: update docstrings now not returning graphs as using self.graph

"""TODO: use for fast node access, eg can do self.ank[n]['asn']
        #Return a dict of neighbors of node n.  Use the expression 'G[n]'. 
        def __getitem__(self, n):

also look at
    def __iter__(self):

and 
    def __contains__(self,n):

to pass through to the netx graph methods for quick access

"""

#TODO: allow direct access to the graph where possible,
# function G is reference to the graph
# with all other methods only for access subgraphs etc
# and for getting graphs by properties

# TODO: abstract eBGP etc to be subgraph by property,
# with eBGP just being split on the 'asn' property

node_namedtuple = namedtuple('node', "id, network")
link_namedtuple = namedtuple('link', "id, subnet, reject")


class Network(object): 
    """ Main network containing router graph"""

    def __init__(self, physical_graph=None):
        # IP config information
        #TODO: make this a general attributes dictionary
        self.tap_host = None
        self.tap_sn = None
        self.ip_as_allocs = None

        self.as_names = {}
        self._graphs = {}
        self._graphs['physical'] = nx.DiGraph()
        if physical_graph:
            self._graphs['physical'] = physical_graph
        self._graphs['bgp_session'] = nx.DiGraph()
        self._graphs['dns'] = nx.DiGraph()
        self.compiled_labs = {} # Record compiled lab filenames, and configs

    @deprecated
    def update_node_type(self, default_type):
        """ Updates any node in graph that has no type set to be default_type"""
        for node, data in self.graph.nodes(data=True):
            if 'type' not in data: 
                self.graph.node[node]['type'] = default_type

    # store network reference in node

#TODO: add add_device function, which auto relabels with network reference
    def instantiate_nodes(self):
        #mapping = dict( node_namedtuple(n, self) for n in self.graph)
        mapping = dict( (n, node_namedtuple(n, self)) for n in self.graph)
        nx.relabel_nodes(self.graph, mapping, copy=False)

    def add_device(self, node_id, asn=None, device_type=None, **kwargs):
        """ Adds a device to the physical graph"""
#TODO: keep internal counter of number of nodes that should be present, and compare in verification step - ie if user has added their own, possible corruption
        if not asn:
            asn = 1
#TODO: set this to debug once finished with
            LOG.info("Setting default asn=1 for added device %s" % node_id)
        if not device_type:
            device_type = 1
#TODO: set this to debug once finished with
            LOG.info("Setting default device_type='router' for added device %s" % node_id)
        node = node_namedtuple(node_id, self)
        self.graph.add_node(node, asn=asn, device_type=device_type, **kwargs)
        print "added device", self.graph.node[node]
# Return name for reference
        return node

    ################################################## 
    #### Initial Public API functions ###
    # these are used by plugins

    # or write functional library like in networkx function.py file

    #TODO: deprecate these in future, allow for .physical_graph property
    @property
    def graph(self):
        return self._graphs['physical']

    @graph.setter
    def graph(self, value):
        self._graphs['physical'] = value

    @property
    def g_session(self):
        return self._graphs['bgp_session']

    @g_session.setter
    def g_session(self, value):
        self._graphs['bgp_session'] = value

    @property
    def g_dns(self):
        return self._graphs['dns']

    @g_dns.setter
    def g_dns(self, value):
        self._graphs['dns'] = value

    @deprecated
    def get_edges(self, node=None):
        if node != None:
            # Can't use shortcut of "if node" as param node=0 would 
            # evaluate to same as None
            return self.graph.edges(node)
        else:
            return self.graph.edges()

    @deprecated
    def get_edge_count(self, node):
        return self.graph.degree(node)

    @deprecated
    def get_nodes_by_property(self, prop, value):
        return [n for n in self.graph
                if self.graph.node[n].get(prop) == value]

    def __getitem__(self, n):
        return self.graph.node.get(n)

    def edge(self, src, dst):
        return self.graph[src][dst]

    def q(self, nodes=None, **kwargs):
        if not nodes:
            nodes = self.graph.nodes_iter() # All nodes in graph

        # need to allow filter_func to access these args
        myargs = kwargs
        # also need to handle speed__gt=50 etc
        def ff(n):
            return all(self.graph.node[n].get(k) == v for k,v in
                            myargs.items())

        return (n for n in nodes if ff(n))

    def u(self, nodes, **kwargs):
        for n in nodes:
            for key, val in kwargs.items():
                self.graph.node[n][key] = val

    def groupby(self, attribute, nodes=None):
        if not nodes:
            nodes = self.graph.nodes_iter() # All nodes in graph

        def keyfunc(node):
            return self.graph.node[node][attribute]
        nodes = sorted(nodes, key=keyfunc )
        return groupby(nodes, keyfunc)
        
    def set_default_node_property(self, prop, value):
        for node, data in self.graph.nodes(data=True):
            if prop not in data:
                self.graph.node[node][prop] = value


    @deprecated
    def set_default_edge_property(self, prop, value):
        #TODO: allow list of edges to be passed in
        # sets property if not already set
        for src, dst, data in self.graph.edges(data=True):
            if prop not in data:
                self.graph[src][dst][prop] = value

    @deprecated
    def set_edge_property(self, src, dst, prop, value):
        self.graph[src][dst][prop] = value

    @deprecated
    def get_subgraph(self, nodes):
        return self.graph.subgraph(nodes)

    def devices(self, asn=None):
        """return devices in a network"""
        if asn:
            return (n for n in self.graph if self.asn(n) == asn)
        else:
# return all nodes
            return self.graph.nodes_iter()


    def device_type(self, node):
        return self.graph.node[node].get("device_type")

    def routers(self, asn=None):
        """return routers in network"""
        return (n for n in self.devices(asn) if self.device_type(n) == 'router')

    def servers(self, asn=None):
        """return servers in network"""
        return (n for n in self.devices(asn) if self.device_type(n) == 'server')


    ################################################## 
    #TODO: move these into a nodes shortcut module
    def asn(self, node):
        """ syntactic sugar for accessing asn of a node

        >>> network = ank.example_multi_as()
        >>> network.asn('1a')
        1
        >>> network.asn('2a')
        2
        >>> network.asn('3a')
        3
        
        """
        return int(self.graph.node[node].get('asn'))

    def lo_ip(self, node):
        """ syntactic sugar for accessing loopback IP of a node """
        return self.graph.node[node].get('lo_ip')

    def pop(self, node):
        """ syntactic sugar for accessing pop of a node """
        return self.graph.node[node].get('pop')

    def network(self, node):
        """ syntactic sugar for accessing network of a node """
        retval = self.graph.node[node].get('network')
        if retval:
            return retval
        else:
# try "Network"
            return self.graph.node[node].get('Network')

    def ibgp_cluster(self, node):
        """ syntactic sugar for accessing ibgp_cluster of a node """
        return self.graph.node[node].get('ibgp_cluster')

    def ibgp_level(self, node):
        """ syntactic sugar for accessing ibgp_level of a node """
#TODO: catch int cast exception
        return int(self.graph.node[node].get('ibgp_level'))

    def route_reflector(self, node):
        """ syntactic sugar for accessing if a ndoe is a route_reflector"""
        return self.graph.node[node].get('route_reflector')

    def label(self, node):
        """ syntactic sugar for accessing label of a node """
        if node in self.graph:
            label = self.graph.node[node].get('label')
            if label:
                return label
            return str(node.id)
        else:
            return [self.label(n) for n in node]


    def fqdn(self, node):
        """Shortcut to fqdn"""
        return ank.fqdn(self, node)


# edge accessors


    # For dealing with BGP Sessions graphs
#TODO: expand this to work with arbitrary graphs
    def link_weight(self, src, dst):
        return self.graph[src][dst].get("weight")

    def interface_number(self, src, dst):
        return self.graph[src][dst].get("id")

    def int_ip(self, src, dst):
        return self.graph[src][dst].get("ip")

    def link_subnet(self, src, dst):
        return self.graph[src][dst].get("ip")

    def link(e):
        """ Returns a named-tuple for accessing link properties"""

        



