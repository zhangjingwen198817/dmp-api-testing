from behave import *
from framework.api import *
import pyjq
import random
import time
import string

use_step_matcher("cfparse")


@when(u'I use the {zone_name:string} to create the zone')
def step_impl(context, zone_name):
    api_request_post_rds(context, "/zone/add", {
        "db_type": "mysql",
        "zone_name": zone_name,
        "label": "test-mysql"
    })
    context.zone = zone_name


@Then(u'the zone list should contain the zone name')
def step_impl(context):
    assert context.zone is not None
    zone_names = get_all_zone(context)
    assert context.zone in zone_names


def get_all_zone(context):
    resp = api_get_rds(context, "/zone/list")
    return pyjq.all('.[]|.zone_name', resp)


@When(u'I register the {sip:string} to rds')
def step_impl(context, sip):
    api_request_post_rds(context, "/sip/register", {
        "sip_id": sip
    })


@Then(u'the rds should contain the {sip:string}')
def step_impl(context, sip):
    resp = api_get_rds(context, "/sip/list")
    match = pyjq.first('.[] | select(.sip_id=="{0}")'.format(sip), resp)
    assert match is not None


@When(u'I random found a zone')
def step_impl(context):
    zones_json = api_get_rds(context, "/zone/list")
    zone_ids = pyjq.all('.[]|.zone_id', zones_json)
    index = random.randint(0, len(zone_ids)-1)
    context.zone_id = zone_ids[index]


@When(u'I random found a zone with less number servers')
def step_impl(context):
    zones_json = api_get_rds(context, "/zone/list")
    zone_ids_all = pyjq.all('.[]|.zone_id', zones_json)
    zone_ids = pyjq.all('.[]| select(.server_num < 3) |.zone_id', zones_json)

    if len(zone_ids) == 0:
        index = random.randint(0, len(zone_ids_all)-1)
        context.zone_id = zone_ids_all[index]
    else:
        context.zone_id = zone_ids[0]


@When(u'I found a valid sip on urds')
def step_impl(context):
    resp = api_get_rds(context, "/sip/list")
    sip_ids_all = pyjq.all('. | map(select(."status"=="unused")) | .[] |.sip_id', resp)
    sip_ids_zone = pyjq.all('.[] | select(.zone_ids[]) |.sip_id', resp)
    sip_ids_all_no_zone = list(set(sip_ids_all).difference(set(sip_ids_zone)))
    if len(sip_ids_all_no_zone) > 0:
        context.sip_id = sip_ids_all_no_zone[0]


@When(u'I add sip to zone')
def step_impl(context):
    assert context.sip_id is not None
    assert context.zone_id is not None
    api_request_post_rds(context, "/zone/add_sips", {
        "sip_ids": context.sip_id,
        "zone_id": context.zone_id
    })


@Then(u'the zone should contain the sip')
def step_impl(context):
    assert context.zone_id is not None
    assert context.sip_id is not None
    resp = api_get_rds(context, "/zone/list_sips", {
        "zone_id": context.zone_id
    })
    sip_ids = pyjq.all('.[]|.sip_id', resp)
    assert context.sip_id in sip_ids


@When(u'I delete all sips in urds')
def step_impl(context):
    assert context.sip_ids is not None
    for sip in context.sip_ids:
        api_post_rds(context, "/sip/delete", {
            "sip_id": sip
        })


@When(u'I found a without uproxy zone')
def step_impl(context):
    zones_json = api_get_rds(context, "/zone/list")
    zone_id = pyjq.first('.[] | select(.proxy_num ==0) | .zone_id', zones_json)
    context.zone_id = zone_id


@When(u'I found a uproxy')
def step_impl(context):
    resp = api_get_rds(context, "/support/urds_uproxys")
    uproxy_group_id = pyjq.first('.[] | .uproxy_group_id', resp)
    context.uproxy_group_id = uproxy_group_id


@When(u'I add a uproxy to the zone')
def step_impl(context):
    assert context.zone_id is not None
    assert context.uproxy_group_id is not None
    api_request_post_rds(context, "/zone/add_proxys", {
        "zone_id": context.zone_id,
        "uproxy_group_ids": context.uproxy_group_id
    })


