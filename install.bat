@echo off
echo Installing CMJ Jump Height Analyzer dependencies...
echo.
pip install -r requirements.txt
echo.
echo ============================================
echo  Installation complete!
echo  Web app: streamlit run app.py
echo  CLI:     python jump_analyzer.py
echo ============================================
pause
