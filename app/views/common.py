# -*- coding: utf-8 -*-
'''
Created on 2016-10-20

index, login, logout
@author: hustcc
'''

from app import app, github, __version__
from app.utils import ResponseUtil, RequestUtil, DateUtil
from werkzeug.utils import redirect
from flask.helpers import url_for, flash
from flask.globals import session
from app.database.model import User


@app.route('/', methods=['GET'])
def index():
    return ResponseUtil.render_template('index.html', __version__=__version__)


@app.route('/login', methods=['GET'])
def login():
    return github.authorize()


@github.access_token_getter
def token_getter():
    return session.get('oauth_token', None)


@app.route('/github/callback')
@github.authorized_handler
def github_authorized(oauth_token):
    if oauth_token is None:
        flash("Authorization failed.")
        return redirect(url_for('index'))

    session['oauth_token'] = oauth_token

    me = github.get('user')
    user_id = me['login']

    # is user exist
    user = User.query.get(user_id)

    if user is None:
        # not exist, add
        user = User(id=user_id)

    # update github user information
    user.last_login = DateUtil.now_datetime()
    user.name = me.get('name', user_id)
    user.location = me.get('location', '')
    user.avatar = me.get('avatar_url', '')

    user.save()

    RequestUtil.login_user(user.dict())

    return redirect(url_for('index'))


@app.route('/logout', methods=['GET'])
def logout():
    RequestUtil.logout()
    return redirect(url_for('index'))


from app.wraps.login_wrap import login_required

@app.route('/api/user/upgrade_demo', methods=['POST'])
@login_required()
def api_user_upgrade_demo():
    user_id = RequestUtil.get_login_user().get('id', '')
    user = User.query.get(user_id)
    if user:
        user.is_premium = True
        user.save()
        # Update session cache
        RequestUtil.login_user(user.dict())
        return ResponseUtil.standard_response(1, 'Upgrade Success')
    return ResponseUtil.standard_response(0, 'User not found')


@app.route('/login_demo', methods=['GET'])
def login_demo():
    user_id = 'DemoUser'
    user = User.query.get(user_id)
    if user is None:
        user = User(
            id=user_id,
            name="Demo Developer",
            avatar="https://github.com/identicons/demo.png",
            location="SaaS Cloud",
            is_premium=False
        )
        user.save()
    RequestUtil.login_user(user.dict())
    return redirect(url_for('index'))


import requests
from requests.auth import HTTPBasicAuth

def get_paypal_access_token():
    client_id = 'AYfhe3krOaVlJmuDlFdwsGz036zOQDtwlOImoHY48_DJQeUzF0z-aKdZixVlZVoDCLVr_UISowsU9uv3'
    secret = 'EHn7lPPCZlxVf2zYxaNFRjZF7KLU_e2Aw4kG4HQvzbNEZ0E05NWeOUixqL5yYhK9j8ek_GuvH77tz5mr'
    # In sandbox we use sandbox endpoint, but since user switched to Live, we use the Live endpoint api-m.paypal.com
    url = "https://api-m.paypal.com/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US"
    }
    data = {
        "grant_type": "client_credentials"
    }
    try:
        res = requests.post(url, headers=headers, data=data, auth=HTTPBasicAuth(client_id, secret), timeout=10)
        if res.status_code == 200:
            return res.json().get('access_token')
    except Exception as e:
        print("Error getting PayPal token:", e)
    return None

def verify_paypal_subscription(subscription_id):
    token = get_paypal_access_token()
    if not token:
        return False, "Failed to authenticate with PayPal API"
    
    url = f"https://api-m.paypal.com/v1/billing/subscriptions/{subscription_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            sub_data = res.json()
            plan_id = sub_data.get('plan_id', '')
            status = sub_data.get('status', '')
            expected_plan = 'P-8UF10924WA311035LNJLBBUQ'
            if status in ['ACTIVE', 'APPROVED'] and plan_id == expected_plan:
                return True, "Success"
            return False, f"Plan mismatch or inactive status: {status}"
    except Exception as e:
        print("Error verifying PayPal subscription:", e)
    return False, "Failed to verify payment with PayPal"

@app.route('/api/user/upgrade_paypal', methods=['POST'])
@login_required()
def api_user_upgrade_paypal():
    user_id = RequestUtil.get_login_user().get('id', '')
    subscription_id = RequestUtil.get_parameter('subscription_id', '')
    if not subscription_id:
        return ResponseUtil.standard_response(0, 'Missing subscription_id')
        
    user = User.query.get(user_id)
    if not user:
        return ResponseUtil.standard_response(0, 'User not found')
        
    # Securely verify with PayPal servers
    success, msg = verify_paypal_subscription(subscription_id)
    if success:
        user.is_premium = True
        user.save()
        RequestUtil.login_user(user.dict())
        return ResponseUtil.standard_response(1, 'Upgrade Success')
    else:
        return ResponseUtil.standard_response(0, f'PayPal Verification Failed: {msg}')
