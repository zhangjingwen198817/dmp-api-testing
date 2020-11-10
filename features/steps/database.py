from behave import *
from framework.api import *
import pyjq
import time
import json
import re
from util import *
from common import *
import time
import datetime
from data_locate import *
import logging
from pprint import pformat
from getinfo import *
import random
LOGGER = logging.getLogger("steps.database")
use_step_matcher("cfparse")


@when(u'I found a running MySQL instance, or I skip the test')
def step_impl(context):
    resp = get_all_group_info(context)
    matchs = pyjq.all('.[] | select(.mysql_group_instance_nums == "1")', resp)
    if len(matchs) == 0:
        context.scenario.skip("Found no MySQL instance")
        return
    for match in matchs:
        mysqls = get_all_mysql_info(context)
        mysql = pyjq.first(
            '.[] | select(.mysql_instance_status == "STATUS_MYSQL_HEALTH_OK" and .mysql_group_id == "{0}" )'
                .format(match['mysql_group_id']), mysqls)
        if mysql != None:
            root_password = api_get(context, context.version_3 + "/helper/get_mysql_password", {
                "mysql_id": mysql["mysql_instance_id"],
                "password_type": "ROOT",
            })
            mysql["root_password"] = root_password
            context.mysql_instance = mysql
            return


@when(u'I query the MySQL instance "{query:any}"')
def step_impl(context, query):
    assert context.mysql_instance is not None
    mysql = context.mysql_instance
    mysql_instance_id = mysql["mysql_instance_id"]
    root_password = get_mysql_instance_root_password(context, mysql_instance_id)
    context.mysql_resp = query_from_mysql_instance(context, mysql_instance_id, root_password, query)


@when(u'I query on the {master_slave:string} instance, with the sql: "{query:any}"')
def step_impl(context, master_slave, query):
    assert context.mysql_instance != None
    password = get_master_root_password(context)
    resp = api_get(
        context, context.version_3 + "/helper/query_mysql", {
            "mysql_id": context.mysql_instance["mysql_instance_id"],
            "query": query,
            "user": "root",
            "password": password,
        })
    context.mysql_resp = resp


@then(u'the MySQL response should be')
def step_impl(context):
    time.sleep(5)
    assert context.mysql_resp != None
    resp = context.mysql_resp
    idx = 0
    for row in context.table:
        actual_row = resp[idx]
        for heading in context.table.headings:
            assert row[heading] == actual_row[heading]
        idx += 1


@when(u'I add a MySQL group with the SIP')
def step_impl(context):
    assert context.valid_sip != None
    sip = context.valid_sip

    mysql_group_id = "mysql-group-" + generate_id()

    api_request_post(context, context.version_3 + "/database/add_group", {
        "is_sync": True,
        "group_id": mysql_group_id,
        "sip": sip,
        "tag_list": "[]",
    })

    context.mysql_group = {"mysql_group_id": mysql_group_id}


@when(u'I add a MySQL group')
def step_impl(context):
    mysql_group_id = "mysql-group-" + generate_id()

    api_request_post(context, context.version_3 + "/database/add_group", {
        "is_sync": True,
        "group_id": mysql_group_id,
        "tag_list": "[]",
    })

    context.mysql_group = {"mysql_group_id": mysql_group_id}


@then(
    u'the MySQL group list {should_or_not:should_or_not} contains the MySQL group'
)
def step_impl(context, should_or_not):
    assert context.mysql_group
    mysql_group_id = context.mysql_group["mysql_group_id"]

    resp = get_all_group_info(context)
    match = pyjq.first(
        '.[] | select(.mysql_group_id == "{0}")'.format(mysql_group_id), resp)
    assert (match != None and should_or_not) or (match == None and
                                                 not should_or_not)


@when(
    u'I found a MySQL group without MySQL instance, and without SIP, or I skip the test'
)
def step_impl(context):
    resp = get_all_group_info(context)
    match = pyjq.first(
        '.[] | select(.mysql_group_instance_nums == "0") | select(has("sip") | not)',
        resp)
    if match is None:
        context.scenario.skip(
            "Found no MySQL group without MySQL instance, and without SIP")
    else:
        context.mysql_group = match


@when(u'I found a MySQL group without MySQL instance, or I skip the test')
def step_impl(context):
    resp = get_all_group_info(context)
    match = pyjq.first('.[] | select(.mysql_group_instance_nums == "0")', resp)
    if match is None:
        context.scenario.skip("Found no MySQL group without MySQL instance")
    else:
        context.mysql_group = match


@when(u'I remove the MySQL group')
def step_impl(context):
    assert context.mysql_group != None
    mysql_group_id = context.mysql_group["mysql_group_id"]

    api_request_post(context, context.version_3 + "/database/remove_group", {
        "is_sync": True,
        "group_id": mysql_group_id,
    })


@when(u'I add MySQL instance in the MySQL group')
def step_impl(context):
    assert context.mysql_group != None
    assert context.valid_port != None
    assert context.server != None
    mysql_group_id = context.mysql_group["mysql_group_id"]
    mysql_instance_id = "mysql-" + generate_id()
    mysql_dir = context.mysql_installation_dir
    port = context.valid_port
    install_file = get_mysql_installation_file(context)
    version = re.match(r".*(\d+\.\d+\.\d+).*", install_file).group(1)
    main_version = re.match(r"(\d+\.\d+)\.\d+", version).group(1)

    mycnf = api_get(context, context.version_3 + "/support/read_umc_file", {
        "path": "mycnfs/my.cnf." + main_version,
    })

    mycnf = mycnf.replace("innodb_data_file_path = ibdata1:1G:autoextend",
                          "innodb_data_file_path = ibdata1:64M:autoextend")

    install_params = {
        "server_id": context.server["server_id"],
        "group_id": context.mysql_group["mysql_group_id"],
        "port": port,
        "mysql_id": mysql_instance_id,
        "mysql_alias": mysql_instance_id,
        "mysql_tarball_path": install_file,
        "install_standard": "uguard_semi_sync",
        "init_data": "",
        "create_extranet_root": "1",
        "extranet_root_privilege": "ALL PRIVILEGES ON *.*\nPROXY ON \"@\"",
        "mysql_root_init_password": "@123qwerTYUIOP",
        "mysql_base_path": mysql_dir + "base/" + version,
        "mysql_data_path": mysql_dir + "data/" + port,
        "mysql_binlog_path": mysql_dir + "log/binlog/" + port,
        "mysql_relaylog_path": mysql_dir + "log/relaylog/" + port,
        "mysql_redolog_path": mysql_dir + "log/redolog/" + port,
        "mysql_tmp_path": mysql_dir + "tmp/" + port,
        "backup_path": mysql_dir + "backup/" + port,
        "mycnf_path": mysql_dir + "etc/" + port + "/my.cnf",
        "version": version,
        "user_type": "single_user",
        "all_user": "universe_op",
        "all_host": "%",
        "all_password": "bupYE@-00",
        "all_privilege":
            "lock tables, process, reload, replication client, super, usage on *.*\nreplication slave, replication client on *.*\nshow databases, show view, update, super, create temporary tables, trigger, create view, alter routine, create routine, execute, file, create tablespace, create user, create, drop, grant option, lock tables, references, event, alter, delete, index, insert, select, usage on *.*\ncreate,select,insert,update,delete on universe.*\nselect on universe.*\nsuper on *.*\nsuper on *.*\nprocess on *.*\nreload on *.*\nreplication client on *.*\nsuper on *.*\nselect on performance_schema.*\nselect on mysql.*\nselect, execute on sys.*\nprocess on *.*\nevent on *.*\n",
        "run_user": "actiontech-mysql",
        "run_user_group": "",
        "mysql_uid": "",
        "mysql_gid": "",
        "mycnf_server_id": str(randint(1, 4294967295)),
        "umask": "0640",
        "umask_dir": "0750",
        "mycnf_config": mycnf
    }

    mycnf = api_post(context, context.version_3 + "/database/apply_my_cnf", install_params)
    install_params["mycnf_config"] = mycnf
    install_params["is_sync"] = True
    install_params["tag_list"] = "[]"

    api_request_post(context, context.version_3 + "/database/add_instance", install_params)


@when(u'I add off-standard MySQL instance in the MySQL group')
def step_impl(context):
    assert context.mysql_group != None
    assert context.valid_port != None
    assert context.server != None
    mysql_group_id = context.mysql_group["mysql_group_id"]
    mysql_instance_id = "mysql-" + generate_id()
    mysql_dir = context.mysql_installation_dir
    port = context.valid_port
    install_file = get_mysql_installation_file(context)
    version = re.match(r".*(\d+\.\d+\.\d+).*", install_file).group(1)
    main_version = re.match(r"(\d+\.\d+)\.\d+", version).group(1)

    mycnf = api_get(context, context.version_3 + "/support/read_umc_file", {
        "path": "mycnfs/my.cnf." + main_version,
    })

    mycnf = mycnf.replace("innodb_data_file_path = ibdata1:1G:autoextend",
                          "innodb_data_file_path = ibdata1:64M:autoextend")

    install_params = {
        "server_id": context.server["server_id"],
        "group_id": mysql_group_id,
        "port": port,
        "mysql_id": mysql_instance_id,
        "mysql_alias": mysql_instance_id,
        "mysql_tarball_path": install_file,
        "loose_io_flush_param_check": "1",
        "install_standard": "uguard_semi_sync",
        "init_data": "",
        "create_extranet_root": "1",
        "extranet_root_privilege": "ALL PRIVILEGES ON *.*\nPROXY ON \"@\"",
        "mysql_root_init_password": "@123qwerTYUIOP",
        "mysql_base_path": mysql_dir + "base/" + version,
        "mysql_data_path": mysql_dir + "data/" + port,
        "mysql_binlog_path": mysql_dir + "log/binlog/" + port,
        "mysql_relaylog_path": mysql_dir + "log/relaylog/" + port,
        "mysql_redolog_path": mysql_dir + "log/redolog/" + port,
        "mysql_tmp_path": mysql_dir + "tmp/" + port,
        "backup_path": mysql_dir + "backup/" + port,
        "mycnf_path": mysql_dir + "etc/" + port + "/my.cnf",
        "version": version,
        "user_type": "single_user",
        "all_user": "universe_op",
        "all_host": "%",
        "all_password": "bupYE@-00",
        "all_privilege":
            "lock tables, process, reload, replication client, super, usage on *.*\nreplication slave, replication client on *.*\nshow databases, show view, update, super, create temporary tables, trigger, create view, alter routine, create routine, execute, file, create tablespace, create user, create, drop, grant option, lock tables, references, event, alter, delete, index, insert, select, usage on *.*\ncreate,select,insert,update,delete on universe.*\nselect on universe.*\nsuper on *.*\nsuper on *.*\nprocess on *.*\nreload on *.*\nreplication client on *.*\nsuper on *.*\nselect on performance_schema.*\nselect on mysql.*\nselect, execute on sys.*\nprocess on *.*\nevent on *.*\n",
        "run_user": "actiontech-mysql",
        "run_user_group": "",
        "mysql_uid": "",
        "mysql_gid": "",
        "mycnf_server_id": str(randint(1, 4294967295)),
        "umask": "0640",
        "umask_dir": "0750",
        "mycnf_config": mycnf
    }

    mycnf = api_post(context, context.version_3 + "/database/apply_my_cnf", install_params)
    install_params["mycnf_config"] = mycnf
    install_params["is_sync"] = True
    install_params["tag_list"] = "[]"

    api_request_post(context, context.version_3 + "/database/add_instance", install_params)


def get_mysql_installation_file(context):
    return get_installation_file(context, "mysql-5.7.21")


@when(u'I add off-standard MySQL slave in the MySQL group')
def step_impl(context):
    assert context.mysql_group != None

    mysql_group_id = context.mysql_group["mysql_group_id"]
    mysql_master = get_mysql_master_in_group(context, mysql_group_id)

    context.execute_steps(u"""
			When I found a server with components ustats,udeploy,uguard-agent,urman-agent, except {server}
		""".format(server=mysql_master["server_id"]))

    resp = api_get(context, context.version_3 + "/support/init_data", {
        "group_id": mysql_group_id,
    })
    assert len(resp) > 0
    init_data = resp[-1]["name"]

    mysql_instance_id = "mysql-" + generate_id()
    port = mysql_master["mysql_instance_port"]
    install_file = get_mysql_installation_file(context)
    version = re.match(r".*(\d+\.\d+\.\d+).*", install_file).group(1)
    main_version = re.match(r"(\d+\.\d+)\.\d+", version).group(1)

    mycnf = mysql_master["mysql_instance_mycnf"]

    install_params = {
        "server_id": context.server["server_id"],
        "group_id": context.mysql_group["mysql_group_id"],
        "port": port,
        "mysql_id": mysql_instance_id,
        "mysql_alias": mysql_instance_id,
        "mysql_tarball_path": install_file,
        "loose_io_flush_param_check": "1",
        "install_standard": "uguard_semi_sync",
        "init_data": init_data,
        "extranet_root_privilege": "",
        "mysql_base_path": mysql_master["mysql_instance_base_path"],
        "mysql_data_path": mysql_master["mysql_instance_data_path"],
        "mysql_binlog_path": mysql_master["mysql_instance_binlog_path"],
        "mysql_relaylog_path": mysql_master["mysql_instance_relaylog_path"],
        "mysql_redolog_path": mysql_master["mysql_instance_redolog_path"],
        "mysql_tmp_path": mysql_master["mysql_instance_tmp_path"],
        "backup_path": mysql_master["mysql_instance_backup_path"],
        "mycnf_path": mysql_master["mysql_instance_mycnf_path"],
        "version": version,
        "user_type": "single_user",
        "run_user": "actiontech-mysql",
        "run_user_group": "",
        "mysql_uid": "",
        "mysql_gid": "",
        "mycnf_server_id": str(randint(1, 4294967295)),
        "umask": "0640",
        "umask_dir": "0750",
        "mycnf_config": mycnf
    }

    mycnf = api_post(context, context.version_3 + "/database/apply_my_cnf", install_params)
    install_params["mycnf_config"] = mycnf
    install_params["is_sync"] = True
    install_params["tag_list"] = "[]"

    api_request_post(context, context.version_3 + "/database/add_instance", install_params)


