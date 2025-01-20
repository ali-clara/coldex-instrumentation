from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class HLine(QFrame):
    """A horizontal line"""
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(10)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
    

class VLine(QFrame):
    """A vertical line"""
    def __init__(self, parent=None, baseline=None, ducklings=None):
        super().__init__(parent)
        self.setMinimumWidth(20)
        self.setFrameShape(QFrame.VLine)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

        print(self.parent())
        print(self.parentWidget().geometry().size())

        if baseline is None:
            baseline = int(self.parentWidget().geometry().height() / 2)
        self.baseline_position = baseline

    def baseline(self):
        return self.baseline_position
    
    def setBaseline(self, baseline):
        self.baseline_position = baseline
    
        
if __name__ == "__main__":
    import sys
    from circle_button import CircleButton
    import yaml

    with open("config/button_locs.yaml", "r") as stream:
        button_locs = yaml.load(stream)

    app = QApplication(sys.argv)
    widget = QWidget()

    separator_vertical = VLine(widget)
    separator_vertical.setGeometry(500, 70, 4, 60)

    print(widget.geometry().size())

    button = CircleButton(50, widget, ducklings=[separator_vertical])
    button.move(button_locs["button 1"]["x"], button_locs["button 1"]["y"])
    print(button.geometry().center())

    widget.show()
    app.exec()

    button_loc_dic = {}
    button_loc_dic.update({"button 1": {"x":button.geometry().center().x(), "y":button.geometry().center().y()}})
    print(button_loc_dic)
    with open("config/button_locs.yaml", "w") as yaml_file:
        dump = yaml.safe_dump(button_loc_dic)
        yaml_file.write(dump)