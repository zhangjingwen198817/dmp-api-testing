import copy
from random import *

import pyjq
from behave import *
from hamcrest import *

from database import *

LOGGER = logging.getLogger("steps.instance")
use_step_matcher("cfparse")


@given(u'I config the installed MySQL group and instance')
def step_imp(context):
    context.list_A = ["1m1s-A1", "1m1s-A2", "1m1s-A3"]
    context.list_B = ["1m2s-B1", "1m2s-B2", "1m2s-B3", "1m2s-B4", "1m2s-B5", "1m2s-B6", "1m2s-B7", "1m2s-B8",
                      "1m2s-B9", "1m2s-B10", "1m2s-B11", "1m2s-B12"]
    context.list_C = ["1m4s-C1", "1m4s-C2", "1m4s-C3", "1m4s-C4", "1m4s-C5"]
    context.list_test_54 = ["1m4s-C5", "1m4s-C2", "1m4s-C4"]
    context.list_test_52 = ["1m2s-B4", "1m2s-B5", "1m2s-B6", "1m2s-B7"]

    # prepare valid sip pool
    get_all_valid_sip(context)

    # prepare tag pool
    list_all = []
    list_all.extend(context.list_A)
    list_all.extend(context.list_B)
    list_all.extend(context.list_C)
    tag_pool_prepare(context, list_all)

    # get all config for repl_ip
    docker_compose = readYaml("deploy/compose/docker-compose.yaml")
    context.server_info_list = get_all_nodes(docker_compose)

    # prepare all config
    if judge_group_amount(context, 2) != 0:
        config_mysql(context, 2)
    if judge_group_amount(context, 3) != 0:
        config_mysql(context, 3)
    if judge_group_amount(context, 5) != 0:
        config_mysql(context, 5)


def judge_group_amount(context, count):
    resp = get_all_group_info(context)
    condition = '.[] | select(.mysql_group_instance_nums == "{0}")'.format(count)
    match = pyjq.all(condition, resp)
    return len(match)


def config_mysql(context, count):
    count_instances(context, count)
    groups = context.mysql_group
    if count == 2:
        scenario_list = context.list_A
    elif count == 3:
        scenario_list = context.list_B
        # scenario_list = context.list_test_52
    elif count == 5:
        scenario_list = context.list_C
        # scenario_list = context.list_test_54
        add_ha_policy_protocol(context, "ha_policy")
        add_tag_zone_pool(context)

    if count == 3:
        bool_group = False
        for group in groups:
            mysql_group_id = group["mysql_group_id"]
            list_instance = get_mysql_info_in_group(context, mysql_group_id)
            for instance in list_instance:
                path = "universe/v3/mysqls/"
                key = path + instance["mysql_instance_id"]
                resp = get_config_metadata_info(context, path, key)
                value_resp = resp["loose_io_flush_param_check"]
                if value_resp:
                    group_temp = group
                    groups.remove(group)
                    bool_group = True
                    break
            break
        bool_list = False
        for i in range(len(scenario_list)):
            if scenario_list[i] == "1m2s-B2":
                del scenario_list[i]
                bool_list = True
                break
        if bool_group and bool_list:
            groups.insert(0, group_temp)
            scenario_list.insert(0, "1m2s-B2")

    for i in range(len(scenario_list)):
        key = scenario_list[i]
        context.template_values = des_to_json(key)
        group = groups[i]
        mysql_group_id = group["mysql_group_id"]

        # add a tag
        add_tag(context, mysql_group_id, key)

        # update the config
        update_group_udelay_enable(context, group)
        bind_sla_protocol(context, group)
        update_sip(context, group)
        update_uguard_status(context, mysql_group_id)
        edit_mysql_config_sequence(context, group)
        edit_mysql_config_readonly(context, group)
        update_data_supply_from_slave(context, mysql_group_id)
        update_ignore_guard_action(context, mysql_group_id)
        update_collect_timeout_sec(context, mysql_group_id)
        update_repl_ip(context, mysql_group_id)
        if count == 5:
            config_instance_zone(context, mysql_group_id)

        # assert if config successful
        found_mysql(context, key, count)
        length = len(context.mysql_group)
        context.config_dict = {}
        try:
            assert (length != 0), "config {0} failed".format(key)
            context.config_dict[key] = 1
        except AssertionError as e:
            context.config_dict[key] = 0
            print(str(e) + "\n")


@then(u'all the MySQL should config OK')
def assert_config(context):
    for key in context.config_dict:
        if context.config_dict[key] == 0:
            assert False, "Some config failed"


def update_repl_ip(context, group_id):
    value = context.template_values["repl_ip"]
    list_instance = get_mysql_info_in_group(context, group_id)
    for instance in list_instance:
        if value == "0":
            api_request_post(context, context.version_3 + "/helper/mysql/instance/update_repl_ip", {
                "is_sync": True,
                "mysql_instance_id": instance["mysql_instance_id"]
            })
        elif value == "1":
            server_id = instance["server_id"]
            for server in context.server_info_list:
                if server_id == "server-" + server["host_name"]:
                    api_request_post(context, context.version_3 + "/helper/mysql/instance/update_repl_ip", {
                        "is_sync": True,
                        "mysql_instance_id": instance["mysql_instance_id"],
                        "repl_ip": server["ip_2"],
                    })


def update_collect_timeout_sec(context, mysql_group_id):
    value = int(context.template_values["collect_timeout_sec"])
    api_request_post(context, context.version_3 + "/helper/mysql/group/update_collect_timeout_sec", {
        "is_sync": True,
        "mysql_group_id": mysql_group_id,
        "timeout": value
    })


def update_ignore_guard_action(context, mysql_group_id):
    value = context.template_values["ignore_guard_action"]
    if value == "0":
        flag = False
    elif value == "1":
        flag = True
    api_post(context, context.version_3 + "/helper/mysql/group/update_uguard_action_switch", {
        "is_sync": True,
        "mysql_group_id": mysql_group_id,
        "is_enabled": flag,
    })


def update_data_supply_from_slave(context, mysql_group_id):
    value = context.template_values["data_supply_from_slave"]
    if value == "0":
        flag = False
    elif value == "1":
        flag = True
    api_post(context, context.version_3 + "/helper/mysql/group/update_data_supply_from_slave_switch", {
        "is_sync": True,
        "mysql_group_id": mysql_group_id,
        "is_enabled": flag,
    })


