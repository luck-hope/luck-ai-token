"""
TokenTrackerGateway - 跨平台 AI 用量网关与桌面原生悬浮胶囊监控
运行环境: Python 3.10+
支持系统: macOS (Apple Silicon/Intel), Windows 10/11, Linux

特性:
1. 后台自动化多线程 Uvicorn FastAPI 网关 (默认端口 4000);
2. 跨平台 PySide6 桌面原生无边框置顶悬浮窗 (支持拖拽、右键快捷菜单、双击切换形态);
3. 三态无缝切换：微型圆标 (Orb) ↔ 椭圆摘要胶囊 (CapsuleBar) ↔ 全量大屏监控 (Full Panel);
4. 系统常驻托盘图标 (QSystemTrayIcon)，支持一键显隐与安全退出。
"""

import sys
import os
import io
import logging

# ---------------------------------------------------------------------------
# 修复 Windows / macOS 下 PyInstaller --noconsole / --windowed 打包时
# sys.stdout / sys.stderr / sys.stdin 为 None 导致的 AttributeError: 'NoneType' object has no attribute 'isatty'
# ---------------------------------------------------------------------------
class SafeStream(io.StringIO):
    def write(self, s):
        pass
    def flush(self):
        pass
    def isatty(self):
        return False
    def fileno(self):
        raise io.UnsupportedOperation("fileno not supported")

if sys.stdout is None:
    sys.stdout = SafeStream()
if sys.stderr is None:
    sys.stderr = SafeStream()
if sys.stdin is None:
    sys.stdin = SafeStream()

import signal
import threading
import uvicorn
import platform
import webbrowser
from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QMessageBox
)
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen, QAction
from PySide6.QtCore import Qt, QRectF

from gateway.proxy import app as gateway_app
from ui.widget import GatewayFloatingWidget
from config import GATEWAY_HOST, GATEWAY_PORT

class GatewayAppServer:
    """网关后台服务管理器"""
    def __init__(self, host=GATEWAY_HOST, port=GATEWAY_PORT):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        # 自定义无色彩、无 isatty 依赖的安全日志配置，杜绝 Windows 打包后 uvicorn logging 崩溃
        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                # uvicorn 0.52+ configure_logging 会无条件访问 formatters["default"] / ["access"]
                # 键名必须是 default / access，否则 KeyError: 'default'
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "use_colors": False,
                },
                "access": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "use_colors": False,
                },
            },
            "handlers": {
                "null": {
                    "class": "logging.NullHandler",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["null"], "level": "WARNING", "propagate": False},
                "uvicorn.error": {"handlers": ["null"], "level": "WARNING", "propagate": False},
                "uvicorn.access": {"handlers": ["null"], "level": "WARNING", "propagate": False},
            },
        }

        config = uvicorn.Config(
            gateway_app,
            host=self.host,
            port=self.port,
            log_level="warning",
            loop="asyncio",
            use_colors=False,
            log_config=log_config,
        )
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        print(f"[Gateway] 🚀 本地代理网关已就绪: http://{self.host}:{self.port}/v1")

    def stop(self):
        if self.server:
            self.server.should_exit = True
            print("[Gateway] 网关服务正在安全停止...")

