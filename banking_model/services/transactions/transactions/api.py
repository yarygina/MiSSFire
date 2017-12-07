import sys
import json
import datetime

from flask import Flask, request, make_response

from general import log, getEnvVar, isDocker
from db_controller import db_create, db_migrate, dbCtrl
from MiSSFire import ServiceCert, CorrelationToken

SERVICE_TYPE = "transactions"

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
    FLASK_PORT = 9083

app = Flask(__name__)


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


@app.route("/getAllTransactions", methods=['GET'])
def transactionsIndex():
   return nice_json(db.getAllTransactions()), 200


@app.route("/getAccountTransactions", methods=['POST'])
def getAccountTransactions():
    if not request.json or not 'accNum' in request.json:
        abort(400)
    accNum = request.json['accNum']
    print accNum
    return nice_json(db.getAllTransactionsForAcc(accNum, json=True)), 200


@app.route("/getTransaction", methods=['POST'])
def getTransaction():
    if not request.json or not 'number' in request.json:
        abort(400)
    number = request.json['number']
    return nice_json(db.getTransactionByNum(number, json=True)), 200


@app.route("/postTransaction", methods=['POST'])
def postTransaction():
    if (not request.json or not 'fromAccNum' in request.json
                        or not 'toAccNum' in request.json
                        or not 'amount' in request.json):
        abort(400)
    fromAccNum = request.json['fromAccNum']
    toAccNum = request.json['toAccNum']
    amount = int(request.json['amount'])
    res = ""
    res_code = 400
    transNum = db.addTransactionBetweenAccs(fromAccNum, toAccNum, amount)
    if transNum != 0:
        res = {'number': transNum}
        res_code = 200
    return nice_json(res), res_code


@app.route("/cancelTransaction", methods=['POST'])
def cancelTransaction():
    if not request.json or not 'number' in request.json:
        abort(400)
    number = request.json['number']
    res = ""
    res_code = 400
    if db.cancelTransaction(number) == 0:
        res = {'number': number}
        res_code = 200
    return nice_json(res), res_code


def nice_json(arg):
    """Form JSON responses."""
    response = make_response(json.dumps(arg, sort_keys = True, indent=4, default=json_serial))
    response.headers['Content-type'] = "application/json"
    return response

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type not serializable")



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



