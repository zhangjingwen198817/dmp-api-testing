from behave import *
from framework.api import *
import pyjq
import time
import json
import re
from util import *
from common import *
from database import get_mysql_group_brief
from lxml import etree

use_step_matcher("cfparse")


@when(u'I add a Ushard group')
def step_impl(context):
    assert context.valid_ports != None
    assert len(context.valid_ports) >= 2
    flow_port, manage_port = context.valid_ports[0], context.valid_ports[1]

    group_id = "ushard-group-" + generate_id()

    api_request_post(
        context, context.version_3 + "/ushard/add_group", {
            "is_sync": True,
            "group_id": group_id,
            "admin_user": "root_user",
            "admin_password": "root_password",
            "flow_port": flow_port,
            "manage_port": manage_port,
            "charset": "utf8",
            "version": "5.6.23",
        })

    context.ushard_group = {"group_id": group_id}


@then(
    u'the Ushard group list {should_or_not:should_or_not} contains the Ushard group'
)
def step_impl(context, should_or_not):
    assert context.ushard_group != None
    group_id = context.ushard_group["group_id"]

    resp = api_get(context, context.version_3 + "/ushard/list_group", {
        "number": context.page_size_to_select_all,
    })
    match = pyjq.first('.data[] | select(.group_id == "{0}")'.format(group_id),
                       resp)
    assert (match != None and should_or_not) or (match == None and
                                                 not should_or_not)


@when(u'I found a Ushard group without Ushard instance, or I skip the test')
def step_impl(context):
    resp = api_get(context, context.version_3 + "/ushard/list_group", {
        "number": context.page_size_to_select_all,
    })
    match = pyjq.first('.data[] | select(.group_instance_num == "0")', resp)
    if match is None:
        context.scenario.skip("Found no Ushard group without Ushard instance")
    else:
        context.ushard_group = match


@when(u'I remove the Ushard group')
def step_impl(context):
    assert context.ushard_group != None
    group_id = context.ushard_group["group_id"]

    api_request_post(context, context.version_3 + "/ushard/remove_group", {
        "is_sync": True,
        "group_id": group_id,
    })


@when(u'I add Ushard instance in the Ushard group')
def step_impl(context):
    assert context.ushard_group != None
    assert context.server != None
    print(context.server)
    ushard_id = "ushard-" + generate_id()

    install_params = {
        "is_sync": True,
        "group_id": context.ushard_group["group_id"],
        "ushard_id": ushard_id,
        "server_id": context.server["server_id"],
        "cpu_cores": "1",
        "direct_memory": "0",
        "memory_heap_initial_capacity": "1024",
        "memory_heap_max_capacity": "4096",
        "ushard_path": "/opt/ushard",
        "ushard_install_file": get_ushard_installation_file(context),
        "dble_path": "/opt/ushard",
        "dble_install_file": get_dble_installation_file(context)
    }
    api_request_post(context, context.version_3 + "/ushard/add_instance", install_params)


def get_ushard_installation_file(context):
    return get_installation_file(context, "ushard")


def get_dble_installation_file(context):
    return get_installation_file(context, "dble")


@then(
    u'the Ushard group should have {expect_count:int} running Ushard instance in {duration:time}'
)
def step_impl(context, expect_count, duration):
    assert context.ushard_group != None
    group_id = context.ushard_group["group_id"]

    def condition(context, flag):
        resp = api_get(context, context.version_3 + "/ushard/list_instance", {
            "group_id": group_id,
        })
        data = resp["data"]
        assert len(data) == expect_count
        condition = '.data[] | select(."mysql_status" != "STATUS_MYSQL_HEALTH_OK" or ."replication_status" != "STATUS_MYSQL_REPL_OK")'
        match = pyjq.first(condition, resp)
        if match is not None:
            return True

    waitfor(context, condition, duration)


@when(u'I found a server without ushard')
def step_impl(context):
    resp = api_get(context, context.version_3 + "/server/list", {
        "number": context.page_size_to_select_all,
    })
    for server in pyjq.all('.data[]', resp):
        resp = api_get(context, context.version_3 + "/ushard/list_instance",
                       {"server_id": server["server_id"]})
        match = pyjq.first('.data[] | .', resp)
        if match is None:
            context.server = server
            return

    assert False