def create_default_tray_icon() -> QIcon:
    """动态生成暗夜翠绿雷电指示灯托盘矢量图标"""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 1. 绘制暗黑圆角底框
    painter.setBrush(QBrush(QColor(17, 24, 39)))
    painter.setPen(QPen(QColor(74, 222, 128), 3))
    painter.drawRoundedRect(QRectF(4, 4, 56, 56), 16, 16)

    # 2. 绘制翠绿核心指示灯
    painter.setBrush(QBrush(QColor(34, 197, 94)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(QRectF(22, 22, 20, 20))

    # 3. 绘制中心微光
    painter.setBrush(QBrush(QColor(220, 252, 231)))
    painter.drawEllipse(QRectF(27, 27, 10, 10))
    painter.end()

    return QIcon(pixmap)

class SystemTrayManager:
    """系统托盘管理器"""
    def __init__(self, app: QApplication, widget: GatewayFloatingWidget, gateway_server: GatewayAppServer):
        self.app = app
        self.widget = widget
        self.gateway_server = gateway_server
        self.tray_icon = QSystemTrayIcon()
        self.init_tray()

    def init_tray(self):
        self.tray_icon.setIcon(create_default_tray_icon())
        self.tray_icon.setToolTip(f"TokenTrackerGateway (127.0.0.1:{GATEWAY_PORT}) - 运行中")

        menu = QMenu()

        status_action = QAction(f"🟢 网关状态: 运行中 (:{GATEWAY_PORT})", menu)
        status_action.setEnabled(False)
        menu.addAction(status_action)
        menu.addSeparator()

        self.toggle_action = QAction("👁️ 显示/隐藏 悬浮胶囊", menu)
        self.toggle_action.triggered.connect(self.toggle_widget)
        menu.addAction(self.toggle_action)

        mode_menu = menu.addMenu("🔄 切换显示形态")
        act_capsule = QAction("椭圆摘要胶囊 (Capsule)", mode_menu)
        act_capsule.triggered.connect(lambda: self.widget.set_mode("capsule"))
        act_circle = QAction("微型圆标 (Orb)", mode_menu)
        act_circle.triggered.connect(lambda: self.widget.set_mode("circle"))
        act_expand = QAction("全量网关大屏 (Full Panel)", mode_menu)
        act_expand.triggered.connect(lambda: self.widget.set_mode("expanded"))
        mode_menu.addAction(act_capsule)
        mode_menu.addAction(act_circle)
        mode_menu.addAction(act_expand)

        reset_action = QAction("🎯 重置悬浮窗位置 (右上角)", menu)
        reset_action.triggered.connect(self.widget.reset_position)
        menu.addAction(reset_action)

        menu.addSeparator()

        copy_action = QAction(f"📋 复制 IDE 接入地址 (http://127.0.0.1:{GATEWAY_PORT}/v1)", menu)
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(f"http://127.0.0.1:{GATEWAY_PORT}/v1"))
        menu.addAction(copy_action)

        menu.addSeparator()

        quit_action = QAction("🚪 退出 TokenTrackerGateway", menu)
        quit_action.triggered.connect(self.quit_application)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.showMessage(
                "AI 用量监控已就绪",
                "桌面悬浮看板已启动（直连即用），双击悬浮窗或托盘图标切换视图。",
                QSystemTrayIcon.MessageIcon.Information,
                2500
            )

    def toggle_widget(self):
        if self.widget.isVisible():
            self.widget.hide()
        else:
            self.widget.show()
            self.widget.activateWindow()

    def on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.toggle_widget()

    def quit_application(self):
        print("[App] 正在退出应用...")
        self.gateway_server.stop()
        self.widget.close()
        self.tray_icon.hide()
        self.app.quit()

def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        QApplication.highDpiScaleFactorRoundingPolicy().PassThrough
    )
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("TokenTrackerGateway")
    qt_app.setQuitOnLastWindowClosed(False)

    server = GatewayAppServer()
    server.start()

    widget = GatewayFloatingWidget(port=GATEWAY_PORT)
    widget.show()

    tray_manager = SystemTrayManager(qt_app, widget, server)
    widget.set_tray_manager(tray_manager)

    signal.signal(signal.SIGINT, lambda *args: tray_manager.quit_application())

    print("[UI] 桌面原生悬浮窗已就绪！")
    print("      - 单击拖拽移动位置")
    print("      - 双击切换形态：微型圆标 (Orb) ↔ 摘要胶囊 (Capsule) ↔ 全量面板 (Dashboard)")
    print("      - 右键打开快捷操作菜单")
    sys.exit(qt_app.exec())

if __name__ == "__main__":
    main()
