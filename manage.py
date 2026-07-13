# -*- coding: utf-8 -*-
'''
Created on 2016-11-23

@author: hustcc
'''

import subprocess
import sys
import os
from app import SQLAlchemyDB as db, app, __version__

# Expose app for gunicorn (manage:app)
app = app

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print("Usage: python manage.py [createdb|celery|version]")
        sys.exit(1)
    
    cmd = args[0]
    if cmd == 'createdb':
        # Drop first option if passed
        drop_first = '--drop' in args or 'drop_first' in args
        with app.app_context():
            if drop_first:
                db.drop_all()
            db.create_all()
        print('OK: database is initialed.')
    elif cmd == 'celery':
        # Replicate Celery worker startup command
        # e.g., celery --loglevel=info --logfile=/data/celery.log --pidfile=/run/celery.pid --detach -P eventlet
        celery_args = args[1:]
        # Remove --detach option if celery >= 5.0.0 because it was removed in celery v5.0
        # Instead, celery v5 uses db/redis background management or systemd/supervisord.
        # But to be safe, let's keep compatibility by stripping --detach if it causes issues, 
        # or we just run the celery worker command directly.
        # In python 3 / Celery 5, --detach is deprecated. We can handle it or pass it.
        # Celery 5.0+ removed the --detach option. We should filter it out.
        filtered_args = []
        detach_mode = False
        for arg in celery_args:
            if arg == '--detach':
                detach_mode = True
            else:
                filtered_args.append(arg)
        
        # Build celery command: celery -A app.celeryInstance worker ...
        run_cmd = ['celery', '-A', 'app.celeryInstance', 'worker'] + filtered_args
        if detach_mode:
            # If detach is requested, we can use subprocess.Popen instead of blocking call
            print("Running Celery worker in background (detached)...")
            subprocess.Popen(run_cmd)
        else:
            ret = subprocess.call(run_cmd)
            sys.exit(ret)
    elif cmd == 'version':
        print(__version__)
    else:
        print("Unknown command: %s" % cmd)
        sys.exit(1)
