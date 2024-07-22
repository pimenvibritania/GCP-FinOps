def count_child_keys(data):
    counts = {'development': 0, 'staging': 0, 'production': 0}

    for key in data:
        for subkey in data[key]:
            for env in data[key][subkey]:
                counts[env] += 1

    total_count = sum(counts.values())
    return total_count
