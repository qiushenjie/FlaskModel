from app.database.redis_db import Redis
from app.api.main import model

@model.route('/testRedisWrite', methods=['GET'])
def test_redis_write():
	"""
	测试redis
	"""
	Redis.write("test_key","test_value",60)
	return "ok"

@model.route('/testRedisRead', methods=['GET'])
def test_redis_read():
	"""
	测试redis
	"""
	data = Redis.read("test_key")
	return data