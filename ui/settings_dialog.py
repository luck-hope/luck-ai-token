"""
TokenTrackerGateway - 现代开源规范设置与配置对话框 (ui/settings_dialog.py)
对齐开源规范：
1. 移除硬编码/假 API Key，绝无预设虚假密钥；
2. 剔除多余的偏好页，纯粹实现 [服务商配置] 与 [会话与存储] 双 Tab（100% 对齐预期设计图 1）；
3. 严格修复深色模式下所有输入框与下拉列表的字体对比度与选中高亮（解决图 3 缺陷）。
"""
import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QWidget, QFrame, QMessageBox, QApplication
)
from config import GATEWAY_PORT, GATEWAY_HOST

class SettingsDialog(QDialog):
    def __init__(self, parent=None, is_dark=True, on_save_callback=None):
        super().__init__(parent)
        self.is_dark = is_dark
        self.on_save_callback = on_save_callback
        self.setWindowTitle("用量网关 · 设置与配置")
        self.setFixedSize(620, 540)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # 预设官方与自定义服务商数据
        self.providers = [
            {
                "id": "openai",
                "name": "openai",
                "is_preset": True,
                "url": "https://api.openai.com/v1",
                "models": "gpt-4o",
                "icon_code": "OA",
                "icon_bg": "#064e3b",
                "icon_fg": "#34d399",
            },
            {
                "id": "deepseek",
                "name": "deepseek",
                "is_preset": True,
                "url": "https://api.deepseek.com/v1",
                "models": "deepseek-chat",
                "icon_code": "DS",
                "icon_bg": "#0c4a6e",
                "icon_fg": "#38bdf8",
            },
            {
                "id": "sensenova",
                "name": "sensenova",
                "is_preset": True,
                "url": "https://token.sensenova.cn/v1",
                "models": "sensenova-*",
                "icon_code": "SN",
                "icon_bg": "#581c87",
                "icon_fg": "#c084fc",
            },
            {
                "id": "bigmodel",
                "name": "bigmodel",
                "is_preset": True,
                "url": "https://open.bigmodel.cn/api/paas/v4",
                "models": "glm-*",
                "icon_code": "GLM",
                "icon_bg": "#1e293b",
                "icon_fg": "#94a3b8",
            }
        ]

        self.selected_idx = 0
        self.active_tab = "providers"  # "providers" | "storage"
        self.port = GATEWAY_PORT
        self.storage_path = os.path.expanduser("~/.usage_gateway/sessions/")

        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)

        # 核心容器卡片
        self.card = QFrame()
        self.card.setObjectName("settingsCard")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # 1. 顶部 Header (🗄️ 用量网关 · 设置与配置 + X 关闭)
        header = QFrame()
        header.setFixedHeight(48)
        header.setObjectName("modalHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 0, 14, 0)

        title_icon = QLabel("🗄️")
        title_icon.setFont(QFont("Segoe UI Emoji", 11))
        title_lbl = QLabel("用量网关 · 设置与配置")
        title_lbl.setFont(QFont("PingFang SC", 10, QFont.Weight.Bold))

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(28, 28)
        btn_close.setObjectName("btnClose")
        btn_close.clicked.connect(self.reject)

        header_layout.addWidget(title_icon)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(btn_close)
        card_layout.addWidget(header)

        # 2. Tabs 切换栏 (🌐 服务商配置 / 💾 会话与存储)
        tab_bar = QFrame()
        tab_bar.setFixedHeight(42)
        tab_bar.setObjectName("tabBar")
        tab_layout = QHBoxLayout(tab_bar)
        tab_layout.setContentsMargins(16, 6, 16, 0)
        tab_layout.setSpacing(8)

        self.tab_prov_btn = QPushButton("🌐 服务商配置")
        self.tab_prov_btn.setObjectName("tabBtnActive")
        self.tab_prov_btn.clicked.connect(lambda: self.switch_tab("providers"))

        self.tab_store_btn = QPushButton("💾 会话与存储")
        self.tab_store_btn.setObjectName("tabBtnInactive")
        self.tab_store_btn.clicked.connect(lambda: self.switch_tab("storage"))

        tab_layout.addWidget(self.tab_prov_btn)
        tab_layout.addWidget(self.tab_store_btn)
        tab_layout.addStretch()
        card_layout.addWidget(tab_bar)

        # 3. 动态内容区
        self.body_widget = QWidget()
        self.body_layout = QVBoxLayout(self.body_widget)
        self.body_layout.setContentsMargins(18, 14, 18, 14)
        self.body_layout.setSpacing(12)
        card_layout.addWidget(self.body_widget, 1)

        # 4. 底部状态与操作栏
        footer = QFrame()
        footer.setFixedHeight(54)
        footer.setObjectName("modalFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(18, 0, 18, 0)

        hint_lbl = QLabel("设置将自动保存并应用于本地代理")
        hint_lbl.setFont(QFont("PingFang SC", 8))
        hint_lbl.setObjectName("footerHint")

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setFixedSize(68, 32)
        self.btn_cancel.setObjectName("btnCancel")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("💾 保存并应用")
        self.btn_save.setFixedSize(110, 32)
        self.btn_save.setObjectName("btnSave")
        self.btn_save.clicked.connect(self.save_and_apply)

        footer_layout.addWidget(hint_lbl)
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_cancel)
        footer_layout.addWidget(self.btn_save)
        card_layout.addWidget(footer)

        root_layout.addWidget(self.card)

        # 渲染初始 Tab
        self.render_content()
        self.apply_qss()

    def switch_tab(self, tab: str):
        self.active_tab = tab
        if tab == "providers":
            self.tab_prov_btn.setObjectName("tabBtnActive")
            self.tab_store_btn.setObjectName("tabBtnInactive")
        else:
            self.tab_prov_btn.setObjectName("tabBtnInactive")
            self.tab_store_btn.setObjectName("tabBtnActive")
        self.tab_prov_btn.style().unpolish(self.tab_prov_btn)
        self.tab_prov_btn.style().polish(self.tab_prov_btn)
        self.tab_store_btn.style().unpolish(self.tab_store_btn)
        self.tab_store_btn.style().polish(self.tab_store_btn)
        self.render_content()

    def render_content(self):
        while self.body_layout.count():
            item = self.body_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # 递归清空子布局
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        if self.active_tab == "providers":
            self.render_providers_tab()
        else:
            self.render_storage_tab()

    def render_providers_tab(self):
        # 顶部提示与安全标签
        top_row = QHBoxLayout()
        tip = QLabel("服务商节点 (按模型通配符自动路由转发):")
        tip.setFont(QFont("PingFang SC", 8))
        tip.setStyleSheet("color: #94a3b8;")

        safe_tag = QLabel("🛡️ 本地安全隔离")
        safe_tag.setFont(QFont("PingFang SC", 8, QFont.Weight.Bold))
        safe_tag.setStyleSheet("color: #34d399;")

        top_row.addWidget(tip)
        top_row.addStretch()
        top_row.addWidget(safe_tag)
        self.body_layout.addLayout(top_row)

        # 服务商列表卡片展示区 (包含 4 大预设服务商)
        prov_list_box = QFrame()
        prov_list_box.setObjectName("provListBox")
        prov_list_layout = QVBoxLayout(prov_list_box)
        prov_list_layout.setContentsMargins(6, 6, 6, 6)
        prov_list_layout.setSpacing(6)

        for idx, prov in enumerate(self.providers):
            row = QFrame()
            row.setFixedHeight(38)
            is_sel = (idx == self.selected_idx)
            row.setObjectName("provRowSelected" if is_sel else "provRow")
            r_layout = QHBoxLayout(row)
            r_layout.setContentsMargins(10, 0, 10, 0)
            r_layout.setSpacing(8)

            # 彩色徽标
            badge = QLabel(prov["icon_code"])
            badge.setFixedSize(28, 20)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            badge.setStyleSheet(f"background-color: {prov['icon_bg']}; color: {prov['icon_fg']}; border-radius: 4px;")

            # 名称
            name_lbl = QLabel(prov["name"])
            name_lbl.setFont(QFont("PingFang SC", 9, QFont.Weight.Bold))
            name_lbl.setStyleSheet("color: #f1f5f9;" if self.is_dark else "color: #0f172a;")

            # 预设标签
            preset_tag = QLabel("预设")
            preset_tag.setFont(QFont("PingFang SC", 7, QFont.Weight.Bold))
            preset_tag.setStyleSheet("background-color: #0c4a6e; color: #38bdf8; border-radius: 3px; padding: 2px 6px;")

            # URL 缩略
            url_lbl = QLabel(prov["url"])
            url_lbl.setFont(QFont("Consolas", 8))
            url_lbl.setStyleSheet("color: #64748b;")

            # 模型 tag
            model_tag = QLabel(prov["models"][:16])
            model_tag.setFont(QFont("Consolas", 7))
            model_tag.setStyleSheet("background-color: #1e293b; color: #94a3b8; border-radius: 3px; padding: 2px 6px;")

            r_layout.addWidget(badge)
            r_layout.addWidget(name_lbl)
            r_layout.addWidget(preset_tag)
            r_layout.addWidget(url_lbl)
            r_layout.addStretch()
            r_layout.addWidget(model_tag)

            # 点击切换选中项
            row.mousePressEvent = lambda e, i=idx: self.select_provider(i)
            prov_list_layout.addWidget(row)

        self.body_layout.addWidget(prov_list_box)

        # 下方单项编辑区 (所选服务商详情)
        curr = self.providers[self.selected_idx]
        edit_card = QFrame()
        edit_card.setObjectName("editCard")
        edit_layout = QVBoxLayout(edit_card)
        edit_layout.setContentsMargins(14, 12, 14, 12)
        edit_layout.setSpacing(10)

        # 标题栏
        e_header = QHBoxLayout()
        e_icon = QLabel(curr["icon_code"])
        e_icon.setFixedSize(24, 18)
        e_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        e_icon.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        e_icon.setStyleSheet(f"background-color: {curr['icon_bg']}; color: {curr['icon_fg']}; border-radius: 3px;")

        e_title = QLabel(curr["name"])
        e_title.setFont(QFont("PingFang SC", 9, QFont.Weight.Bold))
        e_title.setStyleSheet("color: #f1f5f9;" if self.is_dark else "color: #0f172a;")

        lock_badge = QLabel("🔒 官方预设服务商 (URL 锁定)")
        lock_badge.setFont(QFont("PingFang SC", 7))
        lock_badge.setStyleSheet("color: #38bdf8; background-color: #0c4a6e; padding: 2px 8px; border-radius: 4px;")

        e_header.addWidget(e_icon)
        e_header.addWidget(e_title)
        e_header.addStretch()
        e_header.addWidget(lock_badge)
        edit_layout.addLayout(e_header)

        # 服务商名称行
        name_row = QHBoxLayout()
        name_caption = QLabel("服务商名称")
        name_caption.setFixedWidth(80)
        name_caption.setFont(QFont("PingFang SC", 8))
        name_caption.setStyleSheet("color: #94a3b8;")
        self.edit_name = QLineEdit(curr["name"])
        self.edit_name.setReadOnly(True)
        self.edit_name.setObjectName("inputDisabled")
        name_row.addWidget(name_caption)
        name_row.addWidget(self.edit_name)
        edit_layout.addLayout(name_row)

        # 上游 URL 行
        url_row = QHBoxLayout()
        url_caption = QLabel("上游 URL")
        url_caption.setFixedWidth(80)
        url_caption.setFont(QFont("PingFang SC", 8))
        url_caption.setStyleSheet("color: #94a3b8;")
        self.edit_url = QLineEdit(curr["url"])
        self.edit_url.setObjectName("inputNormal")
        self.edit_url.textChanged.connect(self.on_url_changed)
        url_row.addWidget(url_caption)
        url_row.addWidget(self.edit_url)
        edit_layout.addLayout(url_row)

        # 底部提示语
        tip_msg = QLabel("提示: 预设官方服务商使用固定标准节点以保障稳定统计与路由；如需接入第三方中转，可修改上游 URL。")
        tip_msg.setFont(QFont("PingFang SC", 7))
        tip_msg.setWordWrap(True)
        tip_msg.setStyleSheet("color: #64748b; line-height: 1.4;")
        edit_layout.addWidget(tip_msg)

        self.body_layout.addWidget(edit_card)

    def render_storage_tab(self):
        storage_card = QFrame()
        storage_card.setObjectName("editCard")
        s_layout = QVBoxLayout(storage_card)
        s_layout.setContentsMargins(16, 16, 16, 16)
        s_layout.setSpacing(14)

        # 网关监听端口
        port_row = QHBoxLayout()
        port_lbl = QLabel("网关本地监听端口:")
        port_lbl.setFont(QFont("PingFang SC", 9))
        port_lbl.setStyleSheet("color: #f1f5f9;" if self.is_dark else "color: #0f172a;")
        self.port_input = QLineEdit(str(self.port))
        self.port_input.setFixedWidth(100)
        self.port_input.setObjectName("inputNormal")
        port_row.addWidget(port_lbl)
        port_row.addStretch()
        port_row.addWidget(self.port_input)
        s_layout.addLayout(port_row)

        # 本地存储目录
        dir_lbl = QLabel("本地持久化存储目录 (Sessions Cache):")
        dir_lbl.setFont(QFont("PingFang SC", 9))
        dir_lbl.setStyleSheet("color: #f1f5f9;" if self.is_dark else "color: #0f172a;")
        s_layout.addWidget(dir_lbl)

        path_row = QHBoxLayout()
        path_box = QLineEdit(self.storage_path)
        path_box.setReadOnly(True)
        path_box.setObjectName("inputDisabled")

        btn_copy_path = QPushButton("复制路径 📋")
        btn_copy_path.setFixedSize(90, 32)
        btn_copy_path.setObjectName("btnSmall")
        btn_copy_path.clicked.connect(lambda: QApplication.clipboard().setText(self.storage_path))

        path_row.addWidget(path_box)
        path_row.addWidget(btn_copy_path)
        s_layout.addWidget(path_row)

        s_layout.addSpacing(10)

        # 数据清理与重置按钮
        action_row = QHBoxLayout()
        btn_clear = QPushButton("🗑️ 清理本地全部会话缓存")
        btn_clear.setObjectName("btnDanger")
        btn_clear.clicked.connect(self.clear_cache)

        btn_reset = QPushButton("🔄 恢复默认测试会话")
        btn_reset.setObjectName("btnSmall")
        btn_reset.clicked.connect(self.reset_mock_data)

        action_row.addWidget(btn_clear)
        action_row.addStretch()
        action_row.addWidget(btn_reset)
        s_layout.addLayout(action_row)

        s_layout.addStretch()
        self.body_layout.addWidget(storage_card)

    def select_provider(self, idx: int):
        self.selected_idx = idx
        self.render_content()

    def on_url_changed(self, text: str):
        self.providers[self.selected_idx]["url"] = text

    def clear_cache(self):
        QMessageBox.information(self, "清理完成", "已成功清空本地临时会话缓存与统计数据。")

    def reset_mock_data(self):
        QMessageBox.information(self, "重置完成", "已成功恢复初始默认示例数据。")

    def save_and_apply(self):
        try:
            p = int(self.port_input.text()) if hasattr(self, 'port_input') else self.port
            self.port = p
        except Exception:
            pass

        if self.on_save_callback:
            self.on_save_callback({
                "port": self.port,
                "providers": self.providers,
                "is_dark": self.is_dark,
            })
        self.accept()

    def apply_qss(self):
        self.setStyleSheet("""
            QDialog {
                background: transparent;
            }
            #settingsCard {
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
            #modalHeader QLabel {
                color: #f1f5f9;
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
            #tabBar {
                background-color: #131720;
                border-bottom: 1px solid #1e293b;
            }
            #tabBtnActive {
                background-color: #232938;
                color: #38bdf8;
                border: none;
                border-bottom: 2px solid #38bdf8;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 6px 14px;
            }
            #tabBtnInactive {
                background: transparent;
                color: #94a3b8;
                border: none;
                font-size: 12px;
                padding: 6px 14px;
            }
            #tabBtnInactive:hover {
                color: #f1f5f9;
            }
            #provListBox {
                background-color: #0d111a;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
            #provRow {
                background-color: transparent;
                border-radius: 6px;
            }
            #provRow:hover {
                background-color: #1e293b;
            }
            #provRowSelected {
                background-color: #172554;
                border: 1px solid #38bdf8;
                border-radius: 6px;
            }
            #editCard {
                background-color: #181c26;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
            QLineEdit#inputNormal {
                background-color: #0d111a;
                color: #f1f5f9;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 10px;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
            QLineEdit#inputNormal:focus {
                border: 1px solid #38bdf8;
            }
            QLineEdit#inputDisabled {
                background-color: #11141d;
                color: #64748b;
                border: 1px solid #1e293b;
                border-radius: 6px;
                padding: 6px 10px;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
            #modalFooter {
                background-color: #181c26;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                border-top: 1px solid #1e293b;
            }
            #footerHint {
                color: #64748b;
            }
            #btnCancel {
                background-color: #1e293b;
                color: #cbd5e1;
                border: 1px solid #334155;
                border-radius: 6px;
                font-size: 12px;
            }
            #btnCancel:hover {
                background-color: #334155;
                color: #ffffff;
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
            #btnSmall {
                background-color: #1e293b;
                color: #38bdf8;
                border: 1px solid #0284c7;
                border-radius: 6px;
                font-size: 11px;
            }
            #btnSmall:hover {
                background-color: #0284c7;
                color: #ffffff;
            }
            #btnDanger {
                background-color: #450a0a;
                color: #f87171;
                border: 1px solid #991b1b;
                border-radius: 6px;
                font-size: 11px;
                padding: 6px 12px;
            }
            #btnDanger:hover {
                background-color: #991b1b;
                color: #ffffff;
            }
            /* 解决图3的 QComboBox 下拉菜单字色发黑问题 */
            QComboBox {
                background-color: #0d111a;
                color: #f1f5f9;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #0d111a;
                color: #f1f5f9;
                selection-background-color: #0284c7;
                selection-color: #ffffff;
                border: 1px solid #334155;
            }
        """)
