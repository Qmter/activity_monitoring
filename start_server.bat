@echo off

cd server

python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не найден!
    echo Установите Python с https://python.org
    pause
    exit /b 1
)

python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo Установка зависимостей...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Ошибка установки зависимостей!
        echo Попробуйте запустить install_dependencies.bat
        pause
        exit /b 1
    )
)

echo Запуск сервера на http://localhost:8000
python main.py

pause 