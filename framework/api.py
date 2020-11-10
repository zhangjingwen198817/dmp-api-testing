import requests

import sys
from framework import log_it
this = sys.modules[__name__]
this.login_fn = None
this.token = None
this.login_fn_rds = None
this.urds_token = None
this.cookie = None
import logging
from pprint import pformat
from hamcrest import *
LOGGER = logging.getLogger("environment.api")
def api_set_token():
    this.token = None

def api_set_login_fn(fn):
    this.login_fn = fn


def api_set_login_fn_rds(fn_rds):
    this.login_fn_rds = fn_rds


def api_get_response(context, r=None):
    if r is None:
        return context.r.json()
    elif r.content:
        return r.json()
    else:
        return r


def api_get(context, url_path_segment, params=None, files=None):
    # Files has no use
    r = api_request_op("get", context, url_path_segment, True, params)
    assert r.status_code == 200
    return api_get_response(context, r)


def api_post(context, url_path_segment, params=None, files=None):
    r = api_request_op("post", context, url_path_segment, True, params, files=files)
    if r.status_code != 200:
        LOGGER.error("API URL is error:<{0}> and params:<{1}>".format(pformat(r.url),params))
        LOGGER.error("API post is error:<{0}>".format(pformat(r.text)))
        assert_that(r.status_code,equal_to(200),"response is:<{0}>".format(r.status_code))
    return api_get_response(context, r)


def api_request_get(context, url_path_segment, params=None, files=None):
    # Files has no use
    r = api_request_op("get", context, url_path_segment, True, params)
    context.r = r
    return r


def api_request_post(context, url_path_segment, params=None, files=None):
    r = api_request_op("post", context, url_path_segment, True, params, files=files)
    context.r = r
    return r

@log_it
def api_request_op(op,
                   context,
                   url_path_segment,
                   try_login_if_need,
                   params=None,
                   files=None):
    url = context.base_url + url_path_segment

    if context == params:
        params = {}
        for row in context.table:
            for x in context.table.headings:
                params[x] = row[x]
                if row[x].startswith("context"):
                    params[x] = eval(row[x])

    headers = {}
    if this.token != None:
        headers = {"authorization": this.token}

    r = getattr(requests, op)(url, params, headers=headers, files=files)        
    api_log_full(r)
        



    if try_login_if_need and r.status_code == 401 and login_fn != None:
        this.token = None
        token = login_fn(context)
        this.token = token
        return api_request_op(op, context, url_path_segment, False, params, files=files)
    else:
        return r


# urds
def api_get_rds(context, url_path_segment, params=None, files=None):
    # Files has no use
    r = api_request_op_rds("get", context, url_path_segment, True, params)
    assert r.status_code == 200
    return api_get_response(context, r)


def api_post_rds(context, url_path_segment, params=None, files=None):
    r = api_request_op_rds("post", context, url_path_segment, True, params, files=files)
    assert r.status_code == 200
    return api_get_response(context, r)


def api_request_get_rds(context, url_path_segment, params=None, files=None):
    # Files has no use
    r = api_request_op_rds("get", context, url_path_segment, True, params)
    context.r = r
    return r


def api_request_post_rds(context, url_path_segment, params=None, files=None):
    r = api_request_op_rds("post", context, url_path_segment, True, params, files=files)
    context.r = r
    return r


def api_request_op_rds(op,
                   context,
                   url_path_segment,
                   try_login_if_need,
                   params=None,
                   files=None):
    url = context.rds_base_url + url_path_segment

    if context == params:
        params = {}
        for row in context.table:
            for x in context.table.headings:
                params[x] = row[x]
                if row[x].startswith("context"):
                    params[x] = eval(row[x])

    headers = {}
    if this.urds_token != None:
        headers = {"authorization": this.urds_token, "Cookie": this.cookie}

    r = getattr(requests, op)(url, params, headers=headers, files=files)
    api_log_full(r)

    if try_login_if_need and r.status_code == 401 and login_fn_rds != None:
        this.urds_token = None
        urds_token = login_fn_rds(context)
        this.urds_token = urds_token
        return api_request_op_rds(op, context, url_path_segment, False, params, files=files)
    else:
        return r


def api_log_full(r):
    req = r.request
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".
    However pay attention at the formatting used in
    this function because it is programmed to be pretty
    printed and may differ from the actual request.
    """

    print("")
    print("")

    print('{0}\n{1}\n{2}\n\n{3}'.format(
        '-----------REQUEST-----------',
        req.method + ' ' + req.url,
        '\n'.join('{0}: {1}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))

    print("")

    print('{0}\n{1}\n{2}\n\n{3}'.format(
        '-----------RESPONSE-----------',
        str(r.status_code) + ' ' + r.reason,
        '\n'.join('{0}: {1}'.format(k, v) for k, v in r.headers.items()),
        r.text,
    ))
    print("")
    for k, v in r.headers.items():
        if k == "Set-Cookie":
            this.cookie = v

    print('Operation took ' + str(round(r.elapsed.total_seconds(), 3)) + 's')

    print("")
    print("")
    print("")
    print("")
