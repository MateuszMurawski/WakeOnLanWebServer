import signal
from WOLWebServer.wolWebServer import WOLWebServer


class SignalHandler:
    """
    Class to handle system signals (SIGINT, SIGTERM) for graceful shutdown.
    This allows the program to listen for shutdown requests.
    """

    def __init__(self, server: WOLWebServer) -> None:
        """
        Initialize the signal handler.
        Set up signal handlers for SIGINT (Ctrl+C) and SIGTERM (termination signal).

        Args:
            server (WOLWebServer): The server instance that will be stopped when a shutdown signal is received.

        Returns:
            None
        """

        self.server: WOLWebServer = server

        # Register the signal handlers
        signal.signal(signal.SIGINT, self.request_shutdown)  # Handle SIGINT (Ctrl+C)
        signal.signal(signal.SIGTERM, self.request_shutdown)  # Handle SIGTERM (termination signal)

    def request_shutdown(self, *args: tuple) -> None:
        """
        Callback function to handle the shutdown request.
        This method will be called when SIGINT or SIGTERM is received.

        Args:
            *args: Arguments passed when the signal is received (unused in this case).

        Returns:
            None
        """

        # Once the shutdown request is received, stop the server
        self.server.stop()

if __name__ == '__main__':
    # Initialize the WOL Web Server
    server: WOLWebServer = WOLWebServer()

    # Initialize the signal handler to listen for shutdown signals
    signal_handler: SignalHandler = SignalHandler(server)

    # Run the server
    server.run()
