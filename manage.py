from flask_script import Manager
from flask_migrate import MigrateCommand
from app import create_app
import os

# 环境 此处直接默认为生产环境
# config_name = os.environ.get('CONFIG_NAME') or 'default'
# 创建app

app = create_app('ProductionConfig')

# # 关键点，往celery推入flask信息，使得celery能使用flask上下文。本项目在/app/api/celery_worker.py中实现了一个with_app_context()修饰器来实现这个功能，因此，这两种方法二选一都可
# app.app_context().push()

# 创建flask脚本管理工具对象， 使终端可以使用指令来操作程序
manager = Manager(app)

# # 创建数据库迁移工具对象，这里暂时用不到
# Migrate(app, db)

# # 向manager对象中添加数据库的操作命令
# # 第一个参数是给这条命令取的名字叫什么,关于数据库的我们通常叫db
# # 第二个参数就是具体的命令
# # 这里暂时用不到
# manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