def update_uguard_status(context, mysql_group_id):
    value = context.template_values["uguard"]
    instances = get_mysql_info_in_group(context, mysql_group_id)
    for instance in instances:
        if instance["mysql_instance_role"] == "STATUS_MYSQL_MASTER":
            instance_master = instance
            break
    instances.remove(instance_master)
    if value == "1" and instance["uguard_status"] != "UGUARD_ENABLE":
        instances.insert(0, instance_master)
        for instance in instances:
            api_post(context, context.version_3 + "/database/start_mysql_ha_enable", {
                "is_sync": True,
                "group_id": mysql_group_id,
                "mysql_id": instance["mysql_instance_id"],
            })
    elif value == "0" and instance["uguard_status"] != "MANUAL_EXCLUDE_HA":
        instances.append(instance_master)
        for instance in instances:
            api_request_post(context, context.version_3 + "/database/stop_mysql_ha_enable", {
                "is_sync": True,
                "group_id": mysql_group_id,
                "mysql_id": instance["mysql_instance_id"],
            })


def update_group_udelay_enable(context, group):
    value = context.template_values["group_udelay_enable"]
    if value == "0":
        if group["mysql_group_udelay_enable"] == "1":
            api_post(context, context.version_3 + "/database/pause_udelay_detection", {
                "is_sync": True,
                "group_id": group["mysql_group_id"],
            })
    elif value == "1":
        if group["mysql_group_udelay_enable"] == "0":
            mysql_group_id = group["mysql_group_id"]
            resp = get_mysql_info_in_group(context, mysql_group_id)
            instance = pyjq.first('.[]|select(."mysql_instance_role" == "STATUS_MYSQL_MASTER")', resp)
            mysql_instance_id = instance["mysql_instance_id"]
            api_post(context, context.version_3 + "/database/start_udelay_detection", {
                "is_sync": True,
                "udelay_user": "universe_op",
                "group_id": mysql_group_id,
                "master_instance": mysql_instance_id,
                "is_update_password": False,
            })


def bind_sla_protocol(context, group):
    value = context.template_values["sla_template"]
    body = {}
    if value == "SLA_RPO_sample":
        body = {
            "group_id": group["mysql_group_id"],
            "add_sla_template": value,
            "is_sync": True
        }
    elif value == "SLA_RTO_sample":
        body = {
            "group_id": group["mysql_group_id"],
            "add_sla_template": value,
            "is_sync": True
        }
    elif value == "ha_policy":
        body = {
            "group_id": group["mysql_group_id"],
            "add_sla_template": context.sla_template["name"],
            "is_sync": True
        }
    elif value == "0":
        pass
    api_request_post(context, context.version_3 + "/database/add_sla_protocol", body)
    start_sla_protocol(context, group)


def add_ha_policy_protocol(context, type):
    sla_template = "ha_policy"
    body = {
        "name": sla_template,
        "sla_type": type,
        "ha_policy_failover_election": "HA_POLICY_FAILOVER_ELECTION_SAME_ZONE",
        "ha_policy_semisync_count": "HA_POLICY_SEMISYNC_COUNT_MINUS_ONE_MINIMUM_ONE",
        "is_sync": True
    }
    api_request_post(context, context.version_4 + "/mysql/group/ha_policy/add", body)
    context.sla_template = {"name": sla_template}


def start_sla_protocol(context, group):
    api_request_post(context, context.version_3 + "/database/start_sla_protocol", {
        "group_id": group['mysql_group_id'],
        "is_sync": True,
    })


def update_sip(context, group):
    value = context.template_values["sip"]
    if value == "0" and "mysql_group_sip" in group:
        api_post(context, context.version_3 + "/database/update_mysql_sip", {
            "is_sync": True,
            "group_id": group["mysql_group_id"],
            "sip": "",
        })
        mysql_group_id = group["mysql_group_id"]
        instances = get_mysql_info_in_group(context, mysql_group_id)
        for instance in instances:
            if "mysql_instance_useable_sip" in instance:
                api_post(context, context.version_3 + "/database/update_mysql_instance_sip", {
                    "is_sync": True,
                    "mysql_id": instance["mysql_instance_id"],
                    "sip": "",
                })
                context.valid_sip.insert(0, instance["mysql_instance_useable_sip"])
    elif value == "1":
        mysql_group_id = group["mysql_group_id"]
        instances = get_mysql_info_in_group(context, mysql_group_id)
        if "mysql_group_sip" not in group:
            sip = context.valid_sip[0]
            context.valid_sip.pop(0)
            api_post(context, context.version_3 + "/database/update_mysql_sip", {
                "is_sync": True,
                "group_id": group["mysql_group_id"],
                "sip": sip,
            })
        else:
            sip = group["mysql_group_sip"]
        for instance in instances:
            if "mysql_instance_useable_sip" not in instance or instance["mysql_instance_useable_sip"] != sip:
                api_post(context, context.version_3 + "/database/update_mysql_instance_sip", {
                    "is_sync": True,
                    "mysql_id": instance["mysql_instance_id"],
                    "sip": sip,
                })
    elif value == "2":
        mysql_group_id = group["mysql_group_id"]
        instances = get_mysql_info_in_group(context, mysql_group_id)
        instance = instances[0]
        if "mysql_group_sip" not in group:
            sip = context.valid_sip[0]
            context.valid_sip.pop(0)
            api_post(context, context.version_3 + "/database/update_mysql_sip", {
                "is_sync": True,
                "group_id": group["mysql_group_id"],
                "sip": sip,
            })
        else:
            sip = group["mysql_group_sip"]
        if "mysql_instance_useable_sip" not in instance or instance["mysql_instance_useable_sip"] == sip:
            ins_sip = context.valid_sip[0]
            context.valid_sip.pop(0)
            api_post(context, context.version_3 + "/database/update_mysql_instance_sip", {
                "is_sync": True,
                "mysql_id": instance["mysql_instance_id"],
                "sip": ins_sip,
            })


def edit_mysql_config_sequence(context, group):
    list_instance = get_mysql_info_in_group(context, group["mysql_group_id"])
    valuse = context.template_values['master_sequence']
    master_sequence = [10, 60, 90, 120, 160]
    if valuse == "100":
        for instance in list_instance:
            body = {
                "server_id": instance['server_id'],
                "mysql_id": instance['mysql_instance_id'],
                "config": "master-sequence",
                "value": 100,
                "is_sync": True,
            }
            api_request_post(context, context.version_3 + "/database/edit_mysql_config", body)
    elif valuse == "0":
        i = 0
        for instance in list_instance:
            body = {
                "server_id": instance['server_id'],
                "mysql_id": instance['mysql_instance_id'],
                "config": "master-sequence",
                "value": master_sequence[i],
                "is_sync": True,
            }
            api_request_post(context, context.version_3 + "/database/edit_mysql_config", body)
            i = i + 1


