from behave import *
from framework.api import *
import pyjq
import time
import json
import re
from util import *
from common import *

use_step_matcher("cfparse")


@when(u'I add {type:string} alert channel')
def step_imp(context, type):
    if type == "smtp":
        config = {
            "name":
                "smtp",
            "universe_configs": [{
                "send_resolved": True,
                "type": "smtp",
                "smtp_addr": "smtp.exmail.qq.com",
                "smtp_port": 465,
                "smtp_ssl": True,
                "smtp_user": "tester@actionsky.com",
                "smtp_password": "CGPKPhYAgnAJw2tZ",
                "smtp_from": "dmp_test@163.com ",
                "smtp_tos": "dmp_test@163.com ",
                "desc": "test_smtp"
            }]
        }
        alert_info = get_all_alert_info(context)
        alert_info['receivers'].append(config)
        body = {"is_sync": True, "alert_config": json.dumps(alert_info)}
        api_request_post(context, context.version_3 + "/alert/save_alert", body)

    elif type == "wechat":
        config = {
            "name":
                "wechat",
            "universe_configs": [{
                "send_resolved": True,
                "type": "wechat",
                "wechat_corpid": "wx0a593f2cdb0b487f",
                "wechat_corpsecret":
                    "G6kAsnnU_EAflXKHxE5_h6iPp0ydf3S69WzSP20eF03evkBj6tfHFDFiiVrBhwT2",
                "wechat_agentid": 1,
                "wechat_safe": 1,
                "wechat_proxy": "",
                "wechat_touser": "13812069570",
                "wechat_toparty": "",
                "wechat_totag": "",
                "desc": "test_wechat"
            }]
        }
        alert_info = get_all_alert_info(context)
        alert_info['receivers'].append(config)
        body = {"is_sync": True, "alert_config": json.dumps(alert_info)}
        api_request_post(context, context.version_3 + "/alert/save_alert", body)


@then(
    u'the alert channel list {should_or_not:should_or_not} contains the {type:string} alert channel'
)
def step_imp(context, should_or_not, type):
    alert_info = get_all_alert_info(context)
    match = pyjq.first('.|.receivers[]|.universe_configs[]|select(."type"=="{0}")'.format(type), alert_info)
    assert (match and should_or_not) or (not match and not should_or_not)


@then(u'the alert channel list {should_or_not:should_or_not} contains the alert channel')
def setp_impl(context, should_or_not):
    channel_list = get_all_alert_info(context)
    receivers = channel_list["receivers"]
    assert (len(receivers) == 3 and not should_or_not) or (len(receivers) > 3 and should_or_not)


@when(u'I found a valid the {type:string} alert channel, or I skip the test')
def step_imp(context, type):
    alert_info = get_all_alert_info(context)
    match = pyjq.first('.|.receivers[]|select(."name" == "{0}")'.format(type), alert_info)
    if match is None:
        context.scenario.skip("No valid {0} alert channel".format(type))
        return
    if type == "smtp":
        context.alert_channel = match
    else:
        context.alert_channel = match


@when(u'I update the {type:string} alert channel')
def step_imp(context, type):
    alert_info = get_all_alert_info(context)
    if type == "smtp":
        config = context.alert_channel
        alert_info['receivers'].remove(config)
        config['universe_configs'][0]['desc'] = "smtp_update"
        alert_info['receivers'].append(config)

        body = {"is_sync": True, "alert_config": json.dumps(alert_info)}
        api_request_post(context, context.version_3 + "/alert/save_alert", body)
    elif type == "wechat":
        config = context.alert_channel
        alert_info['receivers'].remove(config)
        config['universe_configs'][0]['desc'] = "wechat_update"
        alert_info['receivers'].append(config)

        body = {"is_sync": True, "alert_config": json.dumps(alert_info)}
        api_request_post(context, context.version_3 + "/alert/save_alert", body)


@then(u'the {type:string} alert channel should be updated')
def step_imp(context, type):
    alert_info = get_all_alert_info(context)
    if type == "smtp":
        match = pyjq.first(
            '.|.receivers[]|select(."name" == "smtp")|.universe_configs|any(."desc" == "smtp_update")', alert_info)
        assert match is not False
    elif type == "wechat":
        match = pyjq.first(
            '.|.receivers[]|select(."name" == "wechat")|.universe_configs|any(."desc" == "wechat_update")', alert_info)
        assert match is not False


