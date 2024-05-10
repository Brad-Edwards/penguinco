# nosec
import json
from unittest.mock import patch

import pytest
import stripe

from backend.src.app import app


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


class TestAttachPaymentMethod:
    @patch("stripe.PaymentMethod.create")
    @patch("stripe.PaymentMethod.attach")
    @patch("stripe.Customer.modify")
    def test_attach_payment_method_success(
        self, mock_modify, mock_attach, mock_create, client
    ):
        mock_create.return_value = {"id": "pm_123"}
        mock_attach.return_value = None
        mock_modify.return_value = None

        data = {
            "customer_id": "cus_123",
            "payment_identifier": "tok_visa",
            "set_as_default": True,
        }

        response = client.post("/attach_payment_method", json=data)
        assert response.status_code == 200
        assert json.loads(response.data)["payment_method_id"] == "pm_123"

    @patch("stripe.PaymentMethod.create")
    def test_attach_payment_method_with_existing_id(self, mock_create, client):
        mock_create.return_value = {"id": "pm_123"}

        data = {"customer_id": "cus_123", "payment_identifier": "pm_123"}

        response = client.post("/attach_payment_method", json=data)
        assert response.status_code == 400

    @patch("stripe.PaymentMethod.create")
    @patch("stripe.PaymentMethod.attach")
    def test_attach_payment_method_stripe_error(self, mock_attach, mock_create, client):
        mock_create.return_value = {"id": "pm_123"}
        mock_attach.side_effect = stripe.error.StripeError("An error occurred")

        data = {"customer_id": "cus_123", "payment_identifier": "tok_visa"}

        response = client.post("/attach_payment_method", json=data)
        assert response.status_code == 400
        assert "error" in json.loads(response.data)

    def test_attach_payment_method_invalid_data(self, client):
        # Test data missing customer_id
        data = {"payment_identifier": "tok_visa"}

        response = client.post("/attach_payment_method", json=data)
        assert response.status_code == 500
        assert "error" in json.loads(response.data)

    @patch("stripe.PaymentMethod.create")
    @patch("stripe.PaymentMethod.attach")
    def test_attach_payment_method_exception(self, mock_attach, mock_create, client):
        # Simulate an unexpected exception
        mock_create.side_effect = Exception("Unexpected error")

        data = {"customer_id": "cus_123", "payment_identifier": "tok_visa"}

        response = client.post("/attach_payment_method", json=data)
        assert response.status_code == 500
        assert "error" in json.loads(response.data)


class TestAuthorizeCharge:
    @patch("stripe.PaymentMethod.create")
    @patch("stripe.PaymentMethod.attach")
    @patch("stripe.Customer.modify")
    def test_authorize_charge_success(
        self, mock_modify, mock_attach, mock_create, client
    ):
        mock_create.return_value = {"id": "pm_123"}
        mock_attach.return_value = None
        mock_modify.return_value = None

        data = {
            "customer_id": "cus_123",
            "payment_identifier": "tok_visa",
            "set_as_default": True,
        }

        response = client.post("/attach_payment_method", json=data)
        assert response.status_code == 200
        assert json.loads(response.data)["payment_method_id"] == "pm_123"

        def test_authorize_charge_missing_data(self, client):
            data = {}

            response = client.post("/authorize_charge", json=data)
            assert response.status_code == 400
            assert "error" in json.loads(response.data)

        def test_authorize_charge_invalid_payment_method(self, client):
            data = {"customer_id": "cus_123", "payment_identifier": "invalid_token"}

            response = client.post("/authorize_charge", json=data)
            assert response.status_code == 400
            assert "error" in json.loads(response.data)

        def test_authorize_charge_success(self, client):
            data = {"customer_id": "cus_123", "payment_identifier": "tok_visa"}

            response = client.post("/authorize_charge", json=data)
            assert response.status_code == 200
            assert "payment_intent_id" in json.loads(response.data)

        def test_authorize_charge_exception(self, client):
            with patch("backend.src.app.create_payment_intent") as mock_create:
                mock_create.side_effect = Exception("Unexpected error")
                data = {"customer_id": "cus_123", "payment_identifier": "tok_visa"}

                response = client.post("/authorize_charge", json=data)
                assert response.status_code == 500
                assert "error" in json.loads(response.data)


