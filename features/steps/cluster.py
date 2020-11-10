from behave import *
from framework.api import *
import pyjq
import time
import json
import re
from util import *
from common import *


@when(u'I init DMP')
def step_impl(context):
    localsys = api_get(context, context.version_3 + "/support/localsys")
    hostname = localsys["hostname"]
    ip = localsys["sip"]

    ucore = api_get(context, context.version_3 + "/support/component?pattern=ucore")[-1]["Name"]
    uagent = api_get(context, context.version_3 + "/support/component?pattern=uagent")[-1]["Name"]
    ustats = api_get(context, context.version_3 + "/support/component?pattern=ustats")[-1]["Name"]
    udeploy = api_get(context, context.version_3 + "/support/component?pattern=udeploy")[-1]["Name"]
    mysql = api_get(context, context.version_3 + "/support/component?pattern=mysql-5.7")[-1]["Name"]

    api_post(context, context.version_3 + "/install/umc", {
        "is_sync": True,
        "component_path": "/opt",
        "server_id": "server-" + hostname,
        "server_ip": ip,
        "hostname": hostname,
        "ucore_path": "/opt/ucore",
        "ucore_install_file": ucore,
        "ucore_id": "ucore-" + hostname,
        "uagent_path": "/opt/uagent",
        "uagent_install_file": uagent,
        "uagent_id": "uagent-" + hostname,
        "udeploy_path": "/opt/udeploy",
        "udeploy_install_file": udeploy,
        "udeploy_id": "udeploy-" + hostname,
        "ustats_path": "/opt/ustats",
        "ustats_install_file": ustats,
        "ustats_id": "ustats-" + hostname,
        "umc_path": "/opt/umc",
        "umc_id": "umc-" + hostname,
        "mysql_tarball_path": mysql,
        "mysql_path": "/opt/udb/mysql",
        "mysql_port": "5690",
        "initial_mgr_port": "5691",
        "mysql_id": "mysql-udb1",
        "version": "5.7.20",
        "install_standard": "semi_sync"
    })

    uguard_mgr = api_get(context, context.version_3 + "/support/component?pattern=uguard-mgr")[-1]["Name"]
    api_post(context, context.version_3 + "/server/install", {
        "is_sync": True,
        "server_id": "server-" + hostname,
        "component": "uguard-mgr",
        "uguard-mgr_path": "/opt/uguard-mgr",
        "uguard-mgr_id": "uguard-mgr-" + hostname,
        "uguard-mgr_install_file": uguard_mgr
    })

    uguard_agent = api_get(context, context.version_3 + "/support/component?pattern=uguard-agent")[-1]["Name"]
    api_post(context, context.version_3 + "/server/install", {
        "is_sync": True,
        "server_id": "server-" + hostname,
        "component": "uguard-agent",
        "uguard-agent_path": "/opt/uguard-agent",
        "uguard-agent_id": "uguard-agent-" + hostname,
        "uguard-agent_install_file": uguard_agent
    })

    umon = api_get(context, context.version_3 + "/support/component?pattern=umon")[-1]["Name"]
    api_post(context, context.version_3 + "/server/install", {
        "is_sync": True,
        "server_id": "server-" + hostname,
        "component": "umon",
        "umon_path": "/opt/umon",
        "umon_id": "umon-" + hostname,
        "umon_install_file": umon
    })

    urman_mgr = api_get(context, context.version_3 + "/support/component?pattern=urman-mgr")[-1]["Name"]
    api_post(context, context.version_3 + "/server/install", {
        "is_sync": True,
        "server_id": "server-" + hostname,
        "component": "urman-mgr",
        "urman-mgr_path": "/opt/urman-mgr",
        "urman-mgr_id": "urman-mgr-" + hostname,
        "urman-mgr_install_file": urman_mgr
    })

    urman_agent = api_get(context, context.version_3 + "/support/component?pattern=urman-agent")[-1]["Name"]
    api_request_post(context, context.version_3 + "/server/install", {
        "is_sync": True,
        "server_id": "server-" + hostname,
        "component": "urman-agent",
        "urman-agent_path": "/opt/urman-agent",
        "urman-agent_id": "urman-agent-" + hostname,
        "urman-agent_install_file": urman_agent
    })

    urds = api_get(context, context.version_3 + "/support/component?pattern=urds")[-1]["Name"]
    api_post(context, "server/install", {
        "is_sync": True,
        "server_id": "server-" + hostname,
        "component": "urds",
        "op_user": "actiontech-universe",
        "urds_path": "/opt/urds",
        "urds_id": "urds-" + hostname,
        "urds_install_file": urds
    })


