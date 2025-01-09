import logging
import ssl
import sys
from http.server import HTTPServer
from pathlib import Path
from typing import Optional, Type

from WOLWebServer import Server
from WOLWebServer.computerManager import ComputerManager
from WOLWebServer.invalidconfigurationexception import InvalidConfigurationException

class WOLWebServer:
    """
    Class to manage the Web Server for Wake-On-LAN (WOL).
    """

    def __init__(self):
        """
        Initialize the WOLWebServer instance.
        """

        self.httpd: Optional[HTTPServer] = None  # Instance of the HTTP server
        self.stopped: bool = False  # Flag to track if the server is already stopped
        self.is_serving: bool = False  # Flag to track if the server is actively serving requests

    def stop(self) -> None:
        """
        Stop the running HTTP server.

        Safely shuts down the server if it is running and releases resources.
        Prevents multiple stop attempts by using the `stopped` flag.

        Returns:
            None
        """

        if self.stopped:  # Check if the server has already been stopped
            return

        if self.is_serving:
            # Mark the server as stopped
            self.stopped = True

            logging.info("Stopping the server...")
            try:
                self.httpd.shutdown()   # Shutdown the server
                self.httpd.server_close()   # Close the server socket
                logging.info("Server stopped successfully.")
            except Exception as e:
                logging.error(f"Error stopping the server: {e}")
        else:
            logging.warning("Server is not running.")

    def configureSSL(self) -> ssl.SSLContext:
        """
        Configure SSL for the server.
        Creates and configures an SSL context for secure connections.

        Returns:
            ssl.SSLContext: Configured SSL context.

        Raises:
            InvalidConfigurationException: If the SSL certificate or key is invalid or missing.
        """

        try:
            # Create SSL context with TLS support
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            # Load SSL certificate and key
            context.load_cert_chain(certfile=ComputerManager.CERTFILE, keyfile=ComputerManager.KEYFILE)
            return context
        except FileNotFoundError as e:
            raise InvalidConfigurationException(f"SSL certificate or key file not found: {e}")
        except ssl.SSLError as e:
            raise InvalidConfigurationException(f"SSL error: {e}")
        except Exception as e:
            raise InvalidConfigurationException(f"Unexpected SSL error: {e}")

    def run(self, server_class: Type[HTTPServer] = HTTPServer, handler_class: Type[Server] = Server) -> None:
        """
        Run the HTTP server.

        Starts the server with the specified configurations and handles incoming requests.

        Args:
            server_class (Type[HTTPServer]): The HTTP server class to use.
            handler_class (Type[Server]): The request handler class to use.

        Returns:
            None

        Raises:
            InvalidConfigurationException: If server configuration is invalid.
        """
        try:
            # Determine base path for executable or script
            base_path = Path(sys.executable).parent

            # Configure logging
            logging.basicConfig(filename=base_path / 'LOG/server.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

            # Load server configurations
            ComputerManager.loadConfig('CONFIG/config.ini', base_path)
            ComputerManager.loadComputers()

            # Initialize the HTTP server
            self.httpd = server_class(('0.0.0.0', ComputerManager.PORT), handler_class)

            # Configure SSL if enabled
            if ComputerManager.SSL:
                context = self.configureSSL()
                self.httpd.socket = context.wrap_socket(self.httpd.socket, server_side=True)

            # Start the server
            self.is_serving = True
            logging.info(f'Server running on {"https" if ComputerManager.SSL else "http"}://0.0.0.0:{ComputerManager.PORT}')
            self.httpd.serve_forever()

        except KeyboardInterrupt:
            # Handle graceful shutdown on user interrupt
            logging.info("Server shutdown requested by user (KeyboardInterrupt).")
        except InvalidConfigurationException as e:
            # Log configuration errors
            logging.error(f"Configuration error: {e}")
        except Exception as e:
            # Log unexpected server errors
            logging.exception(f"Unexpected server error: {e}")
        finally:
            # Ensure server is stopped in any case
            self.stop()