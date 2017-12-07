from db_controller import db

# The User class contains several fields, defined as class variables. 
# Fields are created as instances of the db.Column class, which takes the field type as an 
# argument, plus other optional arguments that allow us, for example, to indicate which fields are unique and indexed.
# The __repr__ method tells Python how to print objects of this class. We will use this for debugging.

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    pwd = db.Column(db.String(120), index=True, unique=False)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def __repr__(self):
        return '<User %r>' % (self.username)