def edit_mysql_config_readonly(context, group):
    list_instance = get_mysql_info_in_group(context, group["mysql_group_id"])
    valuse = context.template_values['readonly']

    if valuse == "0":
        for instance in list_instance:
            if instance['mysql_instance_role'] == "STATUS_MYSQL_MASTER":
                continue
            body = {
                "server_id": instance['server_id'],
                "mysql_id": instance['mysql_instance_id'],
                "config": "readonly",
                "value": 0,
                "is_sync": True,
            }
            api_request_post(context, context.version_3 + "/database/edit_mysql_config", body)
    elif valuse == "1":
        info = get_group_info_by_id(context, group["mysql_group_id"])
        if info['mysql_group_instance_nums'] == "2":
            for instance in list_instance:
                if instance['mysql_instance_role'] == "STATUS_MYSQL_MASTER":
                    continue
                body = {
                    "server_id": instance['server_id'],
                    "mysql_id": instance['mysql_instance_id'],
                    "config": "readonly",
                    "value": 1,
                    "is_sync": True,
                }
                api_request_post(context, context.version_3 + "/database/edit_mysql_config", body)
        elif info['mysql_group_instance_nums'] == "3":
            for instance in list_instance:
                if instance['mysql_instance_role'] == "STATUS_MYSQL_MASTER":
                    continue
                body = {
                    "server_id": instance['server_id'],
                    "mysql_id": instance['mysql_instance_id'],
                    "config": "readonly",
                    "value": 1,
                    "is_sync": True,
                }
                api_request_post(context, context.version_3 + "/database/edit_mysql_config", body)
                return
        elif int(info['mysql_group_instance_nums']) > 3:
            for instance in list_instance:
                if instance['mysql_instance_role'] == "STATUS_MYSQL_MASTER":
                    continue
                body = {
                    "server_id": instance['server_id'],
                    "mysql_id": instance['mysql_instance_id'],
                    "config": "readonly",
                    "value": 1,
                    "is_sync": True,
                }
                api_request_post(context, context.version_3 + "/database/edit_mysql_config", body)


def add_tag(context, mysql_group_id, key):
    api_post(context, context.version_3 + "/mysql/group/tag/add", {
        "is_sync": True,
        "mysql_group_id": mysql_group_id,
        "tag_attribute": "scenarios",
        "tag_value": key,
    })


def tag_pool_prepare(context, list_all):
    resp = get_all_tag_info(context)
    tag_list = pyjq.all('.[] | select(."tag_attribute" == "scenarios")', resp)
    if len(tag_list) == 0:
        for i in range(0, len(list_all)):
            api_post(context, context.version_4 + "/tag/add", {
                "is_sync": True,
                "tag_attribute": "scenarios",
                "tag_value": list_all[i],
                "tag_color": "blue",
            })


def add_tag_zone_pool(context):
    zone = ["徐汇", "浦东", "漕河泾"]
    for tem in zone:
        body = {
            "tag_attribute": "zone",
            "tag_value": tem,
            "tag_color": "blue",
            "is_sync": True,
        }
        api_request_post(context, context.version_4 + "/tag/add", body)


def config_instance_zone(context, mysql_group_id):
    mysql_info = get_mysql_info_in_group(context, mysql_group_id)
    same_park = []
    different_park = []
    for mysql in mysql_info:
        if mysql['mysql_instance_role'] == "STATUS_MYSQL_MASTER":
            same_park.append(mysql)
        elif mysql['mysql_instance_role'] == "STATUS_MYSQL_SLAVE" and mysql[
            'mysql_instance_installation_standard'] == "uguard_repl":
            different_park.append(mysql)
    mysql_info.remove(same_park[0])
    mysql_info.remove(different_park[0])
    mysql = choice(mysql_info)
    same_park.append(mysql)
    mysql_info.remove(mysql)
    different_park.extend(mysql_info)
    for info in same_park:
        body = {
            "attribute": "zone",
            "value": "徐汇",
            "server_id": info["server_id"],
        }
        api_request_post(context, context.version_3 + "/server/add_tag", body)
    for temp_info in different_park:
        body = {
            "attribute": "zone",
            "value": "浦东",
            "server_id": temp_info["server_id"],
        }
        api_request_post(context, context.version_3 + "/server/add_tag", body)


@when(u'I reset MySQL instance in group')
def reset_instance_group(context):
    assert context.mysql_group != None
    resps = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    mysql_info = pyjq.first('.[]|select(."mysql_instance_role"=="STATUS_MYSQL_SLAVE")', resps)
    context.mysql_instance = mysql_info
    context.execute_steps(u"""
                When I make a manual backup on the MySQL instance
                Then the response is ok
                When I stop MySQL instance ha enable
                Then the response is ok
                And MySQL instance ha enable should stopped in 2m
                When I reset database instance
                Then the response is ok
                And reset database instance should succeed in 2m
                When I enable the MySQL instance HA
                Then the response is ok
                And MySQL instance HA status should be running in 1m                
                                  """)


@when(u'I promote the slave instance to master')
def step_imp(context):
    assert context.mysql_group != None
    resps = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    if int(context.mysql_group[0]["mysql_group_instance_nums"]) < 5:
        the_slave = pyjq.first('.[]|select(."mysql_instance_role" == "STATUS_MYSQL_SLAVE")',
                               resps)
        body = {
            "mysql_id": the_slave['mysql_instance_id'],
            "is_sync": True
        }
    else:
        the_slave = pyjq.first('.[]|select(."mysql_instance_role" == "STATUS_MYSQL_SLAVE" '
                               'and ."mysql_instance_installation_standard" != "uguard_repl")',
                               resps)
        body = {
            "mysql_id": the_slave['mysql_instance_id'],
            "is_sync": True
        }
    resp = api_post(context, context.version_3 + "/database/promote_to_master", body)
    progress_id = resp['progress_id']
    context.execute_steps(u"""
        Then wait for progress {0} is finished in {1}s
        """.format(progress_id, 120))
    context.slave_instance = the_slave


@when(u'I disable the MySQL instance HA in group')
def disable_instance_ha(context):
    assert context.mysql_group != None
    resps = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    mysql = pyjq.first(
        '.[] | select(.mysql_instance_status == "STATUS_MYSQL_HEALTH_OK" and '
        '.uguard_status == "UGUARD_ENABLE" and ."mysql_instance_role" == "STATUS_MYSQL_SLAVE" )'
        , resps)
    body = {
        "server_id": mysql['server_id'],
        "group_id": mysql['mysql_group_id'],
        "mysql_id": mysql['mysql_instance_id'],
        "is_sync": True
    }
    resp = api_post(context, context.version_3 + "/database/stop_mysql_ha_enable", body)
    progress_id = resp['progress_id']
    context.execute_steps(u"""
            Then wait for progress {0} is finished in {1}s
            """.format(progress_id, 30))
    context.mysql_instance = mysql


