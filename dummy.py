#!/usr/bin/env python3
# coding=UTF-8

class App(object):
    def __init__(self,program_dict=None):
        super().__init__()
        self.dummy=True #lets ui.Root distinguish this from the real App
        self.name='tkinter UI module'
        self.url='https://github.com/kent-rasmussen/azt'
        self.Email='kent_rasmussen@sil.org'
        self.theme='Kim'
        for k in program_dict:
            setattr(self,k,program_dict[k])
        
class TaskChooser(object):
    def __init__(self):
        super().__init__()
        self.filename='test.lift'

        
    