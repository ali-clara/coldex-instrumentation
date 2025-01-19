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

        self.button_up = QColor(255, 255, 0, 255)

        self.button_down = QColor(255, 0, 0, 255)

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
            super().mousePressEvent(event)

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
        rect = self.getButtonRect()
        if self.isDown() or self.isChecked():
            qp.setBrush(self.button_down)
            qp.drawEllipse(rect)
        else:
            qp.setBrush(self.button_up)
            qp.drawEllipse(rect)

def style_option_cast(obj, cls):
    """
    python version of qstyleoption_cast<target_type>(object)
    """
    try:
        if isinstance(obj, QStyleOption):
            if obj.version >= cls.Version:
                if (obj.type == cls.Type
                            or cls.Type == QStyleOption.SO_Default
                            or cls.Type == QStyleOption.SO_Complex and obj.type > QStyleOption.SO_Complex):
                    return sip.cast(obj, cls)
        elif isinstance(obj, QStyleHintReturn):
            if obj.version >= cls.Version:
                if (obj.type == cls.Type
                            or cls.Type == QStyleHintReturn.SH_Default):
                    return sip.cast(obj, cls)
    except TypeError:
        pass  # bad conversion (sibling type)
    return None


class MyStyle(QProxyStyle):
    def drawPrimitive(self, element, option, painter, widget=None):
        if element == QStyle.PE_PanelButtonCommand:
            button = style_option_cast(option, QStyleOptionButton)
            if button:
                isDown = (option.state & QStyle.State_Sunken) or (option.state & QStyle.State_On)
                isEnabled = option.state & QStyle.State_Enabled
                hasFocus = (option.state & QStyle.State_HasFocus) and (option.state & QStyle.State_KeyboardFocusChange)
                mouseover = option.state & QStyle.State_MouseOver
                pal = option.palette
                rect = option.rect.adjusted(0, 1, -1, 0)

                painter.setRenderHint(QPainter.Antialiasing, True)
                painter.translate(0.5, -0.5)

                outline = pal.window().color().darker(140)

                fill = QBrush(pal.button().color())
                if isDown:
                    fill = QBrush(pal.button().color().darker(110))

                # painter.setPen(Qt.transparent)
                painter.setBrush(fill)
                painter.drawEllipse(rect)
                # Outline
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(outline) if isEnabled else outline.lighter(115))
                painter.drawEllipse(rect)
                # Inline
                painter.setPen(QColor(255, 255, 255, 30))
                painter.drawEllipse(rect.adjusted(1, 1, -1, -1))
                return
        super().drawPrimitive(element, option, painter, widget)

def clicked():
    print("clicked!")

# testing
from PyQt5.QtWidgets import (
        QApplication,
        QPushButton)

qapp = QtWidgets.QApplication(sys.argv)
w = QWidget()

# myButton = QPushButton('Doing it\nwith 𝙌𝙋𝙧𝙤𝙭𝙮𝙎𝙩𝙮𝙡𝙚 !', w)
# myButton.setStyle(MyStyle('Fusion'))
# myButton.resize(300, 300)

myButton = CircleButton(50, w)
myButton.clicked.connect(clicked)

w.show()
qapp.exec_()
# Uncomment this if you hate corners...
# QApplication.setStyle(MyStyle('Fusion'))
