from behave import *
from framework.api import *
import pyjq
import time
from util import *
from common import *


use_step_matcher("cfparse")


@when(u'I want to create {count:int} zone on the urds')
def step_impl(context, count):
    for i in range(0, count):
        zone_name = "zone-00"+str(i+1)
        context.execute_steps("""
            When I use the {zone_name} to create the zone
            Then the response is ok
            And the zone list should contain the zone name
        """.format(zone_name=zone_name))


@When(u'I found a lot of sip in DMP')
def step_impl(context):
    resp = api_get(context, context.version_3+"/sippool/list")
    sips = pyjq.all('.[].sip', resp)
    context.sips = sips


@When(u'I register the sips to urds')
def step_impl(context):
    assert context.sips is not None
    for sip in context.sips:
        context.execute_steps(u"""
                    When I register the {sip} to rds
                    Then the response is ok
                    And the rds should contain the {sip}
                """.format(sip=sip))


@When(u'I add sips to each zone')
def step_impl(context):
    resp = api_get_rds(context, "/support/unused_sips")
    sips = pyjq.all('.[] | .sip_id', resp)

    for i in range(0, len(sips)):
        context.execute_steps(u"""
            When I random found a zone
            When I found a valid sip on urds
            When I add sip to zone
            Then the response is ok
            And the zone should contain the sip
             """)


@When(u'I found a lot of uproxy group in dmp')
def step_impl(context):
    resp = api_get_rds(context, "/support/unused_uproxys")
    group_ids = pyjq.all('.[] | .uproxy_group_id', resp)
    for group_id in group_ids:
        context.execute_steps(u"""
            When I register the {group_id} group to rds
            Then the response is ok
            And the urds should contain the {group_id}
            """.format(group_id=group_id))


@When(u'I register the {group_id:string} group to rds')
def step_impl(context, group_id):
    assert group_id is not None
    api_request_post_rds(context, "/proxy/register", {
        "uproxy_group_id": group_id,
        "max_service_num": 1000
    })


@Then(u'the urds should contain the {group_id:string}')
def step_impl(context, group_id):
    assert group_id is not None
    resp = api_get_rds(context, "/proxy/list")
    match = pyjq.first('.[]| select(.uproxy_group_id=="{0}")'.format(group_id), resp)
    assert match is not None


@When(u'I add a uproxy to each zone')
def stp_impl(context):
    zones_json = api_get_rds(context, "/zone/list")
    zone_ids = pyjq.all('.[] | select(.proxy_num ==0) | .zone_id', zones_json)
    for i in zone_ids:
        context.execute_steps(u"""
            When I found a without uproxy zone
            When I found a uproxy
            When I add a uproxy to the zone
            Then the response is ok
            And  the zone list should contain the uproxy
            """)


@When(u'I add all dmp server to urds')
def step_impl(context):
    resp = api_get(context, context.version_3+"/server/list", {
        "number": context.page_size_to_select_all
    })
    server_ids = pyjq.all('.data[] | .server_id', resp)
    if server_ids is not None:
        for server_id in server_ids:
            context.execute_steps(u"""
                When I register a {server_id}
                Then the response is ok
                And the server list should contain the server
                    """.format(server_id=server_id))


@when(u'I register a {server_id:string}')
def step_impl(context, server_id):
    assert server_id is not None
    api_request_post_rds(context, "/server/register", {
        "server_id": server_id,
        'cpu': '4',
        'disk': '512',
        'memory': '4096',
        "type": "virtual_machine",
        "iops": 0
    })
    context.server_id = server_id


@Then(u'the server list should contain the server')
def step_impl(context):
    assert context.server_id is not None
    server_id = context.server_id
    r = api_get_rds(context, "/server/list", {
        "key_word": server_id
    })
    assert r is not None


