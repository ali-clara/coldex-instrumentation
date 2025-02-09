import time

class TestRoutine:
    def __init__(self):
        self.started = False
        self.running = False
        self.paused = False
        
        self.i = 0

    def run_routine(self):
        while True:
            print(self.i)
            time.sleep(1)
            self.i += 1
        
myRoutine = TestRoutine()

def run():
    myRoutine.run_routine()