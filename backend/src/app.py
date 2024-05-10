import logging
import os
from typing import List, Tuple

import stripe
from dotenv import load_dotenv
from flasgger import Swagger
from flask import Flask, jsonify, request

logger = logging.getLogger(__name__)

app = Flask(__name__)
swagger = Swagger(app)

load_dotenv()
stripe.api_key = os.getenv("STRIPE_API_KEY")
stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")


def missing_params(required_params, data) -> Tuple[bool, List[str]]:
    """
    Check if any required parameters are missing from the data.

    Args:
        required_params (list): The required parameters.
        data (dict): The data to check.

    Returns:
        Tuple[bool, List[str]]: A tuple containing a boolean indicating if any
        required parameters are missing and a list of missing parameters.
    """
    missing_params = [param for param in required_params if not data.get(param)]
    if missing_params:
        return True, missing_params
    return False, []


@app.route("/attach_payment_method", methods=["POST"])
def attach_payment_method():
    """
    Attach a payment method to a customer.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: AttachPaymentMethod
          required:
            - customer_id
            - payment_identifier
            - set_as_default
          properties:
            customer_id:
              type: string
              description: The ID of the customer to attach the payment method to.
            payment_identifier:
              type: string
              description: The ID of the payment method to attach.
            set_as_default:
              type: boolean
              description: Whether to set the payment method as the default for the customer.
    responses:
      200:
        description: Payment method attached successfully.
        schema:
          id: PaymentMethodResponse
          properties:
            payment_method_id:
              type: string
              description: The ID of the payment method.
    """
    try:
        data = request.get_json()
        customer_id = data["customer_id"]
        payment_identifier = data["payment_identifier"]
        set_as_default = data.get("set_as_default", False)

        missing, params = missing_params(["customer_id", "payment_identifier"], data)
        if missing:
            return (
                jsonify(
                    {"error": "Missing required parameters", "missing_params": params}
                ),
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


@app.route("/authorize_charge", methods=["POST"])
def authorize_charge():
    """
    Authorize a charge for a customer.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: AuthorizeCharge
          required:
            - amount
            - customer_id
            - payment_method_id
          properties:
            amount:
              type: integer
              description: The amount to charge the customer in cents.
            currency:
              type: string
              default: USD
              description: The currency to charge the customer in.
            customer_id:
              type: string
              description: The ID of the customer to charge.
            payment_method_id:
              type: string
              description: The ID of the payment method to charge.
            payment_method_types:
              type: array
              items:
                type: string
              description: The types of payment methods to charge.
            description:
              type: string
              description: The description of the charge.
            metadata:
              type: object
              description: The metadata to attach to the charge.
    responses:
      200:
        description: Charge authorized successfully.
        schema:
          id: PaymentIntentResponse
          properties:
            payment_intent_id:
              type: string
              description: The ID of the payment intent.
    """
    data = request.get_json()
    data["capture_method"] = "manual"

    response = create_payment_intent()
    return response


@app.route("/capture_charge", methods=["POST"])
def capture_charge():
    """
    Capture a charge for a customer.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: CaptureCharge
          required:
            - payment_intent_id
          properties:
            payment_intent_id:
              type: string
              description: The ID of the payment intent to capture.
    responses:
        200:
            description: Charge captured successfully.
            schema:
            id: CaptureResponse
            properties:
                payment_intent_id:
                type: string
                description: The ID of the payment intent.
                status:
                type: string
                description: The status of the payment intent.
                amount_captured:
                type: integer
                description: The amount captured in cents.
    """
    try:
        data = request.get_json()
        payment_intent_id = data["payment_intent_id"]

        missing, params = missing_params(["payment_intent_id"], data)
        if missing:
            return (
                jsonify(
                    {"error": "Missing required parameters", "missing_params": params}
                ),
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


@app.route("/complete_charge", methods=["POST"])
def complete_charge():
    """
    Complete a charge for a customer.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: CompleteCharge
          required:
            - payment_intent_id
          properties:
            payment_intent_id:
              type: string
              description: The ID of the payment intent to complete.
    responses:
        200:
            description: Charge completed successfully.
            schema:
            id: CompleteResponse
            properties:
                payment_intent_id:
                type: string
                description: The ID of the payment intent.
                status:
                type: string
                description: The status of the payment intent.
                amount_captured:
                type: integer
                description: The amount captured in cents.
    """
    data = request.get_json()
    data["capture_method"] = "automatic"
    response = create_payment_intent()
    return response


@app.route("/create_customer", methods=["POST"])
def create_customer():
    """
    Create a customer.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: CreateCustomer
          required:
            - name
            - email
          properties:
            name:
              type: string
              description: The name of the customer.
            email:
              type: string
              description: The email of the customer.
    responses:
        200:
            description: Customer created successfully.
            schema:
            id: CustomerResponse
            properties:
                customer_id:
                type: string
                description: The ID of the customer.
    """
    try:
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")

        missing, params = missing_params(["name", "email"], data)
        if missing:
            return (
                jsonify(
                    {"error": "Missing required parameters", "missing_params": params}
                ),
                400,
            )

        customer = stripe.Customer.create(name=name, email=email)

        return jsonify({"customer_id": customer.id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/create_payment_intent", methods=["POST"])
def create_payment_intent():
    """
    Create a payment intent for a customer.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: CreatePaymentIntent
          required:
            - amount
            - customer_id
            - payment_method_id
          properties:
            amount:
              type: integer
              description: The amount to charge the customer in cents.
            currency:
              type: string
              default: USD
              description: The currency to charge the customer in.
            customer_id:
              type: string
              description: The ID of the customer to charge.
            payment_method_id:
              type: string
              description: The ID of the payment method to charge.
            payment_method_types:
              type: array
              items:
                type: string
              description: The types of payment methods to charge.
            description:
              type: string
              description: The description of the charge.
            metadata:
              type: object
              description: The metadata to attach to the charge.
            capture_method:
              type: string
              default: automatic
              description: The method to capture the charge.
    responses:
        200:
            description: Payment intent created successfully.
            schema:
            id: PaymentIntentResponse
            properties:
                payment_intent_id:
                type: string
                description: The ID of the payment intent.
                client_secret:
                type: string
                description: The client secret of the payment intent.
    """
    try:
        data = request.get_json()
        amount = data["amount"]
        currency = data.get("currency", "usd")
        customer_id = data.get("customer_id", None)
        payment_method_id = data.get("payment_method_id", None)
        payment_method_types = data.get("payment_method_types", ["card"])
        description = data.get("description", "")
        metadata = data.get("metadata", {})
        capture_method = data.get("capture_method", "automatic")

        missing, params = missing_params(
            ["amount", "customer_id", "payment_method_id"], data
        )
        if missing:
            return (
                jsonify(
                    {"error": "Missing required parameters", "missing_params": params}
                ),
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


@app.route("/create_price", methods=["POST"])
def create_price():
    """
    Create a price for a product.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: CreatePrice
          required:
            - product_id
            - unit_amount
          properties:
            product_id:
              type: string
              description: The ID of the product to create the price for.
            unit_amount:
              type: integer
              description: The unit amount to charge the customer in cents.
            currency:
              type: string
              default: USD
              description: The currency to charge the customer in.
    responses:
        200:
            description: Price created successfully.
            schema:
            id: PriceResponse
            properties:
                price_id:
                type: string
                description: The ID of the price.
    """
    try:
        data = request.get_json()
        product_id = data["product_id"]
        unit_amount = data["unit_amount"]
        currency = data.get("currency", "usd")

        missing, params = missing_params(["product_id", "unit_amount"], data)
        if missing:
            return (
                jsonify(
                    {"error": "Missing required parameters", "missing_params": params}
                ),
                400,
            )

        price = stripe.Price.create(
            product=product_id, unit_amount=unit_amount, currency=currency
        )
        return jsonify({"price_id": price.id}), 200
    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/create_product", methods=["POST"])
def create_product():
    """
    Create a product.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: CreateProduct
          required:
            - name
          properties:
            name:
              type: string
              description: The name of the product.
            description:
              type: string
              description: The description of the product.
            active:
              type: boolean
              default: true
              description: Whether the product is active.
    responses:
        200:
            description: Product created successfully.
            schema:
            id: ProductResponse
            properties:
                product_id:
                type: string
                description: The ID of the product.
                name:
                type: string
                description: The name of the product.
                active:
                type: boolean
                description: Whether the product is active.
    """
    try:
        data = request.get_json()
        name = data["name"]
        description = data.get("description", "")
        active = data.get("active", True)

        missing, params = missing_params(["name"], data)
        if missing:
            return (
                jsonify(
                    {"error": "Missing required parameters", "missing_params": params}
                ),
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


@app.route("/create_subscription", methods=["POST"])
def create_subscription():
    """
    Create a subscription for a customer.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: CreateSubscription
          required:
            - customer_id
            - price_id
          properties:
            customer_id:
              type: string
              description: The ID of the customer to create the subscription for.
            price_id:
              type: string
              description: The ID of the price to subscribe to.
    responses:
        200:
            description: Subscription created successfully.
            schema:
            id: SubscriptionResponse
            properties:
                subscription_id:
                type: string
                description: The ID of the subscription.
                status:
                type: string
                description: The status of the subscription.
                invoice_id:
                type: string
                description: The ID of the invoice.
    """
    try:
        data = request.get_json()
        customer_id = data["customer_id"]
        price_id = data["price_id"]

        missing, params = missing_params(["customer_id", "price_id"], data)
        if missing:
            return (
                jsonify(
                    {"error": "Missing required parameters", "missing_params": params}
                ),
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


@app.route("/refund_payment", methods=["POST"])
def refund_payment():
    """
    Refund a payment for a customer.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: RefundPayment
          required:
            - payment_intent_id
          properties:
            payment_intent_id:
              type: string
              description: The ID of the payment intent to refund.
    responses:
        200:
            description: Payment refunded successfully.
            schema:
            id: RefundResponse
            properties:
                refund_id:
                type: string
                description: The ID of the refund.
                status:
                type: string
                description: The status of the refund.
    """
    try:
        data = request.get_json()
        payment_intent_id = data["payment_intent_id"]

        missing, params = missing_params(["payment_intent_id"], data)
        if missing:
            return (
                jsonify(
                    {"error": "Missing required parameters", "missing_params": params}
                ),
                400,
            )

        refund = stripe.Refund.create(payment_intent=payment_intent_id)

        return jsonify({"refund_id": refund.id, "status": refund.status}), 200

    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/update_billing_anchor", methods=["POST"])
def update_billing_anchor():
    """
    Update the billing anchor date for a subscription.

    Args:
        subscription_id (str): The ID of the subscription to update.
        billing_anchor_date (str): The date to anchor the billing on.

    Returns:
        subscription_id (str): The ID of the subscription.
        current_period_start (int): The start of the current period.
        current_period_end (int): The end of the current period.
    """
    """
    Update the billing anchor date for a subscription.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: UpdateBillingAnchor
          required:
            - subscription_id
            - billing_anchor_date
          properties:
            subscription_id:
              type: string
              description: The ID of the subscription to update.
            billing_anchor_date:
              type: integer
              description: The date to anchor the billing on.
    responses:
        200:
            description: Billing anchor updated successfully.
            schema:
            id: BillingAnchorResponse
            properties:
                subscription_id:
                type: string
                description: The ID of the subscription.
                current_period_start:
                type: integer
                description: The start of the current period.
                current_period_end:
                type: integer
                description: The end of the current period.
    """
    try:
        data = request.get_json()
        subscription_id = data["subscription_id"]
        billing_anchor_date = data["billing_anchor_date"]

        missing, params = missing_params(
            ["subscription_id", "billing_anchor_date"], data
        )
        if missing:
            return (
                jsonify(
                    {"error": "Missing required parameters", "missing_params": params}
                ),
                400,
            )

        updated_subscription = stripe.Subscription.modify(
            subscription_id,
            billing_cycle_anchor=billing_anchor_date,
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


if __name__ == "__main__":
    app.run(debug=False)
