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
from models import User

class dbCtrl():
    """Wrapper over the users database."""
    def __init__(self, logger):
        self.logger = logger
        self.to_json = lambda user: {"id": user.id, "username": user.username,
                                     "pwd": user.pwd}

    def getByUsername(self, username, json=False):
        try:
            # A non existing username gives None
            u = User.query.filter_by(username=username).first()
            self.logger.info('User (%s) is retrieved' % username)
            if json:
                return self.to_json(u)
            else:
                return u
        except Exception as error:
            db.session.rollback()
            self.logger.error(error)

    def isUser(self, username):
        u = self.getByUsername(username)
        self.logger.info('Checked users existence username (%s)' % username)
        return not (u is None)

    def createUser(self, username, pwd):
        res = 1
        try:
            if not self.isUser(username):
                u = User(username=username, pwd=pwd)
                db.session.add(u)
                db.session.commit()
                res = self.to_json(u)
                self.logger.info('User (%s) is created' % username)
            else:
                res = 2
                self.logger.warning('Username (%s) already in use' % username)
        except Exception as error:
            db.session.rollback()
            self.logger.error(error)
        finally:
            return res

    def getAllUsers(self, json=False):
        try:
            users = User.query.all()
            self.logger.info('Users are retrieved')
            if json:
                return [self.to_json(user) for user in users]
            else:
                return users
        except Exception as error:
            db.session.rollback()
            self.logger.error(error)

    def isUserAllowed(self, username, pwd):
        res = 1     
        u = self.getByUsername(username)
        if u:
            try:
                if u.pwd == pwd:
                    res = 0 # Password is correct
                    self.logger.info('Pwd is correct for username (%s)' \
                                     % username)
                else:
                    res = 3 # User exists, but password is invalid
                    self.logger.warning('Pwd is incorrect for username (%s)' \
                                        % username)
            except Exception as error:
                db.session.rollback()
                self.logger.error(error)
        else:
            res = 2 # Nonexistent user
        return res

    def removeUser(self, username):
        res = 1
        u = self.getByUsername(username)
        if u:
            try:
                db.session.delete(u)
                db.session.commit()
                res = 0
                self.logger.info('User is removed username (%s)' % username)
            except Exception as error:
                db.session.rollback()
                self.logger.error(error)
        return res

    def deleteAll(self):
        res = 1
        try:
            numUsersDeleted = User.query.delete()
            numAccountsDeleted = Account.query.delete()
            db.session.commit()
            res = 0
            self.logger.info('All users removed')
        except Exception as error:
            db.session.rollback()
            self.logger.error(error)
        finally:
            return res





