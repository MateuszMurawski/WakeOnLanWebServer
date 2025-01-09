from datetime import datetime
from typing import Optional


class Computer:
    """
    Class to represent a computer with attributes such as ID, username, MAC address,
    time to wait before checking the status, and the current status.

    Attributes:
        LAST_CHECK_TIME (int): Timestamp of the last global status check.
    """

    LAST_CHECK_TIME: int = 0

    def __init__(self, ID: str, username: str, mac: str, time_wait: int, status: int = 3, time: int = 0):
        """
        Initialize the Computer object with the given attributes.

        Args:
            ID (str): Unique identifier for the computer.
            username (str): Username associated with the computer.
            mac (str): MAC address of the computer (converted to uppercase).
            time_wait (int): Time in seconds to wait before considering status change.
            status (int, optional): Current status of the computer. Default is 3 (unknown).
            time (int, optional): Timestamp of the last status change. Default is 0 (never changed).
        """

        self.ID: str = ID
        self.username: str = username
        self.mac: str = mac.upper()
        self.time_wait: int = time_wait
        self.status: int = status
        self.time: int = time

    def updateStatus(self, is_online: bool) -> None:
        """
        Update the status of the computer based on its online status.

        Args:
            is_online (bool): Whether the computer is online or not.

        Returns:
            None
        """

        if is_online:
            self.status = 1 # Online
        elif self.status == 2 and (datetime.now().timestamp() - self.time) < self.time_wait:
            # If the status is '2' (pending) and the time is less than the time_wait, keep it pending
            self.status = 2
        else:
            self.status = 0 # Offline

    def toList(self, blur: Optional[bool] = False) -> list:
        """
        Convert the computer's basic information to a list format.

        If the `blur` parameter is `True`, the status is set to `3` (checking)
        to obscure the real status.

        Args:
            blur (Optional[bool]): If `True`, returns the status as `3` (checking). Defaults to `False`.

        Returns:
            list: A list containing the computer's ID, username, and status.
        """
        if blur:
            return [self.ID, self.username, 3]
        else:
            return [self.ID, self.username, self.status]

    def setTime(self) -> None:
        """
        Set the timestamp to the current time when the status was last updated.

        Returns:
            None
        """

        self.time = datetime.now().timestamp()

    def setStatus(self, status: int) -> None:
        """
        Set a specific status for the computer.

        Args:
            status (int): The new status to set.

        Returns:
            None
        """

        self.status = status