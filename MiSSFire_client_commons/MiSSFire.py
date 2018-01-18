import os
import ssl
import uuid
import time
from functools import wraps
from socket import error as socket_error

import jwt
import requests
from flask import request, abort

from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend

from general import log, getEnvVar, isDocker


serviceType = os.path.basename(os.getcwd())
logger = log(serviceType).logger
DEBUG = getEnvVar('SERVICE_DEBUG', False)

if isDocker():
    CA_HOSTNAME = "ca"
    CA_PORT = 80
    TOKEN_HOSTNAME = "reversests"
    TOKEN_PORT = 80
else:
    CA_HOSTNAME = '0.0.0.0'
    CA_PORT = 8080
    TOKEN_HOSTNAME = '0.0.0.0'
    TOKEN_PORT = 8083

CA_URL = 'https://%s:%s/' % (CA_HOSTNAME, CA_PORT)
TOKEN_URL = 'http://%s:%s/' % (TOKEN_HOSTNAME, TOKEN_PORT)



class ServiceCert():
    """Management of the service certificate.

    How to use MTLS with Requests module:
    http://docs.python-requests.org/en/latest/user/advanced/#ssl-cert-verification
    How to use MTLS in Flask:
    https://stackoverflow.com/questions/28579142/attributeerror-context-object-has-no-attribute-wrap-socket#28590266
    """
    def __init__(self, logger, serviceType='notype', debug=False):
        self.logger = logger
        self.serviceType = serviceType
        self.debug = debug
        self.sslConfigFile = 'openssl-service.cnf' # Basic service config.
        self.serviceKeyFile = 'servicekey.key' # Private key
        self.serviceCSRFile = 'servicecert.csr' # Service certificate request
        self.serviceCertFile = 'servicecert.pem' # Service certificate
        self.caCert = 'cacert.pem' # CA certificate
        
        if self.debug:
            while(not self.UNSAFE_getCAcert()): time.sleep(2)
        if self.genCSR():
            self.signCSR()
        
    def signCSR(self):
        """Submit an existing CSR to CA for signing."""
        res = False
        if os.path.isfile(self.serviceCSRFile):
            with open(self.serviceCSRFile,'r') as f:
                csrData = f.read()
            try:
                url = CA_URL + 'ca/sign'
                payload = {'token': 'secret', 
                           'serviceType': self.serviceType,
                           'csr': csrData}
                if os.path.exists(self.caCert):
                    res = requests.post(url, json=payload, verify=self.caCert)
                else:
                    msg = "No CA cert found, proceeding w/o verification"
                    logger.error(msg)
                    res = requests.post(url, json=payload, verify=False)
            except requests.exceptions.ConnectionError as e:
                self.logger.error("The CA service is unavailable.%s" % e)
                return res

            if res.status_code != requests.codes.ok:
                self.logger.error("Cannot get certificate signed, resp %s, status code %s" \
                               % (res.text, res.status_code))
            else:
                # Save PEM received from a CA
                with open(self.serviceCertFile,'w') as f:
                    f.write(res.json()['PEM'])
                res = True
        else:
            self.logger.error("No CSR file found")
        return res

    def genCSR(self):
        """Create a service certificate request."""
        res = False
        if os.path.exists(self.sslConfigFile):
            name = self.serviceType + '-' + str(uuid.uuid4())
            info = "/C=NO/ST=Hordaland/L=Bergen/O=UiB/CN=%s" % name
            os.system("openssl req -new -config %s -subj %s -nodes -keyout %s -out %s" \
                   % (self.sslConfigFile, info, self.serviceKeyFile, self.serviceCSRFile))
            return True
        else:
            self.logger.error("OpenSSL service configuration file not found")
        return res

    def UNSAFE_getCAcert(self):
        """Fetch the CA certificate, this is insecure."""
        res = False
        if self.debug:
            self.logger.warning("UNSAFE: Retrieving remote CA certificate")
            try:
                pemCert = ssl.get_server_certificate((CA_HOSTNAME, CA_PORT))
            except socket_error as e:
                self.logger.error("Socket error: %s" %e)
                return res
            if pemCert:
                # Save the retrieved CA cert
                with open(self.caCert,'w') as f:
                    f.write(pemCert)
                    res = True
            else:
                self.logger.error("Remote CA certificate not received.")
        else:
            msg = "No unsafe functionality is allowed. Do better"
            self.logger.warning(msg)
        return res

    def getServiceKeyFileName(self):
        if os.path.isfile(self.serviceKeyFile):
            return self.serviceKeyFile

    def getServiceCertFileName(self):
        if os.path.isfile(self.serviceCertFile):
            return self.serviceCertFile

    def getCaCertFileName(self):
        if os.path.isfile(self.caCert):
            return self.caCert

    def delete(self):
        """Delete the existent certificate.

        Remove all the files of a specific type in the current directory.
        """
        filelist = [f for f in os.listdir('.') \
                    if f.endswith(('.pem', '.key', '.crt', '.csr'))]
        for f in filelist:
            os.remove(os.path.join('.', f))