@when(u'I add server from parameter')
def step_impl(context):
    assert context.new_server_ip != None
    assert context.new_server_ssh_port != None
    assert context.new_server_ssh_user != None
    assert context.new_server_ssh_password != None

    hostname = api_get(context, context.version_3 + "/support/hostname", {
        "ip": context.new_server_ip,
        "port": context.new_server_ssh_port,
        "user": context.new_server_ssh_user,
        "password": context.new_server_ssh_password,
    })
    hostname = hostname.strip()

    uagent = api_get(context, context.version_3 + "/support/component?pattern=uagent")[-1]["Name"]
    ustats = api_get(context, context.version_3 + "/support/component?pattern=ustats")[-1]["Name"]

    api_post(context, context.version_3 + "/server/add", {
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

    udeploy = api_get(context, context.version_3 + "/support/component?pattern=udeploy")[-1]["Name"]
    api_post(context, context.version_3 + "/server/install", {
        "is_sync": True,
        "server_id": "server-" + hostname,
        "component": "udeploy",
        "udeploy_path": "/opt/udeploy",
        "udeploy_id": "udeploy-" + hostname,
        "udeploy_install_file": udeploy
    })

    uguard_agent = api_get(context, context.version_3 + "/support/component?pattern=uguard-agent")[-1]["Name"]
    api_post(context, context.version_3 + "/server/install", {
        "is_sync": True,
        "server_id": "server-" + hostname,
        "component": "uguard-agent",
        "uguard-agent_path": "/opt/uguard-agent",
        "uguard-agent_id": "uguard-agent-" + hostname,
        "uguard-agent_install_file": uguard_agent
    })

    urman_agent = api_get(context, context.version_3 + "/support/component?pattern=urman-agent")[-1]["Name"]
    api_request_post(context, context.version_3 + "/server/install", {
        "is_sync": True,
        "server_id": "server-" + hostname,
        "component": "urman-agent",
        "urman-agent_path": "/opt/urman-agent",
        "urman-agent_id": "urman-agent-" + hostname,
        "urman-agent_install_file": urman_agent
    })


@when(u'I batch add backup rules')
def step_impl(context):
    content = '实例别名,备份规则名,实例ID,服务器ID,备份工具,全备时间（cron）,增备时间（cron）,备份保留份数,备份优先级,备份binlog时间（cron）,binlog回收时间（天）,转储设备名,运维开始时间（cron),运维持续时间,only_slave,only_master'

    resp = api_get(context, context.version_3 + "/database/list_instance", {
        "number": context.page_size_to_select_all,
    })

    mysqls = pyjq.all('.data[]', resp)
    for mysql in mysqls:
        mysql_alias = mysql['mysql_alias']
        mysql_id = mysql['mysql_id']
        rule_name = 'rule-' + mysql_id
        server_id = mysql['server_id']
        row = [mysql_alias, rule_name, mysql_id, server_id, 'xtrabackup', generate_full_backup_cron(),
               generate_incr_backup_cron(), '2', generate_backup_priority(), '', '', '', '0 0 0 1/1 * ?', '1440m',
               'false', 'false']
        content = content + "\n" + ",".join(row)

        rule_name_binlog = rule_name + '_binlog'
        row_binlog = [mysql_alias, rule_name_binlog, mysql_id, server_id, 'binlog', '', '', '', '',
                      generate_incr_backup_cron(), '7', '', '0 0 0 1/1 * ?', '1440m', 'false', 'false']
        content = content + "\n" + ",".join(row_binlog)

    resp = api_post(
        context,
        context.version_3 + "/urman_rule/batch_add_backup_rules", {},
        files={"csv": ('batch_install_mysql.csv', content)})
    api_request_post(context, context.version_3 + "/progress/commit", {
        "is_sync": True,
        "task_limit": 30,
        "id": resp['id'],
    })


def generate_full_backup_cron():
    cron = ['0', str(random.randint(0, 59)), str(random.randint(0, 23))]
    cron.extend(['?', '*'])
    week = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
    cron.append(random.choice(week))
    return ' '.join(cron)


def generate_incr_backup_cron():
    cron = ['0', str(random.randint(0, 59)), str(random.randint(0, 23))]
    cron.extend(['1/1', '*', '?'])
    return ' '.join(cron)


def generate_backup_priority():
    return str(random.randint(1, 99))

