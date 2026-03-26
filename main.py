import sys
from PySide6.QtWidgets import QApplication
from app.file_manager import FileManager

def main():
    app = QApplication(sys.argv)
    window = FileManager()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()