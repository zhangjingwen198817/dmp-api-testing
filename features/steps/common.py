from behave import *
from framework.api import *
from util import *
import parse
import pyjq
from getinfo import *
import logging
from pprint import pformat
from hamcrest import *
LOGGER = logging.getLogger("steps.common")

@step('I set base URL to "{base_url}"')
def set_base_url(context, base_url):
    if base_url.startswith("context"):
        context.base_url = getattr(context, base_url[8:])
    else:
        context.base_url = base_url.encode('ascii')


@then(u'the response is ok')
def step_impl(context):
    # assert context.r.status_code == 200
    if context.r.status_code != 200:
        LOGGER.error("API URL is error:<{0}> and params:<{1}>".format(pformat(context.r.url), context.r.json))
        LOGGER.error("API post is error:<{0}>".format(pformat(context.r.text)))
        assert_that(context.r.status_code, equal_to(200), "response is:<{0}>".format(context.r.status_code))

@then(u'the response is not ok')
def step_impl(context):
    assert context.r.status_code != 200

@when(u'I found a valid port, or I skip the test')
def step_impl(context):
    port = find_valid_ports(context)
    if port != None:
        context.valid_port = str(port)
    else:
        context.scenario.skip("Found no valid port")


@when(u'I found {count:int} valid ports, or I skip the test')
def step_impl(context, count):
    ports = []
    for _ in range(0, count):
        port = find_valid_ports(context, ports)
        if port != None:
            ports.append(port)
        else:
            context.scenario.skip("Found no valid ports")
    context.valid_ports = ports


def find_valid_ports(context, excepts=[]):
    for _ in range(0, 1024):
        port = randint(6000, 65535)

        # MySQL ports
        resp = get_instance_list_by_port(context,port)
        if len(resp) > 0:
            continue

        # Ushard ports
        resp = get_ushard_group_list(context)
        match = pyjq.first('.[] | select(.ushard_dble_flow_port == "{0}")'.format(port),
                           resp)
        if match != None:
            continue
        match = pyjq.first(
            '.[] | select(.ushard_dble_manage_port == "{0}")'.format(port), resp)
        if match != None:
            continue

        # except ports
        if port in excepts:
            continue

        return port
    return None


def get_installation_file(context, pattern):
    resp = get_support_component(context, pattern)
    assert len(resp) > 0
    return resp[-1]["Name"]


@then('wait for progress {progress_id:string} is finished in {duration:time}')
def step_imp(context, progress_id, duration):
    def condition(context, flag):
        res = get_progress(context, progress_id)
        if type(res) == list:
            count = 0
            for info in res:
                if info is not None and len(info['err']) == 0 and info['status'] == "successful":
                    count = count + 1
                if count == len(res):
                    return True
        else:
            if res is not None and len(res['err']) == 0 and res['status'] == "successful":
                return True

    waitfor(context, condition, duration)


# util
def get_all_valid_sip(context):
    resp = get_sippool_list(context)
    valid_sip = []
    matchs = pyjq.all('.[] | select(.used_by? == null)', resp)
    for match in matchs:
        if "sip" in match:
            valid_sip.append(match["sip"])
    context.valid_sip = valid_sip