@when(u'I add MySQL slave in the MySQL group')
def step_impl(context):
    assert context.mysql_group != None

    mysql_group_id = context.mysql_group["mysql_group_id"]
    mysql_master = get_mysql_master_in_group(context, mysql_group_id)

    context.execute_steps(u"""
			When I found a server with components ustats,udeploy,uguard-agent,urman-agent, except {server}
		""".format(server=mysql_master["server_id"]))

    resp = api_get(context, context.version_3 + "/support/init_data", {
        "group_id": mysql_group_id,
    })
    assert len(resp) > 0
    init_data = resp[-1]["name"]

    mysql_instance_id = "mysql-" + generate_id()
    port = mysql_master["mysql_instance_port"]
    install_file = get_mysql_installation_file(context)
    version = re.match(r".*(\d+\.\d+\.\d+).*", install_file).group(1)
    main_version = re.match(r"(\d+\.\d+)\.\d+", version).group(1)

    mycnf = mysql_master["mysql_instance_mycnf"]

    install_params = {
        "server_id": context.server["server_id"],
        "group_id": context.mysql_group["mysql_group_id"],
        "port": port,
        "mysql_id": mysql_instance_id,
        "mysql_alias": mysql_instance_id,
        "mysql_tarball_path": install_file,
        "install_standard": "uguard_semi_sync",
        "init_data": init_data,
        "extranet_root_privilege": "",
        "mysql_base_path": mysql_master["mysql_instance_base_path"],
        "mysql_data_path": mysql_master["mysql_instance_data_path"],
        "mysql_binlog_path": mysql_master["mysql_instance_binlog_path"],
        "mysql_relaylog_path": mysql_master["mysql_instance_relaylog_path"],
        "mysql_redolog_path": mysql_master["mysql_instance_redolog_path"],
        "mysql_tmp_path": mysql_master["mysql_instance_tmp_path"],
        "backup_path": mysql_master["mysql_instance_backup_path"],
        "mycnf_path": mysql_master["mysql_instance_mycnf_path"],
        "version": version,
        "user_type": "single_user",
        "run_user": "actiontech-mysql",
        "run_user_group": "",
        "mysql_uid": "",
        "mysql_gid": "",
        "mycnf_server_id": str(randint(1, 4294967295)),
        "umask": "0640",
        "umask_dir": "0750",
        "mycnf_config": mycnf
    }

    mycnf = api_post(context, context.version_3 + "/database/apply_my_cnf", install_params)
    install_params["mycnf_config"] = mycnf
    install_params["is_sync"] = True
    install_params["tag_list"] = "[]"

    api_request_post(context, context.version_3 + "/database/add_instance", install_params)


@when(u'I takeover MySQL instance')
def step_imp(context):
    assert context.mysql_group != None
    assert context.mysql_instance != None
    mysql_instance_id = "mysql-" + generate_id()
    passwd = get_master_root_password(context)

    body = {
        "server_id": context.mysql_instance['server_id'],
        "group_id": context.mysql_instance['mysql_group_id'],
        "port": context.mysql_instance['mysql_instance_port'],
        "mysql_id": mysql_instance_id,
        "mysql_alias": mysql_instance_id,
        "mysql_tarball_path": context.mysql_instance['mysql_instance_tarball_path'],
        "install_standard": "uguard_semi_sync",
        "mysql_user": "root",
        "mysql_password": passwd,
        "mysql_connect_type": "socket",
        "mysql_socket_path":
            context.mysql_instance['mysql_instance_data_path'] + "/mysqld.sock",
        "backup_path": context.mysql_instance['mysql_instance_backup_path'],
        "mycnf_path": context.mysql_instance['mysql_instance_mycnf_path'],
        "version": context.mysql_instance['mysql_instance_version'],
        "user_type": "single_user",
        "run_user": context.mysql_instance['mysql_instance_run_user'],
        "run_user_group": "",
        "mysql_uid": "",
        "mysql_gid": "",
        "umask": "0640",
        "umask_dir": "0750",
        "tag_list": "[]",
        "resource": "0"
    }
    api_request_post(context, context.version_3 + "/database/takeover_instance", body)
    context.mysql_instance_id = mysql_instance_id


@when(u'I add MySQL {count:int} slave in the MySQL group')
def step_impl(context, count):
    assert context.mysql_group != None

    mysql_group_id = context.mysql_group["mysql_group_id"]
    mysql_master = get_mysql_master_in_group(context, mysql_group_id)
    resp = get_group_info_by_id(context, mysql_group_id)
    match = pyjq.all('.[] | select(."server_id")', resp)
    server_ids = ""
    for temp in match:
        server_ids = temp['server_id'] + "," + server_ids
    context.execute_steps(u"""
    When I found a server with components ustats,udeploy,uguard-agent,urman-agent, except {server}
                    """.format(server=server_ids))

    resp = api_get(context, context.version_3 + "/support/init_data", {
        "group_id": mysql_group_id,
    })
    assert len(resp) > 0
    init_data = resp[-1]["name"]

    mysql_instance_id = "mysql-" + generate_id()
    port = mysql_master["mysql_instance_port"]
    install_file = get_mysql_installation_file(context)
    version = re.match(r".*(\d+\.\d+\.\d+).*", install_file).group(1)
    main_version = re.match(r"(\d+\.\d+)\.\d+", version).group(1)

    mycnf = mysql_master["mysql_instance_mycnf"]

    install_params = {
        "server_id": context.server["server_id"],
        "group_id": context.mysql_group["mysql_group_id"],
        "port": port,
        "mysql_id": mysql_instance_id,
        "mysql_alias": mysql_instance_id,
        "mysql_tarball_path": install_file,
        "install_standard": "uguard_semi_sync",
        "init_data": init_data,
        "extranet_root_privilege": "",
        "mysql_base_path": mysql_master["mysql_instance_base_path"],
        "mysql_data_path": mysql_master["mysql_instance_data_path"],
        "mysql_binlog_path": mysql_master["mysql_instance_binlog_path"],
        "mysql_relaylog_path": mysql_master["mysql_instance_relaylog_path"],
        "mysql_redolog_path": mysql_master["mysql_instance_redolog_path"],
        "mysql_tmp_path": mysql_master["mysql_instance_tmp_path "],
        "backup_path": mysql_master["mysql_instance_backup_path "],
        "mycnf_path": mysql_master["mysql_instance_mycnf_path "],
        "version": version,
        "user_type": "single_user",
        "run_user": "actiontech-mysql",
        "run_user_group": "",
        "mysql_uid": "",
        "mysql_gid": "",
        "mycnf_server_id": str(randint(1, 4294967295)),
        "umask": "0640",
        "umask_dir": "0750",
        "mycnf_config": mycnf
    }

    mycnf = api_post(context, context.version_3 + "/database/apply_my_cnf", install_params)
    install_params["mycnf_config"] = mycnf
    install_params["is_sync"] = True
    install_params["tag_list"] = "[]"

    api_request_post(context, context.version_3 + "/database/add_instance", install_params)


@then(
    u'the MySQL group should have {expect_count:int} running MySQL instance in {duration:time}'
)
def step_impl(context, expect_count, duration):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group["mysql_group_id"])
    data = resp
    assert len(data) == expect_count

    for i in range(1, duration * context.time_weight * 10):
        resp = get_mysql_info_in_group(context, context.mysql_group["mysql_group_id"])
        condition = '.[] | select(."mysql_instance_status" != "STATUS_MYSQL_HEALTH_OK")'
        match = pyjq.first(condition, resp)
        if match == None:
            return
        time.sleep(0.1)
    assert False


@when(u'I found a MySQL master in the MySQL group')
def step_impl(context):
    assert context.mysql_group != None
    match = get_mysql_master_in_group(context, context.mysql_group["mysql_group_id"])
    assert match != None
    context.mysql_instance = match


def get_mysql_master_in_group(context, group_id):
    resp = get_mysql_info_in_group(context, group_id)
    match = pyjq.first('.[] | select(."mysql_instance_role" == "STATUS_MYSQL_MASTER")',
                       resp)
    return match


@when(u'I found a {master_slave:string} MySQL\'s instance in the MySQL group')
def step_impl(context, master_slave):
    assert context.mysql_group != None
    match = get_instance_in_group(context, context.mysql_group[0]["mysql_group_id"], master_slave)
    assert match != None
    context.mysql_instance = match


def get_instance_in_group(context, group_id, master_slave):
    resp = get_mysql_info_in_group(context, group_id)
    match = None
    if master_slave == 'master':
        match = pyjq.first('.[] | select(."mysql_instance_role" == "STATUS_MYSQL_MASTER")', resp)
    elif master_slave == 'slave':
        match = pyjq.first('.[] | select(."mysql_instance_role" == "STATUS_MYSQL_SLAVE")', resp)
    return match


@when(u'I make a manual backup on the MySQL instance')
def step_impl(context):
    assert context.mysql_instance != None
    resp = api_get(context, context.version_3 + "/urman_backupset/list", {
        "instance": context.mysql_instance["mysql_instance_id"],
    })
    origin_id = pyjq.first('.data[] | .backup_set_id', resp)
    context.origin_id = origin_id
    cnf = api_get(context, context.version_3 + "/support/read_umc_file", {
        "path": "backupcnfs/backup.xtrabackup",
    })

    api_request_post(
        context, context.version_3 + "/database/manual_backup", {
            "is_sync": True,
            "mysql_id": context.mysql_instance["mysql_instance_id"],
            "backup_tool": "Xtrabackup",
            "backup_cnf": cnf,
        })


@when(u'I enable HA on all MySQL instance in the MySQL group')
def step_impl(context):
    assert context.mysql_group != None

    mysql_group_id = context.mysql_group["mysql_group_id"]
    resp = get_mysql_info_in_group(context, mysql_group_id)

    for inst in resp:
        api_post(
            context, context.version_3 + "/database/start_mysql_ha_enable", {
                "is_sync": True,
                "group_id": mysql_group_id,
                "mysql_id": inst["mysql_instance_id"],
                "server_id": inst['server_id']
            })


@then(
    u'the MySQL group should have {master_count:int} running MySQL master and {slave_count:int} running MySQL slave in {duration:time}'
)
def step_impl(context, master_count, slave_count, duration):
    assert context.mysql_group != None

    for i in range(1, duration * context.time_weight * 10):
        resp = get_mysql_info_in_group(context, context.mysql_group["mysql_group_id"])
        condition = '.[] | select(."mysql_instance_status" == "STATUS_MYSQL_HEALTH_OK")'
        masters = pyjq.all(
            condition + ' | select(."mysql_instance_role" == "STATUS_MYSQL_MASTER")', resp)
        slaves = pyjq.all(
            condition + ' | select(."mysql_instance_role" == "STATUS_MYSQL_SLAVE")', resp)
        if len(masters) == 1 and len(slaves) == slave_count:
            return
        time.sleep(0.1)
    assert False


@when(u'I remove MySQL instance')
def step_impl(context):
    assert context.mysql_instance != None

    body = {
        "mysql_id": context.mysql_instance['mysql_instance_id'],
        "server_id": context.mysql_instance['server_id'],
        "group_id": context.mysql_instance['mysql_group_id'],
        "force": "1",
        "is_sync": True,
    }
    api_request_post(context, context.version_3 + "/database/delete_instance", body)


@then(
    u'the MySQL instance list should not contains the MySQL instance'
)
def step_impl(context):
    assert context.mysql_instance != None
    mysql_instance_id = context.mysql_instance["mysql_instance_id"]
    resp = get_all_mysql_info(context)
    match = pyjq.first('.| any(."mysql_instance_id" == "{0}")'.format(mysql_instance_id),
                       resp)
    assert match is not True


@when(u'I enable the MySQL instance HA')
def step_impl(context):
    assert context.mysql_instance != None
    body = {
        "server_id": context.mysql_instance['server_id'],
        "group_id": context.mysql_instance['mysql_group_id'],
        "mysql_id": context.mysql_instance['mysql_instance_id'],
        "is_sync": True
    }
    api_request_post(context, context.version_3 + "/database/start_mysql_ha_enable", body)


@then(u'MySQL instance HA status should be running in {duration:time}')
def step_imp(context, duration):
    assert context.mysql_instance != None

    def condition(context, flag):
        mysql_instance_id = context.mysql_instance["mysql_instance_id"]
        resp = get_all_mysql_info(context)
        match = pyjq.first(
            '.[] | select(."mysql_instance_id" == "{0}")'.format(mysql_instance_id), resp)
        if match is not None and match[
            'uguard_status'] == "UGUARD_ENABLE" and match[
            'mysql_instance_status'] == "STATUS_MYSQL_HEALTH_OK":
            return True

    waitfor(context, condition, duration)


