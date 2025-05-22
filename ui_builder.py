import asyncio
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt
from channel_model import ChannelListModel
from styles import AppStyles
from pathlib import Path
from log_manager import LogManager

class UIBuilder:
    def __init__(self, main_window):
        self.main_window = main_window
        self.logger = LogManager()
        self._ui_initialized = False
        self._model_initialized = False

    def build_ui(self):
        if not self._ui_initialized:
            self._init_ui()
            self._setup_toolbar()
            self._ui_initialized = True

    def _setup_channel_list(self, parent: QtWidgets.QSplitter) -> None:  
        """配置频道列表"""
        if not self._model_initialized:
            self._model_initialized = True

    def _init_ui(self):
        """初始化用户界面"""
        self.main_window.setWindowTitle("IPTV Scanner Editor Pro / IPTV 专业扫描编辑工具")
        
        # 加载保存的窗口布局
        width, height, dividers = self.main_window.config.load_window_layout()
        self.main_window.resize(width, height)
        
        # 连接窗口大小变化信号
        self.main_window.resizeEvent = lambda e: self._on_window_resize(e)
        self.main_window.setStyleSheet(AppStyles.main_window_style())
        
        # 主布局
        main_widget = QtWidgets.QWidget()
        self.main_window.setCentralWidget(main_widget)
        main_layout = QtWidgets.QHBoxLayout(main_widget)
        self._init_splitters()
        main_layout.addWidget(self.main_window.main_splitter)

        # 强制应用布局设置
        if dividers and len(dividers) >= 2:
            self.main_window.main_splitter.setSizes(dividers[:2])
            self.main_window.left_splitter.setSizes(dividers[2:4])

        # 状态栏
        status_bar = self.main_window.statusBar()
        status_bar.show()
        status_bar.setStyleSheet(AppStyles.statusbar_style())
        
        self.main_window.progress_indicator = QtWidgets.QProgressBar()
        self.main_window.progress_indicator.setRange(0, 0)
        self.main_window.progress_indicator.setTextVisible(False)
        self.main_window.progress_indicator.setFixedWidth(120)
        self.main_window.progress_indicator.setStyleSheet(AppStyles.progress_style())
        self.main_window.progress_indicator.hide()
        status_bar.addPermanentWidget(self.main_window.progress_indicator)

    def _on_window_resize(self, event):
        """处理窗口大小变化事件"""
        try:
            size = self.main_window.size()
            # 保存当前分割器状态
            dividers = [
                *self.main_window.main_splitter.sizes(),
                *self.main_window.left_splitter.sizes(),
            ]
            
            # 保存窗口布局
            self.main_window.config.save_window_layout(size.width(), size.height(), dividers)
            event.accept()
            
            # 强制更新布局
            QtCore.QTimer.singleShot(50, lambda: [
                self.main_window.main_splitter.update(),
                self.main_window.main_splitter.updateGeometry()
            ])
        except Exception as e:
            self.logger.error(f"窗口大小变化处理错误: {str(e)}")

    def _init_splitters(self):
        """初始化所有分隔条控件"""
        # 加载保存的分隔条位置
        _, _, dividers = self.main_window.config.load_window_layout()
        
        # 主水平分割器（左右布局）
        self.main_window.main_splitter = QtWidgets.QSplitter(Qt.Orientation.Horizontal)
        self.main_window.main_splitter.setChildrenCollapsible(True)  # 允许子部件收起
        self.main_window.main_splitter.setHandleWidth(10)  # 设置足够大的手柄宽度
        self.main_window.main_splitter.setOpaqueResize(True)  # 实时更新分割器位置
        self._setup_custom_splitter(self.main_window.main_splitter)
        
        # 仅在未加载保存布局时设置默认值
        if not (dividers and len(dividers) >= 8):
            # 设置更合理的默认尺寸(基于窗口当前大小)
            width = self.main_window.width()
            height = self.main_window.height()
            self.main_window.main_splitter.setSizes([int(width*0.4), int(width*0.6)])
        
        # 左侧垂直分割器（扫描面板 + 频道列表）
        self.main_window.left_splitter = QtWidgets.QSplitter(Qt.Orientation.Vertical) 
        self._setup_custom_splitter(self.main_window.left_splitter)
        self._setup_scan_panel(self.main_window.left_splitter)
        self._setup_channel_list(self.main_window.left_splitter)

        # 右侧播放器面板
        right_container = QtWidgets.QWidget()
        self._setup_player_panel(right_container)

        # 组装主界面
        self.main_window.main_splitter.addWidget(self.main_window.left_splitter)
        self.main_window.main_splitter.addWidget(right_container)

        # 加载保存的分隔条位置
        _, _, dividers = self.main_window.config.load_window_layout()
        if dividers and len(dividers) >= 2:
            self.main_window.main_splitter.setSizes(dividers[:2])
            self.main_window.left_splitter.setSizes(dividers[2:4])

        else:
            # 设置更合理的默认尺寸(基于窗口当前大小)
            width = self.main_window.width()
            height = self.main_window.height()
            self.main_window.main_splitter.setSizes([int(width*0.4), int(width*0.6)])
            self.main_window.left_splitter.setSizes([int(height*0.4), int(height*0.6)])


    def _setup_custom_splitter(self, splitter):
        splitter.setChildrenCollapsible(False)
        
        # 必须设置足够大的handle宽度
        handle_size = 10
        splitter.setHandleWidth(handle_size)
        
        # 延迟设置确保splitter已初始化
        QtCore.QTimer.singleShot(100, lambda: self._install_handle(splitter))

    def _install_handle(self, splitter):
        if splitter.count() < 2:
            return
            
        handle = splitter.handle(1)
        handle.setStyleSheet("background: transparent;")
        
        # 创建并添加自定义手柄
        custom_handle = AndroidSplitterHandle(splitter.orientation())
        
        # 使用布局确保填充
        layout = QtWidgets.QHBoxLayout(handle) if splitter.orientation() == Qt.Orientation.Horizontal \
                else QtWidgets.QVBoxLayout(handle)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(custom_handle)
        
        # 连接事件
        custom_handle.mousePressEvent = lambda e: self._start_drag(splitter, e)
        custom_handle.mouseMoveEvent = lambda e: self._do_drag(splitter, e)

    def _start_drag(self, splitter, event):
        """开始拖动分隔条"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.globalPosition().toPoint()
            self._drag_splitter = splitter
            self._drag_start_sizes = splitter.sizes()
        else:
            event.ignore()

    def _do_drag(self, splitter, event):
        """处理拖动分隔条"""
        if not hasattr(self, '_drag_start_pos') or not self._drag_start_pos:
            return
            
        if event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint()
            delta = new_pos - self._drag_start_pos
            
            # 计算新尺寸
            sizes = self._drag_start_sizes.copy()
            total = sum(sizes)
            
            if splitter.orientation() == Qt.Orientation.Horizontal:
                sizes[0] = max(50, min(total-50, sizes[0] + delta.x()))
                sizes[1] = total - sizes[0]
            else:
                sizes[0] = max(50, min(total-50, sizes[0] + delta.y()))
                sizes[1] = total - sizes[0]
            
            splitter.setSizes(sizes)
            
            # 保存分隔条位置
            size = self.main_window.size()
            dividers = [
                *self.main_window.main_splitter.sizes(),
                *self.main_window.left_splitter.sizes(),
            ]
            self.main_window.config.save_window_layout(size.width(), size.height(), dividers)
        else:
            self._drag_start_pos = None

    def _setup_player_panel(self, parent: QtWidgets.QWidget) -> None:
        """配置播放器面板"""
        player_group = QtWidgets.QGroupBox("视频播放")
        player_layout = QtWidgets.QVBoxLayout()
        player_layout.setContentsMargins(2, 2, 2, 2)
        player_layout.setSpacing(5)
        
        # 播放器主体
        self.main_window.player = QtWidgets.QWidget()
        player_layout.addWidget(self.main_window.player, stretch=10)  # 大部分空间给播放器

        # 控制按钮区域
        control_layout = QtWidgets.QHBoxLayout()
        control_layout.setContentsMargins(0, 5, 0, 5)
        
        # 播放/停止按钮
        self.main_window.pause_btn = QtWidgets.QPushButton("播放")
        self.main_window.pause_btn.setStyleSheet(AppStyles.button_style(active=False))
        self.main_window.pause_btn.setEnabled(False)
        self.main_window.stop_btn = QtWidgets.QPushButton("停止")
        self.main_window.stop_btn.setStyleSheet(AppStyles.button_style(active=False))
        self.main_window.stop_btn.setEnabled(False)
        
        # 音量控制
        self.main_window.volume_slider = QtWidgets.QSlider(Qt.Orientation.Horizontal)
        self.main_window.volume_slider.setRange(0, 100)
        self.main_window.volume_slider.setValue(50)
        
        control_layout.addWidget(self.main_window.pause_btn)
        control_layout.addWidget(self.main_window.stop_btn)
        control_layout.addWidget(QtWidgets.QLabel("音量："))
        control_layout.addWidget(self.main_window.volume_slider)
        
        player_layout.addLayout(control_layout)
        player_group.setLayout(player_layout)
        parent.setLayout(QtWidgets.QVBoxLayout())
        parent.layout().addWidget(player_group)


    def _setup_scan_panel(self, parent: QtWidgets.QSplitter) -> None:
        """配置扫描面板"""
        scan_group = QtWidgets.QGroupBox("扫描设置")
        scan_layout = QtWidgets.QFormLayout()

        self.main_window.ip_range_input = QtWidgets.QLineEdit()
        self.main_window.scan_progress = QtWidgets.QProgressBar()
        self.main_window.scan_progress.setStyleSheet(AppStyles.progress_style())

        # 超时时间设置
        timeout_layout = QtWidgets.QHBoxLayout()
        timeout_label = QtWidgets.QLabel("设置扫描超时时间（秒）")
        timeout_layout.addWidget(timeout_label)
        self.main_window.timeout_input = QtWidgets.QSpinBox()
        self.main_window.timeout_input.setRange(1, 60)
        self.main_window.timeout_input.setValue(10)
        self.main_window.timeout_input.setSuffix(" 秒")
        timeout_layout.addWidget(self.main_window.timeout_input)
        self.main_window.timeout_input.valueChanged.connect(
            lambda: self.main_window.config.save_network_settings(
                self.main_window.ip_range_input.text(),
                self.main_window.timeout_input.value(),
                self.main_window.thread_count_input.value(),
                self.main_window.user_agent_input.text(),
                self.main_window.referer_input.text()
            )
        )
        
        # 线程数设置
        thread_layout = QtWidgets.QHBoxLayout()
        thread_label = QtWidgets.QLabel("设置扫描使用的线程数量")
        thread_layout.addWidget(thread_label)
        self.main_window.thread_count_input = QtWidgets.QSpinBox()
        self.main_window.thread_count_input.setRange(1, 100)
        self.main_window.thread_count_input.setValue(10)
        thread_layout.addWidget(self.main_window.thread_count_input)
        self.main_window.thread_count_input.valueChanged.connect(
            lambda: self.main_window.config.save_network_settings(
                self.main_window.ip_range_input.text(),
                self.main_window.timeout_input.value(),
                self.main_window.thread_count_input.value(),
                self.main_window.user_agent_input.text(),
                self.main_window.referer_input.text()
            )
        )

        # User-Agent设置
        user_agent_layout = QtWidgets.QHBoxLayout()
        user_agent_label = QtWidgets.QLabel("User-Agent:")
        user_agent_layout.addWidget(user_agent_label)
        self.main_window.user_agent_input = QtWidgets.QLineEdit()
        self.main_window.user_agent_input.setPlaceholderText("可选，留空使用默认")
        user_agent_layout.addWidget(self.main_window.user_agent_input)
        self.main_window.user_agent_input.textChanged.connect(
            lambda: self.main_window.config.save_network_settings(
                self.main_window.ip_range_input.text(),
                self.main_window.timeout_input.value(),
                self.main_window.thread_count_input.value(),
                self.main_window.user_agent_input.text(),
                self.main_window.referer_input.text()
            )
        )

        # Referer设置
        referer_layout = QtWidgets.QHBoxLayout()
        referer_label = QtWidgets.QLabel("Referer:")
        referer_layout.addWidget(referer_label)
        self.main_window.referer_input = QtWidgets.QLineEdit()
        self.main_window.referer_input.setPlaceholderText("可选，留空不使用")
        referer_layout.addWidget(self.main_window.referer_input)
        self.main_window.referer_input.textChanged.connect(
            lambda: self.main_window.config.save_network_settings(
                self.main_window.ip_range_input.text(),
                self.main_window.timeout_input.value(),
                self.main_window.thread_count_input.value(),
                self.main_window.user_agent_input.text(),
                self.main_window.referer_input.text()
            )
        )

        # 扫描控制按钮
        self.main_window.scan_btn = QtWidgets.QPushButton("完整扫描")
        self.main_window.scan_btn.setStyleSheet(AppStyles.button_style(active=True))
        self.main_window.scan_btn.setFixedHeight(36)
        
        # 扫描统计信息
        self.main_window.detailed_stats_label = QtWidgets.QLabel("总频道: 0 | 有效: 0 | 无效: 0 | 耗时: 0s")

        # 使用网格布局让按钮和统计信息并排显示
        button_stats_layout = QtWidgets.QGridLayout()
        button_stats_layout.addWidget(self.main_window.scan_btn, 0, 0, 1, 2)
        button_stats_layout.addWidget(self.main_window.detailed_stats_label, 1, 0, 1, 2)
        
        button_stats_layout.setColumnStretch(0, 1)
        button_stats_layout.setColumnStretch(1, 1)

        scan_layout.addRow("地址格式：", QtWidgets.QLabel("示例：http://192.168.1.1:1234/rtp/10.10.[1-20].[1-20]:5002   [1-20]表示范围"))
        scan_layout.addRow("输入地址：", self.main_window.ip_range_input)
        scan_layout.addRow("超时时间：", timeout_layout)
        scan_layout.addRow("线程数：", thread_layout)
        scan_layout.addRow("User-Agent：", user_agent_layout)
        scan_layout.addRow("Referer：", referer_layout)
        scan_layout.addRow("进度：", self.main_window.scan_progress)
        scan_layout.addRow(button_stats_layout)

        scan_group.setLayout(scan_layout)
        parent.addWidget(scan_group)

    def _setup_channel_list(self, parent: QtWidgets.QSplitter) -> None:  
        """配置频道列表"""
        list_group = QtWidgets.QGroupBox("频道列表")
        list_layout = QtWidgets.QVBoxLayout()

        # 工具栏
        toolbar = QtWidgets.QHBoxLayout()
        
        # 有效性检测按钮
        self.main_window.btn_validate = QtWidgets.QPushButton("检测有效性")
        self.main_window.btn_validate.setStyleSheet(AppStyles.button_style(active=True))
        self.main_window.btn_validate.setFixedHeight(36)
        
        # 隐藏无效项按钮
        self.main_window.btn_hide_invalid = QtWidgets.QPushButton("隐藏无效项")
        self.main_window.btn_hide_invalid.setStyleSheet(AppStyles.button_style(active=False))
        self.main_window.btn_hide_invalid.setFixedHeight(36)
        self.main_window.btn_hide_invalid.setEnabled(False)
        
        # 检测统计标签
        self.main_window.validate_stats_label = QtWidgets.QLabel("请先加载列表")
        
        toolbar.addWidget(self.main_window.btn_validate)
        toolbar.addWidget(self.main_window.btn_hide_invalid)
        toolbar.addWidget(self.main_window.validate_stats_label)
        toolbar.addStretch()
        list_layout.addLayout(toolbar)

        # 频道列表视图
        self.main_window.channel_list = QtWidgets.QTableView()
        self.main_window.channel_list.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.main_window.channel_list.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.main_window.channel_list.horizontalHeader().setStretchLastSection(True)
        self.main_window.channel_list.verticalHeader().setVisible(False)
        if not hasattr(self.main_window, 'model') or not self.main_window.model:
            self.main_window.model = ChannelListModel()
            self.main_window.model.update_status_label = self.main_window._update_validate_status
            self.main_window.channel_list.setModel(self.main_window.model)
        self.main_window.channel_list.setStyleSheet(AppStyles.list_style())
        
        # 设置列宽
        header = self.main_window.channel_list.horizontalHeader()
        header.setStretchLastSection(False)  # 禁用最后列自动拉伸
        header.setMinimumSectionSize(30)  # 最小列宽
        header.setMaximumSectionSize(1000)  # 最大列宽
        
        # 初始设置：URL列优先占用空间
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)
        
        # 其他列自适应内容
        for i in range(header.count()):
            if i != 2:  # 跳过URL列
                header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        
        # 强制延迟列严格按内容宽度
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        
        # 定义列宽调整函数
        def adjust_columns():
            if self.main_window.model.rowCount() > 0:
                # 有数据时：URL列自适应且占用多余空间
                header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Interactive)
                # 延迟列严格按内容宽度
                header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
                # 其他列自适应内容
                for i in range(header.count()):
                    if i not in (2, 5):  # 跳过URL列和延迟列
                        header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
            else:
                # 无数据时：URL列自动拉伸
                header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)

        # 监听数据变化重新计算布局和更新按钮状态
        def update_buttons():
            has_channels = self.main_window.model.rowCount() > 0
            self.main_window.pause_btn.setEnabled(has_channels)
            self.main_window.pause_btn.setStyleSheet(AppStyles.button_style(active=has_channels))
            adjust_columns()

        self.main_window.model.dataChanged.connect(lambda: header.resizeSections())
        self.main_window.model.dataChanged.connect(update_buttons)
        self.main_window.model.rowsInserted.connect(update_buttons)
        self.main_window.model.rowsRemoved.connect(update_buttons)
        self.main_window.model.modelReset.connect(update_buttons)
        
        # 启用拖放排序功能
        self.main_window.channel_list.setDragEnabled(True)
        self.main_window.channel_list.setAcceptDrops(True)
        self.main_window.channel_list.setDragDropOverwriteMode(False)
        self.main_window.channel_list.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.main_window.channel_list.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
        
        # 添加右键菜单
        self.main_window.channel_list.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.main_window.channel_list.customContextMenuRequested.connect(self._show_channel_context_menu)
        
        list_layout.addWidget(self.main_window.channel_list)
        list_group.setLayout(list_layout)
        parent.addWidget(list_group)


    def _show_channel_context_menu(self, pos):
        """显示频道列表的右键菜单"""
        index = self.main_window.channel_list.indexAt(pos)
        if not index.isValid():
            return
            
        menu = QtWidgets.QMenu()
        
        # 获取选中频道的URL和名称
        url = self.main_window.model.data(self.main_window.model.index(index.row(), 2))  # URL在第2列
        name = self.main_window.model.data(self.main_window.model.index(index.row(), 0))  # 名称在第0列
        
        # 添加复制频道名菜单项
        copy_name_action = QtGui.QAction("复制频道名", self.main_window)
        copy_name_action.triggered.connect(lambda: self._copy_channel_name(name))
        menu.addAction(copy_name_action)
        
        # 添加复制URL菜单项
        copy_url_action = QtGui.QAction("复制URL", self.main_window)
        copy_url_action.triggered.connect(lambda: self._copy_channel_url(url))
        menu.addAction(copy_url_action)
        
        # 添加删除频道菜单项
        delete_action = QtGui.QAction("删除频道", self.main_window)
        delete_action.triggered.connect(lambda: self._delete_selected_channel(index))
        menu.addAction(delete_action)
        
        # 显示菜单
        menu.exec(self.main_window.channel_list.viewport().mapToGlobal(pos))
        
    def _copy_channel_url(self, url):
        """复制频道URL到剪贴板"""
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(url)
        self.logger.info(f"已复制URL: {url}")
        
    def _copy_channel_name(self, name):
        """复制频道名到剪贴板"""
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(name)
        self.logger.info(f"已复制频道名: {name}")
        
    def _delete_selected_channel(self, index):
        """删除选中的频道"""
        if not index.isValid():
            return
            
        # 确认删除
        reply = QtWidgets.QMessageBox.question(
            self.main_window,
            "确认删除",
            "确定要删除这个频道吗?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            # 从模型中删除行
            self.main_window.model.removeRow(index.row())
            self.logger.info(f"已删除频道: 行 {index.row()}")
            
            # 更新状态标签
            if hasattr(self.main_window, 'validate_status_label'):
                self.main_window.validate_status_label.setText(
                    f"检测: {self.main_window.model.rowCount()}/0"
                )

    def _setup_toolbar(self):
        """初始化工具栏"""
        toolbar = self.main_window.addToolBar("主工具栏")
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.setMovable(False)
        toolbar.setIconSize(QtCore.QSize(24, 24))  # 设置合适的图标大小
        toolbar.setStyleSheet(AppStyles.toolbar_button_style())

        # 使用emoji作为文本的工具栏按钮
        def create_action(emoji, text, tooltip=None):
            """创建带有emoji文本的动作"""
            action = QtGui.QAction(f"{emoji} {text}", self.main_window)
            if tooltip:
                action.setToolTip(tooltip)
            return action

        # 主要功能按钮
        open_action = create_action("📂", "打开列表", "打开IPTV列表文件")
        save_action = create_action("💾", "保存列表", "保存当前列表到文件")
        about_action = create_action("ℹ️", "关于", "关于本程序")

        # 添加分隔符
        toolbar.addSeparator()

        # 添加按钮到工具栏
        toolbar.addAction(open_action)
        toolbar.addAction(save_action)
        toolbar.addAction(about_action)

    def _show_about_dialog(self):
        """显示关于对话框"""
        from about_dialog import AboutDialog
        dialog = AboutDialog(
            self.main_window)
        dialog.exec()


        
class AndroidSplitterHandle(QtWidgets.QWidget):
    def __init__(self, orientation, parent=None):
        super().__init__(parent)
        self._orientation = orientation
        self.setStyleSheet("background: transparent;")
        
    def sizeHint(self):
        """强制要求布局系统保留足够空间"""
        return QtCore.QSize(20, 20) if self._orientation == Qt.Orientation.Horizontal else QtCore.QSize(20, 20)
        
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        rect = self.rect()
        
        # 计算中心点和线条长度
        center = rect.center()
        line_length = min(rect.width(), rect.height()) - 0
        
        if self._orientation == Qt.Orientation.Horizontal:
            # 水平分隔条：短垂直线
            painter.drawLine(center.x(), center.y() - line_length//1, 
                            center.x(), center.y() + line_length//1)
        else:
            # 垂直分隔条：短水平线
            painter.drawLine(center.x() - line_length//1, center.y(),
                            center.x() + line_length//1, center.y())
