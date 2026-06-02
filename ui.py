import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFileDialog, QListWidget, QMessageBox,
                             QTabWidget, QProgressBar, QLineEdit, QSpinBox, QGroupBox,
                             QCheckBox, QScrollArea, QFrame, QSizePolicy, QComboBox,
                             QPlainTextEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from core import FileProcessor, CHUNK_SIZE

class WorkerThread(QThread):
    progress_updated = pyqtSignal(int)
    operation_completed = pyqtSignal(str, bool)
    
    def __init__(self, operation, *args, **kwargs):
        super().__init__()
        self.operation = operation
        self.args = args
        self.kwargs = kwargs

    @staticmethod
    def format_file_list(title, paths, limit=30):
        names = [os.path.basename(path) for path in paths]
        if not names:
            return f"{title}: None"

        visible_names = names[:limit]
        lines = [f"{title} ({len(names)}):"]
        lines.extend(f"- {name}" for name in visible_names)
        if len(names) > limit:
            lines.append(f"- ...and {len(names) - limit} more")
        return "\n".join(lines)
    
    def run(self):
        try:
            if self.operation == "split":
                file_path, chunk_size, delete_original, output_dir = self.args
                chunk_paths = FileProcessor.split_file(file_path, chunk_size, delete_original, output_dir)
                message = (
                    f"Split complete: {os.path.basename(file_path)}\n\n"
                    f"{self.format_file_list('Created chunks', chunk_paths)}"
                )
                self.operation_completed.emit(message, True)
            elif self.operation == "merge":
                output_path, chunk_paths, delete_chunks = self.args
                FileProcessor.merge_files(output_path, chunk_paths, delete_chunks)
                message = (
                    f"Merge complete: {os.path.basename(output_path)}\n"
                    f"Output: {output_path}\n\n"
                    f"{self.format_file_list('Merged chunks', chunk_paths)}"
                )
                self.operation_completed.emit(message, True)
            elif self.operation == "auto_split":
                directory, chunk_size, delete_original, output_dir = self.args
                large_files = FileProcessor.find_large_files(directory, chunk_size)
                split_files = []
                created_chunks = []
                for i, file in enumerate(large_files):
                    self.progress_updated.emit((i + 1) * 100 // len(large_files))
                    full_path = os.path.join(directory, file)
                    chunk_paths = FileProcessor.split_file(full_path, chunk_size, delete_original, output_dir)
                    split_files.append(full_path)
                    created_chunks.extend(chunk_paths)
                message = (
                    f"Auto split complete: {len(split_files)} file(s) processed.\n\n"
                    f"{self.format_file_list('Split files', split_files)}\n\n"
                    f"{self.format_file_list('Created chunks', created_chunks)}"
                )
                self.operation_completed.emit(message, True)
            elif self.operation == "auto_merge":
                directory, delete_chunks, output_dir = self.args
                file_groups = FileProcessor.find_chunk_groups(directory)
                merged_outputs = []
                merged_chunks = []
                for i, (prefix, group_info) in enumerate(file_groups.items()):
                    self.progress_updated.emit((i + 1) * 100 // len(file_groups))
                    chunks = group_info['chunks']
                    ext = group_info['extension']
                    
                    # Determine output path
                    if output_dir:
                        # Create subdirectory structure in output directory
                        target_dir = os.path.join(output_dir, os.path.dirname(prefix))
                        os.makedirs(target_dir, exist_ok=True)
                        output_filename = f"{os.path.basename(prefix)}{ext}"
                        output_path = os.path.join(target_dir, output_filename)
                    else:
                        # Use original directory structure
                        output_path = os.path.join(directory, f"{prefix}{ext}")
                    
                    FileProcessor.merge_files(output_path, chunks, delete_chunks)
                    merged_outputs.append(output_path)
                    merged_chunks.extend(chunks)
                message = (
                    f"Auto merge complete: {len(merged_outputs)} file group(s) processed.\n\n"
                    f"{self.format_file_list('Merged files', merged_outputs)}\n\n"
                    f"{self.format_file_list('Merged chunks', merged_chunks)}"
                )
                self.operation_completed.emit(message, True)
        except Exception as e:
            self.operation_completed.emit(f"Error: {str(e)}", False)

class FileChunkerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Chunker")
        self.setGeometry(100, 100, 780, 560)
        self.setMinimumSize(520, 420)
        self.setWindowIcon(QIcon.fromTheme("document-open"))
        self.path_rows = []
        self.action_rows = []
        self.compact_layout = None
        self.theme_name = "light"
        
        # Central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(18, 16, 18, 14)
        self.main_layout.setSpacing(12)
        
        # App header
        self.add_header()
        
        # Create tabs
        self.tabs = QTabWidget()
        self.tabs.setUsesScrollButtons(True)
        self.tabs.setElideMode(Qt.ElideRight)
        self.main_layout.addWidget(self.tabs)
        
        # Add tabs
        self.create_split_tab()
        self.create_merge_tab()
        self.create_auto_tab()

        self.add_output_panel()
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_label = QLabel("Ready")
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(220)
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.status_label)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Set style
        self.set_style(self.theme_name)
        self.update_responsive_layout()
    
    def add_header(self):
        title = QLabel("File Chunker")
        title.setObjectName("HeaderTitle")
        title.setAlignment(Qt.AlignLeft)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel("Split and merge files with a clean, minimal interface.")
        subtitle.setObjectName("HeaderSubtitle")
        subtitle.setAlignment(Qt.AlignLeft)
        subtitle_font = QFont()
        subtitle_font.setPointSize(9)
        subtitle.setFont(subtitle_font)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        self.theme_select = QComboBox()
        self.theme_select.setObjectName("ThemeSelect")
        self.theme_select.addItems(["Light", "Dark"])
        self.theme_select.setFixedWidth(110)
        self.theme_select.currentTextChanged.connect(self.change_theme)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        header_layout.addLayout(title_layout, 1)
        header_layout.addWidget(QLabel("Theme:"))
        header_layout.addWidget(self.theme_select)

        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        self.main_layout.addWidget(header_widget)

    def add_output_panel(self):
        output_group = QGroupBox("Operation Output")
        output_layout = QVBoxLayout(output_group)
        output_layout.setSpacing(8)

        self.output_summary = QLabel("Completed split and merge details will appear here.")
        self.output_summary.setObjectName("OutputSummary")
        self.output_summary.setWordWrap(True)
        output_layout.addWidget(self.output_summary)

        self.output_details = QPlainTextEdit()
        self.output_details.setReadOnly(True)
        self.output_details.setPlaceholderText("No operation output yet.")
        self.output_details.setMinimumHeight(110)
        self.output_details.setMaximumHeight(190)
        self.output_details.setLineWrapMode(QPlainTextEdit.NoWrap)
        output_layout.addWidget(self.output_details)

        copy_row = QHBoxLayout()
        copy_row.addStretch(1)
        self.copy_output_btn = QPushButton("Copy Details")
        self.copy_output_btn.setObjectName("SecondaryButton")
        self.copy_output_btn.setEnabled(False)
        self.copy_output_btn.clicked.connect(self.copy_output_details)
        copy_row.addWidget(self.copy_output_btn)
        output_layout.addLayout(copy_row)

        self.main_layout.addWidget(output_group)

    def add_hint(self, layout, text):
        hint = QLabel(text)
        hint.setObjectName("HintLabel")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        return hint

    def add_path_row(self, layout, line_edit, button_text, callback, tooltip=None):
        row = QHBoxLayout()
        row.setSpacing(8)
        line_edit.setMinimumHeight(30)
        line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row.addWidget(line_edit, 1)

        button = QPushButton(button_text)
        button.setObjectName("SecondaryButton")
        button.setMinimumWidth(88)
        button.setMaximumWidth(112)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.clicked.connect(callback)
        if tooltip:
            button.setToolTip(tooltip)
        row.addWidget(button)

        layout.addLayout(row)
        self.path_rows.append((row, button))
        return button

    def add_action_row(self, layout, *buttons):
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        for button in buttons:
            button.setMinimumWidth(128)
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.action_rows.append((row, list(buttons)))
        layout.addWidget(container)
        self.rebuild_action_row(row, buttons, compact=False)

    def rebuild_action_row(self, row, buttons, compact):
        while row.count():
            item = row.takeAt(0)
            widget = item.widget()
            if widget:
                row.removeWidget(widget)

        if compact:
            row.setDirection(QHBoxLayout.TopToBottom)
            for button in buttons:
                button.setMaximumWidth(16777215)
                button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                row.addWidget(button)
        else:
            row.setDirection(QHBoxLayout.LeftToRight)
            row.addStretch()
            for button in buttons:
                button.setMaximumWidth(190)
                button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                row.addWidget(button)

    def add_responsive_tab(self, widget, title):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidget(widget)
        self.tabs.addTab(scroll_area, title)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_responsive_layout()

    def update_responsive_layout(self):
        compact = self.width() < 620
        if compact == self.compact_layout:
            return
        self.compact_layout = compact

        margins = (12, 10, 12, 10) if compact else (18, 16, 18, 14)
        self.main_layout.setContentsMargins(*margins)
        self.progress_bar.setMaximumWidth(150 if compact else 220)

        for row, button in self.path_rows:
            row.setDirection(QHBoxLayout.TopToBottom if compact else QHBoxLayout.LeftToRight)
            button.setMaximumWidth(16777215 if compact else 112)
            button.setSizePolicy(
                QSizePolicy.Expanding if compact else QSizePolicy.Fixed,
                QSizePolicy.Fixed
            )

        for row, buttons in self.action_rows:
            self.rebuild_action_row(row, buttons, compact)

    def change_theme(self, theme_text):
        self.theme_name = theme_text.lower()
        self.set_style(self.theme_name)

    def set_style(self, theme="light"):
        palettes = {
            "light": {
                "window": "#f4f6f8",
                "panel": "#ffffff",
                "panel_alt": "#f8fafc",
                "tab": "#eef2f7",
                "border": "#d8dee8",
                "border_soft": "#cfd8e6",
                "text": "#172033",
                "muted": "#687386",
                "button": "#2f6fed",
                "button_hover": "#245bd0",
                "secondary": "#edf2f8",
                "secondary_hover": "#e3eaf3",
                "accent": "#0f9f8f",
                "accent_hover": "#0b8578",
                "disabled": "#aab4c2",
                "progress_bg": "#e9eef5",
            },
            "dark": {
                "window": "#10141c",
                "panel": "#171c26",
                "panel_alt": "#121722",
                "tab": "#202736",
                "border": "#303847",
                "border_soft": "#3a4454",
                "text": "#edf2f7",
                "muted": "#a7b1c2",
                "button": "#4f8cff",
                "button_hover": "#3d76df",
                "secondary": "#252d3a",
                "secondary_hover": "#303949",
                "accent": "#18b7a7",
                "accent_hover": "#119c8f",
                "disabled": "#586273",
                "progress_bg": "#202736",
            },
        }
        c = palettes.get(theme, palettes["light"])
        css = """
            QMainWindow {
                background: $window;
            }
            QLabel#HeaderTitle {
                color: $text;
            }
            QLabel#HeaderSubtitle {
                color: $muted;
            }
            QLabel, QLabel#OutputSummary {
                color: $text;
            }
            QLabel#HintLabel {
                color: $muted;
                font-size: 9pt;
            }
            QTabWidget::pane {
                border: 1px solid $border;
                border-radius: 8px;
                background: $panel;
                top: -1px;
            }
            QWidget {
                background: $panel;
                color: $text;
            }
            QTabBar::tab {
                padding: 8px 14px;
                background: $tab;
                border: 1px solid $border;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                min-width: 92px;
                color: $muted;
            }
            QTabBar::tab:selected {
                background: $panel;
                color: $text;
                font-weight: 600;
            }
            QTabBar::tab:hover {
                background: $panel_alt;
            }
            QGroupBox {
                border: 1px solid $border;
                border-radius: 8px;
                margin-top: 10px;
                padding: 12px;
                background: $panel;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: $text;
                font-weight: 600;
                background: $panel;
            }
            QPushButton {
                padding: 6px 12px;
                background: $button;
                color: white;
                border: none;
                border-radius: 6px;
                min-height: 24px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: $button_hover;
            }
            QPushButton#SecondaryButton {
                background: $secondary;
                color: $text;
                border: 1px solid $border_soft;
                font-weight: 500;
            }
            QPushButton#SecondaryButton:hover {
                background: $secondary_hover;
                border-color: $border;
            }
            QPushButton#AccentButton {
                background: $accent;
            }
            QPushButton#AccentButton:hover {
                background: $accent_hover;
            }
            QPushButton:disabled {
                background: $disabled;
                color: $window;
            }
            QListWidget, QLineEdit, QSpinBox, QComboBox, QPlainTextEdit {
                border: 1px solid $border_soft;
                border-radius: 6px;
                background: $panel;
                padding: 6px 8px;
                color: $text;
                selection-background-color: $button;
            }
            QLineEdit:focus, QSpinBox:focus, QListWidget:focus, QComboBox:focus, QPlainTextEdit:focus {
                border: 1px solid $button;
            }
            QListWidget {
                background: $panel_alt;
                min-height: 100px;
            }
            QPlainTextEdit {
                background: $panel_alt;
                font-family: Consolas, Courier New, monospace;
                font-size: 9pt;
            }
            QCheckBox {
                color: $text;
                spacing: 8px;
            }
            QStatusBar {
                background: $window;
                color: $muted;
            }
            QProgressBar {
                border: 1px solid $border_soft;
                border-radius: 5px;
                height: 10px;
                background: $progress_bg;
                text-align: center;
            }
            QProgressBar::chunk {
                background: $accent;
                border-radius: 5px;
            }
        """
        # replace tokens with palette values
        for k, v in c.items():
            css = css.replace(f"${k}", v)
        self.setStyleSheet(css)
        
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)
    
    def create_split_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        
        # File selection
        file_group = QGroupBox("File to Split")
        file_layout = QVBoxLayout(file_group)
        
        self.split_file_path = QLineEdit()
        self.split_file_path.setPlaceholderText("Select a file to split...")
        self.split_file_path.setToolTip("Pick a single file to split into chunks.")
        self.add_path_row(
            file_layout,
            self.split_file_path,
            "Browse",
            self.browse_split_file,
            "Open a file browser to choose the file to split."
        )
        
        # Output directory
        output_dir_group = QGroupBox("Output Directory")
        output_dir_layout = QVBoxLayout(output_dir_group)
        
        self.split_output_dir = QLineEdit()
        self.split_output_dir.setPlaceholderText("(Optional) Select output directory...")
        self.add_path_row(
            output_dir_layout,
            self.split_output_dir,
            "Browse",
            lambda: self.browse_output_directory(self.split_output_dir)
        )
        
        # Chunk size
        chunk_group = QGroupBox("Split Settings")
        chunk_layout = QVBoxLayout(chunk_group)
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Chunk Size (MB):"))
        self.chunk_size = QSpinBox()
        self.chunk_size.setRange(1, 1000)
        self.chunk_size.setValue(CHUNK_SIZE // (1024 * 1024))
        size_layout.addWidget(self.chunk_size)
        size_layout.addStretch()
        chunk_layout.addLayout(size_layout)
        
        # Delete original checkbox
        self.delete_after_split = QCheckBox("Delete original file after splitting")
        chunk_layout.addWidget(self.delete_after_split)
        
        # Action button
        split_btn = QPushButton("Split File")
        split_btn.setObjectName("PrimaryButton")
        split_btn.clicked.connect(self.start_split)
        
        layout.addWidget(file_group)
        layout.addWidget(output_dir_group)
        layout.addWidget(chunk_group)
        self.add_action_row(layout, split_btn)
        layout.addStretch()
        
        self.add_responsive_tab(tab, "Split File")
    
    def create_merge_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        
        # Output file
        output_group = QGroupBox("Reconstructed File")
        output_layout = QVBoxLayout(output_group)
        
        self.merge_output_path = QLineEdit()
        self.merge_output_path.setPlaceholderText("Enter output file name or browse...")
        self.merge_output_path.setToolTip("Specify the destination file for the merged result.")
        self.add_path_row(
            output_layout,
            self.merge_output_path,
            "Browse",
            self.browse_output_file,
            "Choose the output file path for the merged file."
        )
        
        # Output directory
        merge_output_dir_group = QGroupBox("Optional Output Directory")
        merge_output_dir_layout = QVBoxLayout(merge_output_dir_group)
        
        self.merge_output_dir = QLineEdit()
        self.merge_output_dir.setPlaceholderText("(Optional) Select output directory...")
        self.add_path_row(
            merge_output_dir_layout,
            self.merge_output_dir,
            "Browse",
            lambda: self.browse_output_directory(self.merge_output_dir)
        )
        
        # Chunks list
        chunks_group = QGroupBox("Chunks to Merge")
        chunks_layout = QVBoxLayout(chunks_group)
        
        self.chunks_list = QListWidget()
        self.chunks_list.setSelectionMode(QListWidget.MultiSelection)
        self.chunks_list.setMinimumHeight(120)
        chunks_layout.addWidget(self.chunks_list)
        
        btn_row = QHBoxLayout()
        add_chunks_btn = QPushButton("Add Chunks...")
        add_chunks_btn.setObjectName("SecondaryButton")
        add_chunks_btn.setMinimumWidth(112)
        add_chunks_btn.setMaximumWidth(132)
        add_chunks_btn.clicked.connect(self.browse_chunks)
        add_chunks_btn.setToolTip("Select chunk files to include in the merge.")
        btn_row.addWidget(add_chunks_btn)

        clear_chunks_btn = QPushButton("Clear List")
        clear_chunks_btn.setObjectName("SecondaryButton")
        clear_chunks_btn.setMinimumWidth(88)
        clear_chunks_btn.setMaximumWidth(108)
        clear_chunks_btn.clicked.connect(self.clear_chunks)
        clear_chunks_btn.setToolTip("Remove all selected chunk paths from the list.")
        btn_row.addWidget(clear_chunks_btn)
        btn_row.addStretch()
        chunks_layout.addLayout(btn_row)
        
        # Delete chunks checkbox
        self.delete_after_merge = QCheckBox("Delete chunk files after merging")
        self.delete_after_merge.setToolTip("Remove chunk files after a successful merge.")
        chunks_layout.addWidget(self.delete_after_merge)
        
        # Action button
        merge_btn = QPushButton("Merge Files")
        merge_btn.setObjectName("PrimaryButton")
        merge_btn.clicked.connect(self.start_merge)
        
        layout.addWidget(output_group)
        layout.addWidget(merge_output_dir_group)
        layout.addWidget(chunks_group)
        self.add_action_row(layout, merge_btn)
        layout.addStretch()
        
        self.add_responsive_tab(tab, "Merge Files")
    
    def create_auto_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        
        # Directory selection
        dir_group = QGroupBox("Directory")
        dir_layout = QVBoxLayout(dir_group)
        
        self.auto_dir_path = QLineEdit()
        self.auto_dir_path.setPlaceholderText("Select a directory...")
        self.add_path_row(
            dir_layout,
            self.auto_dir_path,
            "Browse",
            self.browse_directory
        )
        
        # Output directory
        auto_output_dir_group = QGroupBox("Optional Output Directory")
        auto_output_dir_layout = QVBoxLayout(auto_output_dir_group)
        
        self.auto_output_dir = QLineEdit()
        self.auto_output_dir.setPlaceholderText("(Optional) Select output directory...")
        self.add_path_row(
            auto_output_dir_layout,
            self.auto_output_dir,
            "Browse",
            lambda: self.browse_output_directory(self.auto_output_dir)
        )
        
        # Chunk size for auto-split
        auto_chunk_group = QGroupBox("Auto Split Settings")
        auto_chunk_layout = QVBoxLayout(auto_chunk_group)
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Chunk Size (MB):"))
        self.auto_chunk_size = QSpinBox()
        self.auto_chunk_size.setRange(1, 1000)
        self.auto_chunk_size.setValue(CHUNK_SIZE // (1024 * 1024))
        size_layout.addWidget(self.auto_chunk_size)
        size_layout.addStretch()
        auto_chunk_layout.addLayout(size_layout)
        
        # Delete original checkbox
        self.auto_delete_after_split = QCheckBox("Delete original files after splitting")
        self.auto_delete_after_split.setToolTip("Remove original files automatically after chunking them.")
        auto_chunk_layout.addWidget(self.auto_delete_after_split)
        
        # Delete chunks checkbox
        self.auto_delete_after_merge = QCheckBox("Delete chunk files after merging")
        self.auto_delete_after_merge.setToolTip("Remove chunk files automatically after reconstructing the original file.")
        auto_chunk_layout.addWidget(self.auto_delete_after_merge)
        
        # Action buttons
        auto_split_btn = QPushButton("Auto Split Large Files")
        auto_split_btn.setObjectName("PrimaryButton")
        auto_split_btn.clicked.connect(self.start_auto_split)
        
        auto_merge_btn = QPushButton("Auto Merge Chunks")
        auto_merge_btn.setObjectName("AccentButton")
        auto_merge_btn.clicked.connect(self.start_auto_merge)
        
        layout.addWidget(dir_group)
        layout.addWidget(auto_output_dir_group)
        layout.addWidget(auto_chunk_group)
        self.add_action_row(layout, auto_split_btn, auto_merge_btn)
        layout.addStretch()
        
        self.add_responsive_tab(tab, "Auto Operations")
    
    def browse_split_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File to Split")
        if file_path:
            self.split_file_path.setText(file_path)
    
    def browse_chunks(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Select Chunk Files")
        if file_paths:
            self.chunks_list.clear()
            for path in sorted(file_paths):
                self.chunks_list.addItem(path)

    def browse_output_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Select Output File")
        if file_path:
            self.merge_output_path.setText(file_path)

    def clear_chunks(self):
        self.chunks_list.clear()
        self.update_status("Chunk list cleared.")
    
    def browse_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.auto_dir_path.setText(dir_path)
    
    def browse_output_directory(self, line_edit):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir_path:
            line_edit.setText(dir_path)
    
    def start_split(self):
        file_path = self.split_file_path.text()
        if not file_path:
            QMessageBox.warning(self, "Warning", "Please select a file to split.")
            return
        self.update_status("Preparing split operation...")
        
        chunk_size = self.chunk_size.value() * 1024 * 1024
        delete_original = self.delete_after_split.isChecked()
        output_dir = self.split_output_dir.text() or None
        
        self.worker = WorkerThread("split", file_path, chunk_size, delete_original, output_dir)
        self.set_worker_connections(self.worker)
        self.worker.start()
        self.show_progress(True)
    
    def start_merge(self):
        output_path = self.merge_output_path.text()
        if not output_path:
            QMessageBox.warning(self, "Warning", "Please enter an output file name.")
            return
        self.update_status("Preparing merge operation...")
        
        chunk_paths = [self.chunks_list.item(i).text() for i in range(self.chunks_list.count())]
        if not chunk_paths:
            QMessageBox.warning(self, "Warning", "Please add at least one chunk file.")
            return
        
        # Handle output directory
        output_dir = self.merge_output_dir.text()
        if output_dir:
            output_filename = os.path.basename(output_path)
            output_path = os.path.join(output_dir, output_filename)
        else:
            output_dir = os.path.dirname(os.path.abspath(output_path)) if os.path.dirname(output_path) else os.getcwd()
            output_path = os.path.join(output_dir, os.path.basename(output_path))
        
        delete_chunks = self.delete_after_merge.isChecked()
        
        try:
            self.worker = WorkerThread("merge", output_path, chunk_paths, delete_chunks)
            self.set_worker_connections(self.worker)
            self.worker.start()
            self.show_progress(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start merge: {str(e)}")
    
    def start_auto_split(self):
        dir_path = self.auto_dir_path.text()
        if not dir_path:
            QMessageBox.warning(self, "Warning", "Please select a directory.")
            return
        self.update_status("Preparing batch split...")
        
        chunk_size = self.auto_chunk_size.value() * 1024 * 1024
        delete_original = self.auto_delete_after_split.isChecked()
        output_dir = self.auto_output_dir.text() or None
        
        self.worker = WorkerThread("auto_split", dir_path, chunk_size, delete_original, output_dir)
        self.set_worker_connections(self.worker)
        self.worker.start()
        self.show_progress(True)
    
    def start_auto_merge(self):
        dir_path = self.auto_dir_path.text()
        if not dir_path:
            QMessageBox.warning(self, "Warning", "Please select a directory.")
            return
        self.update_status("Preparing batch merge...")
        
        delete_chunks = self.auto_delete_after_merge.isChecked()
        output_dir = self.auto_output_dir.text() or None
        
        self.worker = WorkerThread("auto_merge", dir_path, delete_chunks, output_dir)
        self.set_worker_connections(self.worker)
        self.worker.start()
        self.show_progress(True)
    
    def set_worker_connections(self, worker):
        worker.progress_updated.connect(self.update_progress)
        worker.operation_completed.connect(self.operation_finished)
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def operation_finished(self, message, success):
        self.show_progress(False)
        self.update_status("Done" if success else "Error")
        self.update_output_panel(message, success)
        if success:
            QMessageBox.information(self, "Success", "Operation completed successfully.")
        else:
            QMessageBox.critical(self, "Error", message)

    def update_output_panel(self, message: str, success: bool):
        if success:
            self.output_summary.setText("Operation completed successfully.")
        else:
            self.output_summary.setText("Operation failed. See details below.")
        self.output_details.setPlainText(message)
        self.copy_output_btn.setEnabled(bool(message.strip()))

    def copy_output_details(self):
        text = self.output_details.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Output details copied to clipboard.")

    def update_status(self, message: str):
        self.status_label.setText(message)
    
    def show_progress(self, show):
        self.progress_bar.setVisible(show)
        if show:
            self.progress_bar.setValue(0)
