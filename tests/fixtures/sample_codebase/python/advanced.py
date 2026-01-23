"""Advanced Python features for testing."""

from typing import Optional, List
from functools import wraps

API_VERSION = "1.0.0"


async def fetch_data(url: str) -> dict:
    """Async function for network operations."""
    await None
    return {"data": "value"}


class Outer:
    """Outer class with inner class."""

    @staticmethod
    def static_method():
        """Static method."""
        pass

    @classmethod
    def class_method(cls):
        """Class method."""
        pass

    class Inner:
        """Inner class definition."""

        def method(self):
            """Instance method."""
            pass


def decorator(func):
    """Simple decorator."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper
