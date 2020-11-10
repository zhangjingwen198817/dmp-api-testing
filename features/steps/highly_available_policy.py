import pyjq
from common import *
from behave import *
import logging
from pprint import pformat
LOGGER = logging.getLogger("steps.highly_available_policy")
use_step_matcher("cfparse")


@when(u'I add a {type:string} template')
def step_impl(context, type):
    add_sla_protocol(context, type)


@when(u'I add a {type:string} template, in version {version:int}')
def step_impl(context, type, version):
    add_sla_protocol(context, type, version)


def add_sla_protocol(context, type, version=3):
    sla_template = "api_{0}_".format(type) + generate_id()
    body = {}
    if type == "rto":
        body = {
            "name": sla_template,
            "sla_type": type,
            "sla_rto": 600,
            "sla_rto_levels": "10,60,600",
            "sla_rto_te": "600",
            "is_sync": True
        }
    elif type == "rpo":
        body = {
            "name": sla_template,
            "sla_type": type,
            "sla_rpo": 0,
            "sla_rpo_levels": "10,50,200",
            "sla_rpo_error_levels": "20,60,600",
            "is_sync": True,
        }
    elif type == "ha_policy":
        body = {
            "name": sla_template,
            "sla_type": type,
            "ha_policy_failover_election": "HA_POLICY_FAILOVER_ELECTION_SAME_ZONE",
            "ha_policy_semisync_count": "HA_POLICY_SEMISYNC_COUNT_EQUAL",
            "is_sync": True
        }
    elif type == "ha_policy_1":
        body = {
            "name": sla_template,
            "sla_type": 'ha_policy',
            "ha_policy_failover_election": "HA_POLICY_FAILOVER_ELECTION_SAME_ZONE",
            "ha_policy_semisync_count": "HA_POLICY_SEMISYNC_COUNT_MINUS_ONE_MINIMUM_ONE",
            "is_sync": True
        }
    if version == 4:
        api_request_post(context, eval('context.version_' + str(version)) + "/mysql/group/ha_policy/add", body)
    elif version == 3:
        api_request_post(context, eval('context.version_' + str(version)) + "/sla/add", body)
    context.sla_template = {"name": sla_template}


@then(
    u'the Highly Available policy list {should_or_not:should_or_not} contains the {type:string} template'
)
def step_impl(context, should_or_not, type):
    assert context.sla_template != None
    sla_type = type
    sla_template = context.sla_template["name"]
    if type == "ha_policy_1":
        sla_type = 'ha_policy'
    resp = api_get(context, context.version_4 + "/mysql/group/ha_policy/list")
    match = None
    if type == 'rpo' or type == 'rto':
        match = pyjq.first('.[] | select(."name"=="{0}") | select(."sla_type"=="{1}")'.format(sla_template, sla_type),
                           resp)
    elif type == 'ha_policy_1':
        match = pyjq.first(
            '.[] | select(."name"=="{0}") | select(."sla_type"=="{1}") | select(."ha_policy_semisync_count"=="HA_POLICY_SEMISYNC_COUNT_MINUS_ONE_MINIMUM_ONE")'.format(
                sla_template, sla_type), resp)
    elif type == 'ha_policy':
        match = pyjq.first(
            '.[] | select(."name"=="{0}") | select(."sla_type"=="{1}") | select(."ha_policy_semisync_count"=="HA_POLICY_SEMISYNC_COUNT_EQUAL")'.format(
                sla_template, sla_type), resp)
    assert (match != None and should_or_not) or (match == None and not should_or_not)


