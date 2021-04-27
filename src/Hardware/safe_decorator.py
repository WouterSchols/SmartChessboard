from typing import Callable, Any


def perform_safe_factory(reset: Callable[[None], None] = None, max_tries: int = 5) -> \
        Callable[[Callable[[Any], Any]], Callable[[Any], Any]]:
    """ Factory to create a decorator to perform an i2c operation safely

    This factory returns the perform_safe decorator. This decorator will try to execute a function until it succeeds
    or until max_tries have failed. If a tca is supplied then the factory will also reset the tca lock
    after every SOError.

    :param reset: Any other function to execute when recovering from an error
    :param max_tries: Maximum amount of times that an operation will be attempted
    :return: The decorator perform safe
    """
    def perform_safe(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
        """" Tries to execute func(*args) until no OSError is thrown or TRIES attempts have failed

        The i2c buss is sensitive to noise. Corrupted messages can trigger an OSError on the buss device.
        We can recover from this error by simply resending the message until it arrives correctly. This method accepts
        a function func which could trigger an OSError which would cause the program to fail.
        We can easily recover from this error by retrying 'func' if the error is cause by noise. The perform
        safe decorator makes sure that an error is only trow if the operation fails max_tries times. Because of an
        error in the adafruit libraries the tca can soft lock after an exception. Resetting the lock to false after
        an exception prevents the errors
        :param func: function to be executed
        :return: function which executes func until it either succeeds or max_tries attempts have failed
        :rtype: Same as func
        """
        def safe_wrapper(*args, **kwargs):
            tries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except OSError:
                    if tries < max_tries:
                        tries += 1
                        if reset is not None:
                            reset()
                    else:
                        raise
        return safe_wrapper
    return perform_safe


perform_safe = perform_safe_factory(None)