class TestCaptureCharge:
    def test_capture_charge_missing_data(self, client):
        data = {}

        response = client.post("/capture_charge", json=data)
        assert response.status_code == 500
        assert "error" in json.loads(response.data)

    def test_capture_charge_invalid_payment_intent(self, client):
        data = {"payment_intent_id": "invalid_intent"}

        response = client.post("/capture_charge", json=data)
        assert response.status_code == 400
        assert "error" in json.loads(response.data)

    @patch("stripe.PaymentIntent.capture")
    def test_capture_charge_success(self, mock_capture, client):
        # Setup mock
        mock_capture.return_value = stripe.PaymentIntent.construct_from(
            {"id": "pi_123", "status": "succeeded", "amount_received": 1000},
            "sk_test_123",
        )

        # Test data and call
        data = {"payment_intent_id": "pi_123"}
        response = client.post("/capture_charge", json=data)

        # Assertions
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["payment_intent_id"] == "pi_123"
        assert response_data["status"] == "succeeded"
        assert "amount_captured" in response_data
        assert response_data["amount_captured"] > 0

    def test_capture_charge_exception(self, client):
        with patch("backend.src.app.stripe.PaymentIntent.capture") as mock_capture:
            mock_capture.side_effect = Exception("Unexpected error")
            data = {"payment_intent_id": "pi_123"}

            response = client.post("/capture_charge", json=data)
            assert response.status_code == 500
            assert "error" in json.loads(response.data)


class TestCreateCustomer:
    def test_create_customer_missing_data(self, client):
        data = {}

        response = client.post("/create_customer", json=data)
        assert response.status_code == 400
        assert "error" in json.loads(response.data)

    def test_create_customer_success(self, client):
        data = {"name": "John Doe", "email": "john.doe@example.com"}

        response = client.post("/create_customer", json=data)
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert "customer_id" in response_data
        assert response_data["customer_id"] is not None

    def test_create_customer_exception(self, client):
        with patch("backend.src.app.stripe.Customer.create") as mock_create:
            mock_create.side_effect = Exception("Unexpected error")
            data = {"name": "Jane Doe", "email": "jane.doe@example.com"}

            response = client.post("/create_customer", json=data)
            assert response.status_code == 400
            assert "error" in json.loads(response.data)


class TestCreatePaymentIntent:
    def test_create_payment_intent_missing_data(self, client):
        data = {"amount": 1000}

        response = client.post("/create_payment_intent", json=data)
        assert response.status_code == 400
        assert "error" in json.loads(response.data)

    @patch("stripe.PaymentIntent.capture")
    def test_capture_charge_success(self, mock_capture, client):
        mock_capture.return_value = stripe.PaymentIntent.construct_from(
            {"id": "pi_123", "status": "succeeded", "amount_received": 1000},
            "sk_test_123",
        )

        data = {"payment_intent_id": "pi_123"}
        response = client.post("/capture_charge", json=data)

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["payment_intent_id"] == "pi_123"
        assert response_data["status"] == "succeeded"
        assert "amount_captured" in response_data
        assert response_data["amount_captured"] > 0

    def test_create_payment_intent_exception(self, client):
        with patch("backend.src.app.stripe.PaymentIntent.create") as mock_create:
            mock_create.side_effect = Exception("Unexpected error")
            data = {
                "amount": 1000,
                "currency": "usd",
                "customer_id": "cus_123",
                "payment_method_id": "pm_123",
            }

            response = client.post("/create_payment_intent", json=data)
            assert response.status_code == 500
            assert "error" in json.loads(response.data)


class TestCreatePrice:
    @patch("stripe.Price.create")
    def test_create_price_success(self, mock_create, client):
        mock_create.return_value = stripe.Price.construct_from(
            {
                "id": "price_123",
                "product": "prod_123",
                "unit_amount": 2000,
                "currency": "usd",
            },
            "sk_test_123",
        )

        data = {"product_id": "prod_123", "unit_amount": 2000, "currency": "usd"}

        response = client.post("/create_price", json=data)
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["price_id"] == "price_123"

    @patch("stripe.Price.create")
    def test_create_price_failure(self, mock_create, client):
        mock_create.side_effect = stripe.error.StripeError("Failed to create price")
        data = {"product_id": "prod_123", "unit_amount": 2000, "currency": "usd"}

        response = client.post("/create_price", json=data)
        assert response.status_code == 500
        assert "error" in json.loads(response.data)

    @patch("stripe.Price.create")
    def test_create_price_exception(self, mock_create, client):
        mock_create.side_effect = Exception("Unexpected error")
        data = {"product_id": "prod_123", "unit_amount": 2000, "currency": "usd"}

        response = client.post("/create_price", json=data)
        assert response.status_code == 500
        assert "error" in json.loads(response.data)