@when(
    u'I found {count:int} Ushard group with Ushard instance, or I skip the test'
)
def step_impl(context, count):
    resp = api_get(context, context.version_3 + "/ushard/list_group", {
        "number": context.page_size_to_select_all,
    })
    match = pyjq.first('.data[] | select(.group_instance_num > 0)', resp)
    if match is None:
        context.scenario.skip("Found no Ushard group with Ushard instance")
    else:
        context.ushard_group = match


@when(u'I configure the Ushard group by adding 2 users to the MySQL groups')
def step_impl(context):
    assert context.ushard_group != None
    assert context.mysql_groups != None
    assert len(context.mysql_groups) >= 2

    configs = api_get(context, context.version_3 + "/ushard_deploy/get_config", {
        "group_id": context.ushard_group["group_id"],
    })

    id = generate_id()
    user1 = {
        "name": "user1_" + id,
        "password": "user1_pass_" + id,
        "schema": "schema_" + id
    }
    id = generate_id()
    user2 = {
        "name": "user2_" + id,
        "password": "user2_pass_" + id,
        "schema": "schema_" + id
    }

    context.ushard_users = {"user1": user1, "user2": user2}

    rule_id = "rule_" + generate_id()

    mysql_group_1 = get_mysql_group_brief(context,
                                          context.mysql_groups[0]["group_id"])
    mysql_group_2 = get_mysql_group_brief(context,
                                          context.mysql_groups[1]["group_id"])

    # prepare database in MySQL
    api_get(
        context, context.version_3 + "/helper/query_mysql", {
            "mysql_id": mysql_group_1["master_id"],
            "user": "root",
            "password": mysql_group_1["root_password"],
            "query": "create database {0}_db1".format(user1["schema"])
        })
    api_get(
        context, context.version_3 + "/helper/query_mysql", {
            "mysql_id": mysql_group_1["master_id"],
            "user": "root",
            "password": mysql_group_1["root_password"],
            "query": "create database {0}_db2".format(user1["schema"])
        })
    api_get(
        context, context.version_3 + "/helper/query_mysql", {
            "mysql_id": mysql_group_2["master_id"],
            "user": "root",
            "password": mysql_group_2["root_password"],
            "query": "create database {0}_db1".format(user2["schema"])
        })
    api_get(
        context, context.version_3 + "/helper/query_mysql", {
            "mysql_id": mysql_group_2["master_id"],
            "user": "root",
            "password": mysql_group_2["root_password"],
            "query": "create database {0}_db2".format(user2["schema"])
        })

    # update dble

    ## server.xml
    serverXmlStr = pyjq.first('.[] | select(.name == "server.xml") | .value',
                              configs)
    assert serverXmlStr is not None
    serverXml = read_xml(serverXmlStr)

    for user in [user1, user2]:
        serverXml.getroot().append(
            etree.fromstring("""
        <user name="{0}">
            <property name="password">{1}</property>
            <property name="readOnly">false</property>
            <property name="schemas">{2}</property>
        </user>""".format(user["name"], user["password"], user["schema"])))

    ## schema.xml
    schemaXmlStr = pyjq.first('.[] | select(.name == "schema.xml") | .value',
                              configs)
    assert schemaXmlStr is not None
    schemaXml = read_xml(schemaXmlStr)

    newSections = """
<newSections>
    <schema name="{1}" sqlMaxLimit="100">
        <table name="test" type="default" primaryKey="id" needAddLimit="true" rule="{0}" dataNode="{1}_dn1,{1}_dn2"></table>
    </schema>
    <schema name="{6}" sqlMaxLimit="100">
        <table name="test" type="default" primaryKey="id" needAddLimit="true" rule="{0}" dataNode="{6}_dn3,{6}_dn4"></table>
    </schema>
    <dataNode name="{1}_dn1" dataHost="{1}_dh1" database="{1}_db1"></dataNode>
    <dataNode name="{1}_dn2" dataHost="{1}_dh1" database="{1}_db2"></dataNode>
    <dataNode name="{6}_dn3" dataHost="{6}_dh2" database="{6}_db1"></dataNode>
    <dataNode name="{6}_dn4" dataHost="{6}_dh2" database="{6}_db2"></dataNode>
    <dataHost name="{1}_dh1" maxCon="100" minCon="10" balance="1" switchType="-1" slaveThreshold="-1">
        <heartbeat>show slave status</heartbeat>
        <writeHost host="{1}_M" url="{2}" user="{4}" password="{5}">
            <readHost host="{1}_S1" url="{3}" user="{4}" password="{5}"></readHost>
        </writeHost>
    </dataHost>
    <dataHost name="{6}_dh2" maxCon="100" minCon="10" balance="1" switchType="-1" slaveThreshold="-1">
        <heartbeat>show slave status</heartbeat>
        <writeHost host="{6}_M" url="{7}" user="{9}" password="{10}">
            <readHost host="{6}_S1" url="{8}" user="{9}" password="{10}"></readHost>
        </writeHost>
    </dataHost>
</newSections>""".format(
        rule_id, user1["schema"], mysql_group_1["master_addr"],
        mysql_group_1["slave_addr"], "root", mysql_group_1["root_password"],
        user2["schema"], mysql_group_2["master_addr"],
        mysql_group_2["slave_addr"], "root", mysql_group_2["root_password"])

    for item in etree.fromstring(newSections):
        schemaXml.getroot().append(item)

    ## rule.xml
    ruleXmlStr = pyjq.first('.[] | select(.name == "rule.xml") | .value',
                            configs)
    assert ruleXmlStr is not None
    ruleXml = read_xml(ruleXmlStr)

    ruleXml.getroot().insert(
        0,
        etree.fromstring("""
    <tableRule name="{0}">
        <rule>
            <columns>id</columns>
            <algorithm>{0}</algorithm>
        </rule>
    </tableRule>""".format(rule_id)))

    ruleXml.getroot().append(
        etree.fromstring("""
    <function name="{0}" class="Hash">
        <property name="partitionCount">2</property>
        <property name="partitionLength">1</property>
    </function>""".format(rule_id)))

    ## update config
    cacheServiceXmlStr = pyjq.first(
        '.[] | select(.name == "cacheservice.properties") | .value', configs)
    assert cacheServiceXmlStr is not None
    ehcacheXmlStr = pyjq.first('.[] | select(.name == "ehcache.xml") | .value',
                               configs)
    assert ehcacheXmlStr is not None

    config = [{
        "name": "rule.xml",
        "value": xml_to_str(ruleXml),
    }, {
        "name": "schema.xml",
        "value": xml_to_str(schemaXml),
    }, {
        "name": "server.xml",
        "value": xml_to_str(serverXml),
    }, {
        "name": "cacheservice.properties",
        "value": cacheServiceXmlStr,
    }, {
        "name": "ehcache.xml",
        "value": ehcacheXmlStr,
    }]

    api_request_post(
        context, context.version_3 + "/ushard_deploy/save_config", {
            "is_sync": True,
            "group_id": context.ushard_group["group_id"],
            "ushard_config": json.dumps(config)
        })


