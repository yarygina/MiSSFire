import json

import falcon
from requests import codes
from requests.exceptions import ConnectionError

from general import log, getEnvVar, isDocker
from falcon_app_template import app


SERVICE_TYPE = "apigateway"

logger = log(SERVICE_TYPE).logger

if getEnvVar('MTLS', False):
    PROT = 'https'
    from muServSec import ServiceCert, Requests
    serviceCert = ServiceCert(logger, SERVICE_TYPE, True)
    requests = Requests(serviceCert)
else:
    PROT = 'http'
    import requests


if isDocker():
    USERS_SERVICE_URL        = '%s://%s:%s/' % (PROT, "users", 80)
    ACCOUNTS_SERVICE_URL     = '%s://%s:%s/' % (PROT, "accounts", 80)
    TRANSACTIONS_SERVICE_URL = '%s://%s:%s/' % (PROT, "transactions", 80)
    PAYMENT_SERVICE_URL      = '%s://%s:%s/' % (PROT, "payment", 80)
else:
    USERS_SERVICE_URL        = '%s://%s:%s/' % (PROT, '0.0.0.0', 9081)
    ACCOUNTS_SERVICE_URL     = '%s://%s:%s/' % (PROT, '0.0.0.0', 9082)
    TRANSACTIONS_SERVICE_URL = '%s://%s:%s/' % (PROT, '0.0.0.0', 9083)
    PAYMENT_SERVICE_URL      = '%s://%s:%s/' % (PROT, '0.0.0.0', 9084)



class LoginResource(object):
    def on_post(self, req, resp):
        try:
            username = req.get_param('username')
            pwd = req.get_param('pwd')
        except KeyError:
            raise falcon.HTTPMissingParam(
                'Missing username or pwd',
                'Both username and pwd must be submitted in the request body.')
        try: 
            url = USERS_SERVICE_URL + 'getUser'
            payload = {'username':username, 'pwd':pwd}
            res = requests.post(url, json=payload)

            if res.status_code != codes.ok:
                raise NotFound(
                    "Cannot login user %s, resp %s, status code %s" \
                    % (username, res.text, res.status_code))
            else:
                resp.context = res.json()
                resp.status = falcon.HTTP_200
        except ConnectionError as e:
            raise HTTPBadRequest("Users service connection error: %s."%e)


class UsersResource(object):
    def on_post(self, req, resp):
        try:
            username = req.get_param('username')
            pwd = req.get_param('pwd')
        except KeyError:
            raise falcon.HTTPMissingParam(
                'Missing username or pwd',
                'Both username and pwd must be submitted in the request body.')
        try: 
            url = USERS_SERVICE_URL + 'addUser'
            payload = {'username':username, 'pwd':pwd}
            res = requests.post(url, json=payload)

            if res.status_code != codes.ok:
                raise NotFound(
                    "Cannot register user %s, resp %s, status code %s" \
                    % (username, res.text, res.status_code))
            else:
                resp.context = res.json()
                resp.status = falcon.HTTP_201
        except ConnectionError as e:
            raise HTTPBadRequest("Users service connection error: %s."%e)


class AccountsResource(object):
    def on_post(self, req, resp, userID):
        try: 
            url = ACCOUNTS_SERVICE_URL + 'createAccount'
            payload = {'user_id':userID}
            res = requests.post(url, json=payload)

            if res.status_code != codes.ok:
                raise NotFound(
                    "Cannot open account for userID %s, status code %s" \
                    % (userID, res.status_code))
            else:
                resp.context = res.json()
                resp.status = falcon.HTTP_201
        except ConnectionError as e:
            raise HTTPBadRequest("Accounts service connection error: %s."%e)


class PayResource(object):
    def on_get(self, req, resp):
        resp.data = "hello world"
        resp.status = falcon.HTTP_200

    def on_post(self, req, resp):
        try:
            fromAccNum = req.get_param('fromAccNum')
            toAccNum = req.get_param('toAccNum')
            amount = req.get_param('amount')
        except KeyError:
            raise falcon.HTTPMissingParam(
                'Missing fromAccNum, toAccNum or amount',
                'fromAccNum, toAccNum and amount are required.')
        try:
            url = PAYMENT_SERVICE_URL + 'pay'
            payload = {'fromAccNum':fromAccNum, 'toAccNum':toAccNum, 
                       'amount':amount}
            res = requests.post(url, json=payload)

            if res.status_code != codes.ok:
                raise NotFound("Cannot execute payment from " + \
                           "%s to %s amount %s, resp %s, status code %s" \
                           % (fromAccNum, toAccNum, amount, res.text, 
                              res.status_code))
            else:
                resp.context = res.json()
                resp.status = falcon.HTTP_200
        except ConnectionError as e:
            raise HTTPBadRequest("Payment service connection error: %s."%e)




app.add_route('/login', LoginResource())
app.add_route('/users', UsersResource())
app.add_route('/users/{userID}/accounts', AccountsResource())
app.add_route('/pay', PayResource())






