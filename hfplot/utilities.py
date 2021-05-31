"""Generic utilities
"""

def map_value(old_value, old_min, old_max, new_min, new_max):
    """helper to map value from one interval to new interval
    """
    if old_min == old_max:
        return (new_max - new_min) / 2.
    return (((old_value - old_min) * (new_max - new_min)) / (old_max - old_min)) + new_min
