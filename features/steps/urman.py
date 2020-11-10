from behave import *
from framework.api import *
import pyjq
import json
import os
import time
from datetime import datetime
from util import *

use_step_matcher("cfparse")
from getinfo import *


@when(u'I found a MySQL instance without backup rule, or I skip the test')
def step_impl(context):
    mysqls = get_all_mysql_info(context)
    mysql_ids = pyjq.all('.[] | .mysql_instance_id', mysqls)

    for mysql_id in mysql_ids:
        resp = get_backup_rule_list_by_instance_id(context, mysql_id)
        if len(resp) == 0:
            context.mysql_instance = pyjq.first(
                '.[] | select(.mysql_instance_id == "{0}")'.format(mysql_id), mysqls)
            return
    context.scenario.skip("Found no MySQL instance without backup rule")


@when(u'I found a MySQL instance without backup rule in the group, or I skip the test')
def step_impl(context):
    group_id = context.mysql_group[0]["mysql_group_id"]
    mysqls = get_mysql_info_in_group(context, group_id)
    mysql_ids = pyjq.all('.[] | .mysql_instance_id', mysqls)

    for mysql_id in mysql_ids:
        resp = get_backup_rule_list_by_instance_id(context, mysql_id)
        if len(resp) == 0:
            context.mysql_instance = pyjq.first(
                '.[] | select(.mysql_instance_id == "{0}")'.format(mysql_id), mysqls)
            api_request_post(
                context, context.version_3 + "/urman_rule/recycle_backup_dir", {
                    "instance_id": mysql_id,
                    "rule_type": "backup_tool_rule",
                    "is_sync": "true",
                })
            return
    context.scenario.skip("Found no MySQL instance without backup rule")


@when(
    u'I add a backup rule to the MySQL instance, which will be triggered in {delta_minutes:int}m'
)
def step_impl(context, delta_minutes):
    assert context.mysql_instance != None
    mysql = context.mysql_instance
    mysql_id = mysql["mysql_instance_id"]
    list_resp = get_backup_set_list_by_instance_id(context, mysql_id)
    context.origin_id = pyjq.first('.[] | .urman_backup_set_id', list_resp)

    ts = datetime.now()
    newMinute = (ts.minute + delta_minutes * context.time_weight) % 60
    cron = "0 {0} * * * ?".format(newMinute)
    backup_rule_id = "rule_" + mysql["mysql_instance_id"]

    resp = api_post(
        context, context.version_3 + "/urman_rule/add_backup_rule", {
            "backup_rule_id": backup_rule_id,
            "instance_id": mysql["mysql_instance_id"],
            "server_id": mysql["server_id"],
            "full_backup_cron": cron,
            "increment_backup_cron": "",
            "backup_remains": "2",
            "backup_priority": "99",
            "maintain_start_cron": "0 0 0 1/1 * ?",
            "maintain_duration_time": "1440m",
            "backup_tool": "XtraBackup",
            "backup_cnf": '''[global]
backup_lock_path = ./backup_lock
[mysql_backup]
xb_defaults = --use-memory=200MB --tmpdir={} --ftwrl-wait-timeout=120 --ftwrl-wait-threshold=120 --kill-long-queries-timeout=60 --kill-long-query-type=all --ftwrl-wait-query-type=all --no-version-check
xb_backup_to_image = --defaults-file={} --host={} --port={} --user={} --compress --throttle=300 --no-timestamp --stream=xbstream
xb_incremental_backup_to_image = --defaults-file={} --host={} --port={} --user={} --incremental --incremental-lsn={} --compress --throttle=300 --no-timestamp --stream=xbstream
xb_image_to_backup_dir = -x
xb_decompress = --decompress
xb_full_apply_log = --defaults-file={} --apply-log
xb_apply_incremental_backup = --defaults-file={} --apply-log --incremental-dir={}
xb_copy_back = --defaults-file={} --force-non-empty-directories --move-back

xb_backup_to_image_timeout_seconds = 21600
xb_incremental_backup_to_image_timeout_seconds = 21600
xb_image_to_backup_dir_timeout_seconds = 21600
xb_decompress_seconds = 21600
xb_full_apply_log_timeout_seconds = 21600
xb_apply_incremental_backup_timeout_seconds = 21600
xb_copy_back_timeout_seconds = 21600
''',
            "only_slave": "false",
            "only_master": "false"
        })

    api_request_post(
        context, context.version_3 + "/urman_rule/confirm_add_backup_rule", {
            "config-id": get_3pc_config_id(resp),
            "is-commit": "true",
            "backup_rule_id": backup_rule_id,
        })


