from behave import *
from framework.api import *
from framework.api_base import *
import pyjq
import random
import time
import json
import re
import tarfile
from common import *
import logging
from pprint import pformat

LOGGER = logging.getLogger("steps.server")
use_step_matcher("cfparse")


@when("I get servers list")
def step_impl(context):
    api_request_get(context, context.version_5 + "/server/list")


@then(u'the response is a non-empty list')
def step_impl(context):
    resp = api_get_response(context)
    assert resp['total_nums'] > 0
    assert len(resp['data']) > 0


@then(u'the response list columns are not empty: {cols:strings+}')
def step_impl(context, cols):
    resp = api_get_response(context)
    for col in cols:
        has_empty = pyjq.first('.data | any(."{0}" == null)'.format(col), resp)
        assert not has_empty


@then(
    u'the response list has a record whose {col:string} is "{expect_val:string}"'
)
def step_impl(context, col, expect_val):
    resp = api_get_response(context)
    has_match = pyjq.first(
        '.data | any(."{0}" == "{1}")'.format(col, expect_val), resp)
    assert has_match


@when(
    u'I found a server without component{s:s?} {comps:strings+}, or I skip the test'
)
def step_impl(context, s, comps):
    resp = get_all_server_info(context)
    conditions = map(
        lambda comp: 'select(has("{0}_status") | not)'.format(comp), comps)
    condition = '.[] | ' + " | ".join(conditions)
    match = pyjq.first(condition, resp)
    context.server = match

    if match is None:
        context.scenario.skip(
            "Found no server without components {0}".format(comps))


@when(
    u'I found a server with component{s:s?} {comps:strings+}, or I skip the test'
)
def step_impl(context, s, comps):
    resp = get_all_server_info(context)
    conditions = map(lambda comp: 'select(has("{0}_status"))'.format(comp),
                     comps)
    condition = '.[] | ' + " | ".join(conditions)
    match = pyjq.first(condition, resp)
    if match is None:
        context.scenario.skip(
            "Found no server with components {0}".format(comps))
    else:
        context.server = match
        context.server_id = match["server_id"]


@when(
    u'I found a server with component{s:s?} {comps:strings+} to install MySQL instance, or I skip the test'
)
def step_impl(context, s, comps):
    resp = get_all_server_info(context)
    conditions = map(lambda comp: 'select(has("{0}_status"))'.format(comp),
                     comps)
    condition = '.[] | ' + " | ".join(conditions) + "|" + '.server_address'
    servers_address = pyjq.all(condition, resp)

    temp = {}
    for server_address in servers_address:
        resp_count = api_get(context, context.version_3 + "/server/instance/count", {
            "server_ip": server_address,
        })
        temp[server_address] = resp_count
    dict_servers_address = sorted([(v, k) for k, v in temp.items()])
    condition = '.[] |  select(."server_address"=="' + dict_servers_address[0][1] + '")'
    match = pyjq.first(condition, resp)
    if match is None:
        context.scenario.skip(
            "Found no server with components {0}".format(comps))
    else:
        context.server = match


@when(
    u'I found a server with component{s:s?} {comps:strings+}, except {except_servers:strings+}'
)
def step_impl(context, s, comps, except_servers):
    resp = get_all_server_info(context)
    comp_conds = map(lambda comp: 'select(has("{0}_status"))'.format(comp),
                     comps)
    server_conds = map(
        lambda except_server: 'select(.server_id != "{0}")'.format(
            except_server), except_servers)
    condition = '.[] | ' + " | ".join(comp_conds) + " | " + " | ".join(
        server_conds)

    match = pyjq.first(condition, resp)
    assert match is not None
    context.server = match


def get_installation_file(context, comp):
    installation_files = api_get(context, context.version_3 + "/support/component", {
        "pattern": comp,
    })
    assert len(installation_files) > 0
    installation_files = pyjq.all('.[] | .Name', installation_files)
    installation_file = installation_files[-1]
    assert installation_file is not None
    return installation_file


