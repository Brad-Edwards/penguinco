import logging
import os
from typing import List, Tuple

import stripe
from dotenv import load_dotenv
from flasgger import Swagger
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static/build")
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
swagger = Swagger(app)

load_dotenv()
stripe.api_key = os.getenv("FLASK_APP_STRIPE_API_KEY")
stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

MISSING_PARAMETERS = "Missing required parameters"


def missing_params(required_params, data) -> Tuple[bool, List[str]]:
    missing_params = [param for param in required_params if not data.get(param)]
    if missing_params:
        return True, missing_params
    return False, []


@app.route("/api/attach_payment_method", methods=["POST"])
def attach_payment_method():
    """
    Attach a payment method to a customer
    ---
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        description: Payment method details
        required: true
        schema:
          type: object
          required:
            - customer_id
            - payment_identifier
          properties:
            customer_id:
              type: string
              description: Customer ID to attach the payment method to
            payment_identifier:
              type: string
              description: Payment method identifier
            set_as_default:
              type: boolean
              description: Set the payment method as the default for the customer
    responses:
      200:
        description: Payment method attached successfully
        schema:
          type: object
          properties:
            payment_method_id:
              type: string
              description: ID of the attached payment method
      400:
        description: Error with payment method attachment (e.g., missing parameters, Stripe error)
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
    """
    try:
        data = request.get_json()
        customer_id = data["customer_id"]
        payment_identifier = data["payment_identifier"]
        set_as_default = data.get("set_as_default", False)

        missing, params = missing_params(["customer_id", "payment_identifier"], data)
        if missing:
            return (
                jsonify({"error": MISSING_PARAMETERS, "missing_params": params}),
                400,
            )

        if payment_identifier.startswith("tok_"):
            payment_method = stripe.PaymentMethod.create(
                type="card", card={"token": payment_identifier}
            )
        else:
            payment_method = {"id": payment_identifier}

        stripe.PaymentMethod.attach(payment_method["id"], customer=customer_id)

        if set_as_default:
            stripe.Customer.modify(
                customer_id,
                invoice_settings={"default_payment_method": payment_method["id"]},
            )

        return jsonify({"payment_method_id": payment_method["id"]}), 200
    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/authorize_charge", methods=["POST"])
def authorize_charge():
    """
    Authorize a charge on a customer's payment method.
    ---
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        description: Payment intent details
        required: true
        schema:
          type: object
          required:
            - amount
            - customer_id
            - payment_method_id
          properties:
            amount:
              type: integer
              description: Amount to be charged in cents
            currency:
              type: string
              description: Currency in which the amount is charged
              default: "usd"
            customer_id:
              type: string
              description: Customer ID to charge
            payment_method_id:
              type: string
              description: Payment method ID to be charged
            payment_method_types:
              type: array
              items:
                type: string
              description: Types of payment methods
              default: ["card"]
            description:
              type: string
              description: Description of the transaction
            metadata:
              type: object
              description: Additional metadata for the transaction
            capture_method:
              type: string
              description: Capture method for the charge, e.g., 'automatic' or 'manual'
              default: "manual"
    responses:
      200:
        description: Payment intent created successfully
        schema:
          type: object
          properties:
            payment_intent_id:
              type: string
              description: ID of the created payment intent
      400:
        description: Error with payment intent creation (e.g., missing parameters, Stripe error)
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
    """
    try:
        data = request.get_json()
        amount = data["amount"]
        currency = data.get("currency", "usd")
        customer_id = data["customer_id"]
        payment_method_id = data["payment_method_id"]
        payment_method_types = data.get("payment_method_types", ["card"])
        description = data.get("description", "")
        metadata = data.get("metadata", {})
        capture_method = data.get("capture_method", "manual")

        missing, params = missing_params(
            ["amount", "customer_id", "payment_method_id"], data
        )
        if missing:
            return (
                jsonify({"error": MISSING_PARAMETERS, "missing_params": params}),
                400,
            )

        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            customer=customer_id,
            payment_method_types=payment_method_types,
            payment_method=payment_method_id,
            description=description,
            metadata=metadata,
            capture_method=capture_method,
            confirm=True,
        )

        return (
            jsonify(
                {
                    "payment_intent_id": payment_intent.id,
                    "client_secret": payment_intent.client_secret,
                }
            ),
            200,
        )
    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/capture_charge", methods=["POST"])
