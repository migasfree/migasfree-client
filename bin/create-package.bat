@echo off
REM Copyright (c) 2011-2025 Jose Antonio Chavarría <jachavar@gmail.com>
REM Script to create Windows distribution packages

cd ..

echo Creating Windows packages...
python setup.py bdist_wininst
python setup.py bdist
python setup.py bdist --format=msi

echo.
echo Package creation completed.
echo.
echo Python requirements:
echo   * Python ^>= 3.6
echo   * python-magic-bin
echo   * pywin32
echo   * psutil
echo   * netifaces
echo   * jwcrypto
echo   * requests
echo   * requests-toolbelt
echo   * rich
echo   * cryptography