def get_installation_file_by_version(context, comp, version):
    resp = api_get(context, context.version_3 + "/support/component", {
        "pattern": comp,
    })
    assert len(resp) > 0
    dic = readYaml("conf/version_id.yml")
    version_id = dic[version]
    installation_files = pyjq.all('.[] | .Name', resp)
    installation = []
    for installation_file in installation_files:
        if installation_file.find(version_id) != -1:
            installation.append(installation_file)
    assert len(installation) != 0
    return installation[-1]


@when(u'I install a component {comp:string} on the server')
def step_impl(context, comp):
    assert context.server != None
    server_id = context.server["server_id"]

    installation_file = get_installation_file(context, comp)

    api_request_post(
        context, context.version_3 + "/server/install", {
            "server_id": server_id,
            "component": comp,
            comp + "_id": comp + "_" + server_id,
            comp + "_install_file": installation_file,
            comp + "_path": context.component_installation_dir + comp,
            "is_sync": True
        })


@when(u'I install a component {comp:string} on the server in version {version:string} if not installed')
def step_impl(context, comp, version):
    assert context.server is not None
    server_id = context.server["server_id"]
    server_info = get_server_info_by_id(context, server_id)
    key = comp + "_status"
    if key not in server_info:
        installation_file = get_installation_file_by_version(context, comp, version)
        api_post(
            context, context.version_3 + "/server/install", {
                "server_id": server_id,
                "component": comp,
                comp + "_id": comp + "_" + server_id,
                comp + "_install_file": installation_file,
                comp + "_path": context.component_installation_dir + comp,
                "is_sync": True,
            })


@when(u'I uninstall a component {comp:string} on the server')
def step_impl(context, comp):
    assert context.server is not None
    server_id = context.server["server_id"]

    api_request_post(
        context, context.version_3 + "/server/uninstall", {
            "server_id": server_id,
            "component": comp,
            "is_sync": "true"
        })


@when(u'I uninstall a component {comp:string} on the server if exist')
def step_impl(context, comp):
    assert context.server != None
    server_id = context.server["server_id"]
    resp = get_server_info_by_id(context, server_id)
    server_info = pyjq.first('.[]', resp)
    key = comp + "_status"
    if key in server_info:
        api_request_post(
            context, context.version_3 + "/server/uninstall", {
                "server_id": server_id,
                "component": comp,
                "is_sync": "true"
            })


@then(u'the server should has component{s:s?} {comps:strings+}')
def step_impl(context, s, comps):
    assert context.server != None
    server_id = context.server["server_id"]
    resp = get_all_server_info(context)
    conditions = map(lambda comp: 'select(has("{0}_status"))'.format(comp),
                     comps)
    condition = '.[] | select(."server_id" == "{0}") | '.format(
        server_id) + " | ".join(conditions)
    server_has_comp_status = pyjq.first(condition, resp)
    assert server_has_comp_status


@then(u'the server should not has component{s:s?} {comps:strings+}')
def step_impl(context, s, comps):
    server_id = context.server["server_id"]
    resp = get_all_server_info(context)
    conditions = map(lambda comp: 'select(has("{0}_status"))'.format(comp),
                     comps)
    condition = '.[] | select(."server_id" == "{0}") | '.format(
        server_id) + " | ".join(conditions)
    server_has_comp_status = pyjq.first(condition, resp)
    assert not server_has_comp_status


@then(u'the component {comp:string} should run with the pid in pidfile')
def step_impl(context, comp):
    assert context.server != None
    server_id = context.server["server_id"]

    pids = api_get(context, context.version_3 + "/helper/pgrep", {
        "server_id": server_id,
        "pattern": comp,
    })
    pidfile = api_get(
        context, context.version_3 + "/helper/cat", {
            "server_id": server_id,
            "file":
                context.component_installation_dir + "{0}/{0}.pid".format(comp),
        })

    assert pidfile in pids


