__author__ = 'Tom Van den Eede'
__copyright__ = 'Copyright 2019, Palette2 Splicer Post Processing Project for Simplify 3D'
__credits__ = ['Tom Van den Eede']
__license__ = 'GPLv3'
__maintainer__ = 'Tom Van den Eede'
__email__ = 't.vandeneede@pandora.be'

try:
    # p ython version 2.x
    import Tkinter as tkinter
    import ttk
    import tkMessageBox
except ImportError:
    # python version 3.x
    import tkinter
    from tkinter import ttk
    from tkinter import messagebox as tkMessageBox

import os
import sys
from platform import system

import p2pp.variables as v
import version

platformD = system()

last_pct = -1

errors = 0
warnings = 0


def completed():
    progressbar.destroy()
    if errors or warnings:
        text = "Completed with {} errors and {} warnings".format(errors, warnings)
        color = 'red'
    else:
        text = "Competed without errors"
        color = '#005000'
    progress_field = tkinter.Label(infosubframe , text=text, font=boldfont, foreground=color,  background="#808080")
    progress_field.grid(row=3, column=2, sticky="ew")


color_count = 0
previous_progress = -1

def setprogress(x):
    global previous_progress
    progress.set(x)
    if  not x == previous_progress:
        mainwindow.update()
        previous_progress = x


def create_logitem(text, color="black", force_update=True, position=tkinter.END):
    text = text.strip()
    global color_count
    color_count += 1
    tagname = "color"+str(color_count)
    loglist.tag_configure(tagname, foreground=color)
    loglist.insert(position, "  " + text + "\n", tagname)
    if force_update:
        mainwindow.update()


def error(text):
    global errors
    errors += 1
    create_logitem(text, color='red')

def warning(text):
    global warnings
    warnings += 1
    create_logitem(text, color='blue')

def comment(text):
    create_logitem(text, color='black')

def create_emptyline():
    create_logitem('')

def close_window():
    mainwindow.destroy()

def close_button_enable():
    closebutton.config(state=tkinter.NORMAL)
    mainwindow.mainloop()


def center(win, width, height):
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (width // 2)  # center horizontally in screen
    y = (win.winfo_screenheight() // 2) - (height // 2)  # center vertically in screen
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    win.minsize(width, height)
    win.maxsize(width, height)


def set_printer_id(text):
    printerid.set(text)
    mainwindow.update()


def setfilename(text):
    filename.set(text)
    mainwindow.update()


def user_error(header, body_text):
    tkMessageBox.showinfo(header, body_text)


def ask_yes_no(title, message):
    return (tkMessageBox.askquestion(title, message).upper()=="YES")


def log_warning(text):
    v.process_warnings.append(";" + text)
    create_logitem(text, "red")

def configinfo():
    global infosubframe
    infosubframe.destroy()
    infosubframe = tkinter.Frame(infoframe, border=3, relief='sunken', background="#909090")
    infosubframe.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
    tkinter.Label(infosubframe, text='CONFIGURATION  INFO', font=boldfontlarge, background="#909090").pack(side=tkinter.TOP, expand=1)

    tkinter.Label(infosubframe, text="P2PP/S3D Version "+version.Version+"\n", font=boldfont, background="#909090").pack( side=tkinter.BOTTOM)


mainwindow = tkinter.Tk()
mainwindow.title("Palette2 Post Processing for Simplify-3D")
center(mainwindow, 800, 600)

# if platformD == 'Windows':
#     logo_image = os.path.dirname(sys.argv[0]) + '\\favicon.ico'
#     mainwindow.iconbitmap(logo_image)
#     mainwindow.update()

mainwindow['padx'] = 10
mainwindow['pady'] = 10
boldfontlarge = 'Helvetica 30 bold'
normalfont = 'Helvetica 16'
boldfont = 'Helvetica 16 bold'
fixedfont = 'Courier 14'
fixedsmallfont = 'Courier 12'

# Top Information Frqme
infoframe = tkinter.Frame(mainwindow, border=3, relief='sunken', background="#808080")
infoframe.pack(side=tkinter.TOP, fill=tkinter.X)

# logo
logoimage = tkinter.PhotoImage(file=os.path.dirname(sys.argv[0]) + "/appicon.ppm")
logofield = tkinter.Label(infoframe, image=logoimage)
logofield.pack(side=tkinter.LEFT, fill=tkinter.Y)

infosubframe = tkinter.Frame(infoframe, background="#808080")
infosubframe.pack(side=tkinter.LEFT, fill=tkinter.X)
infosubframe["padx"] = 20

# file name display
tkinter.Label(infosubframe, text='Filename:', font=boldfont, background="#808080").grid(row=0, column=1, sticky="w")
filename = tkinter.StringVar()
setfilename("-----")
tkinter.Label(infosubframe, textvariable=filename, font=normalfont, background="#808080").grid(row=0, column=2,
                                                                                               sticky="w")

# printer ID display
printerid = tkinter.StringVar()
set_printer_id("-----")

tkinter.Label(infosubframe, text='Printer ID:', font=boldfont, background="#808080").grid(row=1, column=1, sticky="w")
tkinter.Label(infosubframe, textvariable=printerid, font=normalfont, background="#808080").grid(row=1, column=2,
                                                                                                sticky="w")


tkinter.Label(infosubframe, text="P2PP/S3D V", font=boldfont, background="#808080").grid(row=2, column=1,
                                                                                            sticky="w")
tkinter.Label(infosubframe, text=version.Version, font=normalfont, background="#808080").grid(row=2, column=2,
                                                                                              sticky="w")

# progress bar
progress = tkinter.IntVar()
progress.set(0)
tkinter.Label(infosubframe, text='Progress:', font=boldfont, background="#808080").grid(row=3, column=1, sticky="w")
progressbar = ttk.Progressbar(infosubframe ,orient='horizontal', mode='determinate', length=500, maximum=100, variable=progress)
progressbar.grid(row=3, column=2,  sticky='ew')


# Log frame
logframe = tkinter.Frame(mainwindow, border=3, relief="sunken")
logframe.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

loglistscroll = tkinter.Scrollbar(logframe, orient=tkinter.VERTICAL)
loglistscroll.pack(side='right', fill=tkinter.Y)

loglist = tkinter.Text(logframe, yscrollcommand=loglistscroll.set, font=fixedsmallfont)
loglist.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=1)

loglistscroll.config(command=loglist.yview)

# Button frame
buttonframe = tkinter.Frame(mainwindow, border=1, relief="sunken")
buttonframe.pack(side=tkinter.BOTTOM, fill=tkinter.X)

closebutton = tkinter.Button(buttonframe, text="Exit", state=tkinter.DISABLED, command=close_window)
closebutton.pack(side=tkinter.RIGHT, fill=tkinter.X, expand=1)


mainwindow.rowconfigure(0, weight=1)
mainwindow.rowconfigure(1, weight=1000)
mainwindow.rowconfigure(2, weight=1)

mainwindow.lift()
mainwindow.attributes('-topmost', True)
mainwindow.after_idle(mainwindow.attributes, '-topmost', False)
mainwindow.update()