def capture_charge():
    """
    Capture a charge on a customer's payment method.
    ---
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        description: Payment intent details
        required: true
        schema:
          type: object
          required:
            - payment_intent_id
          properties:
            payment_intent_id:
              type: string
              description: Payment intent ID to be captured
    responses:
      200:
        description: Payment intent captured successfully
        schema:
          type: object
          properties:
            payment_intent_id:
              type: string
              description: ID of the captured payment intent
      400:
        description: Error with payment intent capture (e.g., missing parameters, Stripe error)
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
    """
    try:
        data = request.get_json()
        payment_intent_id = data["payment_intent_id"]

        missing, params = missing_params(["payment_intent_id"], data)
        if missing:
            return (
                jsonify({"error": MISSING_PARAMETERS, "missing_params": params}),
                400,
            )

        captured_intent = stripe.PaymentIntent.capture(payment_intent_id)

        return (
            jsonify(
                {
                    "payment_intent_id": captured_intent.id,
                    "status": captured_intent.status,
                    "amount_captured": captured_intent.amount_received,
                }
            ),
            200,
        )

    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/complete_charge", methods=["POST"])
def complete_charge():
    """
    Complete a charge on a customer's payment method.
    ---
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        description: Payment intent details
        required: true
        schema:
          type: object
          required:
            - amount
            - customer_id
            - payment_method_id
          properties:
            amount:
              type: integer
              description: Amount to be charged in cents
            currency:
              type: string
              description: Currency in which the amount is charged
              default: "usd"
            customer_id:
              type: string
              description: Customer ID to charge
            payment_method_id:
              type: string
              description: Payment method ID to be charged
            payment_method_types:
              type: array
              items:
                type: string
              description: Types of payment methods
              default: ["card"]
            description:
              type: string
              description: Description of the transaction
            metadata:
              type: object
              description: Additional metadata for the transaction
            capture_method:
              type: string
              description: Capture method for the charge, e.g., 'automatic' or 'manual'
              default: "automatic"
    responses:
      200:
        description: Payment intent captured successfully
        schema:
          type: object
          properties:
            payment_intent_id:
              type: string
              description: ID of the captured payment intent
    responses:
      400:
        description: Error with payment intent capture (e.g., missing parameters, Stripe error)
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
    """
    try:
        data = request.get_json()
        amount = data["amount"]
        currency = data.get("currency", "usd")
        customer_id = data["customer_id"]
        payment_method_id = data["payment_method_id"]
        payment_method_types = data.get("payment_method_types", ["card"])
        description = data.get("description", "")
        metadata = data.get("metadata", {})
        capture_method = data.get("capture_method", "automatic")

        missing, params = missing_params(
            ["amount", "customer_id", "payment_method_id"], data
        )
        if missing:
            return (
                jsonify({"error": MISSING_PARAMETERS, "missing_params": params}),
                400,
            )

        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            customer=customer_id,
            payment_method_types=payment_method_types,
            payment_method=payment_method_id,
            description=description,
            metadata=metadata,
            capture_method=capture_method,
            confirm=True,
        )

        return (
            jsonify(
                {
                    "payment_intent_id": payment_intent.id,
                    "client_secret": payment_intent.client_secret,
                }
            ),
            200,
        )
    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/create_subscription_session", methods=["POST"])
def create_subscription_session():
    """
    Create a Stripe CheckoutSession for a subscription.
    ---
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        description: Subscription session details
        required: true
        schema:
          type: object
          required:
            - customer_id
            - price_id
          properties:
            customer_id:
              type: string
              description: Customer ID for the subscription
            price_id:
              type: string
              description: Price ID for the subscription
            success_url:
              type: string
              description: URL to redirect to upon successful subscription
            cancel_url:
              type: string
              description: URL to redirect to if the subscription is cancelled
    responses:
      200:
        description: CheckoutSession created successfully
        schema:
          type: object
          properties:
            session_url:
              type: string
              description: URL to complete the checkout
      400:
        description: Error with session creation
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
    """
    try:
        data = request.get_json()
        customer_id = data["customer_id"]
        price_id = data["price_id"]
        success_url = data["success_url"]
        cancel_url = data["cancel_url"]

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer=customer_id,
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return jsonify({"session_url": session.url}), 200

    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/create_customer", methods=["POST"])
