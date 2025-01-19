from PyQt5 import QtWidgets, QtCore, sip
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import sys

class CircleButton(QtWidgets.QPushButton):
    def __init__(self, radius=None, parent=None):
        super().__init__(parent)
        if radius is None:
            radius = self.font().pointSize() * 2
        self.setRadius(radius)

        # use the palette as source for the colors
        # palette = self.palette()
        # light = palette.color(palette.Light)
        # # midlight = palette.color(palette.Midlight)
        # mid = palette.color(palette.Mid)
        # dark = palette.color(palette.Dark)

        # print(light.getRgb())
        # # print(midlight.getRgb())
        # print(mid.getRgb())
        # print(dark.getRgb())

        self.button_open = False

        ### ----- colors ----- ###
        closed_light = QColor(247, 217, 126, 255)
        closed_mid = QColor(255, 193, 7, 255)
        closed_dark = QColor(214, 165, 18, 255)

        open_light = QColor(249, 149, 148)
        open_mid = QColor(241, 108, 107, 255)
        open_dark = QColor(216, 27, 96, 255)

        self.closed_color_gradients = self.create_color_gradients(closed_light, closed_mid, closed_dark)
        self.open_color_gradients = self.create_color_gradients(open_light, open_mid, open_dark)

        ### ----- movement ----- ###
        self._mouse_press_pos = None
        self._mouse_move_pos = None
        self.button_locked = False

    
    def create_color_gradients(self, light:QColor, mid:QColor, dark:QColor):
        """A method to create nice gradients between the selected colors to make the button look like
        a 3D object. Graphic deign go!

        It's not as scary as it looks, but it's still pretty magical. I don't fully know how it works, sourced from 
        https://www.riverbankcomputing.com/pipermail/pyqt/2020-March/042586.html

        Args:
            light (QColor): _description_
            mid (QColor): _description_
            dark (QColor): _description_

        Returns:
            _type_: _description_
        """
        # a radial gradient for the "shadow effect" when button is unpressed
        backgroundUp = QConicalGradient(.5, .5, 135)

        backgroundUp.setCoordinateMode(backgroundUp.ObjectBoundingMode)
        backgroundUp.setStops([
            (0.0, light),
            (0.3, dark),
            (0.6, dark),
            (1.0, light),
        ])

        # the same as above, but inverted for pressed state
        backgroundDown = QConicalGradient(.5, .5, 315)

        backgroundDown.setCoordinateMode(backgroundDown.ObjectBoundingMode)
        backgroundDown.setStops(backgroundUp.stops())

        # a "mask" for the conical gradient
        ringShapeDown = QRadialGradient(.5, .5, .5)

        ringShapeDown.setCoordinateMode(ringShapeDown.ObjectBoundingMode)
        ringShapeDown.setStops([
            (0.7536231884057971, mid),
            (0.7960662525879917, QtCore.Qt.transparent),
        ])

        ringShapeUp = QRadialGradient(.5, .5, .5)

        ringShapeUp.setCoordinateMode(ringShapeUp.ObjectBoundingMode)
        ringShapeUp.setStops([
            (0.7536231884057971, mid),
            (0.7960662525879917, QtCore.Qt.transparent),
            (0.9627329192546584, QtCore.Qt.transparent),
        ])

        return backgroundUp, backgroundDown, ringShapeUp, ringShapeDown
    
    def change_button_state(self):
        if self.button_open == False:
            self.button_open = True
        else:
            self.button_open = False
    
    def getButtonRect(self):
        # just a helper function to avoid repetitions
        size = min(self.width(), self.height()) - 1
        rect = QtCore.QRect(0, 0, size, size)
        rect.moveCenter(self.rect().center())
        return rect

    def mousePressEvent(self, event):
        # ensure that the click happens within the circle
        path = QPainterPath()
        path.addEllipse(QtCore.QRectF(self.getButtonRect()))
        if path.contains(event.pos()):
            # Record the position where we clicked
            self.__mousePressPos = event.globalPos()
            self.__mouseMovePos = event.globalPos()
            # Call the parent class method
            super().mousePressEvent(event)
            # Change colors
            self.change_button_state()

    def setRadius(self, radius):
        self.radius = radius
        # notify the layout manager that the size hint has changed
        self.updateGeometry()

    def sizeHint(self):
        return QtCore.QSize(self.radius, self.radius)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return width

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHints(qp.Antialiasing)
        qp.translate(.5, .5)
        qp.setPen(QtCore.Qt.NoPen)
        rect = self.getButtonRect()
        if self.isDown() or self.isChecked():
            if self.button_open:
                qp.setBrush(self.open_color_gradients[1])
                qp.drawEllipse(rect)
                qp.setBrush(self.open_color_gradients[3])
                qp.drawEllipse(rect)
            else:
                qp.setBrush(self.closed_color_gradients[1])
                qp.drawEllipse(rect)
                qp.setBrush(self.closed_color_gradients[3])
                qp.drawEllipse(rect)
        else:
            if self.button_open:
                qp.setBrush(self.open_color_gradients[0])
                qp.drawEllipse(rect)
                qp.setBrush(self.open_color_gradients[2])
                qp.drawEllipse(rect)
            else:
                qp.setBrush(self.closed_color_gradients[0])
                qp.drawEllipse(rect)
                qp.setBrush(self.closed_color_gradients[2])
                qp.drawEllipse(rect)


    def mouseMoveEvent(self, event:QMouseEvent):
        if self.button_locked == False:
            
            self.setStyleSheet("background-color: lightgrey")

            # adjust offset from clicked point to origin of widget
            currPos = self.mapToGlobal(self.pos())
            globalPos = event.globalPos()
            diff = globalPos - self.__mouseMovePos
            newPos = self.mapFromGlobal(currPos + diff)
            # Should constrain the button to the size of the window
            self.move(newPos)

            self.__mouseMovePos = globalPos

        # Trigger the original mouseReleaseEvent callback
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event:QMouseEvent):
        self.setStyleSheet("background-color: lightgrey")
        moved = event.globalPos() - self.__mousePressPos 
        move_threshold = 3
        if moved.manhattanLength() > move_threshold:
            self.change_button_state()
            event.ignore()
        else:
            super().mouseReleaseEvent(event)


if __name__ == "__main__":
    
    def clicked():
        print("clicked!")

    qapp = QtWidgets.QApplication(sys.argv)
    w = QWidget()
    w.setMinimumSize(100, 100)

    myButton = CircleButton(50, w)
    myButton.clicked.connect(clicked)

    w.show()
    qapp.exec_()