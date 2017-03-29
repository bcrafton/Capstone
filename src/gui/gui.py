#!/usr/bin/python
# -*- coding: utf-8 -*-

import Tkinter
import tkFileDialog
from Tkinter import *
from ttk import *
import ctypes
import nmap


class Example(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)

        self.parent = parent
        self.ips = {}
        self.init_ui()

        self.server = ctypes.CDLL('../server/server.so')
        status = self.server.start()
        print "server start status: " + str(status)

    def init_ui(self):
        self.parent.title("Media Player")
        self.style = Style()
        self.style.theme_use("default")

        self.ips = self.get_ips()
        self.squares = []

        selections_frame = Frame(self, height=20)
        selections_frame.pack(fill=X)

        ips_frame = Frame(self, height=100)
        ips_frame.pack(fill=X)

        button_frame = Frame(self, borderwidth=1)
        button_frame.pack(fill=BOTH, expand=True)

        self.pack(fill=BOTH, expand=True)

        song_label = Label(selections_frame, text="Song Location:", width=13)
        song_label.pack(side=LEFT, padx=5, pady=5)

        song_var = Tkinter.StringVar()
        song_location = Entry(selections_frame, width=40, textvariable=song_var)
        song_location.pack(side=LEFT, fill=X, pady=5)

        song_button = Button(selections_frame, text="...", width=3, command=lambda: self.set_song_path(song_var))
        song_button.pack(side=RIGHT, padx=5, pady=5)

        ips_label = Label(ips_frame, text="Available Pis: ", width=13)
        ips_label.pack(side=LEFT, padx=5, pady=5)

        self.canvas = Canvas(ips_frame, width=20, height=100)
        self.canvas.pack(side=RIGHT)
        y0 = 0

        for ip in self.ips:
            var = Tkinter.BooleanVar()
            c = Checkbutton(ips_frame, text=ip, variable=var,
                            command=lambda: self.update_devices())
            c.pack(anchor=N)
            var.set(True)
            self.ips[ip] = var

            y1 = 10 + y0
            self.squares.append(self.canvas.create_rectangle(10, y0, 0, y1, fill="red"))
            y0 += 20

        close_button = Button(self, text="Close", command=self.quit)
        close_button.pack(side=RIGHT, padx=5, pady=5)

        update_ips_button = Button(self, text="Update IPs", command=lambda: self.update_devices())
        update_ips_button.pack(side=RIGHT, padx=5, pady=5)

        stop_button = Button(self, text="Stop", command=lambda: self.stop())
        stop_button.pack(side=RIGHT, padx=5, pady=5)

        play_button = Button(self, text="Play", command=lambda: self.play())
        play_button.pack(side=RIGHT, padx=5, pady=5)

    def play(self):
        status = self.server.play()
        print "play status: " + str(status)

    def stop(self):
        status = self.server.stop()
        print "stop status: " + str(status)

    def get_ips(self):
        """ Get the ip addresses then return them as a list """
        print "Finding all connected nodes..."
        ip = '10.0.0.0/24'
        arguments = '-sP'

        nm = nmap.PortScanner()
        nm.scan(ip, arguments=arguments)

        ip_list = {}
        for h in nm.all_hosts():
            if 'mac' in nm[h]['addresses'] and 'B8:27:EB' in nm[h]['addresses']['mac'] and 'ipv4' in nm[h]['addresses']:
                ip_list[nm[h]['addresses']['ipv4']] = True
        print ip_list
        return ip_list

    def set_song_path(self, song_var):
        location = tkFileDialog.askopenfilename(initialdir='../../sound_files')
        song_var.set(location)
        status = self.server.set_song(ctypes.c_char_p(location))
        print "set song status: " + str(status)

    def update_devices(self):
        i = 0
        for ip in self.ips:
            print ip, self.ips[ip].get()
            if self.ips[ip].get() is True:
                self.update_color(-1, self.squares[i])
                status = self.server.set_device(ctypes.c_char_p(ip))
            else:
                self.update_color(-1, self.squares[i])
                status = self.server.kill_device(ctypes.c_char_p(ip))
            self.update_color(status, self.squares[i])
            print "set device status: " + str(status)
            i += 1

    def update_color(self, status, item):
        if status == -1:
            self.canvas.itemconfig(item, fill="yellow")
        elif status == 0:
            self.canvas.itemconfig(item, fill="green")
        else:
            self.canvas.itemconfig(item, fill="red")


def main():
    root = Tk()
    root.geometry("500x170+300+300")
    app = Example(root)
    root.mainloop()


if __name__ == '__main__':
    main()