def create_customer():
    """
    Create a new customer in Stripe.
    ---
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        description: Customer details
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              description: Customer name
            email:
              type: string
              description: Customer email
    responses:
      200:
        description: Customer created successfully
        schema:
          type: object
          properties:
            customer_id:
              type: string
              description: ID of the created customer
      400:
        description: Error with customer creation (e.g., missing parameters, Stripe error)
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
    """
    try:
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")

        missing, params = missing_params(["name", "email"], data)
        if missing:
            logger.error(f"Missing parameters: {params}")
            return (
                jsonify({"error": MISSING_PARAMETERS, "missing_params": params}),
                400,
            )

        customer = stripe.Customer.create(name=name, email=email)
        logger.info(f"Customer created with ID: {customer.id}")
        return jsonify({"customer_id": customer.id}), 200

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Internal server error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/create_payment_intent", methods=["POST"])
def create_payment_intent():
    """
    Create a new payment intent in Stripe.
    ---
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        description: Payment intent details
        required: true
        schema:
          type: object
          required:
            - amount
          properties:
            amount:
              type: integer
              description: Amount to be charged in cents
            currency:
              type: string
              description: Currency in which the amount is charged
              default: "usd"
            payment_method_types:
              type: array
              items:
                type: string
              description: Types of payment methods
              default: ["card"]
    responses:
      200:
        description: Payment intent created successfully
        schema:
          type: object
          properties:
            payment_intent_id:
              type: string
              description: ID of the created payment intent
      400:
        description: Error with payment intent creation (e.g., missing parameters, Stripe error)
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
    """
    try:
        data = request.get_json()
        print(data)
        amount = data["amount"]
        currency = data.get("currency", "usd")
        payment_method_types = data.get("payment_method_types", ["card"])

        missing, params = missing_params(["amount"], data)
        if missing:
            return (
                jsonify({"error": MISSING_PARAMETERS, "missing_params": params}),
                400,
            )

        payment_intent = stripe.PaymentIntent.create(
            amount=amount, currency=currency, payment_method_types=payment_method_types
        )
        print(payment_intent.id, payment_intent.client_secret)
        return (
            jsonify(
                {
                    "payment_intent_id": payment_intent.id,
                    "client_secret": payment_intent.client_secret,
                }
            ),
            200,
        )

    except stripe.error.StripeError as e:
        print(e)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/create_price", methods=["POST"])
def create_price():
    """
    Create a new price in Stripe, optionally with a recurring interval.
    ---
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        description: Price details
        required: true
        schema:
          type: object
          required:
            - product_id
            - unit_amount
          properties:
            product_id:
              type: string
              description: Product ID to create the price for
            unit_amount:
              type: integer
              description: Unit amount in cents
            currency:
              type: string
              description: Currency in which the unit amount is charged
              default: "usd"
            recurring:
              type: object
              description: Recurring billing details (optional)
              properties:
                interval:
                  type: string
                  description: Billing interval (e.g., 'day', 'week', 'month', 'year')
                interval_count:
                  type: integer
                  description: Number of intervals between bills (optional, default is 1)
    responses:
      200:
        description: Price created successfully
        schema:
          type: object
          properties:
            price_id:
              type: string
              description: ID of the created price
      400:
        description: Error with price creation (e.g., missing parameters, Stripe error)
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
    """
    try:
        data = request.get_json()
        product_id = data["product_id"]
        unit_amount = data["unit_amount"]
        currency = data.get("currency", "usd")
        recurring = data.get("recurring", None)

        price_data = {
            "product": product_id,
            "unit_amount": unit_amount,
            "currency": currency,
        }

        if recurring:
            price_data["recurring"] = {
                "interval": recurring.get("interval"),
                "interval_count": recurring.get("interval_count", 1),
            }

        price = stripe.Price.create(**price_data)
        return jsonify({"price_id": price.id}), 200

    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/create_product", methods=["POST"])
def create_product():
    """
    Create a new product in Stripe.
    ---
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        description: Product details
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
              description: Product name
            description:
              type: string
              description: Product description
            active:
              type: boolean
              description: Whether the product is active
              default: true
    responses:
      200:
        description: Product created successfully
        schema:
          type: object
          properties:
            product_id:
              type: string
              description: ID of the created product
      400:
        description: Error with product creation (e.g., missing parameters, Stripe error)
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
    """
    try:
        data = request.get_json()
        name = data["name"]
        description = data.get("description", "")
        active = data.get("active", True)

        missing, params = missing_params(["name"], data)
        if missing:
            return (
                jsonify({"error": MISSING_PARAMETERS, "missing_params": params}),
                400,
            )

        product = stripe.Product.create(
            name=name, description=description, active=active
        )

        return (
            jsonify(
                {
                    "product_id": product.id,
                    "name": product.name,
                    "active": product.active,
                }
            ),
            200,
        )

    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/create_subscription", methods=["POST"])
def create_subscription():
    """
    Create a new subscription in Stripe.
    ---
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        description: Subscription details
        required: true
        schema:
          type: object
          required:
            - customer_id
            - price_id
          properties:
            customer_id:
              type: string
              description: Customer ID to create the subscription for
            price_id:
              type: string
              description: Price ID to create the subscription for
    responses:
      200:
        description: Subscription created successfully
        schema:
          type: object
          properties:
            subscription_id:
              type: string
              description: ID of the created subscription
      400:
        description: Error with subscription creation (e.g., missing parameters, Stripe error)
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
    """
    try:
        data = request.get_json()
        customer_id = data["customer_id"]
        price_id = data["price_id"]

        missing, params = missing_params(["customer_id", "price_id"], data)
        if missing:
            return (
                jsonify({"error": MISSING_PARAMETERS, "missing_params": params}),
                400,
            )

        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            expand=["latest_invoice.payment_intent"],
        )

        return (
            jsonify(
                {
                    "subscription_id": subscription.id,
                    "status": subscription.status,
                    "invoice_id": subscription.latest_invoice.payment_intent.id,
                }
            ),
            200,
        )

    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/refund_payment", methods=["POST"])
