import logging
from logging.config import dictConfig

import coloredlogs

# 生成日志
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': "[%(asctime)s %(filename)s %(funcName)s %(lineno)d] %(levelname)s %(message)s",
    }},
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',
            'formatter': 'default'
        },
        'file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'INFO',
            'formatter': 'default',
            'filename': 'log/flask.log',
            'encoding': 'utf8',
            'when': 'midnight',
            # 'maxBytes': 8 * 1024 * 1000,
            'backupCount': 30,
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file'],
    }
})

logging.getLogger('apscheduler').setLevel('WARNING')
logging.getLogger('apscheduler').propagate = False

root_logger = logging.getLogger("root")

coloredlogs.install(fmt="[%(asctime)s %(filename)s %(funcName)s %(lineno)d] %(levelname)s %(message)s",
                    level='INFO', logger=root_logger)