@then(u'the MySQL instance should have a backup rule')
def step_impl(context):
    assert context.mysql_instance != None
    mysql = context.mysql_instance
    mysql_id = mysql["mysql_instance_id"]

    resp = get_backup_rule_list_by_instance_id(context, mysql_id)

    has_match = pyjq.first(
        '. | any(."mysql_instance_id" == "{0}")'.format(mysql_id), resp)
    assert has_match


@then(u'the MySQL instance should have a new backup set in {duration:time}')
def step_impl(context, duration):
    assert context.mysql_instance != None
    mysql = context.mysql_instance
    mysql_id = mysql["mysql_instance_id"]

    resp = get_backup_set_list_by_instance_id(context, mysql_id)
    origin_id = pyjq.first('.[] | .urman_backup_set_id'.format(mysql_id), resp)

    for i in range(1, duration * context.time_weight):
        resp = get_backup_set_list_by_instance_id(context, mysql_id)
        id = pyjq.first('.[] | .urman_backup_set_id'.format(mysql_id), resp)
        if id != origin_id:
            return
        time.sleep(1)
    assert False


@when(u'I found a backup rule, or I skip the test')
def step_impl(context):
    resp = get_backup_rule_list(context)
    rule = pyjq.first('.[0]', resp)

    if rule == None:
        context.scenario.skip("Found no backup rule")
    else:
        context.backup_rule = rule


@when(u'I found a MySQL instance with backup rule in the group, or I skip the test')
def step_impl(context):
    group_id = context.mysql_group[0]["mysql_group_id"]
    mysqls = get_mysql_info_in_group(context, group_id)
    mysql_ids = pyjq.all('.[] | .mysql_instance_id', mysqls)
    for mysql_id in mysql_ids:
        resp = get_backup_rule_list_by_instance_id(context, mysql_id)
        if len(resp) != 0:
            context.backup_rule = pyjq.first(
                '.[] | select(.mysql_instance_id == "{0}")'.format(mysql_id), resp)
            context.mysql_instance = pyjq.first(
                '.[] | select(.mysql_instance_id == "{0}")'.format(mysql_id), mysqls)
            return
    context.scenario.skip("Found no MySQL instance with backup rule")


@when(u'I found the MySQL instance of the backup rule')
def step_impl(context):
    assert context.backup_rule != None

    instance_id = context.backup_rule["mysql_instance_id"]
    mysqls = get_mysql_info_by_id(context, instance_id)
    context.mysql_instance = mysqls


@when(u'I remove the backup rule')
def step_impl(context):
    assert context.backup_rule != None
    backup_rule_id = context.backup_rule["urman_backup_rule_id"]
    resp = api_post(context, context.version_3 + "/urman_rule/remove_backup_rule", {
        "backup_rule_id": backup_rule_id,
    })

    api_request_post(
        context, context.version_3 + "/urman_rule/confirm_remove_backup_rule", {
            "config-id": get_3pc_config_id(resp),
            "is-commit": "true",
            "backup_rule_id": backup_rule_id,
        })


@then(u'the backup rule should not exist')
def step_impl(context):
    assert context.backup_rule != None
    backup_rule_id = context.backup_rule["urman_backup_rule_id"]

    resp = get_backup_rule_list(context)
    has_match = pyjq.first(
        '. | any(."urman_backup_rule_id" == "{0}")'.format(backup_rule_id), resp)

    assert not has_match