@when(u'I remove the {type:string} alert channel')
def step_imp(context, type):
    assert context.alert_channel
    alert_info = get_all_alert_info(context)
    if type == "smtp":
        config = context.alert_channel
        alert_info['receivers'].remove(config)

        body = {"is_sync": True, "alert_config": json.dumps(alert_info)}
        api_request_post(context, context.version_3 + "/alert/save_alert", body)
    elif type == "wechat":
        config = context.alert_channel
        alert_info['receivers'].remove(config)

        body = {"is_sync": True, "alert_config": json.dumps(alert_info)}
        api_request_post(context, context.version_3 + "/alert/save_alert", body)


@when(u'I add the {type:string} alert configuration')
def step_imp(context, type):
    assert context.alert_channel != None
    if type == "smtp":
        smtp_config = {
            "route_id":
                "6",
            "is_expression_match":
                True,
            "match_exp":
                "",
            "receiver":
                "smtp",
            "group_by": [
                "code", "level", "src_comp_type", "alert_comp_id",
                "alert_comp_type", "server", "app_name", "src_comp_id"
            ],
            "group_wait":
                5000000000,
            "repeat_interval":
                3600000000000,
            "group_interval":
                3600000000000,
            "continue":
                True,
            "routes": []
        }
        alert_info = get_all_alert_info(context)
        alert_info['route']['routes'].append(smtp_config)
        body = {"is_sync": True, "alert_config": json.dumps(alert_info)}
        api_request_post(context, context.version_3 + "/alert/save_alert", body)
    elif type == "wechat":
        wechat_config = {
            "route_id":
                "9",
            "is_expression_match":
                True,
            "match_exp":
                "",
            "receiver":
                "wechat",
            "group_by": [
                "code", "level", "src_comp_id", "src_comp_type",
                "alert_comp_id", "alert_comp_type", "server", "app_name"
            ],
            "group_wait":
                5000000000,
            "repeat_interval":
                3600000000000,
            "group_interval":
                3600000000000,
            "continue":
                True,
            "routes": []
        }
        alert_info = get_all_alert_info(context)
        alert_info['route']['routes'].append(wechat_config)
        body = {"is_sync": True, "alert_config": json.dumps(alert_info)}
        api_request_post(context, context.version_3 + "/alert/save_alert", body)


@then(
    u'the {type:string} alert configuration list {should_or_not:should_or_not} contains the alert configuration'
)
def step_imp(context, should_or_not, type):
    alert_info = get_all_alert_info(context)
    match = pyjq.first(
        '.|."route"|."routes"|any(."receiver" == "{0}")'.format(type), alert_info)
    assert (match is not False and should_or_not) or (match is not True and not should_or_not)


@when(
    u'I found a valid the {type:string} alert configuration, or I skip the test'
)
def step_imp(context, type):
    alert_info = get_all_alert_info(context)
    match = pyjq.first(
        '.|."route"|.routes[]|select(."receiver" == "{0}")'.format(type), alert_info)
    if match is None:
        context.scenario.skip("No valid {0} alert configuration".format(type))
        return
    if type == "smtp":
        context.alert_configuration = match
    else:
        context.alert_configuration = match


@when(u'I update the {type:string} alert configuration')
def step_imp(context, type):
    assert context.alert_configuration
    alert_info = get_all_alert_info(context)
    if type == "smtp":
        config = context.alert_configuration
        alert_info['route']['routes'].remove(config)
        config['group_wait'] = 1000000000
        config["repeat_interval"] = 12000000000
        config["group_interval"] = 12000000000
        config["continue"] = False
        alert_info['route']['routes'].append(config)

        body = {"is_sync": True, "alert_config": json.dumps(alert_info)}
        api_request_post(context, context.version_3 + "/alert/save_alert", body)
    elif type == "wechat":
        config = context.alert_configuration
        alert_info['route']['routes'].remove(config)
        config['group_wait'] = 1000000000
        config["repeat_interval"] = 12000000000
        config["group_interval"] = 12000000000
        config["continue"] = False
        alert_info['route']['routes'].append(config)

        body = {"is_sync": True, "alert_config": json.dumps(alert_info)}
        api_request_post(context, context.version_3 + "/alert/save_alert", body)


