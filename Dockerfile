FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    make \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /code

CMD mkdir -p /data && \
    python manage.py celery --loglevel=info --logfile=/data/celery.log --pidfile=/run/celery.pid --detach -P gevent && \
    gunicorn -b 0.0.0.0:80 -k gevent -w 1 --log-file=/data/gunicorn.log manage:app
