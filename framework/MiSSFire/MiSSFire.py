import os
import ssl
import uuid

import jwt
import requests

from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend

CA_HOSTNAME = '0.0.0.0'
CA_PORT = 8080
CA_URL = 'https://%s:%s/' % (CA_HOSTNAME, CA_PORT)

TOKEN_HOSTNAME = '0.0.0.0'
TOKEN_PORT = 8083
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
            self.UNSAFE_getCAcert()

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
            except requests.exceptions.ConnectionError:
                self.logger.error("The CA service is unavailable.")
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
        if self.debug:
            self.logger.error("UNSAFE: Retrieving remote CA certificate")
            pemCert = ssl.get_server_certificate((CA_HOSTNAME, CA_PORT))
            if pemCert:
                # Save the retrieved CA cert
                with open(self.caCert,'w') as f:
                    f.write(pemCert)
        else:
            msg = "No unsafe functionality is allowed. Do better"
            self.logger.warning(msg)

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



class CorrelationToken():
    """Manages user authentication tokens in JWT format.

    User authentication information propagates as a JWT through the network.
    """
    def __init__(self, logger, debug=False):
        self.logger = logger
        self.debug = debug
        self.tokenCert = 'tokencert.pem' # CA certificate
        if self.debug:
            self.getCertRemote()
            self.pubKey = self.getPubKey()
            self.validate(self.getTestToken())

    def getCertRemote(self):
        """Fetch a certificate for token verification, this is insecure."""
        try:
            url = TOKEN_URL + 'cert/pem'
            res = requests.get(url)#, verify=self.caCert)
        except requests.exceptions.ConnectionError:
            self.logger.error("The UserAuthToken service is unavailable.")
            return

        if res.status_code != requests.codes.ok:
            self.logger.error("Cannot get a certificate for token verification, resp %s, status code %s" \
                           % (res.text, res.status_code))
        else:
            # Save PEM received from the UserAuthToken service
            with open(self.tokenCert,'w') as f:
                f.write(res.json()['PEM'])
            self.logger.info("UserAuthToken endpoint verif. cert. retrieved")

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
            self.logger.error("UNSAFE: Logging in as a test user")
            try:
                url = TOKEN_URL + 'login'
                payload = {'username': 'test', 
                           'password': 'test'}
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
                    self.logger.info("accessToken: %s" % accessToken)
                    return accessToken
                else:
                    self.logger.warning("No access token found, resp: %s" % data_json)
        else:
            msg = "No unsafe functionality is allowed. Do better"
            self.logger.warning(msg)

    def validate(self, token):
        if token:
            if self.pubKey:
                tmp = jwt.decode(token, self.pubKey, algorithms=['RS256'])
                self.logger.error(tmp)
            else:
                self.logger.info("Public key not initialized.")
        else:
            self.logger.info("Empty token.")


class Requests():
    """Requests with MTLS. 

    A simple wrapper over the requests module that enforces the use of MTLS.
    Supplies client side certificate to the remote server. Always verifies
    the certificate from the remote server.
    """
    def __init__(self, serviceCert):
        self.serviceCertFileName = serviceCert.getServiceCertFileName()
        self.serviceKeyFileName = serviceCert.getServiceKeyFileName()
        self.caCertFileName = serviceCert.getCaCertFileName()                    

    def get(self, *args,**kwargs):
        kwargs['cert'] = (self.serviceCertFileName, self.serviceKeyFileName)
        kwargs['verify'] = self.caCertFileName
        return requests.get(*args,**kwargs)

    def post(self, *args,**kwargs):
        kwargs['cert'] = (self.serviceCertFileName, self.serviceKeyFileName)
        kwargs['verify'] = self.caCertFileName
        return requests.post(*args,**kwargs)
        

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








