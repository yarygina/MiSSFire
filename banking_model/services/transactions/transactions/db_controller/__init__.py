from random import randint
from datetime import datetime

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import or_

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
from models import Transaction


TRANSACTION_NUM_LENGTH = 5


class dbCtrl():
    """Wrapper over the transactions database."""
    def __init__(self, logger):
        self.accumulator = 1
        self.logger = logger
        self.to_json = lambda transaction: {
                              "whenCreated": transaction.whenCreated,
                              "whenExecuted": transaction.whenExecuted,
                              "whenCanceled": transaction.whenCanceled, 
                              "fromAccNum": transaction.fromAccNum,
                              "toAccNum": transaction.toAccNum,
                              "amount": transaction.amount,
                              "number": transaction.number,
                              "status": transaction.status}

    def getAllTransactionsForAcc(self, accNum, json=False):
        try:
            # A non existing user_id gives None
            transactions = Transaction.query.filter(or_(
                                       Transaction.fromAccNum.like(accNum),
                                       Transaction.toAccNum.like(accNum)
                                       ))
            self.logger.info('Transactions for accNum (%s) are retrieved' \
                             % accNum)
            if json:
                return [self.to_json(t) for t in transactions]
            else:
                return transactions
        except Exception as error:
            db.session.rollback()
            self.logger.error(error)

    def getTransactionByNum(self, transNum, json=False):
        try:
            # A non existing accNum gives None
            t = Transaction.query.filter_by(number=transNum).first()
            self.logger.info('Transaction with number=%s is retrieved' \
                             % transNum)
            if json:
                return self.to_json(t)
            else:
                return t
        except Exception as error:
            db.session.rollback()
            self.logger.error(error)

    def getAllTransactions(self):
        try:
            transactions = Transaction.query.all()
            self.logger.info('All accounts are retrieved')
            return [self.to_json(t) for t in transactions]
        except Exception as error:
            db.session.rollback()
            self.logger.error(error)

    def addTransactionBetweenAccs(self, fromAccNum, toAccNum, amount):
        res = None
        if fromAccNum and toAccNum:
            try:
                t = Transaction(whenCreated=datetime.utcnow(), 
                                amount=amount, 
                                fromAccNum=fromAccNum, 
                                toAccNum=toAccNum, status=0)
                db.session.add(t)
                db.session.commit()
                res = t.number
            except Exception as error:
                db.session.rollback()
                self.logger.error(error)
            return res

    def cancelTransaction(self, transNum):
        res = 1
        try:
            t = self.getTransactionByNum(transNum)
            t.status = 2
            t.whenCanceled = datetime.utcnow()
            db.session.add(t)
            db.session.commit()
            res = 0
        except Exception as error:
            db.session.rollback()
            self.logger.error(error)
        return res

