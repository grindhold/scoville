; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "Skarphed"
#define MyAppVersion "0.1"
#define MyAppPublisher "Skarphed Devteam"
#define MyAppURL "http://www.skarphed.org"
#define MyAppExeName "skarphed.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{DEE40272-E1B9-4C3F-99FC-CDDCB31B8318}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={pf}\skarphed
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputBaseFilename=skarphed_0.1_setup
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 0,6.1

[Files]
Source: "C:\Users\\skarphed\admin\src\dist\*"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\\skarphed\admin\src\dist\data\*"; DestDir: "{app}\data"; Flags: ignoreversion
Source: "C:\Users\\skarphed\admin\src\dist\data\icon\*"; DestDir: "{app}\data\icon"; Flags: ignoreversion
Source: "C:\Users\\skarphed\admin\src\dist\installer\_database\*"; DestDir: "{app}\installer\_database"; Flags: ignoreversion
Source: "C:\Users\\skarphed\admin\src\dist\installer\debian6_apache2\*"; DestDir: "{app}\installer\debian6_apache2"; Flags: ignoreversion
Source: "C:\Users\\skarphed\admin\src\dist\core\web\*"; DestDir: "{app}\core\web"; Flags: ignoreversion
Source: "C:\Users\\skarphed\admin\src\dist\core\lib\*"; DestDir: "{app}\core\lib"; Flags: ignoreversion
Source: "C:\Users\\skarphed\admin\src\dist\locale\en_US\LC_MESSAGES\*"; DestDir: "{app}\locale\en_US\LC_MESSAGES"; Flags: ignoreversion
Source: "C:\Users\\skarphed\admin\src\dist\locale\de_DE\LC_MESSAGES\*"; DestDir: "{app}\locale\de_DE\LC_MESSAGES"; Flags: ignoreversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

