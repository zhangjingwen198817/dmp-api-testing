from behave import *
from framework.api import *
import parse
import re


@parse.with_pattern(r"should( not)?")
def parse_should_or_not(text):
    if text == "should not":
        return False
    else:
        return True


register_type(should_or_not=parse_should_or_not)


@parse.with_pattern(r"[^\s]+")
def parse_strings(text):
    return text.strip(" ,")


register_type(strings=parse_strings)


@parse.with_pattern(r"(\s*[^\s]+\s*:\s*[^\s]+,?)+")
def parse_option_values(text):
    temp = text.split(', ')
    dict_values = {}
    for value in temp:
        arr = value.split(":")
        dict_values[arr[0].strip()] = arr[1].strip()
    return dict_values


register_type(option_values=parse_option_values)


@parse.with_pattern(r"[^\s]+")
def parse_string(text):
    return text.strip()


register_type(string=parse_string)


@parse.with_pattern(r".*")
def parse_any(text):
    return text.strip()


register_type(any=parse_any)


@parse.with_pattern(r"[\d]+")
def parse_int(text):
    return int(text)


register_type(int=parse_int)


@parse.with_pattern(r"s")
def parse_s(text):
    return text


register_type(s=parse_s)


@parse.with_pattern(r"[\d]+[sm]")
def parse_time(text):
    num = int(text.strip("sm"))
    if text[-1] == 'm':
        return num * 60
    else:
        return num


register_type(time=parse_time)


def login(context):
    resp = api_post(context, "user/login", {
        "user": "admin",
        "password": "admin",
    })
    return resp["token"]


api_set_login_fn(login)

def urds_login(context):
    resp = api_post_rds(context, "/user/login", {
        "user_group": "root",
        "password": "cm9vdA==",
        "user": "cm9vdA=="
    })
    return resp["token"]


api_set_login_fn_rds(urds_login)
