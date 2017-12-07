import json
import requests
import unittest

BASE_URL = 'http://localhost:5002/'

test_accounts = [['user1_id'],
            ['user2_id'],
            ['user3_id']]


def convertToPosIntSafe(x):
    try:
        value = int(x)
        if value > 0:
            return value
        else:
            print ('Attempted to convert negative number into positive: %s' % value)
    except ValueError as error:
        # it was a string, not an int.
        print ('Attempted to convert sting into integer.\n%s' % error)



class AccountsClient(object):
    def createAccount(self, user_id):
        url = BASE_URL + 'createAccount'
        payload = {'user_id':user_id}
        resp = requests.post(url, json=payload)
        return (resp.status_code, resp.text)

    def getAllAccounts(self):
        url = BASE_URL + 'getAllAccounts'
        resp = requests.get(url)
        return (resp.status_code, resp.text)

    def getAccount(self, accNum):
        url = BASE_URL + 'getAccount'
        payload = {'accNum':accNum}
        resp = requests.post(url, json=payload)
        return (resp.status_code, resp.text)

    def updateAccount(self, accNum, amount=1000):
        url = BASE_URL + 'updateAccount'
        payload = {'accNum':accNum, 'amount':amount}
        resp = requests.post(url, json=payload)
        return (resp.status_code, resp.text)

    def closeAccount(self, accNum):
        url = BASE_URL + 'closeAccount'
        payload = {'accNum':accNum}
        resp = requests.post(url, json=payload)
        return (resp.status_code, resp.text)

    def getUserAccounts(self, user_id):
        url = BASE_URL + 'getUserAccounts'
        payload = {'user_id':user_id}
        resp = requests.post(url, json=payload)
        return (resp.status_code, resp.text)



class TestUsersService(unittest.TestCase):
    def setUp(self):
        self.client = AccountsClient()
        self.userId = test_accounts[0][0]
        status_code, resp = self.client.createAccount(self.userId)
        resp_json = json.loads(resp)
        if status_code == 200 and resp_json and 'accNum' in resp_json:
            self.accNum = resp_json['accNum']

    def tearDown(self):
        if self.accNum:
            self.client.closeAccount(self.accNum)
        self.client = None
        self.accNum = None

    def test_get_account(self):
        status_code, resp = self.client.getAccount(self.accNum)
        resp_json = json.loads(resp)
        self.assertEqual(status_code, 200)
        self.assertIsNotNone(resp_json)
        self.assertIn('accNum', resp_json)
        if 'accNum' in resp_json:
            self.assertEqual(resp_json['accNum'], self.accNum)
        self.assertIn('user_id', resp_json)
        if 'user_id' in resp_json:
            self.assertEqual(resp_json['user_id'], self.userId)
        self.assertIn('balance', resp_json)
        self.assertIn('id', resp_json)

    def test_add_user(self):
        for acc in test_accounts:
            status_code, resp = self.client.createAccount(acc[0])
            resp_json = json.loads(resp)
            self.assertEqual(status_code, 200)
            self.assertIsNotNone(resp_json)
            self.assertIn('accNum', resp_json)
            if status_code == 200 and resp_json and 'accNum' in resp_json:
                acc.append(resp_json['accNum'])

    def test_close_account(self):
        for acc in test_accounts:
            status_code, resp = self.client.closeAccount(acc[1])
            resp_json = json.loads(resp)
            self.assertEqual(status_code, 200)
            self.assertIsNotNone(resp_json)
            self.assertIn('accNum', resp_json)

    def test_update_account(self):
        amount = 20
        status_code, resp = self.client.getAccount(self.accNum)
        resp_json = json.loads(resp)
        self.assertEqual(status_code, 200)
        self.assertIsNotNone(resp_json)
        self.assertIn('balance', resp_json)
        if status_code == 200 and resp_json and 'balance' in resp_json:
            original_balance = convertToPosIntSafe(resp_json['balance'])
            self.assertIsNotNone(original_balance)
            if original_balance:
                status_code, resp = self.client.updateAccount(self.accNum, amount)
                resp_json = json.loads(resp)
                self.assertEqual(status_code, 200)
                self.assertIsNotNone(resp_json)
                self.assertIn('balance', resp_json)
                if status_code == 200 and resp_json and 'balance' in resp_json:
                    new_balance = convertToPosIntSafe(resp_json['balance'])
                    self.assertIsNotNone(new_balance)
                    self.assertEqual(original_balance+amount, new_balance)

if __name__ == '__main__':
    unittest.main()










