@echo off
echo ========================================
echo   Сборка дашборда в .exe файл
echo ========================================
echo.

echo Устанавливаю зависимости...
pip install -r requirements.txt

echo.
echo Собираю .exe файл...
pyinstaller --onefile --add-data "Bak.xlsx;." --collect-all streamlit --collect-all plotly --collect-all pandas --hidden-import=streamlit --hidden-import=plotly.express --hidden-import=pandas app.py

echo.
echo ========================================
if exist dist\app.exe (
    echo   УСПЕШНО! .exe файл в папке dist
) else (
    echo   ОШИБКА! Что-то пошло не так.
    echo   Проверьте сообщения выше.
)
echo ========================================

echo.
echo Нажмите любую клавишу для выхода...
pause > nul