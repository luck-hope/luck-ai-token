"""
TokenTrackerGateway - 原生设置对话框 (ui/settings_dialog.py)
"""
import os
import webbrowser
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QCheckBox, QSlider, QComboBox, QPushButton, QTabWidget,
    QWidget, QFormLayout, QGroupBox, QMessageBox
)
from config import UPSTREAM_CONFIG, GATEWAY_PORT, GATEWAY_HOST

class SettingsDialog(QDialog):
    def __init__(self, parent=None, is_dark=True, on_save_callback=None):
        super().__init__(parent)
        self.is_dark = is_dark
        self.on_save_callback = on_save_callback
        self.setWindowTitle("TokenTrackerGateway - 参数与路由设置")
        self.setFixedSize(540, 480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Tab Widget
        tabs = QTabWidget()

        # Tab 1: 通用设置
        general_tab = QWidget()
        gen_layout = QFormLayout(general_tab)
        gen_layout.setContentsMargins(16, 16, 16, 16)
        gen_layout.setSpacing(14)

        self.port_input = QLineEdit(str(GATEWAY_PORT))
        gen_layout.addRow("本地网关端口:", self.port_input)

        self.top_check = QCheckBox("始终保持悬浮窗置顶 (Always On Top)")
        self.top_check.setChecked(True)
        gen_layout.addRow("窗口层级:", self.top_check)

        # 透明度
        opacity_box = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(50, 100)
        self.opacity_slider.setValue(100)
        self.opacity_label = QLabel("100%")
        self.opacity_slider.valueChanged.connect(lambda v: self.opacity_label.setText(f"{v}%"))
        opacity_box.addWidget(self.opacity_slider)
        opacity_box.addWidget(self.opacity_label)
        gen_layout.addRow("悬浮窗不透明度:", opacity_box)

        # 主题风格
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["深色夜间 (Dark)", "浅色白天 (Light)"])
        self.theme_combo.setCurrentIndex(0 if self.is_dark else 1)
        gen_layout.addRow("界面配色:", self.theme_combo)

        # 默认形态
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["长条胶囊 (Capsule)", "微型圆标 (Orb)", "全量看板 (Full Panel)"])
        gen_layout.addRow("默认形态:", self.mode_combo)

        tabs.addTab(general_tab, "⚙️ 通用偏好")

        # Tab 2: 服务商与密钥
        providers_tab = QWidget()
        prov_layout = QVBoxLayout(providers_tab)
        prov_layout.setContentsMargins(16, 16, 16, 16)
        prov_layout.setSpacing(12)

        # OpenAI
        openai_group = QGroupBox("OpenAI 路由配置")
        openai_form = QFormLayout(openai_group)
        self.openai_url = QLineEdit(UPSTREAM_CONFIG.providers["openai"]["base_url"])
        self.openai_key = QLineEdit(UPSTREAM_CONFIG.providers["openai"]["api_key"])
        self.openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        openai_form.addRow("Base URL:", self.openai_url)
        openai_form.addRow("API Key:", self.openai_key)
        prov_layout.addWidget(openai_group)

        # DeepSeek
        deepseek_group = QGroupBox("DeepSeek 深度求索配置")
        deepseek_form = QFormLayout(deepseek_group)
        self.deepseek_url = QLineEdit(UPSTREAM_CONFIG.providers["deepseek"]["base_url"])
        self.deepseek_key = QLineEdit(UPSTREAM_CONFIG.providers["deepseek"]["api_key"])
        self.deepseek_key.setEchoMode(QLineEdit.EchoMode.Password)
        deepseek_form.addRow("Base URL:", self.deepseek_url)
        deepseek_form.addRow("API Key:", self.deepseek_key)
        prov_layout.addWidget(deepseek_group)

        tabs.addTab(providers_tab, "🔑 上游密钥与路由")

        # Tab 3: 接入指南与关于
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)
        about_layout.setContentsMargins(16, 16, 16, 16)
        about_layout.setSpacing(12)

        desc = QLabel(
            "<b>TokenTrackerGateway</b> - 极轻量桌面 AI 用量网关与悬浮窗<br><br>"
            "<b>IDE 代理接入指南：</b><br>"
            "• 将 Cursor / VS Code / Claude Dev / Cline 等工具中的 OpenAI Base URL 设置为：<br>"
            f"&nbsp;&nbsp;<code style='color:#38bdf8;'>http://127.0.0.1:{GATEWAY_PORT}/v1</code><br>"
            "• 网关将自动拦截请求并提取 Prompt 缓存命中率与流式 Token 实时指标。"
        )
        desc.setWordWrap(True)
        desc.setTextFormat(Qt.TextFormat.RichText)
        about_layout.addWidget(desc)

        btn_web = QPushButton("🌐 打开 Web 仪表盘 (127.0.0.1)")
        btn_web.clicked.connect(lambda: webbrowser.open(f"http://127.0.0.1:{GATEWAY_PORT}"))
        about_layout.addWidget(btn_web)
        about_layout.addStretch()

        tabs.addTab(about_tab, "📖 接入指引")

        main_layout.addWidget(tabs)

        # Bottom buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("保存配置并应用")
        self.btn_save.setDefault(True)
        self.btn_save.clicked.connect(self.save_settings)
        btn_box.addWidget(self.btn_save)

        main_layout.addLayout(btn_box)

    def apply_theme(self):
        if self.is_dark:
            self.setStyleSheet("""
                QDialog {
                    background-color: #0f172a;
                    color: #f1f5f9;
                }
                QTabWidget::pane {
                    border: 1px solid #1e293b;
                    background: #1e293b;
                    border-radius: 6px;
                }
                QTabBar::tab {
                    background: #0f172a;
                    color: #94a3b8;
                    padding: 8px 16px;
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background: #1e293b;
                    color: #38bdf8;
                    font-weight: bold;
                }
                QLabel {
                    color: #cbd5e1;
                    font-size: 13px;
                }
                QLineEdit {
                    background: #0f172a;
                    border: 1px solid #334155;
                    border-radius: 4px;
                    padding: 6px 10px;
                    color: #f8fafc;
                    font-size: 13px;
                }
                QLineEdit:focus {
                    border: 1px solid #38bdf8;
                }
                QComboBox {
                    background: #0f172a;
                    border: 1px solid #334155;
                    border-radius: 4px;
                    padding: 6px 10px;
                    color: #f8fafc;
                }
                QGroupBox {
                    color: #38bdf8;
                    font-weight: bold;
                    border: 1px solid #334155;
                    border-radius: 6px;
                    margin-top: 10px;
                    padding-top: 14px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 4px;
                }
                QCheckBox {
                    color: #cbd5e1;
                }
                QPushButton {
                    background: #334155;
                    color: #f8fafc;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #475569;
                }
                QPushButton:default {
                    background: #0284c7;
                    color: white;
                }
                QPushButton:default:hover {
                    background: #0369a1;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #f8fafc;
                    color: #0f172a;
                }
                QTabWidget::pane {
                    border: 1px solid #e2e8f0;
                    background: #ffffff;
                    border-radius: 6px;
                }
                QTabBar::tab {
                    background: #f1f5f9;
                    color: #64748b;
                    padding: 8px 16px;
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background: #ffffff;
                    color: #0284c7;
                    font-weight: bold;
                }
                QLabel {
                    color: #334155;
                    font-size: 13px;
                }
                QLineEdit {
                    background: #ffffff;
                    border: 1px solid #cbd5e1;
                    border-radius: 4px;
                    padding: 6px 10px;
                    color: #0f172a;
                    font-size: 13px;
                }
                QLineEdit:focus {
                    border: 1px solid #0284c7;
                }
                QComboBox {
                    background: #ffffff;
                    border: 1px solid #cbd5e1;
                    border-radius: 4px;
                    padding: 6px 10px;
                    color: #0f172a;
                }
                QGroupBox {
                    color: #0284c7;
                    font-weight: bold;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    margin-top: 10px;
                    padding-top: 14px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 4px;
                }
                QPushButton {
                    background: #e2e8f0;
                    color: #1e293b;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #cbd5e1;
                }
                QPushButton:default {
                    background: #0284c7;
                    color: white;
                }
                QPushButton:default:hover {
                    background: #0369a1;
                }
            """)

    def save_settings(self):
        try:
            port = int(self.port_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "格式错误", "端口必须为数字 (例如 4000)")
            return

        # 更新全局 UpstreamConfig
        UPSTREAM_CONFIG.providers["openai"]["base_url"] = self.openai_url.text().strip()
        UPSTREAM_CONFIG.providers["openai"]["api_key"] = self.openai_key.text().strip()
        UPSTREAM_CONFIG.providers["deepseek"]["base_url"] = self.deepseek_url.text().strip()
        UPSTREAM_CONFIG.providers["deepseek"]["api_key"] = self.deepseek_key.text().strip()

        settings_data = {
            "port": port,
            "always_on_top": self.top_check.isChecked(),
            "opacity": self.opacity_slider.value() / 100.0,
            "is_dark": self.theme_combo.currentIndex() == 0,
            "mode": ["capsule", "circle", "expanded"][self.mode_combo.currentIndex()]
        }

        if self.on_save_callback:
            self.on_save_callback(settings_data)

        self.accept()
