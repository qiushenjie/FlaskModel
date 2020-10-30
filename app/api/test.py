from flask_restful import Resource


class test(Resource):

    def get(self):
        return {'message': 'ok'}, 200