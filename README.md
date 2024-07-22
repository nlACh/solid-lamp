This is a WIP arm like thingy built with V slot aluminium extrusions. The motion is controlled using NEMA 17 and 23 steppers and a [BigTreeTech SKR Pico] (https://github.com/bigtreetech/SKR-Pico) with RP2040 MCU running circuitpython.
There are 4 TMC2209 stepper drivers on the board. Currently, the drivers are run in a rudimentary STEP-DIR config with UART config in the works...
The stepper libraries are adapted from 

<https://github.com/Chr157i4n/TMC2209_Raspberry_Pi>

and

<https://github.com/kjk25/TMC2209_ESP32>

There's a rotary encoder attached to the board and a push button