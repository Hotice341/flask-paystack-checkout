import os

import requests
from flask import Flask, jsonify, redirect, render_template, request

app = Flask(__name__)

PAYSTACK_API_KEY = os.environ['PAYSTACK_API_KEY']
if not PAYSTACK_API_KEY:
    raise ValueError("PAYSTACK_API_KEY is not set")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/pay', methods=['POST'])
def pay():
    try:
        # Get the amount, firstname, lastname and email from the form
        amount = float(request.form.get('amount'))
        email = request.form.get('email')
        firstname = request.form.get('firstName')
        lastname = request.form.get('lastName')

        # Validate amount and email
        if amount <= 0 or not email:
            raise ValueError("Invalid amount or email")

        # Set up Paystack API endpoint and headers
        paystack_url = 'https://api.paystack.co/transaction/initialize'
        headers = {
            'Authorization': f'Bearer {PAYSTACK_API_KEY}',
            'Content-Type': 'application/json',
        }

        # Set up payload for the Paystack API request
        payload = {
            'first_name': firstname,
            'last_name': lastname,
            'email': email,
            'amount': int(amount * 100),  # Paystack expects amount in kobo
            'currency': 'NGN',
            'callback_url': 'http://localhost:5000/verify_payment',
        }

        # Make the API request to initialize the transaction
        response = requests.post(paystack_url, json=payload, headers=headers)
        data = response.json()

        # Redirect the user to the Paystack payment page
        return redirect(data['data']['authorization_url'])

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/verify_payment')
def verify_payment():
    # Get the transaction reference from the query parameters
    transaction_reference = request.args.get('reference')

    if not transaction_reference:
        return 'Transaction reference not provided', 400

    # Set up Paystack API endpoint and headers for transaction verification
    paystack_verify_url = f'https://api.paystack.co/transaction/verify/{transaction_reference}'
    headers = {
        'Authorization': f'Bearer {PAYSTACK_API_KEY}',
        'Content-Type': 'application/json',
    }

    try:
        # Make the API request to verify the transaction
        response = requests.get(paystack_verify_url, headers=headers)
        data = response.json()

        # Check if the transaction was successful
        if data['data']['status'] == 'success':
            # The payment was successful, you can handle this accordingly
            return render_template("success.html")

        # If the transaction was not successful, handle it accordingly
        return render_template("failed.html")

    except requests.RequestException as e:
        return f'Error verifying payment: {str(e)}', 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