@when(u'I configure MySQL group SIP')
def step_imp(context):
    assert context.mysql_group != None
    assert context.valid_sip != None
    body = {
        "group_id": context.mysql_group['mysql_group_id'],
        "sip": context.valid_sip
    }
    api_request_post(context, context.version_3 + "/database/update_mysql_sip", body)


@when(u'I configure MySQL groups SIP')
def step_imp(context):
    assert context.mysql_group != None
    assert context.valid_sip != None
    body = {
        "group_id": context.mysql_group[0]['mysql_group_id'],
        "sip": context.valid_sip
    }
    api_request_post(context, context.version_3 + "/database/update_mysql_sip", body)


@then(u'update MySQL group SIP successful in {duration:time}')
def step_imp(context, duration):
    assert context.mysql_group != None
    assert context.valid_sip != None
    mysql_group_id = context.mysql_group["mysql_group_id"]

    def condition(context, flag):
        resp = get_all_group_info(context)
        match = pyjq.first(
            '.[] | select(.mysql_group_id == "{0}")'.format(mysql_group_id), resp)
        if "mysql_group_sip" not in match:
            return
        if match is not None and context.valid_sip == match['mysql_group_sip']:
            return True

    waitfor(context, condition, duration)


@then(u'update MySQL groups SIP successful in {duration:time}')
def step_imp(context, duration):
    assert context.mysql_group != None
    assert context.valid_sip != None
    mysql_group_id = context.mysql_group[0]["mysql_group_id"]

    def condition(context, flag):
        resp = get_all_group_info(context)
        match = pyjq.first(
            '.[] | select(.mysql_group_id == "{0}")'.format(mysql_group_id), resp)
        if "mysql_group_sip" not in match:
            return
        if match is not None and context.valid_sip == match['mysql_group_sip']:
            return True

    waitfor(context, condition, duration)
    time.sleep(6)


@when(u'I stop MySQL instance ha enable')
def step_impl(context):
    assert context.mysql_instance != None
    body = {
        "server_id": context.mysql_instance['server_id'],
        "group_id": context.mysql_instance['mysql_group_id'],
        "mysql_id": context.mysql_instance['mysql_instance_id'],
        "is_sync": True
    }
    api_request_post(context, context.version_3 + "/database/stop_mysql_ha_enable", body)


@then(u'MySQL instance ha enable should stopped in {duration:time}')
def step_imp(context, duration):
    assert context.mysql_instance != None

    def condition(context, flag):
        mysql_instance_id = context.mysql_instance["mysql_instance_id"]
        resp = get_all_mysql_info(context)
        match = pyjq.first(
            '.[] | select(."mysql_instance_id" == "{0}")'.format(mysql_instance_id), resp)
        if match is not None and match['uguard_status'] == "MANUAL_EXCLUDE_HA":
            return True

    waitfor(context, condition, duration)


@when(u'I found a running MySQL instance and uguard enable,or I skip the test')
def step_impl(context):
    resp = get_all_group_info(context)
    match = pyjq.first('.[] | select(.mysql_group_instance_nums == "1")', resp)
    if match is None:
        context.scenario.skip("Found no MySQL instance")
        return
    mysqls = api_get(context, context.version_3 + "/database/list_instance", {
        "number": context.page_size_to_select_all,
    })
    mysql = pyjq.first(
        '.[] | select(.mysql_instance_status == "STATUS_MYSQL_HEALTH_OK" and .uguard_status == "UGUARD_ENABLE" and .mysql_group_id == "{0}" )'
            .format(match['mysql_group_id']), mysqls)
    if mysql is None:
        context.scenario.skip("Found no MySQL instance UGUARD_ENABLE")
        return
    else:
        root_password = api_get(context, context.version_3 + "/helper/get_mysql_password", {
            "mysql_id": mysql["mysql_instance_id"],
            "password_type": "ROOT",
        })
        mysql["root_password"] = root_password
        context.mysql_instance = mysql


@when(u'I stop MySQL service')
def step_imp(context):
    assert context.mysql_instance != None
    body = {
        "server_id": context.mysql_instance['server_id'],
        "mysql_id": context.mysql_instance['mysql_instance_id'],
        "is_sync": True,
    }
    api_request_post(context, context.version_3 + "/database/stop_mysql_service", body)


@then(u'stop MySQL service should succeed in {duration:time}')
def step_imp(context, duration):
    assert context.mysql_instance != None

    def condition(context, flag):
        resp = get_all_mysql_info(context)
        match = pyjq.first(
            '.[] | select(.mysql_instance_status == "STATUS_MYSQL_HEALTH_BAD")',
            resp)
        if match is not None:
            return True

    waitfor(context, condition, duration)


@when(u'I reset database instance')
def step_imp(context):
    assert context.mysql_instance != None
    resp = api_get(context, context.version_3 + "/support/init_data", {
        "group_id": context.mysql_instance['mysql_group_id'],
    })
    assert len(resp) > 0
    init_data = resp[-1]["name"]
    body = {
        "server_id": context.mysql_instance['server_id'],
        "mysql_id": context.mysql_instance['mysql_instance_id'],
        "origin_data": init_data,
        "is_sync": True,
    }
    api_request_post(context, context.version_3 + "/database/reset_database_instance", body)


@then(u'reset database instance should succeed in {duration:time}')
def step_imp(context, duration):
    assert context.mysql_instance != None

    def condition(context, flag):
        resp = get_all_mysql_info(context)
        match = pyjq.first(
            '.[] | select(.mysql_instance_status == "STATUS_MYSQL_HEALTH_OK" '
            'and ."mysql_instance_id" == "{0}")'.format(
                context.mysql_instance['mysql_instance_id']), resp)
        if match is not None:
            return True

    waitfor(context, condition, duration)


@when(
    u'I found {count:int} MySQL group{s:s?} with MySQL HA instances, or I skip the test'
)
def step_imp(context, count, s):
    res = get_all_group_info(context)
    matches = pyjq.all(
        '.[] | select(.mysql_group_uguard_status == "UGUARD_PRIMARY_SLAVE_ENABLE")',
        res)
    if matches is None:
        context.scenario.skip("Found no MySQL group with MySQL HA instance")
        return
    if len(matches) < count:
        context.scenario.skip(
            "Found no enough MySQL groups with MySQL HA instance")
        return
    if count == 1:
        context.mysql_group = matches
    else:
        context.mysql_groups = matches[:count]


@when(u'I promote slave instance to master')
def step_imp(context):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    the_slave = pyjq.first('.[]|select(."mysql_instance_role" == "STATUS_MYSQL_SLAVE")',
                           resp)
    body = {
        "mysql_id": the_slave['mysql_instance_id'],
        "is_sync": True
    }
    api_request_post(context, context.version_3 + "/database/promote_to_master", body)
    context.slave_instance = the_slave


@then(u'promote slave instance to master should succeed in {duration:time}')
def step_imp(context, duration):
    assert context.mysql_group != None

    def condition(context, flag):
        resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
        condition = '.[] | select(."mysql_instance_status" == "STATUS_MYSQL_HEALTH_OK" and ."mysql_instance_sip" == "(SIP)")'
        masters = pyjq.all(
            condition +
            ' | select(."mysql_instance_role" == "STATUS_MYSQL_MASTER" and ."mysql_instance_id" =="{0}")'
            .format(context.slave_instance['mysql_instance_id']), resp)

        if len(masters) == 1:
            return True

    waitfor(context, condition, duration)


@when(u'I query the slave instance "{query}"')
def step_impl(context, query):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    the_slave = pyjq.first('.[]|select(."mysql_instance_role" == "STATUS_MYSQL_SLAVE")',
                           resp)
    master = pyjq.first('.[]|select(."mysql_instance_role" == "STATUS_MYSQL_MASTER")',
                        resp)

    master["root_password"] = get_mysql_instance_root_password(
        context, master["mysql_instance_id"])

    resp = api_get(
        context, context.version_3 + "/helper/query_mysql", {
            "mysql_id": the_slave["mysql_instance_id"],
            "query": query,
            "user": "root",
            "password": master["root_password"],
        })
    context.mysql_resp = resp


@when(u'I execute the MySQL instance "{option}"')
def step_impl(context, option):
    assert context.mysql_instance != None
    mysql = context.mysql_instance
    password = get_mysql_instance_root_password(context, mysql["mysql_instance_id"])
    resp = api_get(
        context, context.version_3 + "/helper/query_mysql", {
            "mysql_id": mysql["mysql_instance_id"],
            "query": option,
            "user": "root",
            "password": password,
        })


@when(u'I bind SLA protocol to the MySQL group')
def step_imp(context):
    assert context.mysql_instance != None
    body = {
        "group_id": context.mysql_instance['mysql_group_id'],
        "add_sla_template": "SLA_RPO_sample",
        "is_sync": True,
    }
    api_request_post(context, context.version_3 + "/database/add_sla_protocol", body)


@then(u'SLA protocol of the MySQL group should be binded')
def step_imp(context):
    assert context.mysql_instance != None
    res = get_all_group_info(context)
    match = pyjq.first(
        '.[] | select(.mysql_group_id == "{0}")'.format(
            context.mysql_instance["mysql_group_id"]), res)

    if match is not None and match['mysql_group_sla_template'] == "SLA_RPO_sample":
        return True
    else:
        assert False


@when(u'I enable the SLA protocol of the MySQL group')
def step_imp(context):
    assert context.mysql_instance != None
    api_request_post(context, context.version_3 + "/database/start_sla_protocol", {
        "group_id": context.mysql_instance['mysql_group_id'],
        "is_sync": True,
    })


@then(u'SLA protocol should started')
def step_imp(context):
    assert context.mysql_instance != None
    res = get_all_group_info(context)
    match = pyjq.first(
        '.[] | select(.mysql_group_id == "{0}")'.format(
            context.mysql_instance["mysql_group_id"]), res)
    if match['mysql_group_sla_enable'] == "ENABLE":
        return
    assert False


def get_mysql_group_brief(context, group_id):
    resp = get_mysql_info_in_group(context, group_id)
    master = pyjq.first('.[] | select(.mysql_instance_role == "STATUS_MYSQL_MASTER")',
                        resp)
    assert master is not None
    root_password = get_mysql_instance_root_password(context,
                                                     master["mysql_instance_id"])
    slave = pyjq.first('.[] | select(.mysql_instance_role == "STATUS_MYSQL_SLAVE")', resp)
    assert slave is not None

    return {
        "group_id": group_id,
        "master_id": master["mysql_instance_id"],
        "master_addr": master["server_address"] + ":" + master["mysql_instance_port"],
        "slave_id": slave["mysql_instance_id"],
        "slave_addr": slave["server_address"] + ":" + slave["mysql_instance_port"],
        "root_password": root_password
    }


@when(u'I kill three master pid')
def step_imp(context):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    master = pyjq.first('.[]|select(."mysql_instance_role" == "STATUS_MYSQL_MASTER")',
                        resp)
    for i in range(1, 4):
        api_request_post(context, context.version_3 + "/helper/kill_mysql_process", {
            "mysql_id": master['mysql_instance_id'],
            "is_sync": True
        })
        time.sleep(5)

    context.master_info = master
    context.start_time = time.time()


@when(u'I kill {count:int} times {master_slave:string} mysql instance pid')
def step_imp(context, count, master_slave):
    assert context.mysql_instance != None
    for i in range(0, count):
        api_request_post(context, context.version_3 + "/helper/kill_mysql_process", {
            "mysql_id": context.mysql_instance['mysql_instance_id'],
            "is_sync": True
        })


@then(u"master-slave switching in {duration:time}")
def step_imp(context, duration):
    def condition(context, flag):
        resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
        master = pyjq.first(
            '.data[]|select(."mysql_instance_role" == "STATUS_MYSQL_MASTER" and ."mysql_instance_replication_status" == "STATUS_MYSQL_REPL_EMPTY" and ."mysql_instance_sip" == "(SIP)")',
            resp)
        if master is not None and master['mysql_instance_id'] != context.master_info['mysql_instance_id']:
            return True

    waitfor(context, condition, duration)


@when(u'I found alert code {code:string}, or I skip the test')
def step_imp(context, code):
    resp = api_get(context, context.version_3 + "/alert_record/list_search", {
        'order_by': 'timestamp',
        'ascending': 'false',
    })

    alert_info = pyjq.first('.data[]|select(."code" == {0})'.format(code), resp)
    if alert_info is not None:
        context.scenario.skip("Found alert code")
        return
    else:
        assert True


@then(u'expect alert code {code:string} in {duration:time}')
def step_imp(context, code, duration):
    def condition(context, flag):
        resp = api_get(context, context.version_3 + "/alert_record/list_search", {
            'order_by': 'timestamp',
            'number ': context.page_size_to_select_all,
            'ascending': 'false',
        })

        alert_info = pyjq.first('.data[]|select(."code" == {0})'.format(code),
                                resp)
        if alert_info is not None and context.master_info[
            'server_id'] == alert_info['server']:
            return True

    waitfor(context, condition, duration)