def refund_payment():
    """
    Refund a payment in Stripe.
    ---
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        description: Payment intent ID to refund
        required: true
        schema:
          type: object
          required:
            - payment_intent_id
          properties:
            payment_intent_id:
              type: string
              description: Payment intent ID to refund
    responses:
      200:
        description: Payment refunded successfully
        schema:
          type: object
          properties:
            refund_id:
              type: string
              description: ID of the refunded payment
      400:
        description: Error with payment refund (e.g., missing parameters, Stripe error)
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
    """
    try:
        data = request.get_json()
        payment_intent_id = data["payment_intent_id"]

        missing, params = missing_params(["payment_intent_id"], data)
        if missing:
            return (
                jsonify({"error": MISSING_PARAMETERS, "missing_params": params}),
                400,
            )

        refund = stripe.Refund.create(payment_intent=payment_intent_id)

        return jsonify({"refund_id": refund.id, "status": refund.status}), 200

    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/update_billing_anchor", methods=["POST"])
def update_billing_anchor():
    """
    Update the billing anchor date of a subscription in Stripe.
    ---
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        description: Subscription details
        required: true
        schema:
          type: object
          required:
            - subscription_id
          properties:
            subscription_id:
              type: string
              description: Subscription ID to update
    responses:
      200:
        description: Subscription updated successfully
        schema:
          type: object
          properties:
            subscription_id:
              type: string
              description: ID of the updated subscription
      400:
        description: Error with subscription update (e.g., missing parameters, Stripe error)
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
    """
    try:
        data = request.get_json()
        subscription_id = data["subscription_id"]

        missing, params = missing_params(["subscription_id"], data)
        if missing:
            return (
                jsonify({"error": MISSING_PARAMETERS, "missing_params": params}),
                400,
            )

        updated_subscription = stripe.Subscription.modify(
            subscription_id,
            billing_cycle_anchor="now",
            proration_behavior="none",
        )

        return (
            jsonify(
                {
                    "subscription_id": updated_subscription.id,
                    "current_period_start": updated_subscription.current_period_start,
                    "current_period_end": updated_subscription.current_period_end,
                }
            ),
            200,
        )
    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/product_details", methods=["GET"])
def product_details():
    """
    Get the details of a product in Stripe.
    ---
    parameters:
      - in: query
        name: productId
        description: The ID of the product to retrieve details for
        required: true
        type: string
    responses:
      200:
        description: Product details retrieved successfully
        schema:
          type: object
          properties:
            product:
              type: object
              description: Product details
            prices:
              type: array
              items:
                type: object
                description: Price details
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
    """
    try:
        product_id = request.args.get("productId")
        if not product_id:
            return jsonify({"error": "Missing productId parameter"}), 400

        product = stripe.Product.retrieve(product_id)
        prices = stripe.Price.list(product=product_id, active=True)

        product_details = {
            "product": product,
            "prices": prices.data,
        }
        return jsonify(product_details), 200
    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/products", methods=["GET"])
def products_with_prices():
    """
    Get all products and their associated active prices in the account catalog.
    ---
    responses:
      200:
        description: Products and their active prices retrieved successfully
        schema:
          type: object
          additionalProperties:
            type: object
            properties:
              product:
                type: object
                description: Product details
              prices:
                type: array
                items:
                  type: object
                  description: Price details
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              description: Description of the error
    """
    try:
        products = stripe.Product.list(active=True)
        product_price_dict = {}

        for product in products:
            prices = stripe.Price.list(product=product.id, active=True)
            product_price_dict[product.id] = {
                "product": product,
                "prices": prices,
            }
        return jsonify(product_price_dict), 200
    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    """
    Handle the webhook from Stripe.
    ---
    responses:
      200:
        description: Webhook processed successfully
      400:
        description: Error with webhook processing (e.g., invalid payload, invalid signature)
      500:
        description: Internal server error
    """
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    endpoint_secret = os.getenv("FLASK_APP_STRIPE_WEBHOOK_KEY")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        print(f"Invalid Payload: {e}")
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError as e:
        print(f"Invalid signature: {e}")
        return "Invalid signature", 400

    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        print("PaymentIntent was successful!")
    elif event["type"] == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        print(f"PaymentIntent failed. {payment_intent}")

    return jsonify({"status": "success"}), 200


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    """
    Serve the React app.
    ---
    responses:
      200:
        description: React app served successfully
    """
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(debug=False)
