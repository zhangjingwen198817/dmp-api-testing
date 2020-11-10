from behave import *
from framework.api import *
import pyjq
import random
import time
import json
import re
from util import *
from common import *

use_step_matcher("cfparse")


@when(u'I create a tag in tag pool with attribute {attribute:string}')
def step_impl(context, attribute):
    add_random_to_tag_pool(context, attribute)


def creat_a_random_tag(attribute):
    list_random = attribute
    for i in range(4):
        a = random.randrange(0, 10)
        list_random = list_random + str(a)
    return list_random


def add_random_to_tag_pool(context, attribute):
    tag = creat_a_random_tag(attribute)
    api_request_post(context, context.version_4 + "/tag/add", {
        "is_sync": True,
        "tag_attribute": attribute,
        "tag_value": tag,
        "tag_color": "blue",
    })
    context.tag_value = tag
    context.attribute = attribute


@then(u'the tag should be in the tag pool')
def step_impl(context):
    resp = get_all_tag_info(context)
    tag_list = pyjq.all('.[] | select(."tag_attribute" == "{0}")'.format(context.attribute), resp)
    flag = False
    for tag in tag_list:
        if tag["tag_value"] == context.tag_value:
            flag = True
            break
    assert flag


@when(u'I found a server and add the tag')
def step_impl(context):
    server = get_all_server_info(context)
    server_id = server[0]["server_id"]
    api_post(context, context.version_3 + "/server/add_tag", {
        "is_sync": True,
        "server_id": server_id,
        "attribute": context.attribute,
        "value": context.tag_value,
    })
    context.server_id = server_id


@then(u'the tag should be in the server tag list')
def step_impl(context):
    resp = get_server_info_by_id(context, context.server_id)
    server_tags = resp["server_tags"]
    flag = False
    for tag in server_tags:
        if tag["tag_value"] == context.tag_value:
            flag = True
            break
    assert flag


@when(u'I add a tag to the instance')
def step_impl(context):
    mysql_group = context.mysql_group[0]
    mysql_group_id = mysql_group["mysql_group_id"]
    instance = get_mysql_info_in_group(context, mysql_group_id)
    mysql_instance_id = instance[0]["mysql_instance_id"]
    context.mysql_instance_id = mysql_instance_id
    api_request_post(context, context.version_3 + "/mysql/instance/tag/add", {
        "is_sync": True,
        "mysql_id": mysql_instance_id,
        "tag_attribute": context.attribute,
        "tag_value": context.tag_value,
    })


@then(u'the tag {should_or_not:should_or_not} be in the instance tag list')
def step_impl(context, should_or_not):
    resp = get_mysql_info_by_id(context, context.mysql_instance_id)
    mysql_instance_tags = resp["mysql_instance_tags"]
    flag = False
    for tag in mysql_instance_tags:
        if tag["tag_value"] == context.tag_value:
            flag = True
            break
    if should_or_not:
        assert flag
    elif not should_or_not:
        assert not flag


@when(u'I found a instance with tag attributed {attribute:string}')
def step_impl(context, attribute):
    context.attribute = attribute
    instances = get_all_mysql_info(context)
    for instance in instances:
        mysql_instance_tags = instance["mysql_instance_tags"]
        if len(mysql_instance_tags) != 0:
            for tag in mysql_instance_tags:
                if tag["tag_attribute"] == attribute:
                    context.mysql_instance_id = instance["mysql_instance_id"]
                    context.tag_value = tag["tag_value"]
                    break
        break


@when(u'I remove the tag from the instance')
def step_impl(context):
    api_request_post(context, context.version_3 + "/mysql/instance/tag/remove", {
        "is_sync": True,
        "mysql_id": context.mysql_instance_id,
        "tag_attribute": context.attribute,
        "tag_value": context.tag_value,
    })


@when(u'I found a MySQL group,or I skip the test')
def step_impl(context):
    context.group_info = get_all_group_info(context)[0]
    if not context.group_info:
        context.scenario.skip("Found no MySQL group")


@when(u'I add a tag to the group')
def step_impl(context):
    mysql_group_id = context.group_info["mysql_group_id"]
    api_request_post(context, context.version_3 + "/mysql/group/tag/add", {
        "is_sync": True,
        "mysql_group_id": mysql_group_id,
        "tag_attribute": context.attribute,
        "tag_value": context.tag_value,
    })


@then(u'the tag {should_or_not:should_or_not} be in the group tag list')
def step_impl(context, should_or_not):
    mysql_group_id = context.group_info["mysql_group_id"]
    resp = get_group_info_by_id(context, mysql_group_id)
    mysql_group_tags =  resp["mysql_group_tags"]
    flag = False
    for tag in mysql_group_tags:
        if tag["tag_value"] == context.tag_value:
            flag = True
            break
    if should_or_not:
        assert flag
    elif not should_or_not:
        assert not flag


@when(u'I found a group with tag attributed {attribute:string}')
def step_impl(context, attribute):
    context.attribute = attribute
    groups = get_all_group_info(context)
    for group in groups:
        mysql_group_tags = group["mysql_group_tags"]
        if len(mysql_group_tags) != 0:
            for tag in mysql_group_tags:
                if tag["tag_attribute"] == attribute:
                    context.group_info = group
                    context.mysql_group_id = group["mysql_group_id"]
                    context.tag_value = tag["tag_value"]
                    break
        break


@when(u'I remove the tag from the group')
def step_impl(context):
    api_request_post(context, context.version_3 + "/mysql/group/tag/remove", {
        "is_sync": True,
        "mysql_group_id": context.mysql_group_id,
        "tag_attribute": context.attribute,
        "tag_value": context.tag_value,
    })


@when(u'I update the tag to a new one in {duration:time}')
def step_impl(context, duration):
    old_tag_attribute = context.attribute
    old_tag_value = context.tag_value
    tag_attribute = old_tag_attribute + "new"
    tag_value = old_tag_value + "new"
    api_request_post(context, context.version_4 + "/tag/update", {
        "old_tag_attribute": old_tag_attribute,
        "old_tag_value": old_tag_value,
        "tag_attribute": tag_attribute,
        "tag_value": tag_value,
        "tag_color": "blue",
    })
    context.attribute = tag_attribute
    context.tag_value = tag_value

    def condition(context, flag):
        resp = get_all_tag_info(context)
        tag = pyjq.first('.[] | select(."tag_value" == "{0}")'.format(context.tag_value), resp)
        if tag:
            return True

    waitfor(context, condition, duration)


