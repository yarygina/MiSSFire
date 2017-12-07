import sys
from os import getenv
import logging

# Disable console messages from Flask server
logging.getLogger('werkzeug').setLevel(logging.ERROR)

class log:
    def __init__(self, service_name,):
        self.service_name = service_name
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        # Create console handler
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(filename)s - %(funcName)s - %(lineno)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # Install service-wide exception handler
        #sys.excepthook = self.my_handler

    # Handle all uncaught exceptions
    def my_handler(self, type, value, tb):
        self.logger.exception("Uncaught exception:", exc_info=(type, value, tb))

# Resolve the environment variables if any
def getEnvVar(varName, defaultVal):
    """Translate string variables into boolean variables."""
    varVal = getenv(varName, defaultVal)
    if varVal == 'True': varVal = True
    elif varVal == 'False': varVal = False
    return varVal

def isDocker():
    """Determines if we are running inside Docker.

    The process's PID inside the container differs from it's PID on the host
    (a non-container system).
    """
    procList = ""
    if os.path.isfile('/proc/1/cgroup'):
        with open('/proc/1/cgroup', 'rt') as f:
            procList = f.read()
    procList = procList.decode('utf-8').lower()
    checks = [
        'docker' in procList,
        '/lxc/' in procList,
        procList and procList.split()[0] not in ('systemd', 'init',),
        os.path.exists('/.dockerenv'),
        os.path.exists('/.dockerinit'),
        os.getenv('container', None) is not None
    ]
    return any(checks)
