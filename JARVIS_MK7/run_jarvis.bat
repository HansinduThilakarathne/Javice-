@echo off
title J.A.R.V.I.S. MARK VII - Primary Administrator: Manuja
echo =======================================================
echo    J.A.R.V.I.S. MARK VII (STARK INDUSTRIES ARCHITECTURE)
echo    SOLE USER BIOMETRIC SECURITY GATE: MANUJA
echo =======================================================
cd /d "%~dp0"
py -3.11 app.py || python app.py
pause
