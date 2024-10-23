def merge_gcp_cost(data) -> dict:
    defi = ["defi_mdi", "defi_mfi"]
    platform = ["platform_mdi", "platform_mfi"]
    merged_tf = defi + platform

    result = {
        "defi": {},
        "platform": {},
        "mofi": {},
        "dana_tunai": {},
    }

    for billing, billing_value in data.items():
        for tech_family, tech_services in billing_value.items():
            if tech_family == "__summary" or tech_family == "index_weight" or tech_family == "conversion_rate":
                continue

            if tech_family in defi:
                section = "defi"
            elif tech_family in platform:
                section = "platform"
            else:
                section = tech_family

            for services, environment_value in tech_services.items():
                if not result[section].get(services):
                    result[section][services] = {}

                if services == "__summary":
                    if tech_family not in merged_tf:
                        result[tech_family][services] = environment_value
                    else:
                        if not result[section].get(services):
                            result[section][services] = environment_value
                            result[section][services]["name"] = section
                        else:
                            result[section][services]['current_cost'] += environment_value['current_cost']
                            result[section][services]['previous_cost'] += environment_value['previous_cost']
                else:
                    for env, cost in environment_value.items():
                        if tech_family not in merged_tf:
                            result[tech_family][services][env] = environment_value[env]
                        else:
                            if not result[section][services].get(env):
                                result[section][services][env] = environment_value[env]
                            else:
                                result[section][services][env]['previous_cost'] += environment_value[env][
                                    'previous_cost']
                                result[section][services][env]['current_cost'] += environment_value[env]['current_cost']
                                if result[section][services][env]['gcp_project'] == "-":
                                    result[section][services][env]['gcp_project'] = environment_value[env][
                                        'gcp_project']
                                else:
                                    result[section][services][env][
                                        'gcp_project'] += f", {environment_value[env]['gcp_project']}"

    return result
