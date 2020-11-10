from behave import *
from framework.api import *
import pyjq
import time
import json
import re
from util import *
from common import *
import time
from database import *

use_step_matcher("cfparse")


@when(u'I add Uproxy group')
def step_imp(context):
    assert context.valid_port != None
    group_id = 'uproxy-' + generate_id()
    body = {
        "group_id": group_id,
        "sip": "",
        "port": context.valid_port,
        "is_autocommit": "1",
        "admin_user": "root",
        "admin_password": "QWEASD123",
        "is_sync": True
    }
    api_request_post(context, context.version_3 + "/uproxy/add_group", body)
    context.group_id = group_id


def get_uproxy_installation_file(context):
    return get_installation_file(context, "uproxy-3.19.09.0-el6")


@when(u'I remove the Uproxy router')
def step_imp(context):
    assert context.uproxy_router != None
    api_request_post(
        context, context.version_3 + "/uproxy_router/remove_router", {
            "user": context.uproxy_router['user'],
            "group_id": context.uproxy_router['group_id'],
            "is_sync": True
        })


@then(u'the Uproxy group list {should_or_not:should_or_not} contains the Uproxy group')
def step_impl(context, should_or_not):
    assert context.group_id != None

    resp = get_uproxy_group_list_by_group_id(context, context.group_id)
    assert (len(resp) != 0 and should_or_not) or (len(resp) == 0 and
                                                  not should_or_not)


@when(u'I found a Uproxy group without Uproxy instance, or I skip the test')
def step_impl(context):
    resp = get_uproxy_group_list(context)
    match = pyjq.first('.[] | select(.uproxy_group_instance_nums == "0") ', resp)
    if match is None:
        context.scenario.skip("found a Uproxy group with Uproxy instance")
    else:
        context.uproxy_group = match


@when(u'I found a server without Uproxy instance')
def step_impl(context):
    resp = get_all_server_info(context)
    for server in pyjq.all('.[]', resp):
        res = get_uproxy_instance_list(context)
        match = pyjq.first(
            '.[] | select(.server_id == "{0}")'.format(server['server_id']),
            res)
        if match is None:
            context.server = server
            return
    assert False


@then(
    u'the Uproxy group should have {expect_count:int} running Uproxy instance in {duration:time}'
)
def step_impl(context, expect_count, duration):
    assert context.uproxy_id != None
    assert context.uproxy_group != None
    group_id = context.uproxy_group['uproxy_group_id']

    def condition(context, flag):
        resp = get_uproxy_instance_list_by_group_id(context, group_id)
        if len(resp) == expect_count:
            condition = '.[] | select(."uproxy_instance_status" == "STATUS_OK" and .uproxy_instance_role=="master")'
            match = pyjq.first(condition, resp)
            if match is not None:
                return True

    waitfor(context, condition, duration)


@when(u'I add Uproxy instance')
def step_imp(context):
    assert context.server != None
    assert context.uproxy_group != None
    uproxy_id = "uproxy-" + generate_id()
    install_file = get_uproxy_installation_file(context)
    body = {
        "server_id": context.server['server_id'],
        "group_id": context.uproxy_group['uproxy_group_id'],
        "port": context.uproxy_group["uproxy_group_port"],
        "smp": "1",
        "uproxy_id": uproxy_id,
        "uproxy_path": context.component_installation_dir + "uproxy",
        "uproxy_glibc_install_file": "uproxy-glibc-2.17-el6.x86_64.rpm",
        "uproxy_install_file": install_file,
        "is_sync": True
    }
    api_request_post(context, context.version_3 + "/uproxy/add_instance", body)
    context.uproxy_id = uproxy_id


@when(
    u'I found {count:int} Uproxy group with Uproxy instance, or I skip the test'
)
def step_impl(context, count):
    resp = get_uproxy_group_list(context)
    match = pyjq.first('.[] | select(.uproxy_group_instance_nums > 0)', resp)
    if match is None:
        context.scenario.skip("Found no Uproxy group with Uproxy instance")
    else:
        context.uproxy_group = match


