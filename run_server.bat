@echo off
title Mini Compiler Web IDE Server
echo =======================================================
echo   Starting Mini Compiler Web IDE Local Server...
echo =======================================================
echo.
echo Server running at: http://localhost:8000
echo Press Ctrl+C in this window anytime to stop the server.
echo.
start http://localhost:8000
python -u server.py
pause
