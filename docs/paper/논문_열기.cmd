@echo off
chcp 65001 >nul
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
  start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" "%~dp0작성용_HTML\index.html"
) else (
  start "" "%~dp0작성용_HTML\index.html"
)
