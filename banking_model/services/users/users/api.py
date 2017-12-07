import sys
import json

from flask import Flask, request, make_response

from general import log, getEnvVar, isDocker
from db_controller import db_create, db_migrate, dbCtrl
from MiSSFire import ServiceCert, CorrelationToken


SERVICE_TYPE = "users"

# Environmental variables: security
MTLS = getEnv('MTLS', False)
TOKEN = getEnv('TOKEN', False)
# Environmental variables: debugging
DEBUG = getEnv('SERVICE_DEBUG', False)
FLASK_DEBUG = getEnv('FLASK_DEBUG', False)


logger = log(SERVICE_TYPE).logger

if MTLS:
    serviceCert = ServiceCert(logger, SERVICE_TYPE, DEBUG)

if TOKEN:
    correlationToken = CorrelationToken(logger, DEBUG)


FLASK_HOST = '0.0.0.0'
if isDocker():
    FLASK_PORT = 80
else:
    FLASK_PORT = 9081

app = Flask(__name__)



# Load DB controller
db = dbCtrl(logger)

def prepareDB():
    """Ensure presence of the required DB files."""
    res = False
    if db_create.isDBVolume():
        if not db_create.isDBfile():
            db_create.main()
            db_migrate.main()
        res = True
    return res

if not prepareDB():
    logger.error("Missing volume. Terminating.")
    sys.exit(1)





def all_links():
    links = []
    for rule in app.url_map.iter_rules():
        links.append(str(rule))
    return links


@app.route("/", methods=['GET'])
def hello():
    return nice_json({"subresource_uris": all_links()})


@app.route("/users", methods=['GET'])
def usersIndex():
    res_code = 400
    res = db.getAllUsers(json=True)
    if res:
        res_code = 200
    return nice_json(res), res_code


@app.route("/getUser", methods=['POST'])
def getUser():
    if not request.json or not 'username' in request.json:
        abort(400)
    username = request.json['username']
    res_code = 400
    res = {'id': db.getByUsername(username, json=True)['id']}
    if res:
        res_code = 200
    return nice_json(res), res_code


@app.route("/addUser", methods=['POST'])
def addUser():
    if not request.json or not 'username' in request.json or \
                           not 'pwd' in request.json:
        abort(400)
    username = request.json['username']
    res = ""
    res_code = 400
    if not db.isUser(username):
        pwd = request.json['pwd']
        res = {'id': db.createUser(username, pwd)['id']}
        if res != 1 and res != 2:
            res_code = 200
    else:
        res = "User already exists"
    return nice_json(res), res_code


@app.route("/removeUser", methods=['POST'])
def removeUser():
    if not request.json or not 'username' in request.json:
        abort(400)
    username = request.json['username']
    res = ""
    if db.isUser(username):
        db.removeUser(username)
        res = "User %s is removed" % username
    else:
        res = "User doesn't exist"
    return nice_json({'Result': res}), 201


@app.route("/login", methods=['POST'])
def login():
    if not request.json or not 'username' in request.json or \
                           not 'pwd' in request.json:
        abort(400)
    username = request.json['username']
    pwd = request.json['pwd']

    isAllowedCode = db.isUserAllowed(username, pwd)
    res = "No"
    if isAllowedCode == 0:
        res = "Yes"
    return nice_json({'AuthN': res}), 201


def nice_json(arg):
    """Form JSON responses."""
    response = make_response(json.dumps(arg, sort_keys = True, indent=4))
    response.headers['Content-type'] = "application/json"
    return response



def main():
    logger.info("%s service starting now: MTLS=%s, Token=%s" \
                % (SERVICE_TYPE, MTLS, TOKEN))
    # Start Flask web server
    if MTLS and serviceCert:
        # SSL configuration for Flask. Order matters!
        cert = serviceCert.getServiceCertFileName()
        key = serviceCert.getServiceKeyFileName()
        if cert and key:
            app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, \
                    ssl_context=(cert,key))
        else:
            logger.error("Cannot serve API without SSL cert and key.")
            exit()
    else:
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
        


if __name__ == "__main__":
    main()    



