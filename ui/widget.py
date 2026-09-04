"""
PySide6 跨平台桌面原生悬浮窗 (ui/widget.py)
对齐开源规范与完整桌面交互：
1. 支持无边框窗口 8 边缘八向自由拉伸 (Resize Handles)
2. 表头升降序实时排序 (# / 服务商 / 请求数 / 总消耗 / 命中率 / 模型)
3. 动态列筛选浮层 (⚙ 列筛选)
4. 单击/双击行查看详细指标与 Prompt 分析 (ItemDetailDialog)
5. 日期切换 (📅 2026-09-04) 与 [今天] 快速重置
6. 会话与任务级联过滤联动 (会话 -> 查看该会话所有任务)
7. 明确 📌 钉住 (固定悬浮胶囊监控) 与当前选中的职责划分
8. 剔除误触双击模式跳变，杜绝意外变形
"""

import sys
import platform
import webbrowser
from datetime import datetime
from PySide6.QtCore import Qt, QPoint, QRectF, QTimer
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QAction, QGuiApplication,
    QCursor
)
from PySide6.QtWidgets import (
    QWidget, QMenu, QApplication, QMessageBox, QInputDialog
)

from ui.settings_dialog import SettingsDialog
from ui.detail_dialog import ItemDetailDialog
from config import GATEWAY_HOST, GATEWAY_PORT

