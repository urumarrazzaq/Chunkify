import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QIcon
from ui import FileChunkerUI


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)

def main():
    app = QApplication(sys.argv)
    app_icon = QIcon(resource_path("favicon.ico"))
    app.setWindowIcon(app_icon)
    # Set application metadata
    app.setApplicationName("File Chunker")
    app.setApplicationVersion("1.1")
    app.setOrganizationName("File Utilities")
    
    window = FileChunkerUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

#pyinstaller --onefile --noconsole --icon=favicon.ico --add-data "favicon.ico;." main.py
