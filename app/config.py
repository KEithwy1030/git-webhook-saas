# -*- coding: utf-8 -*-
'''
Created on 2016-10-20

@author: hustcc
'''

# for sqlite
# DATABASE_URI = 'sqlite:///git_webhook.db'
# for mysql
DATABASE_URI = 'mysql+pymysql://root:root@mysql/git_webhook'

CELERY_BROKER_URL = 'redis://:@redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://:@redis:6379/0'

SOCKET_MESSAGE_QUEUE = 'redis://:@redis:6379/0'

GITHUB_CLIENT_ID = 'Ov23liSL70kGGzjUbWPW'
GITHUB_CLIENT_SECRET = '91b5843211ec4d3505d46902fed8b3bd78f62411'
