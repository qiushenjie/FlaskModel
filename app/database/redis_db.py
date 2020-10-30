from config import config  # config.py中包含了redis的一些信息，比如host, port, 数据库名称
from flask import current_app
import redis


class Redis(object):
    """
    redis数据库操作
    """

    @staticmethod
    def _get_r():
        # 当Redis类作为一个appAPI使用时，例如在redisdbOperationAPI.py中调用，会被注册进蓝本，因此可直接从current_app中获取配置信息
        # host = current_app.config['REDIS_HOST']
        # port=current_app.config['REDIS_PORT']
        # db=current_app.config['REDIS_DB']

        # 因为Redis类会在modelInferenceAPI直接使用，因此暂时不从current_app中获取配置信息，而是直接从config中获取
        host = config.redis_map['REDIS_HOST']
        port = config.redis_map['REDIS_PORT']
        db = config.redis_map['REDIS_DB']
        r = redis.StrictRedis(host, port, db)
        return r

    @classmethod
    def write(self, key, value, expire=None):
        """
        写入键值对
        """
        # 判断是否有过期时间，没有就设置默认值
        if expire:
            expire_in_seconds = expire
        else:
            # expire_in_seconds = current_app.config['REDIS_EXPIRE']
            expire_in_seconds = expire
        r = self._get_r()
        r.set(key, value, ex=expire_in_seconds)

    @classmethod
    def read(self, key):
        """
        读取键值对内容
        """
        r = self._get_r()
        value = r.get(key)
        return value.decode('utf-8') if value else value

    @classmethod
    def hset(self, name, key, value):
        """
    	写入hash表
    	"""
        r = self._get_r()
        r.hset(name, key, value)

    @classmethod
    def hmset(self, key, *value):
        """
        读取指定hash表的所有给定字段的值
        """
        r = self._get_r()
        value = r.hmset(key, *value)
        return value

    @classmethod
    def hget(self, name, key):
        """
        读取指定hash表的键值
        """
        r = self._get_r()
        value = r.hget(name, key)
        return value.decode('utf-8') if value else value

    @classmethod
    def hgetall(self, name):
        """
        获取指定hash表所有的值
    	"""
        r = self._get_r()
        return r.hgetall(name)

    @classmethod
    def delete(self, *names):
        """
        删除一个或者多个
        """
        r = self._get_r()
        r.delete(*names)

    @classmethod
    def hdel(self, name, key):
        """
		删除指定hash表的键值
        """
        r = self._get_r()
        r.hdel(name, key)

    @classmethod
    def expire(self, name, expire=None):
        """
        设置过期时间
        """
        if expire:
            expire_in_seconds = expire
        else:
            expire_in_seconds = current_app.config['REDIS_EXPIRE']
        r = self._get_r()
        r.expire(name, expire_in_seconds)