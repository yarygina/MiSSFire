import os.path

DATAVOL = "/transactionsvol"
# Path to the DB file.
SQLALCHEMY_DATABASE_URI_SHORT = os.path.join(DATAVOL, 'transactions.db')
# SQLLite uri required by the Flask-SQLAlchemy extension.
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + SQLALCHEMY_DATABASE_URI_SHORT
# Path to the SQLAlchemy-migrate file
SQLALCHEMY_MIGRATE_REPO = os.path.join(DATAVOL, 'db_repository')
# To turn off the Flask-SQLAlchemy event system and disable the
# annoying warning (likely to be fixed in Flask-SQLAlchemy v3).
SQLALCHEMY_TRACK_MODIFICATIONS = False