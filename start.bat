@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting LLM Document Query System...
echo Web UI will be available at: http://localhost:8000
echo API docs available at: http://localhost:8000/docs
echo.

uvicorn main:app --host 0.0.0.0 --port 8000 --reload