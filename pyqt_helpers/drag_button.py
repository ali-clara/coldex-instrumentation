from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import sys

class DragButton(QPushButton):

    def __init__(self, name, window):
        self.mybutton = super()
        self.mybutton.__init__(name, window)

        self.button_locked = False
        self._mouse_press_pos = None
        self._mouse_move_pos = None

        self.setStyleSheet("background-color: lightgrey")

    def lock_button(self):
        self.button_locked = True

    def unlock_button(self):
        self.button_locked = False

    def mousePressEvent(self, event:QMouseEvent):
        """Overwrites the default mouse click callback. Every time we click the mouse, record the position"""
        self.__mousePressPos = event.globalPos()
        self.__mouseMovePos = event.globalPos()
        self.mybutton.mousePressEvent(event)
        self.setStyleSheet("background-color: lightblue")

    def mouseMoveEvent(self, event:QMouseEvent):
        if self.button_locked == False:
            
            self.setStyleSheet("background-color: lightgrey")

            # adjust offset from clicked point to origin of widget
            currPos = self.mapToGlobal(self.pos())
            globalPos = event.globalPos()
            diff = globalPos - self.__mouseMovePos
            newPos = self.mapFromGlobal(currPos + diff)
            self.move(newPos)

            self.__mouseMovePos = globalPos

        # Trigger the original mouseReleaseEvent callback
        self.mybutton.mouseMoveEvent(event)

    def mouseReleaseEvent(self, event:QMouseEvent):
        self.setStyleSheet("background-color: lightgrey")
        moved = event.globalPos() - self.__mousePressPos 
        move_threshold = 3
        if moved.manhattanLength() > move_threshold:
            event.ignore()
        else:
            self.mybutton.mouseReleaseEvent(event)


if __name__ == "__main__":

    def clicked():
        print("click as normal!")

    qapp = QtWidgets.QApplication(sys.argv)
    w = QWidget()
    w.resize(800,600)

    button = DragButton("Drag", w)
    button.clicked.connect(clicked)

    w.show()
    qapp.exec_()