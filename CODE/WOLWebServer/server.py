import json
import logging
import threading
from http.server import BaseHTTPRequestHandler
from typing import Any

from WOLWebServer.computerManager import ComputerManager
from WOLWebServer.invalidconfigurationexception import InvalidConfigurationException

class Server(BaseHTTPRequestHandler):
    """
    HTTP server to handle requests related to Wake-On-LAN (WOL).

    This class extends BaseHTTPRequestHandler and handles both GET and POST requests.
    It allows updating computer statuses, triggering WOL actions, and returning appropriate data in JSON format.
    """

    def log_request(self, code: str = '-', size: str = '-') -> None:
        """
        Overrides the log_request method to prevent logging every request to the console.

        Args:
            code (str): The HTTP response code (default is '-').
            size (str): The size of the response in bytes (default is '-').

        Returns:
            None
        """

        pass

    def log_message(self, format: str, *args: Any) -> None:
        """
        Overrides the log_message method to prevent logging every message to the console.

        Args:
            format (str): The format of the message.
            *args (Any): Arguments to format the message.

        Returns:
            None
        """

        pass

    def _set_headers(self, content_type: str = 'application/json') -> None:
        """
        Sets the HTTP response headers.

        Args:
            content_type (str): The Content-Type of the response (default is 'application/json').

        Returns:
            None
        """

        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def do_GET(self) -> None:
        """
        Handles GET requests.

        Depending on the path, it returns either updated computer data in JSON format or an HTML page.

        - If the path is '/update_data', returns the updated computer data in JSON format.
        - If the path is '/', returns an HTML page with computer data.
        - For any other paths, returns the homepage (instead of a 404 error).

        Returns:
            None
        """

        try:
            logging.info(f"Received request from IP: {self.client_address[0]}. Update status computers. Action: {self.path}")
            threading.Thread(target=ComputerManager.checkComputersStatus, daemon=True).start()

            if self.path == '/update_data':
                # Endpoint to get updated computer data
                self._set_headers('application/json')
                self.wfile.write(json.dumps(ComputerManager.computerList()).encode('utf-8'))

            elif self.path == '/':
                # Home page, sends HTML
                self._set_headers('text/html')
                self.wfile.write(ComputerManager.openHTML())

            else:
                logging.error(f"Invalid GET request for {self.path}, returning homepage.")
                # Instead of 404, return the homepage
                self._set_headers('text/html')
                self.wfile.write(ComputerManager.openHTML())

        except InvalidConfigurationException as e:
            logging.error(f"Error handling GET request for {self.path}: {e}")
            self.send_error(404, "HTML file not found")

        except Exception as e:
            logging.error(f"Unexpected error handling GET request for {self.path}: {e}")
            self.send_error(500, "Internal Server Error")

    def do_POST(self) -> None:
        """
        Handles POST requests.

        This allows triggering the Wake-On-LAN (WOL) action on a computer identified by the ID passed in the request body.

        - If the path is '/run_action', sends a WOL signal to the computer with the specified ID.
        - For any other paths, returns the homepage (instead of a 404 error).

        Returns:
            None
        """

        try:
            if self.path == '/run_action':
                # Endpoint to trigger a WOL action
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)

                ID = data.get("ID")
                MAC = ComputerManager.findMacByID(ID)
                logging.info(f"Received request from IP: {self.client_address[0]}. Sending wake signal to computer with ID: {ID} and MAC address: {MAC}")

                response = {"status": "error"}

                # Send WOL signal
                if ComputerManager.sendWOL(MAC):
                    response = {"status": "success"}

                self._set_headers('application/json')
                self.wfile.write(json.dumps(response).encode('utf-8'))

            else:
                logging.error(f"Invalid POST request for {self.path}, returning homepage.")
                # Instead of 404, return the homepage
                self._set_headers('text/html')
                self.wfile.write(ComputerManager.openHTML())

        except json.JSONDecodeError:
            logging.error("Failed to decode JSON data from POST request.")
            self.send_error(400, "Bad Request: Invalid JSON")
        except KeyError as e:
            logging.error(f"Missing key in JSON data: {e}")
            self.send_error(400, f"Bad Request: Missing key {e}")
        except Exception as e:
            logging.error(f"Error handling POST request for {self.path}: {e}")
            self.send_error(500, "Internal Server Error")