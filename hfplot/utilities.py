"""Generic utilities
"""

def map_value(old_value, old_min, old_max, new_min, new_max):
    """helper to map value from one interval to new interval
    """
    if old_min == old_max:
        return (new_max - new_min) / 2.
    return (((old_value - old_min) * (new_max - new_min)) / (old_max - old_min)) + new_min

def try_method(obj, name, *args, **kwargs):
    """Try method with name on object obj

    Currently only makes sense when no return statements are involved

    Args:
        obj: any object
        name: str, name of method to be checked
        args: arguments to be passed to method
        kwargs: keyword arguments to be passed to method
    """
    if hasattr(obj, name):
        getattr(obj, name)(*args, **kwargs)
