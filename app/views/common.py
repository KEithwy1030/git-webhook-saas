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


@app.route('/api/github/repos', methods=['GET'])
@login_required()
def api_github_repos():
    try:
        repos_data = github.get('user/repos', params={'per_page': 100, 'sort': 'updated'})
        repos = []
        for repo in repos_data:
            repos.append({
                'name': repo.get('full_name'),
                'clone_url': repo.get('clone_url'),
                'default_branch': repo.get('default_branch', 'master')
            })
        return ResponseUtil.standard_response(1, repos)
    except Exception as e:
        return ResponseUtil.standard_response(0, 'Failed to fetch GitHub repos: ' + str(e))


@app.route('/api/github/detect_project', methods=['POST'])
@login_required()
def api_github_detect_project():
    repo_name = RequestUtil.get_parameter('repo_name', '')
    if not repo_name:
        return ResponseUtil.standard_response(0, 'Missing repo_name')
        
    try:
        contents = github.get(f'repos/{repo_name}/contents')
        files = [f.get('name', '') for f in contents]
        
        shell_script = "# AI Generated Deployment Shell\n"
        project_type = "Generic"
        
        if 'docker-compose.yml' in files:
            project_type = "Docker Compose"
            shell_script += "docker compose pull\ndocker compose up -d --build\necho 'Deploy success!'\n"
        elif 'package.json' in files:
            project_type = "Node.js"
            shell_script += "npm install --registry=https://registry.npmmirror.com\nnpm run build || true\npm run start -d || pm2 restart all || true\n"
        elif 'requirements.txt' in files:
            project_type = "Python"
            shell_script += "pip install -r requirements.txt\npython manage.py db upgrade || true\nkill -9 $(lsof -t -i:8000) || true\nnohup gunicorn app:app -b 0.0.0.0:8000 --detach &\n"
        else:
            shell_script += "# Pull latest code\ngit pull\necho 'Deploy finished!'\n"
            
        return ResponseUtil.standard_response(1, {
            'project_type': project_type,
            'shell_script': shell_script
        })
    except Exception as e:
        return ResponseUtil.standard_response(0, 'AI failed to analyze repo: ' + str(e))
