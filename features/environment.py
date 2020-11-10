from yaml import load
from framework import *
import logging
from features.steps.util import *
CONF_PATH = 'conf/'
logger = logging.getLogger('environment')
def before_all(context):
    context.current_log = init_log_directory()

    setup_logging(os.path.join(CONF_PATH, 'logging.yml'))
    logger.debug('Setup logging configfile=<{0}>'.format(os.path.join(CONF_PATH, 'logging.yml')))

    logger.info('*' * 30)
    logger.info('*       DMP TEST START       *')
    logger.info('*' * 30)

    ud = context.config.userdata
    context.base_url = ud.get("base_url")
    context.rds_base_url = ud.get("rds_base_url")
    context.version_3 = ud.get("version_3")
    context.version_4 = ud.get("version_4")
    context.version_5 = ud.get("version_5")
    context.version_6 = ud.get("version_6")
    context.component_installation_dir = ud.get(
        "component_installation_dir")
    #context.time_weight = ud.get("time_weight")
    context.time_weight = int(ud.get("time_weight"))
    context.page_size_to_select_all = ud.get(
        "page_size_to_select_all")
    context.token = None
    context.mysql_installation_dir = ud.get("mysql_installation_dir")
    context.mysql_version = ud.get("mysql_version")

    context.new_server_ip = ud.get('new_server_ip')
    context.new_server_ssh_port = ud.get('new_server_ssh_port')
    context.new_server_ssh_user = ud.get('new_server_ssh_user')
    context.new_server_ssh_password = ud.get('new_server_ssh_password')

    context.group_sip_1 = ud.get('group_sip_1')
    context.group_sip_2 = ud.get('group_sip_2')
    context.group_sip_3 = ud.get('group_sip_3')
    context.group_sip_4 = ud.get('group_sip_4')
    context.group_sip_5 = ud.get('group_sip_5')
    context.group_sip_6 = ud.get('group_sip_6')
    context.group_sip_7 = ud.get('group_sip_7')
    context.group_sip_8 = ud.get('group_sip_8')
    context.group_sip_9 = ud.get('group_sip_9')
    context.group_sip_10 = ud.get('group_sip_10')
    context.group_sip_11 = ud.get('group_sip_11')
    context.group_sip_12 = ud.get('group_sip_12')
    context.group_sip_13 = ud.get('group_sip_13')
    context.group_sip_14 = ud.get('group_sip_14')
    context.group_sip_15 = ud.get('group_sip_15')
    context.group_sip_16 = ud.get('group_sip_16')
    context.group_sip_17 = ud.get('group_sip_17')
    context.group_sip_18 = ud.get('group_sip_18')
    context.group_sip_19 = ud.get('group_sip_19')
    context.group_sip_20 = ud.get('group_sip_20')
    context.group_sip_21 = ud.get('group_sip_21')
    context.group_sip_22 = ud.get('group_sip_22')
    context.group_sip_23 = ud.get('group_sip_23')
    context.group_sip_24 = ud.get('group_sip_24')
    context.group_sip_25 = ud.get('group_sip_25')
    context.group_sip_26 = ud.get('group_sip_26')
    context.group_sip_27 = ud.get('group_sip_27')
    context.group_sip_28 = ud.get('group_sip_28')
    context.group_sip_29 = ud.get('group_sip_29')
    context.group_sip_30 = ud.get('group_sip_30')
    context.sips = []
    for i in range(1, 31):
        context.sips.append(eval('context.group_sip_' + str(i)))

def after_all(context):

    logger.info('*' * 30)
    logger.info('*       DMP TEST END        *')
    logger.info('*' * 30)


def before_feature(context, feature):
    logger.info('Feature start: <{0}>'.format(feature.name))


def after_feature(context, feature):
    logger.info('Feature end <{0}>'.format(feature.name))
    logger.info('*' * 30)


def before_scenario(context, scenario):
    logger.info('#' * 30)
    logger.info('Scenario start: <{0}>'.format(scenario.name))

def after_scenario(context, scenario):
    logger.info('Scenario end: <{0}>'.format(scenario.name))
    logger.info('#' * 30)


def before_step(context, step):
    logger.info('-' * 30)
    logger.info('Step start: <{0}>'.format(step.name))

def after_step(context, step):
    logger.info('Step end: <{0}>'.format(step.name))
    logger.info('-' * 30)