@then(u'the component {comp:string} should run with the pid in pidfile in {duration:time}')
def step_impl(context, comp, duration):
    assert context.server != None

    def condition(context, flag):
        server_id = context.server["server_id"]
        pids = api_get(context, context.version_3 + "/helper/pgrep", {
            "server_id": server_id,
            "pattern": comp,
        })
        pidfile = api_get(
            context, context.version_3 + "/helper/cat", {
                "server_id": server_id,
                "file":
                    context.component_installation_dir + "{0}/{0}.pid".format(comp),
            })
        if pidfile in pids:
            return True

        waitfor(context, condition, duration)


@then(
    u'the component {comp:string} install directory own user should be "{expect_own_user:string}" and own group should be "{expect_own_group:string}"'
)
def step_impl(context, comp, expect_own_user, expect_own_group):
    assert context.server != None
    server_id = context.server["server_id"]

    resp = api_get(context, context.version_3 + "/helper/stat", {
        "server_id": server_id,
        "file": context.component_installation_dir + comp,
    })

    assert resp["own_user_name"] == expect_own_user
    assert resp["own_group_name"] == expect_own_group


@when(u'I prepare the server for uguard')
def step_impl(context):
    server = context.server
    assert server != None

    params = {
        "is_sync": "true",
        "server_id": server["server_id"],
    }

    for comp in ["udeploy", "ustats", "uguard-agent", "urman-agent"]:
        if not comp + "_status" in server:
            installation_file = get_installation_file(context, comp)
            params["is_installed_" + comp] = "uninstalled"
            params[comp + "_id"] = comp + "_" + server["server_id"]
            params[comp + "_install_file"] = installation_file
            params[comp + "_path"] = context.component_installation_dir + comp
            if comp == "urman-agent":
                params["max-backup-concurrency-num"] = "2"

    api_request_post(context, context.version_3 + "/server/prepare_server_env_for_guard", params)


@when(u'I prepare the server for uguard manager')
def step_impl(context):
    server = context.server
    assert server != None

    params = {
        "is_sync": "true",
        "server_id": server["server_id"],
    }

    for comp in ["uguard-mgr", "urman-mgr"]:
        if not comp + "_status" in server:
            installation_file = get_installation_file(context, comp)
            params["is_installed_" + comp] = "uninstalled"
            params[comp + "_id"] = comp + "_" + server["server_id"]
            params[comp + "_install_file"] = installation_file
            params[comp + "_path"] = context.component_installation_dir + comp

    api_request_post(context, context.version_3 + "/server/prepare_server_env_for_guard_manager",
                     params)


@then(u'the component {comp:string} should be running in {duration:time}')
def step_impl(context, comp, duration):
    assert context.server != None
    server_id = context.server["server_id"]

    for i in range(1, duration * context.time_weight * 10):
        resp = get_all_server_info(context)
        condition = '.[] | select(."server_id" == "{0}") | ."{1}_status"'.format(
            server_id, comp)
        match = pyjq.first(condition, resp)
        if match != None and (match in [
            "STATUS_OK", "STATUS_OK(leader)", "STATUS_OK(master)"
        ]):
            return
        time.sleep(0.1)
    assert False


@then(
    u'the server\'s component{s:s?} {comps:strings+} should be installed as the standard'
)
def step_impl(context, s, comps):
    for comp in comps:
        context.execute_steps(u"""
			Then the component {component} install directory own user should be "actiontech-universe" and own group should be "actiontech"
			And the component {component} should run with the pid in pidfile
			And the component {component} should be running in 120s
		""".format(component=comp))


@when(u'I found servers with {status:string} {comps:strings+}, or I skip the test')
def step_impl(context, status, comps):
    component_status = None
    resp = get_all_server_info(context)
    if status == 'running':
        component_status = 'STATUS_OK'
    elif status == 'stopped':
        component_status = 'STATUS_STOPPED'

    conditions = map(lambda comp: 'select(."{0}_status"=="{1}")'.format(comp, component_status),
                     comps)
    condition = '.[] | ' + " | ".join(conditions) + "|" + '.server_id'

    match = pyjq.all(condition, resp)
    if match is None:
        context.scenario.skip(
            "Found no server with {0} components {1}".format(status, comps))
    else:
        context.server_ids = match


