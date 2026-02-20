; Inno Setup script for Patreon Credits Generator
; Build the exe first with: pyinstaller patreon_credits.spec
; Then compile this .iss with Inno Setup 6+

#define MyAppName "Patreon Credits Generator"
#define MyAppVersion "1.3.1"
#define MyAppPublisher "mscrnt"
#define MyAppURL "https://github.com/mscrnt/patreon-credits"
#define MyAppExeName "PatreonCredits.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=..\dist\installer
OutputBaseFilename=PatreonCredits_Setup_{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
SetupIconFile=..\icon.ico
; Require Windows 10+
MinVersion=10.0
PrivilegesRequired=admin
WizardStyle=modern
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\PatreonCredits.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
var
  DataDirPage: TInputDirWizardPage;

function GetDefaultDataDir: String;
begin
  Result := ExpandConstant('{userdocs}\PatreonCredits');
end;

procedure InitializeWizard;
begin
  DataDirPage := CreateInputDirPage(wpSelectDir,
    'Select Data Directory',
    'Where should the app save settings and generated videos?',
    'Select the folder where Patreon Credits Generator will store its configuration, ' +
    'patron cache, and output videos. This can be changed later in the app settings.',
    False, '');
  DataDirPage.Add('');
  DataDirPage.Values[0] := GetDefaultDataDir;
end;

procedure WriteConfigJson;
var
  ConfigDir: String;
  ConfigFile: String;
  JsonContent: String;
  DataDir: String;
begin
  ConfigDir := ExpandConstant('{localappdata}\PatreonCredits');
  ForceDirectories(ConfigDir);
  ConfigFile := ConfigDir + '\config.json';
  DataDir := DataDirPage.Values[0];
  { Create the data directory }
  ForceDirectories(DataDir);
  { Write config.json with the chosen path — escape backslashes for JSON }
  StringChangeEx(DataDir, '\', '\\', True);
  JsonContent := '{' + #13#10 + '  "data_dir": "' + DataDir + '"' + #13#10 + '}';
  SaveStringToFile(ConfigFile, JsonContent, False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    WriteConfigJson;
end;