@then(u'the {type:string} alert configuration should be updated')
def step_imp(context, type):
    alert_info = get_all_alert_info(context)
    if type == "smtp":
        match = pyjq.first(
            '.|."route"|.routes[]|select(."receiver" == "{0}")'.format(type), alert_info)
        assert match is not None

    elif type == "wechat":
        match = pyjq.first(
            '.|."route"|.routes[]|select(."receiver" == "{0}")'.format(type), alert_info)
        assert match is not None


@when(u'I remove the {type:string} alert configuration')
def step_imp(context, type):
    assert context.alert_configuration
    alert_info = get_all_alert_info(context)
    if type == "smtp":
        config = context.alert_configuration
        alert_info['route']['routes'].remove(config)
        body = {"is_sync": True, "alert_config": json.dumps(alert_info)}
        api_request_post(context, context.version_3 + "/alert/save_alert", body)
    elif type == "wechat":
        config = context.alert_configuration
        alert_info['route']['routes'].remove(config)
        body = {"is_sync": True, "alert_config": json.dumps(alert_info)}
        api_request_post(context, context.version_3 + "/alert/save_alert", body)


@when(u'I add the {type:string} alert configuration subkey')
def step_imp(context, type):
    assert context.alert_configuration
    if type == "smtp":
        smtp_config = {
            "routes": [{
                "route_id":
                    "10",
                "is_expression_match":
                    True,
                "match_exp":
                    "",
                "receiver":
                    "smtp",
                "group_by": [
                    "code", "level", "src_comp_id", "src_comp_type",
                    "alert_comp_id", "alert_comp_type", "server", "app_name"
                ],
                "group_wait":
                    5000000000,
                "repeat_interval":
                    3600000000000,
                "group_interval":
                    3600000000000,
                "continue":
                    True,
                "routes": []
            }]
        }
        alert_info = get_all_alert_info(context)
        alert_info['route']['routes'].append(smtp_config)
        body = {"is_sync": True, "alert_config": json.dumps(alert_info)}
        api_request_post(context, context.version_3 + "/alert/save_alert", body)
    elif type == "wechat":
        wechat_config = {
            "routes": [{
                "route_id":
                    "22",
                "is_expression_match":
                    True,
                "match_exp":
                    "",
                "receiver":
                    "wechat",
                "group_by": [
                    "code", "level", "src_comp_id", "src_comp_type",
                    "alert_comp_id", "alert_comp_type", "server", "app_name"
                ],
                "group_wait":
                    5000000000,
                "repeat_interval":
                    3600000000000,
                "group_interval":
                    3600000000000,
                "continue":
                    True,
                "routes": []
            }]
        }
        alert_info = get_all_alert_info(context)
        alert_info['route']['routes'].append(wechat_config)
        body = {"is_sync": True, "alert_config": json.dumps(alert_info)}
        api_request_post(context, context.version_3 + "/alert/save_alert", body)


@then(u'expect alert code {code:string}')
def step_imp(context, code):
    resp = get_alert_record_in_order(context, 'timestamp')
    alert_info = pyjq.first('.[]|select(."code" == {0})'.format(code), resp)
    if alert_info is not None:
        return True


@when(u'I add an alert channel for {type:string}')
def step_impl(context, type):
    path = 'conf/alert/add_' + type + '_alert_channel.json'
    load_dict = get_json_from_conf(path)
    body = {
        "alert_config": json.dumps(load_dict)
    }
    api_request_post(context, context.version_3 + "/alert/save_alert", body)


@when(u'I remove all the {config:string}')
def step_impl(context, config):
    path = 'conf/alert/remove_alert_channel.json'
    load_dict = get_json_from_conf(path)
    body = {
        "alert_config": json.dumps(load_dict)
    }
    api_request_post(context, context.version_3 + "/alert/save_alert", body)


