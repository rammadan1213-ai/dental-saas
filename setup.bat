@echo off
REM Dental Clinic Management System - Quick Setup Script

echo ====================================
echo Dental Clinic Management System
echo Quick Setup Script
echo ====================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9 or higher
    pause
    exit /b 1
)

echo Step 1: Creating virtual environment...
python -m venv venv

echo Step 2: Activating virtual environment...
call venv\Scripts\activate.bat

echo Step 3: Installing dependencies...
pip install -r requirements.txt

echo Step 4: Running migrations...
python manage.py makemigrations
python manage.py migrate

echo Step 5: Creating sample data? (y/n)
set /p create_data=
if /i "%create_data%"=="y" (
    python manage.py create_sample_data
)

echo Step 6: Creating superuser? (y/n)
set /p create_superuser=
if /i "%create_superuser%"=="y" (
    python manage.py createsuperuser
)

echo.
echo ====================================
echo Setup Complete!
echo ====================================
echo.
echo To start the development server:
echo   python manage.py runserver
echo.
echo Default URLs:
echo   Application: http://127.0.0.1:8000/
echo   Admin Panel: http://127.0.0.1:8000/admin/
echo   API: http://127.0.0.1:8000/api/
echo.
pause
