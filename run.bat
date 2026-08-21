@echo off
echo Устанавливаю зависимости...
pip install -r requirements.txt
echo.
echo Запускаю дашборд...
streamlit run app.py
pause