@echo off
setlocal
cd /d "%~dp0.."

echo === Feature 6-8 offline unit tests ===
.\.venv\Scripts\python.exe -m pytest tests\test_logging_config.py tests\test_error_messages.py tests\test_cli_errors.py tests\test_smoke_test.py tests\test_cli_smoke.py -v -m "not integration"
if errorlevel 1 exit /b 1

echo.
echo === Feature 8 live smoke test (requires .env) ===
.\.venv\Scripts\python.exe cli.py smoke_test
exit /b %errorlevel%