def get_3pc_config_id(resp):
    idx = resp['raw'].rindex('{"config-id"')
    obj = json.loads(resp['raw'][idx:])
    config_id = obj['config-id']
    assert config_id != None
    return config_id


@when(u'I recycle the backup dir of the MySQL instance')
def step_impl(context):
    assert context.mysql_instance != None
    mysql = context.mysql_instance
    mysql_id = mysql["mysql_instance_id"]

    api_request_post(
        context, context.version_3 + "/urman_rule/recycle_backup_dir", {
            "instance_id": mysql_id,
            "rule_type": "backup_tool_rule",
            "is_sync": "true",
        })


@then(u'the backup dir of the MySQL instance should not exist')
def step_impl(context):
    assert context.mysql_instance != None
    mysql = context.mysql_instance
    server_id = mysql["server_id"]
    backup_path = mysql["mysql_instance_backup_path"]
    dir1 = os.path.split(backup_path)
    dir2 = os.path.split(dir1[0])
    dir_mysql = dir2[0]
    dir_backup = dir1[0]
    resp_mysql = api_get(context, context.version_3 + "/helper/ll", {
        "server_id": server_id,
        "path": dir_mysql,
    })
    flag = True
    for mysql_file in resp_mysql:
        if mysql_file and mysql_file["filename"] == "backup":
            flag = False
            break
    if not flag:
        flag = True
        resp_backup = api_get(context, context.version_3 + "/helper/ll", {
            "server_id": server_id,
            "path": dir_backup,
        })
        for backup_file in resp_backup:
            if backup_file and backup_file["filename"] == dir1[1]:
                flag = False
                break
        if not flag:
            resp = api_get(context, context.version_3 + "/helper/ll", {
                "server_id": server_id,
                "path": backup_path,
            })
            if len(resp) == 0:
                flag = True
    assert flag


@when(
    u'I update the backup rule, make it will be triggered in {delta_minutes:int}m'
)
def step_impl(context, delta_minutes):
    assert context.backup_rule != None
    backup_rule_id = context.backup_rule["urman_backup_rule_id"]

    assert context.mysql_instance != None
    mysql = context.mysql_instance

    ts = datetime.now()
    newMinute = (ts.minute + delta_minutes * context.time_weight) % 60
    cron = "0 {0} * * * ?".format(newMinute)

    cnf = api_get(context, context.version_3 + "/support/read_umc_file", {
        "path": "backupcnfs/backup.xtrabackup",
    })

    resp = api_post(
        context, context.version_3 + "/urman_rule/update_backup_rule", {
            "backup_rule_id": backup_rule_id,
            "instance_id": mysql["mysql_instance_id"],
            "server_id": mysql["server_id"],
            "full_backup_cron": cron,
            "increment_backup_cron": "",
            "backup_remains": "2",
            "backup_priority": "99",
            "maintain_start_cron": "0 0 0 1/1 * ?",
            "maintain_duration_time": "1440m",
            "backup_tool": "XtraBackup",
            "backup_cnf": cnf,
            "only_slave": "false",
            "only_master": "false"
        })

    api_request_post(
        context, context.version_3 + "/urman_rule/confirm_update_backup_rule", {
            "config-id": get_3pc_config_id(resp),
            "is-commit": "true",
            "backup_rule_id": backup_rule_id,
        })


@then(u'the MySQL instance should have a new backup set in {duration:time} in version {version:int}')
def step_impl(context, duration, version):
    assert context.mysql_instance != None
    mysql = context.mysql_instance
    mysql_id = mysql["mysql_instance_id"]
    # .format(mysql_id)
    for i in range(1, duration * context.time_weight):
        resp = get_backup_set_list_by_instance_id(context, mysql_id)
        id = pyjq.first('.[] | .urman_backup_set_id', resp)
        if id != context.origin_id:
            return
        time.sleep(1)
    assert False


@when(u'I found a backup set, or I skip the test')
def step_impl(context):
    resp = get_backup_set_list(context)
    if len(resp) != 0:
        backup_set = pyjq.first('.[]', resp)
        context.set_id = backup_set["urman_backup_set_id"]
        return
    context.scenario.skip("Found no backup set")


