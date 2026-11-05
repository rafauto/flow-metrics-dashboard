"""Errors with messages written for the person using the dashboard."""


class DataValidationError(ValueError):
    """The input data or configuration cannot be used. The message says how to fix it."""
