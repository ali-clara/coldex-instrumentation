import sys
from PyQt5.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QPushButton, 
    QLabel,
    QVBoxLayout,
    QWidget, 
    )

class my_window(QMainWindow):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        self.label = QLabel("Name of Button")
        layout.addWidget(self.label)
        
        for cnt in range(1,6):
            txt = str(cnt)+"_Button"
            wid = QPushButton(txt)
            wid.setCheckable(True)
            wid.setObjectName(txt)            
            wid.clicked.connect(lambda state, btn=wid : self.update_labels(btn))
            layout.addWidget(wid)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
    def update_labels(self, btn):
        self.label.setText(btn.objectName())
          
app = QApplication(sys.argv)
window = my_window()
window.show()
app.exec()
