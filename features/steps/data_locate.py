from behave import *
from framework.api import *
import pyjq
import time
import json
import types
from util import *
from common import *
from getinfo import *
import time
from configparser import ConfigParser
import yaml
import logging
from pprint import pformat
LOGGER = logging.getLogger("steps.data_locate")


@when(u'I found {des:string} MySQL group with {count:int} MySQL instances,or I skip the test')
def found_mysql(context, des, count):
    template_values = des_to_json(des)

    # query groups with instances
    count_instances(context, count)

    # groups for sla_template
    found_for_sla_template(context, template_values)

    # groups for collect_timeout_sec default:60
    found_for_collect_timeout_sec(context, template_values)

    # groups for ignore_guard_action and data_supply_from_slave default:0
    found_for_ignore_guard_action(context, template_values)
    found_for_data_supply_from_slave(context, template_values)

    # get all config for repl_ip
    docker_compose = load_yaml_config("deploy/compose/docker-compose.yaml")
    context.server_info_list = get_all_nodes(docker_compose)
    # instances for repl_ip
    found_for_repl_ip(context, template_values, count)

    # instances for udelay_enable,master_sequence
    found_for_master_sequence(context, template_values, count)

    # found for udelay_enable
    found_for_udelay_enable(context, template_values)

    # instances for run_user
    found_for_run_user(context, template_values, count)

    # instances for readonly
    found_for_readonly(context, template_values, count)

    # groups and instances for uguard
    found_for_uguard(context, template_values, count)

    # groups and instances for sip
    found_for_sip(context, template_values, count)

    # found for loose_io_flush_param_check
    found_for_loose_io_flush_param_check(context, template_values, count)

    return context.mysql_group


def found_for_loose_io_flush_param_check(context, template_values, count):
    value = template_values["loose_io_flush_param_check"]
    match = []
    flag = 0
    for group in context.mysql_group:
        mysql_group_id = group["mysql_group_id"]
        list_instance = get_mysql_info_in_group(context, mysql_group_id)
        for instance in list_instance:
            path = "universe/v3/mysqls/"
            key = path + instance["mysql_instance_id"]
            resp = get_config_metadata_info(context, path, key)
            value_resp = resp["loose_io_flush_param_check"]
            if value == "0" and not value_resp:
                flag = flag + 1
            elif value == "1" and value_resp:
                flag = flag + 1
        if flag == count:
            match.append(group)
    context.mysql_group = match
    if len(match) == 0:
        debug_info(context)
        context.scenario.skip("Found no groups accord")


def found_for_udelay_enable(context, template_values):
    match = []
    for group in context.mysql_group:
        if template_values["group_udelay_enable"] == "1" and group["mysql_group_udelay_enable"] == "1":
            match.append(group)
        elif template_values["group_udelay_enable"] == "0" and group["mysql_group_udelay_enable"] == "0":
            match.append(group)
    context.mysql_group = match
    if len(match) == 0:
        debug_info(context)
        context.scenario.skip("Found no groups accord")


def found_for_run_user(context, template_values, count):
    match = []
    for group in context.mysql_group:
        mysql_group_id = group["mysql_group_id"]
        resp = get_mysql_info_in_group(context, mysql_group_id)
        instances = pyjq.all('.[]', resp)
        user_flag = 0
        for instance in instances:
            if template_values["run_user"] == "actiontech-mysql" and instance["mysql_instance_run_user"] == "actiontech-mysql":
                user_flag = user_flag + 1
            elif template_values["run_user"] == "0" and instance["mysql_instance_run_user"] != "actiontech-mysql":
                user_flag = user_flag + 1
        if user_flag == count:
            match.append(group)
    context.mysql_group = match
    if len(match) == 0:
        debug_info(context)
        context.scenario.skip("Found no groups accord")


@when(u'I found groups with {count:int} instance, or I skip the test')
def count_instances(context, count):
    # query groups with instances
    resp = get_all_group_info(context)
    condition = '.[] | select(.mysql_group_instance_nums == "{0}")'.format(count)
    match = pyjq.all(condition, resp)
    if len(match) == 0:
        context.mysql_group = []
        context.scenario.skip(
            "Found no MySQL group with {0} MySQL instance".format(count))
    else:
        if type(match) != list:
            mysql_group = [1]
            mysql_group[0] = match
            context.mysql_group = mysql_group
        else:
            context.mysql_group = match


