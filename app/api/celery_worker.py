from app.utils.tf_gRPC_dicom_batch_app import request_server
from app.database.redis_db import Redis
from celery import Celery
from config import config
import functools
import os

CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'  # 当改成'redis://127.0.0.1:6379/1'后，表示连接的是redis数据库1原先在'redis://127.0.0.1:6379/0'路由中数据库的数据就无法访问，直到重启服务切回'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'

# broker redis的消息中间件, backend 存储任务结果
CLASSMODEL = Celery("FlaskModel",
                    broker=CELERY_BROKER_URL,
                    backend=CELERY_RESULT_BACKEND,
                    CELERY_TASK_SERIALIZER='json',
                    )

def with_app_context(task):
    memo = {'app': None}

    @functools.wraps(task)
    def _wrapper(*args, **kwargs):
        if not memo['app']:
            from app import create_app

            app = create_app()
            memo['app'] = app
        else:
            app = memo['app']

        # 把 task 放到 application context 环境中运行
        with app.app_context():
            return task(*args, **kwargs)

    return _wrapper

@CLASSMODEL.task  # 这里写了一个异步方法，等待被调用
@with_app_context
def inference(SeriesInstanceNumberUID, start, end):
    # sleep(10)
    server_url = 'localhost:8500'
    root = config.root
    image_path = os.path.join(root, SeriesInstanceNumberUID)
    data = {'success':False}
    try:
        post_res, res = request_server(image_path, start, end, server_url)
        data['predictions'] = res
        data['post_predictions'] = post_res
        data['success'] = True
        for k, v in res.items():
            data['k'] = v
            key = str(SeriesInstanceNumberUID) + '_' + str(k)
            value = str(v)
            print(key, value)
            Redis.write(key, value)
    except:
        pass
    return data

def get_result(task_id):  # 通过任务id可以获取该任务的结果
    result = CLASSMODEL.AsyncResult(task_id)
    return result.result



