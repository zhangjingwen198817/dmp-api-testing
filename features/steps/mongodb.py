from behave import *
from framework.api import *
import pyjq
import time
import json
import re
from util import *
from common import *
import time
from getinfo import *
import logging
from pprint import pformat
LOGGER = logging.getLogger("steps.mongodb")
use_step_matcher("cfparse")



@when(u'I add MongoDB group')
def step_imp(context):
    assert context.valid_port != None
    mongodb_group_id = "mongodb-" + generate_id()
    body = {
        "group_id": mongodb_group_id,
        "port": context.valid_port,
        "mongodb_admin_user": "admin",
        "mongodb_admin_password": "QWEasd123",
        "is_sync": True
    }
    api_request_post(context, context.version_3 + "/mongodb/add_group", body)
    context.mongodb_group_id = mongodb_group_id


@then(
    u'the MongoDB group list {should_or_not:should_or_not} contains the MongoDB group'
)
def step_impl(context, should_or_not):
    assert context.mongodb_group_id != None

    resp = get_all_mongo_group(context)
    match = pyjq.first(
        '.[] | select(.mongodb_group_id == "{0}")'.format(context.mongodb_group_id),
        resp)
    assert (match != None and should_or_not) or (match == None and
                                                 not should_or_not)


@when(u'I found a MongoDB group without MongoDB instance, or I skip the test')
def step_impl(context):
    resp = get_all_mongo_group(context)
    match = pyjq.first('.[] | select(.mongodb_group_instance_nums == "0") ', resp)
    if match is None:
        context.scenario.skip("found a MongoDB group with MongoDB instance")
    else:
        context.mongodb_group = match


@when(u'I add MongoDB {role:string} instance')
def step_imp(context, role):
    assert context.mongodb_group != None
    install_file = get_mongodb_installation_file(context)
    base_dir = context.component_installation_dir
    if role == "master":
        assert context.server != None
    else:
        mongodb_group_id = context.mongodb_group["mongodb_group_id"]
        mongodb_master = get_mongo_instance_group(context, mongodb_group_id)
        context.execute_steps(u"""
        			When I found a server with components ustats,udeploy,uguard-agent,urman-agent, except {server}
        		""".format(server=mongodb_master[0]["server_id"]))

    body = {
        "server_id":
            context.server['server_id'],
        "group_id":
            context.mongodb_group['mongodb_group_id'],
        "mongodb_id":
            "mongodb-" + generate_id(),
        "mongodb_alias":
            "mongodb-" + generate_id(),
        "mongodb_tarball_path":
            install_file,
        "mongodb_base_path":
            base_dir + "mongodb/base/" + context.mongodb_group['mongodb_group_port'],
        "mongodb_data_path":
            base_dir + "mongodb/data/" + context.mongodb_group['mongodb_group_port'],
        "mongodb_config_path":
            base_dir + "mongodb/etc/" + context.mongodb_group['mongodb_group_port'] + "/config",
        "mongodb_backup_path":
            base_dir + "mongodb/backup/" + context.mongodb_group['mongodb_group_port'],
        "mongodb_run_user":
            "actiontech-mongodb",
        "is_sync": True
    }
    res=api_post(context, context.version_3 + "/mongodb/add_instance", body)
    progress_id = res['progress_id']
    context.execute_steps(u"""
                    Then wait for progress {0} is finished in {1}s
                    """.format(progress_id, 120))

def get_mongodb_installation_file(context):
    return get_installation_file(context, "mongodb")


@then(u'the MongoDB instance should add succeed in {duration:time}')
def step_imp(context, duration):
    assert context.mongodb_group != None

    def condition(context, flag):
        resp = get_all_mongo_instance(context)
        match = pyjq.first(
            '.[] | select(.mongodb_group_id == "{0}")'.format(
                context.mongodb_group['mongodb_group_id']), resp)
        assert match is not None
        if match['mongodb_instance_health_status'] == "STATUS_MONGODB_HEALTH_OK":
            return True

    waitfor(context, condition, duration)


