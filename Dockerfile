FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY . .
CMD ["gunicorn","-b", "0.0.0.0:8000","--workers", "3","--threads", "2","--timeout", "60","--access-logfile", "-","--error-logfile", "-","--log-level", "info","--capture-output","--access-logformat", "%(h)s %(l)s %(u)s %(t)s \"%(r)s\" %(s)s %(b)s \"%(f)s\" \"%(a)s\"","app:create_app()"]