@when(u'I pause {comps:strings+} on the {server_id:strings}')
def step_impl(context, comps, server_id):
    for comp in comps:
        template_params = {
            "server_id": server_id,
            "component": comp,
            "is_sync": True
        }
        api_request_post(context, context.version_3 + "/server/pause", template_params)
    context.server_id = server_id


@when(u'I pause {comps:strings+} on all these servers')
def step_impl(context, comps):
    assert context.server_ids != None
    for server_id in context.server_ids:
        context.execute_steps(u"""
    			When I pause {components} on the {server_id}
    			Then the response is ok
    			Then the {server_id}'s components, {components} should be stopped in 60s
    		""".format(components=",".join(comps), server_id=server_id))
    time.sleep(5)


@then(
    u'the {server_id:strings}\'s component{s:s?}, {comps:strings+} should be {status:strings} in {duration:time}')
def step_impl(context, server_id, s, comps, status, duration):
    def component_status(context, flag):
        resp = get_all_server_info(context)
        conditions = None
        if status == 'running':
            conditions = map(lambda comp: 'select(."{0}_status"=="STATUS_OK")'.format(comp), comps)
        elif status == 'stopped':
            conditions = map(lambda comp: 'select(."{0}_status"=="STATUS_STOPPED")'.format(comp), comps)

        condition = '.[] | select(."server_id"=="{0}") | '.format(server_id) + " | ".join(
            conditions) + " | " + '.server_id'
        match = pyjq.first(condition, resp)
        if match != None:
            return True

    waitfor(context, component_status, duration)
    context.server_id = server_id


@when(u'I start {comps:strings+} on the {server_id:strings}')
def step_impl(context, comps, server_id):
    for comp in comps:
        template_params = {
            "server_id": server_id,
            "component": comp,
            "is_sync": True
        }
        api_request_post(context, context.version_3 + "/server/start", template_params)
    context.server_id = server_id


@when(u'I start {comps:strings+} on all these servers')
def step_impl(context, comps):
    assert context.server_ids != None
    for server_id in context.server_ids:
        context.execute_steps(u"""
    			When I start {components} on the {server_id}
    			Then the response is ok
    			Then the {server_id}'s components, {components} should be running in 60s		
    		""".format(components=",".join(comps), server_id=server_id))
    time.sleep(5)


@when(u'I trigger the uguard drill')
def step_impl(context):
    api_request_post(context, context.version_3 + "/helper/component/uguard/trigger_exercise_task")


@when(u'I start {comps:strings+} except the {master_slave:string}\'s server')
def step_impl(context, comps, master_slave):
    context.execute_steps(u"""
            When I found servers with stopped {components}, or I skip the test
            Then the response is ok
           	""".format(components=",".join(comps)))
    context.server_ids.remove(context.mysql_instance['server_id'])
    context.execute_steps(u"""
        When I start {components} on all these servers
        Then the response is ok
       	""".format(components=",".join(comps)))


@when(u'I start {comps:strings+} on the {master_slave:string}\'s server')
def step_impl(context, comps, master_slave):
    context.execute_steps(u"""
           When I start {components} on the {server_id}
           Then the response is ok
          	""".format(components=",".join(comps), server_id=context.mysql_instance['server_id']))


@when(u'I found a server without MySQL instance')
def step_imp(context):
    resp = get_all_server_info(context)
    for server in resp:
        res = get_all_mysql_info(context)
        match = pyjq.first('.[] | select(.server_id == "{0}")'.format(server['server_id']), res)
        if match is None:
            context.server = server
            return
    assert False


@when(u'I kill component {comp:string} on this server')
def step_imp(context, comp):
    comps = comp + "_" + context.server["server_id"]
    api_post(context, context.version_3 + "/helper/component/kill", {
        "is_sync": True,
        "component_instance_id": comps
    })


