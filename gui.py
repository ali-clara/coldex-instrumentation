# -------------
# This is the Graphical User Interface (GUI) - true to its name, many graphs and user interfaces going on here!
# I've tried to make it as modular as possible, so adding additional sensors in the future won't be as much of a pain.
# 
# Most of the GUI features - like what sensors we display, what notetaking capabilities we need out of a logging panel,
# -------------

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT  as NavigationToolbar
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import matplotlib.pyplot as plt
import numpy as np
import yaml
import sys
import time
from collections import deque
from functools import partial
import concurrent.futures
import traceback
import pandas as pd

import logging
from logdecorator import log_on_start , log_on_end , log_on_error
# Set up a logger for this module
logger = logging.getLogger(__name__)
# Set the lowest-severity log message the logger will handle (debug = lowest, critical = highest)
logger.setLevel(logging.DEBUG)
# Create a handler that saves logs to the log folder named as the current date
# fh = logging.FileHandler(f"logs\\{time.strftime('%Y-%m-%d', time.localtime())}.log")
fh = logging.StreamHandler()
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)
# Create a formatter to specify our log format
formatter = logging.Formatter("%(levelname)s: %(asctime)s - %(name)s:  %(message)s", datefmt="%H:%M:%S")
fh.setFormatter(formatter)

from pyqt_helpers.live_plots import MyFigureCanvas
from pyqt_helpers.circle_button import CircleButton
from pyqt_helpers.lines import VLine
from pyqt_helpers.helpers import epoch_to_pacific_time, find_grid_dims

from main_pipeline.sensor import Sensor
from main_pipeline.interpreter import Interpreter
from main_pipeline.writer import Writer
from main_pipeline.bus import Bus


