import logging
from concurrent.futures import ThreadPoolExecutor
import csv
import threading
import socket
import re
import configparser
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from WOLWebServer.computer import Computer
from WOLWebServer.invalidconfigurationexception import InvalidConfigurationException

class ComputerManager():
    """
    Manages the configuration, state, and actions of computers in a network.

    This class provides functionality for:
    - Loading and validating configuration settings from a file.
    - Managing a list of computers and their Wake-On-LAN (WOL) capabilities.
    - Checking the online status of computers.
    - Sending WOL packets to wake up computers.
    - Accessing related files like an HTML file or a list of computers.
    - Thread-safe operations on the computer list.

    Attributes:
        PORT (Optional[int]): Server port for listening or communication.
        SSL (Optional[bool]): Indicates if SSL is enabled.
        CERTFILE (Optional[Path]): Path to the SSL certificate file.
        KEYFILE (Optional[Path]): Path to the SSL key file.
        COMPUTERS_LIST (Optional[Path]): Path to the CSV file containing computer details.
        TIME_WAIT (Optional[int]): Time in seconds to wait before considering a status change, especially when it's pending. Prevents frequent status updates.
        HTML (Optional[Path]): Path to the HTML file for UI purposes.
        CHECK_PORT (Optional[int]): Port number used for checking computer status.
        NUM_SCAN_THREADS (Optional[int]): Number of threads to use for concurrent status checks.

        computers_data (List[Computer]): List of computer objects managed by the class.
        check_status_thread_active (threading.Event): Flag to manage status check thread activity.
        lock_computers_data (threading.Lock): Lock for thread-safe access to computers_data.
    """

    # Configuration attributes
    PORT: Optional[int] = None
    SSL: Optional[bool] = None
    CERTFILE: Optional[Path] = None
    KEYFILE: Optional[Path] = None
    COMPUTERS_LIST: Optional[Path] = None
    TIME_WAIT: Optional[int] = None
    HTML: Optional[Path] = None
    CHECK_PORT: Optional[int] = None
    NUM_SCAN_THREADS: Optional[int] = None

    computers_data: List[Computer] = []
    check_status_thread_active: threading.Event = threading.Event()
    lock_computers_data: threading.Lock = threading.Lock()

    @classmethod
    def loadConfig(cls, config_file: str, base_path: str) -> None:
        """
        Loads and validates the server and application configuration from a file.

        Args:
            config_file (str): The name of the configuration file.
            base_path (str): The base directory path to resolve relative file paths.

       Returns:
            None

        Raises:
            InvalidConfigurationException: If the configuration file contains invalid or missing settings.
        """

        config = configparser.ConfigParser()

        try:
            base_path = Path(base_path)
            config.read(base_path / config_file)

            try:
                cls.PORT = int(config['ServerConfig'].get('PORT'))
                if not (0 <= cls.PORT <= 65535):
                    raise InvalidConfigurationException("PORT must be between 0 and 65535.")
            except ValueError:
                raise InvalidConfigurationException("PORT must be an integer.")

            try:
                cls.SSL = config['ServerConfig'].getboolean('SSL')
            except ValueError:
                raise InvalidConfigurationException("SSL must be a boolean (True or False or 1 or 0).")

            cls.CERTFILE = config['ServerConfig'].get('CERTFILE') if cls.SSL else None
            cls.KEYFILE = config['ServerConfig'].get('KEYFILE') if cls.SSL else None
            if cls.SSL and (not cls.CERTFILE or not cls.KEYFILE):
                raise InvalidConfigurationException("CERTFILE and KEYFILE must be specified when SSL is enabled.")

            cls.CERTFILE = base_path / cls.CERTFILE
            cls.KEYFILE = base_path / cls.KEYFILE

            cls.COMPUTERS_LIST = config['ServerConfig'].get('COMPUTERS_LIST')
            if not cls.COMPUTERS_LIST:
                raise InvalidConfigurationException("COMPUTERS_LIST file path must be specified.")

            cls.COMPUTERS_LIST = base_path / cls.COMPUTERS_LIST

            try:
                cls.TIME_WAIT = int(config['ServerConfig'].get('TIME_WAIT'))
                if cls.TIME_WAIT < 0:
                    raise InvalidConfigurationException("TIME_WAIT must be a non-negative integer.")
            except (ValueError, TypeError):
                raise InvalidConfigurationException("TIME_WAIT must be a non-negative integer.")

            cls.HTML = config['ServerConfig'].get('HTML')
            if not cls.HTML:
                raise InvalidConfigurationException("HTML file path must be specified.")

            cls.HTML = base_path / cls.HTML

            try:
                cls.CHECK_PORT = int(config['ServerConfig'].get('CHECK_PORT'))
                if not (0 <= cls.CHECK_PORT <= 65535):
                    raise InvalidConfigurationException("CHECK_PORT must be between 0 and 65535.")
            except ValueError:
                raise InvalidConfigurationException("CHECK_PORT must be an integer.")

            try:
                cls.NUM_SCAN_THREADS = int(config['ServerConfig'].get('NUM_SCAN_THREADS'))
                if cls.NUM_SCAN_THREADS < 0:
                    raise InvalidConfigurationException("NUM_SCAN_THREADS must be a non-negative integer.")
            except (ValueError, TypeError):
                raise InvalidConfigurationException("NUM_SCAN_THREADS must be a non-negative integer.")

        except Exception as e:
            raise InvalidConfigurationException(f"An unexpected error occurred while loading configuration: {e}")

    @classmethod
    def loadComputers(cls) -> None:
        """
        Loads the list of computers from a CSV file specified in the configuration.

        The CSV file must contain three columns: ID, username, and MAC address.
        Validates the MAC address format and ensures each row has the required number of fields.

       Returns:
            None

        Raises:
            InvalidConfigurationException: If the file is missing, unreadable, or contains invalid data.
        """
        try:
            mac_regex = re.compile(r"^(([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})|([0-9a-fA-F]{12}))$")

            with open(cls.COMPUTERS_LIST, newline='') as csvfile:
                reader = csv.reader(csvfile, delimiter=';')
                cls.computers_data = []
                for row in reader:
                    if len(row) < 3:
                        raise InvalidConfigurationException(f"Each row in {cls.COMPUTERS_LIST} must contain 3 fields.")
                    ID, username, mac = row[0], row[1], row[2]

                    if not mac_regex.match(mac):
                        raise InvalidConfigurationException(f"Invalid MAC address format for {mac} in row: {row}")

                    cls.computers_data.append(Computer(ID=ID, username=username, mac=mac, time_wait=cls.TIME_WAIT))

        except FileNotFoundError:
            raise InvalidConfigurationException(f"The file {cls.COMPUTERS_LIST} was not found.")
        except IOError:
            raise InvalidConfigurationException(f"An error occurred while reading the file {cls.COMPUTERS_LIST}.")
        except Exception as e:
            raise InvalidConfigurationException(f"An unexpected error occurred while loading computers: {e}")

    @classmethod
    def sendWOL(cls, mac_address: str) -> bool:
        """
        Sends a Wake-On-LAN (WOL) magic packet to wake up a computer.

        Args:
            mac_address (str): The MAC address of the target computer.

        Returns:
            bool: True if the WOL packet was sent successfully, False otherwise.

        Logs:
            Info: When a WOL packet is successfully sent.
            Error: If there is a failure in sending the packet.
        """

        mac_address_clear = mac_address.replace(":", "").replace("-", "")
        magic_packet = bytes.fromhex('FF' * 6) + bytes.fromhex(mac_address_clear * 16)

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.sendto(magic_packet, ('255.255.255.255', 9))
                logging.info(f"Magic packet sent to {mac_address}")

                with cls.lock_computers_data:
                    for computer in cls.computers_data:
                        if computer.mac == mac_address:
                            computer.setStatus(2)
                            computer.setTime()
                            return True

        except socket.error as e:
            logging.error(f"Failed to send magic packet to {mac_address}: {e}")
            return False

    @classmethod
    def checkComputersStatus(cls) -> None:
        """
        Checks the online status of all managed computers.

        Uses a thread pool to perform concurrent checks for efficiency. Updates the status of each
        computer based on whether the target port is reachable.

        Thread Safety:
            Ensures thread-safe access to the computers_data list during status updates.
        """

        if cls.check_status_thread_active.is_set():
            return

        cls.check_status_thread_active.set()

        with cls.lock_computers_data:
            computers_to_check = list(cls.computers_data)

        with ThreadPoolExecutor(max_workers=cls.NUM_SCAN_THREADS) as executor:
            local_statuses = list(executor.map(cls.checkStatus, computers_to_check))

        with cls.lock_computers_data:
            for computer, is_online in local_statuses:
                computer.updateStatus(is_online)

            Computer.LAST_CHECK_TIME = datetime.now().timestamp()

        cls.check_status_thread_active.clear()

    @classmethod
    def checkStatus(cls, computer: Computer) -> Tuple[Computer, bool]:
        """
        Checks the online status of a single computer by attempting to connect to a specified port.

        Args:
            computer (Computer): The computer whose status needs to be checked.

        Returns:
            Tuple[Computer, bool]: A tuple containing the computer object and its online status (True if online).
        """

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                return computer, (sock.connect_ex((computer.ID, cls.CHECK_PORT)) == 0)
        except socket.error:
            return computer, False

    @classmethod
    def computerList(cls) -> List[List[str]]:
        """
        Retrieves a list of all managed computers along with their details.

        Returns:
            List[List[str]]: A list of computers, where each computer's details are represented as a list.
        """

        with cls.lock_computers_data:
            if Computer.LAST_CHECK_TIME > datetime.now().timestamp() - 900:
                return [computer.toList() for computer in cls.computers_data]
            else:
                return [computer.toList(blur=True) for computer in cls.computers_data]

    @classmethod
    def openHTML(cls) -> bytes:
        """
        Opens and reads the contents of the HTML file specified in the configuration.

        Returns:
            bytes: The content of the HTML file.

        Raises:
            InvalidConfigurationException: If the HTML file is not found.
        """

        try:
            return cls.HTML.read_bytes()

        except FileNotFoundError:
            raise InvalidConfigurationException(f"HTML file {cls.HTML} not found.")

    @classmethod
    def findMacByID(cls, ID: str) -> str:
        """
        Finds and returns the MAC address of a computer by its ID.

        Args:
            ID (str): The unique identifier of the computer.

        Returns:
            str: The MAC address of the computer.

        Raises:
            InvalidConfigurationException: If no computer with the specified ID is found.
        """

        with cls.lock_computers_data:
            for computer in cls.computers_data:
                if computer.ID == ID:
                    return computer.mac

        raise InvalidConfigurationException(f"Computer with ID: {ID} was not found in the list.")