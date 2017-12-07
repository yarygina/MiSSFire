#import multiprocessing
from os import getenv


# Server Socket
bind = "localhost:8888"


# Worker Processes
# The number of worker processes for handling requests.
workers = 1 #multiprocessing.cpu_count()
# Run each worker with the specified number of threads.
threads = 1

# The type of workers to use. The default class is sync.
#worker_class = 'gevent'
# The maximum number of simultaneous clients.
# Affects the Eventlet and Gevent worker types.
#worker_connections = 1#30


# Security
if getenv('MTLS', False) == 'True':
	print "Gunicorn SSL enabled"
	# SSL key file
	keyfile = 'servicekey.key'
	# SSL certificate file
	certfile = 'servicecert.pem'
	# Whether client certificate is required (see stdlib ssl module)
	cert_reqs = 1
	# CA certificates file
	ca_certs = 'cacert.pem'
else:
	print "Gunicorn SSL disabled"
# The maximum size of HTTP request line in bytes.
# Request-line consists of the HTTP method, URI, and protocol version.
# Value is a number from 0 (unlimited) to 8190.
limit_request_line = 1024
# Limit the number of HTTP headers fields in a request.
# Default = 100, cannot be larger than 32768.
limit_request_fields = 10
# Limit the allowed size of an HTTP request header field.
limit_request_field_size = 2048


# Debugging
# Restart workers when code changes.
reload = False

# Logging
#loglevel = warning


