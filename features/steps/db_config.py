from behave import *
from framework.api import *
from framework.api_base import *
import pyjq
import time
import json
from getinfo import *
import requests

use_step_matcher("cfparse")


@when(
    u'I update MySQL {types:string} configuration "{option:string}" to "{option_value:string}" with {way:string}'
)
def step_impl(context, types, option, option_value, way):
    if types == "group":
        assert context.mysql_group
        mysql_group_id = context.mysql_group[0]["mysql_group_id"]
        root_password = get_mysql_group_root_password(context, mysql_group_id)
        body = {
            "mysql_option_update_infos": [
                {
                    "mysql_instance_super_user": "root",
                    "mysql_instance_super_password": root_password,
                    "mysql_instance_connect_type": way,
                    "mysql_instance_options": [
                        {
                            "mysql_instance_option_name": option,
                            "mysql_instance_option_value": option_value
                        }
                    ],
                    "mysql_group_id": mysql_group_id
                }
            ]
        }
    elif types == "instance":
        assert context.mysql_instance
        mysql_instance_id = context.mysql_instance["mysql_instance_id"]
        root_password = get_mysql_instance_root_password(context, mysql_instance_id)
        body = {
            "mysql_option_update_infos": [
                {
                    "mysql_instance_super_user": "root",
                    "mysql_instance_super_password": root_password,
                    "mysql_instance_connect_type": way,
                    "mysql_instance_options": [
                        {
                            "mysql_instance_option_name": option,
                            "mysql_instance_option_value": option_value
                        }
                    ],
                    "mysql_instance_id": mysql_instance_id
                }
            ]
        }
    body_str = json.dumps(body)
    api_request_type_post(context, context.version_3 + "/mysql/config/update", body_str, None, "raw")


@then(u'the MySQL {types:string} configuration "{option:string}" should be "{option_value:string}" with {way:string} '
      u'in {duration:time}')
def step_impl(context, types, option, option_value, way, duration):
    if types == "group":
        mysql_group_id = context.mysql_group[0]["mysql_group_id"]
        root_password = get_mysql_group_root_password(context, mysql_group_id)
        body = {
            "mysql_instance_super_user": "root",
            "mysql_instance_super_password": root_password,
            "mysql_instance_connect_type": way,
            "mysql_group_id": mysql_group_id,
            "fuzzy_keyword": option
        }
    elif types == "instance":
        mysql_instance_id = context.mysql_instance["mysql_instance_id"]
        root_password = get_mysql_instance_root_password(context, mysql_instance_id)
        body = {
            "mysql_instance_super_user": "root",
            "mysql_instance_super_password": root_password,
            "mysql_instance_connect_type": way,
            "mysql_instance_id": mysql_instance_id,
            "fuzzy_keyword": option
        }

    def condition(context, flag):
        resp = api_post(context, context.version_3 + "/mysql/config/list", body)
        config = pyjq.first('.data[]', resp)
        if config["mysql_instance_option_current_value"] == option_value:
            return True

    waitfor(context, condition, duration)


@when(u'I found the master MySQL instance in the group')
def step_impl(context):
    assert context.mysql_group
    mysql_group_id = context.mysql_group[0]["mysql_group_id"]
    instances = get_mysql_info_in_group(context, mysql_group_id)
    master_instance = pyjq.first('.[]|select(.mysql_instance_role=="STATUS_MYSQL_MASTER")', instances)
    context.mysql_instance = master_instance


@when(u'I found a MySQL instance in the group')
def step_impl(context):
    assert context.mysql_group
    mysql_group_id = context.mysql_group[0]["mysql_group_id"]
    instances = get_mysql_info_in_group(context, mysql_group_id)
    context.mysql_instance = instances[0]


@when(u'I export the MySQL group config')
def step_impl(context):
    assert context.mysql_group
    mysql_group_id = context.mysql_group[0]["mysql_group_id"]
    resp = api_get_text(context, context.version_3 + "/mysql/config/export", {
        "mysql_group_id": mysql_group_id
    })
    context.export = resp


@then(u'the export is not empty')
def step_impl(context):
    assert context.export


@then(u'I should get the config information of the MySQL {group_or_instance:string}')
def step_impl(context, group_or_instance):
    if group_or_instance == "group":
        mysql_group_id = context.mysql_group[0]["mysql_group_id"]
        resp = api_get(context, context.version_3 + "/mysql/config/get", {
            "mysql_group_id": mysql_group_id,
        })
        config_info = resp["mysql_instance_config"]

        instances = get_mysql_info_in_group(context, mysql_group_id)
        master_info = pyjq.first('.[] | select(.mysql_instance_role == "STATUS_MYSQL_MASTER")', instances)
        mysql_instance_mycnf = master_info["mysql_instance_mycnf"]
    elif group_or_instance == "instance":
        mysql_instance_mycnf = context.mysql_instance["mysql_instance_mycnf"]

        mysql_instance_id = context.mysql_instance["mysql_instance_id"]
        resp = api_get(context, context.version_3 + "/mysql/config/get", {
            "mysql_instance_id": mysql_instance_id,
        })
        config_info = resp["mysql_instance_config"]

    assert config_info == mysql_instance_mycnf
