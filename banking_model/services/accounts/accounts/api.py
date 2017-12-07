import sys
import json

from flask import Flask, request, make_response

from general import log, getEnvVar, isDocker
from db_controller import db_create, db_migrate, dbCtrl
from MiSSFire import ServiceCert, CorrelationToken


SERVICE_TYPE = "accounts"

# Environmental variables: security
MTLS = getEnvVar('MTLS', False)
TOKEN = getEnvVar('TOKEN', False)
# Environmental variables: debugging
DEBUG = getEnvVar('SERVICE_DEBUG', False)
FLASK_DEBUG = getEnvVar('FLASK_DEBUG', False)


logger = log(SERVICE_TYPE).logger

if MTLS:
    serviceCert = ServiceCert(logger, SERVICE_TYPE, DEBUG)

if TOKEN:
    correlationToken = CorrelationToken(logger, DEBUG)


FLASK_HOST = '0.0.0.0'
if isDocker():
    FLASK_PORT = 80
else:
    FLASK_PORT = 9082

app = Flask(__name__)



DEFAULT_BALANCE = 1000

# Load DB controller
db = dbCtrl(logger)

def prepareDB():
    """Insure presence of the required DB files."""
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


@app.route("/getAllAccounts", methods=['GET'])
def accountsIndex():
    res = db.getAllAccounts()
    res_code = 400
    if res:
        res_code = 200
    return nice_json(res), res_code


@app.route("/getUserAccounts", methods=['POST'])
def getUserAccounts():
    if not request.json or not 'user_id' in request.json:
        abort(400)
    user_id = request.json['user_id']
    res = db.getAccountsByUserId(user_id, json=True)
    if not res:
        res = {}
    return nice_json(res), 200


@app.route("/getAccount", methods=['POST'])
def getAccount():
    if not request.json or not 'accNum' in request.json:
        abort(400)
    res = ""
    res_code = 400
    try:
        accNum = int(request.json['accNum'])
        res = db.getAccountByNum(accNum, json=True)
        if res:
            res_code = 200
    except ValueError:
        msg="accNum expected integer, received: %s"%request.json['accNum']
        logger.warning(msg)
        res['msg': msg]
    return nice_json(res), res_code


@app.route("/createAccount", methods=['POST'])
def createAccountForUserId():
    if not request.json or not 'user_id' in request.json:
        abort(400)
    res = ""
    res_code = 400
    try:
        user_id = int(request.json['user_id'])
        accNum = db.createAccountForUserId(user_id, DEFAULT_BALANCE)
        if accNum != 1:
            res = {'accNum': accNum}
            res_code = 200
    except ValueError:
        msg="UserID expected integer, received: %s"%request.json['user_id']
        logger.warning(msg)
        res['msg': msg]
    return nice_json(res), res_code


@app.route("/createAccountSuper", methods=['POST'])
def createAccountForSuperUserId():
    if not request.json or not 'user_id' in request.json:
        abort(400)
    res = ""
    res_code = 400
    try:
        user_id = int(request.json['user_id'])
        accNum = db.createAccountForUserId(user_id, sys.maxint / 2)
        if accNum != 1:
            res = {'accNum': accNum}
            res_code = 200
    except ValueError:
        msg="UserID expected integer, received: %s"%request.json['user_id']
        logger.warning(msg)
        res['msg': msg]
    return nice_json(res), res_code



@app.route("/closeAccount", methods=['POST'])
def closeAccount():
    if not request.json or not 'accNum' in request.json:
        abort(400)
    res = ""
    res_code = 400
    try:
        accNum = int(request.json['accNum'])
        if db.closeAccount(accNum) == 0:
            res = request.json
            res_code = 200
    except ValueError:
        msg="accNum expected integer, received: %s"%request.json['accNum']
        logger.warning(msg)
        res['msg': msg]
    return nice_json(res), res_code


@app.route("/updateAccount", methods=['POST'])
def updateAccount():
    if not request.json or not 'accNum' in request.json \
                        or not 'amount' in request.json:
        abort(400)
    res = ""
    res_code = 400
    try:
        accNum = int(request.json['accNum'])
        amount = int(request.json['amount'])
        new_balance = db.updateAccount(accNum, amount)
        if new_balance:
            res = {'balance':new_balance}
            res_code = 200
    except ValueError:
        msg = "Expected integers: accNum=%s, amount=%s" \
              % (request.json['accNum'], request.json['amount'])
        logger.warning(msg)
        res['msg': msg]
    return nice_json(res), res_code


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


