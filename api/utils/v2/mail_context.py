from api.utils.conversion import Conversion
from api.utils.v2.conversion import Conversion as ConversionV2


class MailContext:

    # Function to generate GCP cost context for email
    @staticmethod
    async def gcp_context(gcp_data, conversion_rate):
        gcp_context = {}

        """
            Formatting table and data for GCP Cost
        """
        current_total_idr_gcp = gcp_data["__summary"][
            "current_cost"
        ]
        previous_total_idr_gcp = gcp_data["__summary"][
            "previous_cost"
        ]
        current_rate_gcp = conversion_rate["current"]
        previous_rate_gcp = conversion_rate["previous"]
        cost_difference_idr_gcp = current_total_idr_gcp - previous_total_idr_gcp
        percent_status_gcp = Conversion.get_percentage(
            current_total_idr_gcp, previous_total_idr_gcp
        )
        ranged_cost_period = gcp_data["__summary"]["usage_date"]
        current_cost_period = gcp_data["__summary"]["usage_date_current"]
        previous_cost_period = gcp_data["__summary"]["usage_date_previous"]

        # Determine cost status for GCP
        if current_total_idr_gcp > previous_total_idr_gcp:
            cost_status_gcp = (
                f"""<span style="color:#e74c3c">⬆ {percent_status_gcp}%</span>"""
            )
        elif current_total_idr_gcp < previous_total_idr_gcp:
            cost_status_gcp = (
                f"""<span style="color:#1abc9c">⬇ {percent_status_gcp}%</span>"""
            )
        else:
            cost_status_gcp = """<strong><span style="font-size:16px">Equal&nbsp;</span></strong>"""

        # Initialize HTML table template for GCP cost details
        table_template_gcp = """
                    <table>
                        <thead>
                            <tr>
                                <th style="width:160px">Service</th>
                                <th>GCP Project</th>
                                <th>Environment</th>
                                <th>Current IDR</th>
                                <th>Current USD</th>
                                <th>Previous IDR</th>
                                <th>Previous USD</th>
                                <th style="width:75px">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                """

        # Loop through services in GCP data and populate the table
        for service in gcp_data:
            if service == "__summary":
                continue

            services = gcp_data[service]

            for index, environment in enumerate(services):
                current_service_cost_period = services[environment]["current_cost"]
                previous_service_cost_period = services[environment]["previous_cost"]
                percent_status_service = Conversion.get_percentage(
                    current_service_cost_period, previous_service_cost_period
                )
                gcp_project = services[environment]["gcp_project"]
                if index == 0:
                    tr_first = f"""
                                <tr>
                                    <td class="centered-text" rowspan="{len(gcp_data[service])}">{service}</td>
                            """
                else:
                    tr_first = "<tr>"

                if current_service_cost_period > previous_service_cost_period:
                    cost_status_service_gcp = f"""<span style="color:#e74c3c">⬆ {percent_status_service}%</span>"""
                elif current_service_cost_period < previous_service_cost_period:
                    cost_status_service_gcp = f"""<span style="color:#1abc9c">⬇ {percent_status_service}%</span>"""
                else:
                    cost_status_service_gcp = """Equal"""

                row = f"""
                            {tr_first}
                                <td>{gcp_project}</td>
                                <td>{environment}</td>
                                <td>{Conversion.idr_format(current_service_cost_period)}</td>
                                <td>{ConversionV2.convert_usd(current_service_cost_period, current_rate_gcp)} USD</td>
                                <td>{Conversion.idr_format(previous_service_cost_period)}</td>
                                <td>{ConversionV2.convert_usd(previous_service_cost_period, previous_rate_gcp)} USD</td>
                                <td>{cost_status_service_gcp}</td>
                            </tr>
                        """

                table_template_gcp += row

        table_template_gcp += "</tbody>\n</table>"

        # Create the context dictionary for GCP cost data
        context_gcp = {
            "cost_status_gcp": cost_status_gcp,
            "ranged_cost_period": ranged_cost_period,
            "current_cost_period": current_cost_period,
            "previous_cost_period": previous_cost_period,
            "total_cost_this_period": current_total_idr_gcp,
            "previous_total_idr_gcp": Conversion.idr_format(previous_total_idr_gcp),
            "previous_total_usd_gcp": ConversionV2.convert_usd(
                previous_total_idr_gcp, previous_rate_gcp
            ),
            "current_total_idr_gcp": Conversion.idr_format(current_total_idr_gcp),
            "current_total_usd_gcp": ConversionV2.convert_usd(
                current_total_idr_gcp, current_rate_gcp
            ),
            "current_rate_gcp": current_rate_gcp,
            "cost_difference_idr_gcp": Conversion.idr_format(
                cost_difference_idr_gcp
            ),
            "cost_difference_usd_gcp": ConversionV2.convert_usd(
                cost_difference_idr_gcp, current_rate_gcp
            ),
            "services_gcp": table_template_gcp,
            "gcp_exist": True,
        }

        gcp_context.update(context_gcp)

        return gcp_context

    # Function to generate Kubecost context for email
    @staticmethod
    async def kubecost_context(kubecost_payload):
        table_template_kubecost = """
                        <table>
                            <thead>
                                <tr>
                                    <th>Service Name</th>
                                    <th>Service Environment</th>
                                    <th>Cost This period</th>
                                    <th>Date</th>
                                    <th>Cost Previous period</th>
                                    <th style="width:75px">Status Cost</th>
                                </tr>
                            </thead>
                            <tbody>
                    """

        previous_total_usd_kubecost = kubecost_payload["data"]["summary"][
            "cost_prev_period"
        ]
        current_total_usd_kubecost = kubecost_payload["data"]["summary"][
            "cost_this_period"
        ]

        cost_summary_kubecost = current_total_usd_kubecost - previous_total_usd_kubecost
        percent_status_kubecost = Conversion.get_percentage(
            current_total_usd_kubecost, previous_total_usd_kubecost
        )

        # Determine cost status for Kubecost
        if kubecost_payload["data"]["summary"]["cost_status"] == "UP":
            cost_status_kubecost = (
                f"""<span style="color:#e74c3c">⬆ {percent_status_kubecost}%</span>"""
            )
        elif kubecost_payload["data"]["summary"]["cost_status"] == "DOWN":
            cost_status_kubecost = (
                f"""<span style="color:#1abc9c">⬇ {percent_status_kubecost}%</span>"""
            )
        else:
            cost_status_kubecost = """Equal"""

        # Loop through services in Kubecost data and populate the table
        for item in kubecost_payload["data"]["services"]:
            percentage_period_kubecost = Conversion.get_percentage(
                item["cost_this_period"], item["cost_prev_period"]
            )

            if item["cost_status"].upper() == "UP":
                cost_status_service_kubecost = f"""<span style="color:#e74c3c">⬆ {percentage_period_kubecost}%</span>"""
            elif item["cost_status"].upper() == "DOWN":
                cost_status_service_kubecost = f"""<span style="color:#1abc9c">⬇ {percentage_period_kubecost}%</span>"""
            else:
                cost_status_service_kubecost = """Equal"""

            table_template_kubecost += f"""
                            <tr>
                                <td>{item["service_name"].upper()}</td>
                                <td>{item["environment"]}</td>
                                <td>{Conversion.usd_format(item["cost_this_period"])} USD</td>
                                <td>{kubecost_payload["data"]["date"]}</td>
                                <td>{Conversion.usd_format(item["cost_prev_period"])} USD</td>
                                <td>{cost_status_service_kubecost}</td>
                            </tr>
                        """
        table_template_kubecost += """
                        </tbody></table>
                    """

        # Create the context dictionary for Kubecost data
        context_kubecost = {
            "previous_total_usd_kubecost": Conversion.usd_format(
                previous_total_usd_kubecost
            ),
            "current_total_usd_kubecost": Conversion.usd_format(
                current_total_usd_kubecost
            ),
            "cost_summary_kubecost": Conversion.usd_format(cost_summary_kubecost),
            "services_kubecost": table_template_kubecost,
            "cost_status_kubecost": cost_status_kubecost,
        }

        return context_kubecost
