from datetime import datetime, timedelta


class Date:
    @classmethod
    def get_date_range(cls, input_date, period):
        est_date = datetime.strptime(input_date, "%Y-%m-%d")
        current_week = previous_week = datetime
        if period == "weekly":
            current_week = est_date - timedelta(days=6)
            previous_week = current_week - timedelta(days=7)
        elif period == "monthly":
            current_week = est_date - timedelta(days=29)
            previous_week = current_week - timedelta(days=30)

        current_week_to = current_week - timedelta(days=1)

        f_current_week = current_week.strftime("%Y-%m-%d")
        f_current_week_to = current_week_to.strftime("%Y-%m-%d")
        f_previous_week = previous_week.strftime("%Y-%m-%d")

        current_week_from = f_current_week
        current_week_to = input_date
        previous_week_from = f_previous_week
        previous_week_to = f_current_week_to

        return current_week_from, current_week_to, previous_week_from, previous_week_to