def read_xml(str):
    return etree.ElementTree(etree.XML(str))


def xml_to_str(xml):
    return etree.tostring(
        xml,
        doctype=xml.docinfo.doctype.replace("<!DOCTYPE ",
                                            "<!DOCTYPE dble:")).decode()


@when(u'I create test table to dble by {user_name:string}')
def step_impl(context, user_name):
    assert context.ushard_group != None
    assert context.ushard_users != None

    user = context.ushard_users[user_name]
    ushard_group_id = context.ushard_group["group_id"]

    api_get(
        context, context.version_3 + "/helper/query_dble", {
            "ushard_group_id": ushard_group_id,
            "user": user["name"],
            "password": user["password"],
            "query": "create table test(id int)",
            "schema": user["schema"]
        })


@when(u'I insert data to dble by {user_name:string}')
def step_impl(context, user_name):
    assert context.ushard_group != None
    assert context.ushard_users != None

    user = context.ushard_users[user_name]
    ushard_group_id = context.ushard_group["group_id"]
    id = randint(0, 1048576)
    context.insert_dble_data_id = id

    api_get(
        context, context.version_3 + "/helper/query_dble", {
            "ushard_group_id": ushard_group_id,
            "user": user["name"],
            "password": user["password"],
            "query": "insert into test (id) values({0})".format(id),
            "schema": user["schema"]
        })


@then(u'I found the data in MySQL by {user_name:string}')
def step_impl(context, user_name):
    assert context.ushard_group != None
    assert context.ushard_users != None
    assert context.insert_dble_data_id != None

    user = context.ushard_users[user_name]
    ushard_group_id = context.ushard_group["group_id"]
    resp = api_get(
        context, context.version_3 + "/helper/query_dble", {
            "ushard_group_id":
            ushard_group_id,
            "user":
            user["name"],
            "password":
            user["password"],
            "query":
            "select * from test where id = '{0}'".format(
                context.insert_dble_data_id),
            "schema":
            user["schema"]
        })
    assert len(resp) == 1
