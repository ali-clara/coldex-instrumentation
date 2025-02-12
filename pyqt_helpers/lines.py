from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class HLine(QFrame):
    """A horizontal line"""
    def __init__(self, parent, start_x=0, baseline=None, thickness=20):
        super().__init__(parent)
        self.setMinimumHeight(thickness)
        self.setMidLineWidth(thickness)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Raised)

        parent_width = self.parentWidget().geometry().width()
        parent_height = self.parentWidget().geometry().height()

        # make sure the line shows up at the beginning by seeding it with a geometry
        if start_x > baseline:
            self.setGeometry(0,0,0,0)
        else:
            self.setGeometry(parent_width, parent_height, 0, 0)

        if baseline is None:
            baseline = int(parent_width / 2)
        self.setBaseline(baseline)

        # Movement params
        self.line_locked = True
        self._mouse_press_pos = None
        self._mouse_move_pos = None

    def baseline(self):
        return self.baseline_position
    
    def setBaseline(self, baseline):
        self.baseline_position = baseline

    def mousePressEvent(self, event:QMouseEvent):
        """Overwrites the default mouse click callback. Every time we click the mouse, record the position"""
        self._mouse_press_pos = event.globalPos()
        self._mouse_move_pos = event.globalPos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event:QMouseEvent):
        """Overwrites the QPushButton mouseMoveEvent method. Records the position of the mouse movement, finds the difference
        between that position and the button, and moves the button
        """
        # If we're allowing the line to move...
        if self.line_locked == False:
            # Adjust offset from clicked point to origin of widget
            currPos = self.mapToGlobal(self.pos())
            globalPos = event.globalPos()
            diff = globalPos - self._mouse_move_pos
            newPos = self.mapFromGlobal(currPos + diff)
            # Move and record
            super().move(newPos)
            self._mouse_move_pos = globalPos
    
class VLine(QFrame):
    """A vertical line"""
    def __init__(self, parent, start_y=0, baseline=None, thickness=20):
        super().__init__(parent)
        self.setMinimumWidth(thickness)
        self.setMidLineWidth(thickness)
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Raised)
        
        parent_height = self.parentWidget().geometry().height()
        parent_width = self.parentWidget().geometry().width()
        if baseline is None:
            baseline = int(parent_height / 2)
        self.setBaseline(baseline)

        # make sure the line shows up at the beginning by seeding it with a geometry
        if start_y > baseline:
            self.setGeometry(0,0,0,0)
        else:
            self.setGeometry(parent_width, parent_height, 0, 0)

        # Movement params
        self.line_locked = True
        self._mouse_press_pos = None
        self._mouse_move_pos = None
    
    def baseline(self):
        return self.baseline_position
    
    def setBaseline(self, baseline):
        self.baseline_position = baseline

    def mousePressEvent(self, event:QMouseEvent):
        """Overwrites the default mouse click callback. Every time we click the mouse, record the position"""
        self._mouse_press_pos = event.globalPos()
        self._mouse_move_pos = event.globalPos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event:QMouseEvent):
        """Overwrites the QPushButton mouseMoveEvent method. Records the position of the mouse movement, finds the difference
        between that position and the button, and moves the button
        """
        # If we're allowing the line to move...
        if self.line_locked == False:
            # Adjust offset from clicked point to origin of widget
            currPos = self.mapToGlobal(self.pos())
            globalPos = event.globalPos()
            diff = globalPos - self._mouse_move_pos
            newPos = self.mapFromGlobal(currPos + diff)
            # Move and record
            super().move(newPos)
            self._mouse_move_pos = globalPos
    
        
if __name__ == "__main__":
    import sys
    from circle_button import CircleButton
    import yaml

    with open("config/button_locs.yaml", "r") as stream:
        button_locs = yaml.safe_load(stream)

    app = QApplication(sys.argv)
    widget = QWidget()
    widget.setGeometry(0, 0, 500, 500)

    hrz_lines = button_locs["button 1"]["hlines"]
    vrt_lines = button_locs["button 1"]["vlines"]

    ducklings = []
    for baseline, thickness in zip(vrt_lines["baselines"], vrt_lines["thicknesses"]):
        line = VLine(widget, button_locs["button 1"]["y"], baseline, thickness)
        ducklings.append(line)

    for baseline, thickness in zip(hrz_lines["baselines"], hrz_lines["thicknesses"]):
        line = HLine(widget, button_locs["button 1"]["x"], baseline, thickness)
        ducklings.append(line)

    print(widget.geometry().size()) 

    button = CircleButton(50, 
                          widget, 
                          start_pos=(button_locs["button 1"]["x"], button_locs["button 1"]["y"]),
                          ducklings=ducklings, 
                          locked=False)
    
    print(button.geometry().center())

    widget.show()
    app.exec()

    button_loc_dic = {}
    button_loc_dic.update({"button 1": {"x":button.geometry().center().x(), "y":button.geometry().center().y()}})
    print(button_loc_dic)