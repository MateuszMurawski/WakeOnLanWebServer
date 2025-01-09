!define APP_NAME "WakeOnLanWebServer"  ; Define application name
!define EXE_NAME "WakeOnLanWebServer.exe"  ; Define executable file name
!define INSTALL_DIR "$PROGRAMFILES\${APP_NAME}"  ; Define the installation directory

OutFile "${APP_NAME}_Installer.exe"  ; Output file name for the installer
InstallDir "${INSTALL_DIR}"  ; Set the default installation directory
RequestExecutionLevel admin  ; Request admin rights for the installer
Name "${APP_NAME}"  ; This will set the name of the setup window

Page directory  ; Page for selecting the installation directory
Page instfiles  ; Page to display installation progress
UninstPage uninstConfirm  ; Page to confirm uninstallation
UninstPage instfiles  ; Page to display uninstallation progress

Section "Install"  ; Installation section
    ; Copying files to the installation directory
    
    SetOutPath "$INSTDIR"  ; Set the installation directory
    File "${EXE_NAME}"  ; Copy the executable to the installation directory

    SetOutPath "$INSTDIR\CONFIG"  ; Set output path for configuration files
    File /r "CONFIG\*.*"  ; Recursively copy all files in the CONFIG folder

    SetOutPath "$INSTDIR\DATA"  ; Set output path for data files
    File /r "DATA\*.*"  ; Recursively copy all files in the DATA folder

    SetOutPath "$INSTDIR\HTML"  ; Set output path for HTML files
    File /r "HTML\*.*"  ; Recursively copy all files in the HTML folder

    SetOutPath "$INSTDIR\LOG"  ; Set output path for log files
    File /r "LOG\*.*"  ; Recursively copy all files in the LOG folder

    SetOutPath "$INSTDIR\SSL"  ; Set output path for SSL files
    File /r "SSL\*.*"  ; Recursively copy all files in the SSL folder

    ; Save the installation directory in the registry for uninstallation
    WriteRegStr HKLM "Software\${APP_NAME}" "Install_Dir" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\Uninstall.exe"

    ; Create the uninstaller executable
    WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Run as Service" SEC_SERVICE  ; Section to install and manage the service
    ; Create the service
    nsExec::Exec 'sc create ${APP_NAME} binPath= "\"$INSTDIR\\${EXE_NAME}\"" start= demand'

    ; Ask the user whether to start the service after installation
    MessageBox MB_YESNO "Do you want to start the ${APP_NAME} service after installation?" IDNO SkipStart
    nsExec::Exec "sc start ${APP_NAME}"  ; Start the service
SkipStart:

    ; Ask the user whether to set the service to start automatically on system startup
    MessageBox MB_YESNO "Do you want to set the ${APP_NAME} service to start automatically with Windows?" IDNO SkipAutoStart
    nsExec::Exec "sc config ${APP_NAME} start= auto"  ; Configure the service to start automatically
SkipAutoStart:

    ; Ask if the user wants to unblock port 443 in Windows Firewall
    MessageBox MB_YESNO "Do you want to unblock port 443 in the Windows Firewall for ${APP_NAME}?" IDNO SkipFirewall
    ExecWait 'netsh advfirewall firewall add rule name="${APP_NAME} HTTPS" dir=in action=allow protocol=TCP localport=443 program="$INSTDIR\${EXE_NAME}"'  ; Allow inbound connections on port 443
    ExecWait 'netsh advfirewall firewall add rule name="${APP_NAME} HTTPS OUT" dir=out action=allow protocol=TCP localport=443 program="$INSTDIR\${EXE_NAME}"'  ; Allow outbound connections on port 443
SkipFirewall:
SectionEnd

Section "Uninstall"  ; Uninstallation section
    ; Stop and delete the service
    nsExec::Exec "sc stop ${APP_NAME}"
    nsExec::Exec "sc delete ${APP_NAME}"
	
	; Remove firewall rules
    ExecWait 'netsh advfirewall firewall delete rule name="${APP_NAME} HTTPS"'  ; Remove the inbound firewall rule
    ExecWait 'netsh advfirewall firewall delete rule name="${APP_NAME} HTTPS OUT"'  ; Remove the outbound firewall rule

    ; Remove files and registry entries
    Delete "$INSTDIR\${EXE_NAME}"  ; Delete the executable file
    Delete "$INSTDIR\Uninstall.exe"  ; Delete the uninstaller executable
    RMDir /r "$INSTDIR\CONFIG"  ; Remove the CONFIG folder and its contents
    RMDir /r "$INSTDIR\DATA"  ; Remove the DATA folder and its contents
    RMDir /r "$INSTDIR\HTML"  ; Remove the HTML folder and its contents
    RMDir /r "$INSTDIR\LOG"  ; Remove the LOG folder and its contents
    RMDir /r "$INSTDIR\SSL"  ; Remove the SSL folder and its contents
    
    RMDir /r "$INSTDIR"  ; Remove the installation directory
    
    ; Remove registry entries
    DeleteRegKey HKLM "Software\${APP_NAME}"  ; Remove the installation path registry key
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"  ; Remove the uninstall entry from the registry
SectionEnd
