import json
import requests
import unittest

BASE_URL = 'http://localhost:5001/'

test_users = [['user1', '1234'],
            ['user2', '5678'],
            ['user3', '9012']]

def addUser(username, pwd, baseUrl=BASE_URL):
    url = baseUrl + 'addUser'
    payload = {'username':username, 'pwd':pwd}
    resp = requests.post(url, json=payload)
    return (resp.status_code, resp.text)


class TestUsersService(unittest.TestCase):
    def test_add_user(self):
        for user in test_users:
            status_code, resp_json = addUser(user[0], user[1])
            print resp_json
            self.assertEqual(status_code, 200)

if __name__ == '__main__':
    unittest.main()