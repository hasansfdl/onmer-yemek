; Onmer Stok & Finans — Windows kurulum sihirbazi (Inno Setup 6)
; Derleme: packaging\build_stok_windows.ps1

#define MyAppName "Onmer Stok & Finans"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Onmer Yemekcilik"
#define MyAppExeName "OnmerStokFinans.exe"
#define MyAppUrl "https://onmer.com.tr"

[Setup]
AppId={{A7C4E2F1-9B3D-4A6E-8C1F-2D5E6A9B0C3D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppUrl}
AppSupportURL={#MyAppUrl}
AppUpdatesURL={#MyAppUrl}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=OnmerStokFinans_Kurulum
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
UsePreviousAppDir=yes
CloseApplications=force
RestartApplications=no
LicenseFile=
InfoBeforeFile=
InfoAfterFile=

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaustu kisayolu olustur"; GroupDescription: "Ek secenekler:"; Flags: checkedonce

[Files]
Source: "..\dist\OnmerStokFinans\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#ifexist "seed_data\onmer_stok.db"
Source: "seed_data\onmer_stok.db"; DestDir: "{localappdata}\OnmerStokFinans"; Flags: onlyifdoesntexist uninsneveruninstall
#endif

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Kaldir"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Onmer Stok && Finans'i baslat"; Flags: nowait postinstall skipifsilent

[Messages]
turkish.WelcomeLabel2=Bu sihirbaz [name/ver] uygulamasini bilgisayariniza kuracaktir.%n%nVerileriniz su konumda saklanir:%n%LOCALAPPDATA%\OnmerStokFinans%n%nNot: Bu kurulumda mevcut veritabani dahil edildiyse, yeni bilgisayarda otomatik yuklenir (hedefte veri yoksa).
