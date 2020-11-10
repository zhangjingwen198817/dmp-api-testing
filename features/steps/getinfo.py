from behave import *
from framework.api import *
import pyjq
import time
import json
import re
from util import *
from common import *
import time
import logging
from pprint import pformat

LOGGER = logging.getLogger("steps.getinfo")
use_step_matcher("cfparse")


def get_all_server_info(context):
    resp = api_get(context, context.version_5 + "/server/list", {
        "page_size": context.page_size_to_select_all,
    })
    str_resp = json.dumps(resp['data'])
    json_resp = str_resp.replace('uguard_agent_status', 'uguard-agent_status').replace('uguard_mgr_status',
                                                                                       'uguard-mgr_status').replace(
        'urman_agent_status', 'urman-agent_status').replace('urman_mgr_status', 'urman-mgr_status')
    return json.loads(json_resp)


def get_server_info_by_id(context, server_id):
    info = get_all_server_info(context)
    for server_info in info:
        if server_info['server_id'] == server_id:
            return server_info
    else:
        return None


def get_all_group_info(context):
    res = api_get(context, context.version_5 + "/mysql/group/list", {
        "page_size": context.page_size_to_select_all,
    })
    return res['data']


def get_group_info_by_id(context, mysql_group_id):
    info = get_all_group_info(context)
    for group_info in info:
        if group_info['mysql_group_id'] == mysql_group_id:
            return group_info
    else:
        return None


def get_all_mysql_info(context):
    resp = api_get(context, context.version_5 + "/mysql/instance/list", {
        "page_size": context.page_size_to_select_all,
    })
    return resp['data']


def get_mysql_info_by_id(context, mysql_instance_id):
    info = get_all_mysql_info(context)
    for mysql_info in info:
        if mysql_info['mysql_instance_id'] == mysql_instance_id:
            return mysql_info
    else:
        return None


def get_mysql_info_in_group(context, mysql_group_id):
    info = get_all_mysql_info(context)
    group_mysqls = []
    for mysql_info in info:
        if mysql_info['mysql_group_id'] == mysql_group_id:
            group_mysqls.append(mysql_info)
    return group_mysqls


def get_progress(context, progress_id):
    resp = api_get(context, context.version_3 + "/progress", {
        "id": progress_id,
    })
    return resp


# def get_group_list(context):
#     resp = api_get(context, context.version_5 + "/mysql/group/list", {
#         "number": context.page_size_to_select_all,
#     })
#     return resp
#
#
# def get_group_list_by_id(context, group_id):
#     info = get_group_list(context)
#     match = pyjq.first('.data[] |  select(."mysql_group_id"=="{0}")'.format(group_id), info)
#     return match

def get_role_list(context):
    resp = api_get(context, context.version_3 + "/role/list_role")
    return resp['data']


def get_tag_pool_list(context):
    resp = api_get(context, context.version_3 + "/tag_pool/list")
    return resp


def get_all_tag_info(context):
    resp = api_get(context, context.version_4 + "/tag/list", {
        "page_size": context.page_size_to_select_all,
    })
    return resp["data"]


def get_user_list(context):
    resp = api_get(context, context.version_3 + "/user/list_user")
    return resp['data']


def get_login_user(context):
    resp = api_get(context, context.version_3 + "/user/get_login_user")
    return resp


def get_ushard_group_list(context):
    resp = api_get(context, context.version_4 + "/ushard/group/list", {
        "page_size": context.page_size_to_select_all,
    })
    return resp["data"]


def get_sippool_list(context):
    resp = api_get(context, context.version_4 + "/sippool/list", {
        "page_size": context.page_size_to_select_all,
    })
    return resp["data"]


def get_support_component(context, pattern):
    resp = api_get(context, context.version_3 + "/support/component", {
        "pattern": pattern
    })
    return resp


def get_instance_list_by_port(context, port):
    infos = get_all_mysql_info(context)
    mysql_infos = []
    for mysql_info in infos:
        if mysql_info['mysql_instance_port'] == port:
            mysql_infos.append(mysql_info)
    return mysql_infos


def get_user_action_list(context):
    resp = api_get(context, context.version_3 + "/user/list_action", {
        "view": "all",
        "scope_user": False
    })
    return resp


def get_config_metadata_info(context, path, key):
    resp = api_get(context, context.version_3 + "/config_metadata/list_next", {
        "query": path,
    })
    match = json.loads(eval(resp)[key])
    return match


def get_sippool_all_ips(context):
    resp = api_get(context, context.version_4 + "/sippool/list", {
        "page_size": context.page_size_to_select_all,
    })
    return pyjq.all('.data[] | .sip', resp)


def get_all_alert_info(context):
    resp = api_get(context, context.version_3 + "/alert/list_alert", {
        "number": context.page_size_to_select_all,
    })
    res = resp.replace("\/", "")
    alert_info = json.loads(res)
    return alert_info


def get_json_from_conf(path):
    with open(path, 'r') as load_f:
        load_dict = json.load(load_f)
        return load_dict


