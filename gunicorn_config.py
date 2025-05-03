import multiprocessing

# Bind to this socket
bind = "127.0.0.1:8001"

# Number of workers
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class
worker_class = "gthread"
threads = 2

# Logging
errorlog = "logs/gunicorn-error.log"
accesslog = "logs/gunicorn-access.log"
loglevel = "info"

# Timeout
timeout = 30

# Reload on code changes (set to False in production)
reload = False

# Process name
proc_name = "koshimart_gunicorn"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190 