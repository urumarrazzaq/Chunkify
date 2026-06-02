import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QIcon
from ui import FileChunkerUI

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("favicon.ico"))
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
