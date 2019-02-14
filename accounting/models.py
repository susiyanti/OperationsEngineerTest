from accounting import db
# from sqlalchemy.ext.declarative import declarative_base
# 
# DeclarativeBase = declarative_base()

class Policy(db.Model):
    __tablename__ = 'policies'

    __table_args__ = {}

    #column definitions
    id = db.Column(u'id', db.INTEGER(), primary_key=True, nullable=False)
    policy_number = db.Column(u'policy_number', db.VARCHAR(length=128), nullable=False)
    effective_date = db.Column(u'effective_date', db.DATE(), nullable=False)
    status = db.Column(u'status', db.Enum(u'Active', u'Canceled', u'Expired'), default=u'Active', nullable=False)
    billing_schedule = db.Column(u'billing_schedule', db.Enum(u'Annual', u'Two-Pay', u'Quarterly', u'Monthly'), default=u'Annual', nullable=False)
    annual_premium = db.Column(u'annual_premium', db.INTEGER(), nullable=False)
    named_insured = db.Column(u'named_insured', db.INTEGER(), db.ForeignKey('contacts.id'), nullable=False)
    agent = db.Column(u'agent', db.INTEGER(), db.ForeignKey('contacts.id'))
    cancel_date = db.Column(u'cancel_date', db.DATE())
    cancel_desc = db.Column(u'cancel_desc', db.VARCHAR(length=128))

    def __init__(self, policy_number, effective_date, annual_premium):
        self.policy_number = policy_number
        self.effective_date = effective_date
        self.annual_premium = annual_premium

    def serialize(self):
        return {
                 'id': self.id,
                 'policy_number': self.policy_number,
                 'effective_date': str(self.effective_date),
                 'status': self.status,
                 'cancel_date': str(self.cancel_date),
                 'cancel_desc': self.cancel_desc,
                 'billing_schedule': self.billing_schedule,
                 'annual_premium': self.annual_premium,
                 'named_insured': self.named_insured,
                 'agent': self.agent,
                 'invoices': [i.serialize() for i in self.invoices if not i.deleted]
        }

    invoices = db.relation('Invoice', primaryjoin="Invoice.policy_id==Policy.id")


class Contact(db.Model):
    __tablename__ = 'contacts'

    __table_args__ = {}

    #column definitions
    id = db.Column(u'id', db.INTEGER(), primary_key=True, nullable=False)
    name = db.Column(u'name', db.VARCHAR(length=128), nullable=False)
    role = db.Column(u'role', db.Enum(u'Named Insured', u'Agent'), nullable=False)

    def __init__(self, name, role):
        self.name = name
        self.role = role


class Invoice(db.Model):
    __tablename__ = 'invoices'

    __table_args__ = {}

    #column definitions
    id = db.Column(u'id', db.INTEGER(), primary_key=True, nullable=False)
    policy_id = db.Column(u'policy_id', db.INTEGER(), db.ForeignKey('policies.id'), nullable=False)
    bill_date = db.Column(u'bill_date', db.DATE(), nullable=False)
    due_date = db.Column(u'due_date', db.DATE(), nullable=False)
    cancel_date = db.Column(u'cancel_date', db.DATE(), nullable=False)
    amount_due = db.Column(u'amount_due', db.INTEGER(), nullable=False)
    deleted = db.Column(u'deleted', db.Boolean, default=False, server_default='0', nullable=False)

    def __init__(self, policy_id, bill_date, due_date, cancel_date, amount_due):
        self.policy_id = policy_id
        self.bill_date = bill_date
        self.due_date = due_date
        self.cancel_date = cancel_date
        self.amount_due = amount_due

    def serialize(self):
        return {
            'id': self.id,
            'policy_id': self.policy_id,
            'bill_date': str(self.bill_date),
            'due_date': str(self.due_date),
            'cancel_date': str(self.cancel_date),
            'amount_due': self.amount_due
        }


class Payment(db.Model):
    __tablename__ = 'payments'

    __table_args__ = {}

    #column definitions
    id = db.Column(u'id', db.INTEGER(), primary_key=True, nullable=False)
    policy_id = db.Column(u'policy_id', db.INTEGER(), db.ForeignKey('policies.id'), nullable=False)
    contact_id = db.Column(u'contact_id', db.INTEGER(), db.ForeignKey('contacts.id'), nullable=False)
    amount_paid = db.Column(u'amount_paid', db.INTEGER(), nullable=False)
    transaction_date = db.Column(u'transaction_date', db.DATE(), nullable=False)

    def __init__(self, policy_id, contact_id, amount_paid, transaction_date):
        self.policy_id = policy_id
        self.contact_id = contact_id
        self.amount_paid = amount_paid
        self.transaction_date = transaction_date

    def serialize(self):
        return {
            'policy_id': self.policy_id,
            'contact_id': self.contact_id,
            'amount_paid': self.amount_paid,
            'transaction_date': str(self.transaction_date)
        }
