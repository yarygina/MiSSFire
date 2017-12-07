import json
import time
import datetime
import multiprocessing

import requests



HOST = '0.0.0.0'
PORT = 31337

PROT = 'http'
APIGATEWAY_PORT = 8888


class Simulation():
    def __init__(self):
        self.client = BankClient()
        self.customers = [{'username':'A', 'pwd':'1234'},
                          {'username':'B', 'pwd':'5678'}]
        self.operationsCounter = 0
        self.startTime = datetime.datetime.now()


    def printPerformance(self):
        endTime = datetime.datetime.now()
        secondsPassed = float((endTime - self.startTime).total_seconds())
        operationsPerSec = float(self.operationsCounter / secondsPassed)
        print "Transactions per second (%d/%f): %f" \
              % (self.operationsCounter, secondsPassed, operationsPerSec)
        self.operationsCounter = 0
        self.startTime = endTime
        

    def run(self):
        if len(self.customers) == 0:
            print "Error: No customers to add!"
            exit()

        print "Adding %s bank customers." % (len(self.customers))
        for customer in self.customers:
            userID = self.client.createUser(customer['username'],
                                             customer['pwd'])
            if userID:
                customer['userID'] = userID
            else:
                exit()

        print "Creating bank accounts for the customers."
        for customer in self.customers:
            accNum = self.client.openAccount(customer['userID'])
            if accNum:
                customer['accNum'] = accNum
            else:
                exit()

        print "Start payment."
        x = 0
        y = 1
        for i in xrange(0,2002):
            res = self.client.pay(self.customers[x]['accNum'], self.customers[y]['accNum'], 20)
            if res:
                x, y = y, x
            else:
                print "Fail"
            self.operationsCounter +=1
            if self.operationsCounter > 1000:
                self.printPerformance()

        return




class BankClient:
    def __init__(self):
        self.BASE_URL = "%s://%s:%s" % (PROT, HOST, APIGATEWAY_PORT)

    def createUser(self, username, pwd):
        userID = None
        try:
            url = self.BASE_URL + '/users'
            payload = {'username':username, 
                       'pwd':pwd}
            resp = requests.post(url, json=payload, verify=False)

            # If the user already exist, request his id
            if 'User already exists' in resp.text:
                url += '/%s' % username
                resp = requests.get(url, json=payload, verify=False)
            # Proceed with the id extraction
            if resp.status_code != requests.codes.ok:
                print "Fail to create user: %s; reason: %s; status: %s" \
                      % (username, resp.text, resp.status_code)
            elif 'id' not in resp.json():
                print "'id' not in response msg: %s" % resp.json()
            else:
                userID = resp.json()['id']

        except requests.exceptions.ConnectionError as e:
            print "Connection error create user: %s" % e
        return userID

    def openAccount(self, userID):
        accNum = None
        url = '{}/users/{}/accounts'.format(self.BASE_URL, userID)
        try:
            resp = requests.post(url, verify=False)

            if resp.status_code != requests.codes.ok:
                print "Fail to open account for user: %s; reason: %s; status: %s" \
                      % (userID, resp.text, resp.status_code)
            elif 'accNum' not in resp.json():
                print "'accNum' not in response msg: %s" % resp.json()
            else:
                accNum = resp.json()['accNum']

        except requests.exceptions.ConnectionError as e:
            print "Connection error open account: %s" % e
        return accNum

    def pay(self, fromAccNum, toAccNum, amount):
        res = False
        try:
            url = self.BASE_URL + '/pay'
            payload = {'fromAccNum':fromAccNum, 
                       'toAccNum':toAccNum, 
                       'amount':amount}
            resp = requests.post(url, json=payload, verify=False)

            if resp.status_code != requests.codes.ok:
                print "Fail to pay: %s; reason: %s; status: %s" \
                      % (payload, resp.text, resp.status_code)
            else:
                res = True

        except requests.exceptions.ConnectionError as e:
            print "Connection error payment: %s" % e
        return res




def main():
    for x in xrange(0,1):
        p = multiprocessing.Process(target=Simulation().run)
        p.start()



if __name__ == "__main__":
    main()