RESIZE_MARGIN = 8

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

        # 当前选中的活跃任务索引与 Tab 状态
        self.current_task_idx = 0
        self.active_tab = "tasks"  # "tasks" | "sessions"
        self.selected_date = "2026-09-04"
        self.session_filter_id = None  # 用于会话与任务级联筛选

        # 排序状态
        self.sort_column = None
        self.sort_order = "desc"  # "asc" | "desc"

        # 列可见性配置
        self.visible_cols = {
            "pin": True,
            "id": True,
            "provider": True,
            "req": True,
            "tokens": True,
            "hit": True,
            "model": True,
            "name": True,
        }

        # 任务列表 (包含所属 sessionId)
        self.tasks = [
            {"id": 5, "sessionId": "sess_001", "pinned": True, "provider": "openai", "req": 1, "tokens": 165, "hit": 82.5, "cost": 0.0032, "model": "o3-mini", "name": "OpenAI 思考模型接入与流式 Token 统计", "time": "2026-09-04 14:32:05"},
            {"id": 4, "sessionId": "sess_002", "pinned": False, "provider": "deepseek", "req": 2, "tokens": 80, "hit": 75.0, "cost": 0.0012, "model": "deepseek-coder", "name": "连接池与长连接健康检查优化", "time": "2026-09-04 14:28:10"},
            {"id": 3, "sessionId": "sess_002", "pinned": False, "provider": "deepseek", "req": 1, "tokens": 72, "hit": 68.2, "cost": 0.0011, "model": "deepseek-coder", "name": "极简悬浮窗置顶与拖拽事件监听", "time": "2026-09-04 14:20:00"},
            {"id": 2, "sessionId": "sess_003", "pinned": False, "provider": "sensenova", "req": 2, "tokens": 70, "hit": 80.0, "cost": 0.0010, "model": "sensenova-v5-5", "name": "商汤日日新 TokenPlan 适配与路由", "time": "2026-09-04 14:15:33"},
            {"id": 1, "sessionId": "sess_001", "pinned": False, "provider": "bigmodel", "req": 4, "tokens": 276, "hit": 78.6, "cost": 0.0041, "model": "glm-4-flash", "name": "智谱 GLM 多模态路由拦截测试", "time": "2026-09-04 14:02:18"},
        ]

        # 会话列表
        self.sessions = [
            {"id": "sess_001", "name": "主业务网关路由与流式转发", "provider": "openai", "model": "o3-mini", "req": 5, "tokens": 441, "hit": 80.5, "time": "2026-09-04 14:32:05", "cost": 0.0073},
            {"id": "sess_002", "name": "代码重构辅助与测试验证", "provider": "deepseek", "model": "deepseek-coder", "req": 3, "tokens": 152, "hit": 72.0, "time": "2026-09-04 14:28:10", "cost": 0.0023},
            {"id": "sess_003", "name": "商汤多模态图片识别分析", "provider": "sensenova", "model": "sensenova-v5-5", "req": 2, "tokens": 70, "hit": 80.0, "time": "2026-09-04 14:15:33", "cost": 0.0010},
        ]

        self.sprint_title = "当前冲刺: 重构流式 usage 提取及悬浮胶囊"

        # 交互区域缓存
        self.clickable_regions = []
        self.hovered_region_id = None

        # 窗口边缘拉伸状态 (八向拉伸)
        self.resizing_edge = None
        self.resize_start_pos = QPoint()
        self.resize_start_geo = None

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
    def filtered_tasks(self):
        if self.session_filter_id:
            return [t for t in self.tasks if t.get("sessionId") == self.session_filter_id]
        return self.tasks

    @property
    def current_task(self):
        # 优先展示钉住的任务；若未钉住，则展示当前选中的任务
        pinned_tasks = [t for t in self.tasks if t.get("pinned", False)]
        if pinned_tasks:
            return pinned_tasks[0]
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
        return len(self.sessions)

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
            self.resize(800, 520)
        
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
        self.is_dark = settings.get("is_dark", True)
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
    # 排序与列筛选
    # ------------------------------------------------------------------------
    def sort_by_column(self, col_key: str):
        if self.sort_column == col_key:
            self.sort_order = "asc" if self.sort_order == "desc" else "desc"
        else:
            self.sort_column = col_key
            self.sort_order = "desc"

        reverse = (self.sort_order == "desc")
        if self.active_tab == "tasks":
            self.tasks.sort(key=lambda x: x.get(col_key, 0), reverse=reverse)
        else:
            self.sessions.sort(key=lambda x: x.get(col_key, 0), reverse=reverse)
        self.update()

    def open_column_filter_menu(self, global_pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {'#131720' if self.is_dark else '#ffffff'};
                border: 1px solid {'#334155' if self.is_dark else '#cbd5e1'};
                border-radius: 8px;
                padding: 6px;
                color: {'#f1f5f9' if self.is_dark else '#0f172a'};
                font-size: 11px;
            }}
            QMenu::item {{
                padding: 4px 18px 4px 8px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: #0284c7;
                color: #ffffff;
            }}
        """)

        cols = [
            ("pin", "📌 钉住状态"),
            ("id", "# 序号/ID"),
            ("provider", "服务商徽标"),
            ("req", "请求数"),
            ("tokens", "总消耗 Token"),
            ("hit", "Prompt 命中率"),
            ("model", "模型名称"),
            ("name", "任务标题/描述"),
        ]

        for key, name in cols:
            act = QAction(name, menu)
            act.setCheckable(True)
            act.setChecked(self.visible_cols.get(key, True))
            act.triggered.connect(lambda chk, k=key: self.toggle_column_vis(k, chk))
            menu.addAction(act)

        menu.exec(global_pos)

    def toggle_column_vis(self, key: str, checked: bool):
        self.visible_cols[key] = checked
        self.update()

    def open_date_picker(self):
        text, ok = QInputDialog.getItem(
            self, "选择查看日期", "请选择要查看的历史日期或快速重置：",
            ["2026-09-04 (今天)", "2026-09-03 (昨天)", "2026-09-02", "2026-09-01"],
            0, False
        )
        if ok and text:
            self.selected_date = text.split(" ")[0]
            self.update()

    def reset_today(self):
        self.selected_date = "2026-09-04"
        self.session_filter_id = None
        self.update()

    def open_item_detail(self, item_data: dict, item_type: str = "task"):
        dlg = ItemDetailDialog(
            item_data=item_data,
            item_type=item_type,
            is_dark=self.is_dark,
            parent=self,
            on_toggle_pin=self.on_detail_toggle_pin,
            on_filter_session=self.on_detail_filter_session
        )
        dlg.exec()

    def on_detail_toggle_pin(self, item_id, is_pinned):
        for t in self.tasks:
            if t["id"] == item_id:
                t["pinned"] = is_pinned
            else:
                # 单选钉住，确保胶囊锁定唯一项
                if is_pinned:
                    t["pinned"] = False
        self.update()

    def on_detail_filter_session(self, sess_id: str):
        self.session_filter_id = sess_id
        self.active_tab = "tasks"
        self.update()

    # ------------------------------------------------------------------------
    # 八向边缘拉伸算法与鼠标事件
    # ------------------------------------------------------------------------
    def calculate_resize_edge(self, pos: QPoint) -> str:
        if self.mode != "expanded":
            return None
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        m = RESIZE_MARGIN

        on_left = x <= m
        on_right = x >= w - m
        on_top = y <= m
        on_bottom = y >= h - m

        if on_top and on_left:
            return "top-left"
        if on_top and on_right:
            return "top-right"
        if on_bottom and on_left:
            return "bottom-left"
        if on_bottom and on_right:
            return "bottom-right"
        if on_left:
            return "left"
        if on_right:
            return "right"
        if on_top:
            return "top"
        if on_bottom:
            return "bottom"
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()

            # 1. 优先判定边缘拉伸 (仅 expanded 状态支持八向自由拉伸)
            edge = self.calculate_resize_edge(pos)
            if edge:
                self.resizing_edge = edge
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_geo = self.geometry()
                event.accept()
                return

            # 2. 判定按钮与热区命中
            for reg in self.clickable_regions:
                if reg["rect"].contains(event.position()):
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
                        idx = reg.get("data", 0)
                        self.current_task_idx = idx
                        self.open_item_detail(self.filtered_tasks[idx], "task")
                        self.update()
                    elif act == "select_session":
                        idx = reg.get("data", 0)
                        self.open_item_detail(self.sessions[idx], "session")
                        self.update()
                    elif act == "select_tab":
                        self.active_tab = reg.get("data", "tasks")
                        self.update()
                    elif act == "sort_col":
                        self.sort_by_column(reg.get("data"))
                    elif act == "open_filter":
                        self.open_column_filter_menu(event.globalPosition().toPoint())
                    elif act == "open_date":
                        self.open_date_picker()
                    elif act == "reset_today":
                        self.reset_today()
                    elif act == "clear_session_filter":
                        self.session_filter_id = None
                        self.update()
                    event.accept()
                    return

            # 3. 窗口拖拽移动
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()

        # 处理八向拉伸中
        if self.resizing_edge and event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.resize_start_pos
            geo = self.resize_start_geo
            x, y, w, h = geo.x(), geo.y(), geo.width(), geo.height()
            min_w, min_h = 680, 420

            if "right" in self.resizing_edge:
                w = max(min_w, geo.width() + delta.x())
            if "bottom" in self.resizing_edge:
                h = max(min_h, geo.height() + delta.y())
            if "left" in self.resizing_edge:
                new_w = max(min_w, geo.width() - delta.x())
                if new_w != min_w:
                    x = geo.x() + delta.x()
                w = new_w
            if "top" in self.resizing_edge:
                new_h = max(min_h, geo.height() - delta.y())
                if new_h != min_h:
                    y = geo.y() + delta.y()
                h = new_h

            self.setGeometry(x, y, w, h)
            event.accept()
            return

        # 悬停边缘光标变化
        edge = self.calculate_resize_edge(pos)
        if edge:
            if edge in ("top-left", "bottom-right"):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif edge in ("top-right", "bottom-left"):
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif edge in ("left", "right"):
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif edge in ("top", "bottom"):
                self.setCursor(Qt.CursorShape.SizeVerCursor)
            return

        # 悬停普通按钮热区
        hovered_act = None
        for reg in self.clickable_regions:
            if reg["rect"].contains(event.position()):
                hovered_act = reg["id"]
                break

        if hovered_act != self.hovered_region_id:
            self.hovered_region_id = hovered_act
            if hovered_act:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()

        # 拖拽移动
        if self.is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            if platform.system() == "Darwin":
                new_pos.setY(max(26, new_pos.y()))
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.is_dragging = False
        self.resizing_edge = None

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.set_mode("capsule" if self.mode == "expanded" else "circle")
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
                border: 1px solid {'#334155' if self.is_dark else '#cbd5e1'};
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
                background-color: {'#1e293b' if self.is_dark else '#e2e8f0'};
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

        settings_act = QAction("⚙️ 打开用量网关设置...", menu)
        settings_act.triggered.connect(self.open_settings)
        menu.addAction(settings_act)

        menu.addSeparator()
        quit_act = QAction("✕ 退出程序", menu)
        quit_act.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_act)

        menu.exec(event.globalPos())

    # ------------------------------------------------------------------------
    # 纯原生绘图引擎 (QPainter 100% 自绘制无锯齿渲染)
    # ------------------------------------------------------------------------
    def paintEvent(self, event):
        self.clickable_regions.clear()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = self.rect()
        is_mac = (platform.system() == "Darwin")

        # --------------------------------------------------------------------
        # 1. 微型圆标模式 (Circle / Orb)
        # --------------------------------------------------------------------
        if self.mode == "circle":
            bg_color = QColor(15, 23, 42, 235) if self.is_dark else QColor(255, 255, 255, 245)
            border_color = QColor(56, 189, 248, 180) if self.is_dark else QColor(2, 132, 199, 160)
            
            painter.setBrush(QBrush(bg_color))
            painter.setPen(QPen(border_color, 1.5))
            painter.drawEllipse(rect.adjusted(2, 2, -2, -2))

            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.setPen(QColor(56, 189, 248))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{int(self.cache_hit_rate)}%")

            self.clickable_regions.append({"id": "orb_expand", "rect": QRectF(rect), "action": "shrink_capsule"})

        # --------------------------------------------------------------------
        # 2. 长条胶囊模式 (CapsuleBar)
        # --------------------------------------------------------------------
        elif self.mode == "capsule":
            bg_color = QColor(13, 17, 26, 240) if self.is_dark else QColor(255, 255, 255, 245)
            border_color = QColor(38, 48, 68) if self.is_dark else QColor(226, 232, 240)
            
            painter.setBrush(QBrush(bg_color))
            painter.setPen(QPen(border_color, 1.2))
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 22, 22)

            # (1) 切换任务按钮 <
            prev_rect = QRectF(rect.x() + 8, rect.y() + 8, 24, 28)
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            painter.setPen(QColor(148, 163, 184))
            painter.drawText(prev_rect, Qt.AlignmentFlag.AlignCenter, "‹")
            self.clickable_regions.append({"id": "cap_prev", "rect": prev_rect, "action": "prev_task"})

            # (2) 服务商彩色徽标
            badge_rect = QRectF(rect.x() + 34, rect.y() + 10, 36, 24)
            p_code = self.provider
            if p_code == "openai":
                painter.setBrush(QBrush(QColor(6, 78, 59, 180)))
                painter.setPen(QPen(QColor(52, 211, 153), 1))
                painter.drawRoundedRect(badge_rect, 4, 4)
                painter.setPen(QColor(52, 211, 153))
                painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, "OA")
            elif p_code == "deepseek":
                painter.setBrush(QBrush(QColor(12, 74, 110, 180)))
                painter.setPen(QPen(QColor(56, 189, 248), 1))
                painter.drawRoundedRect(badge_rect, 4, 4)
                painter.setPen(QColor(56, 189, 248))
                painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, "DS")
            elif p_code == "sensenova":
                painter.setBrush(QBrush(QColor(88, 28, 135, 180)))
                painter.setPen(QPen(QColor(192, 132, 252), 1))
                painter.drawRoundedRect(badge_rect, 4, 4)
                painter.setPen(QColor(192, 132, 252))
                painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, "SN")
            else:
                painter.setBrush(QBrush(QColor(30, 41, 59, 180)))
                painter.setPen(QPen(QColor(148, 163, 184), 1))
                painter.drawRoundedRect(badge_rect, 4, 4)
                painter.setPen(QColor(148, 163, 184))
                painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, "GLM")

            # (3) 切换任务按钮 >
            next_rect = QRectF(rect.x() + 74, rect.y() + 8, 24, 28)
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            painter.setPen(QColor(148, 163, 184))
            painter.drawText(next_rect, Qt.AlignmentFlag.AlignCenter, "›")
            self.clickable_regions.append({"id": "cap_next", "rect": next_rect, "action": "next_task"})

            # (4) 任务简述
            title_rect = QRectF(rect.x() + 102, rect.y() + 8, 180, 28)
            painter.setFont(QFont("PingFang SC" if is_mac else "Microsoft YaHei", 9))
            painter.setPen(QColor(241, 245, 249) if self.is_dark else QColor(15, 23, 42))
            title_txt = painter.fontMetrics().elidedText(self.session_title, Qt.TextElideMode.ElideRight, 175)
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignVCenter, title_txt)

            # (5) 消耗数值
            tok_rect = QRectF(rect.x() + 286, rect.y() + 10, 75, 24)
            painter.setBrush(QBrush(QColor(12, 74, 110, 100) if self.is_dark else QColor(224, 242, 254)))
            painter.setPen(QPen(QColor(56, 189, 248, 80), 1))
            painter.drawRoundedRect(tok_rect, 12, 12)
            painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
            painter.setPen(QColor(56, 189, 248) if self.is_dark else QColor(2, 132, 199))
            tok_str = f"¥{self.cost_cny:.3f}" if self.show_cost else f"tok {self.total_tokens}"
            painter.drawText(tok_rect, Qt.AlignmentFlag.AlignCenter, tok_str)
            self.clickable_regions.append({"id": "cap_cost", "rect": tok_rect, "action": "toggle_cost"})

            # (6) 命中率绿牌
            hit_rect = QRectF(rect.x() + 366, rect.y() + 10, 68, 24)
            painter.setBrush(QBrush(QColor(6, 78, 59, 140) if self.is_dark else QColor(236, 253, 245)))
            painter.setPen(QPen(QColor(52, 211, 153, 80), 1))
            painter.drawRoundedRect(hit_rect, 12, 12)
            painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
            painter.setPen(QColor(52, 211, 153) if self.is_dark else QColor(5, 150, 105))
            painter.drawText(hit_rect, Qt.AlignmentFlag.AlignCenter, f"⚡{self.cache_hit_rate:.1f}%")

            # (7) 展开/控制按钮
            theme_btn = QRectF(rect.x() + 438, rect.y() + 10, 24, 24)
            painter.setFont(QFont("Segoe UI Emoji" if platform.system() == "Windows" else "Apple Color Emoji", 8))
            painter.drawText(theme_btn, Qt.AlignmentFlag.AlignCenter, "🌙" if self.is_dark else "☀️")
            self.clickable_regions.append({"id": "cap_theme", "rect": theme_btn, "action": "toggle_theme"})

            set_btn = QRectF(rect.x() + 462, rect.y() + 10, 24, 24)
            painter.setFont(QFont("Segoe UI Emoji" if platform.system() == "Windows" else "Apple Color Emoji", 8))
            painter.drawText(set_btn, Qt.AlignmentFlag.AlignCenter, "⚙")
            self.clickable_regions.append({"id": "cap_set", "rect": set_btn, "action": "open_settings"})

            expand_btn = QRectF(rect.x() + 486, rect.y() + 10, 26, 24)
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            painter.setPen(QColor(148, 163, 184))
            painter.drawText(expand_btn, Qt.AlignmentFlag.AlignCenter, "⤢")
            self.clickable_regions.append({"id": "cap_expand", "rect": expand_btn, "action": "expand_full"})

        # --------------------------------------------------------------------
        # 3. 全量大看板模式 (Expanded Full Panel)
        # --------------------------------------------------------------------
        elif self.mode == "expanded":
            bg_color = QColor(13, 17, 26, 252) if self.is_dark else QColor(255, 255, 255, 252)
            border_color = QColor(38, 48, 68) if self.is_dark else QColor(203, 213, 225)
            
            painter.setBrush(QBrush(bg_color))
            painter.setPen(QPen(border_color, 1.2))
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 14, 14)

            # (1) 顶栏 Header
            header_rect = QRectF(rect.x(), rect.y(), rect.width(), 44)
            painter.setBrush(QBrush(QColor(18, 24, 38) if self.is_dark else QColor(248, 250, 252)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(header_rect, 14, 14)

            # 区分 macOS 红绿灯 vs Windows 呼吸灯
            center_y = rect.y() + 22
            if is_mac:
                r_red = QRectF(rect.x() + 16, center_y - 6, 12, 12)
                r_yel = QRectF(rect.x() + 34, center_y - 6, 12, 12)
                r_grn = QRectF(rect.x() + 52, center_y - 6, 12, 12)

                painter.setBrush(QBrush(QColor(239, 68, 68)))
                painter.drawEllipse(r_red)
                painter.setBrush(QBrush(QColor(245, 158, 11)))
                painter.drawEllipse(r_yel)
                painter.setBrush(QBrush(QColor(34, 197, 94)))
                painter.drawEllipse(r_grn)

                self.clickable_regions.append({"id": "mac_close", "rect": r_red, "action": "close_app"})
                self.clickable_regions.append({"id": "mac_min", "rect": r_yel, "action": "shrink_capsule"})
                self.clickable_regions.append({"id": "mac_orb", "rect": r_grn, "action": "shrink_circle"})
                title_left_x = rect.x() + 76
            else:
                dot_circ = QRectF(rect.x() + 16, center_y - 5, 10, 10)
                painter.setBrush(QBrush(QColor(56, 189, 248)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(dot_circ)
                title_left_x = rect.x() + 34

            # 标题与端口
            painter.setFont(QFont("PingFang SC" if is_mac else "Microsoft YaHei", 10, QFont.Weight.Bold))
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
            painter.setFont(QFont("PingFang SC" if is_mac else "Microsoft YaHei", 9))
            painter.setPen(QColor(148, 163, 184) if self.is_dark else QColor(100, 116, 139))
            painter.drawText(QRectF(title_left_x + 124, rect.y(), 250, 44), Qt.AlignmentFlag.AlignVCenter, f"请求 {self.total_requests} · 会话 {self.total_sessions} · 命中 {self.cache_hit_rate:.1f}%")

            # 顶部右侧工具栏
            right_width = 240 if not is_mac else 200
            right_x = rect.right() - right_width
            
            theme_btn = QRectF(right_x, rect.y() + 10, 28, 24)
            painter.setFont(QFont("Segoe UI Emoji" if platform.system() == "Windows" else "Apple Color Emoji", 9))
            painter.setPen(QColor(245, 158, 11) if self.is_dark else QColor(100, 116, 139))
            painter.drawText(theme_btn, Qt.AlignmentFlag.AlignCenter, "🌙" if self.is_dark else "☀️")
            self.clickable_regions.append({"id": "panel_theme", "rect": theme_btn, "action": "toggle_theme"})

            set_btn = QRectF(right_x + 32, rect.y() + 8, 56, 28)
            if self.hovered_region_id == "panel_set":
                painter.setBrush(QBrush(QColor(56, 189, 248, 40)))
                painter.setPen(QPen(QColor(56, 189, 248), 1))
                painter.drawRoundedRect(set_btn, 4, 4)
            painter.setFont(QFont("PingFang SC" if is_mac else "Microsoft YaHei", 8, QFont.Weight.Bold))
            painter.setPen(QColor(241, 245, 249) if self.is_dark else QColor(15, 23, 42))
            painter.drawText(set_btn, Qt.AlignmentFlag.AlignCenter, "⚙ 设置")
            self.clickable_regions.append({"id": "panel_set", "rect": set_btn, "action": "open_settings"})

            shrink_cap_btn = QRectF(right_x + 100, rect.y() + 8, 32, 28)
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.setPen(QColor(148, 163, 184))
            painter.drawText(shrink_cap_btn, Qt.AlignmentFlag.AlignCenter, "↗")
            self.clickable_regions.append({"id": "panel_cap", "rect": shrink_cap_btn, "action": "shrink_capsule"})

            shrink_orb_btn = QRectF(right_x + 136, rect.y() + 8, 32, 28)
            painter.setFont(QFont("Arial", 11))
            painter.drawText(shrink_orb_btn, Qt.AlignmentFlag.AlignCenter, "⦿")
            self.clickable_regions.append({"id": "panel_orb", "rect": shrink_orb_btn, "action": "shrink_circle"})

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

            # (2) 第二行: 日历 + 冲刺 + 会话级联筛选标签 + 列筛选
            sub_bar_rect = QRectF(rect.x() + 16, rect.y() + 52, rect.width() - 32, 34)
            painter.setBrush(QBrush(QColor(18, 24, 38) if self.is_dark else QColor(241, 245, 249)))
            painter.setPen(QPen(QColor(38, 48, 68) if self.is_dark else QColor(226, 232, 240), 1))
            painter.drawRoundedRect(sub_bar_rect, 6, 6)

            # 日历药丸
            date_rect = QRectF(rect.x() + 24, rect.y() + 56, 120, 26)
            painter.setBrush(QBrush(QColor(13, 17, 26) if self.is_dark else QColor(255, 255, 255)))
            painter.setPen(QPen(QColor(56, 189, 248, 80), 1))
            painter.drawRoundedRect(date_rect, 4, 4)
            painter.setFont(QFont("PingFang SC" if is_mac else "Microsoft YaHei", 8))
            painter.setPen(QColor(56, 189, 248))
            painter.drawText(date_rect, Qt.AlignmentFlag.AlignCenter, f"📅 {self.selected_date}")
            self.clickable_regions.append({"id": "bar_date", "rect": date_rect, "action": "open_date"})

            today_rect = QRectF(rect.x() + 150, rect.y() + 56, 44, 26)
            painter.setBrush(QBrush(QColor(30, 41, 59) if self.is_dark else QColor(226, 232, 240)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(today_rect, 4, 4)
            painter.setPen(QColor(203, 213, 225) if self.is_dark else QColor(51, 65, 85))
            painter.drawText(today_rect, Qt.AlignmentFlag.AlignCenter, "今天")
            self.clickable_regions.append({"id": "bar_today", "rect": today_rect, "action": "reset_today"})

            # 会话级联筛选标签
            start_x = rect.x() + 204
            if self.session_filter_id:
                filter_tag_rect = QRectF(start_x, rect.y() + 56, 150, 26)
                painter.setBrush(QBrush(QColor(12, 74, 110, 140)))
                painter.setPen(QPen(QColor(56, 189, 248), 1))
                painter.drawRoundedRect(filter_tag_rect, 4, 4)
                painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
                painter.setPen(QColor(56, 189, 248))
                painter.drawText(filter_tag_rect, Qt.AlignmentFlag.AlignCenter, f"🏷️ 会话: {self.session_filter_id} ✕")
                self.clickable_regions.append({"id": "bar_clear_filter", "rect": filter_tag_rect, "action": "clear_session_filter"})
                start_x += 158

            sprint_rect = QRectF(start_x, rect.y() + 52, rect.width() - start_x - 100, 34)
            painter.setFont(QFont("PingFang SC" if is_mac else "Microsoft YaHei", 8, QFont.Weight.Bold))
            painter.setPen(QColor(52, 211, 153) if self.is_dark else QColor(5, 150, 105))
            painter.drawText(sprint_rect, Qt.AlignmentFlag.AlignVCenter, f"☑ {self.sprint_title}")

            filter_rect = QRectF(rect.right() - 95, rect.y() + 56, 75, 26)
            painter.setBrush(QBrush(QColor(30, 41, 59) if self.is_dark else QColor(226, 232, 240)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(filter_rect, 4, 4)
            painter.setFont(QFont("PingFang SC" if is_mac else "Microsoft YaHei", 8))
            painter.setPen(QColor(148, 163, 184) if self.is_dark else QColor(71, 85, 105))
            painter.drawText(filter_rect, Qt.AlignmentFlag.AlignCenter, "⚙ 列筛选")
            self.clickable_regions.append({"id": "bar_col_filter", "rect": filter_rect, "action": "open_filter"})

            # (3) 第三行: Tab 栏 (任务列表 / 会话列表)
            tab_y = rect.y() + 94
            is_task_tab = (self.active_tab == "tasks")

            tab_task_rect = QRectF(rect.x() + 16, tab_y, 110, 32)
            if is_task_tab:
                painter.setBrush(QBrush(QColor(12, 74, 110, 120) if self.is_dark else QColor(224, 242, 254)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(tab_task_rect, 6, 6)
                painter.setPen(QPen(QColor(56, 189, 248), 2))
                painter.drawLine(int(tab_task_rect.left() + 10), int(tab_task_rect.bottom() - 1), int(tab_task_rect.right() - 10), int(tab_task_rect.bottom() - 1))
                painter.setPen(QColor(56, 189, 248) if self.is_dark else QColor(2, 132, 199))
            else:
                painter.setPen(QColor(148, 163, 184) if self.is_dark else QColor(100, 116, 139))
            painter.setFont(QFont("PingFang SC" if is_mac else "Microsoft YaHei", 9, QFont.Weight.Bold if is_task_tab else QFont.Weight.Normal))
            painter.drawText(tab_task_rect, Qt.AlignmentFlag.AlignCenter, f"任务列表 ({len(self.filtered_tasks)})")
            self.clickable_regions.append({"id": "tab_tasks", "rect": tab_task_rect, "action": "select_tab", "data": "tasks"})

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
            painter.setFont(QFont("PingFang SC" if is_mac else "Microsoft YaHei", 9, QFont.Weight.Bold if not is_task_tab else QFont.Weight.Normal))
            painter.drawText(tab_sess_rect, Qt.AlignmentFlag.AlignCenter, f"会话列表 ({len(self.sessions)})")
            self.clickable_regions.append({"id": "tab_sessions", "rect": tab_sess_rect, "action": "select_tab", "data": "sessions"})

            tips_rect = QRectF(rect.right() - 340, tab_y, 320, 32)
            painter.setFont(QFont("PingFang SC" if is_mac else "Microsoft YaHei", 8))
            painter.setPen(QColor(100, 116, 139))
            tips_text = "单击行查看详情 · 点击 📌 锁定至悬浮窗" if is_task_tab else "单击会话行可查看综合指标或联动筛选所属任务"
            painter.drawText(tips_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, tips_text)

            # (4) 表头与点击排序交互
            th_y = tab_y + 38
            painter.setPen(QColor(148, 163, 184) if self.is_dark else QColor(100, 116, 139))
            painter.setFont(QFont("PingFang SC" if is_mac else "Microsoft YaHei", 8, QFont.Weight.Bold))

            if is_task_tab:
                # 📌
                painter.drawText(QRectF(rect.x() + 20, th_y, 30, 20), Qt.AlignmentFlag.AlignCenter, "📌")
                # # ↑↓
                th_id_rect = QRectF(rect.x() + 55, th_y, 45, 20)
                painter.drawText(th_id_rect, Qt.AlignmentFlag.AlignCenter, "# ↑↓")
                self.clickable_regions.append({"id": "th_id", "rect": th_id_rect, "action": "sort_col", "data": "id"})
                # 服务商
                th_prov_rect = QRectF(rect.x() + 105, th_y, 60, 20)
                painter.drawText(th_prov_rect, Qt.AlignmentFlag.AlignCenter, "服务商")
                self.clickable_regions.append({"id": "th_prov", "rect": th_prov_rect, "action": "sort_col", "data": "provider"})
                # 请求数 ↑↓
                th_req_rect = QRectF(rect.x() + 170, th_y, 65, 20)
                painter.drawText(th_req_rect, Qt.AlignmentFlag.AlignCenter, "请求数 ↑↓")
                self.clickable_regions.append({"id": "th_req", "rect": th_req_rect, "action": "sort_col", "data": "req"})
                # 总消耗 ↑↓
                th_tok_rect = QRectF(rect.x() + 240, th_y, 70, 20)
                painter.drawText(th_tok_rect, Qt.AlignmentFlag.AlignCenter, "总消耗 ↑↓")
                self.clickable_regions.append({"id": "th_tok", "rect": th_tok_rect, "action": "sort_col", "data": "tokens"})
                # 命中率 ↑↓
                th_hit_rect = QRectF(rect.x() + 315, th_y, 65, 20)
                painter.drawText(th_hit_rect, Qt.AlignmentFlag.AlignCenter, "命中率 ↑↓")
                self.clickable_regions.append({"id": "th_hit", "rect": th_hit_rect, "action": "sort_col", "data": "hit"})
                # 模型
                th_mod_rect = QRectF(rect.x() + 385, th_y, 110, 20)
                painter.drawText(th_mod_rect, Qt.AlignmentFlag.AlignLeft, "模型")
                self.clickable_regions.append({"id": "th_mod", "rect": th_mod_rect, "action": "sort_col", "data": "model"})
                # 任务标题
                painter.drawText(QRectF(rect.x() + 500, th_y, 240, 20), Qt.AlignmentFlag.AlignLeft, "任务标题")
            else:
                painter.drawText(QRectF(rect.x() + 24, th_y, 70, 20), Qt.AlignmentFlag.AlignLeft, "会话ID")
                painter.drawText(QRectF(rect.x() + 110, th_y, 60, 20), Qt.AlignmentFlag.AlignCenter, "服务商")
                painter.drawText(QRectF(rect.x() + 180, th_y, 120, 20), Qt.AlignmentFlag.AlignLeft, "模型")
                th_s_req = QRectF(rect.x() + 310, th_y, 65, 20)
                painter.drawText(th_s_req, Qt.AlignmentFlag.AlignCenter, "请求数 ↑↓")
                self.clickable_regions.append({"id": "th_s_req", "rect": th_s_req, "action": "sort_col", "data": "req"})
                th_s_tok = QRectF(rect.x() + 385, th_y, 75, 20)
                painter.drawText(th_s_tok, Qt.AlignmentFlag.AlignCenter, "消耗Token ↑↓")
                self.clickable_regions.append({"id": "th_s_tok", "rect": th_s_tok, "action": "sort_col", "data": "tokens"})
                th_s_hit = QRectF(rect.x() + 470, th_y, 65, 20)
                painter.drawText(th_s_hit, Qt.AlignmentFlag.AlignCenter, "命中率 ↑↓")
                self.clickable_regions.append({"id": "th_s_hit", "rect": th_s_hit, "action": "sort_col", "data": "hit"})
                painter.drawText(QRectF(rect.x() + 550, th_y, 200, 20), Qt.AlignmentFlag.AlignLeft, "会话描述 / 最后活跃")

            # (5) 表格数据行
            row_y = th_y + 24
            items_to_render = self.filtered_tasks if is_task_tab else self.sessions
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

                    # 服务商徽标
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

                    # 总消耗
                    painter.setPen(QColor(56, 189, 248))
                    painter.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
                    painter.drawText(QRectF(rect.x() + 240, row_y, 70, 40), Qt.AlignmentFlag.AlignCenter, f"{item['tokens']} tok")

                    # 命中率
                    painter.setPen(QColor(52, 211, 153))
                    painter.setFont(QFont("PingFang SC" if is_mac else "Microsoft YaHei", 8, QFont.Weight.Bold))
                    painter.drawText(QRectF(rect.x() + 315, row_y, 65, 40), Qt.AlignmentFlag.AlignCenter, f"⚡{item['hit']:.1f}%")

                    # 模型
                    painter.setPen(QColor(203, 213, 225) if self.is_dark else QColor(51, 65, 85))
                    painter.setFont(QFont("Consolas", 8))
                    painter.drawText(QRectF(rect.x() + 385, row_y, 110, 40), Qt.AlignmentFlag.AlignVCenter, item["model"])

                    # 任务标题
                    painter.setFont(QFont("PingFang SC" if is_mac else "Microsoft YaHei", 9, QFont.Weight.Bold))
                    painter.setPen(QColor(241, 245, 249) if self.is_dark else QColor(15, 23, 42))
                    painter.drawText(QRectF(rect.x() + 500, row_y, 240, 40), Qt.AlignmentFlag.AlignVCenter, item["name"])
                else:
                    self.clickable_regions.append({"id": f"sess_row_{idx}", "rect": row_rect, "action": "select_session", "data": idx})

                    painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
                    painter.setPen(QColor(56, 189, 248))
                    painter.drawText(QRectF(rect.x() + 24, row_y, 80, 40), Qt.AlignmentFlag.AlignVCenter, item["id"])

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

                    painter.setFont(QFont("PingFang SC" if is_mac else "Microsoft YaHei", 9))
                    painter.setPen(QColor(241, 245, 249))
                    painter.drawText(QRectF(rect.x() + 550, row_y, 200, 40), Qt.AlignmentFlag.AlignVCenter, f"{item['name']} ({item['time']})")

                row_y += 44

            # (6) 底部状态栏
            footer_y = rect.bottom() - 40
            painter.setBrush(QBrush(QColor(18, 24, 38) if self.is_dark else QColor(248, 250, 252)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(rect.x(), footer_y, rect.width(), 40), 14, 14)

            painter.setFont(QFont("PingFang SC" if is_mac else "Microsoft YaHei", 8))
            painter.setPen(QColor(148, 163, 184) if self.is_dark else QColor(100, 116, 139))
            painter.drawText(QRectF(rect.x() + 20, footer_y, 40, 40), Qt.AlignmentFlag.AlignVCenter, "接入:")

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
            painter.setFont(QFont("PingFang SC" if is_mac else "Microsoft YaHei", 8))
            painter.drawText(QRectF(rect.x() + 285, footer_y, 260, 40), Qt.AlignmentFlag.AlignVCenter, "· 支持按键滑动 W/A/S/D ↑↓←→")

            web_btn = QRectF(rect.right() - 220, footer_y + 8, 80, 24)
            painter.setBrush(QBrush(QColor(30, 41, 59) if self.is_dark else QColor(241, 245, 249)))
            painter.setPen(QPen(QColor(56, 189, 248, 80), 1))
            painter.drawRoundedRect(web_btn, 4, 4)
            painter.setPen(QColor(56, 189, 248))
            painter.drawText(web_btn, Qt.AlignmentFlag.AlignCenter, "🌐 Web 控制台")
            self.clickable_regions.append({"id": "panel_web", "rect": web_btn, "action": "open_web"})

            painter.setPen(QColor(148, 163, 184))
            cnt_text = f"共 {len(self.filtered_tasks)} 条  < 1 / 1 >" if is_task_tab else f"共 {len(self.sessions)} 会话"
            painter.drawText(QRectF(rect.right() - 130, footer_y, 110, 40), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, cnt_text)
