import os

'''
使用 BaseConfig 作为配置基类，存放所有共用的配置，而不同的环境使用不同的配置子类，子类只需要修改特定的值就可以，便于查看
如果配置的值需要在运行是注入（如数据库连接等），则可以使用环境变量的方式（如下面的 SECRET_KEY），使用 or 提供了没有环境变量的默认值
'''
class BaseConfig:
    """
    配置基类，用于存放共用的配置
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(16)
    DEBUG = False
    TESTING = False


class ProductionConfig(BaseConfig):
    """
    生产环境配置类，用于存放生产环境的配置
    """
    @staticmethod
    def init_app(app):
        pass

    pass

class DevelopmentConfig(BaseConfig):
    DEBUG = True

    @staticmethod
    def init_app(app):
        pass

    pass

class TestingConfig(BaseConfig):
    """
    测试环境配置类，用于存放开发环境的配置
    """
    DEBUG = True
    TESTING = True

    @staticmethod
    def init_app(app):
        pass
    pass

config_map = {
    'DevelopmentConfig': DevelopmentConfig,
    'ProductionConfig': ProductionConfig,
    'TestingConfig': TestingConfig
}


# sql数据库访问参数
USERNAME = 'root'  # 用户名
PASSWORD = '123' # 密码
HOST = '127.0.0.1'  # 数据库地址
PORT = '3306'  # 端口
DATABASE = 'test'  # 数据库名
database_url ='mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8'.format(
    USERNAME, PASSWORD, HOST, PORT, DATABASE)

mysql_map = {
    'SQLALCHEMY_DATABASE_URI': database_url,
    'SQLALCHEMY_COMMIT_ON_TEARDOWN': False
}

# redis数据库访问参数
redis_map = {
    'REDIS_HOST': '127.0.0.1',  # redis数据库地址
    'REDIS_PORT': 6379,  # redis 端口号
    'REDIS_DB': 1,  # 数据库名, 只能是以数字命名，0表示数据库0
    'REDIS_EXPIRE': None  # redis 过期时间
}

# 数据路径
root = '/home/ubuntu/qiushenjie/Taurus/data/test_dicom/'