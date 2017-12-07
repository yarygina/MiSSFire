from db_controller import db

# Transaction status codes:
# 0 - created
# 1 - executed (i.e. accounts are updated successfully)
# 2 - canceled

class Transaction(db.Model):
    number = db.Column(db.Integer, primary_key = True)
    whenCreated = db.Column(db.DateTime) 
    whenExecuted = db.Column(db.DateTime) 
    whenCanceled = db.Column(db.DateTime)  
    amount = db.Column(db.Integer)
    fromAccNum = db.Column(db.String(64))
    toAccNum = db.Column(db.String(64))
    status = db.Column(db.Integer)

    def __repr__(self):
        return '<Transaction number %r>' % (self.number)