@when(u'I create MySQL user "{user}" and grants "{grants}"')
def step_imp(context, user, grants):
    assert context.mysql_instance != None
    mysql = context.mysql_instance
    api_request_post(
        context, context.version_3 + "/database/create_mysql_user", {
            "group_id": mysql['mysql_group_id'],
            "admin_user": "root",
            "admin_password": mysql["root_password"],
            "mysql_connect_type": "socket",
            "master_instance": mysql['mysql_instance_id'],
            "user": user,
            "user_host": "%",
            "password": "@123qwerTYUIOP",
            "grants": grants,
            "is_sync": True
        })


@when(u'I update MySQL user "{user}" and password "{password}"')
def step_imp(context, user, password):
    assert context.mysql_instance != None
    mysql = context.mysql_instance
    context.update_password = password
    api_request_post(
        context, context.version_3 + "/database/update_mysql_user_password", {
            "group_id": mysql['mysql_group_id'],
            "admin_user": "root",
            "admin_password": mysql["root_password"],
            "mysql_connect_type": "socket",
            "master_instance": mysql['mysql_instance_id'],
            "user": user,
            "user_host": "%",
            "update_password": password,
            "is_sync": True
        })


@when(u'I query the MySQL instance use user "{user}" "{query:any}"')
def step_imp(context, query, user):
    assert context.mysql_instance != None
    mysql = context.mysql_instance
    password = context.update_password
    resp = api_get(
        context, context.version_3 + "/helper/query_mysql", {
            "mysql_id": mysql["mysql_instance_id"],
            "query": query,
            "user": user,
            "password": password,
        })
    context.mysql_resp = resp


@when(u'I detach MySQL instance')
def step_imp(context):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    slave_info = pyjq.first(
        '.[] | select(.mysql_instance_role == "STATUS_MYSQL_SLAVE" and .mysql_instance_installation_standard == "uguard_semi_sync")',
        resp)
    assert slave_info is not None
    context.mysql_instance = slave_info
    context.execute_steps(u"""
        When I stop MySQL instance ha enable
        Then the response is ok
        And MySQL instance ha enable should stopped in 2m
                          """)
    api_request_post(
        context, context.version_3 + "/database/detach_instance", {
            "mysql_id": context.mysql_instance['mysql_instance_id'],
            "server_id": context.mysql_instance['server_id'],
            "group_id": context.mysql_instance['mysql_group_id'],
            "force": True,
            "is_sync": True
        })


@then(u'the MySQL instance should be not exist')
def step_imp(context):
    assert context.mysql_group != None
    assert context.mysql_instance != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    match = pyjq.first(
        '. | any(."mysql_instance_id" == "{0}")'.format(
            context.mysql_instance['mysql_instance_id']), resp)
    if match is not True:
        return
    else:
        assert False


def get_master_root_password(context):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    master_info = pyjq.first('.[] | select(.mysql_instance_role == "STATUS_MYSQL_MASTER")',
                             resp)
    assert master_info is not None
    root_password = api_get(context, context.version_3 + "/helper/get_mysql_password", {
        "mysql_id": master_info["mysql_instance_id"],
        "password_type": "ROOT",
    })
    return root_password


@then(u'the MySQL instance should be listed')
def step_imp(context):
    assert context.mysql_group != None
    res = get_all_group_info(context)
    match = pyjq.first(
        '.[] | select(.mysql_group_instance_nums == "2" and ."mysql_group_id" == "{0}")'.
            format(context.mysql_instance["mysql_group_id"]), res)
    if match is not None:
        resp = get_mysql_info_in_group(context, context.mysql_instance["mysql_group_id"])
        res = pyjq.first(
            '.|any(."mysql_instance_status" == "STATUS_MYSQL_HEALTH_BAD")', resp)
        if res is not True:
            return
        else:
            assert False
    results = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    context.mysql_instance = pyjq.first(
        '.[] | select(."uguard_status" == "UGUARD_DISABLE")', results)


@when(u'I exclude ha MySQL instance')
def step_imp(context):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    slave = pyjq.first('.[] | select(.mysql_instance_role == "STATUS_MYSQL_SLAVE")', resp)
    assert slave is not None
    context.mysql_instance = slave
    context.execute_steps(u"""
    When I stop MySQL instance ha enable
    """)


@then(
    u'expect alert code {code:string} and detail "{detail}" in {duration:time}')
def step_imp(context, code, detail, duration):
    def condition(context, flag):
        resp = api_get(context, context.version_3 + "/alert_record/list_search", {
            'order_by': 'timestamp',
            'ascending': 'false',
        })
        alert_info = pyjq.first('.data[]|select(."code" == {0})'.format(code),
                                resp)
        if alert_info is not None and detail in alert_info['detail']:
            return True

    waitfor(context, condition, duration)


@then(u'group sla level {level:string} in {duration:time}')
def step_imp(context, level, duration):
    assert context.mysql_group != None

    def condition(context, flag):
        res = get_all_group_info(context)
        match = pyjq.first(
            '.[] | select(.mysql_group_id == "{0}")'.format(
                context.mysql_group[0]["mysql_group_id"]), res)
        if match is not None and "mysql_group_sla_level" not in match:
            return
        if match['mysql_group_sla_level'] == level:
            return True

    waitfor(context, condition, duration)


@when(u'I remove the group SLA protocol')
def step_imp(context):
    assert context.mysql_group != None
    body = {
        "group_id": context.mysql_group[0]["mysql_group_id"],
        "is_sync": True
    }
    api_request_post(context, context.version_3 + "/database/remove_sla_protocol", body)


@when(u'I pause the group SLA protocol')
def step_imp(context):
    assert context.mysql_group != None
    body = {
        "group_id": context.mysql_group[0]["mysql_group_id"],
        "is_sync": True
    }
    api_request_post(context, context.version_3 + "/database/pause_sla_protocol", body)


@then(u'the group SLA protocol should paused in {duration:time}')
def step_imp(context, duration):
    assert context.mysql_group != None

    def condition(context, flag):
        res = get_all_group_info(context)
        match = pyjq.first(
            '.[] | select(.mysql_group_id == "{0}")'.format(
                context.mysql_group[0]["mysql_group_id"]), res)
        assert match is not None
        if match['mysql_group_sla_enable'] == "DISABLE":
            return True

    waitfor(context, condition, duration)


@then(u'the group SLA protocol should remove succeed in {duration:time}')
def step_imp(context, duration):
    assert context.mysql_group != None

    def condition(context, flag):
        res = get_all_group_info(context)
        match = pyjq.first(
            '.[] | select(.mysql_group_id == "{0}")'.format(
                context.mysql_group[0]["mysql_group_id"]), res)
        if match is not None and 'mysql_group_sla_template' not in match:
            return True

    waitfor(context, condition, duration)


@when(u'I add the ip to sip pool')
def step_imp(context):
    assert context.sips != None
    for sip in context.sips:
        api_request_post(context, context.version_3 + "/sippool/add", {
            "sip": sip,
            "is_sync": True
        })


@when(u'I action {action:string} MySQL instance component {component:string}')
def step_imp(context, action, component):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    slave = pyjq.first('.[] | select(.mysql_instance_role == "STATUS_MYSQL_SLAVE")', resp)
    assert slave is not None
    context.mysql_instance = slave
    if action.lower() == "pause":
        context.execute_steps(u"""
        When I pause component {0}
            """.format(component))
    else:
        context.execute_steps(u"""
    	When I start component {0}
    	    """.format(component))


@when(u'I pause component {component:string}')
def step_imp(context, component):
    assert context.mysql_instance != None
    api_request_post(
        context, context.version_3 + "/server/pause", {
            "server_id": context.mysql_instance['server_id'],
            "component": component,
            "is_sync": True
        })


@when(u'I start component {component:string}')
def step_imp(context, component):
    assert context.mysql_instance != None
    api_request_post(
        context, context.version_3 + "/server/start", {
            "server_id": context.mysql_instance['server_id'],
            "component": component,
            "is_sync": True
        })


@then(
    u'action {action:string} MySQL instance component {component:string} should succeed in {duration:time}'
)
def step_imp(context, action, component, duration):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    slave = pyjq.first('.[] | select(.mysql_instance_role == "STATUS_MYSQL_SLAVE")', resp)
    assert slave is not None
    context.mysql_instance = slave
    component_status = component + "_status"
    if action.lower() == "pause":

        def condition(context, flag):
            resp = get_all_server_info(context)
            match = pyjq.first(
                '.[] | select(."server_id" == "{0}")'.format(
                    slave['server_id']), resp)
            if match is not None and match["{0}".format(
                    component_status)] == "STATUS_STOPPED":
                return True

        waitfor(context, condition, duration)

    else:

        def condition(context, flag):
            resp = get_all_server_info(context)
            match = pyjq.first(
                '.[] | select(."server_id" == "{0}")'.format(
                    slave['server_id']), resp)
            if match is not None and match["{0}".format(
                    component_status)] == "STATUS_OK":
                return True

        waitfor(context, condition, duration)


@when(u'I create and insert table in master instance "{statement}"')
def step_imp(context, statement):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    mysql = pyjq.first('.[] | select(.mysql_instance_role == "STATUS_MYSQL_MASTER")', resp)
    master_root = get_mysql_instance_root_password(context, mysql['mysql_instance_id'])
    assert mysql is not None
    resp = api_get(
        context, context.version_3 + "/helper/query_mysql", {
            "mysql_id": mysql["mysql_instance_id"],
            "query": statement,
            "user": "root",
            "password": master_root,
        })


@when(
    u'I update MySQL configuration with host connect "{option:string}" to "{option_value:string}"'
)
def step_impl(context, option, option_value):
    assert context.mysql_instance != None
    mysql = context.mysql_instance

    query_resp = api_post(
        context, context.version_3 + "/modify_config/query", {
            "super_user": "root",
            "super_password": mysql["root_password"],
            "mysql_connect_type": "server_addr",
            "mysql_ids": mysql["mysql_instance_id"],
            "option": option,
            "option_value": option_value,
        })

    condition = '.[] | select(."option" == "{0}")'.format(option)
    assert len(pyjq.all(condition, query_resp)) == 1

    api_request_post(context, context.version_3 + "/modify_config/save", {
        "config": json.dumps(query_resp),
        "is_sync": True,
    })


@when(u'I action {action:string} role {role:string} on HA instance')
def step_imp(context, action, role):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    master_info = pyjq.first('.[] | select(.mysql_instance_role == "{0}")'.format(role),
                             resp)
    slave_info = pyjq.all('.[] | select(.mysql_instance_role == "{0}")'.format(role), resp)
    if action.lower() == "stop":
        if role == "STATUS_MYSQL_MASTER":
            api_request_post(
                context, context.version_3 + "/database/stop_mysql_ha_enable", {
                    "server_id": master_info['server_id'],
                    "group_id": master_info['mysql_group_id'],
                    "mysql_id": master_info['mysql_instance_id'],
                    "is_sync": True,
                })
        else:
            for slave in slave_info:
                api_request_post(
                    context, context.version_3 + "/database/stop_mysql_ha_enable", {
                        "server_id": slave['server_id'],
                        "group_id": slave['mysql_group_id'],
                        "mysql_id": slave['mysql_instance_id'],
                        "is_sync": True,
                    })
    else:
        if role == "STATUS_MYSQL_MASTER":
            api_request_post(
                context, context.version_3 + "/database/start_mysql_ha_enable", {
                    "server_id": master_info['server_id'],
                    "group_id": master_info['mysql_group_id'],
                    "mysql_id": master_info['mysql_instance_id'],
                    "is_sync": True,
                })
        else:
            for slave in slave_info:
                api_request_post(
                    context, context.version_3 + "/database/start_mysql_ha_enable", {
                        "server_id": slave['server_id'],
                        "group_id": slave['mysql_group_id'],
                        "mysql_id": slave['mysql_instance_id'],
                        "is_sync": True,
                    })


@then(u'the server uguard should running')
def step_impl(context):
    resp = get_all_server_info(context)
    condition = '.[] | select(."uguard-agent_status" and ."urman-agent_status" or ."uguard-mgr_status")'
    match = pyjq.all(condition, resp)
    assert match is not None
    for temp in match:
        if temp['uguard-agent_status'] in ["STATUS_OK", "STATUS_OK(leader)", "STATUS_OK(master)"] and \
                temp['urman-agent_status'] in ["STATUS_OK", "STATUS_OK(leader)", "STATUS_OK(master)"] or \
                temp['uguard-mgr_status'] in ["STATUS_OK", "STATUS_OK(leader)", "STATUS_OK(master)"]:
            return
        else:
            assert False


@when(u'I action {action:string} component {component:string} in server')
def step_imp(context, action, component):
    resp = get_all_server_info(context)
    com_status = component + "_status"
    server_info = pyjq.first(
        '.[] |  select(."{0}" == "STATUS_OK(master)")'.format(com_status),
        resp)
    context.server = server_info
    context.execute_steps(u"""
       When I action {0} component {1}
       """.format(action, component))


@when(u'I action {action:string} component {component:string}')
def step_imp(context, action, component):
    assert context.server != None
    server_info = context.server
    if action.lower() == "stop":
        api_request_post(
            context, context.version_3 + "/server/pause", {
                "server_id": server_info['server_id'],
                "component": component,
                "is_sync": True
            })
    else:
        api_request_post(
            context, context.version_3 + "/server/start", {
                "server_id": server_info['server_id'],
                "component": component,
                "is_sync": True
            })


