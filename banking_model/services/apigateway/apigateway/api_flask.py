import json
from os import getenv

from flask import Flask, request, make_response
from requests import codes
from requests.exceptions import ConnectionError
from werkzeug.exceptions import NotFound, ServiceUnavailable

from general import log, getEnvVar, isDocker
from MiSSFire import ServiceCert, CorrelationToken, Requests


SERVICE_TYPE = "apigateway"

# Resolve the environment variables if any
def getEnv(varName, defaultVal):
    """Translate string variables into boolean variables."""
    varVal = getenv(varName, defaultVal)
    if varVal == 'True': varVal = True
    elif varVal == 'False': varVal = False
    return varVal

# Environmental variables: security
MTLS = getEnv('MTLS', False)
TOKEN = getEnv('TOKEN', False)
# Environmental variables: debugging
DEBUG = getEnv('SERVICE_DEBUG', False)
FLASK_DEBUG = getEnv('FLASK_DEBUG', False)


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
    PAYMENT_SERVICE_URL      = '%s://%s:%s/' % (PROT, "payment", 80)
else:
    FLASK_PORT = 9080
    USERS_SERVICE_URL        = '%s://%s:%s/' % (PROT, '0.0.0.0', 9081)
    ACCOUNTS_SERVICE_URL     = '%s://%s:%s/' % (PROT, '0.0.0.0', 9082)
    TRANSACTIONS_SERVICE_URL = '%s://%s:%s/' % (PROT, '0.0.0.0', 9083)
    PAYMENT_SERVICE_URL      = '%s://%s:%s/' % (PROT, '0.0.0.0', 9084)

app = Flask(__name__)



def all_links():
    links = []
    for rule in app.url_map.iter_rules():
        links.append(str(rule))
    return links


@app.route("/", methods=['GET'])
def hello():
    return nice_json({"subresource_uris": all_links()})


@app.route("/users/<username>", methods=['GET'])
def userInfo(username):
    # try:
    #     url = USERS_SERVICE_URL + 'getUser'
    #     payload = {'username':username}
    #     users = requests.post(url, json=payload)
    # except ConnectionError as e:
    #     raise ServiceUnavailable("Users service connection error: %s."%e)

    # if users.status_code != codes.ok:
    #     raise NotFound("No users were found for username %s, status %s" \
    #                    % (username, users.status_code))
    users = {'id': 1}
    return nice_json(users)#.json())


@app.route("/users/<userID>/accounts", methods=['GET'])
def accountsInfo(userID):
    try:
        url = ACCOUNTS_SERVICE_URL + 'getUserAccounts'
        payload = {'user_id':userID}
        user_accounts = requests.post(url, json=payload)
    except ConnectionError as e:
        raise ServiceUnavailable("Accounts service connection error: %s."%e)

    if user_accounts.status_code != codes.ok:
        raise NotFound("No accounts found for userID %s, status %s" \
                       % (userID, user_accounts.status_code))

    return nice_json(user_accounts.json())


@app.route("/accounts/<accNum>/transactions", methods=['GET'])
def transactionsInfo(accNum):
    try:
        url = TRANSACTIONS_SERVICE_URL + 'getAccountTransactions'
        payload = {'accNum':accNum}
        user_transactions = requests.post(url, json=payload)
    except ConnectionError as e:
        raise ServiceUnavailable(
              "Transactions service connection error: %s." % e)

    if user_transactions.status_code != codes.ok:
        raise NotFound("No transactions found for accNum %s, status %s" \
                       % (accNum, user_transactions.status_code))

    return nice_json(user_transactions.json())


@app.route("/users", methods=['POST'])
def userEnroll():
    # if not request.json or not 'username' in request.json or \
    #                        not 'pwd' in request.json:
    #     abort(400)
    # username = request.json['username']
    # pwd = request.json['pwd']
    # try:
    #     url = USERS_SERVICE_URL + 'addUser'
    #     payload = {'username':username, 'pwd':pwd}
    #     res = requests.post(url, json=payload)
    # except ConnectionError as e:
    #     raise ServiceUnavailable("Users service connection error: %s."%e)

    # if res.status_code != codes.ok:
    #     raise NotFound("Cannot register user %s, resp %s, status code %s" \
    #                    % (username, res.text, res.status_code))
    res = {'id': 1}
    return nice_json(res)#.json())


@app.route("/users/<userID>/accounts", methods=['POST'])
def openAccount(userID):
    # try:
    #     url = ACCOUNTS_SERVICE_URL + 'createAccount'
    #     payload = {'user_id':userID}
    #     res = requests.post(url, json=payload)
    # except ConnectionError as e:
    #     raise ServiceUnavailable("Accounts service connection error: %s."%e)

    # if res.status_code != codes.ok:
    #     raise NotFound("Cannot open account for userID %s, status code %s" \
    #                    % (userID, res.status_code))
    res = {'accNum': 22}
    return nice_json(res)#.json())


@app.route("/pay", methods=['POST'])
def pay():
    # if (not request.json or not 'fromAccNum' in request.json
    #                     or not 'toAccNum' in request.json
    #                     or not 'amount' in request.json):
    #     abort(400)
    # fromAccNum = request.json['fromAccNum']
    # toAccNum = request.json['toAccNum']
    # amount = request.json['amount']
    # try:
    #     url = PAYMENT_SERVICE_URL + 'pay'
    #     payload = {'fromAccNum':fromAccNum, 'toAccNum':toAccNum, 
    #                'amount':amount}
    #     res = requests.post(url, json=payload)
    # except ConnectionError as e:
    #     raise ServiceUnavailable("Payment service connection error: %s."%e)

    # if res.status_code != codes.ok:
    #     raise NotFound("Cannot execute payment from " + \
    #                    "%s to %s amount %s, resp %s, status code %s" \
    #                    % (fromAccNum, toAccNum, amount, res.text, 
    #                       res.status_code))
    res = ""
    return nice_json(res)#.json())

@app.route("/logout", methods=['GET'])
def logout():
    raise NotImplementedError()

@app.route("/login", methods=['GET'])
def login():
    raise NotImplementedError()

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
            app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)#, 
            #        ssl_context=(cert,key))
        else:
            logger.error("Cannot serve API without SSL cert and key.")
            exit()
    else:
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)



if __name__ == "__main__":
    main()









