import sys
import os
import subprocess
import shutil
import glob
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QWidget, QFileDialog, QLabel, QTextEdit, QMessageBox, QHBoxLayout)
from PySide6.QtCore import Qt

class OfuscadorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cython Obfuscator Pro")
        self.resize(700, 500)

        layout = QVBoxLayout()
        self.label = QLabel("Selecciona un archivo .py o una carpeta completa")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px;")
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

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

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
            # 1. Determinar directorio de trabajo
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
                if target.startswith("temp_setup") or target == "__init__.py": continue # No autocompilar el setup
                
                self.log.append(f"Procesando: {target}...")
                
                # 2. Setup temporal específico para CADA archivo (evita conflictos de rutas)
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

                # 3. Ejecutar compilación
                process = subprocess.run(
                    [sys.executable, setup_name],
                    capture_output=True, text=True, shell=True
                )

                # 4. Renombrar y Limpiar
                pyd_files = glob.glob(f"{target.replace('.py', '')}.cp*.pyd") + \
                            glob.glob(f"{target.replace('.py', '')}.cp*.so")
                
                if pyd_files:
                    full_pyd = pyd_files[0]
                    ext = ".pyd" if full_pyd.endswith(".pyd") else ".so"
                    final_name = target.replace(".py", ext)
                    
                    if os.path.exists(final_name): os.remove(final_name)
                    os.rename(full_pyd, final_name)
                    self.log.append(f"✅ Ofuscado: {final_name}")
                    encontrados += 1
                else:
                    self.log.append(f"❌ Error en {target}: {process.stderr}")

                # Limpieza inmediata de temporales del archivo
                if os.path.exists(setup_name): os.remove(setup_name)
                c_file = target.replace(".py", ".c")
                if os.path.exists(c_file): os.remove(c_file)

            # Limpieza de carpeta build
            if os.path.exists("build"): shutil.rmtree("build")

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
    window = OfuscadorApp()
    window.show()
    sys.exit(app.exec())