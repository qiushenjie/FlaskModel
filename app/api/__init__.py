from .modelInferenceAPI import *

'''
注册 Flask 蓝图
每个业务模块有自己的路由、ORM 或蓝图等，这是业务自己的代码，必须与骨架解耦。
用一个特定的方法作为规范一是便于自定义的代码扩展，二是便于团队理解，不需要灵活的配置，这里约定大于配置
'''

# 蓝本 二维元组(蓝本(端口),'路由')
DEFAULT_BLUEPRINT = (
    (model, '/'),
)

# 注册函数(蓝本)
def blueprint_config(app):
    for blueprint, prefix in DEFAULT_BLUEPRINT:
        app.register_blueprint(blueprint, url_prefix=prefix)  # 这里DEFAULT_BLUEPRINT中只有一个蓝本，将app交给model这个蓝本管理