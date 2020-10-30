from app.api.celery_worker import *
from app.api.main import model
# 这里包含的主要是用来处理业务的逻辑, 以下函数为传递的各种参数类型与传递方式

@model.route("/inference/<SeriesInstanceNumberUID>/<start>/<end>")
def Inference(SeriesInstanceNumberUID, start, end):
    result = inference.delay(str(SeriesInstanceNumberUID), str(start), str(end))  # 调用异步方法并传参数
    return result.id


@model.route("/get_result/<result_id>")
def result_(result_id):
    result = get_result(result_id)
    return str(result)




# model = Blueprint('CTClassficationModelFlask', __name__)  # __name__代表主模块名或者包
#
# @model.route("/mul/<arg1>/<arg2>")
# def mul_(arg1, arg2):
#     result = mul.delay(int(arg1), int(arg2))  # 调用异步方法并传参数
#     return result.id
#
#
# @model.route("/get_result/<result_id>")
# def result_(result_id):
#     result = get_result(result_id)
#     return str(result)