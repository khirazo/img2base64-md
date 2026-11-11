@echo off
rem Launcher for img2base64_md.py (Windows).
rem Register this file as an external application in your image viewer and pass the
rem current file path as the only argument, in double quotes. The path token differs
rem per viewer; check the viewer's documentation.
rem
rem NOTE: when started from a GUI program (such as an image viewer), cmd.exe briefly
rem flashes a console window before this file even runs. To avoid that, use
rem img2base64-md.vbs instead. This .cmd file is meant for terminals and for tools that
rem need a plain batch file.
rem
rem pythonw.exe is preferred because it does not open a console window itself. Errors
rem are still reported through a dialog. Falls back to the py launcher, then python.
rem
rem Note: labels are used instead of parenthesized blocks so that the exit code of
rem Python is passed on (%errorlevel% inside a block is expanded too early).
setlocal
set "SCRIPT=%~dp0..\img2base64_md.py"

where pythonw >nul 2>nul
if not errorlevel 1 goto :use_pythonw
where pyw >nul 2>nul
if not errorlevel 1 goto :use_pyw
python "%SCRIPT%" %*
exit /b %errorlevel%

:use_pythonw
pythonw "%SCRIPT%" %*
exit /b %errorlevel%

:use_pyw
pyw -3 "%SCRIPT%" %*
exit /b %errorlevel%