@then(u'the inhibit rule list {should_or_not:should_or_not} contains the new inhibit rule')
def step_impl(context, should_or_not):
    channel_list = get_all_alert_info(context)
    receivers = channel_list["inhibit_rules"]
    assert (len(receivers) == 7 and not should_or_not) or (len(receivers) > 7 and should_or_not)


@when(u'I add a inhibit rule')
def step_impl(context):
    path = 'conf/alert/add_inhibit_rule.json'
    load_dict = get_json_from_conf(path)
    body = {
        "alert_config": json.dumps(load_dict)
    }
    api_request_post(context, context.version_3 + "/alert/save_alert", body)


@when(u'I found a new inhibit rule in the inhibit rule list')
def step_impl(context):
    channel_list = get_all_alert_info(context)
    receivers = channel_list["inhibit_rules"]
    assert len(receivers) == 8


@when(u'I count the unresolved alert number of the unresolved alert list')
def step_impl(context):
    unresolved_num = get_unresolved_num(context)
    context.unresolved_num = unresolved_num


@when(u'I creat an test unresolved alert in {duration:time}')
def step_impl(context, duration):
    desc = "test"
    for i in range(2):
        a = random.randrange(0, 10)
        desc = desc + str(a)
    b = str(random.randrange(1, 40))
    api_request_post(context, context.version_3 + "/alert_test/test", {
        "is_sync": True,
        "code": "UMC_TEST_ALERT",
        "level": "CRITICAL",
        "desc": desc,
        "source_component": "umc",
        "source_component_id": "uagent-udp" + b,
        "alert_component": "umc",
        "alert_component_id": "uagent-udp" + b,
        "server_id": "server-udp" + b,
    })

    def condition(context, flag):
        resp = get_all_alert_record(context)
        alert_record = pyjq.first('.[]|select(."detail"=="{0}")'.format(desc), resp)
        if alert_record:
            context.fingerprint = alert_record["fingerprint"]
            return True

    waitfor(context, condition, duration)


@when(u'I mark the unresolved alert to resolved in {duration:time}')
def step_impl(context, duration):
    api_request_post(context, context.version_3 + "/alert_record/mark_resolve_alert", {
        "is_sync": True,
        "fingerprints": context.fingerprint,
    })

    def condition(context, flag):
        resp = get_all_unresolved_alert_record(context)
        alert_record = pyjq.first('.[]|select(.fingerprint=="{0}")'.format(context.fingerprint), resp)
        if not alert_record:
            return True

    waitfor(context, condition, duration)


@when(u'I create a silence rule')
def step_impl(context):
    seed = "1234567890abcdefghijklmnopqrstuvwxyz"
    sa = []
    for i in range(6):
        sa.append(random.choice(seed))
    salt = ''.join(sa)
    rule_id = "silence-" + salt
    rule_name = "test" + salt
    exp_matcher = "code==\'mysql_repl_delay_more_than_1000\'"
    start = int(time.time())
    end = start + 31536000000
    api_request_post(context, context.version_3 + "/alert/add_silence", {
        "is_sync": True,
        "rule_id": rule_id,
        "rule_name": rule_name,
        "exp_matcher": exp_matcher,
        "start": start,
        "end": end,
        "created_by": "admin",
    })
    context.rule_name = rule_name
    context.rule_id = rule_id


@then(u'the silence rule {should_or_not:should_or_not} in the silence rule list')
def step_impl(context, should_or_not):
    rule = get_silence_list_by_rule_name(context, context.rule_name)
    assert (rule and should_or_not) or (not rule and not should_or_not)


@when(u'I remove the silence rule')
def step_impl(context):
    api_request_post(context, context.version_3 + "/alert/remove_silence", {
        "is_sync": True,
        "rule_id": context.rule_id,
    })


@then(u'the test unresolved alert {should_or_not:should_or_not} in the unresolved alert list')
def step_impl(context, should_or_not):
    resp = get_all_unresolved_alert_record(context)
    alert_record = pyjq.first('.[]|select(.fingerprint=="{0}")'.format(context.fingerprint), resp)
    assert (alert_record and should_or_not) or (not alert_record and not should_or_not)