@then(
    u'the MongoDB group should have {master_count:int} running MongoDB master and {slave_count:int} running MongoDB slave in {duration:time}'
)
def step_impl(context, master_count, slave_count, duration):
    assert context.mongodb_group != None

    def condition(context, flag):
        resp = get_all_mongo_instance(context)
        condition = '.[] | select(."mongodb_instance_health_status" == "STATUS_MONGODB_HEALTH_OK")'
        masters = pyjq.all(
            condition +
            ' | select(."mongodb_instance_replication_status" == "STATUS_MONGODB_PRIMARY" and ."mongodb_group_id" == "{0}")'.format(context.mongodb_group['mongodb_group_id']),
            resp)
        slaves = pyjq.all(
            condition +
            ' | select(."mongodb_instance_replication_status" == "STATUS_MONGODB_SECONDARY" and ."mongodb_group_id" == "{0}")'.format(context.mongodb_group['mongodb_group_id']),
            resp)
        if len(masters) == master_count and len(slaves) == slave_count:
            return True

    waitfor(context, condition, duration)


@when(u'I found a running MongoDB instance {role:string}, or I skip the test')
def step_imp(context, role):
    resp = get_all_mongo_instance(context)
    if role == "slave":
        role = "STATUS_MONGODB_SECONDARY"
    else:
        role = "STATUS_MONGODB_PRIMARY"
    condition = '.[] | select(."mongodb_instance_health_status" == "STATUS_MONGODB_HEALTH_OK")'
    masters = pyjq.first(
        condition + ' | select(."mongodb_instance_replication_status" == "{0}")'.format(role),
        resp)
    slaves = pyjq.first(
        condition + ' | select(."mongodb_instance_replication_status" == "{0}")'.format(role),
        resp)
    if masters is None and slaves is None:
        context.scenario.skip("no found a MongoDB group with MongoDB instance")
        return
    else:
        if role == 'slave':
            context.mongodb_info = slaves
        else:
            context.mongodb_info = masters


@when(u'I action {action:string} the MongoDB instance')
def step_imp(context, action):
    assert context.mongodb_info != None
    if action.lower() == "stop":
        api_request_post(context, context.version_3 + "/mongodb/stop_instance", {
            "mongodb_id": context.mongodb_info['mongodb_instance_id'],
            "is_sync": True
        })
    else:
        api_request_post(context, context.version_3 + "/mongodb/start_instance", {
            "mongodb_id": context.mongodb_info['mongodb_instance_id'],
            "is_sync": True
        })


@then(u'the MongoDB instance should {status:string} in {duration:time}')
def step_imp(context, status, duration):
    assert context.mongodb_info != None
    if status == "stopped":

        def condition(context, flag):
            resp = get_all_mongo_instance(context)
            match = pyjq.first(
                '.[] | select(."mongodb_instance_health_status" == "STATUS_MONGODB_HEALTH_BAD" and ."mongodb_instance_id" == "{0}")'
                    .format(context.mongodb_info['mongodb_instance_id']), resp)
            if match is not None:
                return True

        waitfor(context, condition, duration)
    else:

        def condition(context, flag):
            resp = get_all_mongo_instance(context)
            match = pyjq.first(
                '.[] | select(."mongodb_instance_health_status" == "STATUS_MONGODB_HEALTH_OK" and ."mongodb_instance_id" == "{0}")'
                    .format(context.mongodb_info['mongodb_instance_id']), resp)
            if match is not None:
                return True

        waitfor(context, condition, duration)


@when(u'I remove MongoDB instance')
def step_imp(context):
    assert context.mongodb_info != None
    api_request_post(context, context.version_3 + "/mongodb/remove_instance", {
        "mongodb_id": context.mongodb_info['mongodb_instance_id'],
        "is_sync": True
    })


@then(
    u'the MongoDB instance list should not contains the MongoDB instance in {duration:time}'
)
def step_impl(context, duration):
    assert context.mongodb_info != None

    def condition(context, flag):
        resp = get_all_mongo_instance(context)
        match = pyjq.first(
            '.[] | select(.mongodb_instance_id == "{0}")'.format(
                context.mongodb_info['mongodb_instance_id']), resp)
        if match is None:
            return True

    waitfor(context, condition, duration)
