import sys
import logging

# Disable console messages from Flask server
logging.getLogger('werkzeug').setLevel(logging.ERROR)

class log:
    def __init__(self, service_name,):
        self.service_name = service_name
        self.logger = logging.getLogger()

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


