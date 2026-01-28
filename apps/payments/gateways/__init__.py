from .base import PaymentGateway
from .stripe_gateway import StripeGateway
from .paypal_gateway import PayPalGateway
from .momo_gateway import MoMoGateway
from .offline_gateway import OfflineGateway

GATEWAY_REGISTRY = {
    'STRIPE': StripeGateway,
    'PAYPAL': PayPalGateway,
    'MTN_MOMO': MoMoGateway,
    'ORANGE_MONEY': MoMoGateway,
    'OFFLINE': OfflineGateway,
}


def get_gateway(provider: str) -> PaymentGateway:
    gateway_class = GATEWAY_REGISTRY.get(provider)
    if not gateway_class:
        raise ValueError(f"Unknown payment provider: {provider}")
    return gateway_class()
