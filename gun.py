import multiprocessing

# 由于IO操作非常耗时，程序经常会处于等待状态
# 比如请求多个网页有时候需要等待，gevent可以自动切换协程
# 协程就是协同工作的程序，不是进程也不是线程，理解成不带返回值的函数调用， python中的yield和第三方库greenlet，都可以实现协程
# 遇到阻塞自动切换协程，程序启动时执行monkey.patch_all()解决
# 实现异步并发
import gevent.monkey
gevent.monkey.patch_all()


# gunicorn配置参数

debug = True
loglevel = 'deubg'
bind = '127.0.0.1:5000'
# bind = '0.0.0.0:8000'
pidfile = 'logs/gunicorn.pid'
logfile = 'logs/debug.log'

#启动的进程数
workers = multiprocessing.cpu_count() * 2 + 1
# workers = multiprocessing.cpu_count()
worker_class = 'gunicorn.workers.ggevent.GeventWorker'  # 工作进程类型，gevent模式来支持并发

x_forwarded_for_header = 'X-FORWARDED-FOR'
