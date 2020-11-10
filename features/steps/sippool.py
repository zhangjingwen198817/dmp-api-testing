from behave import *
from framework.api import *
import pyjq
import time
from common import *
import random
use_step_matcher("cfparse")


@when(u'I found a ip segments xx.xx.0.0/16 which not contains in sip pool')
def step_impl(context):
    exist_ips = get_sippool_all_ips(context)

    context.free_ip_segments = None

    for i in range(100, 254):
        conflict_with_exist = any(
            ip.startswith('{0}.'.format(i)) for ip in exist_ips)
        if exist_ips == None or (not conflict_with_exist):
            context.free_ip_segments = '{0}.1'.format(i)
            break

    assert context.free_ip_segments != None


@when(u'I add ip {ip_desc:string} to sip pool')
def step_impl(context, ip_desc):
    assert context.free_ip_segments != None

    ip_desc = ip_desc.replace("xx.xx", context.free_ip_segments)
    api_request_post(context, context.version_3 + "/sippool/add", {
        "is_sync": "true",
        "sip": ip_desc,
    })


@when(u'I remove ip {ip_desc:string} from sip pool')
def step_impl(context, ip_desc):
    assert context.free_ip_segments != None

    ip_desc = ip_desc.replace("xx.xx", context.free_ip_segments)
    api_request_post(context, context.version_3 + "/sippool/remove", {
        "is_sync": "true",
        "sip": ip_desc,
    })


@then(
    u'the sip pool should have {expect_count:int} ips match {ip_pattern:string}'
)
def step_impl(context, expect_count, ip_pattern):
    assert context.free_ip_segments != None
    exist_ips = get_sippool_all_ips(context)

    ip_prefix = ip_pattern.rstrip("*").replace("xx.xx",
                                               context.free_ip_segments)
    count = 0
    for ip in exist_ips:
        if ip.startswith(ip_prefix):
            count += 1

    assert count == expect_count


@then(u'the sip pool should contain {expect_ips:strings+}')
def step_impl(context, expect_ips):
    assert context.free_ip_segments != None
    exist_ips = get_sippool_all_ips(context)

    for expect_ip in expect_ips:
        expect_ip = expect_ip.replace("xx.xx", context.free_ip_segments)
        assert expect_ip in exist_ips


@then(u'the sip pool should not contain {expect_ips:strings+}')
def step_impl(context, expect_ips):
    assert context.free_ip_segments != None
    exist_ips = get_sippool_all_ips(context)

    for expect_ip in expect_ips:
        expect_ip = expect_ip.replace("xx.xx", context.free_ip_segments)
        assert not (expect_ip in exist_ips)


@when(u'I found a valid SIP, or I skip the test')
def step_impl(context):
    resp = api_get(context, context.version_3 + "/sippool/list", {
        "number": context.page_size_to_select_all,
    })
    match = pyjq.first('.[] | select(.used_by? == null)', resp)
    if match is None:
        context.scenario.skip("Found no MySQL instance without backup rule")
        return
    context.valid_sip = match["sip"]


@then(u'the sip pool should contain the added IP')
def step_impl(context):
    assert context.sips != None
    exist_ips = get_sippool_all_ips(context)

    for expect_ip in context.sips:
        assert expect_ip in exist_ips


@when(u'I remove a sip from sippool')
def step_impl(context):
    resp = get_sippool_all_ips(context)
    if not resp:
        context.scenario.skip("the sippool is empty")
    else:
        context.sip = resp[0]['sip']
        api_request_post(context, context.version_3 + "/sippool/remove", {
            "sip": context.sip,
            "is_sync": True
        })


@then(u'I can not find the sip from the sip pool')
def step_impl(context):
    resp = get_sippool_all_ips(context)
    isContain = False
    for sip in resp:
        if sip["sip"] == context.sip:
            isContain = True
    context.isContain = isContain
    assert not isContain


@when(u'I add a sip to sippool')
def step_impl(context):
    if not context.isContain:
        api_request_post(context, context.version_3 + "/sippool/add", {
            "is_sync": True,
            "sip": context.sip
        })
    else:
        context.scenario.skip("this sip already exists")