@when(u'I enable the MySQL instance HA in group')
def enable_instance_ha(context):
    assert context.mysql_group != None
    resps = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    mysql = pyjq.first(
        '.[] | select(.mysql_instance_status == "STATUS_MYSQL_HEALTH_OK" and '
        '.uguard_status != "UGUARD_ENABLE" and ."mysql_instance_role" == "STATUS_MYSQL_SLAVE" )'
        , resps)
    body = {
        "server_id": mysql['server_id'],
        "group_id": mysql['mysql_group_id'],
        "mysql_id": mysql['mysql_instance_id'],
        "is_sync": True
    }
    resp = api_post(context, context.version_3 + "/database/start_mysql_ha_enable", body)
    progress_id = resp['progress_id']
    context.execute_steps(u"""
            Then wait for progress {0} is finished in {1}s
            """.format(progress_id, 30))
    context.mysql_instance = mysql


@when(u'I {action:string} the MySQL instance in group')
def action_instance(context, action):
    assert context.mysql_group != None
    resps = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    if action == "stop":
        mysql = pyjq.first(
            '.[] | select(.mysql_instance_status == "STATUS_MYSQL_HEALTH_OK" and ."mysql_instance_role" == "STATUS_MYSQL_SLAVE" )'
            , resps)
        context.mysql_instance = mysql
        if mysql['uguard_status'] == "UGUARD_ENABLE":
            context.execute_steps(u"""
            When I stop MySQL instance ha enable
            Then the response is ok
            And MySQL instance ha enable should stopped in 1m
            When I stop MySQL service
            Then stop MySQL service should succeed in 1m
            """)
        else:
            context.execute_steps(u"""
            When I stop MySQL service
            Then stop MySQL service should succeed in 1m
                        """)
    elif action == "start":
        context.execute_steps(u"""
            When I start MySQL service
            And I enable the MySQL instance HA
            Then the response is ok
            And MySQL instance HA status should be running in 1m
                                """)


@when(u'I start MySQL service')
def step_imp(context):
    assert context.mysql_instance != None
    body = {
        "server_id": context.mysql_instance['server_id'],
        "mysql_id": context.mysql_instance['mysql_instance_id'],
        "is_sync": True,
    }
    resp = api_post(context, context.version_3 + "/database/start_mysql_service", body)
    progress_id = resp['progress_id']
    context.execute_steps(u"""
                Then wait for progress {0} is finished in {1}s
                """.format(progress_id, 30))


@when(u'I make a manual backup with {tool:string} in group')
def step_impl(context, tool):
    assert context.mysql_group != None
    resps = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    mysql = pyjq.first(
        '.[] | select(.mysql_instance_status == "STATUS_MYSQL_HEALTH_OK" and '
        '."mysql_instance_role" == "STATUS_MYSQL_SLAVE" )'
        , resps)
    context.mysql_instance = mysql
    resp = api_get(context, context.version_3 + "/urman_backupset/list", {
        "instance": context.mysql_instance["mysql_instance_id"],
    })
    origin_id = pyjq.first('.data[] | .backup_set_id', resp)
    context.origin_id = origin_id

    cnf = api_get(context, context.version_3 + "/support/read_umc_file", {
        "path": "backupcnfs/backup.{0}".format(tool.lower()),
    })

    resp = api_post(
        context, context.version_3 + "/database/manual_backup", {
            "is_sync": True,
            "mysql_id": context.mysql_instance["mysql_instance_id"],
            "backup_tool": tool,
            "backup_cnf": cnf,
        })
    progress_id = resp['progress_id']
    context.execute_steps(u"""
                    Then wait for progress {0} is finished in {1}s
                    """.format(progress_id, 60))


@then(
    u'the MySQL group manual backup list should contains the urman backup set in {duration:time}'
)
def step_impl(context, duration):
    assert context.mysql_instance != None
    mysql_id = context.mysql_instance["mysql_instance_id"]

    def condition(context, flag):
        resp = get_backup_set_list_by_instance_id(context, mysql_id)
        id = pyjq.first('.[] | .urman_backup_set_id', resp)
        if id != context.origin_id:
            return True

    waitfor(context, condition, duration)


@when(u'I pause HA and stop copying the MySQL instance in group')
def step_imp(context):
    assert context.mysql_group != None
    resps = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    slave_info = pyjq.first(
        '.[] | select(.mysql_instance_role == "STATUS_MYSQL_SLAVE" and .uguard_status == "UGUARD_ENABLE")',
        resps)
    assert slave_info is not None
    context.mysql_instance = slave_info
    body = {
        "group_id": slave_info['mysql_group_id'],
        "mysql_id": slave_info['mysql_instance_id'],
        "is_sync": True,
    }
    resp = api_post(context, context.version_3 + "/database/isolate_mysql", body)
    progress_id = resp['progress_id']
    context.execute_steps(u"""
                        Then wait for progress {0} is finished in {1}s
                        """.format(progress_id, 60))


@then(
    u'the MySQL instance {replication_status:string} and {uguard_status:string} should be {status:string} in {duration:time}')
def step_imp(context, replication_status, uguard_status, status, duration):
    assert context.mysql_instance != None

    def condition(context, flag):
        mysql_info = get_mysql_info_by_id(context, context.mysql_instance['mysql_instance_id'])
        if status == "running":
            if mysql_info['mysql_instance_replication_status'] == replication_status and mysql_info[
                'uguard_status'] == uguard_status:
                return True
        else:
            if mysql_info['mysql_instance_replication_status'] == replication_status and mysql_info[
                'uguard_status'] == uguard_status:
                return True

    waitfor(context, condition, duration)


@when(u'I takeover MySQL instance in group')
def step_imp(context):
    assert context.mysql_group[0]["mysql_group_id"] != None
    assert context.mysql_instance != None
    mysql_instance_id = "mysql-" + generate_id()
    passwd = get_master_root_password(context)
    body = {
        "server_id": context.mysql_instance['server_id'],
        "group_id": context.mysql_instance['mysql_group_id'],
        "port": context.mysql_instance['mysql_instance_port'],
        "mysql_id": mysql_instance_id,
        "mysql_alias": context.mysql_instance['mysql_instance_alias'],
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
        "run_user_group": context.mysql_instance['mysql_instance_run_user_group'],
        "mysql_uid": "",
        "mysql_gid": "",
        "umask": "0640",
        "umask_dir": "0750",
        "tag_list": "[]",
        "resource": "0"
    }
    resp = api_post(context, context.version_3 + "/database/takeover_instance", body)
    progress_id = resp['progress_id']
    context.execute_steps(u"""
                            Then wait for progress {0} is finished in {1}s
                            """.format(progress_id, 120))
    context.mysql_instance_id = mysql_instance_id


