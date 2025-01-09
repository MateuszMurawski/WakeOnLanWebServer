import sys
import servicemanager
import win32event
import win32service
import win32serviceutil

from WOLWebServer.wolWebServer import WOLWebServer

class WOLWebServerService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'WakeOnLanWebServerService'  # Name of the Windows service
    _svc_display_name_ = 'Wake On Lan Web Server Service'   # Display name of the service
    _svc_description_ = 'Runs the Wake On Lan Web Server as a Windows Service'  # Description of the service

    def __init__(self, args: list[str]) -> None:
        """
        Initialize the service instance.

        Args:
            args (list[str]): Arguments provided during service execution.

        Returns:
            None
        """

        super().__init__(args)
        self.event = win32event.CreateEvent(None, 0, 0, None)   # Synchronization event
        self.server: WOLWebServer | None = None # Instance of the WOL web server

    def GetAcceptedControls(self) -> int:
        """
        Specify which control signals the service can handle.

        Returns:
            int: Bitmask of accepted control signals, including pre-shutdown.
        """

        result = super().GetAcceptedControls()
        result |= win32service.SERVICE_ACCEPT_PRESHUTDOWN
        return result

    def SvcDoRun(self) -> None:
        """
        Entry point when the service starts.

        Initializes and runs the WOL Web Server.

        Returns:
            None
        """

        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING) # Notify that the service is starting
        self.server: WOLWebServer = WOLWebServer()    # Initialize the web server
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)  # Notify that the service is running
        self.server.run()   # Start the web server

    def SvcStop(self) -> None:
        """
        Entry point when the service is requested to stop.

        Stops the WOL Web Server gracefully.

        Returns:
            None
        """

        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING) # Notify that the service is stopping
        if self.server:
            self.server.stop()  # Stop the web server
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)  # Notify that the service has stopped
        win32event.SetEvent(self.event) # Signal the stop event

if __name__ == '__main__':
    # Check if the service is run as a script or via service manager
    if len(sys.argv) == 1:
        # Initialize and run the service
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(WOLWebServerService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Handle command-line operations for the service (e.g., install, remove)
        win32serviceutil.HandleCommandLine(WOLWebServerService)