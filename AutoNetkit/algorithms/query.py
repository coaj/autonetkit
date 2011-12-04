# -*- coding: utf-8 -*-
"""
Query
"""
__author__ = "\n".join(['Simon Knight'])
#    Copyright (C) 2009-2011 by Simon Knight, Hung Nguyen

import networkx as nx
import AutoNetkit as ank
import logging
LOG = logging.getLogger("ANK")
#TODO: only import what is needed
from pyparsing import *
import operator

graph = nx.read_gpickle("condensed_west_europe.pickle")
#print graph.nodes(data=True)

##### parser
# Node selection syntax

attribute = Word(alphas, alphanums+'_').setResultsName("attribute")
#TODO: check how evaluation examples on pyparsing work out which comparison/operator is used

lt = Literal("<").setResultsName("<")
le = Literal("<=").setResultsName("<=")
eq = Literal("=").setResultsName("=")
ne = Literal("!=").setResultsName("!=")
ge = Literal(">=").setResultsName(">=")
gt = Literal(">").setResultsName(">")

opn = {
        '<': operator.lt,
        '<=': operator.le,
        '=': operator.eq,
        '>=': operator.ge,
        '>': operator.gt,
        '&': set.intersection,
        '|': set.union,
        }

# Both are of comparison to access in same manner when evaluating
comparison = (lt | le | eq | ne | ge | gt).setResultsName("comparison")
stringComparison = (eq | ne).setResultsName("comparison")
#
#quoted string is already present
integer = Word(nums).setResultsName("value").setParseAction(lambda t: int(t[0]))

#TODO: allow parentheses? - should be ok as pass to the python parser

boolean_and = Literal("&").setResultsName("&")
boolean_or = Literal("|").setResultsName("|")
boolean = (boolean_and | boolean_or).setResultsName("boolean")

numericQuery = Group(attribute + comparison + integer).setResultsName( "numericQuery")

stringValues = (Word(alphanums) | quotedString.setParseAction(removeQuotes)).setResultsName("value")

stringQuery =  Group(attribute + stringComparison + stringValues).setResultsName( "stringQuery")

singleQuery = numericQuery | stringQuery
queryParser = singleQuery + ZeroOrMore(boolean + singleQuery)

tests = [
        'Network = ACOnet & asn = 1853 & Latitude < 50',
        'Network = ACOnet & Longitude < 14',
        'asn = 680 & label = HAN',
        'Network = GEANT',
        'Network = GEANT & Country = Greece',
        'Network = GEANT & Latitude > 55',
        'Network = GEANT & type = "Fully Featured"',
        ]

def evaluate(stack):
    if len(stack) == 1:
        return set(stack.pop())
    else:
        a = set(stack.pop())
        op = stack.pop()
        return opn[op](a, evaluate(stack))





def query(qstring):
    result = queryParser.parseString(qstring)

#TODO: rearrange so remove stack and iterate over nodes only once
# so execute the boolean as function, rather than using stack on node sets
# ie test each node for all the required matches in one step
# and use data(=True) so get the dictionary reference once -> faster
# especially if using short circuits so when false stop executing

    def comp_fn_string(token, n):
        return opn[token.comparison](graph.node[n].get(token.attribute), token.value)

    def comp_fn_numeric(token, n):
        return opn[token.comparison](float(graph.node[n].get(token.attribute)), token.value)

    stack = []

    for token in result:
        if token in boolean:
            stack.append(token)
            continue

# different function depending on value type: numeric or string

        if isinstance(token.value, str):
            comp_fn = comp_fn_string
        if isinstance(token.value, int):
            comp_fn = comp_fn_numeric
       
        if comp_fn:
            #TODO: change to generator expressions and evaluate as sets in the evaluate function
            result_set = set(n for n in graph if token.attribute in graph.node[n] and comp_fn(token, n) )
            stack.append(result_set)

    final_set = evaluate(stack)
    #print ", ".join(graph.node[n].get('label') for n in final_set)
    return final_set


# can set parse action to be return string?

#TODO: create function from the parsed result
# eg a lambda, and then apply this function to the nodes in the graph
# eg G.node[n].get(attribute) = "quotedstring"  operator 



"""
for test in tests:
    print "--------------------------"
    print test
    print query(test)
    #print result.dump()
"""

set_a =  query('Network = GEANT')     
set_a =  query('Network = ACOnet')     
set_b = query('Network = CESNET')
print set_a
print set_b

node_set = set_a | set_b
print node_set

edges = graph.edges(node_set)
print edges
# 1 ->, 2 <-, 3 <->


def select_fn_u_to_v( (u, v), src_set, dst_set):
    """ u -> v"""
    return (u in src_set and v in dst_set)

def select_fn_u_from_v( (u, v), src_set, dst_set):
    """ u <- v"""
    return (u in dst_set and v in src_set)

def select_fn_v_to_from_u( (u, v), src_set, dst_set):
    """ u <- v"""
    return (u in src_set and v in dst_set) or (u in dst_set and v in src_set)

select_type = 1
if select_type == 1:
    select_function = select_fn_u_to_v
elif select_type == 2:
    select_function = select_fn_u_from_v
elif select_type == 3:
    select_function = select_fn_v_to_from_u 

matching_edges = ( e for e in edges if select_function(e, set_a, set_b))

print list(matching_edges)

