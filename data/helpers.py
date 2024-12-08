from functools import wraps


def retry_on_rate_limit(retries=10, delay=1, rps_limit_error_code=429):
    """
    Decorator to retry a method when receiving a Too Many Requests error.

    Args:
        retries (int): Number of retry attempts.
        delay (int): Delay between retries in seconds.
        rps_limit_error_code (int): Error code for the Too Many Requests error
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except RequestException as e:
                    if e.status_code == rps_limit_error_code:
                        last_exception = e
                        logging.info(f"Rate limit exceeded, retrying in {delay} seconds... (Attempt {attempt + 1}/{retries})")
                        time.sleep(delay)
                    else:
                        raise
            if last_exception:
                raise last_exception
        return wrapper
    return decorator
