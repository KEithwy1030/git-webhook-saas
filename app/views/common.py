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