# main window
class ApplicationWindow(QWidget):
    """
    This is the Graphical User Interface, or GUI! It sets up the user interface for the main pipeline.

    Args:
        This class inherets from the general QWidget class in order to make the main window. There are lots of different 
        ways to this inheriting, which make some of the syntax slightly different in between applications. Ah well.
        
    """
    def __init__(self):
        """Constructor, called when the class is instantiated"""
        # Initialize the inherited class (QWidget)
        super().__init__()

        # Window settings
        self.setGeometry(50, 50, 2000, 1200) # window size (x-coord, y-coord, width, height)
        self.setWindowTitle("")

        # Set some fonts
        self.bold16 = QFont("Helvetica", 16)
        self.bold16.setBold(True)
        self.norm16 = QFont("Helvetica", 16)
        self.bold12 = QFont("Helvetica", 12)
        self.bold12.setBold(True)
        self.norm12 = QFont("Helvetica", 12)
        self.norm10 = QFont("Helvetica", 10)

        # Initialize the main sense-interpret-save data pipeline
        self.init_data_pipeline()
        
        # Set data buffer parameters
        self.max_buffer_length = 5000 # How long we let the buffers get, helps with memory
        self.default_plot_length = 60 # Length of time (in sec) we plot before you have to scroll back to see it
        self.init_data_buffer()
        
        # Create the three main GUI panels:

        # 1. Top left panel: sensor status and control
        left_widget = QWidget(self)
        left_widget.setLayout(self.build_control_layout(QGridLayout()))

        # 2. Top right panel: plots
        right_widget = QWidget(self)
        right_widget.setLayout(self.build_plotting_layout(QVBoxLayout()))

        # 3. Bottom panel: pneumatic layout
        self.pneumatic_grid_buttons = []
        self.pneumatic_autonomous_controls = []
        bottom_widget = QWidget(self)
        bottom_widget.setMinimumHeight(int(self.height()/2))
        bottom_widget.setLayout(self.build_pneumatic_layout(QHBoxLayout()))
        

        main_layout = QGridLayout()
        main_layout.addWidget(left_widget, 0, 0)
        main_layout.addWidget(right_widget, 0, 1)
        main_layout.addWidget(bottom_widget, 1, 0, 1, 2)
        self.setLayout(main_layout)
        
        # Create a threadpool for this class, so we can do threading later
        self.threadpool = QThreadPool()
            
        # Initiate two timers that both trigger every X ms:
        timer_update = 1000
        # One for updating the plots...
        self.plot_figs_timer = QTimer()
        self.plot_figs_timer.timeout.connect(self.update_plots)
        self.plot_figs_timer.start(timer_update)
        # ...and one for collecting, processing, and saving data
        self.execution_timer = QTimer()
        self.execution_timer.timeout.connect(self.run_data_collection)
        self.execution_timer.start(timer_update)
        
        # Show the window
        self.show()

    def __del__(self):
        """Destructor, called when the class is destroyed
        """
        self.sensor.shutdown_sensors()
    
    # def closeEvent(self, event):
    #     """This method overwrites the default QWidget closeEvent that triggers when the window "X" is clicked.
    #     It ensures we can shutdown sensors cleanly by opening a QMessageBox to prompt the user to quit/cancel
    #     """
    #     self.check_close_event()
    #     # If we actually want to shut down, shutdown the sensors and then accept the closeEvent
    #     if self.accept_quit:
    #         self.sensor.shutdown_sensors()
    #         try:
    #             self.executor.shutdown()
    #         except:
    #             pass
    #         event.accept()
    #     # Otherwise, ignore it
    #     else:
    #         event.ignore()

    def check_close_event(self):
        """Method to check if the user actually wants to quit or not. Opens a QMessageBox and stores
        the result as a boolean in self.accept_quit."""
        # Flags to handle clean shutdown by storing the "are you sure you want to quit" result
        self.accept_quit = None
        # Set up a messagebox to prompt the user
        msgbox = QMessageBox()
        msgbox.setIcon(QMessageBox.Question)
        msgbox.setText("Are you sure you want to close the app? This shuts down sensors and stops data collection.")
        msgbox.setWindowTitle("MGR App")
        msgbox.setStandardButtons(QMessageBox.Close | QMessageBox.Cancel)
        # Get the user click and parse it appropriately
        msg_return = msgbox.exec()
        if msg_return == QMessageBox.Close:
            self.accept_quit = True
        elif msg_return == QMessageBox.Cancel:
            self.accept_quit = False

    ## --------------------- HELPERS --------------------- ## 
    def _make_default_label(self, text, font):
        label = QLabel(self)
        label.setText(text)
        label.setFont(font)
        label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        return label

    ## --------------------- SENSOR STATUS & CONTROL --------------------- ## 
       
    def build_control_layout(self, left_layout:QGridLayout):
        """Method to build the layout for sensor status & control

        Args:
            left_layout (QLayout): The layout we want to store our status & control widgets in
        """
        left_layout.setContentsMargins(0, 20, 10, 0)
        # Initialize variables to store sensor control parameters, like temperature and pressure setpoint
        self.init_sensor_control_params()
        # Grab button information for both the main title array and the individual sensors
        title_button_info, sensor_button_info, control_button_info = self.define_sensor_button_callbacks()
        # Make the title row - has general buttons for initializing sensors and starting data collection
        start_next_row, title_colspan = self.make_title_control_panel(left_layout, title_button_info)
        # Make the individual button rows
        self.make_sensor_control_panel(left_layout, sensor_button_info, control_button_info, starting_row=start_next_row, colspan=title_colspan)
        # Position the panel at the top of the window and make it stretchy
        left_layout.setAlignment(QtCore.Qt.AlignTop)
        for i in range(title_colspan):
            left_layout.setColumnStretch(i, 1)

        return left_layout
    
    def init_sensor_control_params(self):
        """Method to initialize dictionaries to hold sensor control information, namely their status and setpoint control values
        """
        # Every instrument has a status value, so initialize a dictionary with a status entry for every sensor
        self.sensor_status_dict = {}
        for name in self.sensor_names:
            self.sensor_status_dict.update({name:0}) # "0" means offline

        # The instruments that have setpoint control values have that set in the sensor_data configuration file, which 
        # lives in self.big_data dict. If there's a key corresponding to "Control", add the sensor and the name of the
        # control parameter to our control dictionary
        self.sensor_control_inputs = {}
        for sensor in self.sensor_names:
            try:
                self.big_data_dict[sensor]["Control"]
            except KeyError:
                pass
            else:
                for control_param in self.big_data_dict[sensor]["Control"]:
                    self.sensor_control_inputs.update({sensor: {control_param: None}}) # Initialize it to None to be safe

    def make_title_control_panel(self, parent:QGridLayout, title_button_info:dict, colspan=2):
        """Builds the panel for general sensor control - has buttons to initialize/shutdown sensors and start/stop data collection

        Args:
            parent (QGridLayout): Parent layout
            title_button_info (dict): Dictionary containing key-value pairs of 
                "button name":{"callback:button_callback_function, "enabled":True/False}
            colspan (int, optional): How many columns of buttons. Defaults to 2.

        Returns:
            start_next_row (int): What row of a QGridLayout any further widgets should start on

            **colspan**: *int*: How many columns we've used so far
        """
        # Set the title
        label = QLabel(self)
        label.setText("Sensor Status & Control")
        label.setFont(self.bold16)
        label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        parent.addWidget(label, 0, 0, 1, colspan) # args: widget, row, column, rowspan, columnspan

        # Determine the dimensions of our button grid
        num_rows, num_cols = find_grid_dims(num_elements=len(title_button_info), num_cols=colspan)

        # For all the buttons we want to generate (stored in the title_button_info dict),
        # create, position, and assign a callback for each
        i = 0
        title_button_text = list(title_button_info.keys())
        self.title_buttons = {} # Holding onto the buttons for later
        for row in range(1, num_rows+1): # Adjusting for the QLabel title that we put on row 1
            for col in range(num_cols):
                button_text = title_button_text[i]
                button = QPushButton(self)
                button.setText(button_text)
                button.setFont(self.norm12)
                button.pressed.connect(title_button_info[button_text]["callback"]) # set the button callback
                button.setEnabled(title_button_info[button_text]["enabled"]) # set the button initial state (enabled/disabled)
                parent.addWidget(button, row, col)
                self.title_buttons.update({button_text:button})
                i+=1

        # Add a separation line to the layout after all the buttons
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        parent.addWidget(line, row+1, 0, 1, colspan)

        # We should add any further widgets after that^ line widget, so 2 rows after the last button
        start_next_row = num_rows+2

        return start_next_row, colspan
        
    def make_sensor_control_panel(self, parent:QGridLayout, sensor_buttons:dict, input_buttons:dict, starting_row, colspan):
        """Builds the panel for specific sensor control - has buttons that depend upon sensor functionality

        Args:
            parent (QGridLayout): Parent layout
            sensor_buttons (dict): Dictionary containing key-value pairs of "sensor_name":{button_1_name:button_1_callback, ...}
                for the buttons that do whatever they say in their names
            input_buttons (dict): Dictionary containing key-value pairs of "sensor_name":{button_1_name:button_1_callback, ...}
                for the buttons that send setpoint commands
            starting_row (int): What row of the parent layout we should start building from
            colspan (int): How many columns are already being used in the parent layout

        Returns:
            start_next_row (int): What row of a QGridLayout any further widgets should start on
        """
        # For all the sensors, create control buttons (if applicable) and a status indicator
        self.sensor_status_display = {} # Holding onto the status displays for later
        row = starting_row
        for sensor in self.sensor_names:
            # First widget we want to place - the sensor title
            title = QLabel(self)
            title.setFont(self.bold12)
            title.setText(sensor)
            title.setAlignment(Qt.AlignHCenter)
            title.setStyleSheet("padding-top:10px")
            parent.addWidget(title, row, 0, 1, colspan)
            row +=1
            # Second widget - the status indicator (QLabel that changes color & text upon initialization and shutdown)
            status = QLabel(self)
            status.setText("OFFLINE")
            status.setFont(self.norm12)
            status.setStyleSheet("background-color:#AF5189; margin:10px")
            status.setAlignment(Qt.AlignCenter)
            parent.addWidget(status, row, 0, 1, colspan)
            row +=1
            self.sensor_status_display.update({sensor:status}) # Hold onto the status display for later
            # Third widget - sensor buttons (initialize, shutdown, start, etc)
            # If this sensor has buttons to add...
            try:
                # ...extract their names from the dictionary...
                buttons = sensor_buttons[sensor]
                c = 0 # Column counter
                n = 0 # Button counter
                for button in buttons:
                    # ...make a button...
                    b = QPushButton(self)
                    b.setText(button)
                    b.setFont(self.norm12)
                    # ...and connect its callback to the function that lives at this key in the dictionary.
                    b.pressed.connect(sensor_buttons[sensor][button])
                    parent.addWidget(b, row, c)
                    c += 1
                    n += 1
                    # Every two buttons, add another row and reset the column counter
                    if n%2 == 0:
                        row += 1
                        c = 0
                row +=1
            # Otherwise, catch the error and move on
            except KeyError:
                logger.info(f"No command buttons for the {sensor}")
            # Fourth widget - control input. This is a button that sends the input (the callback function lives in 
                # input_buttons) and a line entry that lets the user set the input
                # Validation for the inputs happens in the lowest level sensor interface, so it's safe to chuck any
                # values at them from here
            try:
                control_inputs = self.sensor_control_inputs[sensor]
                buttons = input_buttons[sensor]
                # Iterate through both lists, making buttons and text inputs as we go
                for button, ctrl_input in zip(buttons, control_inputs):
                    # Add a button
                    b = QPushButton(self)
                    b.setText(button)
                    b.setFont(self.norm12)
                    # Connect its callback to the function that lives at this key of the dictionary
                    b.pressed.connect(input_buttons[sensor][button])
                    parent.addWidget(b, row, 0)
                    # Add a text input
                    line = QLineEdit(self)
                    line.setFont(self.norm12)
                    # Display the current value of the control input as placeholder text
                    line.setPlaceholderText(f"{ctrl_input}: {self.sensor_control_inputs[sensor][ctrl_input]}")
                    # When the input is set, add it to the dictionary of control inputs
                    line.editingFinished.connect(partial(self._save_control_input, line, sensor, ctrl_input))
                    parent.addWidget(line, row, 1)
                    row +=1
            except KeyError:
                logger.info(f"No control inputs for the {sensor}")
            # Fifth widget - dividing line
            line = QFrame(self)
            line.setFrameShape(QFrame.HLine)
            parent.addWidget(line, row, 0, 1, colspan)
            row +=1

        # We should add any further widgets after the last dividing line
        start_next_row = row + 1
        return start_next_row
    
    def define_sensor_button_callbacks(self):
        """Method that sets the button callbacks for the sensor status & control panel. **If you're adding a new sensor, you'll
        likely need to add to this method.**

        Returns:
            title_buttons (dict): Dictionary with title button information 
                {"button_name":{"callback":button_callback, "enabled":True/False}}
            
            sensor_buttons (dict): Dictionary with sensor button information {"sensor_name":{"button_name":button_callback}}
        """

        # Initialize a dictionary of general title buttons - these functions control all the sensors or general large GUI functions
        title_buttons = {}
        title_button_names = ["Initialize All Sensors", "Shutdown All Sensors", "Start Data Collection", "Stop Data Collection"]
        title_button_callbacks = [self._on_sensor_init, self._on_sensor_shutdown, self._on_start_data, self._on_stop_data]
        title_button_enabled = [True, True, False, False]
        for name, callback, enabled in zip(title_button_names, title_button_callbacks, title_button_enabled):
            title_buttons.update({name: {"callback":callback, "enabled":enabled}})

        # Initialize a dictionary of buttons for each sensor. These buttons do whatever they say on the tin (e.g "Start Picarro"
            # runs the initialization sequence for the Picarro.)
            # I want the "status" bar of each sensor to update when some of these buttons are pressed, so I do something a little cheeky
            # with their callbacks - using "partial()" creates a temporary function where the first argument is the function 
            # to execute and the following arguments are its inputs. I use this to pass each sensor button function into a general
            # "_on_sensor_button" method that updates the sensor status as well as executing the desired callback whenever the button
            # is pressed
        sensor_buttons = {}
        sensor_buttons.update({"Arduino": {"Start Arduino": partial(self._on_sensor_button, "Arduino", self.sensor.arduino.initialize_arduino),
                                           "Stop Arduino": partial(self._on_sensor_button, "Arduino", self.sensor.arduino.shutdown_arduino)}})

        # sensor_buttons.update({"Picarro Gas": {"Start Picarro":
        #                                        partial(self._on_sensor_button, "Picarro Gas", self.sensor.gas_picarro.initialize_picarro)}})
        
        # Initialize another dictionary of buttons for each sensor. These are a special set that sends user-specified control inputs,
            # instead of running the same function/protocol each time. I use the same "partial()" strategy here to specify which
            # sensor and which input parameter we're sending, which gets read from a dictionary in _send_control_input and saved to 
            # that dictionary in _save_control_input
        input_buttons = {}
        input_buttons.update({"Arduino": {"Arduino Input": partial(self._send_control_input, "Arduino", "Arduino control 1", self.sensor.arduino.send_command)}})      

        return title_buttons, sensor_buttons, input_buttons
        
    def _on_sensor_button(self, sensor:str, initialization_function):
        """Method that calls the function passed into initialization_function, gets the initialization result,
        and uses it to update the appropriate sensor status.

        Args:
            sensor (str): Name of the sensor. Must match a key in self.big_data_dict
            initialization_function (method): Whatever you want the sensor button to do
        """
        init_result = initialization_function()
        self.sensor_status_dict.update({sensor: init_result})
        self.update_sensor_status()

    def _on_sensor_init(self):
        """Callback function for the 'Initialize All Sensors' button
        """
        # Start our sensor initialization in a thread so any blocking doesn't cause the GUI to freeze
        worker = Worker(self.sensor.initialize_sensors)
        # When it's done, trigger the _finished_sensor_init function
        worker.signals.result.connect(self._finished_sensor_init)
        self.threadpool.start(worker)

    def _finished_sensor_init(self, sensor_status:dict):
        """Method that gets triggered when that thread^ in _on_sensor_init finishes.

        Args:
            sensor_status (dict): dictionary returned from self.sensor.initialize_sensors
        """
        # Update the sensor status dictionary and the GUI
        self.sensor_status_dict = sensor_status
        self.update_sensor_status()
        # Enable the data collection buttons
        self.title_buttons["Start Data Collection"].setEnabled(True)
        self.title_buttons["Stop Data Collection"].setEnabled(True)
        
    def _on_sensor_shutdown(self):
        """Callback function for the 'Shutdown All Sensors' button
        """
        self.data_collection = False
        # Start our sensor shutdown in a thread so any blocking doesn't cause the GUI to freeze
        worker = Worker(self.sensor.shutdown_sensors)
        # When it's done, trigger the _finished_sensor_shutdown function
        worker.signals.result.connect(self._finished_sensor_shutdown)
        self.threadpool.start(worker)

    def _finished_sensor_shutdown(self, sensor_status:dict):
        """Method that gets triggered when that thread^ in _on_sensor_shutdown finishes.

        Args:
            sensor_status (dict): dictionary returned from self.sensor.shutdown_sensors
        """
        # Update the sensor status dictionary and the GUI
        self.sensor_status_dict = sensor_status
        self.update_sensor_status()
        # Enable the data collection buttons
        self.title_buttons["Start Data Collection"].setEnabled(False)
        self.title_buttons["Stop Data Collection"].setEnabled(False)
    
    def _on_start_data(self):
        """Callback function for the "Start Data Collection" button. Sets the data_collection flag to true
        """
        self.data_collection = True
        
    def _on_stop_data(self):
        """Callback function for the "Stop Data Collection" button. Sets the data_collection flag to false
        """
        self.data_collection = False

    def _send_control_input(self, sensor:str, input_name:str, control_function):
        """Method to grab the control input out of the self.sensor_control_inputs dictionary
        and send it to the provided control function

        Args:
            sensor (str): The sensor name, must correspond to a key in self.big_data_dict
            input_name (str): The name of the input parameter we're sending, must correspond to a key in self.sensor_control_inputs
            control_function (method): The function in question
        """
        control_input = self.sensor_control_inputs[sensor][input_name]
        control_function(control_input)

    def _save_control_input(self, line:QLineEdit, sensor:str, input_name:str):
        """Callback function for the QLineEdit entries, called whenever the user finishes editing them.

        Args:
            line (QLineEdit): The line entry in question
            sensor (str): The sensor name, must correspond to a key in self.big_data_dict
            input_name (str): The name of the input parameter we're sending, must correspond to a key in self.sensor_control_inputs
        """
        # Grab the current text of the line entry
        current_input = line.text()
        # Save the text to the correct key of the dictionary
        self.sensor_control_inputs[sensor][input_name] = current_input
        # Set the line text to reflect the new input, and clear the line
        line.setPlaceholderText(f"{input_name}: {current_input}")
        line.clear()

    def update_sensor_status(self):
        """Method to update the sensor status upon initialization or shutdown. Uses the values stored in
        self.sensor_status_dict to set the color and text of each sensor status widget."""
        # Loop through the sensors and grab their status from the sensor status dictionary
        for name in self.sensor_names:
            status = self.sensor_status_dict[name]
            # If we're offline
            if status == 0:
                # color = "#D80F0F"
                color = "#AF5189"
                text = "OFFLINE"
            # If we're online / successfully initialized
            elif status == 1:
                color = "#619CD2"
                text = "ONLINE"
            # If we're disconnected / using shadow hardware
            elif status == 2:
                color = "#FFC107"
                text = "SHADOW HARDWARE"
            # IF we failed initialization / there's some other error going on
            elif status == 3:
                color = "#D55E00"
                text = "ERROR"
            # If we recieved an erroneous reading, make it obvious
            else:
                color = "purple"
                text = "?????"

            # Update the sensor status accordingly
            status = self.sensor_status_display[name] # This is a dictionary of QLabels
            status.setText(text)
            status.setStyleSheet(f"background-color:{color}; margin:10px")

    ## --------------------- PNEUMATIC GRID --------------------- ##

    def build_pneumatic_layout(self, bottom_layout:QHBoxLayout):
        
        pneum_control_frame = self.make_pneumatic_control()
        pneum_grid = QGridLayout()
        pneum_grid_sidebar = QVBoxLayout()

        # middle
        line = QFrame(self)
        line.setFrameShape(QFrame.VLine)
        pneum_grid.addWidget(line, 0, 0, 2, 1)

        label = self._make_default_label("Pneumatic Grid", self.bold16)
        pneum_grid.addWidget(label, 0, 1)
                             
        pneum_widget = self.make_pneumatic_button_grid()
        pneum_grid.addWidget(pneum_widget, 1, 1)

        line = QFrame(self)
        line.setFrameShape(QFrame.VLine)
        pneum_grid.addWidget(line, 0, 2, 2, 1)
        
        # right
        button = QPushButton(self)
        button.setText("Unlock Button Positions")
        button.setFont(self.norm12)
        button.setMinimumWidth(int(self.width()*0.15))
        button.clicked.connect(partial(self._control_pneumatic_button_movement, button))
        pneum_grid_sidebar.addWidget(button)

        button = QPushButton(self)
        button.setText("Save button positions")
        button.setFont(self.norm12)
        button.clicked.connect(self._save_pneumatic_button_positions)
        pneum_grid_sidebar.addWidget(button)

        pneum_grid_sidebar.setAlignment(QtCore.Qt.AlignCenter)

        bottom_layout.addLayout(pneum_control_frame)
        bottom_layout.addLayout(pneum_grid)
        bottom_layout.addLayout(pneum_grid_sidebar)

        return bottom_layout
    
    def make_pneumatic_control(self):
        pneum_control_frame = QVBoxLayout()

        label = self._make_default_label("Control Method", self.bold16)
        pneum_control_frame.addWidget(label)

        label = self._make_default_label("Manual Valve Controls", self.norm12)
        pneum_control_frame.addWidget(label)

        button = QPushButton(self)
        button.setCheckable(True)
        button.setStyleSheet("background-color : green")
        button.setFixedWidth(int(label.width() * 1.5))
        
        button.clicked.connect(partial(self._on_manual_valve_control, button))
        pneum_control_frame.addWidget(button, alignment=QtCore.Qt.AlignHCenter)

        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        pneum_control_frame.addWidget(line)

        label = self._make_default_label("Automation Routine", self.norm12)
        pneum_control_frame.addWidget(label)

        dropdown = QComboBox()
        dropdown.addItems(['One', 'Two', 'Three', 'Four']) # Replace with automation routines
        dropdown.setDisabled(True)
        self.pneumatic_autonomous_controls.append(dropdown)
        pneum_control_frame.addWidget(dropdown)

        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        pneum_control_frame.addWidget(line)

        buttons_layout = QHBoxLayout()

        button = QPushButton()
        button.setIcon(QIcon("doc/imgs/play.png"))
        button.clicked.connect(partial(self._on_start_autonomous, dropdown))
        button.setDisabled(True)
        self.pneumatic_autonomous_controls.append(button)
        buttons_layout.addWidget(button) 

        button = QPushButton()
        button.setIcon(QIcon("doc/imgs/pause.png"))
        button.clicked.connect(partial(self._on_pause_autonomous, dropdown))
        button.setDisabled(True)
        self.pneumatic_autonomous_controls.append(button)
        buttons_layout.addWidget(button) 

        button = QPushButton()
        button.setIcon(QIcon("doc/imgs/stop.png"))
        button.clicked.connect(partial(self._on_stop_autonomous, dropdown))
        button.setDisabled(True)
        self.pneumatic_autonomous_controls.append(button)
        buttons_layout.addWidget(button) 

        pneum_control_frame.addLayout(buttons_layout)

        # Position the widgets at the top of the layout
        pneum_control_frame.setAlignment(QtCore.Qt.AlignTop)

        return pneum_control_frame


    def make_pneumatic_button_grid(self):
        parent_widget = QWidget()
        parent_widget.setMinimumHeight(int(self.height()/2.25))
        parent_widget.setMinimumWidth(int(self.width()*0.6))

        def yey():
            print("clicked")

        button = CircleButton(radius=50, parent=parent_widget)
        self.pneumatic_grid_buttons.append(button)
        button.clicked.connect(yey)
        
        return parent_widget
    
    def _on_manual_valve_control(self, button:QPushButton):
        # If button is checked
        if button.isChecked():
            button.setStyleSheet("background-color : grey")
            for pneumatic_button in self.pneumatic_grid_buttons:
                pneumatic_button.setDisabled(True)
            for control in self.pneumatic_autonomous_controls:
                control.setEnabled(True)
            # button.setText("Click for manual valve controls")
            # label.setText("Valve Controls: Autonomous")
        # If button is unchecked
        else:
            button.setStyleSheet("background-color : green")
            for pneumatic_button in self.pneumatic_grid_buttons:
                pneumatic_button.setEnabled(True)
            for control in self.pneumatic_autonomous_controls:
                control.setDisabled(True)
            # button.setText("Click for autonomous valve controls")
            # label.setText("Valve Controls: Manual")

    def _on_start_autonomous(self, routine_select:QComboBox):
        routine_name = routine_select.currentText()
        print(f"start autonomous mode: {routine_name}")

    def _on_pause_autonomous(self, routine_select:QComboBox):
        routine_name = routine_select.currentText()
        print(f"pause autonomous mode: {routine_name}")

    def _on_stop_autonomous(self, routine_select:QComboBox):
        routine_name = routine_select.currentText()
        print(f"stop autonomous mode: {routine_name}")

    def _control_pneumatic_button_movement(self, control_button:QPushButton):
        if self.pneumatic_grid_buttons[0].button_locked:
            for pneumatic_button in self.pneumatic_grid_buttons:
                pneumatic_button.unlock_button_movement()
                control_button.setText("Lock Button Positions")
        else:
            for pneumatic_button in self.pneumatic_grid_buttons:
                pneumatic_button.lock_button_movement()
                control_button.setText("Unlock Button Positions")

    def _save_pneumatic_button_positions(self):
        for i, pneumatic_button in enumerate(self.pneumatic_grid_buttons):
            button_loc_dic = {}
            button_loc_dic.update({f"button {i}": {"x":pneumatic_button.geometry().center().x(), 
                                                "y":pneumatic_button.geometry().center().y()}})
            with open("config/button_locs.yaml", "w") as yaml_file:
                dump = yaml.safe_dump(button_loc_dic)
                yaml_file.write(dump)
            
    
    ## --------------------- DATA STREAMING / LIVE PLOTTING --------------------- ##

    def build_plotting_layout(self, center_layout:QLayout):
        """
        A method to build the central plotting panel. Takes in the parent layout (center_layout) and adds a QTabWidget
        to give us a convienent way to display the live sensor plots. For each sensor (stored in self.sensor_names), we add a tab
        to hold the matplotlib figure and toolbar that will display sensor data.

        Args:
            center_layout (QLayout): The main window layout we want to nest the plots in
        """
        center_layout.setContentsMargins(10, 20, 10, 0)
        # Make a title
        label = QLabel(self)
        label.setText("Live Sensor Data")
        label.setFont(self.bold16)
        label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        center_layout.addWidget(label)

        # Initialize the plotting flag
        self.data_collection = False

        # Create some object variables to hold plotting information - the QTabWidget that displays the figs, and a dictionary
        # to hold onto the figure objects themselves for later updating
        self.plot_tab = QTabWidget(self)
        self.plot_figs = {}
        # Loop through the sensors, create a figure & toolbar for each, and add them to the QTabWidget
        for sensor in self.sensor_names:
            # Create a new tab and give it a vertical layout
            tab = QWidget(self)
            tab.setObjectName(sensor)
            tab_vbox = QVBoxLayout(tab)
            # For each figure, we want a subplot corresponding to each piece of data returned by the sensor. Grab that number
            num_subplots = len(self.big_data_dict[sensor]["Data"])
            # Create the figure and toolbar
            fig = MyFigureCanvas(x_init=[[np.nan]]*num_subplots,   # List of lists, one for each subplot, to initialize the figure x-data
                                 y_init=[[np.nan]]*num_subplots, # List of lists, one for each subplot, to initialize the figure y-data
                                 xlabels=["Time"]*num_subplots,
                                 ylabels=list(self.big_data_dict[sensor]["Data"].keys()),
                                 num_subplots=num_subplots,
                                 x_range=self.default_plot_length, # Set xlimit range of each axis
                                 )
            toolbar = NavigationToolbar(canvas=fig, parent=self, coordinates=False)
            # Create a button to plot the entire day of data in a separate window
            button = QPushButton("Plot Entire Day")
            button.setFont(self.norm12)
            button.pressed.connect(partial(self.plot_entire_day, sensor))
            # Add the figure, toolbar, and button to this tab's layout
            tab_vbox.addWidget(toolbar, alignment=Qt.AlignHCenter)
            tab_vbox.addWidget(fig)
            tab_vbox.addWidget(button)
            # Add this tab to the QTabWidget
            self.plot_tab.addTab(tab, sensor)
            # Hold onto the figure object for later
            self.plot_figs.update({sensor: fig})
        # Once we've done all that, add the QTabWidget to the main layout
        center_layout.addWidget(self.plot_tab)

        return center_layout


    def _thread_plots(self):
        """Method to update the live plots with the buffers stored in self.big_data_dict
        """
        # Grab the name of the current QTabWidget tab we're on (which sensor data we're displaying)
        plot_name = self.plot_tab.currentWidget().objectName()
        fig = self.plot_figs[plot_name]
        # Make sure the figure is the correct object - not strictly necessary, but a good safety check
        if type(fig) == MyFigureCanvas:
            # Grab the updated x and y values from the big data buffer
            x_data_list, y_data_list = self.get_xy_data_from_buffer(plot_name)
            # Pass the updated data into the figure object and redraw the axes
            fig.update_data(x_new=x_data_list, y_new=y_data_list)
            fig.update_canvas()
    
    def update_plots(self):
        """Method to start a thread that will update the live plots with the buffers stored in self.big_data_dict
        """
        # If the data collection flag is active...
        if self.data_collection:
            worker = Worker(self._thread_plots)
            self.threadpool.start(worker)

    def get_xy_data_from_buffer(self, plot_name:str):
        """Method to parse the big data buffer and pull out the sensor channels we're interested in plotting.

        Args:
            plot_name (str): The name of the QWidget we're plotting on, should match a sensor in self.sensor names or be "All" for the
                main page plots

        Returns:
            x_data_list (list): List of deques from self.big_data_dict - timestamp for each sensor channel

            **y_data_list** (list): List of deques from self.big_data_dict - data for each sensor channel
        """
        # Try to extract "plot_name" from the big buffer - if it's a sensor, we'll be able to pull the data directly
        try:
            # Extract data from the buffer
            num_subplots = len(self.big_data_dict[plot_name]["Data"].keys())
            t = self.big_data_dict[plot_name]["Time (epoch)"]
            y = list(self.big_data_dict[plot_name]["Data"].values())
            # Convert from UTC epoch time to pacific time, passing in the y_data too to ensure the arrays
            # stay the same shape
            t_pacific_time, y_data_list = epoch_to_pacific_time(t, y)
            # All sensor channels have the same timestamp, so make n_subplots copies of the time
            x_data_list = [t_pacific_time]*num_subplots 
            
        # If we can't find it in the buffer (and we should never get here since all dict keys are passed in externally), 
        # something went wrong. The plots safely don't update if we pass in None, so do that
        except KeyError as e:
            logger.error(f"Error in reading the data buffer when updating plots: {e}")
            x_data_list = None
            y_data_list = None

        return x_data_list, y_data_list

    def _get_entire_day_data(self, sensor):
        """Method that reads the big data saving csv, pulls out the channels of the sensor we want,
        and returns them.

        Args:
            sensor (str): The name of the sensor, must match a key in self.big_data_dict

        Returns:
            result (tuple): tuple of (sensor: *str*, data: *dict*)
        """
        # Grab the filepath of the data csv from the writer object
        filepath = self.writer.get_data_directory()
        # Grab the data channels we have for this sensor - we'll use these to get data from the csv
        channels = list(self.big_data_dict[sensor]["Data"].keys())
        # Add time so we can get that too
        channels.append("time (epoch)")
        # The data is saved to the csv in the form "Sensor Name": "Channel Name", so format it here
        cols = [f"{sensor}: {channel}" for channel in channels]
        try:
            data = pd.read_csv(filepath, delimiter=',', header=0, usecols=cols)
        except FileNotFoundError as e:
            logger.warning(f"Error in accessing csv data: {e}")
            data = {}

        return sensor, data
    
    def _update_entire_day_plot(self, result):
        """Method that triggers when the threaded self._get_entire_day_data finishes, 
        giving us the dictionary of sensor data pulled from the csv file. 

        Args:
            result (tuple): tuple of (sensor: *str*, data: *dict*)
        """
        # The thread retuns the name of the sensor and the dictionary of data
        sensor, data = result
        # Grab some metadata from the big_data_dict - the channels of data we have for this sensor, and the 
        # number of subplots we need to display them all
        channels = list(self.big_data_dict[sensor]["Data"].keys())
        num_subplots = len(channels)
        # Pull the time from the data input and convert it from UTC epoch time to Pacific time
        t = (data[f"{sensor}: time (epoch)"]).values
        y = [data[f"{sensor}: {channel}"] for channel in channels]
        t_pacific_time, y_data = epoch_to_pacific_time(t, y)
        # Create a figure and toolbar with the data for each sensor channel
        fig = MyFigureCanvas(x_init=[t_pacific_time]*num_subplots,
                             y_init=y_data,
                             num_subplots=num_subplots,
                             xlabels=["Datetime"]*num_subplots,
                             ylabels=channels,
                             x_range=len(t),
                             )
        toolbar = NavigationToolbar(fig, self)
        # Create another window, add the widgets, and show the window
        self.plot_window = AnotherWindow(title=sensor)
        self.plot_window.set_widget(toolbar)
        self.plot_window.set_widget(fig)
        self.plot_window.show()

    def plot_entire_day(self, sensor:str):
        """Method to spin up a thread that plots the entire day's worth of data and displays it on another window.

        Args:
            sensor (str): The name of the sensor, must match a key in self.big_data_dict
        """
        # Set up the thread to grab sensor data from the csv
        worker = Worker(self._get_entire_day_data, sensor)
        # When the thread finishes, display the result
        worker.signals.result.connect(self._update_entire_day_plot)
        # Start the thread
        self.threadpool.start(worker)
        

    ## --------------------- DATA COLLECTION PIPELINE --------------------- ##

    def init_data_pipeline(self):
        """Creates objects of the Sensor(), Interpreter(), and Display() classes, and sets busses and delay times 
        for each sense/interpret/save process (see run_data_collection for how these are all used)
        """
        # Create each main object of the pipeline
        self.sensor = Sensor(debug=False)
        self.interpreter = Interpreter()
        self.writer = Writer()

        # Initialize a bus for each thread we plan to spin up later
        self.abakus_bus = Bus()
        self.flowmeter_sli2000_bus = Bus()
        self.flowmeter_sls1500_bus = Bus()
        self.laser_bus = Bus()
        self.picarro_gas_bus = Bus()
        self.bronkhorst_bus = Bus()
        self.main_interp_bus = Bus()

    def init_data_buffer(self):
        """Method to read in and save the sensor_data configuration yaml file

        Updates:
            **self.big_data_dict**: *dict* - Holds buffer of data with key-value pairs 'Sensor Name':deque[data buffer]

            **self.sensor_names**: *list* - Sensor names that correspond to the buffer dict keys

        """
        # Read in the sensor data config file to initialize the data buffer. 
        # Creates a properly formatted, empty dictionary to store timestamps and data readings to each sensor
        try:
            with open("config/sensor_data.yaml", 'r') as stream:
                self.big_data_dict = yaml.safe_load(stream)
        except FileNotFoundError as e:
            logger.error(f"Error in loading the sensor data config file: {e}")
            self.big_data_dict = {}

        # Comb through the keys, set the timestamp to the current time and the data to zero
        sensor_names = self.big_data_dict.keys()
        for name in sensor_names:
            channels = self.big_data_dict[name]["Data"].keys()
            self.big_data_dict[name]["Time (epoch)"] = deque([np.nan], maxlen=self.max_buffer_length)
            for channel in channels:
                self.big_data_dict[name]["Data"][channel] = deque([np.nan], maxlen=self.max_buffer_length)

        # Grab the names of the sensors from the dictionary
        self.sensor_names = list(sensor_names)

    def _thread_data_collection(self):
        """Method to spin up threads for each sensor, plus the interpreter and the writer. 
        Allows us to take, process, and save data (mostly) simultaneously

        Returns:
            data (dict): Big dictionary of processed sensor data, has the same structure as self.big_data_dict
        """
        # Create a ThreadPoolExecutor to accomplish a bunch of tasks at once. These threads pass data between themselves with busses (which handle
        # proper locking, so we're not trying to read and write at the same time) and return a big dictionary of the most recent processed sensor data
        try:
            with concurrent.futures.ThreadPoolExecutor() as self.executor:
                self.executor.submit(self.sensor.abakus_producer, self.abakus_bus)
                self.executor.submit(self.sensor.flowmeter_sli2000_producer, self.flowmeter_sli2000_bus)
                self.executor.submit(self.sensor.flowmeter_sls1500_producer, self.flowmeter_sls1500_bus)
                self.executor.submit(self.sensor.laser_producer, self.laser_bus)
                self.executor.submit(self.sensor.picarro_gas_producer, self.picarro_gas_bus)
                self.executor.submit(self.sensor.bronkhorst_producer, self.bronkhorst_bus)
                self.executor.submit(self.interpreter.main_consumer_producer, self.abakus_bus, self.flowmeter_sli2000_bus,
                                            self.flowmeter_sls1500_bus, self.laser_bus, self.picarro_gas_bus, self.bronkhorst_bus, 
                                            self.main_interp_bus)

                eWriter = self.executor.submit(self.writer.write_consumer, self.main_interp_bus)
        except RuntimeError as e:
            logger.warning(f"Encountered Error in data threading: {e}")

        # Get the processed data from the final class (also blocks until everything has completed its task)
        data = eWriter.result()
        return data
    
    def _update_buffer(self, new_data:dict):
        """Method to update the self.big_data_dict buffer with new data from the sensor pipeline.
        
        Args:
            new_data (dict): Most recent data update. Should have the same key/value structure as big_data_dict
            use_noise (bool): Adds some random noise if true. For testing only
        """
        # For each sensor, grab the timestamp and the data from each sensor channel
        for name in self.sensor_names:
            # Grab and append the timestamp
            try:    # Check if the dictionary key exists... 
                new_time = new_data[name]["Time (epoch)"]  
                self.big_data_dict[name]["Time (epoch)"].append(new_time)
            except KeyError as e:   # ... otherwise log an exception
                logger.warning(f"Error updating the {name} buffer timestamp: {e}")
            except TypeError as e:  # Sometimes due to threading shenanigans it comes through as "NoneType", check for that too
                logger.warning(f"Error updating the {name} buffer timestamp: {e}")
                pass
            
            # Grab and append the data from each channel
            channels = list(self.big_data_dict[name]["Data"].keys())
            for channel in channels:
                try:    # Check if the dictionary key exists... 
                    ch_data = new_data[name]["Data"][channel]
                    self.big_data_dict[name]["Data"][channel].append(ch_data)
                except KeyError:    # ... otherwise log an exception
                    logger.warning(f"Error updating the {name} buffer data: {e}")
                    pass
                except TypeError as e: 
                    logger.warning(f"Error updating the {name} buffer data: {e}")
                    pass
    
    def run_data_collection(self):
        """Method to complete the entire sense/interpret/save data pipeline once. This is called by a timer way back in __init__, so gets triggered every time that
        timer fires. It spins up a bunch of threads to gather data from each sensor, pass raw data into the interpretor class, and save the processed data
        """
        # If data collection is active...
        if self.data_collection:
            # Set up a thread to go query all the instruments once and process their results
            worker = Worker(self._thread_data_collection)
            # Once that's finished, trigger the method to save the results to our internal data buffer
            worker.signals.result.connect(self._update_buffer)
            # Spin up the thread
            self.threadpool.start(worker)

