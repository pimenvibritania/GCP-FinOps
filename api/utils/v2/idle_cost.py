from api.utils.conversion import Conversion


def get_idle_cost(idle_data, index_weight):
    table_template_idle_cost = """
            <table>
            <thead>
                <tr>
                    <th>Cluster Name</th>
                    <th>Project</th>
                    <th>Environment</th>
                    <th>Cost This period</th>
                    <th>Cost Previous period</th>
                    <th style="width:75px">Status Cost</th>
                </tr>
            </thead>
            <tbody>
    """
    total_current_idle_cost = 0
    total_previous_idle_cost = 0

    for item in idle_data:
        project = item["project"]
        cluster_name = item["cluster_name"]
        environment = item["environment"]
        iw = index_weight[environment]
        cost_this_period = item["cost_this_period"] * (iw / 100)
        cost_prev_period = item["cost_prev_period"] * (iw / 100)
        total_current_idle_cost += cost_this_period
        total_previous_idle_cost += cost_prev_period
        percentage_period_idle = Conversion.get_percentage(
            cost_this_period, cost_prev_period
        )

        if item["cost_this_period"] > item["cost_prev_period"]:
            cost_status_idle = f"""<span style="color:#e74c3c">⬆ {percentage_period_idle}%</span>"""
        elif item["cost_this_period"] < item["cost_prev_period"]:
            cost_status_idle = f"""<span style="color:#1abc9c">⬇ {percentage_period_idle}%</span>"""
        else:
            cost_status_idle = """Equal"""

        table_template_idle_cost += f"""
            <tr>
                <td>{cluster_name}</td>
                <td>{project}</td>
                <td>{environment}</td>
                <td>{Conversion.usd_format(cost_this_period)} USD</td>
                <td>{Conversion.usd_format(cost_prev_period)} USD</td>
                <td>{cost_status_idle}</td>
            </tr>
        """

    table_template_idle_cost += """
        </tbody></table>
    """

    total_percentage_period_idle = Conversion.get_percentage(
        total_current_idle_cost, total_previous_idle_cost
    )

    if total_current_idle_cost > total_previous_idle_cost:
        cost_total_status_idle = (
            f"""<span style="color:#e74c3c">⬆ {total_percentage_period_idle}%</span>"""
        )
    elif total_current_idle_cost < total_previous_idle_cost:
        cost_total_status_idle = (
            f"""<span style="color:#1abc9c">⬇ {total_percentage_period_idle}%</span>"""
        )
    else:
        cost_total_status_idle = """Equal"""

    return {
        "table_idle_cost": table_template_idle_cost,
        "total_current_idle_cost": Conversion.usd_format(total_current_idle_cost),
        "total_previous_idle_cost": Conversion.usd_format(total_previous_idle_cost),
        "cost_total_status_idle": cost_total_status_idle,
    }
