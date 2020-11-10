from getinfo import *


@when(u'I create {roleName:string} with administrator authorities,or I skip the test if the role already exists')
def step_impl(context, roleName):
    context.role = roleName
    roles = get_role_list(context)
    match = pyjq.first('.[]|select(.id=="{0}")'.format(roleName), roles)
    if match is not None:
        context.scenario.skip("Role name already exists")
        return

    authorityList = get_user_action_list(context)

    tagList = get_tag_pool_list(context)
    tags = []
    for dir in tagList:
        for key, value in dir.items():
            if key == "tag_attribute":
                tag_key = value
            if key == "tag_values":
                for v in value:
                    tag_value = v
                    tag = {"attribute": tag_key, "value": tag_value}
                    tags.append(tag)

    api_request_post(context, context.version_3 + "/role/add_role", {
        "is_sync": "true",
        "authority": json.dumps(authorityList),
        "prohibit": '',
        "role_id": roleName,
        "tags": json.dumps(tags)
    })


@when(u'I update {roleName:string} without {authority:string},or I skip the test if the role already exists')
def step_impl(context, roleName, authority):
    context.role = roleName
    roles = get_role_list(context)
    match = pyjq.first('.[]|select(.id=="{0}")'.format(roleName), roles)
    if match is None:
        context.scenario.skip("Role not exists")
        return

    authorityList = get_user_action_list(context)

    prohibit = ''
    for key, value in authorityList.items():
        if isinstance(value, dict):
            for k, v in value.items():
                for i in range(len(v) - 1, -1, -1):
                    v[i]["type"] = k
                    if v[i]["btn"] == authority:
                        if v[i]["name"] != "":
                            prohibit += v[i]["name"]
                        v.remove(v[i])
        else:
            for i in range(len(value) - 1, -1, -1):
                if value[i]["btn"] == authority:
                    if value[i]["name"] != "":
                        prohibit += value[i]["name"]
                    value.remove(value[i])

    tagList = get_tag_pool_list(context)
    tags = []
    for dir in tagList:
        for key, value in dir.items():
            if key == "tag_attribute":
                tag_key = value
            if key == "tag_values":
                for v in value:
                    tag_value = v
                    tag = {"attribute": tag_key, "value": tag_value}
                    tags.append(tag)

    api_request_post(context, context.version_3 + "/role/update_role", {
        "is_sync": "true",
        "authority": json.dumps(authorityList),
        "prohibit": prohibit,
        "role_id": roleName,
        "tags": json.dumps(tags)
    })


@then(u'the {roleName:string} {should_or_not:should_or_not} contain {authority:string}')
def step_impl(context, roleName, should_or_not, authority):
    roles = get_role_list(context)
    match = pyjq.first('.[]|select(.id=="{0}")|.authority'.format(roleName), roles)
    result = []
    for key, value in json.loads(match).items():
        if isinstance(value, dict):
            for k, v in value.items():
                alist = pyjq.all('.[]|.btn', v)
                result.extend(alist)
        else:
            blist = pyjq.all('.[]|.btn', value)
            result.extend(blist)
    assert (should_or_not and authority in result) or (not should_or_not and authority not in result)


@then(u'the role list {should_or_not:should_or_not} contain the role')
def step_impl(context, should_or_not):
    assert context.role is not None
    roles = get_role_list(context)
    match = pyjq.first('.[]|select(.id=="{0}")'.format(context.role), roles)
    assert (match is not None and should_or_not) or (match is None and not should_or_not)


@when(
    u'I create {userName:string} with the role,password is {password:string},or I skip the test if the user already exists')
def step_impl(context, userName, password):
    assert context.role is not None
    context.user = userName

    users = get_user_list(context)
    match = pyjq.first('.[]|select(.name=="{0}")'.format(userName), users)
    if match is not None:
        context.scenario.skip("userName already exists")
        return

    api_request_post(context, context.version_3 + "/user/add_user", {
        "name": userName,
        "password": password,
        "roleId": context.role,
        "is_sync": "true"
    })


@then(u'the user list {should_or_not:should_or_not} contain the user')
def step_impl(context, should_or_not):
    assert context.user is not None
    users = get_user_list(context)
    match = pyjq.first('.[]|select(.name=="{0}")'.format(context.user), users)
    assert (match is not None and should_or_not) or (match is None and not should_or_not)


@when(u'I login with {userName:string},{password:string}')
def step_impl(context, userName, password):
    context.userName = userName
    context.password = password
    api_set_login_fn(login)


def login(context):
    resp = api_post(context, "user/login", {
        "user": context.userName,
        "password": context.password
    })
    return resp["token"]


@then(u'the login user should be {user:string}')
def step_impl(context, user):
    resp = get_login_user(context)
    assert resp["name"] == user


@when(u'I logout of the current user')
def step_impl(context):
    api_request_post(context, context.version_3 + "/user/logout")
    api_set_token()