@then(u'the MySQL instance should be {exist:string} in group')
def step_imp(context, exist):
    assert context.mysql_group != None
    assert context.mysql_instance != None

    def condition(context, flag):
        if exist == "exist":
            resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
            match = pyjq.first(
                '.[] | select(."mysql_instance_id" == "{0}")'.format(
                    context.mysql_instance_id), resp)
            if match is not None:
                return True

        else:
            resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
            match = pyjq.first(
                '.| any(."mysql_instance_id" == "{0}")'.format(
                    context.mysql_instance['mysql_instance_id']), resp)
            if match is not True:
                return True

    waitfor(context, condition, 120)
    if exist == "exist":
        context.mysql_instance = get_mysql_info_by_id(context, context.mysql_instance_id)


@when(u'I stop delay detection')
def step_impl(context):
    assert context.mysql_group is not None
    api_request_post(context, context.version_3 + "/database/pause_udelay_detection", {
        "group_id": context.mysql_group[0]["mysql_group_id"],
        "is_sync": True
    })


@when(u'I start delay detection')
def step_impl(context):
    assert context.mysql_group is not None
    mysql_group_id = context.mysql_group[0]["mysql_group_id"]
    instances = get_mysql_info_in_group(context, mysql_group_id)
    match = pyjq.first('.[]|select(."mysql_instance_role"=="STATUS_MYSQL_MASTER")', instances)
    assert match is not None

    api_request_post(context, context.version_3 + "/database/start_udelay_detection", {
        "is_sync": True,
        "group_id": mysql_group_id,
        "udelay_user": context.mysql_group[0]["mysql_group_udelay_user"],
        "is_update_password": "false",
        "master_instance": match["mysql_instance_id"],
        "status": "start"
    })


@then(u'{operate} delay detection should succeed in {duration:time}')
def step_impl(context, operate, duration):
    assert context.mysql_group is not None

    def condition(context, flag):
        resp = get_all_group_info(context)
        if operate == "start":
            match = pyjq.first(
                '.[]|select(."mysql_group_id"=="{0}" and ."mysql_group_udelay_enable"=="1")'.format(
                    context.mysql_group[0]["mysql_group_id"]), resp)
        elif operate == "stop":
            match = pyjq.first(
                '.[]|select(."mysql_group_id"=="{0}" and ."mysql_group_udelay_enable"=="0")'.format(
                    context.mysql_group[0]["mysql_group_id"]), resp)
        if match is not None:
            return True

    waitfor(context, condition, duration)


@then(u'the MySQL instance {should_or_not:should_or_not} be in the MySQL instance list')
def step_impl(context, should_or_not):
    assert context.mysql_instance != None
    mysql_instance_id = context.mysql_instance["mysql_instance_id"]
    resp = get_all_mysql_info(context)
    match = pyjq.first('.[] | select(."mysql_instance_id" == "{0}")'.format(mysql_instance_id), resp)
    assert (match is not None and should_or_not) or (match is None and not should_or_not)


@when(u'I stop monitoring')
def step_impl(context):
    assert context.mysql_group is not None
    api_request_post(context, context.version_3 + "/database/pause_monitor_group", {
        "group_id": context.mysql_group[0]["mysql_group_id"],
        "is_sync": True
    })


@when(u'I start monitoring')
def step_impl(context):
    assert context.mysql_group is not None
    api_request_post(context, context.version_3 + "/database/start_monitor_group", {
        "is_sync": True,
        "group_id": context.mysql_group[0]["mysql_group_id"],
        "ustats_user": context.mysql_group[0]["mysql_group_ustats_user"],
        "is_update_password": "false"
    })


@then(u'{operate} monitoring should succeed in {duration:time}')
def step_impl(context, operate, duration):
    assert context.mysql_group is not None

    def condition(context, flag):
        resp = get_all_group_info(context)
        if operate == "start":
            match = pyjq.first(
                '.[]|select(."mysql_group_id"=="{0}" and ."mysql_group_ustats_status"=="1")'.format(
                    context.mysql_group[0]["mysql_group_id"]), resp)
        elif operate == "stop":
            match = pyjq.first(
                '.[]|select(."mysql_group_id"=="{0}" and ."mysql_group_ustats_status"=="0")'.format(
                    context.mysql_group[0]["mysql_group_id"]), resp)
        if match is not None:
            return True

    waitfor(context, condition, duration)


@when(u'I upgrade MySQL instance with {tar:string}')
def step_imp(context, tar):
    assert context.mysql_group[0]["mysql_group_id"] != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    mysql_info = pyjq.first('.[] | select(.mysql_instance_role == "STATUS_MYSQL_SLAVE" and '
                            '.uguard_status == "UGUARD_ENABLE")', resp)

    version = tar.split("-")[1]
    passwd = get_master_root_password(context)
    context.mysql_instance = mysql_info
    context.execute_steps(u"""
            When I stop MySQL instance ha enable
            Then the response is ok
            And MySQL instance ha enable should stopped in 1m
    """)
    mysql_base_path = os.path.dirname(mysql_info['mysql_instance_base_path']) + "/" + version
    body = {
        "server_id": mysql_info['server_id'],
        "mysql_id": mysql_info['mysql_instance_id'],
        "mysql_tarball_path": tar,
        "mysql_base_path": mysql_base_path,
        "mysql_root_password": passwd,
        "version": version
    }
    res = api_post(context, context.version_3 + "/database/upgrade_instance", body)
    progress_id = res['progress_id']
    context.execute_steps(u"""
        Then wait for progress {0} is finished in {1}s
        """.format(progress_id, 120))


@then(u'the MySQL instance upgrade to {tar:string} should succeed')
def step_imp(context, tar):
    assert context.mysql_instance != None
    version = tar.split("-")[1]

    def condition(context, flag):
        mysql = get_mysql_info_by_id(context, context.mysql_instance['mysql_instance_id'])
        if mysql['mysql_instance_tarball_path'] == tar and mysql['mysql_instance_version'] == version and mysql[
            'mysql_instance_status'] == "STATUS_MYSQL_HEALTH_OK":
            return True

    waitfor(context, condition, 60)
    context.execute_steps(u"""
                When I enable the MySQL instance HA
                Then the response is ok
                And MySQL instance HA status should be running in 1m
                                    """)