@then(u'component {component:string} should stopped in {duration:time}')
def step_imp(context, component, duration):
    assert context.server != None
    com_status = component + "_status"

    def condition(context, flag):
        resp = get_all_server_info(context)
        match = pyjq.first(
            '.[] |  select(."{0}" == "STATUS_STOPPED(master)" or ."{0}" == "STATUS_STOPPED" or ."{0}" == "STATUS_STOPPED(leader)" and ."server_id" == "{1}")'
                .format(com_status, context.server['server_id']), resp)
        if match is not None:
            return True

    waitfor(context, condition, duration)


@then(u'component {component:string} should started in {duration:time}')
def step_imp(context, component, duration):
    assert context.server != None
    com_status = component + "_status"

    def condition(context, flag):
        resp = get_all_server_info(context)
        match = pyjq.first(
            '.[] |  select(."{0}" == "STATUS_OK" or ."{0}" == "STATUS_OK(master)" or ."{0}" == "STATUS_OK(leader)" and ."server_id" == "{1}")'
                .format(com_status, context.server['server_id']), resp)
        if match is not None:
            return True

    waitfor(context, condition, duration)


@when(u'I query the MySQL group "{query:any}" with sip')
def step_impl(context, query):
    assert context.mysql_group != None
    group = context.mysql_group[0]

    resp = api_get(context, context.version_3 + "/helper/mysql/query_by_sip", {
        "mysql_group_id": group["mysql_group_id"],
        "sql": query,
    })
    context.mysql_resp = resp


@when(u'I execute the MySQL group "{query:any}" with sip')
def step_impl(context, query):
    assert context.mysql_group is not None
    group = context.mysql_group[0]
    resp = api_request_get(context, context.version_3 + "/helper/mysql/query_by_sip", {
        "mysql_group_id": group["mysql_group_id"],
        "sql": query,
    })
    time.sleep(3)


@when(u'I pause SLA protocol')
def step_imp(context):
    assert context.mysql_instance != None
    api_request_post(context, context.version_3 + "/database/pause_sla_protocol", {
        "group_id": context.mysql_instance['mysql_group_id'],
        "is_sync": True,
    })


@then(u'SLA protocol should paused')
def step_imp(context):
    assert context.mysql_instance != None
    res = get_all_group_info(context)
    match = pyjq.first(
        '.[] | select(.mysql_group_id == "{0}")'.format(
            context.mysql_instance["mysql_group_id"]), res)
    if match['mysql_group_sla_enable'] == "DISABLE":
        return
    assert False


@when(u'I unbind SLA protocol')
def step_imp(context):
    assert context.mysql_instance != None
    api_request_post(context, context.version_3 + "/database/remove_sla_protocol", {
        "group_id": context.mysql_instance['mysql_group_id'],
        "is_sync": True,
    })


@then(u'SLA protocol should not exist')
def step_imp(context):
    assert context.mysql_instance != None
    res = get_all_group_info(context)
    match = pyjq.first(
        '.[] | select(.mysql_group_id == "{0}")'.format(
            context.mysql_instance["mysql_group_id"]), res)

    assert match is not None and 'mysql_group_sla_template' not in match


@then(u'alert code {code:string} should not exist in {duration:time}')
def step_imp(context, code, duration):
    def condition(context, flag):
        resp = api_get(context, context.version_3 + "/alert_record/list_search", {
            'order_by': 'timestamp',
            'ascending': 'false',
        })
        alert_info = pyjq.first('.data[]|select(."code" == "{0}")'.format(code),
                                resp)
        if alert_info is None:
            return True

    waitfor(context, condition, duration)


@when(u'I isolate the MySQL instance')
def step_imp(context):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    slave_info = pyjq.first('.[] | select(.mysql_instance_role == "STATUS_MYSQL_SLAVE")',
                            resp)
    assert slave_info is not None
    context.mysql_instance = slave_info
    body = {
        "group_id": slave_info['mysql_group_id'],
        "mysql_id": slave_info['mysql_instance_id'],
        "is_sync": True,
    }
    api_request_post(context, context.version_3 + "/database/isolate_mysql", body)
    time.sleep(10)


@then(u'alert code {code:string} should contains in {duration:time}')
def step_imp(context, code, duration):
    def condition(context, flag):
        resp = api_get(context, context.version_3 + "/alert_record/list_search", {
            'order_by': 'timestamp',
            'ascending': 'false',
        })
        alert_info = pyjq.first('.data[]|select(."code" == "{0}")'.format(code),
                                resp)
        if alert_info is not None:
            return True

    waitfor(context, condition, duration)


@when(
    u'I found a MySQL group with {count:int} MySQL instance, and {with_without:string} SIP, or I skip the test'
)
def step_impl(context, count, with_without):
    resp = get_all_group_info(context)

    condition = None
    if with_without == 'without':
        condition = '.[] | select(.mysql_group_instance_nums == "{0}") | select(has("mysql_group_sip") | not)'.format(
            count)
    elif with_without == 'with':
        condition = '.[] | select(.mysql_group_instance_nums == "{0}") | select(has("mysql_group_sip"))'.format(
            count)

    match = pyjq.all(condition, resp)
    if match == []:
        context.scenario.skip(
            "Found no MySQL group with {0} MySQL instance, and without SIP".format(count))
        return
    else:
        context.mysql_group = match


@when(u'I found a server of the MySQL group\'s {master_slave:string} instance')
def step_imp(context, master_slave):
    find_group_server(context, master_slave)


def find_group_server(context, master_slave):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    condition = None
    if master_slave == 'master':
        condition = pyjq.first('.[]|select(."mysql_instance_role" == "STATUS_MYSQL_MASTER")',
                               resp)
    elif master_slave == 'slave':
        condition = pyjq.first('.[]|select(."mysql_instance_role" == "STATUS_MYSQL_SLAVE")',
                               resp)
    context.mysql_instance = condition


@then(
    u'the slave MySQL instance should {status:string} in {duration:time}'
)
def step_impl(context, status, duration):
    assert context.mysql_instance != None

    def wait_mysql_running(context, flag):
        resp = get_all_mysql_info(context)
        if status == 'running':
            condition = '.[] | select(."mysql_instance_id"=="{0}")  | select(."mysql_instance_status" == "STATUS_MYSQL_HEALTH_OK")'.format(
                context.mysql_instance["mysql_instance_id"])
        elif status == 'stopped':
            condition = '.[] | select(."mysql_instance_id"=="{0}")  | select(."mysql_instance_status" == "STATUS_MYSQL_HEALTH_BAD")'.format(
                context.mysql_instance["mysql_instance_id"])
        match = pyjq.first(condition, resp)
        if match != None:
            return True

    waitfor(context, wait_mysql_running, duration)


@when(
    u'I damage the {role:string} MySQL instance configuration file and kill pid'
)
def step_imp(context, role):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    master_info = pyjq.first(
        '.[] | select(."mysql_instance_role" == "STATUS_MYSQL_MASTER" and ."mysql_instance_sip" == "(SIP)" and ."mysql_instance_status" == "STATUS_MYSQL_HEALTH_OK" and ."mysql_instance_replication_status" == "STATUS_MYSQL_REPL_OK")',
        resp)
    assert master_info is not None
    if role == "master":
        context.mysql_instance = master_info
        context.execute_steps(u"""
        When I damage the MySQL instance configuration file
        When I kill the MySQL instance pid                    
                              """)
    if role == "slave":
        match = pyjq.all('.[] | select(."mysql_instance_id" != "{0}")'.format(master_info['mysql_instance_id']),
                         resp)
        assert match is not None
        for mysql_info in match:
            context.mysql_instance = mysql_info
            context.execute_steps(u"""
            When I damage the MySQL instance configuration file 
            When I kill the MySQL instance pid
                                          """)


@when('I damage the MySQL instance configuration file')
def step_imp(context):
    assert context.mysql_instance != None
    api_request_post(context, context.version_3 + "/helper/mysql/instance/damage_my_cnf", {
        "mysql_instance_id": context.mysql_instance['mysql_instance_id'],
        "is_sync": True,
    })


@when(u'I kill the MySQL instance pid')
def step_imp(context):
    assert context.mysql_instance != None
    api_request_post(context, context.version_3 + "/helper/kill_mysql_process", {
        "mysql_id": context.mysql_instance['mysql_instance_id'],
        "is_sync": True,
    })


@then(u'the slave MySQL instance promoted in {duration:time}')
def step_imp(context, duration):
    assert context.mysql_instance != None

    def condition(context, flag):
        resp = get_mysql_info_in_group(context, context.mysql_instance["mysql_group_id"])

        condition = '.[] | select(."mysql_instance_status" == "STATUS_MYSQL_HEALTH_OK" and ."mysql_instance_sip" == "(SIP)")'
        master = pyjq.first(
            condition + ' | select(."mysql_instance_role" == "STATUS_MYSQL_MASTER")', resp)
        if master is not None and master['mysql_instance_id'] != context.mysql_instance['mysql_instance_id']:
            return True

    waitfor(context, condition, duration)


@when(u'I make a manual backup on the master MySQL instance')
def step_imp(context):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    condition = '.[] | select(."mysql_instance_status" == "STATUS_MYSQL_HEALTH_OK" and ."mysql_instance_sip" == "(SIP)")'
    master = pyjq.first(
        condition + ' | select(."mysql_instance_role" == "STATUS_MYSQL_MASTER")', resp)
    context.mysql_instance = master
    context.execute_steps(u"""
    When I make a manual backup on the MySQL instance                      
                          """)


@when(
    u'I found all server with component{s:s?} {comps:strings+}, or I skip the test'
)
def step_impl(context, s, comps):
    resp = get_all_server_info(context)
    conditions = map(lambda comp: 'select(has("{0}_status"))'.format(comp),
                     comps)
    condition = '.[] | ' + " | ".join(conditions)
    servers_ip = pyjq.all(condition, resp)

    match = pyjq.all(condition, resp)
    if match is None:
        context.scenario.skip(
            "Found no server with components {0}".format(comps))
    else:
        context.server = match


@when(u'I batch install the MySQL m-ns {count:int}instances use {port:int} in {groupname:string}')
def step_imp(context, count, port, groupname):
    batch_install_mysqls(context, groupname, "mysql-" + groupname, count, port)


@when(
    u'I batch install the MySQL m-ns {count:int}instances use {port:int} in {groupname:string}, with specify run user and group')
def step_imp(context, count, port, groupname):
    batch_install_specify_user_mysqls(context, groupname, "mysql-" + groupname, count, port)


@when(u'I batch install the MySQL m-s instances')
def step_imp(context):
    batch_install_mysql(context, "mysql-group-test2", "mysql-test2", 2, 6000)


@when(u'I batch install the MySQL m-2s instances')
def step_imp(context):
    batch_install_mysql(context, "mysql-group-test3", "mysql-test3", 3, 7000)


def batch_install_mysql(context, mysql_group_prefix, mysql_prefix, mysql_count_per_group, port0):
    assert context.server != None
    server_info = context.server
    mysql_version = context.mysql_version
    if len(server_info) % mysql_count_per_group == 0:
        servers = server_info
    else:
        group_count = int(len(server_info) / mysql_count_per_group)
        servers = server_info[:group_count * mysql_count_per_group]
    title = """数据库组名（必填）,数据库别名（非必填）,服务器ID（必填）,服务器IP（必填）,数据库角色（必填）,复制类型（必填）,数据库端口（必填）,只读实例（非必填）,数据库版本（必填）,安装包（必填）,ROOT密码（必填）,操作用户（必填）,操作用户密码（必填）,配置文件模板（必填）,配置文件目录（必填）,备份目录（必填）,安装目录（必填）,data目录（必填）,binlog目录（必填）,relaylog目录（必填）,redoLog目录（必填）,tmp目录（必填）,启用高可用（必填）,禁用高可用决策（必填）,启动SLA（必填）,SLA模板（非必填）,SIP（非必填）,高可用切换优先级（非必填，默认100）,运行用户（非必填）,运行用户组（非必填）,UID（非必填）,GID（非必填）,UMASK（非必填）,UMASK_DIR（非必填）,SOCKET文件路径（非必填）,组标签_应用英文名（非必填）,组标签_应用名（非必填）,组标签_数据库用途（非必填）,组标签_应用节点描述（非必填）,组标签_应用等级（非必填）,组标签_灾备等级（非必填）,组标签_域名改造（非必填）,开启slave数据补偿（必填）,实例标签_应用tag（非必填）,实例标签_用途tag（非必填）,实例标签_英文简称（非必填）,实例标签_应用节点描述（非必填）,实例标签_用途（非必填）,实例标签_高可用方式（非必填）,实例标签_域名改造（非必填）,实例标签_操作系统（非必填）,实例标签_物理虚拟（非必填）,实例标签_创建时间（非必填）,实例标签_上线时间（非必填）,实例标签_备注（非必填）,实例标签_备份周期（非必填）,实例标签_备份窗口（非必填）,实例标签_全备时间日期（非必填）,实例标签_全备时间星期（非必填）,MYAWR_RUN（ON/OFF）,MYAWR_SERVER_IP,MYAWR_SERVER_MYSQL_PORT,MYAWR_TIVOLI_PROBE_SERVER,MYAWR_TIVOLI_PROBE_PORT,MYAWR_TIVOLI_APP_NAME,MYAWR_TIVOLI_APP_SHORTNAME,MYAWR_TIVOLI_BUSINESS_NAME,MYAWR_TIVOLI_ORG_NAME"""
    i = 0
    csv_content_servers = ""
    context.batch_group = []
    for server in servers:
        server_ip = server['server_address']
        server_id = server['server_id']
        group_idx = int(i / mysql_count_per_group)
        instance_idx_in_group = i % mysql_count_per_group
        group_id = "{0}-{1}".format(mysql_group_prefix, group_idx)
        mysql_alias = "{0}-{1}-{2}".format(mysql_prefix, group_idx, instance_idx_in_group)
        if instance_idx_in_group == 0:
            role = 'master'
            context.batch_group.append(group_id)
        else:
            role = 'slave'
        csv_content_server = """
{group_id},{mysql_alias},{server_id},{server_ip},{role},uguard_semi_sync,{port},,{mysql_version},mysql-{mysql_version}-linux-glibc2.12-x86_64.tar.gz,action,universe_op,universe_pass,my.cnf.5.7,/opt/mysql/etc/{port}/my.cnf,/opt/mysql/backup/{port},/opt/mysql/base/{mysql_version},/opt/mysql/data/{port},/opt/mysql/log/binlog/{port},/opt/mysql/log/relaylog/{port},/opt/mysql/log/redolog/{port},/opt/mysql/tmp/{port},TRUE,FALSE,TRUE,SLA_RPO_sample,,100,mysql{port},mysql{port},{port},{port},,,/opt/mysql/data/{port}/mysqld.sock,应用英文名,应用名,数据库用途,应用节点描述,应用等级,灾备等级,域名改造,FALSE,应用tag,用途tag,英文简称,应用节点描述,用途,高可用方式,域名改造,操作系统,物理虚拟,创建时间,上线时间,备注,0 0 1 ? *,,0 0 23 1/1 * ?,,on,,,,,,,,""".format(
            group_id=group_id,
            mysql_alias=mysql_alias,
            server_id=server_id,
            server_ip=server_ip,
            role=role,
            port=port0 + group_idx,
            mysql_version=mysql_version)
        csv_content_servers = csv_content_server + csv_content_servers
        i = i + 1
    csv_content = title + csv_content_servers

    resp = api_post(
        context,
        context.version_3 + "/database/batch_install_instances", {
            "task_limit": 15,
        },
        files={"csv": ('batch_install_mysql.csv', csv_content)})
    api_request_post(context, context.version_3 + "/progress/commit", {
        "is_sync": True,
        "task_limit": 15,
        "id": resp['progress_id'],
    })
    progress_id = resp['progress_id']
    context.execute_steps(u"""
            Then wait for progress {0} is finished in {1}s
            """.format(progress_id, 1200))

