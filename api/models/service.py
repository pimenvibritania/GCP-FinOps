class Service:
    def __init__(self, name, cost_service_instance):
        self.name = name
        self.cost_service = list(cost_service_instance)

    def __str__(self):
        return self.name


class CostService:
    def __init__(
        self, environment, cost_this_week, cost_prev_week, cost_difference, cost_status
    ):
        self.environment = environment
        self.cost_this_week = cost_this_week
        self.cost_this_week_prev = cost_prev_week
        self.cost_difference = cost_difference
        self.cost_status = cost_status

    def __str__(self):
        return self.environment
