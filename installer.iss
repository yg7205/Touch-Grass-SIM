[Setup]
AppName=Touch Grass SIM
AppVersion=1.0.1
DefaultDirName={autopf}\Touch Grass SIM
DefaultGroupName=Touch Grass SIM
UninstallDisplayIcon={app}\Touch-Grass-Sim.exe
Compression=lzma
SolidCompression=yes
OutputDir=.
OutputBaseFilename=Touch-Grass-Sim-Windows-Setup

[Files]
Source: "dist\Touch-Grass-Sim\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Touch Grass SIM"; Filename: "{app}\Touch-Grass-Sim.exe"
Name: "{autodesktop}\Touch Grass SIM"; Filename: "{app}\Touch-Grass-Sim.exe"

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ConfigPath: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    ConfigPath := ExpandConstant('{userdocs}\..\.config\touch-grass-sim');
    if DirExists(ConfigPath) then
    begin
      DelTree(ConfigPath, True, True, True);
    end;
  end;
end;