@Then(u'the zone list should contain the uproxy')
def step_impl(context):
    assert context.zone_id is not None
    assert context.uproxy_group_id is not None
    resp = api_get_rds(context, "/zone/list_proxys", {
        "zone_id":  context.zone_id
    })

    match = pyjq.first('.[] | select (.uproxy_group_id=="{0}")'.format(context.uproxy_group_id), resp)
    assert match is not None


@When(u'I found a without {count:int} server zone')
def step_impl(context, count):
    resp = api_get_rds(context, "/zone/list")
    zone_id = pyjq.first('.[] | select(.server_num <={0}) | .zone_id'.format(count), resp)
    context.zone_id = zone_id


@When(u'I found a server')
def step_impl(context):
    resp = api_get_rds(context, "/support/urds_servers")
    server_id = pyjq.first('.[] | select (.zone_id== null) | .server_id', resp)
    context.server_id = server_id


@When(u'I add the server to the zone')
def step_impl(context):
    assert context.zone_id is not None
    assert context.server_id is not None
    api_request_post_rds(context, "/zone/add_servers", {
        "zone_id": context.zone_id,
        "server_ids": context.server_id
    })


@Then(u'the zone server list should contain the server')
def step_impl(context):
    assert context.zone_id is not None
    assert context.server_id is not None
    resp = api_get_rds(context, "/zone/list_servers", {
        "zone_id": context.zone_id
    })

    match = pyjq.first('.[] | select (.server_id=="{0}")'.format(context.server_id), resp)
    assert match is not None


@When(u'I found a valid zone on the urds')
def step_impl(context):
    zones_json = api_get_rds(context, "/zone/list")
    zone_ids = pyjq.all('.[] | select (.server_num > 0) | select(.proxy_num > 0 or .sip_num > 0)  | .zone_id', zones_json)
    index = random.randint(0, len(zone_ids) - 1)
    context.zone_id = zone_ids[index]


@When(u'I modify automatic approval config')
def step_impl(context):
    api_request_post_rds(context, "/system_config/meta_data/update", {
        "id": "automatic-approval",
        "value": 0,
        "category": "automatic-approval",
        "describe": "自动审批"
    })

    api_request_post_rds(context, "/system_config/meta_data/update", {
        "id": "oversold/cpu",
        "value": 20,
        "category": "oversold/cpu",
        "describe": "cpu超卖倍数"
    })

    api_request_post_rds(context, "/system_config/meta_data/update", {
        "id": "backup-rules-enable-slave",
        "value": "0",
        "category": "backup-rules-enable-slave",
        "describe": "slave同时创建备份规则"
    })

    api_request_post_rds(context, "/system_config/meta_data/update", {
        "id": "resource-isolation",
        "value": "false",
        "category": "resource-isolation",
        "describe": "资源隔离"
    })


@When(u'I found mysql template class id')
def step_impl(context):
    resp = api_get_rds(context, "/template/list?db_type=mysql")
    temp_class_id = pyjq.first('.[] | select(.mode=="ordinary") | .service_class_id', resp)
    context.temp_class_id = temp_class_id


@When(u'I add mysql instance')
def step_impl(context):
    assert context.zone_id is not None
    assert context.temp_class_id is not None
    api_request_post_rds(context, "/database/apply_service", {
        "is_automatic": 1,
        "db_service_name": "test-"+generate_id(),
        "is_use_proxy": True,
        "version": 5.7,
        "zone_id": context.zone_id,
        "is_ha_enable": True,
        "is_rws_enable": True,
        "is_ra_enable": False,
        "is_mgr_enable": False,
        "service_class_id": context.temp_class_id,
        "architecture":  "ha_rws",
        "notify_display_names": "root",
        "notify_users": "root/root",
        "db_admin_user": generate_name(),
        "db_admin_password": "sshpass"+str(int(time.time())) + str(random.randint(0, 1000)),
        "max_connection": 1000
    })


def generate_name():
    return 't'.join(random.choices(string.ascii_lowercase + string.digits, k=5)) + str(random.randint(10, 999))


def generate_id():
    return str(int(time.time())) + str(random.randint(0, 10000))


