@when(u'I kill component {comp:string} on all these servers')
def step_imp(context, comp):
    for server in context.server:
        comp_id = comp + "_" + server["server_id"]
        api_post(context, context.version_3 + "/helper/component/kill", {
            "is_sync": True,
            "component_instance_id": comp_id
        })


@Then(
    u'I found all the component{s:s?} {comps:strings+} on the server should be running'
)
def step_impl(context, s, comps):
    resp = get_all_server_info(context)
    conditions = map(lambda comp: 'select(has("{0}_status: "+"STATUS_OK"))'.format(comp), comps)
    condition = '.[] | ' + " | ".join(conditions)

    match = pyjq.all(condition, resp)
    if match is None:
        context.scenario.skip(
            "Found no server with components {0}".format(comps))
    else:
        context.server = match


@then(
    u'the {server_id:strings}\'s component{s:s?}, {comps:strings+} should be {status:strings}')
def step_impl(context, server_id, s, comps, status):
    resp = get_all_server_info(context)
    conditions = None
    if status == 'running':
        conditions = map(lambda comp: 'select(."{0}_status"=="STATUS_OK")'.format(comp), comps)
    elif status == 'stopped':
        conditions = map(lambda comp: 'select(."{0}_status"=="STATUS_STOPPED")'.format(comp), comps)

    condition = '.[] | select(."server_id"=="{0}") | '.format(server_id) + " | ".join(
        conditions) + " | " + '.server_id'
    match = pyjq.first(condition, resp)
    if match != None:
        return True

    context.server_id = server_id


@then(u'All servers\' componment{s:s?}, {comps:strings+} should be {status:string}')
def step_imp(context, s, comps, status):
    assert context.server_ids != None
    for server_id in context.server_ids:
        context.execute_steps(u"""
        Then the {server_id}'s components, {components} should be {status}
        """.format(components=",".join(comps), server_id=server_id, status=status))


@when(u'I update the value of metadate')
def step_imp(context):
    api_post(context, context.version_3 + "/helper/component/uguard/trigger_exercise_task", {
        "is_sync": True
    })


@when(u'I add a server')
def step_impl(context):
    assert context.new_server_ip is not None
    assert context.new_server_ssh_port is not None
    assert context.new_server_ssh_user is not None
    assert context.new_server_ssh_password is not None

    hostname = "udp40"

    uagent = api_get(context, context.version_3 + "/support/component?pattern=uagent")[-1]["Name"]
    ustats = api_get(context, context.version_3 + "/support/component?pattern=ustats")[-1]["Name"]

    api_request_post(context, context.version_3 + "/server/add", {
        "is_sync": True,
        "uagent_install_method": "ssh",
        "server_ip": context.new_server_ip,
        "ssh_port": context.new_server_ssh_port,
        "ssh_user": context.new_server_ssh_user,
        "ssh_password": context.new_server_ssh_password,
        "hostname": hostname,
        "server_id": "server-" + hostname,
        "uagent_path": "/opt/uagent",
        "uagent_id": "uagent-" + hostname,
        "uagent_install_file": uagent,
        "ustats_path": "/opt/ustats",
        "ustats_id": "ustats-" + hostname,
        "ustats_install_file": ustats,
    })
    context.server_id = "server-" + hostname


@when(u'I remove a server')
def step_impl(context):
    hostname = "udp40"
    api_post(context, context.version_3 + "/server/uninstall", {
        "is_sync": True,
        "server_id": "server-" + hostname,
        "component": "ustats",
    })
    api_request_post(context, context.version_3 + "/server/remove", {
        "is_sync": True,
        "server_id": "server-" + hostname,
        "ssh_port": context.new_server_ssh_port,
        "ssh_user": context.new_server_ssh_user,
        "ssh_password": context.new_server_ssh_password,
    })
    context.server_id = "server-" + hostname


