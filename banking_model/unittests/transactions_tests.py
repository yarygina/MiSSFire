import json
import requests
import unittest

BASE_URL = 'http://localhost:5003/'

test_transactions = [['user1_acc', 'user4_acc', 100],
            ['user2_acc', 'user5_acc', 110],
            ['user3_acc', 'user6_acc', 120]]


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



class TransactionsClient(object):
    def getTransaction(self, number):
        url = BASE_URL + 'getTransaction'
        payload = {'number':number}
        resp = requests.post(url, json=payload)
        return (resp.status_code, resp.text)

    def getAllTransactions(self):
        url = BASE_URL + 'getAllTransactions'
        resp = requests.get(url)
        return (resp.status_code, resp.text)

    def getAccountTransactions(self, accNum):
        url = BASE_URL + 'getAccountTransactions'
        payload = {'accNum':accNum}
        resp = requests.post(url, json=payload)
        return (resp.status_code, resp.text)

    def postTransaction(self, fromAccNum, toAccNum, amount):
        url = BASE_URL + 'postTransaction'
        payload = {'fromAccNum':fromAccNum, 'toAccNum':toAccNum, 'amount':amount}
        resp = requests.post(url, json=payload)
        return (resp.status_code, resp.text)

    def cancelTransaction(self, number):
        url = BASE_URL + 'cancelTransaction'
        payload = {'number':number}
        resp = requests.post(url, json=payload)
        return (resp.status_code, resp.text)




class TestUsersService(unittest.TestCase):
    def setUp(self):
        self.client = TransactionsClient()
        self.fromAccNum = test_transactions[0][0]
        self.toAccNum = test_transactions[0][1]
        self.amount = test_transactions[0][2]
        status_code, resp = self.client.postTransaction(self.fromAccNum, self.toAccNum, self.amount)
        resp_json = json.loads(resp)
        if status_code == 200 and resp_json and 'number' in resp_json:
            self.transNum = resp_json['number']

    def tearDown(self):
        if self.transNum:
            self.client.cancelTransaction(self.transNum)
        self.client = None
        self.accNum = None

    def test_get_transaction(self):
        status_code, resp = self.client.getTransaction(self.transNum)
        print resp
        resp_json = json.loads(resp)
        self.assertEqual(status_code, 200)
        self.assertIsNotNone(resp_json)
        self.assertIn('fromAccNum', resp_json)
        if 'fromAccNum' in resp_json:
            self.assertEqual(resp_json['fromAccNum'], self.fromAccNum)
        self.assertIn('toAccNum', resp_json)
        if 'toAccNum' in resp_json:
            self.assertEqual(resp_json['toAccNum'], self.toAccNum)
        self.assertIn('amount', resp_json)
        if 'amount' in resp_json:
            self.assertEqual(resp_json['amount'], self.amount)
        self.assertIn('id', resp_json)

    def test_add_transaction(self):
        for t in test_transactions:
            status_code, resp = self.client.postTransaction(t[0], t[1], t[2])
            resp_json = json.loads(resp)
            self.assertEqual(status_code, 200)
            self.assertIsNotNone(resp_json)
            self.assertIn('number', resp_json)
            if status_code == 200 and resp_json and 'number' in resp_json:
                self.assertIsNotNone(resp_json['number'])
                t.append(resp_json['number'])

    def test_cancel_transaction(self):
        for t in test_transactions:
            status_code, resp = self.client.cancelTransaction(t[3])
            resp_json = json.loads(resp)
            self.assertEqual(status_code, 200)
            self.assertIsNotNone(resp_json)
            self.assertIn('number', resp_json)



if __name__ == '__main__':
    unittest.main()










