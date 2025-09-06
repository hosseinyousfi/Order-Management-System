@echo off
REM ── change into script’s own directory ──
pushd "%~dp0"

REM ── force Python to search this folder first ──
set PYTHONPATH=%~dp0


REM ── apply migrations ──
python-embed\python.exe manage.py collectstatic --noinput
python-embed\python.exe manage.py makemigrations --noinput
python-embed\python.exe manage.py migrate

REM ── start server ──
python-embed\python.exe run_waitress.py

popd
pause