def batch_install_mysqls(context, mysql_group_prefix, mysql_prefix, mysql_count_per_group, port0):
    assert context.server != None
    server_info = context.server
    mysql_version = context.mysql_version
    if len(server_info) % mysql_count_per_group == 0:
        servers = server_info
    else:
        group_count = int(len(server_info) / mysql_count_per_group)
        servers = server_info[:group_count * mysql_count_per_group]
    title = """数据库组名（必填）,数据库别名（非必填）,服务器ID（必填）,服务器IP（必填）,数据库角色（必填）,复制类型（必填）,数据库端口（必填）,只读实例（非必填）,数据库版本（必填）,安装包（必填）,ROOT密码（必填）,操作用户（必填）,操作用户密码（必填）,配置文件模板（必填）,配置文件目录（必填）,备份目录（必填）,安装目录（必填）,data目录（必填）,binlog目录（必填）,relaylog目录（必填）,redoLog目录（必填）,tmp目录（必填）,启用高可用（必填）,禁用高可用决策（必填）,启动SLA（必填）,SLA模板（非必填）,SIP（非必填）,高可用切换优先级（非必填，默认100）,运行用户（非必填）,运行用户组（非必填）,UID（非必填）,GID（非必填）,UMASK（非必填）,UMASK_DIR（非必填）,SOCKET文件路径（非必填）,组标签_应用英文名（非必填）,组标签_应用名（非必填）,组标签_数据库用途（非必填）,组标签_应用节点描述（非必填）,组标签_应用等级（非必填）,组标签_灾备等级（非必填）,组标签_域名改造（非必填）,开启slave数据补偿（必填）,实例标签_应用tag（非必填）,实例标签_用途tag（非必填）,实例标签_英文简称（非必填）,实例标签_应用节点描述（非必填）,实例标签_用途（非必填）,实例标签_高可用方式（非必填）,实例标签_域名改造（非必填）,实例标签_操作系统（非必填）,实例标签_物理虚拟（非必填）,实例标签_创建时间（非必填）,实例标签_上线时间（非必填）,实例标签_备注（非必填）,实例标签_备份周期（非必填）,实例标签_备份窗口（非必填）,实例标签_全备时间日期（非必填）,实例标签_全备时间星期（非必填）,MYAWR_RUN（ON/OFF）,MYAWR_SERVER_IP,MYAWR_SERVER_MYSQL_PORT,MYAWR_TIVOLI_PROBE_SERVER,MYAWR_TIVOLI_PROBE_PORT,MYAWR_TIVOLI_APP_NAME,MYAWR_TIVOLI_APP_SHORTNAME,MYAWR_TIVOLI_BUSINESS_NAME,MYAWR_TIVOLI_ORG_NAME"""
    i = 0
    csv_content_servers = ""
    context.batch_group = []
    for server in servers:
        server_ip = server['server_address']
        server_id = server['server_id']
        group_idx = int(i / mysql_count_per_group)
        instance_idx_in_group = i % mysql_count_per_group
        group_id = "{0}-{1}".format(mysql_group_prefix, group_idx)
        mysql_alias = "{0}-{1}-{2}".format(mysql_prefix, group_idx, instance_idx_in_group)
        if instance_idx_in_group == 0:
            role = 'master'
            context.batch_group.append(group_id)
        else:
            role = 'slave'
        csv_content_server = """
{group_id},{mysql_alias},{server_id},{server_ip},{role},uguard_semi_sync,{port},,{mysql_version},mysql-{mysql_version}-linux-glibc2.12-x86_64.tar.gz,action,universe_op,universe_pass,my.cnf.5.7,/opt/mysql/etc/{port}/my.cnf,/opt/mysql/backup/{port},/opt/mysql/base/{mysql_version},/opt/mysql/data/{port},/opt/mysql/log/binlog/{port},/opt/mysql/log/relaylog/{port},/opt/mysql/log/redolog/{port},/opt/mysql/tmp/{port},TRUE,FALSE,FALSE,,,100,actiontech-mysql,actiontech-mysql,,,,,/opt/mysql/data/{port}/mysqld.sock,,,,,,,,FALSE,,,,,,,,,,,,,,,,,on,,,,,,,,""".format(
            group_id=group_id,
            mysql_alias=mysql_alias,
            server_id=server_id,
            server_ip=server_ip,
            role=role,
            port=port0 + group_idx,
            mysql_version=mysql_version)
        csv_content_servers = csv_content_server + csv_content_servers
        i = i + 1
    csv_content = title + csv_content_servers
    resp = api_post(
        context,
        context.version_3 + "/database/batch_install_instances", {
            "task_limit": 15,
        },
        files={"csv": ('batch_install_mysql.csv', csv_content)})
    api_request_post(context, context.version_3 + "/progress/commit", {
        "is_sync": True,
        "task_limit": 15,
        "id": resp['progress_id'],
    })
    progress_id = resp['progress_id']
    context.execute_steps(u"""
        Then wait for progress {0} is finished in {1}s
        """.format(progress_id, 1200))


def batch_install_specify_user_mysqls(context, mysql_group_prefix, mysql_prefix, mysql_count_per_group, port0):
    assert context.server != None
    server_info = context.server
    if len(server_info) % mysql_count_per_group == 0:
        servers = server_info
    else:
        group_count = int(len(server_info) / mysql_count_per_group)
        servers = server_info[:group_count * mysql_count_per_group]
    title = """数据库组名（必填）,数据库别名（非必填）,服务器ID（必填）,服务器IP（必填）,数据库角色（必填）,复制类型（必填）,数据库端口（必填）,只读实例（非必填）,数据库版本（必填）,安装包（必填）,ROOT密码（必填）,操作用户（必填）,操作用户密码（必填）,配置文件模板（必填）,配置文件目录（必填）,备份目录（必填）,安装目录（必填）,data目录（必填）,binlog目录（必填）,relaylog目录（必填）,redoLog目录（必填）,tmp目录（必填）,启用高可用（必填）,禁用高可用决策（必填）,启动SLA（必填）,SLA模板（非必填）,SIP（非必填）,高可用切换优先级（非必填，默认100）,运行用户（非必填）,运行用户组（非必填）,UID（非必填）,GID（非必填）,UMASK（非必填）,UMASK_DIR（非必填）,SOCKET文件路径（非必填）,组标签_应用英文名（非必填）,组标签_应用名（非必填）,组标签_数据库用途（非必填）,组标签_应用节点描述（非必填）,组标签_应用等级（非必填）,组标签_灾备等级（非必填）,组标签_域名改造（非必填）,开启slave数据补偿（必填）,实例标签_应用tag（非必填）,实例标签_用途tag（非必填）,实例标签_英文简称（非必填）,实例标签_应用节点描述（非必填）,实例标签_用途（非必填）,实例标签_高可用方式（非必填）,实例标签_域名改造（非必填）,实例标签_操作系统（非必填）,实例标签_物理虚拟（非必填）,实例标签_创建时间（非必填）,实例标签_上线时间（非必填）,实例标签_备注（非必填）,实例标签_备份周期（非必填）,实例标签_备份窗口（非必填）,实例标签_全备时间日期（非必填）,实例标签_全备时间星期（非必填）,MYAWR_RUN（ON/OFF）,MYAWR_SERVER_IP,MYAWR_SERVER_MYSQL_PORT,MYAWR_TIVOLI_PROBE_SERVER,MYAWR_TIVOLI_PROBE_PORT,MYAWR_TIVOLI_APP_NAME,MYAWR_TIVOLI_APP_SHORTNAME,MYAWR_TIVOLI_BUSINESS_NAME,MYAWR_TIVOLI_ORG_NAME"""

    csv_content_servers = ""
    context.batch_group = []
    s = [servers[i:i + int(mysql_count_per_group)] for i in range(0, len(servers), 5)]
    k = 0
    for groups in s:
        i = 0
        for server in groups:
            server_ip = server['server_address']
            server_id = server['server_id']
            group_idx = k
            port = port0 + group_idx
            instance_idx_in_group = i
            group_id = "{0}-{1}".format(mysql_group_prefix, group_idx)
            mysql_alias = "{0}-{1}-{2}".format(mysql_prefix, group_idx, instance_idx_in_group)
            if i == 2:
                role = 'master'
                stand = "uguard_semi_sync"
                context.batch_group.append(group_id)
            elif i == 3:
                role = 'slave'
                stand = "uguard_repl"
            else:
                role = 'slave'
                stand = "uguard_semi_sync"

            csv_content_server = """
{group_id},{mysql_alias},{server_id},{server_ip},{role},{stand},{port},,5.7.21,mysql-5.7.21-linux-glibc2.12-x86_64.tar.gz,action,universe_op,universe_pass,my.cnf.5.7,/opt/mysql/etc/{port}/my.cnf,/opt/mysql/backup/{port},/opt/mysql/base/5.7.21,/opt/mysql/data/{port},/opt/mysql/log/binlog/{port},/opt/mysql/log/relaylog/{port},/opt/mysql/log/redolog/{port},/opt/mysql/tmp/{port},TRUE,FALSE,FALSE,,,100,mysql{port},mysql{port},{port},{port},,,/opt/mysql/data/{port}/mysqld.sock,,,,,,,,FALSE,,,,,,,,,,,,,,,,,on,,,,,,,,""".format(
                group_id=group_id,
                mysql_alias=mysql_alias,
                server_id=server_id,
                server_ip=server_ip,
                role=role,
                stand=stand,
                port=port)
            csv_content_servers = csv_content_server + csv_content_servers
            i = i + 1
        k = k + 1
    csv_content = title + csv_content_servers
    resp = api_post(
        context,
        context.version_3 + "/database/batch_install_instances", {
            "task_limit": 15,
        },
        files={"csv": ('batch_install_mysql.csv', csv_content)})
    api_request_post(context, context.version_3 + "/progress/commit", {
        "is_sync": True,
        "task_limit": 15,
        "id": resp['progress_id'],
    })
    progress_id = resp['progress_id']
    context.execute_steps(u"""
        Then wait for progress {0} is finished in {1}s
        """.format(progress_id, 1200))


@then(
    u'the batch MySQL instance list should contains the MySQL instance in {duration:time}'
)
def step_imp(context, duration):
    assert context.batch_group != None
    group = context.batch_group

    def condition(context, flag):
        res = get_all_group_info(context)
        count = 0
        for group_id in group:
            match = pyjq.first(
                '.[] | select(."mysql_group_id" == "{0}" and ."mysql_group_uguard_status" == "UGUARD_PRIMARY_SLAVE_ENABLE")'
                    .format(group_id), res)
            if match is not None:
                count = count + 1
            if count == len(group):
                return True

    waitfor(context, condition, duration)


