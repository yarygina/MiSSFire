#!flask/bin/python

# The way SQLAlchemy-migrate creates a migration is by comparing the structure of 
# the existing database file against the structure of the models. The differences 
# between the two are recorded as a migration script inside the migration repository.
# The migration script knows how to apply a migration or undo it, so it is always 
# possible to upgrade or downgrade a database format.

import imp
from migrate.versioning import api

from db_controller import db
from db_controller.db_config import SQLALCHEMY_DATABASE_URI
from db_controller.db_config import SQLALCHEMY_MIGRATE_REPO

def main():
	v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
	migration = SQLALCHEMY_MIGRATE_REPO + ('/versions/%03d_migration.py' \
		                                % (v+1))
	tmp_module = imp.new_module('old_model')
	old_model = api.create_model(SQLALCHEMY_DATABASE_URI, 
		                         SQLALCHEMY_MIGRATE_REPO)
	exec(old_model, tmp_module.__dict__)
	script = api.make_update_script_for_model(SQLALCHEMY_DATABASE_URI, 
		                                      SQLALCHEMY_MIGRATE_REPO, 
		                                      tmp_module.meta, db.metadata)
	open(migration, "wt").write(script)
	api.upgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
	v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
	print('New migration saved as ' + migration)
	print('Current database version: ' + str(v))



if __name__ == '__main__':
	main()