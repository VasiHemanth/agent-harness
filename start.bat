@echo off
setlocal
cd /d "%~dp0"

REM Allow overriding ports from CLI: start.bat 3010 8010
set FRONTEND_PORT=%1
if "%FRONTEND_PORT%"=="" set FRONTEND_PORT=3000

set BACKEND_PORT=%2
if "%BACKEND_PORT%"=="" set BACKEND_PORT=8000

echo Starting TokenTelemetry with FRONTEND_PORT=%FRONTEND_PORT% and BACKEND_PORT=%BACKEND_PORT%...

set FRONTEND_PORT=%FRONTEND_PORT%
set BACKEND_PORT=%BACKEND_PORT%

node bin\cli.js
