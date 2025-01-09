class InvalidConfigurationException(Exception):
    """
    Custom exception raised when there is an invalid configuration.
    """
    def __init__(self, message: str) -> None:
        """
        Initialize the InvalidConfigurationException with a custom message.

        Args:
            message (str): The error message explaining the invalid configuration.
        """
        super().__init__(message)  # Call the parent constructor with the message