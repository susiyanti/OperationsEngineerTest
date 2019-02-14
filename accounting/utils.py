#!/user/bin/env python2.7

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from accounting import db
from models import Contact, Invoice, Payment, Policy

"""
#######################################################
This is the base code for the engineer project.
#######################################################
"""

class PolicyAccounting(object):
    """
     Each policy has its own instance of accounting.
    """
    def __init__(self, policy_id):
        self.policy = Policy.query.filter_by(id=policy_id).one()

        if not self.policy.invoices:
            self.make_invoices()

    def return_account_balance(self, date_cursor=None):
        """
         Calculate account balance by adding all amount due from invoices and subtract from all payments
        """
        if not date_cursor:
            date_cursor = datetime.now().date()

        invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
                                .filter(Invoice.bill_date <= date_cursor)\
                                .order_by(Invoice.bill_date)\
                                .all()
        due_now = 0
        for invoice in invoices:
            due_now += invoice.amount_due

        payments = Payment.query.filter_by(policy_id=self.policy.id)\
                                .filter(Payment.transaction_date <= date_cursor)\
                                .all()
        for payment in payments:
            due_now -= payment.amount_paid

        return due_now

    def make_payment(self, contact_id=None, date_cursor=None, amount=0):
        """
         Add new payment data to database.
         Use current date if date_cursor argument is not provided
         Use named insured id as contact id if not provided
        """
        if not date_cursor:
            date_cursor = datetime.now().date()

        if not contact_id:
            try:
                contact_id = self.policy.named_insured
            except:
                pass

        # If a policy is in cancellation pending due to non_pay, only an
        # agent should be able to make a payment on it
        if self.evaluate_cancellation_pending_due_to_non_pay(date_cursor) and contact_id is not self.policy.agent:
            print "Contact your agent for making payment"
            return None
        else:
            payment = Payment(self.policy.id,
                              contact_id,
                              amount,
                              date_cursor)
            db.session.add(payment)
            db.session.commit()

        return payment

    def evaluate_cancellation_pending_due_to_non_pay(self, date_cursor=None):
        """
         If this function returns true, an invoice
         on a policy has passed the due date without
         being paid in full. However, it has not necessarily
         made it to the cancel_date yet.
        """
        if not date_cursor:
            date_cursor = datetime.now().date()

        # Get invoices that has passed due date but not passed cancel date
        invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
                                .filter(Invoice.due_date < date_cursor)\
                                .filter(Invoice.cancel_date > date_cursor)\
                                .order_by(Invoice.bill_date)\
                                .all()

        # Check those invoices for balances
        for invoice in invoices:
            if not self.return_account_balance(invoice.cancel_date):
                continue
            else:
                return True
                break
        else:
            return False

    def evaluate_cancel(self, date_cursor=None):
        """
         Check if a policy should have canceled
         based on invoices that's not paid by cancel_date
        """
        if not date_cursor:
            date_cursor = datetime.now().date()

        invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
                                .filter(Invoice.cancel_date <= date_cursor)\
                                .order_by(Invoice.bill_date)\
                                .all()

        for invoice in invoices:
            if not self.return_account_balance(invoice.cancel_date):
                continue
            else:
                print "THIS POLICY SHOULD HAVE CANCELED"
                return True
        else:
            print "THIS POLICY SHOULD NOT CANCEL"
            return False

    def cancel_policy(self, date_cursor=None, desc=None):
        """
         Cancel policy for reason specified in desc or automatically cancel unpaid policy
        """
        if not date_cursor:
            date_cursor = datetime.now().date()

        # Cancel the policy for reason specified in desc
        if desc:
            self.policy.status = 'Canceled'
            self.policy.cancel_date = date_cursor
            self.policy.cancel_desc = desc
            db.session.commit()
        # Cancel the unpaid policy
        elif self.evaluate_cancel(date_cursor):
            self.policy.status = 'Canceled'
            self.policy.cancel_date = date_cursor
            self.policy.cancel_desc = "Unpaid"
            db.session.commit()
        else:
            return

    def create_new_invoices(self, invoices_left=None, start_date=None, due_now=None):
        billing_schedules = {'Annual': 1, 'Two-Pay': 2, 'Quarterly': 4, 'Monthly': 12}

        if not invoices_left:
            invoices_left = billing_schedules.get(self.policy.billing_schedule)
        if not start_date:
            start_date = self.policy.effective_date
        if not due_now:
            due_now = self.policy.annual_premium

        invoices = []

        if self.policy.billing_schedule in billing_schedules:
            for i in range(0, invoices_left):
                months_after_eff_date = i * 12/billing_schedules.get(self.policy.billing_schedule)
                bill_date = start_date + relativedelta(months=months_after_eff_date)
                invoice = Invoice(self.policy.id,
                                  bill_date,
                                  bill_date + relativedelta(months=1),
                                  bill_date + relativedelta(months=1, days=14),
                                  due_now / invoices_left)
                invoices.append(invoice)
        else:
            print "You have chosen a bad billing schedule."

        for invoice in invoices:
            db.session.add(invoice)
        db.session.commit()

    def make_invoices(self):
        """
         Create invoices for policy based on billing_schedule
        """
        for invoice in self.policy.invoices:
            invoice.delete()

        self.create_new_invoices()

    def change_billing_schedule(self, new_schedule):
        """
         Implement change billing schedule for cases that change from less frequest to more frequent
         Ex : From Two-Pay to Quarterly, Two-Pay to Monthly, or Quarterly to Monthly
        """
        billing_schedules = {'Annual': 1, 'Quarterly': 4, 'Two-Pay': 2, 'Monthly': 12}
        os = billing_schedules.get(self.policy.billing_schedule)
        ns = billing_schedules.get(new_schedule)

        # Cant change billing schedule from less frequent to more frequent
        # Ex : Two-Pay to Annual, Monthly to Quarterly
        if os >= ns:
            print "Cant change from more frequent to less frequent or same schedule"
            return

        # Get all payments made until now
        date_cursor = datetime.now().date()
        payments = Payment.query.filter_by(policy_id=self.policy.id)\
                                .filter(Payment.transaction_date <= date_cursor)\
                                .order_by(Payment.transaction_date.desc())\
                                .all()
        # Calculate how many month/quarter/two-pay left unpaid for new invoices
        invoices_left = ns - ns/os * len(payments)

        # if all invoices paid then no need to change billing
        if invoices_left == 0:
            print "All billing paid"
            return

        # if there are payments, get unpaid invoices only
        if len(payments) > 0:
            last_payment_date = payments[0].transaction_date
            invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
                                    .filter(Invoice.bill_date > last_payment_date)\
                                    .order_by(Invoice.bill_date)\
                                    .all()
        # if no payment made yet, get all invoices
        else:
            invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
                                    .order_by(Invoice.bill_date)\
                                    .all()

        # calculate due from invoices
        # and mark those invoices for deleted
        due_now = 0
        for invoice in invoices:
            due_now += invoice.amount_due
            invoice.deleted = True

        # change policy billing_schedule
        start_date = invoices[0].bill_date
        self.policy.billing_schedule = new_schedule
        db.session.commit()

        # generate new invoices for new billing schedule
        self.create_new_invoices(invoices_left, start_date, due_now)

