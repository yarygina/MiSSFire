import json
import requests
import unittest

BASE_URL = 'http://localhost/'

test_users = [['user1', '1234'],
			['user2', '5678'],
			['user3', '9012']]


class ApiGatewayClient(object):
	def __init__(self, url):
		self.baseUrl = url

	def addUser(self, username, pwd):
		url = '{}/users/enroll'.format(self.baseUrl)
		payload = {'username':username, 'pwd':pwd}
		return requests.post(url, json=payload)

	def openAccount(self, userID):
		url = '{}/users/{}/accounts/open'.format(self.baseUrl, userID)
		return requests.get(url)

	def showAccounts(self, userID):
		url = '{}/users/{}/accounts'.format(self.baseUrl, userID)
		return requests.get(url)

	def showTransactions(self, accNum):
		url = '{}/accounts/{}/transactions'.format(self.baseUrl, accNum)
		return requests.get(url)

	def showUser(self, username):
		url = '{}/users/{}'.format(self.baseUrl, username)
		return requests.get(url)

	def pay(self, fromAccNum, toAccNum, amount):
		url = '{}/pay'.format(self.baseUrl)
		payload = {'fromAccNum':fromAccNum, 'toAccNum':toAccNum, 'amount':amount}
		return requests.post(url, json=payload)
		



class TestUsersService(unittest.TestCase):
	def setUp(self):
		self.client = ApiGatewayClient(BASE_URL)

	def tearDown(self):
		self.client = None

	def test_add_user(self):
		for user in test_users:
			status_code, resp_json = addUser(user[0], user[1])
			print resp_json
			self.assertEqual(status_code, 200)

if __name__ == '__main__':
	unittest.main()