###################################### HELPER CLASSES ######################################

## --------------------- SEPARATE WINDOW --------------------- ##
class AnotherWindow(QWidget):
    """This class is a skeleton window with the capability of adding external widgets. If we need another window 
    (e.g to plot all that day's data on a new screen) we can call this class and add widgets. It's bare-bones and
    really only good for simple windows; if you need more functionality, you'd probably want to make a custom class.

    Args:
        QWidget (QWidget): Inherits from the general QWidget class
    """
    def __init__(self, title="New Window"):
        super().__init__()
        self.setWindowTitle(title)
        # Give the window a single layout
        self.my_layout = QVBoxLayout()
        self.setLayout(self.my_layout)

    def set_widget(self, widget:QWidget):
        """Simple method to add a widget to the layout.

        Args:
            widget (QWidget): The widget to be added
        """
        self.my_layout.addWidget(widget)


## --------------------- PYQT THREADING --------------------- ##
class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.

    Supported signals are:
        - finished: None
        - error: tuple (exctype, value, traceback.format_exc() )
        - result: anything (object data returned from processing)
        - progress: int indicating % progress
    """
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class Worker(QRunnable):
    """
    Worker thread

    Inherits from QRunnable to handle worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function
    """
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        """
        Initialise the runner function with passed args, kwargs.
        """
        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except: # If there's an error, report it
            exctype, value = sys.exc_info()[:2]
            logger.error(traceback.print_exc((exctype, value, traceback.format_exc())))
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit() # Done


# If we're running from this script, spin up QApplication and start the GUI
if __name__ == "__main__":
    qapp = QtWidgets.QApplication(sys.argv)
    app = ApplicationWindow()
    qapp.exec_()