@echo off
echo ============================================
echo  CMJ Jump Analyzer - Web App
echo ============================================
echo.
echo Installing / verifying dependencies...
pip install -r requirements.txt -q
echo.
echo Starting web server...
echo.
echo  Local:  http://localhost:5000
echo  Phone:  run "ngrok http 5000" in another window
echo          then open the ngrok URL on your phone
echo.
echo Press Ctrl+C to stop the server.
echo ============================================
echo.
python webapp.py
pause
