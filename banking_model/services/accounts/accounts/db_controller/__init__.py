from random import randint

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from sqlalchemy.engine import Engine
from sqlalchemy import event

# SQLAlchemy allows for the PRAGMA statement to be emitted automatically
# for new connections through the usage of events.
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA synchronous = OFF")
    cursor.execute("PRAGMA journal_mode = MEMORY")
    cursor.close()

app = Flask(__name__)
app.config.from_object('db_controller.db_config')
db = SQLAlchemy(app)

import models
from models import Account


ACCOUNT_NUM_LENGTH = 10


class dbCtrl():
    """Wrapper over the accounts database."""
    def __init__(self, logger):
        self.logger = logger
        self.to_json = lambda account: {
                              "user_id": account.user_id, 
                              "accNum": account.number, 
                              "balance": account.balance}

    def getAccountsByUserId(self, user_id, json=False):
        try:
            # A non existing user_id gives None
            accounts = Account.query.filter_by(user_id=user_id)
            self.logger.debug('Accounts for user_id (%s) are retrieved' \
                             % user_id)
            if json:
                return [self.to_json(account) for account in accounts]
            else:
                return accounts
        except Exception as error:
            db.session.rollback()
            self.logger.error(error)

    def getAccountByNum(self, accNum, json=False):
        try:
            # A non existing accNum gives None
            a = Account.query.filter_by(number=accNum).first()
            self.logger.debug('Account with number (%s) is retrieved' % accNum)
            if json:
                return self.to_json(a)
            else:
                return a
        except Exception as error:
            db.session.rollback()
            self.logger.error(error)

    def createAccountForUserId(self, user_id, initial_balance):
        res = 1
        try:
            a = Account(user_id=user_id, balance=initial_balance)
            db.session.add(a)
            db.session.commit()
            res = a.number
        except Exception as error:
            db.session.rollback()
            self.logger.error(error)
        return res

    def updateAccount(self, accNum, amount):
        res = None
        a = self.getAccountByNum(accNum)
        if a:
            try:
                a.balance += amount
                #db.session.add(a)
                db.session.commit()
                res = a.balance
            except Exception as error:
                db.session.rollback()
                self.logger.error(error)
        return res

    def closeAccount(self, accNum):
        res = 1
        a = self.getAccountByNum(accNum)
        if a:
            try:
                db.session.delete(a)
                db.session.commit()
                res = 0
                self.logger.debug('Account is removed user_id (%s)' % user_id)
            except Exception as error:
                db.session.rollback()
                self.logger.error(error)
        return res

    def getAllAccounts(self):
        try:
            accounts = Account.query.all()
            self.logger.debug('All accounts are retrieved')
            return [self.to_json(account) for account in accounts]
        except Exception as error:
            db.session.rollback()
            self.logger.error(error)








