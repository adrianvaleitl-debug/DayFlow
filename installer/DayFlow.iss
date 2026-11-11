#define MyAppName "DayFlow"
#define MyAppVersion "1.4.7"
#define MyAppPublisher "Adrian Vale"
#define MyAppExeName "DayFlow.exe"

[Setup]
AppId={{B7A3E61D-4D2C-4F6B-9F3A-DF120A71C8D9}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\DayFlow
DefaultGroupName=DayFlow
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=..\release
OutputBaseFilename=DayFlow-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
CloseApplications=yes
RestartApplications=no
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=..\assets\dayflow.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "..\dist\DayFlow.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\dayflow.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Uninstall DayFlow"; Filename: "{uninstallexe}"; WorkingDir: "{app}"
Name: "{group}\DayFlow"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\dayflow.ico"; AppUserModelID: "AdrianVale.DayFlow"
Name: "{autodesktop}\DayFlow"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\dayflow.ico"; AppUserModelID: "AdrianVale.DayFlow"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch DayFlow"; Flags: postinstall nowait
