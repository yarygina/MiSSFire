#!flask/bin/python
import os.path
from os import remove

from migrate.versioning import api

from db_controller.db_config import SQLALCHEMY_DATABASE_URI
from db_controller.db_config import SQLALCHEMY_DATABASE_URI_SHORT, DATAVOL
from db_controller.db_config import SQLALCHEMY_MIGRATE_REPO
from db_controller import db


def isDBVolume():
	res = os.path.exists(DATAVOL)
	# print "Volume %s exists: %s" % (DATAVOL, res)
	if res:
		res = isWritable(DATAVOL)
		# print "Volume %s is writable: %s" % (DATAVOL, res)
	return res

def isWritable(directory):
    try:
        filepath = os.path.join(directory, "test.txt")
        f = open(filepath,"w")
        f.close()
        remove(filepath)
        return True
    except Exception as e:
        print "{}".format(e)
        return False

def isDBfile():
	return os.path.exists(SQLALCHEMY_DATABASE_URI_SHORT)

def main():
	# print SQLALCHEMY_DATABASE_URI, SQLALCHEMY_DATABASE_URI_SHORT
	db.create_all()
	if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
	    api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
	    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
	else:
	    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))


if __name__ == '__main__':
	main()