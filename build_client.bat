@echo off

cd client

cmake --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: CMake не найден!
    echo Установите CMake с https://cmake.org
    pause
    exit /b 1
)

if not exist "build" mkdir build
cd build

echo Поиск доступной версии Visual Studio...

cmake .. -G "Visual Studio 17 2022" -A x64 >nul 2>&1
if not errorlevel 1 (
    echo Найдена Visual Studio 2022
    goto :build
)

cmake .. -G "Visual Studio 16 2019" -A x64 >nul 2>&1
if not errorlevel 1 (
    echo Найдена Visual Studio 2019
    goto :build
)

cmake .. -G "Visual Studio 15 2017" -A x64 >nul 2>&1
if not errorlevel 1 (
    echo Найдена Visual Studio 2017
    goto :build
)

cmake .. -G "MinGW Makefiles" >nul 2>&1
if not errorlevel 1 (
    echo Найден MinGW
    goto :build
)

echo Ошибка: Не найдена подходящая версия Visual Studio!
echo Установите одну из версий:
echo - Visual Studio 2022 Community (рекомендуется)
echo - Visual Studio 2019 Community
echo - Visual Studio 2017 Community
echo - MinGW
echo.
echo Скачать Visual Studio: https://visualstudio.microsoft.com/downloads/
pause
exit /b 1

:build
echo Генерация проекта...
cmake .. -A x64
if errorlevel 1 (
    echo Ошибка генерации проекта!
    pause
    exit /b 1
)

echo Сборка проекта...
cmake --build . --config Release
if errorlevel 1 (
    echo Ошибка сборки!
    pause
    exit /b 1
)

echo Копирование исполняемого файла...
if exist "Release\monitor_client.exe" (
    copy "Release\monitor_client.exe" "..\monitor_client.exe"
) else if exist "monitor_client.exe" (
    copy "monitor_client.exe" "..\monitor_client.exe"
) else (
    echo Предупреждение: Исполняемый файл не найден в ожидаемом месте
    echo Проверьте папку build для результатов сборки
)

echo Сборка завершена!
echo Исполняемый файл: client\monitor_client.exe
pause 