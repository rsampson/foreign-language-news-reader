; Inno Setup script for the French News Reader Windows installer.
; Built by .github/workflows/release.yml:  iscc packaging\windows\installer.iss
; Installs for the current user only, so no administrator rights are needed.

[Setup]
AppId={{6C0E7B55-3A0B-4B0E-9C59-7B2F1D2A9E41}
AppName=French News Reader
AppVersion=1.0.0
AppPublisher=French News Reader
DefaultDirName={autopf}\French News Reader
DefaultGroupName=French News Reader
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\..\dist
OutputBaseFilename=french-news-reader-windows-setup
SetupIconFile=..\icon.ico
UninstallDisplayIcon={app}\french-news-reader.exe
LicenseFile=..\..\LICENSE
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; Flags: checkedonce

[Files]
Source: "..\..\dist\french-news-reader\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\French News Reader"; Filename: "{app}\french-news-reader.exe"
Name: "{autodesktop}\French News Reader"; Filename: "{app}\french-news-reader.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\french-news-reader.exe"; Description: "Start French News Reader"; Flags: nowait postinstall skipifsilent
