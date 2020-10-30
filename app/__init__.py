import os
from flask import Flask
from config.logger import config_logger
from app.api import blueprint_config
from config import config
from app.api.celery_worker import CLASSMODEL


from app.extensions import *
from app.database import db


def register_logger():
    '''
    越早注册日志，日志就会越早开始收集。如果载入配置类后才配置日志，那如果创建 app 时报错就无法被我们定义的日志收集器收集到了
    从环境变量里获取配置，并调用之前的配置函数配置日志
    '''
    log_level = os.environ.get('LOG_LEVEL') or 'INFO'
    log_file = os.environ.get('LOG_FILE') or 'app.log'
    config_logger(
        enable_console_handler=True,
        enable_file_handler=True,
        log_level=log_level,
        log_file=log_file
    )


def get_config_object(env=None):
    '''
    载入配置对象的方法
    从 FLASK_ENV 这个环境变量获取运行的环境，然后根据之前配置类里的 config_map 获取对应的配置类，实现配置类的载入
    '''
    if not env:
        env = os.environ.get('FLASK_ENV')
    else:
        os.environ['FLASK_ENV'] = env
    if env in config.config_map:
        return config.config_map[env]
    else:
        # set default env if not set
        env = 'production'
        return config.config_map[env]


def create_app_by_config(conf=None):
    '''
    这里做了几个事情，一是注册日志类，二是载入配置对象，三是创建 instance 目录，四是注册应用业务
    '''
    # initialize logger
    register_logger()
    # check instance path
    instance_path = os.environ.get('INSTANCE_PATH') or None
    # create and configure the app
    app = Flask(__name__, instance_path=instance_path)

    # ensure the instance folder exists
    if app.instance_path:
        try:
            os.makedirs(app.instance_path)
        except OSError:
            pass

    # 加载配置
    # 方式1：对象
    if not conf:
        conf = get_config_object()
    app.config.from_object(conf)
    # 方式2：文件
    # app.config.from_pyfile('d2_config.py')
    # 方式3：环境变量
    # app.config.from_envvar('CONFIG')


    ###########################################扩展###########################################
    # 加载扩展，这里加入了firstApi这个视图，暂时不用
    # extension_config(app)


    # 添加sql数据库
    # 添加sql数据库配置文件到flask App中
    app.config.from_object(config.mysql_map)
    # 注册数据库连接
    db.app = app
    db.init_app(app)


    # 添加redis数据库
    # 添加redis数据库配置文件到flask App中
    app.config.from_object(config.redis_map)
    ###########################################扩展###########################################

    # 注册蓝本
    blueprint_config(app)

    return app

# 获取app对象，用于生产和测试
def create_app(envConfig_name='DevelopmentConfig'):
    '''
    封装创建方法
    :param config_name: 环境名:'DevelopmentConfig', 'ProductionConfig', 'TestingConfig'
    :return: app应用
    '''
    conf = get_config_object(envConfig_name)
    return create_app_by_config(conf)
