@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist "%~dp0.runtime\pythonw.exe" (
  where python >nul 2>nul
  if errorlevel 1 (
    echo 缺少项目运行时，且未找到可用的 Python 来安装它。
    pause
    exit /b 1
  )
  python "%~dp0tools\bootstrap_runtime.py"
  if errorlevel 1 (
    echo 项目运行时安装失败。
    pause
    exit /b 1
  )
)
start "" "%~dp0.runtime\pythonw.exe" "%~dp0launcher.py"
