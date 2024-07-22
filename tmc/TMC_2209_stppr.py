# Write your code here :-)
import digitalio
import board
import time

class TMC2209_stp_dir:
    def __init__(self, DIR, STEP, EN, idx, dir_reversed):
        self.dir_multiplier = 1
        self.name = idx
        self._dir = digitalio.DigitalInOut(DIR)
        self._step = digitalio.DigitalInOut(STEP)
        self._en = digitalio.DigitalInOut(EN)

        self._dir.direction = digitalio.Direction.OUTPUT
        self._step.direction = digitalio.Direction.OUTPUT
        self._en.direction = digitalio.Direction.OUTPUT

        self._dir.value = False
        self._step.value = False
        self._en.value = True
        self.isEnabled = False
        if dir_reversed:
            self.dir_multiplier = -1

    def enable(self):
        self._en.value = False
        self.isEnabled = True

    def disable(self):
        self._en.value = True
        self.isEnabled = False

    def step(self, fwd = True):
        self._dir.value = fwd
        # Make jitter
        self._step.value = True
        time.sleep(1e-6)
        self._step.value = False

    def move_blocking(self, steps, speed = 200.0):
        self._dir.value = (self.dir_multiplier*steps>=0) # if negative, then move backwards
        time_per_step = 1/speed
        for count in range(abs(steps)):
            self._step.value = True
            time.sleep(1e-6)
            self._step.value = False
            time.sleep(time_per_step)

    def deinit(self):
        self._dir.deinit()
        self._step.deinit()
        self._en.deinit()

        self._dir = None
        self._step = None
        self._en = None

    def __enter__(self):
        return self

    def __exit__(self):
        self.deinit()
