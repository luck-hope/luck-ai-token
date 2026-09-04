"""
TokenTrackerGateway 独立可执行程序打包脚本
支持 Windows (.exe) 和 macOS (.app / .dmg)
"""
import os
import sys
import subprocess
import platform

def build():
    print("=== 开始执行 PyInstaller 独立打包 ===")
    sep = ";" if platform.system() == "Windows" else ":"
    
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir" if platform.system() == "Darwin" else "--onefile",
        "--windowed",
        "--name", "TokenTrackerGateway",
        "--hidden-import", "ui.settings_dialog",
        "--hidden-import", "ui.widget",
        "--hidden-import", "gateway.proxy",
        "--hidden-import", "config",
        "main.py"
    ]
    
    print("执行命令:", " ".join(cmd))
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n🎉 打包完成！生成文件位于 dist/ 目录中：")
        if platform.system() == "Darwin":
            print("  - macOS 应用程序包: dist/TokenTrackerGateway.app")
        elif platform.system() == "Windows":
            print("  - Windows 可执行文件: dist/TokenTrackerGateway.exe")
        else:
            print("  - Linux 二进制程序: dist/TokenTrackerGateway")
    else:
        print("❌ 打包失败，请检查报错日志。")

if __name__ == "__main__":
    build()
