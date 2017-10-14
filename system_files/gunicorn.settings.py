accesslog = "log/access.log"
errorlog = "log/error.log"
daemon = False
pidfile = "pids/gunicorn.pid"
bind = "127.0.0.1:5001"
workers = 1
