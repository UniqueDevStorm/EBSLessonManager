import sys
from PyQt5.QtWidgets import QApplication, QWidget, QDesktopWidget


class EBSLessonManager(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('EBS OnlineClass Manager')
        self.center()
        self.resize(1000, 700)
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


if __name__ == '__main__':
   app = QApplication(sys.argv)
   ex = EBSLessonManager()
   sys.exit(app.exec_())