@when(u'I detach the batch MySQL instance')
def step_imp(context):
    assert context.mysql_group != None
    group = context.mysql_group[0]

    resp = get_mysql_info_in_group(context, group['mysql_group_id'])
    slave_info = pyjq.all('.[] | select(.mysql_instance_role == "STATUS_MYSQL_SLAVE")',
                          resp)
    assert slave_info is not None
    context.slave_list = slave_info
    for slave in slave_info:
        context.mysql_instance = slave
        context.execute_steps(u"""
                            When I stop MySQL instance ha enable
                            Then the response is ok
                            And MySQL instance ha enable should stopped in 1m
                                              """)
        api_request_post(
            context, context.version_3 + "/database/detach_instance", {
                "mysql_id": context.mysql_instance['mysql_instance_id'],
                "server_id": context.mysql_instance['server_id'],
                "group_id": context.mysql_instance['mysql_group_id'],
                "force": "1",
                "is_sync": True,
            })

    master_info = pyjq.first('.[] | select(.mysql_instance_role == "STATUS_MYSQL_MASTER")',
                             resp)
    assert master_info is not None
    context.master = master_info
    context.mysql_instance = master_info
    context.password = get_mysql_instance_root_password(context,
                                                        master_info['mysql_instance_id'])
    context.execute_steps(u"""
                            When I stop MySQL instance ha enable
                            Then the response is ok
                            And MySQL instance ha enable should stopped in 1m
                                              """)
    api_request_post(
        context, context.version_3 + "/database/detach_instance", {
            "mysql_id": context.mysql_instance['mysql_instance_id'],
            "server_id": context.mysql_instance['server_id'],
            "group_id": context.mysql_instance['mysql_group_id'],
            "force": "1",
            "is_sync": True,
        })


@then(u'the MySQL instance list should be not exist the MySQL instance')
def step_imp(context):
    assert context.mysql_group != None
    group = context.mysql_group[0]

    res = get_all_group_info(context)
    match = pyjq.first(
        '.[] | select(."mysql_group_id" == "{0}" and ."mysql_group_instance_nums" == "0")'
            .format(group['mysql_group_id']), res)
    assert match is not None


@when(u'I batch takeover the MySQL instance')
def step_imp(context):
    assert context.slave_list != None
    assert context.master != None
    api_post(context, context.version_3 + "/database/remove_group", {
        "is_sync": True,
        "group_id": context.master['mysql_group_id'],
    })
    master = context.master
    root = context.password
    id = master['mysql_group_id'].lstrip()
    alias = master['mysql_instance_alias']
    server_id = master['server_id']
    server_addr = master['server_address']
    port = master['mysql_instance_port']
    version = master['mysql_instance_version']
    path = master['mysql_instance_tarball_path']
    cnf = master['mysql_instance_mycnf_path ']
    back = master['mysql_instance_backup_path ']
    title = """数据库组名（必填）,数据库别名（非必填）,服务器ID（必填）,服务器IP（必填）,数据库角色（必填）,复制类型（必填）,数据库端口（必填）,只读实例（非必填）,数据库版本（必填）,安装包（必填）,ROOT密码（必填）,操作用户（必填）,操作用户密码（必填）,配置文件目录（必填）,备份目录（必填）,启用高可用（必填）,禁用高可用决策（必填）,启动SLA（必填）,SLA模板（非必填）,SIP（非必填）,运行用户（非必填）,运行用户组（非必填）,UID（非必填）,GID（非必填）,UMASK（非必填）,UMASK_DIR（非必填）,SOCKET文件路径（非必填）,组标签_应用英文名（非必填）,组标签_应用名（非必填）,组标签_数据库用途（非必填）,组标签_应用节点描述（非必填）,组标签_应用等级（非必填）,组标签_灾备等级（非必填）,组标签_域名改造（非必填）,开启slave数据补偿（必填）,实例标签_应用tag（非必填）,实例标签_用途tag（非必填）,实例标签_英文简称（非必填）,实例标签_应用节点描述（非必填）,实例标签_用途（非必填）,实例标签_高可用方式（非必填）,实例标签_域名改造（非必填）,实例标签_操作系统（非必填）,实例标签_物理虚拟（非必填）,实例标签_创建时间（非必填）,实例标签_上线时间（非必填）,实例标签_备注（非必填）,实例标签_备份周期（非必填）,实例标签_备份窗口（非必填）,实例标签_全备时间日期（非必填）,实例标签_全备时间星期（非必填）"""
    master_info = "\n{0},{1},{2},{3},master,uguard_semi_sync,{4},,{5},{6},{7},universe_op,bupYE@-00,{8},{9},TRUE,FALSE,TRUE,SLA_RPO_sample,,actiontech-mysql,,,,,,,,,,,,,,TRUE,,,,,,,,,,,,,,,,".format(
        id, alias, server_id, server_addr, port, version, path, root, cnf, back)
    slave_all = ""
    for slave in context.slave_list:
        id = slave['mysql_group_id'].lstrip()
        alias = slave['mysql_instance_alias']
        server_id = slave['server_id']
        server_addr = slave['server_address']
        port = slave['mysql_instance_port']
        version = slave['mysql_instance_version']
        path = slave['mysql_instance_tarball_path']
        cnf = slave['mysql_instance_mycnf_path ']
        back = slave['mysql_instance_backup_path ']
        slave_one = "\n{0},{1},{2},{3},slave,uguard_semi_sync,{4},,{5},{6},{7},universe_op,bupYE@-00,{8},{9},TRUE,FALSE,TRUE,SLA_RPO_sample,,actiontech-mysql,,,,,,,,,,,,,,TRUE,,,,,,,,,,,,,,,,". \
            format(id, alias, server_id, server_addr, port, version, path, root, cnf, back)
        slave_all = slave_one + slave_all
    csv_content = title + master_info + slave_all

    resp = api_post(
        context,
        context.version_3 + "/database/batch_takeover_instances", {
            "task_limit": 30,
        },
        files={"csv": ('batch_takeover_mysql.csv', csv_content)})
    api_request_post(context, context.version_3 + "/progress/commit", {
        "is_sync": True,
        "task_limit": 30,
        "id": resp['progress_id'],
    })


@then(
    u'batch takeover the MySQL instance list should contains the MySQL instance in {duration:time}'
)
def step_imp(context, duration):
    assert context.master != None

    def condition(context, flag):
        res = get_all_group_info(context)
        match = pyjq.first(
            '.[] | select(."mysql_group_id" == "{0}" and ."mysql_group_uguard_status" == "UGUARD_PRIMARY_SLAVE_ENABLE")'
                .format(context.master['mysql_group_id']), res)
        if match is not None:
            return True

    waitfor(context, condition, duration)


@when(u'I found all MySQL instance, or I skip the test')
def step_imp(context):
    resp = get_all_mysql_info(context)
    match = pyjq.all(
        '[] | select(."mysql_instance_status" == "STATUS_MYSQL_HEALTH_OK")', resp)
    if match is None:
        context.scenario.skip("No valid MySQL instance")
        return
    else:
        context.mysql_instance_list = match


@when(u'I trigger diagnosis report')
def step_imp(context):
    assert context.mysql_instance != None
    origin_id = None
    resp = api_get(context, context.version_4 + "/diagnosis/report/list", {
        "page_size": context.page_size_to_select_all,
    })
    if resp['data'] != None:
        origin_id = pyjq.all('.data[] | .diagnosis_report_id', resp)
    context.origin_id = origin_id
    body = {
        "server_id": context.mysql_instance['server_id'],
        "mysql_id": context.mysql_instance['mysql_instance_id'],
        "group_id": context.mysql_instance['mysql_group_id'],
        "is_sync": True
    }
    api_request_post(context, context.version_3 + "/database/trigger_diagnosis_report", body)


@then(u'the diagnosis list should contains the diagnosis report')
def step_imp(context):
    resp = api_get(context, context.version_4 + "/diagnosis/report/list", {
        "page_size": context.page_size_to_select_all,
    })
    if resp['data'] != None:
        match = pyjq.all('.data[] | .diagnosis_report_id', resp)
    assert context.origin_id != match
    list_report_id = list(set(match).difference(set(context.origin_id)))
    LOGGER.info('The new created diagnosis report is <{0}>'.format(pformat(list_report_id)))
    new_report = pyjq.first(
        '.data[] | select(."diagnosis_report_id" == "{0}") | select(."mysql_instance_id" == "{1}")'.format(
            list_report_id[0], context.mysql_instance['mysql_instance_id']), resp)
    assert new_report != None


@when(u'I trigger diagnosis score report')
def step_imp(context):
    assert context.mysql_instance != None
    origin_id = None
    resp = api_get(context, context.version_3 + "/diagnosis_score/list", {
        "page_size": context.page_size_to_select_all,
    })
    if resp['data'] != None:
        origin_id = pyjq.all('.data[]|.Key', resp)
    context.origin_id = origin_id
    LOGGER.info('The Key of diagnosis score report is <{0}>'.format(pformat(origin_id)))
    body = {
        "server_id": context.mysql_instance['server_id'],
        "mysql_id": context.mysql_instance['mysql_instance_id'],
        "group_id": context.mysql_instance['mysql_group_id'],
        "is_sync": True
    }
    api_request_post(context, context.version_3 + "/database/trigger_diagnosis_score_report", body)


@then(u'the diagnosis score list should contains the diagnosis score')
def step_imp(context):
    resp = api_get(context, context.version_3 + "/diagnosis_score/list", {
        "page_size": context.page_size_to_select_all,
    })
    if resp['data'] != None:
        match = pyjq.all('.data[]|.Key', resp)
    assert context.origin_id != match
    list_Key = list(set(match).difference(set(context.origin_id)))
    LOGGER.info('The new created Key of diagnosis score report is <{0}>'.format(pformat(list_Key)))
    new_report = pyjq.first(
        '.data[] | select(."Key" == "{0}") | select(."MysqlId" == "{1}")'.format(
            list_Key[0], context.mysql_instance['mysql_instance_id']), resp)
    assert new_report != None


@when(u'I create and insert table in slave instance "{statement}"')
def step_imp(context, statement):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    mysql_master = pyjq.first(
        '.[] | select(.mysql_instance_role == "STATUS_MYSQL_MASTER")', resp)
    master_root = get_mysql_instance_root_password(context, mysql_master['mysql_instance_id'])
    mysql = pyjq.first('.[] | select(.mysql_instance_role == "STATUS_MYSQL_SLAVE")', resp)
    assert mysql is not None
    context.mysql_instance = mysql
    resp = api_get(
        context, context.version_3 + "/helper/query_mysql", {
            "mysql_id": mysql["mysql_instance_id"],
            "query": statement,
            "user": "root",
            "password": master_root,
        })


@then(u'the MySQL instance should be exclude HA in {duration:time}')
def step_imp(context, duration):
    assert context.mysql_instance != None

    def condition(context, flag):
        resp = get_mysql_info_in_group(context, context.mysql_instance['mysql_group_id'])
        match = pyjq.first(
            '.[] | select(."mysql_instance_id" == "{0}")'.format(
                context.mysql_instance['mysql_instance_id']), resp)
        if match['uguard_status'] != "UGUARD_ENABLE":
            return True

    waitfor(context, condition, duration)


@when(u'I pull the MySQL instance GTID')
def step_imp(context):
    assert context.mysql_instance != None
    body = {
        "group_id": context.mysql_instance['mysql_group_id'],
        "mysql_id": context.mysql_instance['mysql_instance_id'],
        "is_sync": True
    }
    api_request_post(context, context.version_3 + "/database/leveling_gtid", body)


@then(u'the MySQL group GTID should be consistent in {duration:time}')
def step_imp(context, duration):
    assert context.mysql_group != None

    def condition(context, flag):
        resp = api_get(context, context.version_3 + "/database/list_group_gtid",
                       {"group_id": context.mysql_group[0]['group_id']})
        match = pyjq.all('.[]|.GTID', resp)
        assert len(match) > 1
        if match[0] == match[1]:
            return True

    waitfor(context, condition, duration)


@then(u'the MySQL group GTID should not consistent in {duration:time}')
def step_imp(context, duration):
    assert context.mysql_group != None

    def condition(context, flag):
        resp = api_get(context, context.version_3 + "/database/list_group_gtid",
                       {"group_id": context.mysql_group[0]['group_id']})
        match = pyjq.all('.[]|.GTID', resp)
        assert len(match) > 1
        if match[0] != match[1]:
            return True

    waitfor(context, condition, duration)


@when(u'I enable HA on the MySQL instance with uguard_status not health')
def step_imp(context):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]['mysql_group_id'])
    match = pyjq.first('.[]|select(."uguard_status" != "UGUARD_ENABLE")',
                       resp)
    assert match is not None
    body = {
        "server_id": match['server_id'],
        "group_id": match['mysql_group_id'],
        "mysql_id": match['mysql_instance_id'],
        "is_sync": True,
    }
    api_request_post(context, context.version_3 + "/database/start_mysql_ha_enable", body)


@when(u'I update the MySQL instance config readonly {value:int}')
def step_imp(context, value):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]['mysql_group_id'])
    match = pyjq.first('.[] | select(."mysql_instance_role" == "STATUS_MYSQL_SLAVE")',
                       resp)
    body = {
        "server_id": match['server_id'],
        "mysql_id": match['mysql_instance_id'],
        "config": "readonly",
        "value": value,
        "is_sync": True,
    }
    api_request_post(context, context.version_3 + "/database/edit_mysql_config", body)
    context.mysql_instance = match


@then(u'the MySQL instance config readonly should be {value:int}')
def step_imp(context, value):
    assert context.mysql_instance != None
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]['mysql_group_id'])
    match = pyjq.first(
        '.[] | select(."mysql_instance_id" == "{0}")'.format(
            context.mysql_instance['mysql_instance_id']), resp)
    assert match['readonly'] == "{0}".format(value)