@then(u'the config should succeed in {duration:time}')
def step_impl(context, duration):
    def condition(context, flag):
        mysql_group_id = context.mysql_instance[0]["mysql_group_id"]
        resp = get_mysql_info_in_group(context, mysql_group_id)
        for instance in resp:
            assert instance["mysql_instance_useable_sip"] == context.sip
        return True

    waitfor(context, condition, duration)


@when(u'I remove sip from the database instance')
def step_impl(context):
    assert context.mysql_instance != None
    for instance in context.mysql_instance:
        api_request_post(context, context.version_3 + "/database/update_mysql_instance_sip", {
            "is_sync": True,
            "mysql_id": instance["mysql_instance_id"]
        })


@then(u'the operation should succeed in {duration:time}')
def step_impl(context, duration):
    def condition(context, flag):
        mysql_group_id = context.mysql_instance[0]["mysql_group_id"]
        resp = get_mysql_info_in_group(context, mysql_group_id)
        match = pyjq.all('.[] | select(has("mysql_instance_useable_sip"))', resp)
        assert match == []
        return True

    waitfor(context, condition, duration)


@when(u'I found a MySQL {master_or_slave:string} instance in the group')
def step_impl(context, master_or_slave):
    mysql_group_id = context.mysql_group[0]["mysql_group_id"]
    instances = get_mysql_info_in_group(context, mysql_group_id)
    context.master_instance = pyjq.first('.[]|select(.mysql_instance_role=="STATUS_MYSQL_MASTER")', instances)
    context.slave_instance = pyjq.first('.[]|select(.mysql_instance_role=="STATUS_MYSQL_SLAVE")', instances)
    if master_or_slave == "master":
        context.mysql_instance = context.master_instance
    elif master_or_slave == "slave":
        context.mysql_instance = context.slave_instance
    print(context.mysql_instance)


@when(u'I prepare the instance with sip if not exists')
def step_impl(context):
    mysql_instance_id = context.mysql_instance["mysql_instance_id"]
    get_all_valid_sip(context)
    sip = random.choice(context.valid_sip)
   # context.valid_sip.pop(0)
    if "mysql_instance_useable_sip" not in context.mysql_instance:
        api_request_post(context, context.version_3 + "/database/update_mysql_instance_sip", {
            "is_sync": True,
            "mysql_id": mysql_instance_id,
            "sip": sip,
        })
    context.sip = sip


@then(u'the MySQL {master_or_slave:string} instance {should_or_not:should_or_not} have sip')
def step_impl(context, master_or_slave, should_or_not):
    if master_or_slave == "master":
        mysql_instance_id = context.master_instance["mysql_instance_id"]
    elif master_or_slave == "slave":
        mysql_instance_id = context.slave_instance["mysql_instance_id"]
    instance = get_mysql_info_by_id(context, mysql_instance_id)
    flag = ("mysql_instance_useable_sip" in instance) and (instance["mysql_instance_useable_sip"] == context.sip)
    assert (flag and should_or_not) or (not flag and not should_or_not)


@when(u'I remove the sip for the MySQL {master_or_slave:string} instance')
def step_impl(context, master_or_slave):
    if master_or_slave == "master":
        mysql_instance_id = context.master_instance["mysql_instance_id"]
    elif master_or_slave == "slave":
        mysql_instance_id = context.slave_instance["mysql_instance_id"]
    api_post(context, context.version_3 + "/database/update_mysql_instance_sip", {
        "is_sync": True,
        "mysql_id": mysql_instance_id,
    })


@when(u'I update the sip for the umc with id {component_group_id:string}')
def step_impl(context, component_group_id):
    sip = context.valid_sip
    api_request_post(context, context.version_3 + "/component/group/update_sip", {
        "is_sync": True,
        "component_group_id": component_group_id,
        "component_group_type": "umc",
        "sip": sip,
    })
    context.component_group_id = component_group_id


@then(u'the umc sip should in the sip list')
def step_impl(context):
    resp = get_sippool_list(context)
    info = pyjq.first('.[]|select(.sip=="{0}")'.format(context.valid_sip), resp)
    component_group_id = info["used_by"]
    assert component_group_id == context.component_group_id
