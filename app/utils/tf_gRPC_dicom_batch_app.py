'''
开启tensorflow serving
命令行输入
docker run --runtime=nvidia -p 8500:8500 \
  --mount type=bind,source=/home/ubuntu/Docker/taurusApp/tf_serving_model,target=/models \
  -t --entrypoint=tensorflow_model_server tensorflow/serving:1.12.0-gpu \
  --port=8500 --per_process_gpu_memory_fraction=0.1 \
  --enable_batching=true --model_name=ct_classification \
  --model_base_path=/models/ct_model &  # 进一步指定到容器某个模型文件夹

提供REST（restful API）和gRPC两种形式的接口调用
docker run --runtime=nvidia -p 8500:8500 \
  --mount type=bind,source=/home/ubuntu/Docker/taurusApp/tf_serving_model,target=/models \
  -t tensorflow/serving:1.12.0-gpu \
  --per_process_gpu_memory_fraction=0.1 \
  --enable_batching=true --model_name=ct_classification  \
  --model_base_path=/models/ct_model &

'''

from __future__ import print_function
from grpc.beta import implementations
import tensorflow as tf
from tensorflow_serving.apis import prediction_service_pb2
from tensorflow_serving.apis import predict_pb2
import warnings

from app.utils import Search
from app.utils import groupSlices, Series
from flask import Flask, request
import numpy as np
import flask
import json
import cv2

def dicom2img(dicom_path, img_size=(512, 512)):
    slice_series = groupSlices(dicom_path)
    for (k, v) in slice_series.items():
        slice_series = Series.sortByInstanceNumber(v.series)
        images = []
        slices_path = []
        for i, slice in enumerate(slice_series):
            slice.array2D = Series.unifyPixelValue(slice.array2D) * 255.0
            img = slice.array2D.copy()
            img = cv2.resize(img, dsize=img_size)
            images.append(img)
            slices_path.append(slice.instanceNumber)

        images = np.array(images)
        return images, slices_path

class batch_generator:
    def __init__(self, total):
        self.total = total
        self.range = [i for i in range(total)]
        self.index = 0

    def get(self, batchsize):
        r_n = self.range[self.index: self.index + batchsize]
        self.index = self.index + batchsize

        return r_n

def postp(series_matrix):
    s = Search(series_matrix)
    path = np.array(s.searchPath())
    # path_ = path_.reshape(-1, 1)
    direction = s.direction
    return path, direction

def request_server(series_instance_uid_path, start, end, server_url):
    host, port = server_url.split(':')
    batch_size = 1
    n_class = 12
    start, end = int(start), int(end)
    # 建立存根，使用IP地址和端口号搭建连接
    channel = implementations.insecure_channel(host, int(port))
    stub = prediction_service_pb2.beta_create_PredictionService_stub(channel)
    # Send request

    # See prediction_service.proto for gRPC request/response details.
    dicom_imgs, dicom_slices_path = dicom2img(series_instance_uid_path)
    dicom_imgs, dicom_slices_path = dicom_imgs[start: end], dicom_slices_path[start: end]
    BatchGenerator = batch_generator(len(dicom_imgs))

    # 建立一个请求
    request = predict_pb2.PredictRequest()
    request.model_spec.name = 'ct_classification' # 这个name跟tensorflow_model_server  --model_name="ct_classification" 对应
    request.model_spec.signature_name = 'predict_images' # 这个signature_name  跟signature_def_map 对应

    res = []
    while BatchGenerator.index < len(dicom_imgs):
        batch_imgs_index = BatchGenerator.get(batchsize=batch_size)
        batch_data = []
        for index in batch_imgs_index:
            image = dicom_imgs[index]
            warnings.simplefilter('ignore', ResourceWarning)
            data = np.array(image).astype(np.float32)
            data = data[..., np.newaxis]
            batch_data.append(data)
        batch_data = np.array(batch_data)

        request.inputs['dicom_image'].CopyFrom(  # signature中的inputs={'dicom_image': model.input},是你导出模型时设置的输入名称
            tf.contrib.util.make_tensor_proto(batch_data, shape=[batch_size, 512, 512, 1])) # shape跟 keras的model.input类型对应
        result = stub.Predict(request, 3.0)  # 10 secs timeout
        scores = np.asarray(result.outputs["scores"].float_val)
        a = scores
        res.extend(list(scores))
    series_res = np.array(res).reshape((-1, n_class))
    res, direction = postp(series_res)
    post_res_dict = {}
    res_dict = {}
    if direction < 0:
        dicom_slices_path = dicom_slices_path[::-1]
        res = res[::-1]
        series_res = series_res[::-1]
    for (name, label) in zip(dicom_slices_path, res):
        post_res_dict[name] = label.tolist()
    # post_res_dict = json.dumps(post_res_dict, sort_keys=False, indent=4, separators=(',', ':'))

    for (name, label) in zip(dicom_slices_path, series_res):
        res_dict[name] = str(np.argmax(label))
    # res_dict = json.dumps(res_dict, sort_keys=False, indent=4, separators=(',', ':'))

    return post_res_dict, res_dict

# app = Flask(__name__)
# @app.route('/inference', methods=['POST'])
def predict():
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
    return flask.jsonify(data)

# if __name__ == '__main__':
    # app.run()
    # series_res = tf.app.run()
    # cv2.waitKey(0)
    # print(a)
    # series_instance_uid_path = '/home/ubuntu/qiushenjie/taurus/data/dataset256/images/guoyiqing/3'
    # server_url = 'localhost:8500'
    # series_res = request_server(series_instance_uid_path, server_url)
    # path_ = series_res.argmax(axis=-1)
    # print(path_)
    # print(postp(series_res))