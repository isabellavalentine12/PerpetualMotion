# ////////////////////////////////////////////////////////////////
# //                     IMPORT STATEMENTS                      //
# ////////////////////////////////////////////////////////////////

import math
import sys
import time
import threading

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import *
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from kivy.config import Config
from kivy.core.window import Window
from pidev.kivy import DPEAButton
from pidev.kivy import PauseScreen
from time import sleep
import spidev
import os
import RPi.GPIO as GPIO
from pidev.stepper import stepper
from Slush.Devices import L6470Registers
from pidev.Cyprus_Commands import Cyprus_Commands_RPi as cyprus
spi = spidev.SpiDev()
from threading import Thread


# ////////////////////////////////////////////////////////////////
# //                      GLOBAL VARIABLES                      //
# //                         CONSTANTS                          //
# ////////////////////////////////////////////////////////////////
ON = False
OFF = True
HOME = True
TOP = False
OPEN = False
CLOSE = True
BLUE = .180, 0.188, 0.980, 1
USEDBLUE = .180, 0.188, 0.980, .5
YELLOW = 0.917, 0.796, 0.380, 1
USEDYELLOW = 0.917, 0.796, 0.380, .5
DEBOUNCE = 0.1
INIT_RAMP_SPEED = 150
RAMP_LENGTH = 725


# ////////////////////////////////////////////////////////////////
# //            DECLARE APP CLASS AND SCREENMANAGER             //
# //                     LOAD KIVY FILE                         //
# ////////////////////////////////////////////////////////////////
class MyApp(App):
    def build(self):
        self.title = "Perpetual Motion"
        return sm

Builder.load_file('main.kv')
Window.clearcolor = (.1, .1,.1, 1) # (WHITE)

cyprus.initialize()
cyprus.open_spi()

# ////////////////////////////////////////////////////////////////
# //                    SLUSH/HARDWARE SETUP                    //
# ////////////////////////////////////////////////////////////////
sm = ScreenManager()
s0 = stepper(port=0, micro_steps=32, hold_current=20, run_current=20, accel_current=20, deaccel_current=20,
             steps_per_unit=200, speed=3)

# ////////////////////////////////////////////////////////////////
# //                       MAIN FUNCTIONS                       //
# //             SHOULD INTERACT DIRECTLY WITH HARDWARE         //
# ////////////////////////////////////////////////////////////////
	
# ////////////////////////////////////////////////////////////////
# //        DEFINE MAINSCREEN CLASS THAT KIVY RECOGNIZES        //
# //                                                            //
# //   KIVY UI CAN INTERACT DIRECTLY W/ THE FUNCTIONS DEFINED   //
# //     CORRESPONDS TO BUTTON/SLIDER/WIDGET "on_release"       //
# //                                                            //
# //   SHOULD REFERENCE MAIN FUNCTIONS WITHIN THESE FUNCTIONS   //
# //      SHOULD NOT INTERACT DIRECTLY WITH THE HARDWARE        //
# ////////////////////////////////////////////////////////////////
class MainScreen(Screen):
    version = cyprus.read_firmware_version()
    staircaseSpeedText = '0'
    rampSpeed = INIT_RAMP_SPEED
    staircaseSpeed = 40
    gatecount = 0
    staircount = 0

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.initialize()

    def toggleGate(self):
        print("Open and Close gate here")
        if self.gatecount%2 == 0:
            self.gate.disabled = True
            self.gate.text = "Close Gate"
            self.ids.gate.color = USEDBLUE
            cyprus.set_servo_position(2, .6)  # port 5
            self.gatecount += 1
            self.gate.disabled = False
        else:
            self.gate.disabled = True
            self.gate.text = "Open Gate"
            self.ids.gate.color = USEDBLUE
            cyprus.set_servo_position(2, 0)  # port 5
            self.gatecount += 1
            self.gate.disabled = False
        self.ids.gate.color = BLUE

    def threadToggleGate(self):
        Thread(target=self.toggleGate, daemon=True).start()
        print('using gate thread')

    def toggleStaircase(self):
        if self.staircount%2 == 0:
            self.staircase.disabled = True
            self.staircase.text = "Staircase Off"
            self.ids.staircase.color = USEDBLUE
            cyprus.set_pwm_values(1, period_value=100000, compare_value=50000, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            self.staircount += 1
            self.ids.staircase.color = BLUE
            self.staircase.disabled = False
        else:
            self.staircase.disabled = True
            self.staircase.text = "Staircase On"
            self.ids.staircase.color = USEDBLUE
            cyprus.set_pwm_values(1, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            self.staircount += 1
            self.ids.staircase.color = BLUE
            self.staircase.disabled = False

    def toggleRamp(self):
        self.ramp.disabled = True
        self.ids.ramp.color = USEDBLUE
        s0.start_relative_move(29)
        while s0.is_busy() and s0.get_position_in_units() < 29:
           sleep(.1)
        s0.softStop()
        sleep(1)
        s0.start_relative_move(-29)
        while s0.is_busy() and s0.get_position_in_units() > 0:
            sleep(.1)
        s0.softStop()
        self.ramp.disabled = False
        self.ids.ramp.color = BLUE

    def threadToggleRamp(self):
        Thread(target=self.toggleRamp, daemon=True).start()
        print('using thread')

    def auto(self):
        print("Run through one cycle of the perpetual motion machine")
        s0.start_relative_move(29)
        while s0.is_busy():
           sleep(.1)
        s0.softStop()
        sleep(1)
        s0.start_relative_move(-29)
        print("Turn on and off staircase here")
        cyprus.set_pwm_values(1, period_value=100000, compare_value=100000, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
        sleep(8)
        cyprus.set_pwm_values(1, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
        sleep(1)
        print("Open and Close gate here")
        cyprus.set_servo_position(2, .75)  # port 5
        sleep(5)
        
    def setRampSpeed(self, speed):
        print("Set the ramp speed and update slider text")
        #self.rampSpeed.value = speed

        
    def setStaircaseSpeed(self, speed):
        print("Set the staircase speed and update slider text")
        
    def initialize(self):
        sleep(1)
        cyprus.set_pwm_values(1, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
        sleep(1)
        s0.go_until_press(0, 3*6400)
        while s0.is_busy():
           sleep(.1)
        s0.set_as_home()
        cyprus.set_servo_position(2, 0)  # port 5
        sleep(5)

        print("Close gate, stop staircase and home ramp here")
        print(self.version)

    def resetColors(self):
        self.ids.gate.color = BLUE
        self.ids.staircase.color = BLUE
        self.ids.ramp.color = BLUE
        self.ids.auto.color = YELLOW
    
    def quit(self):
        print("Exit")
        MyApp().stop()

sm.add_widget(MainScreen(name = 'main'))

# ////////////////////////////////////////////////////////////////
# //                          RUN APP                           //
# ////////////////////////////////////////////////////////////////

MyApp().run()
cyprus.close_spi()