@when(u'I found a valid {type:string} template, or I skip the test')
def step_impl(context, type):
    sla_type = None
    condition = None
    if type == "ha_policy_1":
        sla_type = "ha_policy"
    if type == 'rpo' or type == 'rto':
        condition = '.[] | select(."valid"=="1") | select(."sla_type"=="{0}")'.format(type)
    elif type == 'ha_policy_1':
        condition = '.[] | select(."valid"=="1") | select(."sla_type"=="{0}") | select(."ha_policy_semisync_count"=="HA_POLICY_SEMISYNC_COUNT_MINUS_ONE_MINIMUM_ONE")'.format(
            sla_type)
    elif type == 'ha_policy':
        condition = '.[] | select(."valid"=="1") | select(."sla_type"=="{0}") | select(."ha_policy_semisync_count"=="HA_POLICY_SEMISYNC_COUNT_EQUAL")'.format(
            type)
    resp = api_get(context, context.version_4 + "/mysql/group/ha_policy/list")
    match = pyjq.first(condition, resp)
    if match is None:
        context.scenario.skip("No valid {0} template found".format(type))
        return
    if type == 'rto':
        context.sla_rto_levels = match['sla_rto_levels']
        context.sla_rto = match['sla_rto']
    elif type == 'rpo':
        context.sla_rpo = match['sla_rpo']
        context.sla_rpo_levels = match['sla_rpo_levels']
        context.sla_rpo_error_levels = match['sla_rpo_error_levels']
    elif type == 'ha_policy_1':
        context.ha_policy_semisync_count = match['ha_policy_semisync_count']
        context.ha_policy_failover_election = match['ha_policy_failover_election']
    elif type == 'ha_policy':
        context.ha_policy_semisync_count = match['ha_policy_semisync_count']
        context.ha_policy_failover_election = match['ha_policy_failover_election']
    context.sla_template = match["name"]


@when(
    u'I update the {type:string} template configuration, {template_values:option_values}'
)
def step_impl(context, type, template_values):
    assert context.sla_template != None
    template_params = {}
    if type == 'rto':
        template_params = {
            "name": context.sla_template,
            "sla_rto": template_values['sla_rto'],
            "sla_rto_levels": template_values['sla_rto_levels'],
            "sla_rto_te": "500",
            "sla_type": type,
            "is_sync": True,
        }
        context.sla_rto_levels = template_values['sla_rto_levels']
        context.sla_rto = template_values['sla_rto']
    elif type == 'rpo':
        template_params = {
            "name": context.sla_template,
            "sla_rpo": template_values['sla_rpo'],
            "sla_rpo_levels": template_values['sla_rpo_levels'],
            "sla_rpo_error_levels": template_values['sla_rpo_error_levels'],
            "sla_type": type,
            "is_sync": True,
        }
        context.sla_rpo = template_values['sla_rpo']
        context.sla_rpo_levels = template_values['sla_rpo_levels']
        context.sla_rpo_error_levels = template_values['sla_rpo_error_levels']
    api_request_post(context, context.version_4 + "/mysql/group/ha_policy/update", template_params)


@when(
    u'I update the {type:string} template, with the configuration {template_values:string}'
)
def step_impl(context, type, template_values):
    dic = readYaml("conf/keyword.yml")
    assert context.sla_template != None
    assert dic['sla_policy'][template_values] != None
    template_params = {}
    if type == 'rto':
        template_params = {
            "name": context.sla_template,
            "sla_rto": dic['sla_policy'][template_values]['sla_rto'],
            "sla_rto_levels": dic['sla_policy'][template_values]['sla_rto_levels'],
            "sla_rto_te": "500",
            "sla_type": type,
            "is_sync": True,
        }
        context.sla_rto_levels = dic['sla_policy'][template_values]['sla_rto_levels']
        context.sla_rto = dic['sla_policy'][template_values]['sla_rto']
    elif type == 'rpo':
        template_params = {
            "name": context.sla_template,
            "sla_rpo": dic['sla_policy'][template_values]['sla_rpo'],
            "sla_rpo_levels": dic['sla_policy'][template_values]['sla_rpo_levels'],
            "sla_rpo_error_levels": dic['sla_policy'][template_values]['sla_rpo_error_levels'],
            "sla_type": type,
            "is_sync": True,
        }
        context.sla_rpo = dic['sla_policy'][template_values]['sla_rpo']
        context.sla_rpo_levels = dic['sla_policy'][template_values]['sla_rpo_levels']
        context.sla_rpo_error_levels = dic['sla_policy'][template_values]['sla_rpo_error_levels']
    elif type == "ha_policy":
        template_params = {
            "name": context.sla_template,
            "sla_type": type,
            "ha_policy_failover_election": dic['sla_policy'][template_values]['ha_policy_failover_election'],
            "ha_policy_semisync_count": dic['sla_policy'][template_values]['ha_policy_semisync_count'],
            "is_sync": True
        }
    elif type == "ha_policy_1":
        template_params = {
            "name": context.sla_template,
            "sla_type": 'ha_policy',
            "ha_policy_failover_election": dic['sla_policy'][template_values]['ha_policy_failover_election'],
            "ha_policy_semisync_count": dic['sla_policy'][template_values]['ha_policy_semisync_count'],
            "is_sync": True
        }

    api_request_post(context, context.version_4 + "/mysql/group/ha_policy/update", template_params)


