; Inno Setup script for the Foreign Language News Reader Windows installer.
; Built by .github/workflows/release.yml:  iscc packaging\windows\installer.iss
; Installs for the current user only, so no administrator rights are needed.

[Setup]
AppId={{F2DB3FFE-0330-4E1B-A146-6ACE55E9DF43}
AppName=Foreign Language News Reader
AppVersion=1.2.0
AppPublisher=Foreign Language News Reader
DefaultDirName={autopf}\Foreign Language News Reader
DefaultGroupName=Foreign Language News Reader
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\..\dist
OutputBaseFilename=foreign-language-news-reader-windows-setup
SetupIconFile=..\icon.ico
UninstallDisplayIcon={app}\foreign-language-news-reader.exe
LicenseFile=..\..\LICENSE
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; Flags: checkedonce

[Files]
Source: "..\..\dist\foreign-language-news-reader\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\Foreign Language News Reader"; Filename: "{app}\foreign-language-news-reader.exe"
Name: "{autodesktop}\Foreign Language News Reader"; Filename: "{app}\foreign-language-news-reader.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\foreign-language-news-reader.exe"; Description: "Start Foreign Language News Reader"; Flags: nowait postinstall skipifsilent
