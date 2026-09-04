"""
PySide6 跨平台桌面原生悬浮窗 (ui/widget.py)
包含三态无缝切换：
1. circle: 微型圆标 (Orb)
2. capsule: 椭圆摘要胶囊 (CapsuleBar) - 具备任务切换、服务商徽标、快速设置、明暗主题与大触控区展开
3. expanded: 全量网关大屏 (FullGatewayPanel) - 具备完整表单、设置窗口交互、状态栏与快捷工具
"""

import sys
import platform
import webbrowser
from PySide6.QtCore import Qt, QPoint, QRectF, QTimer
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QAction, QGuiApplication,
    QCursor
)
from PySide6.QtWidgets import QWidget, QMenu, QApplication, QMessageBox

from ui.settings_dialog import SettingsDialog
from config import GATEWAY_HOST, GATEWAY_PORT

class GatewayFloatingWidget(QWidget):
    def __init__(self, port: int = GATEWAY_PORT):
        super().__init__()
        self.port = port
        self.mode = "capsule"  # "circle" | "capsule" | "expanded"
        self.tray_manager = None
        self.always_on_top = True
        self.is_dark = True
        self.show_cost = False  # False: 显示 Token 数, True: 显示人民币预估
        self.copied_feedback = False  # 是否展示复制成功提示

        # 当前选中的活跃任务索引
        self.current_task_idx = 0
        self.active_tab = "tasks"  # "tasks" | "sessions"
        self.selected_date = "2026-09-03"

        # 任务列表
        self.tasks = [
            {"id": 5, "pinned": True, "provider": "openai", "req": 1, "tokens": 165, "hit": 82.5, "cost": 0.0032, "model": "o3-mini", "name": "OpenAI 思考模型接入与流式 Token 统计"},
            {"id": 4, "pinned": False, "provider": "deepseek", "req": 2, "tokens": 80, "hit": 75.0, "cost": 0.0012, "model": "deepseek-coder", "name": "连接池与长连接健康检查优化"},
            {"id": 3, "pinned": False, "provider": "deepseek", "req": 1, "tokens": 72, "hit": 68.2, "cost": 0.0011, "model": "deepseek-coder", "name": "极简悬浮窗置顶与拖拽事件监听"},
            {"id": 2, "pinned": False, "provider": "sensenova", "req": 2, "tokens": 70, "hit": 80.0, "cost": 0.0010, "model": "sensenova-v5-5", "name": "商汤日日新 TokenPlan 适配与路由"},
            {"id": 1, "pinned": False, "provider": "bigmodel", "req": 4, "tokens": 276, "hit": 78.6, "cost": 0.0041, "model": "glm-4-flash", "name": "智谱 GLM 多模态路由拦截测试"},
        ]

        # 会话列表
        self.sessions = [
            {"id": "sess_001", "name": "主业务网关路由与流式转发", "provider": "openai", "model": "o3-mini", "req": 5, "tokens": 345, "hit": 82.5, "time": "14:32:05"},
            {"id": "sess_002", "name": "代码重构辅助与测试验证", "provider": "deepseek", "model": "deepseek-coder", "req": 3, "tokens": 152, "hit": 72.0, "time": "14:28:10"},
            {"id": "sess_003", "name": "商汤多模态图片识别分析", "provider": "sensenova", "model": "sensenova-v5-5", "req": 2, "tokens": 70, "hit": 80.0, "time": "14:15:33"},
        ]

        self.sprint_title = "当前冲刺: 重构流式 usage 提取及悬浮胶囊"

        # 交互区域缓存 (在 paintEvent 中动态登记，在 mousePressEvent/mouseMoveEvent 中命中判定)
        self.clickable_regions = []
        self.hovered_region_id = None

        # 窗口无边框置顶与透明度
        self.apply_window_flags()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)

        self.drag_position = QPoint()
        self.is_dragging = False
        self.set_mode("capsule")
        self.reset_position()

        # 状态刷新定时器
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.fetch_latest_state)
        self.poll_timer.start(800)

        # 复制反馈倒计时
        self.feedback_timer = QTimer(self)
        self.feedback_timer.setSingleShot(True)
        self.feedback_timer.timeout.connect(self.clear_copied_feedback)

    @property
    def current_task(self):
        if 0 <= self.current_task_idx < len(self.tasks):
            return self.tasks[self.current_task_idx]
        return self.tasks[0]

    @property
    def cache_hit_rate(self):
        return self.current_task.get("hit", 82.5)

    @property
    def total_tokens(self):
        return self.current_task.get("tokens", 165)

    @property
    def cost_cny(self):
        return self.current_task.get("cost", 0.0032)

    @property
    def requests_count(self):
        return self.current_task.get("req", 1)

    @property
    def session_title(self):
        return self.current_task.get("name", "未命名会话")

    @property
    def provider(self):
        return self.current_task.get("provider", "openai")

    @property
    def total_requests(self):
        return sum(t.get("req", 1) for t in self.tasks)

    @property
    def total_sessions(self):
        return len(self.tasks)

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
        self.update()

    def set_mode(self, mode: str):
        old_center = self.geometry().center()
        self.mode = mode
        if mode == "circle":
            self.resize(48, 48)
        elif mode == "capsule":
            self.resize(520, 44)
        elif mode == "expanded":
            self.resize(780, 500)
        
        self.move(old_center.x() - self.width() // 2, old_center.y() - self.height() // 2)
        self.update()

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.update()

    def open_settings(self):
        dlg = SettingsDialog(
            parent=self,
            is_dark=self.is_dark,
            on_save_callback=self.on_settings_saved
        )
        dlg.exec()

    def on_settings_saved(self, settings: dict):
        self.port = settings.get("port", self.port)
        self.always_on_top = settings.get("always_on_top", True)
        self.is_dark = settings.get("is_dark", True)
        opacity = settings.get("opacity", 1.0)
        self.setWindowOpacity(opacity)
        self.apply_window_flags()
        self.show()
        if "mode" in settings:
            self.set_mode(settings["mode"])
        self.update()

    def prev_task(self):
        self.current_task_idx = (self.current_task_idx - 1) % len(self.tasks)
        self.update()

    def next_task(self):
        self.current_task_idx = (self.current_task_idx + 1) % len(self.tasks)
        self.update()

    def copy_gateway_url(self):
        url = f"http://127.0.0.1:{self.port}/v1"
        QApplication.clipboard().setText(url)
        self.copied_feedback = True
        self.feedback_timer.start(1800)
        self.update()

    def clear_copied_feedback(self):
        self.copied_feedback = False
        self.update()

    # ------------------------------------------------------------------------
    # 鼠标与快捷键事件处理 (实现 100% 精确触控)
    # ------------------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            # 优先判定是否点击了已登记的按钮控件
            for reg in self.clickable_regions:
                if reg["rect"].contains(pos):
                    act = reg["action"]
                    if act == "shrink_circle":
                        self.set_mode("circle")
                    elif act == "shrink_capsule":
                        self.set_mode("capsule")
                    elif act == "expand_full":
                        self.set_mode("expanded")
                    elif act == "close_app":
                        if self.tray_manager:
                            self.hide()
                        else:
                            self.close()
                    elif act == "prev_task":
                        self.prev_task()
                    elif act == "next_task":
                        self.next_task()
                    elif act == "toggle_cost":
                        self.show_cost = not self.show_cost
                        self.update()
                    elif act == "toggle_theme":
                        self.toggle_theme()
                    elif act == "open_settings":
                        self.open_settings()
                    elif act == "copy_url":
                        self.copy_gateway_url()
                    elif act == "open_web":
                        webbrowser.open(f"http://127.0.0.1:{self.port}")
                    elif act == "toggle_pin":
                        task_id = reg.get("data")
                        for t in self.tasks:
                            if t["id"] == task_id:
                                t["pinned"] = not t["pinned"]
                        self.update()
                    elif act == "select_task":
                        self.current_task_idx = reg.get("data", 0)
                        self.update()
                    elif act == "select_tab":
                        self.active_tab = reg.get("data", "tasks")
                        self.update()
                    event.accept()
                    return

            # 如果未点击任何按钮，则启动窗口拖拽
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        pos = event.position()
        hovered_act = None
        for reg in self.clickable_regions:
            if reg["rect"].contains(pos):
                hovered_act = reg["id"]
                break

        if hovered_act != self.hovered_region_id:
            self.hovered_region_id = hovered_act
            if hovered_act:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()

        if self.is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            if platform.system() == "Darwin":
                new_pos.setY(max(26, new_pos.y()))
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.is_dragging = False

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 双击背景切换形态
            modes = ["circle", "capsule", "expanded"]
            next_idx = (modes.index(self.mode) + 1) % len(modes)
            self.set_mode(modes[next_idx])

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.set_mode("capsule" if self.mode == "expanded" else "circle")
        elif key in (Qt.Key.Key_Tab, Qt.Key.Key_Space):
            modes = ["circle", "capsule", "expanded"]
            next_idx = (modes.index(self.mode) + 1) % len(modes)
            self.set_mode(modes[next_idx])
        elif key in (Qt.Key.Key_Left, Qt.Key.Key_A, Qt.Key.Key_W):
            self.prev_task()
        elif key in (Qt.Key.Key_Right, Qt.Key.Key_D, Qt.Key.Key_S):
            self.next_task()
        elif key == Qt.Key.Key_T:
            self.toggle_theme()
        elif key == Qt.Key.Key_C:
            self.copy_gateway_url()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {'#11141c' if self.is_dark else '#ffffff'};
                border: 1px solid {'rgba(255, 255, 255, 0.15)' if self.is_dark else '#cbd5e1'};
                border-radius: 8px;
                padding: 6px;
                color: {'#e2e8f0' if self.is_dark else '#0f172a'};
                font-size: 12px;
            }}
            QMenu::item {{
                padding: 6px 20px 6px 12px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: #0284c7;
                color: #ffffff;
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {'rgba(255, 255, 255, 0.1)' if self.is_dark else '#e2e8f0'};
                margin: 4px 6px;
            }}
        """)

        mode_menu = menu.addMenu("🔄 切换视图形态")
        m_capsule = QAction("长条胶囊 (Capsule)", mode_menu)
        m_capsule.triggered.connect(lambda: self.set_mode("capsule"))
        m_circle = QAction("微型圆标 (Orb)", mode_menu)
        m_circle.triggered.connect(lambda: self.set_mode("circle"))
        m_expand = QAction("全量看板 (Full Panel)", mode_menu)
        m_expand.triggered.connect(lambda: self.set_mode("expanded"))
        mode_menu.addAction(m_capsule)
        mode_menu.addAction(m_circle)
        mode_menu.addAction(m_expand)

        theme_act = QAction("☀️ 切换浅色白天模式" if self.is_dark else "🌙 切换深色夜间模式", menu)
        theme_act.triggered.connect(self.toggle_theme)
        menu.addAction(theme_act)

        settings_act = QAction("⚙️ 打开参数与路由设置...", menu)
        settings_act.triggered.connect(self.open_settings)
        menu.addAction(settings_act)

        menu.addSeparator()

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

        copy_act = QAction(f"📋 复制接入地址 (http://127.0.0.1:{self.port}/v1)", menu)
        copy_act.triggered.connect(self.copy_gateway_url)
        menu.addAction(copy_act)

        web_act = QAction("🌐 打开 Web 仪表盘", menu)
        web_act.triggered.connect(lambda: webbrowser.open(f"http://127.0.0.1:{self.port}"))
        menu.addAction(web_act)

        menu.addSeparator()

        quit_act = QAction("🚪 退出 TokenTrackerGateway", menu)
        if self.tray_manager:
            quit_act.triggered.connect(self.tray_manager.quit_application)
        else:
            quit_act.triggered.connect(self.close)
        menu.addAction(quit_act)

        menu.exec(event.globalPos())

    # ------------------------------------------------------------------------
    # 原生绘制与控件交互区域注册
    # ------------------------------------------------------------------------
    def paintEvent(self, event):
        self.clickable_regions = []
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)

        # --------------------------------------------------------------------
        # 1. 微型圆标态 (Orb)
        # --------------------------------------------------------------------
        if self.mode == "circle":
            bg_color = QColor(11, 15, 25, 245) if self.is_dark else QColor(255, 255, 255, 245)
            border_color = QColor(40, 50, 70) if self.is_dark else QColor(203, 213, 225)
            painter.setBrush(QBrush(bg_color))
            painter.setPen(QPen(border_color, 1.5))
            painter.drawEllipse(rect)

            # 绿色命中率刻度环
            green_pen = QPen(QColor(52, 211, 153), 3.0)
            green_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(green_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            span = int((self.cache_hit_rate / 100.0) * 360 * 16)
            painter.drawArc(rect.adjusted(4, 4, -4, -4), 90 * 16, -span)

            # 中心亮蓝发光核心
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(56, 189, 248)))
            painter.drawEllipse(rect.adjusted(14, 14, -14, -14))

            # 注册点击圆标展开为胶囊
            self.clickable_regions.append({"id": "orb_expand", "rect": rect, "action": "shrink_capsule"})
            return

        # --------------------------------------------------------------------
        # 2. 椭圆摘要胶囊态 (CapsuleBar)
        # --------------------------------------------------------------------
        if self.mode == "capsule":
            radius = rect.height() / 2
            bg_color = QColor(13, 17, 26, 248) if self.is_dark else QColor(255, 255, 255, 248)
            border_color = QColor(56, 189, 248, 80) if self.is_dark else QColor(203, 213, 225)
            painter.setBrush(QBrush(bg_color))
            painter.setPen(QPen(border_color, 1.2))
            painter.drawRoundedRect(rect, radius, radius)

            # (1) 左侧微型圆标 (点击收缩为 Orb)
            orb_rect = QRectF(rect.x() + 5, rect.y() + 5, 34, 34)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(20, 26, 38) if self.is_dark else QColor(241, 245, 249)))
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
            self.clickable_regions.append({"id": "cap_orb", "rect": orb_rect, "action": "shrink_circle"})

            # (2) 服务商徽标 (OpenAI/DeepSeek/Claude/Sense/GLM)
            prov_rect = QRectF(rect.x() + 44, rect.y() + 8, 48, 28)
            prov_bg = QColor(6, 78, 59, 140) if self.provider == "openai" else QColor(12, 74, 110, 140)
            prov_text_color = QColor(52, 211, 153) if self.provider == "openai" else QColor(56, 189, 248)
            painter.setBrush(QBrush(prov_bg))
            painter.setPen(QPen(prov_text_color, 1))
            painter.drawRoundedRect(prov_rect, 5, 5)
            painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 8, QFont.Weight.Bold))
            painter.setPen(prov_text_color)
            prov_label = "OpenAI" if self.provider == "openai" else ("DeepSeek" if self.provider == "deepseek" else self.provider[:6])
            painter.drawText(prov_rect, Qt.AlignmentFlag.AlignCenter, prov_label)

            # (3) 任务切换器 < 标题 >
            prev_btn_rect = QRectF(rect.x() + 96, rect.y() + 8, 20, 28)
            painter.setPen(QColor(148, 163, 184))
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            painter.drawText(prev_btn_rect, Qt.AlignmentFlag.AlignCenter, "◀")
            self.clickable_regions.append({"id": "cap_prev", "rect": prev_btn_rect, "action": "prev_task"})

            title_rect = QRectF(rect.x() + 118, rect.y(), 115, rect.height())
            painter.setPen(QColor(241, 245, 249) if self.is_dark else QColor(15, 23, 42))
            painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 9, QFont.Weight.Bold))
            title_text = f"#{self.current_task.get('id', 1)} " + self.session_title
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignVCenter, title_text[:11] + "..")
            self.clickable_regions.append({"id": "cap_title", "rect": title_rect, "action": "expand_full"})

            next_btn_rect = QRectF(rect.x() + 235, rect.y() + 8, 20, 28)
            painter.setPen(QColor(148, 163, 184))
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            painter.drawText(next_btn_rect, Qt.AlignmentFlag.AlignCenter, "▶")
            self.clickable_regions.append({"id": "cap_next", "rect": next_btn_rect, "action": "next_task"})

            # (4) 请求数药丸
            req_x = rect.x() + 258
            req_rect = QRectF(req_x, rect.y() + 9, 44, 26)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(30, 41, 59) if self.is_dark else QColor(241, 245, 249)))
            painter.drawRoundedRect(req_rect, 13, 13)
            painter.setPen(QColor(203, 213, 225) if self.is_dark else QColor(71, 85, 105))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.drawText(req_rect, Qt.AlignmentFlag.AlignCenter, f"请求 {self.requests_count}")

            # (5) Token / 金额切换药丸 (点击切换 tok / ¥)
            tok_x = req_x + 48
            tok_rect = QRectF(tok_x, rect.y() + 9, 58, 26)
            painter.setBrush(QBrush(QColor(26, 33, 48) if self.is_dark else QColor(241, 245, 249)))
            painter.drawRoundedRect(tok_rect, 13, 13)
            painter.setPen(QColor(148, 163, 184) if self.is_dark else QColor(100, 116, 139))
            val_text = f"¥{self.cost_cny:.3f}" if self.show_cost else f"tok {self.total_tokens}"
            painter.drawText(tok_rect, Qt.AlignmentFlag.AlignCenter, val_text)
            self.clickable_regions.append({"id": "cap_cost", "rect": tok_rect, "action": "toggle_cost"})

            # (6) 命中率药丸
            hit_x = tok_x + 62
            hit_rect = QRectF(hit_x, rect.y() + 9, 54, 26)
            painter.setBrush(QBrush(QColor(6, 78, 59, 180) if self.is_dark else QColor(236, 253, 245)))
            painter.setPen(QPen(QColor(52, 211, 153, 120), 1))
            painter.drawRoundedRect(hit_rect, 13, 13)
            painter.setPen(QColor(52, 211, 153) if self.is_dark else QColor(5, 150, 105))
            painter.drawText(hit_rect, Qt.AlignmentFlag.AlignCenter, f"⚡ {self.cache_hit_rate:.1f}%")

            # (7) 主题与设置按钮
            theme_x = hit_x + 58
            theme_rect = QRectF(theme_x, rect.y() + 9, 24, 26)
            painter.setPen(QColor(245, 158, 11) if self.is_dark else QColor(100, 116, 139))
            painter.setFont(QFont("Segoe UI Emoji" if platform.system() == "Windows" else "Apple Color Emoji", 9))
            painter.drawText(theme_rect, Qt.AlignmentFlag.AlignCenter, "🌙" if self.is_dark else "☀️")
            self.clickable_regions.append({"id": "cap_theme", "rect": theme_rect, "action": "toggle_theme"})

            settings_x = theme_x + 24
            set_rect = QRectF(settings_x, rect.y() + 9, 24, 26)
            painter.setPen(QColor(148, 163, 184))
            painter.drawText(set_rect, Qt.AlignmentFlag.AlignCenter, "⚙")
            self.clickable_regions.append({"id": "cap_set", "rect": set_rect, "action": "open_settings"})

            # (8) 放大展开全量面板按钮 (大尺寸触控区 30x30)
            expand_x = settings_x + 24
            expand_rect = QRectF(expand_x, rect.y() + 7, 28, 30)
            if self.hovered_region_id == "cap_expand":
                painter.setBrush(QBrush(QColor(56, 189, 248, 60)))
                painter.setPen(QPen(QColor(56, 189, 248), 1))
                painter.drawRoundedRect(expand_rect, 6, 6)
            painter.setPen(QColor(56, 189, 248) if self.hovered_region_id == "cap_expand" else QColor(148, 163, 184))
            painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            painter.drawText(expand_rect, Qt.AlignmentFlag.AlignCenter, "⤢")
            self.clickable_regions.append({"id": "cap_expand", "rect": expand_rect, "action": "expand_full"})
            return

        # --------------------------------------------------------------------
        # 3. 全量大屏看板态 (Full Dashboard Panel)
        # --------------------------------------------------------------------
        if self.mode == "expanded":
            bg_color = QColor(13, 17, 26, 252) if self.is_dark else QColor(255, 255, 255, 252)
            border_color = QColor(45, 55, 75) if self.is_dark else QColor(226, 232, 240)
            painter.setBrush(QBrush(bg_color))
            painter.setPen(QPen(border_color, 1.5))
            painter.drawRoundedRect(rect, 14, 14)

            # 判定平台
            is_mac = (platform.system() == "Darwin")
            header_rect = QRectF(rect.x(), rect.y(), rect.width(), 44)
            painter.setBrush(QBrush(QColor(18, 24, 38) if self.is_dark else QColor(248, 250, 252)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(header_rect, 14, 14)
            painter.drawRect(QRectF(rect.x(), rect.y() + 26, rect.width(), 18))

            title_left_x = rect.x() + 16
            center_y = rect.y() + 22

            if is_mac:
                # ── macOS 风格: 左上角红黄绿红绿灯 ──
                red_hit = QRectF(rect.x() + 8, rect.y() + 6, 24, 30)
                red_circ = QRectF(rect.x() + 14, center_y - 6, 12, 12)
                painter.setBrush(QBrush(QColor(239, 68, 68)))
                painter.setPen(QPen(QColor(220, 38, 38), 0.8))
                painter.drawEllipse(red_circ)
                if self.hovered_region_id == "win_close":
                    painter.setPen(QColor(69, 10, 10))
                    painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                    painter.drawText(red_circ, Qt.AlignmentFlag.AlignCenter, "×")
                self.clickable_regions.append({"id": "win_close", "rect": red_hit, "action": "close_app"})

                yellow_hit = QRectF(rect.x() + 32, rect.y() + 6, 22, 30)
                yellow_circ = QRectF(rect.x() + 36, center_y - 6, 12, 12)
                painter.setBrush(QBrush(QColor(245, 158, 11)))
                painter.setPen(QPen(QColor(217, 119, 6), 0.8))
                painter.drawEllipse(yellow_circ)
                if self.hovered_region_id == "win_orb":
                    painter.setPen(QColor(69, 26, 3))
                    painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                    painter.drawText(yellow_circ, Qt.AlignmentFlag.AlignCenter, "−")
                self.clickable_regions.append({"id": "win_orb", "rect": yellow_hit, "action": "shrink_circle"})

                green_hit = QRectF(rect.x() + 54, rect.y() + 6, 24, 30)
                green_circ = QRectF(rect.x() + 58, center_y - 6, 12, 12)
                painter.setBrush(QBrush(QColor(16, 185, 129)))
                painter.setPen(QPen(QColor(5, 150, 105), 0.8))
                painter.drawEllipse(green_circ)
                if self.hovered_region_id == "win_cap":
                    painter.setPen(QColor(6, 78, 59))
                    painter.setFont(QFont("Arial", 7, QFont.Weight.Bold))
                    painter.drawText(green_circ, Qt.AlignmentFlag.AlignCenter, "⤡")
                self.clickable_regions.append({"id": "win_cap", "rect": green_hit, "action": "shrink_capsule"})

                title_left_x = rect.x() + 82
            else:
                # ── Windows 风格: 左上角天蓝色呼吸指示圆点 ──
                dot_circ = QRectF(rect.x() + 16, center_y - 5, 10, 10)
                painter.setBrush(QBrush(QColor(56, 189, 248)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(dot_circ)
                title_left_x = rect.x() + 34

            # 用量网关标题与端口
            painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 10, QFont.Weight.Bold))
            painter.setPen(QColor(241, 245, 249) if self.is_dark else QColor(15, 23, 42))
            painter.drawText(QRectF(title_left_x, rect.y(), 66, 44), Qt.AlignmentFlag.AlignVCenter, "用量网关")

            port_rect = QRectF(title_left_x + 68, rect.y() + 13, 50, 18)
            painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
            painter.setBrush(QBrush(QColor(12, 74, 110) if self.is_dark else QColor(224, 242, 254)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(port_rect, 4, 4)
            painter.setPen(QColor(56, 189, 248) if self.is_dark else QColor(2, 132, 199))
            painter.drawText(port_rect, Qt.AlignmentFlag.AlignCenter, f":{self.port}")

            # 汇总指标
            painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 9))
            painter.setPen(QColor(148, 163, 184) if self.is_dark else QColor(100, 116, 139))
            painter.drawText(QRectF(title_left_x + 124, rect.y(), 250, 44), Qt.AlignmentFlag.AlignVCenter, f"请求 {self.total_requests} · 会话 {self.total_sessions} · 命中 {self.cache_hit_rate:.1f}%")

            # 顶部右侧工具栏: 主题 + 设置 + 收起胶囊 + 收起圆标 (+ Windows 关闭键)
            right_width = 240 if not is_mac else 200
            right_x = rect.right() - right_width
            
            # 主题切换
            theme_btn = QRectF(right_x, rect.y() + 10, 28, 24)
            painter.setFont(QFont("Segoe UI Emoji" if platform.system() == "Windows" else "Apple Color Emoji", 9))
            painter.setPen(QColor(245, 158, 11) if self.is_dark else QColor(100, 116, 139))
            painter.drawText(theme_btn, Qt.AlignmentFlag.AlignCenter, "🌙" if self.is_dark else "☀️")
            self.clickable_regions.append({"id": "panel_theme", "rect": theme_btn, "action": "toggle_theme"})

            # 设置按钮
            set_btn = QRectF(right_x + 32, rect.y() + 8, 56, 28)
            if self.hovered_region_id == "panel_set":
                painter.setBrush(QBrush(QColor(56, 189, 248, 40)))
                painter.setPen(QPen(QColor(56, 189, 248), 1))
                painter.drawRoundedRect(set_btn, 4, 4)
            painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 8, QFont.Weight.Bold))
            painter.setPen(QColor(241, 245, 249) if self.is_dark else QColor(15, 23, 42))
            painter.drawText(set_btn, Qt.AlignmentFlag.AlignCenter, "⚙ 设置")
            self.clickable_regions.append({"id": "panel_set", "rect": set_btn, "action": "open_settings"})

            # 分隔线
            painter.setPen(QPen(QColor(71, 85, 105) if self.is_dark else QColor(203, 213, 225), 1))
            painter.drawLine(int(right_x + 94), int(rect.y() + 14), int(right_x + 94), int(rect.y() + 30))

            # 收缩回胶囊 ⤢
            shrink_cap_btn = QRectF(right_x + 100, rect.y() + 8, 32, 28)
            if self.hovered_region_id == "panel_cap":
                painter.setBrush(QBrush(QColor(255, 255, 255, 20)))
                painter.setPen(QPen(QColor(255, 255, 255, 60), 1))
                painter.drawRoundedRect(shrink_cap_btn, 4, 4)
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.setPen(QColor(148, 163, 184))
            painter.drawText(shrink_cap_btn, Qt.AlignmentFlag.AlignCenter, "↗")
            self.clickable_regions.append({"id": "panel_cap", "rect": shrink_cap_btn, "action": "shrink_capsule"})

            # 收缩回圆标 ⦿
            shrink_orb_btn = QRectF(right_x + 136, rect.y() + 8, 32, 28)
            if self.hovered_region_id == "panel_orb":
                painter.setBrush(QBrush(QColor(255, 255, 255, 20)))
                painter.setPen(QPen(QColor(255, 255, 255, 60), 1))
                painter.drawRoundedRect(shrink_orb_btn, 4, 4)
            painter.setFont(QFont("Arial", 11))
            painter.drawText(shrink_orb_btn, Qt.AlignmentFlag.AlignCenter, "⦿")
            self.clickable_regions.append({"id": "panel_orb", "rect": shrink_orb_btn, "action": "shrink_circle"})

            # Windows 专有右上角 X 关闭按钮
            if not is_mac:
                win_close_btn = QRectF(right_x + 174, rect.y() + 6, 36, 32)
                if self.hovered_region_id == "win_close_btn":
                    painter.setBrush(QBrush(QColor(239, 68, 68)))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawRoundedRect(win_close_btn, 4, 4)
                    painter.setPen(QColor(255, 255, 255))
                else:
                    painter.setPen(QColor(148, 163, 184))
                painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
                painter.drawText(win_close_btn, Qt.AlignmentFlag.AlignCenter, "✕")
                self.clickable_regions.append({"id": "win_close_btn", "rect": win_close_btn, "action": "close_app"})

            # (2) 第二行: 日历 + 当前冲刺 + 列筛选
            sub_bar_rect = QRectF(rect.x() + 16, rect.y() + 52, rect.width() - 32, 34)
            painter.setBrush(QBrush(QColor(18, 24, 38) if self.is_dark else QColor(241, 245, 249)))
            painter.setPen(QPen(QColor(38, 48, 68) if self.is_dark else QColor(226, 232, 240), 1))
            painter.drawRoundedRect(sub_bar_rect, 6, 6)

            # 日历输入药丸
            date_rect = QRectF(rect.x() + 24, rect.y() + 56, 120, 26)
            painter.setBrush(QBrush(QColor(13, 17, 26) if self.is_dark else QColor(255, 255, 255)))
            painter.setPen(QPen(QColor(56, 189, 248, 80), 1))
            painter.drawRoundedRect(date_rect, 4, 4)
            painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 8))
            painter.setPen(QColor(56, 189, 248))
            painter.drawText(date_rect, Qt.AlignmentFlag.AlignCenter, "📅 2026-09-03")

            today_rect = QRectF(rect.x() + 150, rect.y() + 56, 44, 26)
            painter.setBrush(QBrush(QColor(30, 41, 59) if self.is_dark else QColor(226, 232, 240)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(today_rect, 4, 4)
            painter.setPen(QColor(203, 213, 225) if self.is_dark else QColor(51, 65, 85))
            painter.drawText(today_rect, Qt.AlignmentFlag.AlignCenter, "今天")

            # 冲刺文本
            sprint_rect = QRectF(rect.x() + 204, rect.y() + 52, rect.width() - 300, 34)
            painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 9, QFont.Weight.Bold))
            painter.setPen(QColor(52, 211, 153) if self.is_dark else QColor(5, 150, 105))
            painter.drawText(sprint_rect, Qt.AlignmentFlag.AlignVCenter, f"☑ {self.sprint_title}")

            # 列筛选
            filter_rect = QRectF(rect.right() - 95, rect.y() + 56, 75, 26)
            painter.setBrush(QBrush(QColor(30, 41, 59) if self.is_dark else QColor(226, 232, 240)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(filter_rect, 4, 4)
            painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 8))
            painter.setPen(QColor(148, 163, 184) if self.is_dark else QColor(71, 85, 105))
            painter.drawText(filter_rect, Qt.AlignmentFlag.AlignCenter, "⚙ 列筛选")

            # (3) 第三行: Tab 栏 (任务列表 (5) / 会话列表 (3))
            tab_y = rect.y() + 94
            
            # 任务列表 Tab
            tab_task_rect = QRectF(rect.x() + 16, tab_y, 110, 32)
            is_task_tab = (self.active_tab == "tasks")
            if is_task_tab:
                painter.setBrush(QBrush(QColor(12, 74, 110, 120) if self.is_dark else QColor(224, 242, 254)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(tab_task_rect, 6, 6)
                # 下边蓝条
                painter.setPen(QPen(QColor(56, 189, 248), 2))
                painter.drawLine(int(tab_task_rect.left() + 10), int(tab_task_rect.bottom() - 1), int(tab_task_rect.right() - 10), int(tab_task_rect.bottom() - 1))
                painter.setPen(QColor(56, 189, 248) if self.is_dark else QColor(2, 132, 199))
            else:
                painter.setPen(QColor(148, 163, 184) if self.is_dark else QColor(100, 116, 139))
            painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 9, QFont.Weight.Bold if is_task_tab else QFont.Weight.Normal))
            painter.drawText(tab_task_rect, Qt.AlignmentFlag.AlignCenter, f"任务列表 ({len(self.tasks)})")
            self.clickable_regions.append({"id": "tab_tasks", "rect": tab_task_rect, "action": "select_tab", "data": "tasks"})

            # 会话列表 Tab
            tab_sess_rect = QRectF(rect.x() + 134, tab_y, 110, 32)
            if not is_task_tab:
                painter.setBrush(QBrush(QColor(12, 74, 110, 120) if self.is_dark else QColor(224, 242, 254)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(tab_sess_rect, 6, 6)
                painter.setPen(QPen(QColor(56, 189, 248), 2))
                painter.drawLine(int(tab_sess_rect.left() + 10), int(tab_sess_rect.bottom() - 1), int(tab_sess_rect.right() - 10), int(tab_sess_rect.bottom() - 1))
                painter.setPen(QColor(56, 189, 248) if self.is_dark else QColor(2, 132, 199))
            else:
                painter.setPen(QColor(148, 163, 184) if self.is_dark else QColor(100, 116, 139))
            painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 9, QFont.Weight.Bold if not is_task_tab else QFont.Weight.Normal))
            painter.drawText(tab_sess_rect, Qt.AlignmentFlag.AlignCenter, f"会话列表 ({len(self.sessions)})")
            self.clickable_regions.append({"id": "tab_sessions", "rect": tab_sess_rect, "action": "select_tab", "data": "sessions"})

            # 右侧提示说明
            tips_rect = QRectF(rect.right() - 320, tab_y, 300, 32)
            painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 8))
            painter.setPen(QColor(100, 116, 139))
            tips_text = "单击行查看详情 · 点击 📌 锁定至悬浮窗" if is_task_tab else "展示活跃流式代理会话及实时连接耗时"
            painter.drawText(tips_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, tips_text)

            # (4) 表头
            th_y = tab_y + 38
            painter.setPen(QColor(148, 163, 184) if self.is_dark else QColor(100, 116, 139))
            painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 8, QFont.Weight.Bold))
            if is_task_tab:
                painter.drawText(QRectF(rect.x() + 20, th_y, 30, 20), Qt.AlignmentFlag.AlignCenter, "📌")
                painter.drawText(QRectF(rect.x() + 55, th_y, 45, 20), Qt.AlignmentFlag.AlignCenter, "# ↑↓")
                painter.drawText(QRectF(rect.x() + 105, th_y, 60, 20), Qt.AlignmentFlag.AlignCenter, "服务商")
                painter.drawText(QRectF(rect.x() + 170, th_y, 65, 20), Qt.AlignmentFlag.AlignCenter, "请求数 ↑↓")
                painter.drawText(QRectF(rect.x() + 240, th_y, 70, 20), Qt.AlignmentFlag.AlignCenter, "总消耗 ↑↓")
                painter.drawText(QRectF(rect.x() + 315, th_y, 65, 20), Qt.AlignmentFlag.AlignCenter, "命中率 ↑↓")
                painter.drawText(QRectF(rect.x() + 385, th_y, 110, 20), Qt.AlignmentFlag.AlignLeft, "模型")
                painter.drawText(QRectF(rect.x() + 500, th_y, 240, 20), Qt.AlignmentFlag.AlignLeft, "任务标题")
            else:
                painter.drawText(QRectF(rect.x() + 24, th_y, 70, 20), Qt.AlignmentFlag.AlignLeft, "会话ID")
                painter.drawText(QRectF(rect.x() + 110, th_y, 60, 20), Qt.AlignmentFlag.AlignCenter, "服务商")
                painter.drawText(QRectF(rect.x() + 180, th_y, 120, 20), Qt.AlignmentFlag.AlignLeft, "模型")
                painter.drawText(QRectF(rect.x() + 310, th_y, 65, 20), Qt.AlignmentFlag.AlignCenter, "请求数")
                painter.drawText(QRectF(rect.x() + 385, th_y, 75, 20), Qt.AlignmentFlag.AlignCenter, "消耗Token")
                painter.drawText(QRectF(rect.x() + 470, th_y, 65, 20), Qt.AlignmentFlag.AlignCenter, "命中率")
                painter.drawText(QRectF(rect.x() + 550, th_y, 200, 20), Qt.AlignmentFlag.AlignLeft, "会话描述 / 最后活跃")

            # (5) 表格数据行
            row_y = th_y + 24
            items_to_render = self.tasks if is_task_tab else self.sessions
            for idx, item in enumerate(items_to_render):
                row_rect = QRectF(rect.x() + 16, row_y, rect.width() - 32, 40)
                is_selected = (idx == self.current_task_idx) if is_task_tab else False
                
                if is_selected:
                    bg = QColor(30, 58, 138, 100) if self.is_dark else QColor(224, 242, 254)
                elif item.get("pinned", False):
                    bg = QColor(22, 30, 46) if self.is_dark else QColor(248, 250, 252)
                else:
                    bg = QColor(16, 21, 32) if (self.is_dark and idx % 2 == 0) else (QColor(13, 17, 26) if self.is_dark else QColor(255, 255, 255))

                painter.setBrush(QBrush(bg))
                painter.setPen(QPen(QColor(56, 189, 248, 90) if is_selected else (QColor(30, 41, 59) if self.is_dark else QColor(226, 232, 240)), 1))
                painter.drawRoundedRect(row_rect, 4, 4)

                if is_task_tab:
                    # 注册行点击切换任务
                    self.clickable_regions.append({"id": f"row_{idx}", "rect": row_rect, "action": "select_task", "data": idx})

                    # 钉住按钮
                    pin_rect = QRectF(rect.x() + 20, row_y, 30, 40)
                    painter.setFont(QFont("Arial", 9))
                    painter.setPen(QColor(245, 158, 11) if item["pinned"] else QColor(100, 116, 139))
                    painter.drawText(pin_rect, Qt.AlignmentFlag.AlignCenter, "📌")
                    self.clickable_regions.append({"id": f"pin_{item['id']}", "rect": pin_rect, "action": "toggle_pin", "data": item['id']})

                    # ID
                    painter.setFont(QFont("Consolas", 9))
                    painter.setPen(QColor(148, 163, 184))
                    painter.drawText(QRectF(rect.x() + 55, row_y, 45, 40), Qt.AlignmentFlag.AlignCenter, f"#{item['id']}")

                    # 服务商彩色徽标
                    prov_box = QRectF(rect.x() + 115, row_y + 8, 36, 24)
                    p_code = item["provider"]
                    if p_code == "openai":
                        painter.setBrush(QBrush(QColor(6, 78, 59, 160)))
                        painter.setPen(QPen(QColor(52, 211, 153), 1))
                        painter.drawRoundedRect(prov_box, 4, 4)
                        painter.setPen(QColor(52, 211, 153))
                        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                        painter.drawText(prov_box, Qt.AlignmentFlag.AlignCenter, "OA")
                    elif p_code == "deepseek":
                        painter.setBrush(QBrush(QColor(12, 74, 110, 160)))
                        painter.setPen(QPen(QColor(56, 189, 248), 1))
                        painter.drawRoundedRect(prov_box, 4, 4)
                        painter.setPen(QColor(56, 189, 248))
                        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                        painter.drawText(prov_box, Qt.AlignmentFlag.AlignCenter, "DS")
                    elif p_code == "sensenova":
                        painter.setBrush(QBrush(QColor(88, 28, 135, 160)))
                        painter.setPen(QPen(QColor(192, 132, 252), 1))
                        painter.drawRoundedRect(prov_box, 4, 4)
                        painter.setPen(QColor(192, 132, 252))
                        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                        painter.drawText(prov_box, Qt.AlignmentFlag.AlignCenter, "SN")
                    else:
                        painter.setBrush(QBrush(QColor(30, 41, 59, 160)))
                        painter.setPen(QPen(QColor(148, 163, 184), 1))
                        painter.drawRoundedRect(prov_box, 4, 4)
                        painter.setPen(QColor(148, 163, 184))
                        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                        painter.drawText(prov_box, Qt.AlignmentFlag.AlignCenter, "GLM")

                    # 请求数徽章
                    req_badge = QRectF(rect.x() + 180, row_y + 9, 44, 22)
                    painter.setBrush(QBrush(QColor(6, 78, 59, 160) if self.is_dark else QColor(236, 253, 245)))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawRoundedRect(req_badge, 4, 4)
                    painter.setPen(QColor(52, 211, 153) if self.is_dark else QColor(5, 150, 105))
                    painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
                    painter.drawText(req_badge, Qt.AlignmentFlag.AlignCenter, f"✓ {item['req']}")

                    # 总消耗 (蓝)
                    painter.setPen(QColor(56, 189, 248))
                    painter.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
                    painter.drawText(QRectF(rect.x() + 240, row_y, 70, 40), Qt.AlignmentFlag.AlignCenter, f"{item['tokens']} tok")

                    # 命中率 (绿)
                    painter.setPen(QColor(52, 211, 153))
                    painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 8, QFont.Weight.Bold))
                    painter.drawText(QRectF(rect.x() + 315, row_y, 65, 40), Qt.AlignmentFlag.AlignCenter, f"⚡{item['hit']:.1f}%")

                    # 模型
                    painter.setPen(QColor(203, 213, 225) if self.is_dark else QColor(51, 65, 85))
                    painter.setFont(QFont("Consolas", 8))
                    painter.drawText(QRectF(rect.x() + 385, row_y, 110, 40), Qt.AlignmentFlag.AlignVCenter, item["model"])

                    # 任务标题
                    painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 9, QFont.Weight.Bold))
                    painter.setPen(QColor(241, 245, 249) if self.is_dark else QColor(15, 23, 42))
                    painter.drawText(QRectF(rect.x() + 500, row_y, 240, 40), Qt.AlignmentFlag.AlignVCenter, item["name"])
                else:
                    # 渲染会话行
                    painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
                    painter.setPen(QColor(56, 189, 248))
                    painter.drawText(QRectF(rect.x() + 24, row_y, 80, 40), Qt.AlignmentFlag.AlignVCenter, item["id"])

                    # 服务商
                    prov_box = QRectF(rect.x() + 115, row_y + 8, 36, 24)
                    painter.setBrush(QBrush(QColor(30, 41, 59, 160)))
                    painter.setPen(QPen(QColor(148, 163, 184), 1))
                    painter.drawRoundedRect(prov_box, 4, 4)
                    painter.setPen(QColor(241, 245, 249))
                    painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                    painter.drawText(prov_box, Qt.AlignmentFlag.AlignCenter, item["provider"][:2].upper())

                    painter.setFont(QFont("Consolas", 8))
                    painter.setPen(QColor(203, 213, 225))
                    painter.drawText(QRectF(rect.x() + 180, row_y, 120, 40), Qt.AlignmentFlag.AlignVCenter, item["model"])

                    painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
                    painter.setPen(QColor(52, 211, 153))
                    painter.drawText(QRectF(rect.x() + 310, row_y, 65, 40), Qt.AlignmentFlag.AlignCenter, f"{item['req']} req")

                    painter.setPen(QColor(56, 189, 248))
                    painter.drawText(QRectF(rect.x() + 385, row_y, 75, 40), Qt.AlignmentFlag.AlignCenter, f"{item['tokens']} tok")

                    painter.setPen(QColor(52, 211, 153))
                    painter.drawText(QRectF(rect.x() + 470, row_y, 65, 40), Qt.AlignmentFlag.AlignCenter, f"⚡{item['hit']:.1f}%")

                    painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 9))
                    painter.setPen(QColor(241, 245, 249))
                    painter.drawText(QRectF(rect.x() + 550, row_y, 200, 40), Qt.AlignmentFlag.AlignVCenter, f"{item['name']} ({item['time']})")

                row_y += 44

            # (5) 底部状态栏与接入地址
            footer_y = rect.bottom() - 40
            painter.setBrush(QBrush(QColor(18, 24, 38) if self.is_dark else QColor(248, 250, 252)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(rect.x(), footer_y, rect.width(), 40), 14, 14)

            painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 8))
            painter.setPen(QColor(148, 163, 184) if self.is_dark else QColor(100, 116, 139))
            painter.drawText(QRectF(rect.x() + 20, footer_y, 40, 40), Qt.AlignmentFlag.AlignVCenter, "接入:")

            # 绿色接入 URL 药丸 (支持点击复制)
            url_rect = QRectF(rect.x() + 60, footer_y + 8, 210, 24)
            painter.setBrush(QBrush(QColor(6, 78, 59, 160) if self.is_dark else QColor(236, 253, 245)))
            painter.setPen(QPen(QColor(52, 211, 153, 100), 1))
            painter.drawRoundedRect(url_rect, 4, 4)
            painter.setPen(QColor(52, 211, 153) if self.is_dark else QColor(5, 150, 105))
            painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
            url_text = "✓ 已复制到剪贴板!" if self.copied_feedback else f"http://127.0.0.1:{self.port}/v1 📋"
            painter.drawText(url_rect, Qt.AlignmentFlag.AlignCenter, url_text)
            self.clickable_regions.append({"id": "panel_copy", "rect": url_rect, "action": "copy_url"})

            painter.setPen(QColor(100, 116, 139))
            painter.setFont(QFont("PingFang SC" if platform.system() == "Darwin" else "Microsoft YaHei", 8))
            painter.drawText(QRectF(rect.x() + 285, footer_y, 260, 40), Qt.AlignmentFlag.AlignVCenter, "· 支持按键滑动 W/A/S/D ↑↓←→")

            # 打开 Web 控制台按钮
            web_btn = QRectF(rect.right() - 220, footer_y + 8, 80, 24)
            painter.setBrush(QBrush(QColor(30, 41, 59) if self.is_dark else QColor(241, 245, 249)))
            painter.setPen(QPen(QColor(56, 189, 248, 80), 1))
            painter.drawRoundedRect(web_btn, 4, 4)
            painter.setPen(QColor(56, 189, 248))
            painter.drawText(web_btn, Qt.AlignmentFlag.AlignCenter, "🌐 Web 控制台")
            self.clickable_regions.append({"id": "panel_web", "rect": web_btn, "action": "open_web"})

            painter.setPen(QColor(148, 163, 184))
            painter.drawText(QRectF(rect.right() - 130, footer_y, 110, 40), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"共 {len(self.tasks)} 条  < 1 / 1 >")
