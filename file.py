#!/usr/bin/env python3
# coding=UTF-8
from tkinter import filedialog
from tkinter import Tk
import pathlib
import os

# import os
def fullpathname(filename):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = pathlib.Path(__file__).parent #os.path.abspath(".")
    return pathlib.Path.joinpath(
                                # pathlib.Path(__file__).parent,
                                base_path,
                                filename)
def askfilename(self):
    print('Apparently there is no last lift file url; asking...')
    text=(_("Please select a LIFT lexicon file to check"))
    tkinter.Label(self.status, text=text).grid(column=0,
    row=0)
    return lift() #this is a string
def getfilenamedir(filename):
    return pathlib.Path(filename).parent
def getimagesdir(filename):
    dir=pathlib.Path.joinpath(getfilenamedir(filename),'images')
    if not os.path.exists(dir):
        os.mkdir(dir)
    return dir
def getaudiodir(filename):
    dir=pathlib.Path.joinpath(getfilenamedir(filename),'audio')
    # print("Looking for",dir)
    if not os.path.exists(dir):
        # print(dir,"not there, making it!")
        os.mkdir(dir)
    # exit()
    return dir
def exists(file):
    if os.path.exists(file):
        return True
    else:
        return False
def remove(file):
    if exists(file):
        os.remove(file)
    # else:
    #     print(_("Tried to remove {}, but it does not exist.").format(file))
def getdiredurl(dir,filename):
    return pathlib.Path.joinpath(dir,filename)
# def getimagefilename(*args):
#     wavfilename=''
#     for arg in args:
#         print(type(arg),type(args))
#         wavfilename+=arg
#         if args.index(arg) < len(args):
#             wavfilename+='_'
#     # wavfilename+='.wav' #add this elsewhere
#     return pathlib.Path.joinpath(wavfilename)
def getlangnamepaths(filename, langs):
    #lift=getfilename()
    output={}
    wsdir=pathlib.Path.joinpath(pathlib.Path(filename).parent, 'WritingSystems')
    for lang in langs:
        #filename=pathlib.Path.joinpath(wsdir, lang +'.ldml')
        output[lang]=str(pathlib.Path.joinpath(wsdir, lang +'.ldml'))
        #print(filename)
    #print(output)
    #exit()
    return output
def getinterfacelang(self):
    """This is called by the mainapplication class before anything else happens,
    including setting the ui interface language (that's what this enables). So
    I haven't figured out a way to translate the strings here, and I trust that
    will be OK."""
    self.interfacelangs=[{'code':'fr','name':'Français'},
                            {'code':'en','name':'English'},
                            {'code':'fub','name':'Fulfulde'}
                            ]
    try:
        import ui_lang
        #print("lift_url.py imported fine.")
        try:
            self.interfacelang=ui_lang.interfacelang
            #print('filename: '+filename)
        except:
            print("Didn't find ui_lang.interfacelang") #Sorry, no translation!
            self.interfacelang=None
    except:
        print("Didn't find ui_lang.py") #Sorry, no translation!
        self.interfacelang=None
def writeinterfacelangtofile(lang):
    file=pathlib.Path.joinpath(pathlib.Path(__file__).parent, "ui_lang.py")
    f = open(file, 'w', encoding='utf-8') # to create writeable file (deleting existing), "a") #to append
    f.write('interfacelang="'+lang+'"'+'\n')
    f.close()
def getfilename():
    try:
        import lift_url
        #print("lift_url.py imported fine.")
        try:
            filename=lift_url.filename
            #print('filename: '+filename)
        except:
            return lift()
    except:
        return lift()
    try:
        return filename
    except:
        text=(_("Sorry, you don't seem to have selected a LIFT lexicon file."))
        tkinter.Label(self.status, text=text).grid(column=0,row=1)
        #window.
        self.window.wait_window(window=self.window)
        self.destroy()
def lift():
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    filename=filedialog.askopenfilename(initialdir = "$HOME",title = "Select file",)
    # print(filename)
    if filename is (): #Try one more time...
        print("Sorry, not sure what's wrong; trying again.")
        filename=filedialog.askopenfilename(initialdir = "$HOME",title = "Select file",)
        if filename is (): #still, then give up.
            print("Sorry, not sure what's wrong; giving up.")
            # return None
    print(filename)
    """Assuming this file is still in lift/, this works. Once out,
    remove a parent"""
    file=pathlib.Path.joinpath(pathlib.Path(__file__).parent, "lift_url.py")
    f = open(file, 'w', encoding='utf-8') # to create writeable file (deleting existing), "a") #to append
    f.write('filename="'+filename+'"'+'\n')
    f.close()
    return filename
    #print (filename)
    #saveasfilename =  filedialog.asksaveasfilename(initialdir = "$HOME",title = "Select file to save as",)
    #print (saveasfilename)

if __name__ == "__main__":
    import sys
    import ws_environment
    import datetime
    import shutil
    import globalvariables
    wsfolder=ws_environment.getwsfolder()
    langdir=ws_environment.getlangdir()
    xyz=globalvariables.xyz
    def usage():
        print("usage for one entry:")
        print(" python3 " + pathlib.Path(__file__).name + " <forms|ids|tones|prontones|glosses|gloss2s|plurals|pses|all|cards|lxnglosses> <lift file> <guid>")
        print("usage for all entries in lift file:")
        print(" python3 " + pathlib.Path(__file__).name + " <forms|ids|tones|prontones|glosses|gloss2s|plurals|pses|all|cards|lxnglosses|ids2testN|ids2testV> <lift file>")
        exit() #if there is a problem with the usage, we don't want to keep going...
    def liftori():
        global wsfolder
        global xyz
        return pathlib.Path.joinpath(wsfolder, xyz, xyz +'.lift')
    def liftstr():
        global wsfolder
        global xyz
        return str(pathlib.Path.joinpath(wsfolder, xyz, xyz +'.lift'))
    def liftdirstr():
        global wsfolder
        global xyz
        return str(pathlib.Path.joinpath(wsfolder, xyz))

    def baklift():
        global wsfolder
        global xyz
        now=datetime.datetime.now()
        return pathlib.Path.joinpath(wsfolder, xyz, xyz + '.lift' + str(now))
    lift=lift()
    baklift=baklift()

    #Varify that these files and folders exist as appropriate:
    if wsfolder.exists():
        print("WeSay Folder is " + str(wsfolder))
    else:
        print("Sorry, problem with non-existent WeSay folder " + str(wsfolder))
        usage()
    if langdir.exists():
        print("Lang Directory is " + str(langdir))
    else:
        print("Sorry, problem with non-existent language directory " + str(langdir))
        usage()
    if lift.exists():
        print("Lift file is " + str(lift))
    else:
        print("Sorry, problem with non-existent lift file " + str(lift))
        usage()
    if baklift.exists():
        print("Sorry, lift file backup already exists " + str(baklift))
        usage()
    else:
        print("Lift file backup is " + str(baklift))


    def bak():
        now=datetime.datetime.now()
        print("Running at " + str(now))
        global lift
        global baklift
        #lift=lift()
        #baklift=baklift()
        shutil.copyfile(lift, baklift)
        print(lift, "backed up.")
    bak() #do I want this running each time anything happens?
