from PyQt5.QtWidgets import *

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
    def __init__(self, ducklings=None):
        super().__init__()
        self.setMinimumWidth(20)
        self.setFrameShape(QFrame.VLine)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

        
if __name__ == "__main__":
    import sys
    from circle_button import CircleButton
    import yaml

    with open("config/button_locs.yaml", "r") as stream:
        button_locs = yaml.load(stream)

    app = QApplication(sys.argv)
    widget = QWidget()

    separator_vertical = VLine()
    separator_vertical.setParent(widget)
    separator_vertical.setGeometry(500, 70, 4, 60)

    button = CircleButton(50, widget, ducklings=[separator_vertical])
    button.setParent(widget)
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