@when(u'I found a MySQL instance')
def step_impl(context):
    instance = get_all_mysql_info(context)
    if len(instance) == 0:
        context.scenario.skip("No found a MySQL instance")
    context.mysql_instance = instance[0]
    context.mysql_instance_id = instance[0]["mysql_instance_id"]


@when(u'I silent the instance')
def step_impl(context):
    mysql_instance_id = context.mysql_instance_id
    start_time = int(time.time())
    end_time = 31536000000 + start_time
    user_name = "admin"
    api_request_post(context, context.version_3 + "/alert/silence_instances", {
        "instances": mysql_instance_id,
        "start": start_time,
        "end": end_time,
        "created_by": user_name,
    })
    context.start_time = start_time


@then(u'the instance {should_or_not:should_or_not} in the silence list')
def step_impl(context, should_or_not):
    resp = api_get(context, context.version_3 + "/alert/list_silence", {
        "number": context.page_size_to_select_all,
    })
    if should_or_not:
        condition = '.[]|select(."rule_id"=="silence-instance-{0}")|select(."start"=="{1}")' \
            .format(context.mysql_instance_id, context.start_time)
        silence_list = pyjq.all(condition, resp)
        assert len(silence_list) != 0, "the instance silent failed"
    elif not should_or_not:
        condition = '.[]|select(."rule_id"=="silence-instance-{0}")'.format(context.mysql_instance_id)
        silence_list = pyjq.all(condition, resp)
        assert len(silence_list) == 0, "the instance resume failed"


@when(u'I found a MySQL instance in silence')
def step_impl(context):
    resp = api_get(context, context.version_3 + "/alert/list_silence", {
        "number": context.page_size_to_select_all,
    })
    instances = pyjq.all('.[]', resp)
    for instance in instances:
        # spilt information from "silence-server-server-udp9"
        instance_info = instance["rule_id"].split("-", 2)
        if instance_info[1] == "instance":
            mysql_instance_id = instance_info[2]
            context.mysql_instance_id = mysql_instance_id
            context.rule_id = instance["rule_id"]
            break


@when(u'I resume the instance from silence')
def step_impl(context):
    rule_id = context.rule_id
    api_request_post(context, context.version_3 + "/alert/remove_silence", {
        "is_sync": True,
        "rule_id": rule_id,
    })


@when(u'I delete MySQL instance')
def delete_instance(context):
    assert context.mysql_group[0]["mysql_group_id"] != None
    resp = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    mysql_info = pyjq.first('.[] | select(.mysql_instance_role == "STATUS_MYSQL_SLAVE" and '
                            '.uguard_status == "UGUARD_ENABLE")', resp)
    context.mysql_instance = mysql_info
    context.execute_steps(u"""
            When I stop MySQL instance ha enable
            Then the response is ok
            And MySQL instance ha enable should stopped in 1m 
    """)
    body = {
        "mysql_id": context.mysql_instance['mysql_instance_id'],
        "server_id": context.mysql_instance['server_id'],
        "group_id": context.mysql_instance['mysql_group_id'],
        "force": "1",
        "is_sync": True,
    }
    res = api_post(context, context.version_3 + "/database/delete_instance", body)
    progress_id = res['progress_id']
    context.execute_steps(u"""
            Then wait for progress {0} is finished in {1}s
            """.format(progress_id, 120))


@when(u'I found the server which the instance running on')
def step_impl(context):
    assert context.mysql_instance
    instance = context.mysql_instance
    context.server_id = instance["server_id"]


@when(u'I get the system message log')
def step_impl(context):
    resp = api_get(context, context.version_3 + "/server/get_system_message_log", {
        "server_id": context.server_id,
    })
    context.resp = resp


@when(u'I get the MySQL error log')
def step_impl(context):
    mysql_instance_id = context.mysql_instance_id
    resp = api_get(context, context.version_3 + "/mysql/instance/get_mysql_error_log", {
        "mysql_instance_id": mysql_instance_id,
    })
    context.resp = resp


@then(u'the log is not empty')
def step_impl(context):
    assert context.resp


from framework.api_base import *


@when(u'I batch install in one group MySQL instances')
def batch_install_in_one_group(context):
    assert_that(context.server, not_none(), "but server is : <{0}>".format(context.server))
    server_info = context.server
    context.server = random.sample(server_info, 3)
    group_id = "mysql-test" + str(random.randint(100, 500))
    port = str(3500 + random.randint(10, 90))
    with open("data.json", "w") as f:
        body = {
            "mysql_group": {
                "mysql_group_id": group_id,
                "mysql_group_root_user_password": "test"
            }
        }
        instances = []
        info = {}
        for server in context.server:
            info = {
                "server_id": server['server_id'],
                "mysql_instance_port": port,
                "mysql_instance_tarball_path": "mysql-5.7.21-linux-glibc2.12-x86_64.tar.gz",
                "mysql_instance_installation_standard": "uguard_semi_sync",
                "is_mysql_instance_ha_enabled": True,
                "mysql_instance_base_path": "/opt/mysql/base/5.7.21",
                "mysql_instance_data_path": "/opt/mysql/data/{0}".format(port),
                "mysql_instance_binlog_path": "/opt/mysql/log/binlog/{0}".format(port),
                "mysql_instance_relaylog_path": "/opt/mysql/log/relaylog/{0}".format(port),
                "mysql_instance_redolog_path": "/opt/mysql/log/redolog/{0}".format(port),
                "mysql_instance_tmp_path": "/opt/mysql/tmp/{0}".format(port),
                "mysql_instance_backup_path": "/opt/mysql/backup/{0}".format(port),
                "mysql_instance_mycnf_path": "/opt/mysql/etc/{0}/my.cnf".format(port),
                "mysql_instance_run_user": "actiontech-mysql",
                "mysql_instance_mycnf_template_file": "my.cnf.5.7"
            }
            instances.append(info)
        body.update({"mysql_instances": instances})
        json.dump(body, f)
    with open("data.json", "r") as loadfile:
        tmp = json.loads(loadfile.read())

    resp = api_request_type_post(context, "v3/mysql/instance/batch_install_in_one_group", json.dumps(tmp), None, "raw")
    res = resp.json()
    progress_id = res['progress_id']
    commit_id = {
        "id": progress_id
    }
    api_post(context, "v3/progress/commit", commit_id)
    context.execute_steps(u"""
                Then wait for progress {0} is finished in {1}s
                """.format(progress_id, 600))
    context.group_id = group_id


@then(
    u'the batch MySQL group should have {master_count:int} running MySQL master and {slave_count:int} '
    u'running MySQL slave in {duration:time}')
