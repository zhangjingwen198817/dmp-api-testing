from behave import *
from framework.api import *
import pyjq
import time
import json
import re
from util import *
from server import *
import logging
from pprint import pformat
LOGGER = logging.getLogger("steps.prepare")
use_step_matcher("cfparse")


@when(u'I prepare {count:int} agent environment')
def step_imp(context, count):
    for i in range(0, count):
        context.execute_steps(u"""
        When I found a server without components uguard-agent,urman-agent,uguard-mgr, or I skip the test
	    And I prepare the server for uguard
	    Then the response is ok
	    And the server should has components udeploy,ustats,uguard-agent,urman-agent
	    And the server's components udeploy,ustats,uguard-agent,urman-agent should be installed as the standard
		""")


@when(u'I prepare {count:int} mgr environment')
def step_imp(context, count):
    for i in range(0, count):
        context.execute_steps(u"""
        When I found a server without components uguard-mgr,urman-mgr,uguard-agent, or I skip the test
	    And I prepare the server for uguard manager
	    Then the response is ok
	    And the server should has components uguard-mgr,urman-mgr
	    And the server's components uguard-mgr,urman-mgr should be installed as the standard
		""")


@when(u'I prepare {count:int} group MySQL m-ns {sums:int} instances use {port:int} in {groupname:string}')
def step_imp(context, count, sums, port, groupname):
    assert context.server != None
    server_info = context.server
    context.server = random.sample(server_info, count * sums)
    context.execute_steps(u"""
    When I batch install the MySQL m-ns {0}instances use {1} in {2}    
    Then the response is ok
    And the batch MySQL instance list should contains the MySQL instance in 60m
    """.format(sums, port, groupname))


@when(u'I add {count:int} group MySQL m-ns {sums:int} instances use {port:int} in {groupname:string}')
def step_imp(context, count, sums, port, groupname):
    assert context.server != None
    server_info = context.server
    context.server = random.sample(server_info, count * sums)
    context.execute_steps(u"""
    When I batch install the MySQL m-ns {0}instances use {1} in {2}, with specify run user and group    
    Then the response is ok
    And the batch MySQL instance list should contains the MySQL instance in 60m
    """.format(sums, port, groupname))


@when('I prepare {count:int} group 1m2s off-standard MySQL instances')
def step_imp(context, count):
    for i in range(0, count):
        context.execute_steps(u"""
        When I add a MySQL group
        Then the response is ok
        And the MySQL group list should contains the MySQL group

        When I found a MySQL group without MySQL instance, and without SIP, or I skip the test
        And I found a server with components uguard-agent,urman-agent,ustats,udeploy to install MySQL instance, or I skip the test
        And I found a valid port, or I skip the test
        And I add off-standard MySQL instance in the MySQL group
        Then the response is ok
        And the MySQL group should have 1 running MySQL instance in 11s

        When I found a MySQL master in the MySQL group
        And I make a manual backup on the MySQL instance
        Then the response is ok

        When I add off-standard MySQL slave in the MySQL group
        Then the response is ok
        And the MySQL group should have 2 running MySQL instance in 11s

        When I add off-standard MySQL slave in the MySQL group
        Then the response is ok
        And the MySQL group should have 3 running MySQL instance in 11s

        When I enable HA on all MySQL instance in the MySQL group
        Then the response is ok
        And the MySQL group should have 1 running MySQL master and 2 running MySQL slave in 30s 
    		""")
