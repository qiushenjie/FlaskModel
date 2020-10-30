from flask import Blueprint
from app.utils.tf_gRPC_dicom_batch_app import request_server
from flask import request, jsonify

# 这里包含的主要是用来处理业务的逻辑, 以下函数为传递的各种参数类型与传递方式

# 创建视图对象
main = Blueprint('/', __name__)  # __name__代表主模块名或者包

@main.route('/InferenceResult/<SeriesInstanceNumberUID>', methods=['GET', 'POST'])  # <>中为传递给路由的参数
# @main.route('/InferenceResult', methods=['GET', 'POST'])
def predict(SeriesInstanceNumberUID):
    server_url = 'localhost:8500'
    data = {'success': False}
    if request.form.get('image_path'):
        image_path = request.form['image_path']
        start = request.form['start']
        end = request.form['end']
        data['predictions'] = []
        data['post_predictions'] = []
        post_res, res = request_server(image_path, start, end, server_url)
        data['predictions'].append(res)
        data['post_predictions'].append(post_res)
        data['success'] = True
    return jsonify(data)


@main.route('/TaskResponse/<task_id>', methods=['GET', 'POST'])
def taskResponse(task_id):
    # status = request.form.get(argument['arg1'])
    status = str(task_id)
    return jsonify({'status': status})