################################
# The functions below are for the db and
# shouldn't need to be edited.
################################
def build_or_refresh_db():
    db.drop_all()
    db.create_all()
    insert_data()
    print "DB Ready!"

def insert_data():
    #Contacts
    contacts = []
    john_doe_agent = Contact('John Doe', 'Agent')
    contacts.append(john_doe_agent)
    john_doe_insured = Contact('John Doe', 'Named Insured')
    contacts.append(john_doe_insured)
    bob_smith = Contact('Bob Smith', 'Agent')
    contacts.append(bob_smith)
    anna_white = Contact('Anna White', 'Named Insured')
    contacts.append(anna_white)
    joe_lee = Contact('Joe Lee', 'Agent')
    contacts.append(joe_lee)
    ryan_bucket = Contact('Ryan Bucket', 'Named Insured')
    contacts.append(ryan_bucket)

    for contact in contacts:
        db.session.add(contact)
    db.session.commit()

    policies = []
    p1 = Policy('Policy One', date(2015, 1, 1), 365)
    p1.billing_schedule = 'Annual'
    p1.named_insured = john_doe_insured.id
    p1.agent = bob_smith.id
    policies.append(p1)

    p2 = Policy('Policy Two', date(2015, 2, 1), 1600)
    p2.billing_schedule = 'Quarterly'
    p2.named_insured = anna_white.id
    p2.agent = joe_lee.id
    policies.append(p2)

    p3 = Policy('Policy Three', date(2015, 1, 1), 1200)
    p3.billing_schedule = 'Monthly'
    p3.named_insured = ryan_bucket.id
    p3.agent = john_doe_agent.id
    policies.append(p3)

    for policy in policies:
        db.session.add(policy)
    db.session.commit()

    for policy in policies:
        PolicyAccounting(policy.id)

    payment_for_p2 = Payment(p2.id, anna_white.id, 400, date(2015, 2, 1))
    db.session.add(payment_for_p2)
    db.session.commit()
