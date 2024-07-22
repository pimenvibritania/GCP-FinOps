from babel.numbers import format_currency, parse_decimal


class Conversion:

    @classmethod
    def convert_usd(cls, value, rate_idr):
        return format_currency((value / rate_idr), "USD", locale="en_US")
