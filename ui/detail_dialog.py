"""
TokenTrackerGateway - 任务与会话指标详情卡片对话框 (ui/detail_dialog.py)
对齐 Web 预览端 SessionDetailDrawer.tsx 交互：
- 展示详细 Token 消耗 (Prompt / Completion / Total / 节省百分比)
- Prompt 指令分析与一键复制
- 锁定至悬浮胶囊 📌 切换
- 服务商徽标与模型状态
"""
import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QWidget, QFrame, QTextEdit, QApplication
)

class ItemDetailDialog(QDialog):
    def __init__(self, item_data: dict, item_type: str = "task", is_dark: bool = True, parent=None, on_toggle_pin=None, on_filter_session=None):
        super().__init__(parent)
        self.item = item_data
        self.item_type = item_type  # "task" | "session"
        self.is_dark = is_dark
        self.on_toggle_pin = on_toggle_pin
        self.on_filter_session = on_filter_session
        self.is_pinned = self.item.get("pinned", False)

        self.setWindowTitle("详细用量与指令分析")
        self.setFixedSize(560, 480)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)

        self.card = QFrame()
        self.card.setObjectName("detailCard")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # 1. 顶部 Header
        header = QFrame()
        header.setFixedHeight(48)
        header.setObjectName("modalHeader")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(18, 0, 14, 0)
        h_layout.setSpacing(10)

        is_task = (self.item_type == "task")
        tag_text = f"任务 #{self.item.get('id', 1)}" if is_task else f"会话 #{self.item.get('id', 'sess_001')}"
        tag_lbl = QLabel(tag_text)
        tag_lbl.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        tag_lbl.setStyleSheet("background-color: #0c4a6e; color: #38bdf8; border-radius: 4px; padding: 2px 8px;")

        title_lbl = QLabel("任务 (Turn) 详细消耗与指令分析" if is_task else "会话 (Session) 综合统计")
        title_lbl.setFont(QFont("PingFang SC", 9, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #f1f5f9;" if self.is_dark else "color: #0f172a;")

        # 钉住按钮
        self.btn_pin = QPushButton("📌 已锁定至胶囊" if self.is_pinned else "📌 锁定追踪")
        self.btn_pin.setObjectName("btnPinned" if self.is_pinned else "btnUnpinned")
        self.btn_pin.setFixedSize(100, 26)
        self.btn_pin.clicked.connect(self.toggle_pin_state)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(28, 28)
        btn_close.setObjectName("btnClose")
        btn_close.clicked.connect(self.reject)

        h_layout.addWidget(tag_lbl)
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        h_layout.addWidget(self.btn_pin)
        h_layout.addWidget(btn_close)
        card_layout.addWidget(header)

        # 2. 中间内容区
        body = QWidget()
        b_layout = QVBoxLayout(body)
        b_layout.setContentsMargins(18, 14, 18, 14)
        b_layout.setSpacing(12)

        # 卡片 1: 服务商与模型基础信息
        meta_card = QFrame()
        meta_card.setObjectName("innerCard")
        meta_layout = QVBoxLayout(meta_card)
        meta_layout.setContentsMargins(14, 12, 14, 12)
        meta_layout.setSpacing(8)

        meta_top = QHBoxLayout()
        prov_lbl = QLabel(self.item.get("provider", "openai").upper())
        prov_lbl.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        prov_lbl.setStyleSheet("background-color: #064e3b; color: #34d399; border-radius: 4px; padding: 2px 8px;")

        model_lbl = QLabel(f"模型: {self.item.get('model', 'o3-mini')}")
        model_lbl.setFont(QFont("Consolas", 8))
        model_lbl.setStyleSheet("background-color: #1e293b; color: #cbd5e1; border-radius: 4px; padding: 2px 8px;")

        time_lbl = QLabel(self.item.get("time", "2026-09-03 14:32:05"))
        time_lbl.setFont(QFont("Consolas", 8))
        time_lbl.setStyleSheet("color: #64748b;")

        meta_top.addWidget(prov_lbl)
        meta_top.addWidget(model_lbl)
        meta_top.addStretch()
        meta_top.addWidget(time_lbl)
        meta_layout.addLayout(meta_top)

        name_lbl = QLabel(self.item.get("name", "流式转发与上下文提取任务"))
        name_lbl.setFont(QFont("PingFang SC", 10, QFont.Weight.Bold))
        name_lbl.setStyleSheet("color: #f8fafc;" if self.is_dark else "color: #0f172a;")
        meta_layout.addWidget(name_lbl)
        b_layout.addWidget(meta_card)

        # 卡片 2: 四维数据指标网格 (Tokens / Hit / Cost / Requests)
        grid_card = QFrame()
        grid_card.setObjectName("innerCard")
        g_layout = QHBoxLayout(grid_card)
        g_layout.setContentsMargins(12, 12, 12, 12)
        g_layout.setSpacing(10)

        tokens_box = self.create_stat_box("总消耗 Token", f"{self.item.get('tokens', 165)}", "#38bdf8")
        hit_box = self.create_stat_box("缓存命中率", f"{self.item.get('hit', 82.5):.1f}%", "#34d399")
        cost_box = self.create_stat_box("预估成本 (¥)", f"¥{self.item.get('cost', 0.0032):.4f}", "#f59e0b")
        req_box = self.create_stat_box("请求频次", f"{self.item.get('req', 1)} 次", "#a855f7")

        g_layout.addWidget(tokens_box)
        g_layout.addWidget(hit_box)
        g_layout.addWidget(cost_box)
        g_layout.addWidget(req_box)
        b_layout.addWidget(grid_card)

        # 卡片 3: 指令分析与代码/Prompt 预览
        prompt_card = QFrame()
        prompt_card.setObjectName("innerCard")
        p_layout = QVBoxLayout(prompt_card)
        p_layout.setContentsMargins(12, 10, 12, 10)
        p_layout.setSpacing(8)

        p_header = QHBoxLayout()
        p_title = QLabel("📝 用户 Prompt 上下文与指令片段:")
        p_title.setFont(QFont("PingFang SC", 8, QFont.Weight.Bold))
        p_title.setStyleSheet("color: #94a3b8;")

        btn_copy = QPushButton("复制指令 📋")
        btn_copy.setFixedSize(76, 24)
        btn_copy.setObjectName("btnCopy")
        prompt_text = f"优化 {self.item.get('model', 'o3-mini')} 在流式响应下的 Prompt 缓存命中率与上下文 token 复用: {self.item.get('name', '')}"
        btn_copy.clicked.connect(lambda: (QApplication.clipboard().setText(prompt_text), btn_copy.setText("已复制 ✓")))

        p_header.addWidget(p_title)
        p_header.addStretch()
        p_header.addWidget(btn_copy)
        p_layout.addLayout(p_header)

        prompt_box = QTextEdit()
        prompt_box.setReadOnly(True)
        prompt_box.setPlainText(prompt_text)
        prompt_box.setFixedHeight(75)
        prompt_box.setObjectName("promptBox")
        p_layout.addWidget(prompt_box)
        b_layout.addWidget(prompt_card)

        card_layout.addWidget(body, 1)

        # 3. 底部操作栏
        footer = QFrame()
        footer.setFixedHeight(48)
        footer.setObjectName("modalFooter")
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(18, 0, 18, 0)

        if not is_task and self.on_filter_session:
            btn_filter = QPushButton("🔍 查看该会话关联的所有任务")
            btn_filter.setObjectName("btnFilter")
            btn_filter.clicked.connect(self.filter_session_tasks)
            f_layout.addWidget(btn_filter)

        f_layout.addStretch()
        btn_ok = QPushButton("确定")
        btn_ok.setFixedSize(70, 30)
        btn_ok.setObjectName("btnSave")
        btn_ok.clicked.connect(self.accept)
        f_layout.addWidget(btn_ok)
        card_layout.addWidget(footer)

        root_layout.addWidget(self.card)
        self.apply_qss()

    def create_stat_box(self, label: str, value: str, color_hex: str) -> QFrame:
        box = QFrame()
        box.setObjectName("statBox")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        val_lbl = QLabel(value)
        val_lbl.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        val_lbl.setStyleSheet(f"color: {color_hex};")
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_lbl = QLabel(label)
        title_lbl.setFont(QFont("PingFang SC", 7))
        title_lbl.setStyleSheet("color: #94a3b8;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(val_lbl)
        layout.addWidget(title_lbl)
        return box

    def toggle_pin_state(self):
        self.is_pinned = not self.is_pinned
        if self.is_pinned:
            self.btn_pin.setText("📌 已锁定至胶囊")
            self.btn_pin.setObjectName("btnPinned")
        else:
            self.btn_pin.setText("📌 锁定追踪")
            self.btn_pin.setObjectName("btnUnpinned")
        self.btn_pin.style().unpolish(self.btn_pin)
        self.btn_pin.style().polish(self.btn_pin)

        if self.on_toggle_pin:
            self.on_toggle_pin(self.item.get("id"), self.is_pinned)

    def filter_session_tasks(self):
        if self.on_filter_session:
            self.on_filter_session(self.item.get("id"))
        self.accept()

    def apply_qss(self):
        self.setStyleSheet("""
            QDialog {
                background: transparent;
            }
            #detailCard {
                background-color: #131720;
                border: 1px solid #334155;
                border-radius: 12px;
            }
            #modalHeader {
                background-color: #181c26;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: 1px solid #1e293b;
            }
            #btnClose {
                background: transparent;
                color: #94a3b8;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            #btnClose:hover {
                background-color: #ef4444;
                color: #ffffff;
            }
            #innerCard {
                background-color: #181c26;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
            #statBox {
                background-color: #0d111a;
                border: 1px solid #1e293b;
                border-radius: 6px;
            }
            #btnPinned {
                background-color: #78350f;
                color: #fef3c7;
                border: 1px solid #f59e0b;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }
            #btnUnpinned {
                background-color: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 4px;
                font-size: 10px;
            }
            #btnUnpinned:hover {
                background-color: #334155;
                color: #f1f5f9;
            }
            #btnCopy {
                background-color: #1e293b;
                color: #38bdf8;
                border: 1px solid #0284c7;
                border-radius: 4px;
                font-size: 9px;
            }
            #btnCopy:hover {
                background-color: #0284c7;
                color: #ffffff;
            }
            #promptBox {
                background-color: #0d111a;
                color: #cbd5e1;
                border: 1px solid #1e293b;
                border-radius: 6px;
                font-family: Consolas, PingFang SC, monospace;
                font-size: 11px;
                padding: 6px;
            }
            #modalFooter {
                background-color: #181c26;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                border-top: 1px solid #1e293b;
            }
            #btnSave {
                background-color: #0284c7;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            #btnSave:hover {
                background-color: #0369a1;
            }
            #btnFilter {
                background-color: #1e293b;
                color: #38bdf8;
                border: 1px solid #0284c7;
                border-radius: 6px;
                font-size: 11px;
                padding: 4px 10px;
            }
            #btnFilter:hover {
                background-color: #0284c7;
                color: #ffffff;
            }
        """)