@then(u'the server {should_or_not:should_or_not} be in the server list')
def step_impl(context, should_or_not):
    server_id = "server-udp40"
    resp = get_server_info_by_id(context, server_id)
    if resp is not None:
        length = len(resp)
    else:
        length = 0
    assert (length == 0 and not should_or_not) or (length != 0 and should_or_not)


@when(u'I found a dmp server')
def step_impl(context):
    resp = get_all_server_info(context)
    server = pyjq.first('.[]', resp)
    assert (server is not None), "There is no server"
    context.server = server
    context.server_id = server["server_id"]


@when(u'I silent the server')
def step_impl(context):
    server_id = context.server_id
    start_time = int(time.time())
    end_time = 31536000000 + start_time
    user_name = "admin"
    api_request_post(context, context.version_3 + "/alert/silence_servers", {
        "server_ids": server_id,
        "start": start_time,
        "end": end_time,
        "created_by": user_name,
    })
    context.start_time = start_time


@then(u'the server {should_or_not:should_or_not} in the silence list')
def step_impl(context, should_or_not):
    resp = api_get(context, context.version_3 + "/alert/list_silence", {
        "number": context.page_size_to_select_all,
    })
    if should_or_not:
        condition = '.[]|select(."rule_id"=="silence-server-{0}")|select(."start"=="{1}")' \
            .format(context.server_id, context.start_time)
        silence_list = pyjq.all(condition, resp)
        assert len(silence_list) != 0, "the server silent failed"
    elif not should_or_not:
        condition = '.[]|select(."rule_id"=="silence-server-{0}")'.format(context.server_id)
        silence_list = pyjq.all(condition, resp)
        assert len(silence_list) == 0, "the server resume failed"


@when(u'I found a server in silence')
def step_impl(context):
    resp = api_get(context, context.version_3 + "/alert/list_silence", {
        "number": context.page_size_to_select_all,
    })
    servers = pyjq.all('.[]', resp)
    for server in servers:
        # spilt information from "silence-server-server-udp9"
        server_info = server["rule_id"].split("-", 2)
        if server_info[1] == "server":
            server_id = server_info[2]
            context.server_id = server_id
            context.rule_id = server["rule_id"]
            break


@when(u'I resume the server from silence')
def step_impl(context):
    rule_id = context.rule_id
    api_request_post(context, context.version_3 + "/alert/remove_silence", {
        "is_sync": True,
        "rule_id": rule_id,
    })


@when(u'I get the list of servers,through version {version:int}')
def step_impl(context, version):
    serverList = api_request_get(context, context.version_5 + "/server/list")
    context.serverList = json.loads(serverList.text)


@then(u'I check the version information for all components')
def step_impl(context):
    assert context.serverList is not None
    for server in context.serverList["data"]:
        components = api_get(context, context.version_3 + "/server/list_components", {
            "server_id": server["server_id"]
        })
        for component in components:
            assert len(component["version"].strip()) != 0


@then(u'the version of the component {comp:string} should be {version:string}')
def step_impl(context, comp, version):
    assert context.server is not None
    server_id = context.server_id
    resp = api_get(context, context.version_3 + "/server/list_components", {
        "server_id": server_id,
    })
    component = pyjq.first('.[]|select(."type"=="{0}")'.format(comp), resp)
    dic = readYaml("conf/version_id.yml")
    if version == "vs":
        ver = "master"
    else:
        ver = dic[version]
    match = component["version"].find(ver)
    assert component is not None and match


@when(u'I got the status of the component {comp:string}')
def step_impl(context, comp):
    server_id = context.server_id
    resp = get_server_info_by_id(context, server_id)
    server_info = resp
    key = comp + "_status"
    context.comp_status = server_info[key]
    print("context.comp_status:" + context.comp_status)
    print("")


