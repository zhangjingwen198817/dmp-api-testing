import random
import time
import sys
import yaml
import logging
from logging import config
import os
import shutil
from pprint import pformat
from framework import log_it


def init_log_directory(symbolic=False):
    logs_dir = 'logs'
    symbolic_link = 'log'
    cwd = os.getcwd()

    if not os.path.exists(logs_dir):
        os.mkdir(logs_dir)

    os.chdir(logs_dir)

    if symbolic:
        suffix = time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime())
        current_log = 'log_' + suffix
        if os.path.exists(current_log):
            shutil.move(current_log, current_log + '_bak')

        os.mkdir(current_log)
        if os.path.exists(symbolic_link):
            os.remove(symbolic_link)

        os.symlink(current_log, symbolic_link)
    else:
        if os.path.exists(symbolic_link):
            shutil.rmtree(symbolic_link)
        os.mkdir(symbolic_link)

    os.chdir(cwd)

    return os.path.join(logs_dir, symbolic_link)


def setup_logging(logging_path):
    if os.path.exists(logging_path):
        with open(logging_path, 'rt') as f:
            dict_config = yaml.load(f.read())
        logging.config.dictConfig(dict_config)
    else:
        print('No such logging config file : <{0}>'.format(logging_path))
        exit(1)


@log_it
def load_yaml_config(config_path):
    with open(config_path, 'r') as f:
        parsed = yaml.load(f)
    return parsed


def randint(start, end):
    random.seed()
    return random.randint(start, end)


def waitfor(context, getter, duration, interval=1, flag=False):
    starttime = time.time()
    timeout = duration * context.time_weight
    while time.time() - starttime < timeout:
        if getter(context, flag):
            return
        time.sleep(interval)
    else:
        raise Exception


def generate_id():
    return str(int(time.time())) + str(random.randint(0, 10000))


def parse_option_values(text):
    temp = text.split(', ')
    dict_values = {}
    for value in temp:
        arr = value.split(":")
        dict_values[arr[0].strip()] = arr[1].strip()
    return dict_values


def debug_info(context):
    method_name = sys._getframe(1).f_code.co_name
    print(method_name)
    print(context.mysql_group)
    print("")


def readYaml(yamlPath):
    f = open(yamlPath, 'r', encoding='utf-8')
    cfg = f.read()
    dic = yaml.load(cfg)
    return dic