@when(u'I found a lot of valid servers on the urds')
def step_impl(context):
    resp = api_get_rds(context, "/support/urds_servers")
    server_ids = pyjq.all('.[] | select (.zone_id== null) | .server_id', resp)

    for i in range(0, len(server_ids)):
        context.execute_steps(u"""
             When I random found a zone with less number servers
             When I found a server
             When I add the server to the zone
             Then the response is ok
             And the zone server list should contain the server
             """)


@When(u'I add template from config')
def step_impl(context):
    api_request_post_rds(context, "/template/add", {
         "cpu": "1",
         "disk": "10",
         "iops": "100",
         "memory": "64",
         "db_type": "mysql",
         "mode": "ordinary",
         "service_class_name": "mini"
    })

    api_request_post_rds(context, "/template/add", {
      "cpu": "1",
      "disk": "10",
      "iops": "200",
      "memory": "128",
      "db_type": "mysql",
      "mode": "ordinary",
      "service_class_name": "small"
    })

    api_request_post_rds(context, "/template/add", {
      "cpu": "1",
      "disk": "10",
      "iops": "300",
      "memory": "256",
      "db_type": "mysql",
      "mode": "ordinary",
      "service_class_name": "medium"
    })
    context.execute_steps(u"""
          When I modify automatic approval config
        """)


@When(u'I add {count:int} mysql instance')
def step_impl(context, count):
    for i in range(0, count):
        context.execute_steps(u"""
          When I found mysql template class id
          When I found a valid zone on the urds
          When I add mysql instance
          Then the response is ok
        """)


@When(u'I found a lot of mysql services')
def step_impl(context):
    resp = api_get_rds(context, "/approval/list_limit?page=1&number=100")
    approval_ids = pyjq.all('.data[] | select(.db_type=="mysql" and .status=="INIT") | .approval_id', resp)
    for approval_id in approval_ids:
        context.execute_steps(u"""
                 When I approval mysql service by {approval_id}
                 Then the response is ok
            """.format(approval_id=approval_id))
        time.sleep(120)


@When(u'I approval mysql service by {approval_id:string}')
def step_impl(context, approval_id):
    assert approval_id is not None
    api_request_post_rds(context, "/approval/accept", {
        "approval_id": approval_id
    })


@When(u'I found a lot of not sip uproxy group in dmp')
def step_impl(context):
    resp = api_get(context, context.version_5 + "/uproxy/group/list")
    uproxy_groups = pyjq.all(' .data[] | select(.uproxy_group_sip == null) |.uproxy_group_id', resp)
    for uproxy_group_id in uproxy_groups:
        context.execute_steps(u"""
             When I found a unused sip on the dmp
             When I config sip to {uproxy_group_id}
             Then the response is ok
        """.format(uproxy_group_id=uproxy_group_id))


@When(u'I found a unused sip on the dmp')
def step_impl(context):
    resp = api_get(context, context.version_3+"/sippool/list")
    sip = pyjq.first('.[] | select(.used_by == null) | .sip', resp)
    context.sip = sip


@When(u'I config sip to {uproxy_group_id:string}')
def step_impl(context, uproxy_group_id):
    assert context.sip is not None
    assert uproxy_group_id is not None
    api_request_post(context, context.version_3+"/uproxy/config_sip", {
        "group_id": uproxy_group_id,
        "sip": context.sip
    })


@When(u'I add MySQL instance in the MySQL group on all servers')
def setp_impl(context):
    for server in context.server:
        server_id = server["server_id"]
        context.execute_steps(u"""
                        When I add MySQL instance in the MySQL group on the {server_id}
                    """.format(server_id=server_id))


@When(u'I want delete all sips on the urds')
def step_impl(context):
    resp = api_get_rds(context, "/sip/list")
    sips = pyjq.all(".[] | .sip_id", resp)
    for sip in sips:
        context.execute_steps(u"""
               When I delete {sip} urds
           """.format(sip=sip))


@When(u'I delete {sip:string} urds')
def step_impl(context, sip):
    assert sip is not None
    print(sip)
    api_request_post_rds(context, "/sip/unregister", {
        "sip_id": sip
    })

