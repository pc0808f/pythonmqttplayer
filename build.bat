@echo off
echo =====================================
echo Python MQTT Player 打包脚本
echo =====================================
echo.

echo 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python环境
    pause
    exit /b 1
)

echo.
echo 安装/更新依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo 警告: 依赖包安装可能有问题，继续执行...
)

echo.
echo 开始打包应用程序...
python build.py

echo.
echo 打包完成！按任意键退出...
pause