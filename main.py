import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    font = QFont('Microsoft YaHei', 9)
    app.setFont(font)

    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
