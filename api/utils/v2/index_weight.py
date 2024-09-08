def count_child_keys(data):
    counts = {'development': 0, 'staging': 0, 'production': 0}

    for key in data:
        for subkey in data[key]:
            for env in data[key][subkey]:
                counts[env] += 1

    total_count = sum(counts.values())
    return total_count


def adjust_index(data):
    for category, systems in data.items():
        for env in ['development', 'staging', 'production']:
            # Get the current sum for the environment
            current_sum = sum(systems[system][env] for system in systems)

            # If sum is less than 100, add the difference to the smallest value
            if 0 < current_sum < 100:
                diff = 100 - current_sum
                # Find the system with the smallest value for this environment
                min_system = min(systems, key=lambda x: systems[x][env])
                min_system_env = systems[min_system][env]
                systems[min_system][env] = round((min_system_env + diff), 2)

            # If sum is more than 100, subtract the difference from the largest value
            elif current_sum > 100:
                diff = current_sum - 100
                # Find the system with the largest value for this environment
                max_system = max(systems, key=lambda x: systems[x][env])
                max_system_env = systems[max_system][env]
                systems[max_system][env] = round((max_system_env - diff), 2)

    return data
