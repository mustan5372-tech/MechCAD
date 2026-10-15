; =====================================================================
; MechCAD - Autodesk Fusion 360-Class Parametric 3D CAD
; Inno Setup 6 Official Installer Script (x64)
; Output: MechCAD-Setup-x64.exe
; =====================================================================

#define MyAppName "MechCAD"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "MechCAD Contributors"
#define MyAppURL "https://github.com/mustan5372-tech/MechCAD"
#define MyAppExeName "MechCAD.exe"

[Setup]
AppId={{C84F38B9-3B1B-4712-88E2-263B9B9A608F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes
LicenseFile=
OutputDir=..\dist
OutputBaseFilename=MechCAD-Setup-x64
SetupIconFile=..\assets\branding\mechcad.ico
WizardImageFile=..\assets\branding\installer-wizard.bmp
WizardSmallImageFile=..\assets\branding\installer-small.bmp
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ChangesAssociations=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} {#MyAppVersion}
VersionInfoVersion=1.0.0.0
VersionInfoCompany=MechCAD
VersionInfoDescription=MechCAD - Professional 3D Parametric CAD
VersionInfoProductVersion=1.0.0.0
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\MechCAD\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\branding\mechcad.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\branding\mechcad.ico"; Tasks: desktopicon

[Registry]
; Register .mcad file extension association
Root: HKA; Subkey: "Software\Classes\.mcad"; ValueType: string; ValueName: ""; ValueData: "MechCAD.Project"; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.mcad\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\assets\branding\mechcad.ico,0"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\MechCAD.Project"; ValueType: string; ValueName: ""; ValueData: "MechCAD CAD Project"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\MechCAD.Project\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\assets\branding\mechcad.ico,0"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\MechCAD.Project\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
