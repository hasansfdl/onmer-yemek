; Inno Setup 6 - Onmer Admin Panel kurulum sihirbazi
; Derleme: once packaging\build_windows.ps1, sonra bu dosyayi derle.
; PowerShell: & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "...\packaging\OnmerAdminSetup.iss"

#define MyAppName "Onmer Admin Panel"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Onmer Yemek Organizasyon"
#define MyAppExeName "OnmerAdminPanel.exe"
#define DistDir "..\\dist\\OnmerAdminPanel"

[Setup]
AppId={{A7E8F1C2-4B3D-5E6F-8091-2A3B4C5D6E7F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Onmer\AdminPanel
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=OnmerAdminPanel_Setup_{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
