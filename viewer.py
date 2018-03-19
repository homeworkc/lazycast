#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#
# tkinter example for VLC Python bindings
# Copyright (C) 2015 the VideoLAN team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.

import vlc
import sys
import ttk
import socket  
import binascii

import Tkinter as Tk


# import standard libraries
import os
import threading
from threading import Thread
import time
import platform


    
class Setres(Thread):
    def __init__(self, playerself):
        Thread.__init__(self)
        self.playerself = playerself
        self.oldpxy=(0,0)
    def run(self):
        while 1:
            pxy=vlc.libvlc_video_get_size(self.playerself.player,0)
            (px,py)=pxy
            if(pxy!=self.oldpxy):
                print str(px)+'x'+str(py)
                self.playerself.parent.geometry(str(px)+'x'+str(py)) 
                
                self.oldpxy=pxy
            time.sleep(0.2)

class Player(Tk.Frame):
    """The main window has to deal with events.
    """
    inputreport =b"\x00\x00\x00\x14\x02\x00 \
	\x06\x01\x00\x00\x00\x00\x00\x00\x00\x00 \
	\x00\x00\x00\x00"

    def leftclick(caller,event):
        print "clicked at", event.x, event.y
    def middleclick(caller,event):
        print "clicked at", event.x, event.y
    def rightclick(caller,event):
        print "clicked at", event.x, event.y
    def motion(caller,event):
        print "motion: ", event.x, event.y

    
    def __init__(self, parent, title=None):
        Tk.Frame.__init__(self, parent)
        self.parent = parent

        self.parent.title(title)
        self.parent.geometry("1280x800+0+0") 
        self.parent.resizable(0, 0)

        self.player = None
        self.videopanel = ttk.Frame(self.parent)
        self.canvas = Tk.Canvas(self.videopanel).pack(fill=Tk.BOTH,expand=1)
        self.videopanel.pack(fill=Tk.BOTH,expand=1)

        
        


        self.Instance = vlc.Instance()
        self.player = self.Instance.media_player_new()

        self.parent.update()
        self.Media = self.Instance.media_new("rtp://0.0.0.0:1028")
        self.player.set_media(self.Media)
        self.player.set_xwindow(self.GetHandle()) # this line messes up windows
        # Try to launch the media, if this fails display an error message
        if self.player.play() == -1:
            self.errorDialog("Unable to play.")
        
        print binascii.hexlify(self.inputreport)
        self.inputreport[2]=b"x00"
        print binascii.hexlify(self.inputreport)
        


        portnum = int(sys.argv[1])
        print portnum
        controlsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('192.168.101.80', portnum)
        controlsock.connect(server_address)


        self.parent.bind("<Button-1>", self.leftclick)
        self.parent.bind("<Button-2>", self.middleclick)
        self.parent.bind("<Button-3>", self.rightclick)
        self.parent.bind("<Motion>", self.motion)

        self.setres=Setres(self)
        self.setres.start()

    def GetHandle(self):
        return self.videopanel.winfo_id()



    def errorDialog(self, errormessage):
        """Display a simple error dialog.
        """
        Tk.tkMessageBox.showerror(self, 'Error', errormessage)

    

def Tk_get_root():
    if not hasattr(Tk_get_root, "root"): #(1)
        Tk_get_root.root= Tk.Tk()  #initialization call is inside the function
    return Tk_get_root.root

def _quit():
    print("_quit: bye")
    root = Tk_get_root()
    root.quit()     # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
                    # Fatal Python Error: PyEval_RestoreThread: NULL tstate
    os._exit(1)

if __name__ == "__main__":
    # Create a Tk.App(), which handles the windowing system event loop
    root = Tk_get_root()
    root.protocol("WM_DELETE_WINDOW", _quit)

    player = Player(root, title="lazycast")
    # show the player window centred and run the application
    root.mainloop()