@then(u'the {type:string} template {should_or_not:should_or_not} exist')
def step_imp(context, type, should_or_not):
    assert context.sla_template != None
    match = None
    if type == 'rto':
        assert context.sla_rto_levels != None
        assert context.sla_rto != None

        resp = api_get(context, context.version_4 + "/mysql/group/ha_policy/list")
        condition = '.[] | select(."name"=="{0}") | select(."sla_rto_levels"=="{1}") | select(."sla_rto"=="{2}") | select(."sla_type"=="{3}")'.format(
            context.sla_template, context.sla_rto_levels, context.sla_rto, type)
        match = pyjq.first(condition, resp)
    elif type == 'rpo':
        assert context.sla_rpo != None
        assert context.sla_rpo_levels != None
        assert context.sla_rpo_error_levels != None

        resp = api_get(context, context.version_4 + "/mysql/group/ha_policy/list")
        condition = '.[] | select(."name"=="{0}") | select(."sla_rpo_levels"=="{1}") | select(."sla_rpo_error_levels"=="{2}") | select(."sla_rpo"=="{3}") | select(."sla_type"=="{4}")'.format(
            context.sla_template, context.sla_rpo_levels, context.sla_rpo_error_levels, context.sla_rpo, type)
        match = pyjq.first(condition, resp)
    elif type == 'ha_policy':
        assert context.ha_policy_semisync_count != None
        assert context.ha_policy_failover_election != None

        resp = api_get(context, context.version_4 + "/mysql/group/ha_policy/list")
        condition = '.[] | select(."name"=="{0}") | select(."ha_policy_semisync_count"=="{1}") | select(."ha_policy_failover_election"=="{2}") | select(."sla_type"=="{3}")'.format(
            context.sla_template, context.ha_policy_semisync_count, context.ha_policy_failover_election, type)
        match = pyjq.first(condition, resp)
    elif type == 'ha_policy_1':
        assert context.ha_policy_semisync_count != None
        assert context.ha_policy_failover_election != None
        resp = api_get(context, context.version_4 + "/mysql/group/ha_policy/list")
        condition = '.[] | select(."name"=="{0}") | select(."ha_policy_semisync_count"=="{1}") | select(."ha_policy_failover_election"=="{2}") | select(."sla_type"=="{3}")'.format(
            context.sla_template, context.ha_policy_semisync_count, context.ha_policy_failover_election, 'ha_policy')
        match = pyjq.first(condition, resp)

    assert (match != None and should_or_not) or (match == None and not should_or_not)


@when(u'I remove the {type:string} template')
def step_imp(context, type):
    assert context.sla_template != None
    template_params = {
        "name": context.sla_template,
        "sla_type": type,
        "is_sync": True,
    }
    api_request_post(context, context.version_3 + "/sla/remove", template_params)


@then(u'the {type:string} template {should_or_not:should_or_not} be {template_values:option_values}')
def step_imp(context, type, should_or_not, template_values):
    assert context.sla_template != None
    match = None
    if type == 'rto':
        assert context.sla_rto_levels != None
        assert context.sla_rto != None

        resp = api_get(context, context.version_4 + "/mysql/group/ha_policy/list")
        condition = '.[] | select(."name"=="{0}") | select(."sla_rto_levels"=="{1}") | select(."sla_rto"=="{2}") | select(."sla_type"=="{3}")'.format(
            context.sla_template, template_values['sla_rto_levels'], template_values['sla_rto'], type)
        match = pyjq.first(condition, resp)
    elif type == 'rpo':
        assert context.sla_rpo != None
        assert context.sla_rpo_levels != None
        assert context.sla_rpo_error_levels != None

        resp = api_get(context, context.version_4 + "/mysql/group/ha_policy/list")
        condition = '.[] | select(."name"=="{0}") | select(."sla_rpo_levels"=="{1}") | select(."sla_rpo_error_levels"=="{2}") | select(."sla_rpo"=="{3}") | select(."sla_type"=="{4}")'.format(
            context.sla_template, template_values['sla_rpo_levels'], template_values['sla_rpo_error_levels'],
            template_values['sla_rpo'], type)
        match = pyjq.first(condition, resp)

    assert (match != None and should_or_not) or (match == None and not should_or_not)


