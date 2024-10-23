import calendar
from datetime import datetime


def count_days_in_month(date_str) -> int:
    # Parse the date string
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')

    # Extract year and month
    year = date_obj.year
    month = date_obj.month

    # Get the number of days in the month
    _, num_days = calendar.monthrange(year, month)

    return int(num_days)