def step_impl(context, master_count, slave_count, duration):
    assert_that(context.group_id, not_none(), "but group_id is : <{0}>".format(context.group_id))

    for i in range(1, duration * context.time_weight * 10):
        resp = get_mysql_info_in_group(context, context.group_id)
        condition = '.[] | select(."mysql_instance_status" == "STATUS_MYSQL_HEALTH_OK")'
        masters = pyjq.all(
            condition + ' | select(."mysql_instance_role" == "STATUS_MYSQL_MASTER")', resp)
        slaves = pyjq.all(
            condition + ' | select(."mysql_instance_role" == "STATUS_MYSQL_SLAVE")', resp)
        if len(masters) == 1 and len(slaves) == slave_count:
            return
        time.sleep(0.1)
    else:
        assert_that(False, "all mysql info status is ok but status is <{0}> ".format(pformat(resp)))


@given(u'I found a random instance without repl_ip')
def step_impl(context):
    resp = get_all_mysql_info(context)
    instances = pyjq.all('.[]|select(."mysql_instance_role"=="STATUS_MYSQL_SLAVE")|.mysql_instance_id', resp)
    empty_repl_ips = []
    temp = []
    for instance in instances:
        path = "universe/v3/mysqls/"
        key = path + instance
        resp_conf = get_config_metadata_info(context, path, key)
        if resp_conf["repl_ip"] == "":
            empty_repl_ips.append(instance)
    context.empty_repl_ip = random.choice(empty_repl_ips)
    temp.append(context.empty_repl_ip)
    context.match = temp


@when(u'I stop ha and replication for the instance in {num:int} concurrency')
def step_impl(context, num):
    url = context.version_3 + "/mysql/instance/batch_stop_ha_and_replication" \
                              "?mysql_instance_ids={0}&concurrency={1}".format(context.empty_repl_ip, num)
    resp = api_post(context, url)
    progress_id = resp['id']
    context.execute_steps(u"""
            Then wait for progress {0} is finished in {1}s
            """.format(progress_id, 120))


@when(u'I stop ha for the instance in {num:int} concurrency')
def step_impl(context, num):
    url = context.version_3 + "/mysql/instance/batch_stop_ha" \
                              "?mysql_instance_ids={0}&concurrency={1}".format(context.empty_repl_ip, num)
    resp = api_post(context, url)
    progress_id = resp['id']
    context.execute_steps(u"""
            Then wait for progress {0} is finished in {1}s
            """.format(progress_id, 120))


@then(u'the {key:string} of the instance should be {status:string}')
def step_impl(context, key, status):
    for instance in context.match:
        def condition(context, flag):
            resp = api_get(context, context.version_5 + "/mysql/instance/list", {
                "filter_mysql_instance_id": instance,
            })
            if key == "mysql_instance_replication_status":
                if status == "disable":
                    if resp["data"][0][key] == "STATUS_MYSQL_REPL_BAD":
                        return True
                else:
                    if resp["data"][0][key] == "STATUS_MYSQL_REPL_OK":
                        return True
            elif key == "uguard_status":
                if status == "disable":
                    if resp["data"][0][key] == "MANUAL_EXCLUDE_HA":
                        return True
                else:
                    if resp["data"][0][key] == "UGUARD_ENABLE":
                        return True

        waitfor(context, condition, 120)


@when(u'I start ha for the instance in {num:int} concurrency')
def step_impl(context, num):
    url = context.version_3 + "/mysql/instance/batch_start_ha" \
                              "?mysql_instance_ids={0}&concurrency={1}".format(context.empty_repl_ip, num)
    resp = api_post(context, url)
    progress_id = resp['id']
    context.execute_steps(u"""
                Then wait for progress {0} is finished in {1}s
                """.format(progress_id, 120))


@when(u'I rebuild replication for the instance in {num:int} concurrency')
def step_impl(context, num):
    url = context.version_3 + "/mysql/instance/batch_rebuild_replication" \
                              "?mysql_instance_ids={0}&concurrency={1}".format(context.empty_repl_ip, num)
    resp = api_post(context, url)
    progress_id = resp['id']
    context.execute_steps(u"""
                    Then wait for progress {0} is finished in {1}s
                    """.format(progress_id, 120))


@given(u'I found {num:int} groups in group_B {with_or_not:string} repl_ip')
def step_impl(context, num, with_or_not):
    resp_group = get_all_group_info(context)
    group_ids = pyjq.all('.[]|select(."mysql_group_instance_nums"=="3")|.mysql_group_id', resp_group)
    temp = []
    for group_id in group_ids:
        path = "universe/v3/mysql-groups/"
        key = path + group_id
        resp_conf_group = get_config_metadata_info(context, path, key)
        if resp_conf_group["udelay_enable"]:
            resp_instances = get_mysql_info_in_group(context, group_id)
            instances = pyjq.all('.[]|select(."mysql_instance_role"=="STATUS_MYSQL_SLAVE")|.mysql_instance_id',
                                 resp_instances)
            for instance in instances:
                path = "universe/v3/mysqls/"
                key = path + instance
                resp_conf = get_config_metadata_info(context, path, key)
                if with_or_not == "without" and resp_conf["repl_ip"] == "":
                    temp.append(group_id)
                    break
                elif with_or_not == "with" and resp_conf["repl_ip"] != "":
                    temp.append(group_id)
                    break
    match_ids = random.sample(temp, num)

    temp_instance = []
    for group in match_ids:
        resp_instances = get_mysql_info_in_group(context, group)
        instances = pyjq.all('.[]|select(."mysql_instance_role"=="STATUS_MYSQL_SLAVE")|.mysql_instance_id',
                             resp_instances)
        for instance in instances:
            temp_instance.append(instance)

    context.match = temp_instance
    empty_repl_ip = ""
    for instance_id in temp_instance:
        empty_repl_ip = empty_repl_ip + instance_id + ","
    context.empty_repl_ip = empty_repl_ip[:-1]


@when(u'I found one of the instances and {op:string} ha')
def step_impl(context, op):
    ins_id = random.choice(context.match)
    if op == "stop":
        url = context.version_3 + "/mysql/instance/batch_stop_ha" \
                                  "?mysql_instance_ids={0}&concurrency={1}".format(ins_id, 1)
    else:
        url = context.version_3 + "/mysql/instance/batch_start_ha" \
                                  "?mysql_instance_ids={0}&concurrency={1}".format(ins_id, 1)
    resp = api_post(context, url)
    progress_id = resp['id']
    context.execute_steps(u"""
                Then wait for progress {0} is finished in {1}s
                """.format(progress_id, 120))

    def condition(context, flag):
        resp_temp = api_get(context, context.version_5 + "/mysql/instance/list", {
            "filter_mysql_instance_id": ins_id,
        })
        if op == "stop":
            status = "MANUAL_EXCLUDE_HA"
        else:
            status = "UGUARD_ENABLE"

        if resp_temp["data"][0]["uguard_status"] == status:
            return True

    waitfor(context, condition, 120)


