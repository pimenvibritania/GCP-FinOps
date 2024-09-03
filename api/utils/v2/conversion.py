from babel.numbers import format_currency, parse_decimal


class Conversion:

    @classmethod
    def convert_usd(cls, value, rate_idr):
        return format_currency((value / rate_idr), "USD", locale="en_US")

    @classmethod
    def convert_idr(cls, value, rate_idr):
        return format_currency((value * rate_idr), "IDR", locale="id_ID")

    @classmethod
    def idr_format(cls, value):
        return format_currency(value, "IDR", locale="id_ID")

    @classmethod
    def usd_format(cls, value):
        return format_currency(value, "USD", locale="en_US")

    @classmethod
    def unpack_idr(cls, value):
        numeric_string = value.replace("Rp", "")
        numeric_string = parse_decimal(numeric_string, locale="id_ID")
        return float(numeric_string)

