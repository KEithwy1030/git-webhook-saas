# -*- coding: utf-8 -*-
'''
Created on 2016-10-20

@author: hustcc
'''
from app.wraps.login_wrap import login_required
from app import app
from app.utils import ResponseUtil, RequestUtil, AuthUtil
from app.database.model import History, User


# get history list
@app.route('/api/history/list', methods=['GET'])
@login_required()
def api_history_list():
    # login user
    user_id = RequestUtil.get_login_user().get('id', '')

    webhook_id = RequestUtil.get_parameter('webhook_id', '')

    if not AuthUtil.has_readonly_auth(user_id, webhook_id):
        return ResponseUtil.standard_response(0, 'Permission deny!')

    page = RequestUtil.get_parameter('page', '1')
    try:
        page = int(page)
        if page < 1:
            page = 1
    except:
        page = 1

    page_size = 25
    paginations = History.query\
        .filter_by(webhook_id=webhook_id)\
        .order_by(History.id.desc())\
        .paginate(page, page_size, error_out=False)

    histories = [history.dict() for history in paginations.items]

    data = {
        'histories': histories,
        'has_prev': paginations.has_prev,
        'has_next': paginations.has_next,
        'page': paginations.page
    }

    return ResponseUtil.standard_response(1, data)


from app.utils import SshUtil, JsonUtil
from app.tasks import tasks

@app.route('/api/history/autofix', methods=['POST'])
@login_required()
def api_history_autofix():
    user_id = RequestUtil.get_login_user().get('id', '')
    user = User.query.get(user_id)
    if not user or not user.is_premium:
        return ResponseUtil.standard_response(0, 'AI Auto-Fix is only available for Premium subscribers.')
    history_id = RequestUtil.get_parameter('history_id', '')
    
    history = History.query.get(history_id)
    if not history:
        return ResponseUtil.standard_response(0, 'History not found')
        
    webhook = history.webhook
    if not webhook or webhook.user_id != user_id:
        return ResponseUtil.standard_response(0, 'Permission deny')
        
    if not history.ai_fix_suggestion:
        return ResponseUtil.standard_response(0, 'No AI fix suggestion available')
        
    server = webhook.server
    if not server:
        return ResponseUtil.standard_response(0, 'Server not found')
        
    try:
        # Run AI Auto-Fix command on remote server via SSH
        success, log = SshUtil.do_ssh_cmd(
            server.ip, server.port, server.account, server.pkey, 
            history.ai_fix_suggestion, timeout=60
        )
        if not success:
            return ResponseUtil.standard_response(0, 'AI Auto-Fix execution failed: ' + str(log))
            
        # Re-trigger the original Webhook deployment
        tasks.do_task.delay(webhook.id, JsonUtil.json_2_object(history.data), user_id)
        return ResponseUtil.standard_response(1, 'AI Auto-Fix applied successfully! Triggering redeployment...')
    except Exception as e:
        return ResponseUtil.standard_response(0, 'Server connection error during AI Auto-Fix: ' + str(e))
