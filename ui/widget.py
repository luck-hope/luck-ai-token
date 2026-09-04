"""
PySide6 跨平台桌面原生悬浮窗 (ui/widget.py)
包含三态无缝切换：
1. circle: 微型圆标 (Orb)
2. capsule: 椭圆摘要胶囊 (CapsuleBar)
3. expanded: 全量网关大屏 (FullGatewayPanel)
"""

import sys
import platform
import webbrowser
from PySide6.QtCore import Qt, QPoint, QRectF, QTimer
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QAction, QGuiApplication,
    QPainterPath, QCursor
)
from PySide6.QtWidgets import QWidget, QMenu, QApplication

class GatewayFloatingWidget(QWidget):
    def __init__(self, port: int = 4000):
        super().__init__()
        self.port = port
        self.mode = "capsule"  # "circle" | "capsule" | "expanded"
        self.tray_manager = None
        self.always_on_top = True
        self.is_dark = True
        
        # 实时指标数据
        self.session_title = "重构流式 usage 提取及悬浮胶囊"
        self.cache_hit_rate = 82.5
        self.total_tokens = 165
        self.requests_count = 1
        self.success_requests_count = 1
        self.cost_cny = 0.0032
        self.provider = "openai"
        self.model = "o3-mini"
        self.total_requests = 10
        self.total_sessions = 3
        self.sprint_title = "当前冲刺: 重构流式 usage 提取及悬浮胶囊"

        # 示例任务列表 (全量面板中显示)
        self.tasks = [
            {"id": 5, "pinned": True, "provider": "openai", "req": 1, "tokens": 165, "hit": 82.5, "model": "o3-mini", "name": "OpenAI 思考模型接入与流式 Token 统计"},
            {"id": 4, "pinned": False, "provider": "deepseek", "req": 2, "tokens": 80, "hit": 75.0, "model": "deepseek-coder", "name": "连接池与长连接健康检查优化"},
            {"id": 3, "pinned": False, "provider": "deepseek", "req": 1, "tokens": 72, "hit": 68.2, "model": "deepseek-coder", "name": "极简悬浮窗置顶与拖拽事件监听"},
            {"id": 2, "pinned": False, "provider": "sensenova", "req": 2, "tokens": 70, "hit": 80.0, "model": "sensenova-v5-5", "name": "商汤日日新 TokenPlan 适配与路由"},
            {"id": 1, "pinned": False, "provider": "bigmodel", "req": 4, "tokens": 276, "hit": 78.6, "model": "glm-4-flash", "name": "智谱 GLM 多模态路由拦截测试"},
        ]

        # 窗口无边框置顶与透明度
        self.apply_window_flags()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.drag_position = QPoint()
        self.set_mode("capsule")
        self.reset_position()

        # 定时轮询状态
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.fetch_latest_state)
        self.poll_timer.start(800)

    def set_tray_manager(self, tray_manager):
        self.tray_manager = tray_manager

    def apply_window_flags(self):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.SubWindow
        if self.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
            
        if platform.system() == "Darwin":
            flags |= Qt.WindowType.WindowDoesNotAcceptFocus
            self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, True)

        self.setWindowFlags(flags)

    def reset_position(self):
        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            top_margin = 44 if platform.system() == "Darwin" else 24
            self.move(geo.right() - self.width() - 40, geo.top() + top_margin)
        else:
            self.move(200, 80)

    def fetch_latest_state(self):
        # 可在此从本地网关 http://127.0.0.1:{port}/health 获取最新 Token 与 Task
        self.update()

    def set_mode(self, mode: str):
        old_center = self.geometry().center()
        self.mode = mode
        if mode == "circle":
            self.resize(48, 48)
        elif mode == "capsule":
            self.resize(420, 44)
        elif mode == "expanded":
            self.resize(760, 480)
        
        # 保持中心点基本平滑
        self.move(old_center.x() - self.width() // 2, old_center.y() - self.height() // 2)
        self.update()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #11141c;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 6px;
                color: #e2e8f0;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 20px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #2563eb;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: rgba(255, 255, 255, 0.1);
                margin: 4px 6px;
            }
        """)

        mode_menu = menu.addMenu("🔄 切换视图形态")
        m_capsule = QAction("长条胶囊 (Capsule)", mode_menu)
        m_capsule.triggered.connect(lambda: self.set_mode("capsule"))
        m_circle = QAction("微型圆标 (Orb)", mode_menu)
        m_circle.triggered.connect(lambda: self.set_mode("circle"))
        m_expand = QAction("全量面板 (Full Panel)", mode_menu)
        m_expand.triggered.connect(lambda: self.set_mode("expanded"))
        mode_menu.addAction(m_capsule)
        mode_menu.addAction(m_circle)
        mode_menu.addAction(m_expand)

        top_action = QAction("✓ 保持窗口置顶" if self.always_on_top else "📌 保持窗口置顶", menu)
        def toggle_top():
            self.always_on_top = not self.always_on_top
            self.apply_window_flags()
            self.show()
        top_action.triggered.connect(toggle_top)
        menu.addAction(top_action)

        reset_act = QAction("🎯 重置到右上角", menu)
        reset_act.triggered.connect(self.reset_position)
        menu.addAction(reset_act)

        menu.addSeparator()

        copy_act = QAction(f"📋 复制 IDE 接入地址 (http://127.0.0.1:{self.port}/v1)", menu)
        copy_act.triggered.connect(lambda: QApplication.clipboard().setText(f"http://127.0.0.1:{self.port}/v1"))
        menu.addAction(copy_act)

        menu.addSeparator()

        quit_act = QAction("🚪 退出 UsageGateway", menu)
        if self.tray_manager:
            quit_act.triggered.connect(self.tray_manager.quit_application)
        else:
            quit_act.triggered.connect(self.close)
        menu.addAction(quit_act)

        menu.exec(event.globalPos())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            if platform.system() == "Darwin":
                new_pos.setY(max(26, new_pos.y()))
            self.move(new_pos)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            modes = ["circle", "capsule", "expanded"]
            next_idx = (modes.index(self.mode) + 1) % len(modes)
            self.set_mode(modes[next_idx])

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.set_mode("capsule" if self.mode == "expanded" else "circle")
        elif event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Space):
            modes = ["circle", "capsule", "expanded"]
            next_idx = (modes.index(self.mode) + 1) % len(modes)
            self.set_mode(modes[next_idx])

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)

        # 1. 微型圆标态 (Orb)
        if self.mode == "circle":
            painter.setBrush(QBrush(QColor(11, 15, 25, 245)))
            painter.setPen(QPen(QColor(40, 50, 70), 1.5))
            painter.drawEllipse(rect)

            # 外圈命中率绿色刻度环
            green_pen = QPen(QColor(52, 211, 153), 3.0)
            green_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(green_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            span = int((self.cache_hit_rate / 100.0) * 360 * 16)
            painter.drawArc(rect.adjusted(4, 4, -4, -4), 90 * 16, -span)

            # 中心亮蓝呼吸核心
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(56, 189, 248)))
            painter.drawEllipse(rect.adjusted(14, 14, -14, -14))
            return

        # 2. 椭圆摘要胶囊态 (CapsuleBar)
        if self.mode == "capsule":
            radius = rect.height() / 2
            painter.setBrush(QBrush(QColor(13, 17, 26, 248)))
            painter.setPen(QPen(QColor(38, 46, 62), 1.2))
            painter.drawRoundedRect(rect, radius, radius)

            # 左侧微型圆标
            orb_rect = QRectF(rect.x() + 5, rect.y() + 5, 34, 34)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(20, 26, 38)))
            painter.drawEllipse(orb_rect)

            green_pen = QPen(QColor(52, 211, 153), 2.5)
            green_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(green_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            span = int((self.cache_hit_rate / 100.0) * 360 * 16)
            painter.drawArc(orb_rect.adjusted(3, 3, -3, -3), 90 * 16, -span)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(56, 189, 248)))
            painter.drawEllipse(orb_rect.adjusted(10, 10, -10, -10))

            # 服务商绿色小方块
            prov_rect = QRectF(rect.x() + 45, rect.y() + 7, 30, 30)
            painter.setBrush(QBrush(QColor(16, 185, 129, 30)))
            painter.setPen(QPen(QColor(16, 185, 129, 80), 1))
            painter.drawRoundedRect(prov_rect, 6, 6)

            # 居中首会话截断标题
            painter.setPen(QColor(241, 245, 249))
            font = QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 9, QFont.Weight.Bold)
            painter.setFont(font)
            title_rect = QRectF(rect.x() + 84, rect.y(), 120, rect.height())
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignVCenter, self.session_title[:10] + "..")

            # 请求数药丸
            req_x = rect.x() + 210
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(30, 41, 59)))
            painter.drawRoundedRect(QRectF(req_x, rect.y() + 9, 44, 26), 13, 13)
            painter.setPen(QColor(203, 213, 225))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.drawText(QRectF(req_x, rect.y() + 9, 44, 26), Qt.AlignmentFlag.AlignCenter, f"请求 {self.requests_count}")

            # Token 药丸
            tok_x = req_x + 48
            painter.setBrush(QBrush(QColor(26, 33, 48)))
            painter.drawRoundedRect(QRectF(tok_x, rect.y() + 9, 58, 26), 13, 13)
            painter.setPen(QColor(148, 163, 184))
            painter.drawText(QRectF(tok_x, rect.y() + 9, 58, 26), Qt.AlignmentFlag.AlignCenter, f"tok {self.total_tokens}")

            # 命中率药丸
            hit_x = tok_x + 62
            painter.setBrush(QBrush(QColor(6, 78, 59, 180)))
            painter.setPen(QPen(QColor(52, 211, 153, 120), 1))
            painter.drawRoundedRect(QRectF(hit_x, rect.y() + 9, 60, 26), 13, 13)
            painter.setPen(QColor(52, 211, 153))
            painter.drawText(QRectF(hit_x, rect.y() + 9, 60, 26), Qt.AlignmentFlag.AlignCenter, f"⚡ {self.cache_hit_rate:.1f}%")

            # 展开箭头
            arrow_x = hit_x + 68
            painter.setPen(QColor(148, 163, 184))
            painter.setFont(QFont("Arial", 9))
            painter.drawText(QRectF(arrow_x, rect.y(), 20, rect.height()), Qt.AlignmentFlag.AlignCenter, "⤢")
            return

        # 3. 全量大屏面板态 (Full Dashboard Panel)
        if self.mode == "expanded":
            painter.setBrush(QBrush(QColor(13, 17, 26, 252)))
            painter.setPen(QPen(QColor(45, 55, 75), 1.5))
            painter.drawRoundedRect(rect, 14, 14)

            # 顶部标题栏
            header_rect = QRectF(rect.x(), rect.y(), rect.width(), 48)
            painter.setBrush(QBrush(QColor(18, 24, 38)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(header_rect, 14, 14)
            painter.drawRect(QRectF(rect.x(), rect.y() + 30, rect.width(), 18))

            # macOS 风格红黄绿小圆点
            painter.setBrush(QBrush(QColor(239, 68, 68)))
            painter.drawEllipse(QRectF(rect.x() + 16, rect.y() + 18, 12, 12))
            painter.setBrush(QBrush(QColor(245, 158, 11)))
            painter.drawEllipse(QRectF(rect.x() + 34, rect.y() + 18, 12, 12))
            painter.setBrush(QBrush(QColor(16, 185, 129)))
            painter.drawEllipse(QRectF(rect.x() + 52, rect.y() + 18, 12, 12))

            # 用量网关标题与端口
            painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 10, QFont.Weight.Bold))
            painter.setPen(QColor(241, 245, 249))
            painter.drawText(QRectF(rect.x() + 74, rect.y(), 70, 48), Qt.AlignmentFlag.AlignVCenter, "用量网关")

            painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
            painter.setBrush(QBrush(QColor(12, 74, 110)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(rect.x() + 144, rect.y() + 15, 50, 18), 4, 4)
            painter.setPen(QColor(56, 189, 248))
            painter.drawText(QRectF(rect.x() + 144, rect.y() + 15, 50, 18), Qt.AlignmentFlag.AlignCenter, f":{self.port}")

            # 汇总指标
            painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 9))
            painter.setPen(QColor(148, 163, 184))
            painter.drawText(QRectF(rect.x() + 205, rect.y(), 300, 48), Qt.AlignmentFlag.AlignVCenter, f"请求 {self.total_requests} · 会话 {self.total_sessions} · 命中 {self.cache_hit_rate:.1f}%")

            # 折叠回胶囊按钮
            painter.setFont(QFont("Arial", 11))
            painter.setPen(QColor(148, 163, 184))
            painter.drawText(QRectF(rect.right() - 40, rect.y(), 30, 48), Qt.AlignmentFlag.AlignCenter, "⤡")

            # 冲刺横条
            sprint_rect = QRectF(rect.x() + 16, rect.y() + 58, rect.width() - 32, 34)
            painter.setBrush(QBrush(QColor(18, 24, 38)))
            painter.setPen(QPen(QColor(38, 48, 68), 1))
            painter.drawRoundedRect(sprint_rect, 6, 6)
            painter.setPen(QColor(52, 211, 153))
            painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 9, QFont.Weight.Bold))
            painter.drawText(sprint_rect.adjusted(12, 0, 0, 0), Qt.AlignmentFlag.AlignVCenter, f"☑ {self.sprint_title}")

            # 表头
            th_y = rect.y() + 104
            painter.setPen(QColor(148, 163, 184))
            painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 8, QFont.Weight.Bold))
            painter.drawText(QRectF(rect.x() + 20, th_y, 30, 20), Qt.AlignmentFlag.AlignCenter, "📌")
            painter.drawText(QRectF(rect.x() + 55, th_y, 35, 20), Qt.AlignmentFlag.AlignCenter, "#")
            painter.drawText(QRectF(rect.x() + 95, th_y, 60, 20), Qt.AlignmentFlag.AlignCenter, "服务商")
            painter.drawText(QRectF(rect.x() + 160, th_y, 60, 20), Qt.AlignmentFlag.AlignCenter, "请求数")
            painter.drawText(QRectF(rect.x() + 225, th_y, 70, 20), Qt.AlignmentFlag.AlignCenter, "总消耗")
            painter.drawText(QRectF(rect.x() + 300, th_y, 65, 20), Qt.AlignmentFlag.AlignCenter, "命中率")
            painter.drawText(QRectF(rect.x() + 375, th_y, 110, 20), Qt.AlignmentFlag.AlignLeft, "模型")
            painter.drawText(QRectF(rect.x() + 490, th_y, 240, 20), Qt.AlignmentFlag.AlignLeft, "任务标题")

            # 表格数据行
            row_y = th_y + 26
            for idx, item in enumerate(self.tasks):
                row_rect = QRectF(rect.x() + 16, row_y, rect.width() - 32, 42)
                bg = QColor(22, 30, 46) if item["pinned"] else (QColor(16, 21, 32) if idx % 2 == 0 else QColor(13, 17, 26))
                painter.setBrush(QBrush(bg))
                painter.setPen(QPen(QColor(30, 41, 59), 0.8))
                painter.drawRoundedRect(row_rect, 4, 4)

                # 钉住状态
                painter.setFont(QFont("Arial", 9))
                painter.setPen(QColor(245, 158, 11) if item["pinned"] else QColor(100, 116, 139))
                painter.drawText(QRectF(rect.x() + 20, row_y, 30, 42), Qt.AlignmentFlag.AlignCenter, "📌")

                # ID
                painter.setFont(QFont("Consolas", 9))
                painter.setPen(QColor(148, 163, 184))
                painter.drawText(QRectF(rect.x() + 55, row_y, 35, 42), Qt.AlignmentFlag.AlignCenter, f"#{item['id']}")

                # 服务商
                painter.drawText(QRectF(rect.x() + 95, row_y, 60, 42), Qt.AlignmentFlag.AlignCenter, item["provider"])

                # 请求数
                painter.setPen(QColor(52, 211, 153))
                painter.drawText(QRectF(rect.x() + 160, row_y, 60, 42), Qt.AlignmentFlag.AlignCenter, f"✓ {item['req']}")

                # 总消耗
                painter.setPen(QColor(56, 189, 248))
                painter.drawText(QRectF(rect.x() + 225, row_y, 70, 42), Qt.AlignmentFlag.AlignCenter, f"{item['tokens']} tok")

                # 命中率
                painter.setPen(QColor(52, 211, 153))
                painter.drawText(QRectF(rect.x() + 300, row_y, 65, 42), Qt.AlignmentFlag.AlignCenter, f"⚡{item['hit']:.1f}%")

                # 模型
                painter.setPen(QColor(203, 213, 225))
                painter.setFont(QFont("Consolas", 8))
                painter.drawText(QRectF(rect.x() + 375, row_y, 110, 42), Qt.AlignmentFlag.AlignVCenter, item["model"])

                # 任务标题
                painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 9, QFont.Weight.Bold))
                painter.setPen(QColor(241, 245, 249))
                painter.drawText(QRectF(rect.x() + 490, row_y, 240, 42), Qt.AlignmentFlag.AlignVCenter, item["name"])

                row_y += 48

            # 底部状态栏与接入地址
            footer_y = rect.bottom() - 40
            painter.setBrush(QBrush(QColor(18, 24, 38)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(rect.x(), footer_y, rect.width(), 40), 14, 14)

            painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 8))
            painter.setPen(QColor(148, 163, 184))
            painter.drawText(QRectF(rect.x() + 20, footer_y, 40, 40), Qt.AlignmentFlag.AlignVCenter, "接入:")

            # 绿色接入 URL 药丸 (支持点击复制)
            url_rect = QRectF(rect.x() + 60, footer_y + 8, 190, 24)
            painter.setBrush(QBrush(QColor(6, 78, 59, 160)))
            painter.setPen(QPen(QColor(52, 211, 153, 100), 1))
            painter.drawRoundedRect(url_rect, 4, 4)
            painter.setPen(QColor(52, 211, 153))
            painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
            painter.drawText(url_rect, Qt.AlignmentFlag.AlignCenter, f"http://127.0.0.1:{self.port}/v1 📋")

            painter.setPen(QColor(100, 116, 139))
            painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 8))
            painter.drawText(QRectF(rect.x() + 265, footer_y, 260, 40), Qt.AlignmentFlag.AlignVCenter, "· 支持按键滑动 W/A/S/D ↑↓←→")

            painter.drawText(QRectF(rect.right() - 140, footer_y, 120, 40), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"共 {len(self.tasks)} 条   < 1 / 1 >")
