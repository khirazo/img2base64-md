' Windowless launcher for img2base64_md.py (Windows).
'
' A .cmd launcher always flashes a console window when started from a GUI program.
' This script runs Python with a hidden window instead and passes on its exit code.
'
' Register in your image viewer as an external program:
'   Program:   wscript.exe
'   Arguments: "<full path to this file>" "<current image path token>"
' Only the first argument (the image path) is forwarded.
Option Explicit

Dim fso, shell, here, script, cmd, py, i
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

If WScript.Arguments.Count < 1 Then
    WScript.Quit 2
End If

here = fso.GetParentFolderName(WScript.ScriptFullName)
script = fso.BuildPath(fso.GetParentFolderName(here), "img2base64_md.py")

' pythonw.exe has no console. Fall back to the py launcher (pyw.exe) if it is missing.
py = "pythonw.exe"
cmd = py & " """ & script & """ """ & WScript.Arguments(0) & """"

On Error Resume Next
i = shell.Run(cmd, 0, True)
If Err.Number <> 0 Then
    Err.Clear
    i = shell.Run("pyw.exe -3 """ & script & """ """ & WScript.Arguments(0) & """", 0, True)
    If Err.Number <> 0 Then i = 4
End If
On Error GoTo 0
WScript.Quit i
