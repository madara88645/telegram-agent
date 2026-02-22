@echo off
cd /d %~dp0
set TELEGRAM_WORKSPACE=%~dp0
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v OPENROUTER_API_KEY 2^>nul') do set OPENROUTER_API_KEY=%%b
python telegram_agent.py
