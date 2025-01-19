from PyQt5.QtWidgets import *

class HLine(QFrame):
    """A horizontal line"""
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(1)
        # self.setFixedHeight(20)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
    

class VLine(QFrame):
    """A vertical line"""
    def __init__(self, ducklings=None):
        super().__init__()
        # self.setFixedWidth(20)
        self.setMinimumHeight(1)
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)


    # def setGeometry(self, ax, ay, wx, wy):
    #     if self.reference is not None:
    #         reference_coords = self.reference.geometry().getCoords()
    #         print(reference_coords)

    #     super().setGeometry(ax, ay, wx, wy)

    

        
if __name__ == "__main__":
    import sys
    from circle_button import CircleButton

    app = QApplication(sys.argv)
    widget = QWidget()

    separator_vertical = VLine()
    separator_vertical.setParent(widget)
    separator_vertical.setGeometry(500, 70, 4, 40)
    # # separator_vertical.setGeometry(button.x(), button.y(), 2, 30)

    button = CircleButton(50, widget, ducklings=[separator_vertical])
    button.setParent(widget)
    button.setGeometry(10, 10, 50, 50)
    print(button.geometry().center())

    # separator_horizontal = HLine()
    # separator_horizontal.setParent(widget)
    # separator_horizontal.setGeometry(200, 40, 20, 2)

    widget.show()
    sys.exit(app.exec())