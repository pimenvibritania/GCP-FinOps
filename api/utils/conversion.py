from typing import Union

from babel.numbers import format_currency, parse_decimal


class Conversion:
    @classmethod
    def unpack_idr(cls, value):
        numeric_string = value.replace("Rp", "")
        numeric_string = parse_decimal(numeric_string, locale="id_ID")
        return float(numeric_string)

    @classmethod
    def unpack_usd(cls, value):
        numeric_string = value.replace("USD", "").replace("$", "").strip()
        numeric_string = parse_decimal(numeric_string, locale="en_US")
        return float(numeric_string)

    @classmethod
    def idr_format(cls, value):
        return format_currency(value, "IDR", locale="id_ID")

    @classmethod
    def usd_format(cls, value):
        return format_currency(value, "USD", locale="en_US")

    @classmethod
    def convert_usd(cls, value, rate_idr):
        rate = cls.unpack_idr(rate_idr)
        return cls.usd_format(value / rate)

    @classmethod
    def get_percentage(cls, this_period, previous_period) -> Union[float, str]:
        if this_period == 0:
            return 0 if previous_period == 0 else 100
        percent = round(((this_period - previous_period) / previous_period) * 100, 2)
        return 0.01 if percent == 0.0 else percent
