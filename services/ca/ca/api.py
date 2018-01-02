import os
import json
import datetime

from flask import Flask, request, make_response

from logger_client import log


SERVICE_TYPE = "certificate_authority"
logger = log(SERVICE_TYPE).logger


app = Flask(__name__)


HOST = '0.0.0.0'


TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'



def validateTimeStr(timeStr):
    time = None
    try:
        time = datetime.datetime.strptime(timeStr, TIME_FORMAT)
    except ValueError as e:
        print "Unexpected data format: %s." % e
        time = dateutil.parser.parse(timeStr)
    return time




#####################################################################
# Web API
#####################################################################
def all_links():
    links = []
    for rule in app.url_map.iter_rules():
        links.append(str(rule))
    return links

def nice_json(arg):
    """Form JSON responses."""
    response = make_response(json.dumps(arg, sort_keys = True, indent=4))
    response.headers['Content-type'] = "application/json"
    return response


@app.route("/", methods=['GET'])
def hello():
    return nice_json({"subresource_uris": all_links()})


@app.errorhandler(Exception)
def all_exception_handler(error):
    logger.error("Unhandled exception: %s" % error)
    return 'Error', 500


@app.route("/ca/init", methods=['GET'])   
def genRootCert():
    """
    Setup the self-hosted CA. 

    Generates a root certificate (public/private key pair) from a given
    configuration file. Configuration parameters should be reviewed beforehand.
    More information on certificate signing can be found here:
    https://stackoverflow.com/questions/21297139

    openssl-ca.cnf --- a basic CA configuration, input file;
    cacert.pem     --- a CA certificate, output file;
    cakey.pem      --- a CA private key, output file.
    
    """

    # Create a database index file for the CA
    open('index.txt', 'a+').close()
    # Initialize a current serial number file for the CA
    if not os.path.exists('serial.txt'):
        with open('serial.txt', 'w') as f: 
            f.write('01')
    # Generate a new key pair only if it does not exist yet
    if not os.path.exists('cacert.pem') and not os.path.exists('cakey.pem'):
        if os.path.exists('openssl-ca.cnf'):
            os.system("openssl req -x509 -config openssl-ca.cnf -newkey rsa:4096 -sha256 -nodes -out cacert.pem -outform PEM")
        else:
            print "OpenSSL CA configuration file not found"
    else:
        print "cacert.pem and/or cakey.pem already exist"


@app.route("/ca/reset", methods=['GET'])
def resetCA():
    """Delete the existent CA"""

    # Get all files of a specific type in the current directory
    filelist = [ f for f in os.listdir('.') if f.endswith(('.pem', '.txt', '.attr', '.old', '.csr'))]
    for f in filelist:
        os.remove(os.path.join('.', f))


@app.route("/ca/sign", methods=['POST'])
def genServiceCertFromCSR():
    if not request.json or not 'token' in request.json or \
                           not 'serviceType' in request.json or \
                           not 'csr' in request.json:
        abort(400)

    token = request.json['token']
    csr = request.json['csr']
    if not validateToken(token):
        abort(401)

    if not validateCSR(csr):
        abort(400)

    fileId = saveToFileCSR(csr)
    sign(fileId)
    with open(fileId+'.pem','r') as f:
        pemData = f.read()
   
    return nice_json({"PEM": pemData}), 200


def validateToken(token):
    return True


def validateCSR(csr):
    return True


def saveToFileCSR(csr):
    """Save CSR received from a service"""
    fileId = datetime.datetime.now().strftime(TIME_FORMAT)
    with open(fileId+'.csr','w') as f:
        f.write(csr)
    return fileId


def sign(fileId='servicecert'):
    """
    Create a service certificate.

    Sign service's certificate with the root certificate.
    openssl-ca.cnf --- a basic CA configuration, input file;
    servicecert.pem --- a service certificate, output file.
    """
    if os.path.exists('openssl-ca.cnf'):
        os.system("openssl ca -batch -config openssl-ca.cnf -policy signing_policy -extensions signing_req -out %s.pem -infiles %s.csr" % (fileId,fileId))
    else:
        print "OpenSSL CA configuration file not found"


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
        FLASK_PORT = 8080
    # Setup the self-hosted CA
    genRootCert()
    # Order matters!
    context = ('cacert.pem', 'cakey.pem')
    # Start Flask web server
    app.run(port=FLASK_PORT, debug=True, host=HOST, ssl_context=context)

if __name__ == "__main__":
    logger.info("CA service starting NOW")
    main()