@then(u'the {type:string} template {should_or_not:should_or_not} be configuration {template_values:string}')
def step_imp(context, type, should_or_not, template_values):
    assert context.sla_template != None
    dic = readYaml("conf/keyword.yml")
    assert dic['sla_policy'][template_values] != None
    match = None
    if type == 'rto':
        assert context.sla_rto_levels != None
        assert context.sla_rto != None

        resp = api_get(context, context.version_4 + "/mysql/group/ha_policy/list")
        condition = '.[] | select(."name"=="{0}") | select(."sla_rto_levels"=="{1}") | select(."sla_rto"=="{2}") | select(."sla_type"=="{3}")'.format(
            context.sla_template, dic['sla_policy'][template_values]['sla_rto_levels'],
            dic['sla_policy'][template_values]['sla_rto'], type)
        match = pyjq.first(condition, resp)
    elif type == 'rpo':
        assert context.sla_rpo != None
        assert context.sla_rpo_levels != None
        assert context.sla_rpo_error_levels != None

        resp = api_get(context, context.version_4 + "/mysql/group/ha_policy/list")
        condition = '.[] | select(."name"=="{0}") | select(."sla_rpo_levels"=="{1}") | select(."sla_rpo_error_levels"=="{2}") | select(."sla_rpo"=="{3}") | select(."sla_type"=="{4}")'.format(
            context.sla_template, dic['sla_policy'][template_values]['sla_rpo_levels'],
            dic['sla_policy'][template_values]['sla_rpo_error_levels'],
            dic['sla_policy'][template_values]['sla_rpo'], type)
        match = pyjq.first(condition, resp)
    elif type == 'ha_policy':
        resp = api_get(context, context.version_4 + "/mysql/group/ha_policy/list")
        condition = '.[] | select(."name"=="{0}")| select(."ha_policy_failover_election"=="HA_POLICY_FAILOVER_ELECTION_SAME_ZONE") | select(."ha_policy_semisync_count"=="{1}") | select(."sla_type"=="{2}")'.format(
            context.sla_template, dic['sla_policy'][template_values]['ha_policy_semisync_count'], type)
        match = pyjq.first(condition, resp)
    elif type == 'ha_policy_1':
        resp = api_get(context, context.version_4 + "/mysql/group/ha_policy/list")
        condition = '.[] | select(."name"=="{0}")| select(."ha_policy_failover_election"=="HA_POLICY_FAILOVER_ELECTION_SAME_ZONE") | select(."ha_policy_semisync_count"=="{1}") | select(."sla_type"=="{2}")'.format(
            context.sla_template, dic['sla_policy'][template_values]['ha_policy_semisync_count'], 'ha_policy')
        match = pyjq.first(condition, resp)
    assert (match != None and should_or_not) or (match == None and not should_or_not)


@when(u'the MySQL group {should_or_not:should_or_not} bind the SLA, or I skip the test')
def step_imp(context, should_or_not):
    assert context.mysql_group != None
    group_info = get_group_info_by_id(context, context.mysql_group[0]["mysql_group_id"])
    if should_or_not:
        match = pyjq.first('select(has("mysql_group_sla_template"))', group_info)
    else:
        match = pyjq.first('select(has("mysql_group_sla_template")) | not', group_info)
    if match == False:
        context.scenario.skip("The MySQL group have bind the SLA !")
        return


@when(u'I bind a {template_name:string} to the MySQL group')
def step_imp(context, template_name):
    assert context.mysql_group[0]["mysql_group_id"] != None
    body = {
        "group_id": context.mysql_group[0]["mysql_group_id"],
        "add_sla_template": template_name,
        "is_sync": True,
    }
    api_request_post(context, context.version_3 + "/database/add_sla_protocol", body)


@then(u'the SLA protocol should started')
def step_imp(context):
    assert context.mysql_group != None
    res = get_all_group_info(context)
    match = pyjq.first('.[] | select(.mysql_group_id == "{0}")'.format(context.mysql_group[0]["mysql_group_id"]), res)
    if match['mysql_group_sla_enable'] == "ENABLE":
        return
    assert False


