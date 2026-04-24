@echo off
REM Thin wrapper - all real logic lives in bin\cli.js.
cd /d "%~dp0"
node bin\cli.js
