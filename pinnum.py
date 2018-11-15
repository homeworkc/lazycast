#!/usr/bin/env python2

from Tkinter import *
import os
import sys

wps_pin = sys.argv[1]

print(os.getpid())
sys.stdout.flush()

top = Tk()
top.title('WPS Pin')

# desktop (1920-48*8, 1080-100-48)
top.geometry("+1590+932")

w = Label(top, text=wps_pin, fg="red", font = "DejaVuSans 48")
w.pack()

top.mainloop()