@when(u'I found a MySQL instance with backup set in the group, or I skip the test')
def step_impl(context):
    group_id = context.mysql_group[0]["mysql_group_id"]
    mysqls = get_mysql_info_in_group(context, group_id)
    mysql_ids = pyjq.all('.[] | .mysql_instance_id', mysqls)
    for mysql_id in mysql_ids:
        resp = get_backup_set_list_by_instance_id(context, mysql_id)
        if len(resp) != 0:
            context.backup_set = pyjq.first(
                '.[] | select(.mysql_instance_id == "{0}")'.format(mysql_id), resp)
            context.mysql_instance = pyjq.first(
                '.[] | select(.mysql_instance_id == "{0}")'.format(mysql_id), mysqls)
            return
    context.scenario.skip("Found no MySQL instance with backup rule")


@when(u'I check the detail of the backup set')
def step_impl(context):
    backup_set_id = context.set_id
    resp = api_get(context, context.version_3 + "/urman_backupset/view_details", {
        "backup_set_id": backup_set_id,
    })
    context.backup_set_info = pyjq.first('.[]', resp)


@then(u'the detail of the backup set should be viewed')
def step_impl(context):
    assert context.backup_set_info is not None


@when(u'I check the detail of the backup task')
def step_impl(context):
    backup_set_id = context.backup_set["urman_backup_set_id"]
    resp = api_get(context, context.version_3 + "/urman_task/list", {
        "backup_set_id": backup_set_id,
    })
    context.backup_set_info = pyjq.first('.[]', resp)


@then(u'the detail of the backup task should be viewed')
def step_impl(context):
    assert context.backup_set_info is not None


@when(u'I make a manual backup with {tool:string} in instance')
def step_impl(context, tool):
    resp = get_all_mysql_info(context)
    mysql = pyjq.first(
        '.[] | select(.mysql_instance_status == "STATUS_MYSQL_HEALTH_OK" and ."mysql_instance_role" == "STATUS_MYSQL_SLAVE")',
        resp)
    context.mysql_instance = mysql

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
    resp = get_backup_set_list_by_instance_id(context, context.mysql_instance["mysql_instance_id"])
    origin_id = pyjq.first('.[] | .urman_backup_set_id', resp)
    context.origin_id = origin_id


@then(
    u'the MySQL instance manual backup list should contains the urman backup set in {duration:time}'
)
def step_impl(context, duration):
    assert context.mysql_instance != None
    mysql_id = context.mysql_instance["mysql_instance_id"]

    def condition(context, flag):
        resp = get_backup_set_list_by_instance_id(context, mysql_id)
        id = pyjq.first('.[] | .urman_backup_set_id', resp)
        if id == context.origin_id:
            return True

    waitfor(context, condition, duration)


@when(u'I delete the backup set')
def step_impl(context):
    backup_set_ids = context.origin_id
    resp = api_post(context, context.version_3 + "/urman_backupset/recycle_backupsets", {
        "is_sync": True,
        "backup_set_ids": backup_set_ids,
    })
    context.progress_id = resp['progress_id']


@then(u'the backup set should not in the backup set list')
def step_impl(context):
    backup_set_ids = context.origin_id
    resp = get_backup_set_list(context)
    backup_set = pyjq.all('.[]|select(."urman_backup_set_id"=="{0}")'.format(backup_set_ids), resp)
    assert len(backup_set) == 0


@then(u'got the response successful in {times:int}s')
def step_impl(context, times):
    progress_id = context.progress_id
    context.execute_steps(u"""
                        Then wait for progress {0} is finished in {1}s
                        """.format(progress_id, times))


@when(u'I check the server have no backup rule, or I skip the case')
def step_impl(context):
    assert context.server != None
    urman_list = get_backup_rule_list(context)
    server_id = context.server['server_id']
    if server_id in json.dumps(urman_list):
        context.scenario.skip("{0} have backup rule")
        return
