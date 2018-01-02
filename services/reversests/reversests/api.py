import os
import json
import datetime

from flask import Flask, request, make_response, abort
from flask_jwt_extended import JWTManager, create_access_token

from logger_client import log


SERVICE_TYPE = "reversests"
logger = log(SERVICE_TYPE).logger


app = Flask(__name__)


HOST = '0.0.0.0'



#####################################################################
# Web API
#####################################################################
def all_links():
    links = []
    for rule in app.url_map.iter_rules():
        links.append(str(rule))
    return links

@app.route("/", methods=['GET'])
def hello():
    return nice_json({"subresource_uris": all_links()})


@app.route('/login', methods=['POST'])
def login():
    if (not request.json or not 'username' in request.json):
        abort(400)
    username = request.json['username']
    # Identity can be any data that is json serializable
    access_token = create_access_token(identity=username)
    print "JWT issued for '%s'" % username

    return nice_json({'access_token': access_token}), 200


@app.route("/cert/pem", methods=['GET'])
def getTokenCert():
    return nice_json({'PEM': certMng.getCert()}), 200


@app.errorhandler(Exception)
def all_exception_handler(error):
    logger.error("Unhandled exception: %s" % error)
    return 'Error', 500


def nice_json(arg):
    """Form JSON responses."""
    response = make_response(json.dumps(arg, sort_keys = True, indent=4))
    response.headers['Content-type'] = "application/json"
    return response


class CertMng():
    """docstring for CertManager"""
    def __init__(self):
        self.sslConfigFile = 'openssl-service.cnf' # Basic SSL config.
        self.keyFile = 'servicekey.pem' # Private key
        self.certFile = 'servicecert.pem' # Certificate

        self.generate()

    def generate(self):
        """Generates a certificate."""
        if not os.path.exists(self.certFile) \
           and not os.path.exists(self.keyFile):
            if os.path.exists(self.sslConfigFile):
                info = "/C=NO/ST=Hordaland/L=Bergen/O=UiB/CN=UserAuthTokenService"
                cmd="openssl req -x509 -config %s -subj %s -newkey rsa:2048 -nodes -keyout %s -out %s" \
                   % (self.sslConfigFile, info, self.keyFile, self.certFile)
                os.system(cmd)
            else:
                logger.error("SSL configuration file not found")
        else:
            logger.warning("Certificate already exists")

    def remove(self):
        """Remove existent certificates."""
        filelist = [f for f in os.listdir('.') \
                    if f.endswith(('.pem', '.txt', '.attr', '.old', '.csr'))]
        for f in filelist:
            os.remove(os.path.join('.', f))

    def getKey(self):
        if os.path.isfile(self.keyFile):
            with open(self.keyFile, 'r') as f:
                return f.read()
        else:
            logger.error("SSL key not found")

    def getCert(self):
        if os.path.isfile(self.certFile):
            with open(self.certFile, 'r') as f:
                return f.read()
        else:
            logger.error("SSL certificate not found")


certMng = CertMng()

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

def main():
    if isDocker():
        FLASK_PORT = 80
    else:
        FLASK_PORT = 8081
    # Setup the Flask-JWT-Extended extension
    app.config['JWT_ALGORITHM'] = 'RS256'
    # Default expiration time is 15 minutes
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(seconds=60*10)
    app.config['JWT_PRIVATE_KEY'] = certMng.getKey()
    app.config['JWT_PUBLIC_KEY'] = certMng.getCert()
    jwt = JWTManager(app)
    # Order matters!
    #context = ('cacert.pem', 'cakey.pem')
    # Start Flask web server
    app.run(port=FLASK_PORT, debug=True, host=HOST)#, ssl_context=context)

if __name__ == "__main__":
    logger.info("UserAuthToken service starting NOW")
    main()
