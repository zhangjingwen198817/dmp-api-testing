from framework.api import *
import json
import requests


@log_it
def api_request_type_op(op,
                        context,
                        url_path_segment,
                        try_login_if_need,
                        params=None,
                        files=None,
                        types=None,
                        stream=None):
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
        if types == None:
            headers = {"authorization": this.token}
        elif types == "raw":
            headers = {
                "authorization": this.token,
                "content-type": "application/json",
                "accept": "application/json, text/plain, */*",
            }
        elif types == "download":
            headers = {
                "authorization": this.token,
                "content-type": "application/octet-stream",
            }

    r = getattr(requests, op)(url, params, headers=headers, files=files, stream=stream)

    if try_login_if_need and r.status_code == 401 and login_fn != None:
        this.token = None
        token = login_fn(context)
        this.token = token
        return api_request_type_op(op, context, url_path_segment, False, params, files=files, types=types, stream=stream)
    else:
        return r


def api_request_type_post(context, url_path_segment, params=None, files=None, types=None):
    r = api_request_type_op("post", context, url_path_segment, True, params, files=files, types=types)
    context.r = r
    return r


def api_request_type_get(context, url_path_segment, params=None, files=None, types=None, stream=None):
    # Files has no use
    r = api_request_type_op("get", context, url_path_segment, True, params, types=types, stream=stream)
    context.r = r
    return r


def api_get_text_response(context, r=None):
    if r is None:
        return context.r.json()
    elif r.content:
        try:
            return r.json()
        except json.decoder.JSONDecodeError:
            return r.text
            # return str(r.content, encoding="utf-8")
    else:
        return r


def api_get_text(context, url_path_segment, params=None, files=None):
    # Files has no use
    r = api_request_op("get", context, url_path_segment, True, params)
    assert r.status_code == 200
    return api_get_text_response(context, r)
