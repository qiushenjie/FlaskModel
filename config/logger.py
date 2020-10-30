from logging.config import dictConfig

'''
典型的Python日志配置方法，把可变的部分定义为参数（日志文件、级别等），定义了两个日志处理器（文件和控制台），使用时只需要调用这个方法即可
'''
def config_logger(enable_console_handler=True, enable_file_handler=True, log_file='app.log', log_level='ERROR',
                  log_file_max_bytes=5000000, log_file_max_count=5):
    # 定义输出到控制台的日志处理器
    console_handler = {
        'class': 'logging.StreamHandler',
        'formatter': 'default',
        'level': log_level,
        'stream': 'ext://flask.logging.wsgi_errors_stream'
    }
    # 定义输出到文件的日志处理器
    file_handler = {
        'class': 'logging.handlers.RotatingFileHandler',
        'formatter': 'detail',
        'filename': log_file,
        'level': log_level,
        'maxBytes': log_file_max_bytes,
        'backupCount': log_file_max_count
    }
    # 定义日志输出格式
    default_formatter = {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    }
    detail_formatter = {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    }
    handlers = []
    if enable_console_handler:
        handlers.append('console')
    if enable_file_handler:
        handlers.append('file')
    d = {
        'version': 1,
        'formatters': {
            'default': default_formatter,
            'detail': detail_formatter
        },
        'handlers': {
            'console': console_handler,
            'file': file_handler
        },
        'root': {
            'level': log_level,
            'handlers': handlers
        }
    }
    dictConfig(d)