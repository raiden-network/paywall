import requests
from raiden.api.v1.encoding import EventPaymentReceivedSuccessSchema

from raiden_paywall.database import db_session
from raiden_paywall.models import Payment, PaymentState
from raiden_paywall.utils import to_absolute_amount

PaymentReceivedSchema = EventPaymentReceivedSuccessSchema()


def database_update_payments(raiden):
    session = db_session()
    try:
        awaited = Payment.create_filter(
            identifier=None, state=PaymentState.AWAITED
        ).with_for_update(of=Payment)
        if awaited.first():
            id_payment_map = {payment.identifier: payment for payment in awaited}
            for raiden_payment in raiden.iter_payments():
                payment = id_payment_map.get(int(raiden_payment["identifier"]))
                if payment:
                    if int(raiden_payment["amount"]) >= to_absolute_amount(
                        payment.amount, payment.token.decimals
                    ):
                        payment_received_event = PaymentReceivedSchema.make_object(
                            raiden_payment
                        )
                        payment.payment_event = payment_received_event
            session.commit()

    except Exception as e:
        print(f"There was an Error: {e}")