@then(u'the MySQL instance status should be in {duration:time}')
def step_imp(context, duration):
    assert context.mysql_instance != None
    assert context.mysql_group != None
    assert context.master_info != None

    def condition(context, flag):
        resp = get_mysql_info_in_group(context, context.mysql_group[0]['mysql_group_id'])
        old_master = pyjq.first(
            '[] | select(."mysql_instance_status" != "STATUS_MYSQL_HEALTH_OK" and ."mysql_instance_id" = "{0}")'
                .format(context.master_info['mysql_instance_id']), resp)
        new_master = pyjq.first(
            '.[] | select(."mysql_instance_role" == "STATUS_MYSQL_MASTER" and ."mysql_instance_id" != "{0}")'
                .format(context.mysql_instance['mysql_instance_id']), resp)
        slave = pyjq.first(
            '.[] | select(."mysql_instance_role" == "STATUS_MYSQL_SLAVE" and ."mysql_instance_id" == "{0}")'
                .format(context.mysql_instance['mysql_instance_id']), resp)
        if old_master is not None and new_master is not None and slave is not None:
            return True

    waitfor(context, condition, duration)


@when(u'I reset old master MySQL instance')
def step_imp(context):
    assert context.mysql_group != None
    assert context.master_info != None
    context.mysql_instance = context.master_info
    resp = api_get(context, context.version_3 + "/support/init_data", {
        "group_id": context.mysql_instance['group_id'],
    })
    assert len(resp) > 0
    init_data = resp[-1]["name"]
    body = {
        "server_id": context.mysql_instance['server_id'],
        "mysql_id": context.mysql_instance['mysql_instance_id'],
        "origin_data": init_data,
        "is_sync": True,
    }
    api_request_post(context, context.version_3 + "/database/reset_database_instance", body)


@when(u'I update the MySQL instance config master sequence {value:int}')
def step_imp(context, value):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]['mysql_group_id'])
    match = pyjq.first('.[] | select(."mysql_instance_role" == "STATUS_MYSQL_SLAVE")',
                       resp)
    body = {
        "server_id": match['server_id'],
        "mysql_id": match['mysql_instance_id'],
        "config": "master_sequence",
        "value": value,
        "is_sync": True,
    }
    api_request_post(context, context.version_3 + "/database/edit_mysql_config", body)
    context.mysql_instance = match


@when(u'I {action:string} the MySQL instance {role:string} component {component:string}')
def step_imp(context, action, role, component):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]['mysql_group_id'])
    master = pyjq.first('.[] | select(."mysql_instance_role" == "STATUS_MYSQL_MASTER")', resp)
    assert master is not None
    slave = pyjq.first('.[] | select(."mysql_instance_role" == "STATUS_MYSQL_SLAVE")', resp)
    assert slave is not None
    res = get_all_server_info(context)
    if action == "stop" and role == "master":
        context.server = pyjq.first('.[] | select(."server_id" == "{0}")'.format(master['server_id']), res)
        assert context.server != None
        context.mysql_instance = master
        context.execute_steps(u"""
        When I action {0} component {1}
        Then the response is ok
    	Then the component {1} should be stopped in 60s
        """.format(action, component))
    if action == "stop" and role == "slave":
        context.server = pyjq.first('.[] | select(."server_id" == "{0}")'.format(slave['server_id']), res)
        assert context.server != None
        context.mysql_instance = slave
        context.execute_steps(u"""
        When I action {0} component {1}
        Then the response is ok
        Then the component {1} should be stopped in 60s
                """.format(action, component))
    if action == "start" and role == "master":
        context.server = pyjq.first('.[] | select(."server_id" == "{0}")'.format(master['server_id']), res)
        assert context.server != None
        context.mysql_instance = master
        context.execute_steps(u"""
        When I action {0} component {1}
        Then the response is ok
    	Then the component {1} should be running in 60s
        """.format(action, component))
    if action == "start" and role == "slave":
        context.server = pyjq.first('.[] | select(."server_id" == "{0}")'.format(slave['server_id']), res)
        assert context.server != None
        context.mysql_instance = slave
        context.execute_steps(u"""
        When I action {0} component {1}
        Then the response is ok
        Then the component {1} should be running in 60s
        """.format(action, component))
    time.sleep(3)


@then(
    u'the component {comps:strings+} should be {status:strings} in {duration:time}')
def step_impl(context, comps, status, duration):
    assert context.server != None

    def component_status(context, flag):
        resp = get_all_server_info(context)
        conditions = None
        if status == 'running':
            conditions = map(lambda comp: 'select(."{0}_status"=="STATUS_OK")'.format(comp), comps)
        elif status == 'stopped':
            conditions = map(lambda comp: 'select(."{0}_status"=="STATUS_STOPPED")'.format(comp), comps)

        condition = '.[] | select(."server_id"=="{0}") | '.format(context.server['server_id']) + " | ".join(
            conditions) + " | " + '.server_id'
        match = pyjq.first(condition, resp)
        if match != None:
            return True

    waitfor(context, component_status, duration)


@then(u'the MySQL instance should not be health in {duration:time}')
def step_imp(context, duration):
    assert context.mysql_instance != None

    def condition(context, flag):
        resp = get_all_mysql_info(context)
        match = pyjq.first(
            '.[] | select(.mysql_instance_status != "STATUS_MYSQL_HEALTH_OK")',
            resp)
        if match is not None:
            return True

    waitfor(context, condition, duration)


@when(
    u'I found a MySQL group with {count:int} MySQL instance'
)
def step_impl(context, count):
    resp = get_all_group_info(context)
    condition = '.[] | select(.mysql_group_instance_nums == "{0}")'.format(count)
    match = pyjq.all(condition, resp)
    if match is None:
        context.scenario.skip(
            "Found no MySQL group with {0} MySQL instance".format(count))
    else:
        context.mysql_group = match


@then(u'I got the response')
def step_imp(context):
    assert context.mysql_resp != None
    context.resp_first = context.mysql_resp
    context.value_first = context.mysql_resp[3]["Value"]


@when(u'I update the metadata set ignore-guard-action {true_or_false:string}')
def step_imp(context, true_or_false):
    mysql_group_id = context.mysql_group[0]["mysql_group_id"]
    base_url = context.base_url
    url = base_url + "helper/mysql/group/update_uguard_action_switch"
    payload = "is_sync=True&mysql_group_id=" + mysql_group_id + "&is_enabled=" + true_or_false
    headers = {
        'content-type': "application/x-www-form-urlencoded",
        "authorization": this.token,
        'is_sync': "True",
        'mysql_group_id': mysql_group_id,
        'is_enabled': true_or_false
    }
    response = requests.request("POST", url, data=payload, headers=headers)


@then(u'I found the response are the {same_or_different:string}')
def step_impl(context, same_or_different):
    assert context.mysql_resp != None
    if same_or_different == "same":
        assert context.mysql_resp == context.resp_first
        assert context.mysql_resp[3]["Value"] == context.value_first
    else:
        assert context.mysql_resp != context.resp_first
        assert context.mysql_resp[3]["Value"] != context.value_first


@when(u'I restart the master instance')
def step_imp(context):
    master_id = context.mysql_instance["mysql_instance_id"]
    api_post(context, context.version_3 + "/database/stop_mysql_service", {
        "is_sync": True,
        "mysql_id": master_id
    })
    api_post(context, context.version_3 + "/database/start_mysql_service", {
        "is_sync": True,
        "mysql_id": master_id
    })
    time.sleep(5)


@when(u'I restart the replication of the slave instances')
def step_imp(context):
    assert context.mysql_group != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    conditions = pyjq.all('.[]|select(."mysql_instance_role" == "STATUS_MYSQL_SLAVE")', resp)
    for condition in conditions:
        slave_id = condition["mysql_instance_id"]
        api_request_post(context, context.version_3 + "/database/restart_replication", {
            "is_sync": True,
            "mysql_id": slave_id
        })


@when(u'I repair the setting of SEMI_SYNC_WAIT_SLAVE_COUNT')
def step_imp(context):
    assert context.mysql_group != None
    group = context.mysql_group[0]
    api_post(context, context.version_3 + "/database/fix_semi_sync_count", {
        "is_sync": True,
        "group_id": group["mysql_group_id"]
    })
    time.sleep(5)


@when(u'I prepare the MySQL instance with ha')
def step_imp(context):
    group_id = context.mysql_group[0]["mysql_group_id"]
    resp = api_get(context, context.version_3 + "/database/list_instance", {
        "group_id": group_id,
        "sla_status": "MASTER"
    })
    rep = pyjq.first('.data[]', resp)
    instance_id = rep["mysql_id"]
    if "sip" not in rep.keys():
        api_post(context, context.version_3 + "/database/start_mysql_ha_enable", {
            "is_sync": True,
            "group_id ": group_id,
            "mysql_id ": instance_id
        })
    context.master_id = instance_id


@then(u'Value of rpl_semi_sync_master_wait_no_slave should be OFF')
def step_imp(context):
    value = context.mysql_resp[4]["Value"]
    assert value == "OFF"


# update in 0626 used by 1m1s_a2
@when(u'I prepare the group with sip if not exists')
def step_imp(context):
    group_id = context.mysql_group[0]["mysql_group_id"]
    get_all_valid_sip(context)
    sip = random.choice(context.valid_sip)
    #context.valid_sip.pop(0)
    if "mysql_group_sip" not in context.mysql_group[0]:
        api_request_post(context, context.version_3 + "/database/update_mysql_sip", {
            "is_sync": True,
            "group_id": group_id,
            "sip": sip,
        })


# update in 0626 used by 1m1s_a2
@then(u'the MySQL group {should_or_not:should_or_not} have sip')
def step_imp(context, should_or_not):
    group_id = context.mysql_group[0]["mysql_group_id"]
    resp = get_group_info_by_id(context, group_id)
    assert (("mysql_group_sip" in resp) and should_or_not) or (
            ("mysql_group_sip" not in resp) and not should_or_not)


@then(u'the MySQL instance {should_or_not:should_or_not} have sip')
def step_imp(context, should_or_not):
    group_id = context.mysql_group[0]["mysql_group_id"]
    resp = get_mysql_info_in_group(context, group_id)
    mysql_instance = pyjq.first('.[]', resp)
    assert (("useable_sip" in mysql_instance) and should_or_not) or \
           (("useable_sip" not in mysql_instance) and not should_or_not)


@when(u'I kill the component {comp:string} of the instance')
def step_imp(context, comp):
    server_id = context.mysql_instance["server_id"]
    resp = api_get(context, context.version_3 + "/server/list", {
        "server_id": server_id
    })
    server = pyjq.first(
        '.data[] | select(.server_id == "{0}")'.format(server_id),
        resp)
    context.server = server
    compid = comp + "_" + server_id
    api_post(context, context.version_3 + "/helper/component/kill", {
        "is_sync": True,
        "component_instance_id": compid
    })


@when(u'I remove the sip for the MySQL group')
def step_imp(context):
    # if don't sleep, master instance would be error
    time.sleep(5)
    group_id = context.mysql_group[0]["mysql_group_id"]
    api_request_post(context, context.version_3 + "/database/update_mysql_sip", {
        "is_sync": True,
        "group_id": group_id,
    })


@when(u'I found a instance with a {similar_different:string} sip in MySQL group')
def step_impl(context, similar_different):
    mysql_group_id = context.mysql_group[0]["mysql_group_id"]
    resp = get_group_info_by_id(context, mysql_group_id)
    group_sip = resp["mysql_group_sip"]
    list_instance = get_mysql_info_in_group(context, mysql_group_id)
    for instance in list_instance:
        if similar_different == "different" and instance["mysql_instance_useable_sip"] != group_sip:
            context.mysql_instance = instance
            break
        elif similar_different == "similar" and instance["mysql_instance_useable_sip"] == group_sip:
            context.mysql_instance = instance
            break


@then(u'the instance should have a {similar_different:string} sip with the MySQL group')
def step_impl(context, similar_different):
    mysql_group_id = context.mysql_group[0]["mysql_group_id"]
    group = get_group_info_by_id(context, mysql_group_id)
    group_sip = group["mysql_group_sip"]
    instance_sip = context.mysql_instance["mysql_instance_useable_sip"]
    if similar_different == "different":
        assert group_sip != instance_sip
    elif similar_different == "similar":
        assert group_sip == instance_sip


@when(u'I found the password of the root user')
def step_impl(context):
    assert context.mysql_instance is not None
    rootPassword = get_mysql_instance_root_password(context, context.mysql_instance["mysql_instance_id"])
    assert rootPassword is not None
    context.mysql_instance["root_password"] = rootPassword


@when(u'I {show_or_hide:string} udb')
def step_impl(context, show_or_hide):
    mysql_group = {"mysql_group_id": "mysql-group-udb"}
    mysql_instance = {"mysql_instance_id": "mysql-udb1"}
    context.mysql_group = mysql_group
    context.mysql_instance = mysql_instance
    resp = api_get(context, context.version_3 + "/custom/get_config")
    res = resp.replace("\\", "")
    config = json.loads(res)
    if show_or_hide == "hide":
        config["hideUdb"] = "1"
    elif show_or_hide == "show":
        config["hideUdb"] = "0"
    else:
        context.scenario.skip('parameter error: the parameter can only be "show" or "hide"')
        return
    api_request_post(context, context.version_3 + "/custom/set_config", {
        "config": json.dumps(config)
    })
