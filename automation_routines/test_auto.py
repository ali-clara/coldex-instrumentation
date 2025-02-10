###
# Example setup for an automation routine. I suggest setting them all up this way - 
# a class to manage the routine itself with a single entry point (run_routine). These script
# MUST have a function called run() in order for the GUI to understand them. 
# 
# Another thing to note is that I've set up run() to take an arbitrary input: run(**kwargs)
# It looks like magic, but it just means "keyworded argument". Whatever we give the function gets
# turned into a dictionary with the key-value pairs we specified. This lets us stay a little more
# flexible and backwards compatible - if I add a new script with an input we haven't used for
# old scripts, the old scripts can just ignore the new input. Doesn't work in reverse - we can't stop
# using inputs willy nilly - but such is life.

import time
from pyqt_helpers.circle_button import CircleButton

class TestRoutine:
    def __init__(self, **kwargs):

        # an example of how **kwargs works
        print("kwargs: ")
        for key, value in kwargs.items():
            print(f"key: {key}, value: {value}")
        print("-----")

        try:
            self.buttons = kwargs["buttons"]
        except KeyError:
            self.buttons = []

        self.i = 0

    def run_routine(self):
        # while True:
        #     print(self.i)
        #     time.sleep(1)
        #     self.i += 1

        for button in self.buttons:
            # if type(button) == CircleButton:
            # print("click")
            button.click()
            time.sleep(0.5)

def run(**kwargs):
    myRoutine = TestRoutine(**kwargs)
    myRoutine.run_routine()

if __name__ == "__main__":
    # an example of how **kwargs works
    run(buttons = ["button1, button2"])