@when(u'the group SLA protocol should started, or I skip the test')
def step_imp(context):
    assert context.mysql_group != None
    res = get_all_group_info(context)
    match = pyjq.first('.[] | select(.mysql_group_id == "{0}")'.format(context.mysql_group[0]["mysql_group_id"]), res)
    if "mysql_group_ha_policy" in match:
        if match['mysql_group_ha_policy_enable'] == "ENABLE":
            return
        else:
            context.scenario.skip('the group SLA protocol is stopped')
            return
    else:
        if match['mysql_group_sla_enable'] == "ENABLE":
            return
        else:
            context.scenario.skip('the group SLA protocol is stopped')
            return


@when(u'the group SLA protocol should paused ,or I skip the test')
def step_imp(context):
    assert context.mysql_group != None
    res = get_all_group_info(context)
    match = pyjq.first('.[] | select(.mysql_group_id == "{0}")'.format(context.mysql_group[0]["mysql_group_id"]), res)
    if "mysql_group_ha_policy" in match:
        if match['mysql_group_ha_policy_enable'] == "DISABLE":
            return
        else:
            context.scenario.skip('the group SLA protocol is enabled')
            return
    else:
        if match['mysql_group_sla_enable'] == "DISABLE":
            return
        else:
            context.scenario.skip('the group SLA protocol is enabled')
            return


@when(u'I stop the group SLA protocol')
def step_imp(context):
    assert context.mysql_group != None
    api_request_post(context, context.version_3 + "/database/pause_sla_protocol", {
        "group_id": context.mysql_group[0]["mysql_group_id"],
        "is_sync": True,
    })


@then(u'the group SLA protocol should stopped')
def step_imp(context):
    assert context.mysql_group != None
    res = get_all_group_info(context)
    match = pyjq.first('.[] | select(.mysql_group_id == "{0}")'.format(context.mysql_group[0]["mysql_group_id"]), res)
    if "mysql_group_ha_policy" in match:
        if match['mysql_group_ha_policy_enable'] == "DISABLE":
            return
        assert False
    else:
        if match['mysql_group_sla_enable'] == "DISABLE":
            return
        assert False


@when(u'I start the group SLA protocol')
def step_imp(context):
    assert context.mysql_group != None
    api_request_post(context, context.version_3 + "/database/start_sla_protocol", {
        "group_id": context.mysql_group[0]["mysql_group_id"],
        "is_sync": True
    })


@then(u'the group SLA protocol should started')
def step_imp(context):
    assert context.mysql_group != None
    res = get_all_group_info(context)
    match = pyjq.first('.[] | select(.mysql_group_id == "{0}")'.format(context.mysql_group[0]["mysql_group_id"]), res)
    if "mysql_group_ha_policy" in match:
        if match['mysql_group_ha_policy_enable'] == "ENABLE":
            return
        assert False
    else:
        if match['mysql_group_sla_enable'] == "ENABLE":
            return
        assert False


@when(u'I unbind the SLA protocol')
def step_imp(context):
    assert context.mysql_group != None
    api_request_post(context, context.version_3 + "/database/remove_sla_protocol", {
        "group_id": context.mysql_group[0]["mysql_group_id"],
        "is_sync": True
    })


@then(u'the MySQL group {should_or_not:should_or_not} have SLA protocol')
def step_imp(context, should_or_not):
    assert context.mysql_group != None
    group_info = get_group_info_by_id(context, context.mysql_group[0]["mysql_group_id"])
    if should_or_not:
        match = pyjq.first('select(has("mysql_group_sla_template"))', group_info)
    else:
        match = pyjq.first('select(has("mysql_group_sla_template")) | not', group_info)
    if match == False:
        return
    else:
        return match


@when(u'I add SLA protocol "{sla}"')
def step_imp(context, sla):
    assert context.mysql_group != None
    body = {
        "group_id": context.mysql_group[0]["mysql_group_id"],
        "add_sla_template": sla,
        "is_sync": True,
    }
    api_request_post(context, context.version_3 + "/database/add_sla_protocol", body)


@then(u'SLA protocol "{sla}" should added')
def step_imp(context, sla):
    assert context.mysql_group != None
    res = get_all_group_info(context)
    match = pyjq.first(
        '.[] | select(.mysql_group_id == "{0}")'.format(
            context.mysql_group[0]["mysql_group_id"]), res)

    assert match is not None and match['mysql_group_sla_template'] == sla
