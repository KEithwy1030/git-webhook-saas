# -*- coding: utf-8 -*-
'''
Created on 2016-10-20

@author: hustcc
'''
import sys
# reload(sys)  # noqa
# sys.setdefaultencoding('utf8')

import datetime  # noqa
from app import celeryInstance  # noqa
from app.database.model import History, WebHook  # noqa
from app.utils import SshUtil, JsonUtil, HookDataParse  # noqa
from app.utils.AiUtil import analyze_error_log


# webhook / data all is JSON dict.
@celeryInstance.task
def do_webhook_shell(webhook_id, history_id, data, user_id=None):
    webhook = WebHook.query.get(webhook_id)
    history = History.query.get(history_id)
    # server information
    ip = webhook.server.ip
    port = webhook.server.port
    account = webhook.server.account
    pkey = webhook.server.pkey

    # do what
    shell = webhook.shell

    # start to process, add history into database
    status = '2'
    history.push_user = '%s <%s>' % (
        HookDataParse.get_push_name(data) or user_id,
        HookDataParse.get_push_email(data) or 'Web GUI'
    )
    history.updateStatus(status)
    webhook.updateStatus(status)
    try:
        success, log = SshUtil.do_ssh_cmd(
            ip, port, account, pkey, shell, JsonUtil.object_2_json(data))
        status = '3'  # error
        if success:
            status = '4'  # success
    except Exception as e:
        success, log = False, 'Server SSH error: ' + str(e)
        status = '5'  # except

    # ProgrammingError: You must not use 8-bit bytestrings unless you use a
    # text_factory
    log = str(log)  # noqa

    history.shell_log = log

    # AI Root Cause Analysis for failures
    if not success:
        from app.utils.RateLimitUtil import check_and_incr_ai_rate_limit
        from app.database.model import User
        from app import app
        
        owner = User.query.get(webhook.user_id)
        is_premium = owner.is_premium if owner else False
        
        allowed = False
        if is_premium:
            allowed, _msg = check_and_incr_ai_rate_limit(webhook.user_id)
            
        if is_premium and allowed:
            ai_res = analyze_error_log(log)
        else:
            # Fallback to local regex rule-based engine (zero-cost) by temporarily masking API Key
            old_key = app.config.get('GEMINI_API_KEY')
            app.config['GEMINI_API_KEY'] = ''
            ai_res = analyze_error_log(log)
            app.config['GEMINI_API_KEY'] = old_key
            
        history.ai_analysis = ai_res['analysis']
        history.ai_fix_suggestion = ai_res['fix_suggestion']
    else:
        history.ai_analysis = None
        history.ai_fix_suggestion = None

    history.updateStatus(status)
    webhook.updateStatus(status)
