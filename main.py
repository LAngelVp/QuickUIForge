import sys
import os
import subprocess
import shutil
import glob
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QWidget, QFileDialog, QLabel, QTextEdit, QMessageBox, 
                             QHBoxLayout, QTabWidget, QLineEdit, QCheckBox, 
                             QComboBox, QGroupBox, QSplitter, QTabWidget as QTabWidget2)
from PySide6.QtCore import Qt

class ConvertidorRecursos(QWidget):
    """Clase para convertir archivos .qrc a .py con soporte para PyQt6 y PySide6"""
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        # Título
        self.label = QLabel("Convertir archivos .qrc (recursos) a .py")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px;")
        layout.addWidget(self.label)
        
        # Grupo para seleccionar framework
        framework_group = QGroupBox("Seleccionar Framework")
        framework_layout = QVBoxLayout()
        
        self.framework_combo = QComboBox()
        self.framework_combo.addItems(["PySide6", "PyQt6"])
        self.framework_combo.setStyleSheet("padding: 5px;")
        framework_layout.addWidget(self.framework_combo)
        
        # Información de comandos
        self.info_label = QLabel("Comando a usar: pyside6-rcc")
        self.info_label.setStyleSheet("color: #3498db; font-size: 10px; margin-top: 5px;")
        framework_layout.addWidget(self.info_label)
        
        framework_group.setLayout(framework_layout)
        layout.addWidget(framework_group)
        
        # Conectar evento de cambio
        self.framework_combo.currentTextChanged.connect(self.on_framework_changed)
        
        # Botones de selección
        btns_layout = QHBoxLayout()
        self.btn_file = QPushButton("Seleccionar Archivo .qrc")
        self.btn_file.clicked.connect(self.select_qrc_file)
        btns_layout.addWidget(self.btn_file)
        
        self.btn_folder = QPushButton("Seleccionar Carpeta con .qrc")
        self.btn_folder.clicked.connect(self.select_qrc_folder)
        btns_layout.addWidget(self.btn_folder)
        layout.addLayout(btns_layout)
        
        # Ruta seleccionada
        self.ruta_label = QLabel("No se ha seleccionado ningún archivo")
        self.ruta_label.setStyleSheet("color: gray; margin: 5px;")
        layout.addWidget(self.ruta_label)
        
        # Opciones de conversión
        opciones_layout = QHBoxLayout()
        self.chk_recursivo = QCheckBox("Buscar recursivamente en subcarpetas")
        opciones_layout.addWidget(self.chk_recursivo)
        
        self.chk_sobrescribir = QCheckBox("Sobrescribir archivos existentes")
        self.chk_sobrescribir.setChecked(True)
        opciones_layout.addWidget(self.chk_sobrescribir)
        
        self.chk_compressed = QCheckBox("Comprimir recursos (--compress)")
        opciones_layout.addWidget(self.chk_compressed)
        layout.addLayout(opciones_layout)
        
        # Carpeta de salida
        output_layout = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Carpeta de salida (dejar vacío para misma carpeta)")
        output_layout.addWidget(self.output_path)
        
        self.btn_output = QPushButton("Seleccionar Carpeta")
        self.btn_output.clicked.connect(self.select_output_folder)
        output_layout.addWidget(self.btn_output)
        layout.addLayout(output_layout)
        
        # Log de resultados
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Consolas;")
        layout.addWidget(self.log)
        
        # Botón de convertir
        self.btn_convertir = QPushButton("Convertir .qrc a .py")
        self.btn_convertir.setEnabled(False)
        self.btn_convertir.clicked.connect(self.convertir_qrc)
        self.btn_convertir.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; height: 40px;")
        layout.addWidget(self.btn_convertir)
        
        self.setLayout(layout)
        
        # Variables
        self.qrc_path = ""
        self.is_file = False
        self.output_folder = ""
    
    def on_framework_changed(self, framework):
        """Actualizar información según framework seleccionado"""
        if framework == "PySide6":
            self.info_label.setText("Comando a usar: pyside6-rcc")
        else:  # PyQt6
            self.info_label.setText("Comando a usar: pyrcc6")
    
    def select_qrc_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Archivo .qrc", "", "Resource Files (*.qrc)")
        if file_path:
            self.qrc_path = os.path.abspath(file_path)
            self.is_file = True
            self.ruta_label.setText(f"Archivo: {os.path.basename(file_path)}")
            self.btn_convertir.setEnabled(True)
            self.log.append(f"✅ Archivo cargado: {self.qrc_path}")
    
    def select_qrc_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta con archivos .qrc")
        if folder:
            self.qrc_path = os.path.abspath(folder)
            self.is_file = False
            self.ruta_label.setText(f"Carpeta: {os.path.basename(folder)}")
            self.btn_convertir.setEnabled(True)
            self.log.append(f"✅ Carpeta cargada: {self.qrc_path}")
    
    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Salida")
        if folder:
            self.output_folder = os.path.abspath(folder)
            self.output_path.setText(self.output_folder)
            self.log.append(f"📁 Carpeta de salida: {self.output_folder}")
    
    def convertir_archivo_qrc(self, qrc_file, output_dir):
        """Convierte un solo archivo .qrc a .py usando el framework seleccionado"""
        try:
            nombre = os.path.splitext(os.path.basename(qrc_file))[0]
            output_file = os.path.join(output_dir, f"{nombre}_rc.py")
            
            # Verificar si ya existe
            if os.path.exists(output_file) and not self.chk_sobrescribir.isChecked():
                return False, f"⚠️ Archivo ya existe: {output_file}"
            
            framework = self.framework_combo.currentText()
            
            # Determinar el comando según el framework
            if framework == "PySide6":
                cmd = [sys.executable, "-m", "PySide6.scripts.rcc", qrc_file, "-o", output_file]
                if self.chk_compressed.isChecked():
                    cmd.insert(3, "--compress")
            else:  # PyQt6
                cmd = [sys.executable, "-m", "PyQt6.pyrcc", qrc_file, "-o", output_file]
                if self.chk_compressed.isChecked():
                    cmd.insert(3, "--compress")
            
            self.log.append(f"🔄 Ejecutando: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, f"✅ Convertido: {output_file}"
            else:
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                return False, f"❌ Error en {qrc_file}: {error_msg}"
                
        except Exception as e:
            return False, f"❌ Excepción en {qrc_file}: {str(e)}"
    
    def convertir_qrc(self):
        """Función principal de conversión de recursos"""
        if not self.qrc_path:
            QMessageBox.warning(self, "Error", "Selecciona un archivo o carpeta primero")
            return
        
        self.log.clear()
        framework = self.framework_combo.currentText()
        self.log.append(f"🚀 Iniciando conversión de recursos con {framework}...\n")
        
        # Verificar que el comando existe
        if framework == "PySide6":
            check_cmd = [sys.executable, "-c", "import PySide6.scripts.rcc"]
        else:
            check_cmd = [sys.executable, "-c", "import PyQt6.pyrcc"]
        
        try:
            subprocess.run(check_cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError:
            self.log.append(f"❌ Error: {framework} no está instalado correctamente")
            QMessageBox.critical(self, "Error", f"{framework} no está instalado o no se encuentra")
            return
        
        # Determinar directorio de salida
        if self.output_folder:
            output_dir = self.output_folder
        else:
            if self.is_file:
                output_dir = os.path.dirname(self.qrc_path)
            else:
                output_dir = self.qrc_path
        
        # Crear carpeta de salida si no existe
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Buscar archivos .qrc
        qrc_files = []
        if self.is_file:
            if self.qrc_path.endswith('.qrc'):
                qrc_files.append(self.qrc_path)
            else:
                self.log.append("❌ El archivo seleccionado no es .qrc")
                return
        else:
            if self.chk_recursivo.isChecked():
                for root, dirs, files in os.walk(self.qrc_path):
                    for file in files:
                        if file.endswith('.qrc'):
                            qrc_files.append(os.path.join(root, file))
            else:
                qrc_files = glob.glob(os.path.join(self.qrc_path, "*.qrc"))
        
        if not qrc_files:
            self.log.append("❌ No se encontraron archivos .qrc")
            return
        
        self.log.append(f"📝 Encontrados {len(qrc_files)} archivos .qrc\n")
        
        # Convertir cada archivo
        convertidos = 0
        errores = 0
        
        for qrc_file in qrc_files:
            # Mantener estructura de subcarpetas si es necesario
            if not self.is_file and self.output_folder and self.chk_recursivo.isChecked():
                rel_path = os.path.relpath(qrc_file, self.qrc_path)
                output_subdir = os.path.join(self.output_folder, os.path.dirname(rel_path))
                if not os.path.exists(output_subdir):
                    os.makedirs(output_subdir)
                output_actual = output_subdir
            else:
                output_actual = output_dir
            
            success, msg = self.convertir_archivo_qrc(qrc_file, output_actual)
            self.log.append(msg)
            
            if success:
                convertidos += 1
            else:
                errores += 1
        
        # Resumen final
        self.log.append(f"\n📊 RESULTADO FINAL:")
        self.log.append(f"   ✅ Convertidos: {convertidos}")
        self.log.append(f"   ❌ Errores: {errores}")
        self.log.append(f"   📁 Total procesados: {len(qrc_files)}")
        self.log.append(f"   🔧 Framework usado: {framework}")
        
        if convertidos > 0:
            QMessageBox.information(self, "Éxito", f"Se convirtieron {convertidos} archivos .qrc a .py usando {framework}")
        elif errores > 0:
            QMessageBox.warning(self, "Atención", f"Hubo {errores} errores. Revisa el log.")


class ConvertidorUI(QWidget):
    """Clase para convertir archivos .ui a .py con soporte para PyQt6 y PySide6"""
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        # Título
        self.label = QLabel("Convertir archivos .ui a .py")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px;")
        layout.addWidget(self.label)
        
        # Grupo para seleccionar framework
        framework_group = QGroupBox("Seleccionar Framework")
        framework_layout = QVBoxLayout()
        
        self.framework_combo = QComboBox()
        self.framework_combo.addItems(["PySide6", "PyQt6"])
        self.framework_combo.setStyleSheet("padding: 5px;")
        framework_layout.addWidget(self.framework_combo)
        
        # Información de comandos
        self.info_label = QLabel("Comando a usar: pyside6-uic")
        self.info_label.setStyleSheet("color: #3498db; font-size: 10px; margin-top: 5px;")
        framework_layout.addWidget(self.info_label)
        
        framework_group.setLayout(framework_layout)
        layout.addWidget(framework_group)
        
        # Conectar evento de cambio
        self.framework_combo.currentTextChanged.connect(self.on_framework_changed)
        
        # Botones de selección
        btns_layout = QHBoxLayout()
        self.btn_file = QPushButton("Seleccionar Archivo .ui")
        self.btn_file.clicked.connect(self.select_ui_file)
        btns_layout.addWidget(self.btn_file)
        
        self.btn_folder = QPushButton("Seleccionar Carpeta con .ui")
        self.btn_folder.clicked.connect(self.select_ui_folder)
        btns_layout.addWidget(self.btn_folder)
        layout.addLayout(btns_layout)
        
        # Ruta seleccionada
        self.ruta_label = QLabel("No se ha seleccionado ningún archivo")
        self.ruta_label.setStyleSheet("color: gray; margin: 5px;")
        layout.addWidget(self.ruta_label)
        
        # Opciones de conversión
        opciones_layout = QHBoxLayout()
        self.chk_recursivo = QCheckBox("Buscar recursivamente en subcarpetas")
        opciones_layout.addWidget(self.chk_recursivo)
        
        self.chk_sobrescribir = QCheckBox("Sobrescribir archivos existentes")
        self.chk_sobrescribir.setChecked(True)
        opciones_layout.addWidget(self.chk_sobrescribir)
        layout.addLayout(opciones_layout)
        
        # Carpeta de salida
        output_layout = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Carpeta de salida (dejar vacío para misma carpeta)")
        output_layout.addWidget(self.output_path)
        
        self.btn_output = QPushButton("Seleccionar Carpeta")
        self.btn_output.clicked.connect(self.select_output_folder)
        output_layout.addWidget(self.btn_output)
        layout.addLayout(output_layout)
        
        # Log de resultados
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Consolas;")
        layout.addWidget(self.log)
        
        # Botón de convertir
        self.btn_convertir = QPushButton("Convertir .ui a .py")
        self.btn_convertir.setEnabled(False)
        self.btn_convertir.clicked.connect(self.convertir_ui)
        self.btn_convertir.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; height: 40px;")
        layout.addWidget(self.btn_convertir)
        
        self.setLayout(layout)
        
        # Variables
        self.ui_path = ""
        self.is_file = False
        self.output_folder = ""
    
    def on_framework_changed(self, framework):
        """Actualizar información según framework seleccionado"""
        if framework == "PySide6":
            self.info_label.setText("Comando a usar: pyside6-uic")
        else:  # PyQt6
            self.info_label.setText("Comando a usar: pyuic6")
    
    def select_ui_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Archivo .ui", "", "UI Files (*.ui)")
        if file_path:
            self.ui_path = os.path.abspath(file_path)
            self.is_file = True
            self.ruta_label.setText(f"Archivo: {os.path.basename(file_path)}")
            self.btn_convertir.setEnabled(True)
            self.log.append(f"✅ Archivo cargado: {self.ui_path}")
    
    def select_ui_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta con archivos .ui")
        if folder:
            self.ui_path = os.path.abspath(folder)
            self.is_file = False
            self.ruta_label.setText(f"Carpeta: {os.path.basename(folder)}")
            self.btn_convertir.setEnabled(True)
            self.log.append(f"✅ Carpeta cargada: {self.ui_path}")
    
    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Salida")
        if folder:
            self.output_folder = os.path.abspath(folder)
            self.output_path.setText(self.output_folder)
            self.log.append(f"📁 Carpeta de salida: {self.output_folder}")
    
    def convertir_archivo_ui(self, ui_file, output_dir):
        """Convierte un solo archivo .ui a .py usando el framework seleccionado"""
        try:
            nombre = os.path.splitext(os.path.basename(ui_file))[0]
            output_file = os.path.join(output_dir, f"{nombre}.py")
            
            # Verificar si ya existe
            if os.path.exists(output_file) and not self.chk_sobrescribir.isChecked():
                return False, f"⚠️ Archivo ya existe: {output_file}"
            
            framework = self.framework_combo.currentText()
            
            # Determinar el comando según el framework
            if framework == "PySide6":
                cmd = [sys.executable, "-m", "PySide6.scripts.uic", ui_file, "-o", output_file]
            else:  # PyQt6
                cmd = [sys.executable, "-m", "PyQt6.uic.pyuic", ui_file, "-o", output_file]
            
            self.log.append(f"🔄 Ejecutando: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, f"✅ Convertido: {output_file}"
            else:
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                return False, f"❌ Error en {ui_file}: {error_msg}"
                
        except Exception as e:
            return False, f"❌ Excepción en {ui_file}: {str(e)}"
    
    def convertir_ui(self):
        """Función principal de conversión de UI"""
        if not self.ui_path:
            QMessageBox.warning(self, "Error", "Selecciona un archivo o carpeta primero")
            return
        
        self.log.clear()
        framework = self.framework_combo.currentText()
        self.log.append(f"🚀 Iniciando conversión de UI con {framework}...\n")
        
        # Verificar que el comando existe
        if framework == "PySide6":
            check_cmd = [sys.executable, "-c", "import PySide6.scripts.uic"]
        else:
            check_cmd = [sys.executable, "-c", "import PyQt6.uic.pyuic"]
        
        try:
            subprocess.run(check_cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError:
            self.log.append(f"❌ Error: {framework} no está instalado correctamente")
            QMessageBox.critical(self, "Error", f"{framework} no está instalado o no se encuentra")
            return
        
        # Determinar directorio de salida
        if self.output_folder:
            output_dir = self.output_folder
        else:
            if self.is_file:
                output_dir = os.path.dirname(self.ui_path)
            else:
                output_dir = self.ui_path
        
        # Crear carpeta de salida si no existe
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Buscar archivos .ui
        ui_files = []
        if self.is_file:
            if self.ui_path.endswith('.ui'):
                ui_files.append(self.ui_path)
            else:
                self.log.append("❌ El archivo seleccionado no es .ui")
                return
        else:
            if self.chk_recursivo.isChecked():
                for root, dirs, files in os.walk(self.ui_path):
                    for file in files:
                        if file.endswith('.ui'):
                            ui_files.append(os.path.join(root, file))
            else:
                ui_files = glob.glob(os.path.join(self.ui_path, "*.ui"))
        
        if not ui_files:
            self.log.append("❌ No se encontraron archivos .ui")
            return
        
        self.log.append(f"📝 Encontrados {len(ui_files)} archivos .ui\n")
        
        # Convertir cada archivo
        convertidos = 0
        errores = 0
        
        for ui_file in ui_files:
            # Mantener estructura de subcarpetas si es necesario
            if not self.is_file and self.output_folder and self.chk_recursivo.isChecked():
                rel_path = os.path.relpath(ui_file, self.ui_path)
                output_subdir = os.path.join(self.output_folder, os.path.dirname(rel_path))
                if not os.path.exists(output_subdir):
                    os.makedirs(output_subdir)
                output_actual = output_subdir
            else:
                output_actual = output_dir
            
            success, msg = self.convertir_archivo_ui(ui_file, output_actual)
            self.log.append(msg)
            
            if success:
                convertidos += 1
            else:
                errores += 1
        
        # Resumen final
        self.log.append(f"\n📊 RESULTADO FINAL:")
        self.log.append(f"   ✅ Convertidos: {convertidos}")
        self.log.append(f"   ❌ Errores: {errores}")
        self.log.append(f"   📁 Total procesados: {len(ui_files)}")
        self.log.append(f"   🔧 Framework usado: {framework}")
        
        if convertidos > 0:
            QMessageBox.information(self, "Éxito", f"Se convirtieron {convertidos} archivos .ui a .py usando {framework}")
        elif errores > 0:
            QMessageBox.warning(self, "Atención", f"Hubo {errores} errores. Revisa el log.")


class MainApp(QMainWindow):
    """Clase principal con pestañas para todas las herramientas"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CelerisRMPG - Suite de Herramientas")
        self.resize(900, 700)
        
        # Crear widget con pestañas
        tabs = QTabWidget()
        
        # Pestaña 1: Ofuscador
        self.ofuscador = OfuscadorApp()
        tabs.addTab(self.ofuscador, "🔒 Cython Obfuscator")
        
        # Pestaña 2: Convertidor UI
        self.convertidor_ui = ConvertidorUI()
        tabs.addTab(self.convertidor_ui, "🎨 UI to Python")
        
        # Pestaña 3: Convertidor Recursos
        self.convertidor_qrc = ConvertidorRecursos()
        tabs.addTab(self.convertidor_qrc, "📦 Resources (QRC)")
        
        # Configurar ventana principal
        self.setCentralWidget(tabs)
        
        # Estilo mejorado
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QTabWidget::pane {
                border: 1px solid #444;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #fff;
                padding: 8px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #4a4a4a;
                border-bottom: 2px solid #27ae60;
            }
            QTabBar::tab:hover {
                background-color: #505050;
            }
            QGroupBox {
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #fff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QComboBox {
                background-color: #3c3c3c;
                color: #fff;
                border: 1px solid #555;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                color: #fff;
                selection-background-color: #27ae60;
            }
            QCheckBox {
                color: #fff;
            }
            QLabel {
                color: #fff;
            }
        """)


class OfuscadorApp(QWidget):
    """Versión del ofuscador como widget (para integrar en pestañas)"""
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        self.label = QLabel("Selecciona un archivo .py o una carpeta completa")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px; color: #fff;")
        layout.addWidget(self.label)

        btns_layout = QHBoxLayout()
        self.btn_file = QPushButton("Seleccionar Archivo")
        self.btn_file.clicked.connect(self.select_file)
        btns_layout.addWidget(self.btn_file)

        self.btn_folder = QPushButton("Seleccionar Carpeta")
        self.btn_folder.clicked.connect(self.select_folder)
        btns_layout.addWidget(self.btn_folder)
        layout.addLayout(btns_layout)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Consolas;")
        layout.addWidget(self.log)

        self.btn_run = QPushButton("Compilar y Ofuscar")
        self.btn_run.setEnabled(False)
        self.btn_run.clicked.connect(self.run_obfuscation)
        self.btn_run.setStyleSheet("background-color: #2c3e50; color: white; font-weight: bold; height: 40px;")
        layout.addWidget(self.btn_run)

        self.setLayout(layout)
        
        self.path_selected = ""
        self.is_file = False

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Archivo Python", "", "Python Files (*.py)")
        if file_path:
            self.path_selected = os.path.abspath(file_path)
            self.is_file = True
            self.label.setText(f"Archivo: {os.path.basename(file_path)}")
            self.btn_run.setEnabled(True)
            self.log.append(f"Archivo cargado: {self.path_selected}")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Proyecto")
        if folder:
            self.path_selected = os.path.abspath(folder)
            self.is_file = False
            self.label.setText(f"Carpeta: {os.path.basename(folder)}")
            self.btn_run.setEnabled(True)
            self.log.append(f"Directorio cargado: {self.path_selected}")

    def run_obfuscation(self):
        original_cwd = os.getcwd()
        try:
            if self.is_file:
                working_dir = os.path.dirname(self.path_selected)
                files_to_compile = [os.path.basename(self.path_selected)]
            else:
                working_dir = self.path_selected
                files_to_compile = [os.path.basename(f) for f in glob.glob(os.path.join(working_dir, "*.py")) if not os.path.basename(f).startswith("__")]

            os.chdir(working_dir)
            self.log.append(f"\n--- Trabajando en: {working_dir} ---")

            encontrados = 0
            for target in files_to_compile:
                if target.startswith("temp_setup") or target == "__init__.py": 
                    continue
                
                self.log.append(f"Procesando: {target}...")
                
                setup_name = f"temp_setup_{target.replace('.py', '')}.py"
                setup_content = f"""
from setuptools import setup, Extension
from Cython.Build import cythonize
import os

setup(
    ext_modules=cythonize(
        Extension("{target.replace('.py', '')}", ["{target}"]),
        language_level="3",
        compiler_directives={{'always_allow_keywords': True}}
    ),
    script_args=["build_ext", "--inplace"]
)
"""
                with open(setup_name, "w", encoding="utf-8") as f:
                    f.write(setup_content)

                process = subprocess.run(
                    [sys.executable, setup_name],
                    capture_output=True, text=True, shell=True
                )

                pyd_files = glob.glob(f"{target.replace('.py', '')}.cp*.pyd") + \
                            glob.glob(f"{target.replace('.py', '')}.cp*.so")
                
                if pyd_files:
                    full_pyd = pyd_files[0]
                    ext = ".pyd" if full_pyd.endswith(".pyd") else ".so"
                    final_name = target.replace(".py", ext)
                    
                    if os.path.exists(final_name): 
                        os.remove(final_name)
                    os.rename(full_pyd, final_name)
                    self.log.append(f"✅ Ofuscado: {final_name}")
                    encontrados += 1
                else:
                    self.log.append(f"❌ Error en {target}: {process.stderr}")

                if os.path.exists(setup_name): 
                    os.remove(setup_name)
                c_file = target.replace(".py", ".c")
                if os.path.exists(c_file): 
                    os.remove(c_file)

            if os.path.exists("build"): 
                shutil.rmtree("build")

            if encontrados > 0:
                QMessageBox.information(self, "Éxito", f"Se generaron {encontrados} módulos ofuscados.")
            else:
                QMessageBox.warning(self, "Atención", "No se generaron archivos. Revisa el log.")

        except Exception as e:
            self.log.append(f"❌ ERROR CRÍTICO: {str(e)}")
            QMessageBox.critical(self, "Error", str(e))
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())