class TestCreateProduct:
    @patch("stripe.Product.create")
    def test_create_product_success(self, mock_create, client):
        mock_create.return_value = stripe.Product.construct_from(
            {"id": "prod_456", "name": "Test Product", "active": True}, "sk_test_123"
        )

        data = {
            "name": "Test Product",
            "description": "A product for testing",
            "active": True,
        }

        response = client.post("/create_product", json=data)
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["product_id"] == "prod_456"
        assert response_data["name"] == "Test Product"
        assert response_data["active"] is True

    @patch("stripe.Product.create")
    def test_create_product_failure(self, mock_create, client):
        mock_create.side_effect = stripe.error.StripeError("Failed to create product")
        data = {
            "name": "Test Product",
            "description": "A product for testing",
            "active": True,
        }

        response = client.post("/create_product", json=data)
        assert response.status_code == 400
        assert "error" in json.loads(response.data)

    @patch("stripe.Product.create")
    def test_create_product_exception(self, mock_create, client):
        mock_create.side_effect = Exception("Unexpected error")
        data = {
            "name": "Test Product",
            "description": "A product for testing",
            "active": True,
        }

        response = client.post("/create_product", json=data)
        assert response.status_code == 500
        assert "error" in json.loads(response.data)


class TestCreateSubscription:
    @patch("stripe.Subscription.create")
    def test_create_subscription_success(self, mock_create, client):
        mock_create.return_value = stripe.Subscription.construct_from(
            {
                "id": "sub_123",
                "status": "active",
                "latest_invoice": {"payment_intent": {"id": "pi_123"}},
            },
            "sk_test_123",
        )

        data = {"customer_id": "cus_123", "price_id": "price_123"}

        response = client.post("/create_subscription", json=data)
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["subscription_id"] == "sub_123"
        assert response_data["status"] == "active"
        assert response_data["invoice_id"] == "pi_123"

    @patch("stripe.Subscription.create")
    def test_create_subscription_stripe_error(self, mock_create, client):
        mock_create.side_effect = stripe.error.StripeError(
            "Failed to create subscription"
        )

        data = {"customer_id": "cus_123", "price_id": "price_123"}

        response = client.post("/create_subscription", json=data)
        assert response.status_code == 400
        assert "error" in json.loads(response.data)

    @patch("stripe.Subscription.create")
    def test_create_subscription_exception(self, mock_create, client):
        mock_create.side_effect = Exception("Unexpected error")

        data = {"customer_id": "cus_123", "price_id": "price_123"}

        response = client.post("/create_subscription", json=data)
        assert response.status_code == 500
        assert "error" in json.loads(response.data)


class TestRefundPayment:
    @patch("stripe.Refund.create")
    def test_refund_payment_success(self, mock_refund, client):
        mock_refund.return_value = stripe.Refund.construct_from(
            {"id": "rf_123", "status": "succeeded"}, "sk_test_123"
        )

        data = {"payment_intent_id": "pi_123"}

        response = client.post("/refund_payment", json=data)
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["refund_id"] == "rf_123"
        assert response_data["status"] == "succeeded"

    @patch("stripe.Refund.create")
    def test_refund_payment_stripe_error(self, mock_refund, client):
        mock_refund.side_effect = stripe.error.StripeError("Failed to create refund")

        data = {"payment_intent_id": "pi_123"}

        response = client.post("/refund_payment", json=data)
        assert response.status_code == 400
        assert "error" in json.loads(response.data)

    @patch("stripe.Refund.create")
    def test_refund_payment_exception(self, mock_refund, client):
        mock_refund.side_effect = Exception("Unexpected error")

        data = {"payment_intent_id": "pi_123"}

        response = client.post("/refund_payment", json=data)
        assert response.status_code == 500
        assert "error" in json.loads(response.data)


class TestUpdateBillingAnchor:
    @patch("stripe.Subscription.modify")
    def test_update_billing_anchor_success(self, mock_modify, client):
        mock_modify.return_value = stripe.Subscription.construct_from(
            {
                "id": "sub_123",
                "current_period_start": 1609459200,
                "current_period_end": 1612137600,
            },
            "sk_test_123",
        )

        data = {"subscription_id": "sub_123", "billing_anchor_date": 1609459200}

        response = client.post("/update_billing_anchor", json=data)
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["subscription_id"] == "sub_123"
        assert response_data["current_period_start"] == 1609459200
        assert response_data["current_period_end"] == 1612137600

    @patch("stripe.Subscription.modify")
    def test_update_billing_anchor_stripe_error(self, mock_modify, client):
        mock_modify.side_effect = stripe.error.StripeError(
            "Failed to update billing anchor"
        )

        data = {"subscription_id": "sub_123", "billing_anchor_date": 1609459200}

        response = client.post("/update_billing_anchor", json=data)
        assert response.status_code == 400
        assert "error" in json.loads(response.data)

    @patch("stripe.Subscription.modify")
    def test_update_billing_anchor_exception(self, mock_modify, client):
        mock_modify.side_effect = Exception("Unexpected error")

        data = {"subscription_id": "sub_123", "billing_anchor_date": 1609459200}

        response = client.post("/update_billing_anchor", json=data)
        assert response.status_code == 500
        assert "error" in json.loads(response.data)