@when(u'I add Uproxy router')
def step_imp(context):
    assert context.uproxy_group != None
    body = {
        "group_id": context.uproxy_group['uproxy_group_id'],
        "max_frontend_connect_num": "256",
        "user": "test",
        "password": "test",
        "is_rws_enable": "true",
        "is_sync": True
    }
    api_request_post(context, context.version_3 + "/uproxy_router/add_router", body)


@then(
    u'the Uproxy router list {should_or_not:should_or_not} contains the Uproxy router'
)
def step_impl(context, should_or_not):
    assert context.uproxy_group != None

    resp = get_uproxy_router_list_by_group_id(context, context.uproxy_group["uproxy_group_id"])
    assert (len(resp) != 0 and should_or_not) or (len(resp) == 0 and
                                                  not should_or_not)


@when(u'I found {count:int} Uproxy router, or I skip the test')
def step_impl(context, count):
    resp = get_uproxy_router_list(context)
    match = pyjq.first('.[]', resp)
    if match is None:
        context.scenario.skip("Found no Uproxy router with Uproxy router")
    else:
        context.uproxy_group = match


@when(u'I add Uproxy router backend')
def step_imp(context):
    assert context.uproxy_group != None
    assert context.mysql_group != None
    router_user = "test"
    resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    master = pyjq.first('.[]|select(."mysql_instance_role" == "STATUS_MYSQL_MASTER")',
                        resp)
    slave = pyjq.first('.[]|select(."mysql_instance_role" == "STATUS_MYSQL_SLAVE")', resp)
    assert master is not None
    assert slave is not None
    addrs = "{0},{1}".format(master['server_address'], slave['server_address'])
    ports = "{0},{1}".format(master['mysql_instance_port'], slave['mysql_instance_port'])
    mysql_ids = "{0},{1}".format(master['mysql_instance_id'], slave['mysql_instance_id'])
    master["root_password"] = get_mysql_instance_root_password(
        context, master["mysql_instance_id"])
    mysql = master
    api_request_post(
        context, context.version_3 + "/database/create_mysql_user", {
            "group_id": mysql['mysql_group_id'],
            "admin_user": "root",
            "admin_password": master["root_password"],
            "mysql_connect_type": "socket",
            "master_instance": mysql['mysql_instance_id'],
            "user": router_user,
            "user_host": "%",
            "password": "test",
            "grants": "all privileges on *.*",
            "is_sync": True
        })
    body = {
        "group_id": context.uproxy_group['group_id'],
        "user": router_user,
        "is_takeover": "true",
        "mysql_group_id": context.mysql_group[0]["mysql_group_id"],
        "mysql_ids": mysql_ids,
        "addrs": addrs,
        "ports": ports,
        "mbconnlimits": ",",
        "master_slaves": "STATUS_MYSQL_MASTER,STATUS_MYSQL_SLAVE",
        "is_sync": True
    }
    api_request_post(context, context.version_3 + "/uproxy_router/add_backend", body)


@then(
    u'the Uproxy router backend list should contains the backend'
)
def step_imp(context):
    assert context.uproxy_group != None
    assert context.mysql_group != None
    resp = get_uproxy_router_backend_list(context, context.uproxy_group["group_id"], "test")
    assert len(resp) != 0


@when(
    u'I found {count:int} Uproxy router without backend instance, or I skip the test'
)
def step_impl(context, count):
    resp = get_uproxy_router_list(context)
    match = pyjq.first('.[]|select(."instance_num" == "0")', resp)
    if match is None:
        context.scenario.skip("Found no Uproxy router with Uproxy router")
    else:
        context.uproxy_router = match


@then(u'Uproxy router should not contains the Uproxy router in {duration:time}')
def step_imp(context, duration):
    assert context.uproxy_router != None

    def condition(context, flag):
        resp = get_uproxy_router_list_by_group_id(context, context.uproxy_router["group_id"])
        if len(resp) == 0:
            return True

    waitfor(context, condition, duration)


@when(u'I remove the Uproxy group')
def step_impl(context):
    assert context.uproxy_group != None
    api_request_post(context, context.version_3 + "/uproxy/remove_group", {
        "group_id": context.uproxy_group['uproxy_group_id'],
        "is_sync": True,
    })
    context.group_id = context.uproxy_group['uproxy_group_id']