def get_unresolved_num(context):
    resp = api_get(context, context.version_3 + "/alert_record/list_unresolved_num", {})
    return resp["count"]


def get_all_alert_record(context):
    resp = api_get(context, context.version_3 + "/alert_record/list_search", {
        "number": 99
    })
    return resp["data"]


def get_all_unresolved_alert_record(context):
    resp = api_get(context, context.version_3 + "/alert_record/list_search", {
        "resolve_state": "unresolved",
        "number": context.page_size_to_select_all,
    })
    return resp["data"]


def get_alert_record_in_order(context, param):
    resp = api_get(context, context.version_3 + "/alert_record/list_search", {
        'order_by': param,
        'number ': context.page_size_to_select_all,
        'ascending': 'false',
    })
    return resp["data"]


def get_silence_list_by_rule_name(context, rule_name):
    resp = api_get(context, context.version_3 + "/alert/list_silence", {
        "rule_name": rule_name
    })
    rule = pyjq.first('.[]', resp)
    return rule


def get_backup_rule_list(context):
    resp = api_get(context, context.version_4 + "/urman/backup_rule/list", {
        "page_size": context.page_size_to_select_all,
    })
    return resp["data"]


def get_backup_rule_list_by_instance_id(context, instance_id):
    infos = get_backup_rule_list(context)
    rules = []
    for rule in infos:
        if rule["mysql_instance_id"] == instance_id:
            rules.append(rule)
    return rules


def get_backup_set_list(context):
    resp = api_get(context, context.version_4 + "/urman/backup_set/list", {
        "page_size": context.page_size_to_select_all,
    })
    return resp["data"]


def get_backup_set_list_by_instance_id(context, instance_id):
    infos = get_backup_set_list(context)
    backsets = []
    for backset in infos:
        if backset["mysql_instance_id"] == instance_id:
            backsets.append(backset)
    return backsets


def get_uproxy_group_list(context):
    resp = api_get(context, context.version_6 + "/uproxy/group/list", {
        "page_size": context.page_size_to_select_all,
    })
    return resp["data"]


def get_uproxy_group_list_by_group_id(context, group_id):
    infos = get_uproxy_group_list(context)
    groups = []
    for group in infos:
        if group["uproxy_group_id"] == group_id:
            groups.append(group)
    return groups


def get_uproxy_instance_list(context):
    res = api_get(context, context.version_6 + "/uproxy/instance/list", {
        "page_size": context.page_size_to_select_all,
    })
    return res["data"]


def get_uproxy_instance_list_by_group_id(context, group_id):
    infos = get_uproxy_instance_list(context)
    uproxy_instances = []
    for info in infos:
        if info["uproxy_group_id"] == group_id:
            uproxy_instances.append(info)
    return uproxy_instances


def get_uproxy_router_list(context):
    resp = api_get(context, context.version_5 + "/uproxy/router/list", {
        "number": context.page_size_to_select_all,
    })
    return resp["data"]


def get_uproxy_router_list_by_group_id(context, group_id):
    infos = get_uproxy_router_list(context)
    routers = []
    for router in infos:
        if router["group_id"] == group_id:
            routers.append(router)
    return routers


def get_uproxy_router_backend_list(context, group_id, user):
    resp = api_get(context, context.version_5 + "/uproxy/router/backend/list", {
        "filter_uproxy_group_id": group_id,
        "filter_uproxy_router_user": user,
        "page_size": context.page_size_to_select_all
    })
    return resp["data"]


def get_all_mongo_group(context):
    resp = api_get(context, context.version_5 + "/mongodb/group/list", {
        "number": context.page_size_to_select_all,
    })
    return resp


def get_all_mongo_instance(context):
    resp = api_get(context, context.version_5 + "/mongodb/instance/list", {
        "number": context.page_size_to_select_all,
    })
    return resp


def get_mongo_instance_group(context, mongodb_group_id):
    res = get_all_mongo_instance(context)
    group_instance_info = []
    for info in res:
        if info['mongodb_group_id'] == mongodb_group_id:
            group_instance_info.append(info)
    return group_instance_info


def get_mysql_instance_root_password(context, mysql_instance_id):
    root_password = api_get(context, context.version_3 + "/helper/get_mysql_password", {
        "mysql_id": mysql_instance_id,
        "password_type": "ROOT",
    })
    return root_password


def get_mysql_group_root_password(context, mysql_group_id):
    resp = get_mysql_info_in_group(context, mysql_group_id)
    master_info = pyjq.first('.[] | select(.mysql_instance_role == "STATUS_MYSQL_MASTER")', resp)
    assert master_info is not None
    root_password = api_get(context, context.version_3 + "/helper/get_mysql_password", {
        "mysql_id": master_info["mysql_instance_id"],
        "password_type": "ROOT",
    })
    return root_password


def query_from_mysql_instance(context, mysql_instance_id, root_password, query):
    resp = api_get(
        context, context.version_3 + "/helper/query_mysql", {
            "mysql_id": mysql_instance_id,
            "query": query,
            "user": "root",
            "password": root_password,
        })
    return resp
