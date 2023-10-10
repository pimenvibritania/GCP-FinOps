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
    def get_percentage(cls, from_value, to_value) -> Union[float, str]:
        if to_value == 0:
            return "New"

        # percent = round(abs(min((from_value - to_value) / abs(to_value) * 100, 100)), 2)
        percent = round(((from_value - to_value) / to_value) * 100, 2)
        return 0.01 if percent == 0.00 else percent