def found_for_master_sequence(context, template_values, count):
    match = []
    for group in context.mysql_group:
        mysql_group_id = group["mysql_group_id"]
        instances = get_mysql_info_in_group(context, mysql_group_id)
        user_flag = 0
        for instance in instances:
            if template_values["master_sequence"] == "100" and instance["mysql_instance_master_sequence"] == "100":
                user_flag = user_flag + 1
            elif template_values["master_sequence"] == "0" and instance["mysql_instance_master_sequence"] != "100":
                user_flag = user_flag + 1
        if user_flag == count:
            match.append(group)
    context.mysql_group = match
    if len(match) == 0:
        debug_info(context)
        context.scenario.skip("Found no groups accord")


def des_to_json(key):
    config = ConfigParser()
    config.read("conf/scenarios.conf", encoding="UTF-8")
    fd = config["scenarios"]
    template_values = parse_option_values(fd[key])
    return template_values


def found_for_sla_template(context, template_values):
    match = []
    for group in context.mysql_group:
        if "mysql_group_sla_template" not in group and "mysql_group_ha_policy" not in group and \
                template_values['sla_template'] == "0":
            match.append(group)
        elif "mysql_group_ha_policy" in group and group["mysql_group_ha_policy"] == template_values['sla_template']:
            match.append(group)
        elif "mysql_group_sla_template" in group and \
                group["mysql_group_sla_template"] == template_values['sla_template']:
            match.append(group)
    context.mysql_group = match
    if len(match) == 0:
        debug_info(context)
        context.scenario.skip("Found no groups accord")


def found_for_collect_timeout_sec(context, template_values):
    match = []
    for group in context.mysql_group:
        mysql_group_id = group["mysql_group_id"]
        path = "universe/v3/mysql-groups/"
        key = path + mysql_group_id
        resp = get_config_metadata_info(context, path, key)
        if resp["collect_timeout_sec"] == int(template_values["collect_timeout_sec"]):
            match.append(group)
    context.mysql_group = match
    if len(match) == 0:
        debug_info(context)
        context.scenario.skip("Found no groups accord")


def found_for_ignore_guard_action(context, template_values):
    match = []
    for group in context.mysql_group:
        mysql_group_id = group["mysql_group_id"]
        path = "universe/v3/mysql-groups-status/"
        key = path + mysql_group_id
        resp = get_config_metadata_info(context, path, key)
        if bool(int(template_values['ignore_guard_action'])) == resp["ignore_guard_action"]:
            match.append(group)
    context.mysql_group = match
    if len(match) == 0:
        debug_info(context)
        context.scenario.skip("Found no groups accord")


def found_for_data_supply_from_slave(context, template_values):
    match = []
    for group in context.mysql_group:
        mysql_group_id = group["mysql_group_id"]
        path = "universe/v3/mysql-groups-status/"
        key = path + mysql_group_id
        resp = get_config_metadata_info(context, path, key)
        if bool(int(template_values['data_supply_from_slave'])) == resp["data_supply_from_slave"]:
            match.append(group)
    context.mysql_group = match
    if len(match) == 0:
        debug_info(context)
        context.scenario.skip("Found no groups accord")


def found_for_repl_ip(context, template_values, count):
    match = []
    for group in context.mysql_group:
        mysql_group_id = group["mysql_group_id"]
        instances = get_mysql_info_in_group(context, mysql_group_id)
        instance_flag = 0
        for instance in instances:
            mysql_instance_id = instance["mysql_instance_id"]
            path = "universe/v3/mysqls/"
            key = path + mysql_instance_id
            resp = get_config_metadata_info(context, path, key)
            server_id = instance["server_id"]
            for server in context.server_info_list:
                if server_id == "server-" + server["host_name"]:
                    repl_ip = server["ip_2"]
            if template_values["repl_ip"] == "0" and resp["repl_ip"] == "":
                instance_flag = instance_flag + 1
            elif template_values["repl_ip"] == "1" and resp["repl_ip"] == repl_ip:
                instance_flag = instance_flag + 1
        if instance_flag == count:
            match.append(group)
    context.mysql_group = match
    if len(match) == 0:
        debug_info(context)
        context.scenario.skip("Found no groups accord")


