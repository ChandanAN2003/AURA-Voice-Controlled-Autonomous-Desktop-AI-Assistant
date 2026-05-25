Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "run_aura_remote.bat" & chr(34), 0
Set WshShell = Nothing
