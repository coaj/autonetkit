# -*- coding: utf-8 -*-
"""
Parse RPKI sets from the file

.. warning::

    Work in progress.

"""
__author__ = "\n".join(['Simon Knight','Askar Jaboldinov'])
#    Copyright (C) 2009-2012 by Simon Knight, Hung Nguyen, Askar Jaboldinov

import networkx as nx
import logging
import AutoNetkit as ank
import os
from AutoNetkit import config
LOG = logging.getLogger("ANK")
#TODO: only import from pyparsing what is needed
from pyparsing import Literal, Word, alphas, alphanums, nums, Combine, Group, ZeroOrMore, Suppress, quotedString, removeQuotes, oneOf, Forward, Optional, delimitedList
import pyparsing
from collections import namedtuple
import threading
import time

LOG = logging.getLogger("ANK")

def parse_fail_action(s,loc,expr,err):
    #TODO: make this LOG.debug not info
    LOG.info('Parse error at %s' % s[loc:])
    raise pyparsing.ParseFatalException('Error at %s' % s[loc:])
    return


class RpkiSetsParser:
    """Parser class"""
    def __init__(self, network):
        self.network = network
#        self.user_defined_sets = {}

        attribute_unnamed = Word(alphanums+'_'+".")
        attribute = attribute_unnamed.setResultsName("attribute")
        self.attribute = attribute
        integer_string = Word(nums).setResultsName("value").setParseAction(lambda t: int(t[0]))
	
	self.nodeQuery = attribute.setResultsName("nodeQuery").setFailAction(parse_fail_action)

        self.children = Literal("children").setResultsName("children") 
        self.relation = self.children.setResultsName("relation").setFailAction(parse_fail_action)

        set_values = Suppress("{") + delimitedList( attribute, delim=',').setResultsName("set_values") + Suppress("}")
        empty_set = Literal("{}").setResultsName("set_values").setParseAction(lambda x: set())

	self.set_definition = ("(" + self.nodeQuery + ")" + self.relation + (empty_set | set_values))
        self.rpkiSetsLine = (self.set_definition.setResultsName("set_definition"))
	self.path = {}


    def apply_rpki_sets(self, qstring):
        LOG.debug("Applying RPKI sets %s" % qstring)
        result = self.rpkiSetsLine.parseString(qstring)
	self.network.g_rpki.add_node(result.nodeQuery)
        if 'set_definition' in result:
            LOG.debug("Storing set definition %s" % result.set_name)
	    for n in result.set_values:
	        self.network.g_rpki.add_node(n)
    	        self.network.g_rpki.add_edge(result.nodeQuery, n, relation = result.relation)

            return


    def apply_rpki_file(self, rpki_in_file):
        """Applies a BGP policy file to the network"""
        LOG.debug("Applying policy file %s" % rpki_in_file)
        rpki_lines = []
        rpki_path = os.path.split(rpki_in_file)[0]
        with open( rpki_in_file, 'r') as f_rpki:
            for line in f_rpki.readlines():
                line = line.strip()
                if line.startswith("#"):
                    LOG.debug("Skipping commented line %s", line)
                    continue
                if line == "":
                    continue
                rpki_lines.append(line)

        for line in rpki_lines:
            line = line.strip()
            if line.startswith("#"):
                LOG.debug("Skipping commented line %s", line)
                continue
            if line == "":
                continue
            try:
                self.apply_rpki_sets(line)
            except pyparsing.ParseFatalException as e:
                LOG.warn("Unable to parse query line %s" % line)


class ChildComposer:
    """recursively search through children dictionary"""
    def __init__(self, node, indent, rpki_tree):
        self.node = node
	self.indent = indent
	self.rpki_tree = rpki_tree
	self.return_str = ""
	self.counter = 1

    def recursive_search(self, target, space):
        iter0 = self.rpki_tree.items()
        for key, value in iter0:
            if str(target) in str(value['fqdn']):
	        if value['children']:
	            iter1 = value['children'].items()
		    for name, data in iter1:
		        self.return_str+=("\n%s- name: %s\n%s  asn: %s\n%s  ipv4: %s\n%s  roa_request:" %(\
		        space*self.counter,\
		        data['fqdn'],\
		        space*self.counter,\
		        data['asn'],\
		        space*self.counter,\
		        data['aggregate'],\
		        space*self.counter\
		        ))
		        for prefix in data['prefixes']:
		            self.return_str += "\n%s    - asn: %s" % (space*self.counter, data['asn'])
		            self.return_str += "\n%s      ipv4: %s" % (space*self.counter, prefix)
		        iter2 = self.rpki_tree.items()
#		        for i, j in iter2:
#		       	    if str(name) in str(i):
#		    	        if j['children']:
#				    self.return_str += "\n%s  kids:" % (space*self.counter)
#				    self.counter += 1
#			            for k in j['children']:
#				        self.recursive_search(k, self.indent*self.counter)
##				        t = threading.Thread(target = self.recursive_search(k, self.indent*self.counter))
##				        t.start()
##					time.sleep(1)
        return (self.return_str)

    def search(self):
        return self.recursive_search(self.node, self.indent)