@when(u'I found a Uproxy router with backend instance,or I skip the test')
def step_impl(context):
    resp = get_uproxy_router_list(context)
    match = pyjq.first('.[]|select(.instance_num != "0")', resp)
    if match is None:
        context.scenario.skip("Found no Uproxy router with backend instance")
        return
    context.uproxy_router = match


@when(u'I remove all backend instance')
def step_impl(context):
    assert context.uproxy_router is not None
    resp = get_uproxy_router_backend_list(context, context.uproxy_router["group_id"], context.uproxy_router["user"])
    assert len(resp) > 0
    for instance in resp:
        api_request_post(context, context.version_3 + "/uproxy_router/remove_backend", {
            "group_id": context.uproxy_router["group_id"],
            "user": context.uproxy_router["user"],
            "mysqld_addr": instance["mysqld_addr"]
        })


@then(u'the Uproxy router should not contains any backend instance in {duration:time}')
def step_impl(context, duration):
    assert context.uproxy_router is not None

    def condition(context, flag):
        resp = get_uproxy_router_backend_list(context, context.uproxy_router["group_id"], context.uproxy_router["user"])
        if len(resp) == 0:
            return True

    waitfor(context, condition, duration)


@when(u'I remove all Uproxy instance')
def step_impl(context):
    assert context.uproxy_group is not None
    resp = get_uproxy_instance_list_by_group_id(context, context.uproxy_group["uproxy_group_id"])
    for instance in resp:
        api_request_post(context, context.version_3 + "/uproxy/remove_instance", {
            "uproxy_id": instance["uproxy_instance_id"]
        })


@then(u'the Uproxy group should not contains any Uproxy instance in {duration:time}')
def step_impl(context, duration):
    assert context.uproxy_group is not None

    def condition(context, flag):
        resp = get_uproxy_instance_list_by_group_id(context, context.uproxy_group["uproxy_group_id"])
        if len(resp) == 0:
            return True

    waitfor(context, condition, duration)


@when(u'I get uproxy_backend list, page size is {page_size:int}, page index is {page_index:int}')
def step_impl(context, page_size, page_index):
    assert context.uproxy_router is not None
    resp = api_request_get(context, context.version_5 + "/uproxy/router/backend/list", {
        "filter_uproxy_group_id": context.uproxy_router["group_id"],
        "filter_uproxy_router_user": context.uproxy_router["user"],
        "page_size": page_size,
        "page_index": page_index,
    })
    res = json.loads(resp.text)
    if page_index * page_size > res["total_nums"]:
        context.scenario.skip("Current page_index is out of range")
        return
    match = pyjq.all('.data[]|select(.mysql_group_id=="{0}")'.format(context.uproxy_router["group_id"]), res)
    context.datalist = match


@when(u'I get uproxy_pool list, page size is {page_size:int}, page index is {page_index:int}')
def step_impl(context, page_size, page_index):
    assert context.uproxy_router is not None
    resp = api_request_get(context, context.version_5 + "/uproxy/pool/list", {
        "filter_uproxy_group_id": context.uproxy_router["group_id"],
        "page_size": page_size,
        "page_index": page_index,
    })
    res = json.loads(resp.text)
    if page_index * page_size > res["total_nums"]:
        context.scenario.skip("Current page_index is out of range")
        return
    match = pyjq.all('.data[]|select(.group_id=="{0}")'.format(context.uproxy_router["group_id"]), res)
    context.datalist = match


@when(u'I get uproxy_statistic list, page size is {page_size:int}, page index is {page_index:int}')
def step_impl(context, page_size, page_index):
    assert context.uproxy_router is not None
    resp = api_request_get(context, context.version_4 + "/uproxy_pool/list_statistics", {
        "group_id": context.uproxy_router["group_id"],
        "page_size": page_size,
        "page_index": page_index,
    })
    res = json.loads(resp.text)
    if page_index * page_size > res["total_nums"]:
        context.scenario.skip("Current page_index is out of range")
        return
    match = pyjq.all('.data[]|select(.group_id=="{0}")'.format(context.uproxy_router["group_id"]), res)
    context.datalist = match


@then(u'the list should not None')
def step_impl(context):
    assert context.datalist is not None
