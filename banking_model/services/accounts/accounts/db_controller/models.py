from db_controller import db

# The User class contains several fields, defined as class variables. 
# Fields are created as instances of the db.Column class, which takes the field type as an 
# argument, plus other optional arguments that allow us, for example, to indicate which fields are unique and indexed.

# The __repr__ method tells Python how to print objects of this class. We will use this for debugging.

class Account(db.Model):
    number = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer) 
    balance = db.Column(db.Integer)

    def __repr__(self):
        return '<Account number %r>' % (self.number)

