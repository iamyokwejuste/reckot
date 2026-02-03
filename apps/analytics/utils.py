from decimal import Decimal

EXCHANGE_RATES = {
    'XAF': Decimal('0.00167'),
    'XOF': Decimal('0.00167'),
    'USD': Decimal('1.00'),
    'EUR': Decimal('1.08'),
    'GBP': Decimal('1.27'),
    'NGN': Decimal('0.0013'),
    'GHS': Decimal('0.083'),
    'UGX': Decimal('0.00027'),
}


def convert_to_usd(amount, currency='XAF'):
    if not amount:
        return Decimal('0.00')

    amount = Decimal(str(amount))
    rate = EXCHANGE_RATES.get(currency, Decimal('1.00'))

    return (amount * rate).quantize(Decimal('0.01'))


def format_currency_usd(amount):
    if not amount:
        return '$0.00'

    amount = Decimal(str(amount))
    return f'${amount:,.2f}'
