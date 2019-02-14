# You will probably need more methods from flask but this one is a good start.
from flask import render_template, jsonify, json, Response

# Import things from Flask that we need.
from accounting import app, db
from accounting.utils import PolicyAccounting

# Import our models
from models import Contact, Invoice, Policy, Payment
from datetime import datetime, date

# Import for SQL exception
import sqlalchemy

# Routing for the server.
@app.route("/")
def index():
    # You will need to serve something up here.
    return render_template('index.html')


# Return policy by id and date
@app.route("/policy/<int:id>/<string:date>")
def getPolicyByIdAndDate(id, date):

    try:
        # Validate date format
        dateTime = datetime.strptime(date, "%Y-%m-%d")
    except ValueError as error:
        return Response("Please enter a valid date format mm/dd/yyyy", status=404)

    try:
        # Get policy
        policy = Policy.query.filter_by(id=id).one()
    except sqlalchemy.orm.exc.NoResultFound as error:
        # Print not found
        return Response("Policy " + str(id) + " was not found", status=404)

    try:
        # Get insured name
        insured = Contact.query.filter_by(id=policy.named_insured).one()
    except sqlalchemy.orm.exc.NoResultFound as error:
        return Response("Insured not found!", status=404)

    # Get agent name
    try:
        agent = Contact.query.filter_by(id=policy.agent).one()
    except sqlalchemy.orm.exc.NoResultFound as error:
        return Response("Agent not found!", status=404)

    # Serialize policy
    response = policy.serialize()

    # get policy accounting object and account balance
    pa = PolicyAccounting(policy.id)
    balance = pa.return_account_balance(dateTime)
    response['balance'] = balance

    # Add agent and insured names to response.
    response['agent_name'] = agent.name
    response['insured'] = insured.name

    # Get all payments for policy
    payments = Payment.query.filter_by(policy_id=policy.id).all()

    # Add payments
    all_payments = []
    for payment in payments:
        # Serialize payment and add to payments
        payment_response = payment.serialize()
        all_payments.append(payment_response)

    # Add payments to response.
    response['payments'] = all_payments
    return jsonify(response)
