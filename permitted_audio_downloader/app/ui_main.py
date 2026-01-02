from PySide6 import QtCore, QtGui, QtWidgets


class UiMainWindow:
    def setup_ui(self, main_window: QtWidgets.QMainWindow) -> None:
        main_window.setWindowTitle("PermittedAudioDownloader")
        main_window.resize(900, 700)

        central_widget = QtWidgets.QWidget(main_window)
        main_layout = QtWidgets.QVBoxLayout(central_widget)

        warning_label = QtWidgets.QLabel(
            "Use apenas links com permissão do autor / fontes permitidas.")
        warning_label.setStyleSheet("color: #b00020; font-weight: bold;")
        main_layout.addWidget(warning_label)

        url_layout = QtWidgets.QHBoxLayout()
        self.url_input = QtWidgets.QLineEdit()
        self.url_input.setPlaceholderText("Cole a URL de YouTube ou SoundCloud")
        self.add_button = QtWidgets.QPushButton("Adicionar à fila")
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.add_button)
        main_layout.addLayout(url_layout)

        folder_layout = QtWidgets.QHBoxLayout()
        self.output_dir_input = QtWidgets.QLineEdit()
        self.output_dir_button = QtWidgets.QPushButton("Escolher pasta")
        folder_layout.addWidget(QtWidgets.QLabel("Pasta de saída:"))
        folder_layout.addWidget(self.output_dir_input)
        folder_layout.addWidget(self.output_dir_button)
        main_layout.addLayout(folder_layout)

        options_layout = QtWidgets.QHBoxLayout()
        self.preserve_name_checkbox = QtWidgets.QCheckBox("Preservar nome original")
        self.overwrite_checkbox = QtWidgets.QCheckBox("Sobrescrever se existir")
        self.sample_rate_combo = QtWidgets.QComboBox()
        self.sample_rate_combo.addItems(["44100", "48000"])
        options_layout.addWidget(self.preserve_name_checkbox)
        options_layout.addWidget(self.overwrite_checkbox)
        options_layout.addWidget(QtWidgets.QLabel("Sample rate:"))
        options_layout.addWidget(self.sample_rate_combo)
        options_layout.addStretch()
        main_layout.addLayout(options_layout)

        self.table = QtWidgets.QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Status", "Título", "Fonte", "Progresso", "Saída"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        main_layout.addWidget(self.table)

        buttons_layout = QtWidgets.QHBoxLayout()
        self.download_button = QtWidgets.QPushButton("Baixar")
        self.pause_button = QtWidgets.QPushButton("Pausar")
        self.cancel_button = QtWidgets.QPushButton("Cancelar item")
        self.clear_button = QtWidgets.QPushButton("Limpar concluídos")
        buttons_layout.addWidget(self.download_button)
        buttons_layout.addWidget(self.pause_button)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)

        logs_layout = QtWidgets.QVBoxLayout()
        logs_header = QtWidgets.QHBoxLayout()
        logs_header.addWidget(QtWidgets.QLabel("Logs"))
        self.copy_logs_button = QtWidgets.QPushButton("Copiar logs")
        logs_header.addStretch()
        logs_header.addWidget(self.copy_logs_button)
        logs_layout.addLayout(logs_header)
        self.logs_text = QtWidgets.QPlainTextEdit()
        self.logs_text.setReadOnly(True)
        logs_layout.addWidget(self.logs_text)
        main_layout.addLayout(logs_layout)

        main_window.setCentralWidget(central_widget)
