; Inno Setup — instalador Windows do PDF Summarizer
; Pré-requisito: executar PyInstaller antes (dist\PDFSummarizer\ deve existir).
; Compile com: ISCC.exe installer\PDFSummarizer.iss
; Ou use: .\scripts\build.ps1 -Installer

#define AppName "PDF Summarizer"
#define AppExe "PDFSummarizer.exe"
#define AppVersion "0.1.0"
#define AppPublisher "ZAPFCOORP"
#define DistDir "..\dist\PDFSummarizer"

[Setup]
AppId={{A7B3C9D1-4E2F-5A6B-8C0D-1E2F3A4B5C6D}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppSupportURL=https://github.com/ZAPFCOORP/py-rag-local-bot
AppUpdatesURL=https://github.com/ZAPFCOORP/py-rag-local-bot
DefaultDirName={autopf}\PDFSummarizer
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
LicenseFile=
OutputDir=output
OutputBaseFilename=PDFSummarizer-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExe}
SetupLogging=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  if not DirExists(ExpandConstant('{#DistDir}')) then
  begin
    MsgBox(
      'Pasta de build não encontrada:' + #13#10 +
      ExpandConstant('{#DistDir}') + #13#10#13#10 +
      'Execute primeiro o PyInstaller:' + #13#10 +
      '  pyinstaller PDFSummarizer.spec' + #13#10 +
      'ou' + #13#10 +
      '  .\scripts\build.ps1',
      mbError, MB_OK);
    Result := False;
  end
  else
    Result := True;
end;