class SecurityToken():
    """Manages user authentication tokens in JWT format.

    User authentication information propagates as a JWT through the network.
    """
    def __init__(self, logger, debug=False):
        self.logger = logger
        self.debug = debug
        self.tokenCert = 'tokencert.pem' # CA certificate
        self.latest = None
        if self.debug:
            isLoaded = self.getCertRemote()
            if isLoaded:
                self.pubKey = self.getPubKey()
                self.validate(self.getTestToken())
            else:
                self.logger.error("Remote certificate required. Terminating")
                exit()

    def getCertRemote(self):
        """Fetch a certificate for token verification, this is insecure."""
        res = False
        try:
            url = TOKEN_URL + 'cert/pem'
            res = requests.get(url)#, verify=self.caCert)
        except requests.exceptions.ConnectionError:
            self.logger.error("The UserAuthToken service is unavailable.")
            return res

        if res.status_code != requests.codes.ok:
            self.logger.error("Cannot get a certificate for token verification, resp %s, status code %s" \
                           % (res.text, res.status_code))
        else:
            # Save PEM received from the UserAuthToken service
            if res.json()['PEM']:
                with open(self.tokenCert,'w') as f:
                    f.write(res.json()['PEM'])
                self.logger.info("UserAuthToken endpoint verif. cert. retrieved")
                res = True
        return res

    def getPubKey(self):
        """Retrieve a public key from the full certificate."""
        if os.path.isfile(self.tokenCert):
            with open(self.tokenCert,'r') as f:
                certPEM = f.read()
                certObj = load_pem_x509_certificate(certPEM, default_backend())
                return certObj.public_key()
        else:
            self.logger.info("Public key cannot be loaded: file not found.")

    def getTestToken(self):
        if self.debug:
            self.logger.warning("UNSAFE: Logging in as a test user")
            return self.getToken('test')
        else:
            msg = "No unsafe functionality is allowed. Do better"
            self.logger.warning(msg)

    def getToken(self, username):
        try:
            url = TOKEN_URL + 'login'
            payload = {'username': username}
            res = requests.post(url, json=payload)#, verify=self.caCert)
        except requests.exceptions.ConnectionError:
            self.logger.error("The UserAuthToken service is unavailable.")
            return

        if res.status_code != requests.codes.ok:
            self.logger.error("Cannot login as a test user, resp %s, status code %s" \
                           % (res.text, res.status_code))
        else:
            data_json = res.json()
            if 'access_token' in data_json:
                accessToken = data_json['access_token']
                self.logger.info("access_token: %s" % accessToken)
                return accessToken
            else:
                self.logger.warning("No access token found, resp: %s" % data_json)

    def validate(self, token):
        if token:
            if self.pubKey:
                try:
                    token_decoded = jwt.decode(token, self.pubKey, algorithms=['RS256'])
                    self.latest = token
                    return token_decoded
                except jwt.InvalidTokenError as e:
                    self.logger.warning("Invalid JWT: %s." % e)
            else:
                self.logger.info("Public key not initialized.")
        else:
            self.logger.info("Empty token.")
        self.latest = None



class Requests():
    """Requests with MTLS. 

    A simple wrapper over the requests module that enforces the use of MTLS.
    Supplies client side certificate to the remote server. Always verifies
    the certificate from the remote server.
    """
    def __init__(self):
        self.latestToken = ""
        self.s = requests.Session()
        if getEnvVar('TOKEN', False):
            self.securityToken = SecurityToken(logger, DEBUG)
        else:
            self.securityToken = None
        if getEnvVar('MTLS', False):
            serviceCert = ServiceCert(logger, serviceType, DEBUG)
            self.serviceCertFileName = serviceCert.getServiceCertFileName()
            self.serviceKeyFileName = serviceCert.getServiceKeyFileName()
            self.caCertFileName = serviceCert.getCaCertFileName()

            self.s.cert = (self.serviceCertFileName, self.serviceKeyFileName)
            self.s.verify = self.caCertFileName


    def format(self, *args, **kwargs):
        if self.securityToken:
            if self.latestToken and len(self.latestToken) > 0:
                if 'json' not in kwargs:
                    kwargs['json'] = {}
                kwargs['json']['access_token'] = self.latestToken
            else:
                logger.warning("'self.latestToken' in memory is empty.")

        kwargs['allow_redirects'] = False
        kwargs['stream'] = False
        return (args, kwargs)

    def get(self, *args, **kwargs):
        (newArgs, newKwargs) = self.format(*args, **kwargs)
        return self.s.get(*newArgs, **newKwargs)

    def post(self, *args,**kwargs):
        (newArgs, newKwargs) = self.format(*args, **kwargs)
        return self.s.post(*newArgs, **newKwargs)


# MTLS certificates should be in place before Gunicorn web server starts.  
secureRequests = Requests()


def jwt_conditional(reqs):
    def real_decorator(f):
        @wraps(f)
        def decorated_function(*args, **kws):
            #logger.info("request.json: %s" % request.json)
            if not request.json or not 'access_token' in request.json or \
                len(request.json['access_token']) == 0:
                logger.warning("'access_token' not found in the request.")
                abort(401)
            token = request.json['access_token']
            if reqs.securityToken.validate(token):
                reqs.latestToken = token
            else:
                reqs.latestToken = ""
                logger.warning("'access_token' is invalid.")
                abort(403)
            return f(*args, **kws)
        return decorated_function
    return real_decorator