@when(u'I update the server component {comp:string} to version {version:string}')
def step_impl(context, comp, version):
    server_id = context.server_id
    installation_file = get_installation_file_by_version(context, comp, version)
    api_request_post(context, context.version_3 + "/server/update", {
        "is_sync": True,
        "component": comp,
        "server_id": server_id,
        "update_file": installation_file,
    })


@then(u'the status of the component {comp:string} should be the same with before in {duration:time}')
def step_impl(context, comp, duration):
    def condition(context, flag):
        server_id = context.server_id
        resp = get_server_info_by_id(context, server_id)
        server_info = resp
        key = comp + "_status"
        comp_status = server_info[key]
        if comp_status == context.comp_status:
            return True

    waitfor(context, condition, duration)


@when(u'I download logs from the server')
def step_impl(context):
    server_id = context.server_id
    t = time.time()
    filter_date_to = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))
    filter_date_from = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t - 1))

    params = {
        "server_id": server_id,
        "filter_date_from": filter_date_from,
        "filter_date_to": filter_date_to,
    }
    #  url = context.base_url + context.version_3 + "/server/download_logs"
    #  headers = {"authorization": this.token}

    str_t = str(int(time.time()))
    with api_request_type_get(context, context.version_3 + "/server/download_logs", params,
                              types="download", stream=True) as r:
        resp = r
    #   resp = requests.get(url, params, headers=headers, stream=True)
    #   resp = getattr(requests, "get")(url, params, headers=headers, stream=True)
    file_name = str_t + ".tar.gz"
    with open(file_name, "wb") as f:
        for bl in resp.iter_content(chunk_size=1024):
            if bl:
                f.write(bl)
    context.file_name = file_name
    context.str_time = str_t


@then(u'I should download the correct files')
def step_impl(context):
    server_id = context.server_id
    file_name = context.file_name
    str_t = context.str_time

    f = tarfile.open(file_name)
    file_names = f.getnames()
    f.close()

    temp_id = server_id.replace("server-", "")
    log_name_temp = "dump_log_" + temp_id
    log_name = "dump_log_" + temp_id + "_" + str_t

    assert (log_name in file_names) or (log_name_temp in file_names[0])


@when(u'I stop all the uguard manager')
def step_impl(context):
    resp = api_get(context, context.version_5 + "/server/list", {"page_size": 99})
    uguard_mgr = []
    uguard_mgr_master = []
    for server in resp["data"]:
        if "uguard_mgr_status" in server:
            if server["uguard_mgr_status"] == "STATUS_OK":
                uguard_mgr.append(server["server_id"])
            elif server["uguard_mgr_status"] == "STATUS_OK(master)":
                uguard_mgr_master.append(server["server_id"])
    context.stop_uguard_list = uguard_mgr + uguard_mgr_master
    context.start_uguard_list = uguard_mgr_master + uguard_mgr
    for server_id in context.stop_uguard_list:
        api_post(context, context.version_3 + "/server/pause", {
            "is_sync": True,
            "component": "uguard-mgr",
            "server_id": server_id,
        })

        def condition(context, flag):
            resp_server = api_get(context, context.version_5 + "/server/list", {"page_size": 99})
            server_status = pyjq.first('.data[]|select(."server_id"=="{0}")'.format(server_id), resp_server)
            status = server_status["uguard_mgr_status"]
            if status == "STATUS_STOPPED" or status == "STATUS_STOPPED(master)":
                return True

        waitfor(context, condition, 120)


@when(u'I start all the uguard manager')
def step_impl(context):
    for server_id in context.start_uguard_list:
        api_post(context, context.version_3 + "/server/start", {
            "is_sync": True,
            "component": "uguard-mgr",
            "server_id": server_id,
        })

        def condition(context, flag):
            resp_server = api_get(context, context.version_5 + "/server/list", {"page_size": 99})
            server_status = pyjq.first('.data[]|select(."server_id"=="{0}")'.format(server_id), resp_server)
            status = server_status["uguard_mgr_status"]
            if status == "STATUS_OK" or status == "STATUS_OK(master)":
                return True

        waitfor(context, condition, 120)