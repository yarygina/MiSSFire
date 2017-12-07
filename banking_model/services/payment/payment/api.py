import json

from flask import Flask, request, make_response
from requests import codes
from requests.exceptions import ConnectionError
from werkzeug.exceptions import NotFound, ServiceUnavailable

from general import log, getEnvVar, isDocker
from MiSSFire import ServiceCert, CorrelationToken, Requests

SERVICE_TYPE = "payment"

# Environmental variables: security
MTLS = getEnvVar('MTLS', False)
TOKEN = getEnvVar('TOKEN', False)
# Environmental variables: debugging
DEBUG = getEnvVar('SERVICE_DEBUG', False)
FLASK_DEBUG = getEnvVar('FLASK_DEBUG', False)


logger = log(SERVICE_TYPE).logger

if MTLS:
    PROT = 'https'
    serviceCert = ServiceCert(logger, SERVICE_TYPE, DEBUG)
    requests = Requests(serviceCert)
else:
    PROT = 'http'
    import requests

if TOKEN:
    correlationToken = CorrelationToken(logger, DEBUG)


FLASK_HOST = '0.0.0.0'
if isDocker():
    FLASK_PORT = 80
    USERS_SERVICE_URL        = '%s://%s:%s/' % (PROT, "users", 80)
    ACCOUNTS_SERVICE_URL     = '%s://%s:%s/' % (PROT, "accounts", 80)
    TRANSACTIONS_SERVICE_URL = '%s://%s:%s/' % (PROT, "transactions", 80)
else:
    FLASK_PORT = 9084
    USERS_SERVICE_URL        = '%s://%s:%s/' % (PROT, '0.0.0.0', 9081)
    ACCOUNTS_SERVICE_URL     = '%s://%s:%s/' % (PROT, '0.0.0.0', 9082)
    TRANSACTIONS_SERVICE_URL = '%s://%s:%s/' % (PROT, '0.0.0.0', 9083)

app = Flask(__name__)



def all_links():
    links = []
    for rule in app.url_map.iter_rules():
        links.append(str(rule))
    return links


@app.route("/", methods=['GET'])
def hello():
    return nice_json({"subresource_uris": all_links()})


@app.route("/pay", methods=['POST'])
def pay():
    if (not request.json or not 'fromAccNum' in request.json
                        or not 'toAccNum' in request.json
                        or not 'amount' in request.json):
        abort(400)
    fromAccNum = request.json['fromAccNum']
    toAccNum = request.json['toAccNum']
    amount = float(request.json['amount'])

    res = ""
    res_code = 400
    transNum = postTransaction(fromAccNum, toAccNum, amount)

    try:
        if transNum:
            if (not updateAccount(fromAccNum, -amount) or not updateAccount(toAccNum, amount)):
                cancelTransaction(transNum)
            else:
                res_code = 200
    except Exception as e:
        logger.error("Payment: %s" % e)

    return nice_json(res), res_code


def postTransaction(fromAccNum, toAccNum, amount):
    try:
        url = TRANSACTIONS_SERVICE_URL + 'postTransaction'
        payload = {'fromAccNum':fromAccNum, 'toAccNum':toAccNum, 
                   'amount':amount}
        res = requests.post(url, json=payload)
    except ConnectionError as e:
        raise ServiceUnavailable(
              "Transactions service connection error: %s." % e)

    if res.status_code != codes.ok:
        raise NotFound("Cannot post a transaction from " + \
              "%s to %s amount %s, resp %s, status code %s" \
              % (fromAccNum, toAccNum, amount, res.text, res.status_code))
    else:
        return res.json()['number']


def updateAccount(accNum, amount):
    try:
        url = ACCOUNTS_SERVICE_URL + 'updateAccount'
        payload = {'accNum':accNum, 'amount':amount}
        res = requests.post(url, json=payload)
    except ConnectionError as e:
        raise ServiceUnavailable("Accounts service connection error: %s."%e)

    if res.status_code != codes.ok:
        raise NotFound("Cannot update account %s, resp %s, status code %s" \
                       % (accNum, res.text, res.status_code))
    else:
        return res.json()['balance']


def cancelTransaction(transNum):
    try:
        url = TRANSACTIONS_SERVICE_URL + 'cancelTransaction'
        payload = {'number':transNum}
        res = requests.post(url, json=payload)
    except ConnectionError as e:
        raise ServiceUnavailable(
              "Transactions service connection error: %s." % e)

    if res.status_code != codes.ok:
        raise NotFound("Cannot cancel transaction %s, resp %s, status code %s" \
                       % (transNum, res.text, res.status_code))
    else:
        return res.json()['number']


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