def found_for_uguard(context, template_values, count):
    match = []
    for group in context.mysql_group:
        mysql_group_id = group["mysql_group_id"]
        instances = get_mysql_info_in_group(context, mysql_group_id)
        flag = 0
        for instance in instances:
            if template_values['uguard'] == "1" and instance["uguard_status"] == "UGUARD_ENABLE":
                flag = flag + 1
            elif template_values['uguard'] == "0" and instance["uguard_status"] == "MANUAL_EXCLUDE_HA":
                flag = flag + 1
        if flag == count:
            match.append(group)
    context.mysql_group = match
    if len(match) == 0:
        debug_info(context)
        context.scenario.skip("Found no groups accord")


def found_for_sip(context, template_values, count):
    match = []
    if template_values["sip"] == "0":
        for group in context.mysql_group:
            if "mysql_group_sip" not in group:
                mysql_group_id = group["mysql_group_id"]
                instances = get_mysql_info_in_group(context, mysql_group_id)
                sip_flag = 0
                for instance in instances:
                    if "mysql_instance_useable_sip" not in instance:
                        sip_flag = sip_flag + 1
                if sip_flag == count:
                    match.append(group)

    elif template_values["sip"] == "1":
        for group in context.mysql_group:
            if "mysql_group_sip" in group:
                group_sip = group["mysql_group_sip"]
                mysql_group_id = group["mysql_group_id"]
                instances = get_mysql_info_in_group(context, mysql_group_id)
                sip_flag = 0
                for instance in instances:
                    if "mysql_instance_useable_sip" in instance and instance["mysql_instance_useable_sip"] == group_sip:
                        sip_flag = sip_flag + 1
                if sip_flag == count:
                    match.append(group)

    elif template_values["sip"] == "2":
        for group in context.mysql_group:
            if "mysql_group_sip" in group:
                mysql_group_id = group["mysql_group_id"]
                instances = get_mysql_info_in_group(context, mysql_group_id)
                sip_flag = 0
                for instance in instances:
                    if instance["mysql_instance_useable_sip"] == group["mysql_group_sip"]:
                        sip_flag = sip_flag + 1
                if sip_flag != count:
                    match.append(group)
    context.mysql_group = match
    if len(match) == 0:
        debug_info(context)
        context.scenario.skip("Found no groups accord")


def found_for_readonly(context, template_values, count):
    match = []
    for group in context.mysql_group:
        mysql_group_id = group["mysql_group_id"]
        instances = get_mysql_info_in_group(context, mysql_group_id)
        condition_master = '.[] | select(."mysql_instance_role" == "STATUS_MYSQL_MASTER") | ' \
                           'select(."mysql_instance_readonly" == "0")'
        master = pyjq.all(condition_master, instances)
        if len(master) != 0:
            slave_0 = pyjq.all('.[] | select(."mysql_instance_role" == "STATUS_MYSQL_SLAVE") | '
                               'select(."mysql_instance_readonly" == "0")', instances)
            slave_1 = pyjq.all('.[] | select(."mysql_instance_role" == "STATUS_MYSQL_SLAVE") | '
                               'select(."mysql_instance_readonly" == "1")', instances)
            if count == 2:
                if template_values["readonly"] == "0" and len(slave_1) == 0:
                    match.append(group)
                elif template_values["readonly"] == "1" and len(slave_0) == 0:
                    match.append(group)
            elif count == 3:
                if template_values["readonly"] == "0" and len(slave_1) == 0:
                    match.append(group)
                elif template_values["readonly"] == "1" and len(slave_0) == 1 and len(slave_1) == 1:
                    match.append(group)
                elif len(slave_0) == 0:
                    context.scenario.skip("Found all slave readonly")
            elif count == 5:
                if template_values["readonly"] == "0" and len(slave_0) == 4:
                    match.append(group)
                elif template_values["readonly"] == "1" and len(slave_1) == 4:
                    match.append(group)
    context.mysql_group = match
    if len(match) == 0:
        debug_info(context)
        context.scenario.skip("Found no groups accord")


def load_yaml_config(config_path):
    with open(config_path, 'r') as f:
        parsed = yaml.load(f)
    return parsed


def get_all_nodes(docker_compose):
    server_info_list = []
    i = 0
    for _, node_info in docker_compose['services'].items():
        if node_info['hostname'] == 'deploy':
            continue
        dict_list = {}
        server_info_list.append(dict_list)
        server_info_list[i]['host_name'] = node_info['hostname']
        server_info_list[i]['ip_1'] = node_info['networks']['quick_net']['ipv4_address']
        server_info_list[i]['ip_2'] = node_info['networks']['quick_net_1']['ipv4_address']
        i = i + 1
    return server_info_list