@given(u'I got the slave instances in the group')
def step_impl(context):
    mysql_group_id = context.mysql_group[0]["mysql_group_id"]
    resp_instances = get_mysql_info_in_group(context, mysql_group_id)
    instances = pyjq.all('.[]|select(."mysql_instance_role"=="STATUS_MYSQL_SLAVE")|.mysql_instance_id',
                         resp_instances)
    temp = []
    empty_repl_ip = ""
    for instance in instances:
        temp.append(instance)
        empty_repl_ip = empty_repl_ip + instance + ","
    context.match = temp
    context.empty_repl_ip = empty_repl_ip[:-1]


@when(u'I trigger the uguard exercise task by the way manual')
def step_impl(context):
    resp = api_post(context, context.version_3 + "/helper/component/uguard/trigger_exercise_task", {
        "is_sync": True,
    })
    progress_id = resp['progress_id']
    context.execute_steps(u"""
                    Then wait for progress {0} is finished in {1}s
                    """.format(progress_id, 120))


@then(u'the exercise result should be success')
def step_impl(context):
    def condition(context, flag):
        resp = api_get(context, context.version_3 + "/uguard/get_latest_exercise_task_result")
        if "uguard_exercise_task_latest_result" in resp and resp["uguard_exercise_task_latest_result"] == "Success":
            return True

    waitfor(context, condition, 90)


@when(u'I update the uguard exercise task config')
def step_impl(context):
    body = {
        "uguard_exercise_task_cron": "0 * * * * ?",
        "uguard_exercise_task_timeout": 60
    }
    context.body = copy.deepcopy(body)
    body["is_sync"] = True
    resp = api_post(context, context.version_3 + "/uguard/update_exercise_task_config", body)
    progress_id = resp['progress_id']
    context.execute_steps(u"""
                        Then wait for progress {0} is finished in {1}s
                        """.format(progress_id, 120))


@then(u'the exercise task should config correct')
def step_impl(context):
    resp = api_get(context, context.version_3 + "/uguard/get_exercise_task_config")
    assert resp == context.body


@then(u'the exercise task should be running')
def step_impl(context):
    def condition(context, flag):
        resp = api_get(context, context.version_3 + "/uguard/get_latest_exercise_task_result")
        if "uguard_exercise_task_is_running" in resp and resp["uguard_exercise_task_is_running"]:
            return True

    waitfor(context, condition, 60)


@then(u'the result of the exercise task should be timeout')
def step_impl(context):
    def condition(context, flag):
        resp = api_get(context, context.version_3 + "/uguard/get_latest_exercise_task_result")
        if resp["uguard_exercise_task_latest_result"] == "Timeout(60s)":
            return True

    waitfor(context, condition, 120)


@when(u'I query from the slave replication relation')
def step_imp(context):
    assert context.mysql_group != None
    mysql_group_ids = context.mysql_group[0]["mysql_group_id"]
    res = api_get(context, context.version_3 + "/mysql/group/list_with_instances", {
        "mysql_group_ids": mysql_group_ids,
    })
    assert_that(res["data"], not_none(), "the query result is ok but:<{0}> ".format(pformat(res)))


@when(u'I get mysql tips by address')
def step_imp(context):
    assert context.mysql_group != None
    info = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    addre = []
    for tmp in info:
        addre.append(tmp["server_address"] + ":" + tmp["mysql_instance_port"])
    res = api_get(context, context.version_5 + "/mysql/instance/list_tips", {
        "mysql_instance_address": "{0},{1}".format(addre[0], addre[-1]),
    })
    assert_that(len(res), equal_to(2), "the query result is ok but:<{0}> ".format(pformat(res)))
    for temp in res:
        assert_that(temp['ids'], not_none(), "the query result is ok but:<{0}> ".format(pformat(res)))


@when(u'I get hardware specifications')
def step_imp(context):
    assert context.mysql_group != None
    infos = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    mysql_info = pyjq.first('.[] | select(.mysql_instance_role == "STATUS_MYSQL_SLAVE")', infos)
    res = api_get(context, context.version_3 + "/server/get_hardware_specifications",
                  {"ssh_ip": mysql_info["server_address"],
                   "ssh_port": context.new_server_ssh_port,
                   "ssh_user": context.new_server_ssh_user,
                   "ssh_password": context.new_server_ssh_password,
                   "server_id": mysql_info["server_id"]
                   })
    assert_that(res, has_key("server_cpu_core_nums"), "the result is ok but:<{0}>".format(res))
    assert_that(res, has_key("server_memory_size"), "the result is ok but:<{0}>".format(res))
    assert_that(res, has_key("server_disk_size"), "the result is ok but:<{0}>".format(res))


@when(u'I update the instance read_only')
def step_imp(context):
    assert context.mysql_group != None
    infos = get_mysql_info_in_group(context, context.mysql_group[0]["mysql_group_id"])
    mysql_info = pyjq.first('.[] | select(.mysql_instance_role == "STATUS_MYSQL_SLAVE")', infos)
    context.mysql_instance = mysql_info
    context.execute_steps(u"""
    Then I should get the config information of the MySQL instance
    When I update MySQL instance configuration "read_only" to "OFF" with socket
    Then wait platform 30
    Then the MySQL instance configuration "read_only" should be "OFF" with socket in 1m
    When I execute the MySQL instance "use mysql;Create table testgtid(id int,name varchar(10));"
    """)


@then(u'I get inconsistent gtid sqls from slave')
def step_imp(context):
    assert context.mysql_instance != None

    def condition(context, flag):
        res = api_get(context, context.version_3 + "/mysql/instance/get_inconsistent_gtid_sqls_from_slave", {
            "mysql_instance_id": context.mysql_instance['mysql_instance_id'],
            "is_dry_run": False,
            "parse_gtid_timeout": 60,
        })
        if res["inconsistent_gtids_and_related_sqls"] != None:
            return True

    waitfor(context, condition, 60)


@then(u"wait platform {wait:int}")
def step_imp(context, wait):
    time.sleep(wait)


@then(u'the MySQL group {des:string} with {count:int} MySQL instances should back to normal')
def step_impl(context, des, count):
    def condition(context, flag):
        temp_list = found_mysql(context, des, count)
        if len(temp_list) != 0:
            return True

    waitfor(context, condition, 120)