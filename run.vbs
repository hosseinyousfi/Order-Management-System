' launch_app.vbs – invisibly runs run.bat in src, then opens browser
Option Explicit

Dim shell, thisFolder, projectFolder, batPath

Set shell = CreateObject("WScript.Shell")

' Get the folder containing this VBS
thisFolder = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))

' Define the project subfolder and batch path
projectFolder = thisFolder & "src\"                ' note trailing slash
batPath       = projectFolder & "run.bat"      ' your setup/start script

' 1) Run the batch file hidden and asynchronous
shell.Run """" & batPath & """", 0, False

' 2) Wait ~5 seconds for Django to start
WScript.Sleep 5000

' 3) Launch the browser to the admin page (or your root)
shell.Run "http://localhost:8000/admin/base/", 1, False
