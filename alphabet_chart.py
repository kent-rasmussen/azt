#!/usr/bin/env python3
# coding=UTF-8
"""This module controls manipulation of alphabet charts from LIFt databases"""
import os, sys
import logsetup
log=logsetup.getlog(__name__)
logsetup.setlevel('INFO',log) #for this file
log.info(f"Importing {__name__}")
import file
import lift
import ui_tkinter as ui
import pyautogui

class DraggableLabel(ui.Label):
    def __init__(self, parent, *args, **kwargs):
        kwargs['draggable']=True #this provides dnd methods
        super().__init__(parent, *args, **kwargs)
class DroppableLabel(ui.Label):
    """This contains exactly one method which has to be customized.
    Super calls this from ui.Label (as part of its dnd_commit), so this
    can't be brought into the larger class with just a kwarg"""
    def dnd_commit(self, target, event):
        if target:
            # print(f"Dropped to index {self.index}")
            target.dragged_to.set(self.index)
    def __init__(self, parent, *args, **kwargs):
        kwargs['droppable']=True #this provides dnd_accept
        super().__init__(parent, *args, **kwargs)
class OrderAlphabet(ui.Window):
    """This allows users both to order what has been analyzed already, and
    select a picturable word for each grapheme"""
    def print_chart(self):
        log.info("Calling print_chart")
        region=(
            self.frame.winfo_x()+self.winfo_x(),
            self.frame.winfo_y()+self.winfo_y(),
            self.frame.winfo_width(),
            self.frame.winfo_height()
        )
        self.screenshot=pyautogui.screenshot(region=region)
        filename=f"AlpabetChart[{self.db.analang}]x{self.ncolumns}.pdf"
        self.screenshot.save(file.getdiredurl(self.db.reportdir,filename))
    def select_example(self,glyph):
        self.withdraw()
        w=SelectFromPicturableWords(self,self.db,glyph)
        w.wait_window(w)
        if hasattr(w,'selected'):
            self.exids[glyph]=w.selected #.id
            self.exobjs[glyph]=self.db.sensedict[w.selected]
            self.save_settings()
            for k,v in self.get_kwargs(glyph).items():
                self.buttons[glyph].b[k]=v
            # log.info(f"{self.exids=}")
        self.deiconify()
        self.update_idletasks()
    def get_kwargs(self,g):
        if self.exobjs[g] is not None:
            return {'text':self.exobjs[g].entry.lcvalue(),
                    'image':self.exobjs[g].image.scaled,
                }
        elif self.exids[g]:
            log.error("self.exids is there, but self.exobjs isn't? "
                    f"{self.exobjs=} {self.exids=}")
        else:
            return {'text':"?"}
    def column_config(self,change,event=None):
        self.ncolumns+=change
        # log.info(f"Setting {self.ncolumns} columns")
        if self.ncolumns == max(list(self.ncolopts)):
            # log.info(f"Maxed out at {self.ncolumns} columns")
            self.config_buttons[_("More Columns")].grid_remove()
        else:
            self.config_buttons[_("More Columns")].grid()
        if self.ncolumns == min(self.ncolopts):
            # log.info(f"Minned out at {self.ncolumns} columns")
            self.config_buttons[_("Fewer Columns")].grid_remove()
        else:
            self.config_buttons[_("Fewer Columns")].grid()
        self.reflow_chart()
    def reflow_chart(self):
        self.save_settings()
        if set(self.buttons).issuperset(self.show_order):
            for n,g in enumerate(self.show_order):
                self.buttons[g].grid(row=n//self.ncolumns,
                                    column=n%self.ncolumns)
            for g in self.buttons.keys()-set(self.show_order):
                self.buttons[g].grid_forget()
            self.chart.update()
        else:
            self.show_chart() #If buttons are missing, restart.
            return
    def alphabet_config(self):
        """This is only run once, on init"""
        self.config_columns=25
        self.config_config=ui.Frame(self.outsideframe,c=2,r=0,sticky='nw')
        self.config_buttons={}
        for text, command in [(_("(un)hide"),self.hide_letters),
                            (_("reorder"),self.reorder_alphabet),
                            (_("re-alphabetize"),self.alphabetize_order)
                        ]:
            self.config_buttons[text]=ui.Button(self.config_config,
                                            text=text,
                                            command=command,
                                            r=self.config_config.grid_size()[1])
        self.reorder_alphabet()
    def grid_by_n(self,n):
        return n//self.config_columns, n%self.config_columns
    def make_glyph_label(self,glyph):
        """This is needed because I need to pass a variable with a trace calling
        a method here"""
        l=ui.Label(self.dropframes[self.order.index(glyph)],
                    text=glyph,
                    draggable=True,c=1)
        l.dragged_to=ui.IntVar(name=glyph)
        l.dragged_to.trace_add('write', self.update_order)
        return l
    def make_frame_and_droppable(self):
        """These are only done once, on setup"""
        n=len(self.config_order.winfo_children())
        r,c=self.grid_by_n(n)
        f=ui.Frame(self.config_order, r=r, c=c, sticky='news')
        self.dropframes.append(f)
        l=DroppableLabel(self.dropframes[n], text=' ', sticky='news')
        l.index=n
        self.droppables.append(l)
        return f,l
    def reorder_alphabet(self):
        try:
            self.config_buttons[_('reorder')].grid_remove()
            self.config_buttons[_("(un)hide")].grid()
            self.config_buttons[_("re-alphabetize")].grid()
            self.config_hiding.destroy()
        except:
            pass
        self.config_order=ui.Frame(self.outsideframe,c=1,r=0)
        self.droppables=[]
        self.draggables=[]
        self.dropframes=[]
        for i in self.order:
            self.make_frame_and_droppable()
            self.draggables.append(self.make_glyph_label(i))
        self.make_frame_and_droppable() #one more, for the end
    def update_order(self,glyph,index,mode):
        """Figure out what to do with glyphs pushed to the end"""
        index_dest=self._root().getvar(name=glyph)-1 #be inclusive
        index_orig=self.order.index(glyph)
        # pull from the max first, put to the min first.
        if index_orig>index_dest: #moving down/left
            to_move=self.order[index_orig:index_dest:-1]
        else: #moving right, don't move the dropped-to indexed glyph
            to_move=self.order[index_dest:index_orig-1:-1]
        # log.info(f"Moving from index {index_orig} to {index_dest} "
        #         "({len(to_move)} total)")
        indexes_to_move=[self.order.index(i) for i in to_move]
        storage={self.order[i]:self.draggables.pop(i) for i in indexes_to_move}
        # log.info(f"Going to move {to_move} ({index_dest}-{index_orig})")
        # log.info(f"{len(storage)} stored labels: {storage.keys()}")
        self.order.remove(glyph)
        if index_orig>index_dest: #moving down/left
            self.order.insert(index_dest+1,glyph)
        else:
            self.order.insert(index_dest,glyph)# .remove() shifts -1
        for i in indexes_to_move[::-1]: #lowest index first this time
            to_replace=to_move[indexes_to_move.index(i)]
            # log.info(f"replacing {to_replace} with {self.order[i]} @{i}")
            storage[to_replace].grid_remove() #one at a time
            self.draggables.insert(i,self.make_glyph_label(self.order[i]))
            self.update_idletasks()
        index3=self.order.index(glyph)
        text=(f"Glyph ‘{glyph}’ moved to index {index_dest} (between "
                f"{self.order[index3-1]} and ")
        if len(self.order) > index3+1:
            text+=f"{self.order[index3+1]})"
        else:
            text+="the end)"
        log.info(text)
        self.update_shown() #since the order changed
    def alphabetize_order(self):
        """This does unicode code points, which isn't likely what you want. But
        this should help users move closer to what they want, where they only
        have to shuffle the non-ASCII characters."""
        self.order.sort()
        self.reorder_alphabet()
        self.update_shown() #since the order changed
    def hide_letters(self):
        log.info("Going to hide_letters")
        try:
            self.config_buttons[_('reorder')].grid()
            self.config_buttons[_("(un)hide")].grid_remove()
            self.config_buttons[_("re-alphabetize")].grid_remove()
            self.config_order.destroy()
        except:
            pass
        self.config_hiding=ui.Frame(self.outsideframe,c=1,r=0)
        for i in self.order:
            n=len(self.config_hiding.winfo_children())
            self.show_bits[i]=ui.CheckButton(self.config_hiding, text=i,
                                        variable=self.hide_vars[i],
                                        sticky='news',
                                        r=n//self.config_columns,
                                        c=n%self.config_columns,
                                        selectimage=None,
                                        ipadx=0,
                                        ipady=0
                                    )
    def update_shown(self,*args):
        self.show_order=[i for i in self.order
                        if not self.hide_vars[i].get()
                        if not self.show_pictured_only or (
                                            i in self.exids and self.exids[i])
                    ]
        self.reflow_chart()
    def _show_all(self):
        self.show_pictured_only=False
        self.config_buttons[_("Pictured Only")].grid()
        self.config_buttons[_("Show All")].grid_remove()
        self.update_shown()
        # print(f"Showing this alphabetical order: {self.show_order}")
    def _show_pictured_only(self):
        selected_already=[i for i in self.exids if self.exids[i]]
        if len(selected_already) >= self.show_at_least:
            self.show_pictured_only=True
            self.update_shown()
            self.config_buttons[_("Pictured Only")].grid_remove()
            self.config_buttons[_("Show All")].grid()
        else:
            self._show_all()
        # print(f"Showing this alphabetical order: {self.show_order}")
    def show_chart(self):
        """This is run any time new buttons are needed, not just on init
        self.chart init is in chart_config"""
        try:
            for i in self.chart.content.winfo_children():
                i.destroy()
        except:
            pass
        for n,g in enumerate(self.show_order):
            self.buttons[g]=ui.Frame(self.chart.content,
                                    r=n//self.ncolumns,
                                    c=n%self.ncolumns,
                                    sticky='news',
                                    )
            self.buttons[g].l=ui.Label(self.buttons[g], #letter(s)
                                        text=g,font='title',
                                        r=0,c=0)
            self.buttons[g].b=ui.Button(self.buttons[g], #picture and word
                                        choice=g,
                                        compound='top', #picture placement
                                        command=self.select_example,
                                        sticky='news',
                                        r=1,c=0,
                                        **self.get_kwargs(g))
        self.chart.update()
    def chart_config(self):
        self.chart=ui.ScrollingFrame(self.frame,r=1,c=1,ipadx=20,ipady=20)
        self.configFrame=ui.Frame(self.outsideframe, r=1, c=2, sticky='n')
        self.config_buttons['title']=ui.Button(self.configFrame,
                                    text=_("Change Title"),
                                    command=self.edit_title,
                                    r=self.configFrame.grid_size()[1], c=0)
        for text,choice in [(_("More Columns"),1),(_("Fewer Columns"),-1)]:
            self.config_buttons[text]=ui.Button(self.configFrame,
                                        text=text, choice=choice,
                                        command=self.column_config,
                                        r=self.configFrame.grid_size()[1], c=0)
        for text,command in [(_("Pictured Only"), self._show_pictured_only),
                                (_("Show All"), self._show_all),
                                (_("Print"), self.print_chart)]:
            self.config_buttons[text]=ui.Button(self.configFrame,
                                        text=text, command=command,
                                        r=self.configFrame.grid_size()[1], c=0)
    def _hidden(self,value=dict()):
        for i in value:
            self.hide_vars[i].set(value[i])
        return {i:self.hide_vars[i].get() for i in self.hide_vars}
    def save_settings(self):
        if 'settings' not in self.program:
            # log.info(f"settings now {self.exids=} {self.order=} {self.ncolumns=}")
            return
        log.error("If you're seeing this, you have passed a settings module, "
                "but there is no save_settings method in the parent class...")
    def edit_title(self):
        self.title_entry.grid()
        self.title_entry.bind("<Return>",self._set_chart_title)
        self.title_label.grid_remove()
    def _compose_page_title(self):
        self.chart_title.set(_(f"Alphabet Chart for {self.analangname} "
                            f"[{self.db.analang}]"))
    def _set_chart_title(self,event=None):
        self.title_label.grid()
        toset=self.chart_title.get()
        if not toset:
            self._compose_page_title()
        self.title_entry.unbind("<Return>")
        self.title_entry.grid_remove()
        self.save_settings()
    def set_up_chart_title(self):
        self.chart_title=ui.StringVar() #set below, in _set_chart_title
        titleframe=ui.Frame(self.frame, r=0, c=1, sticky='ew')
        self.title_label=ui.Label(titleframe, textvariable=self.chart_title,
                                                                    r=0, c=1)
        self.title_entry=ui.EntryField(titleframe, textvariable=self.chart_title,
                                                                    r=1, c=1)
        self._set_chart_title()
    def __init__(self, parent, **kwargs):
        title="Alphabet Chart UI for Glyph Ordering and Selection"
        log.info(f"Running {title}")
        self.parent=parent
        if not hasattr(self,'program'): #i.e., from calling class
            self.program=parent.program#kwargs.get('program',{})
        self.show_at_least=5
        self.ncolopts=range(1,10)
        self.db=self.program.get('db',kwargs.get('db'))
        self.my_settings=['exids','order','ncolumns','chart_title']
        if 'settings' in self.program:
            for k in self.my_settings:
                setattr(self,k,getattr(self.program['settings'],'alpha_'+k)())
            self.analangname=self.program['settings'].languagenames[
                                                                self.db.analang]
        else:
            for k in ['exids','order']:
                setattr(self,k,kwargs.get(k,0))
            self.ncolumns=kwargs.get('ncolumns',8)
            self.analangname=self.db.analang
        self.imgdir=self.db.imgdir
        log.info(f"using {self.imgdir=}")
        # self.order=program['settings'].get('alphabet_order',kwargs.get('order'))
        if not self.order:
            log.info(f"No alphabetical order found; using all known glyphs")
            self.order=[i for j in self.db.s[self.db.analang].values() for i in j]
            self.order.sort()
        log.info(f"Using this alphabetical order: {self.order}")
        log.info(f"Using these exids: {self.exids}")
        if self.exids:
            # self.exids=exids
            for k in set(self.order)-set(self.exids):
                self.exids[k]=None #only fill in examples, don't remove them.
            self.exobjs={g:(self.db.sensedict[self.exids[g]]
                            if self.exids[g] in self.db.sensedict
                            else None)
                        for g in self.exids}
            for glyph,sense in [(k,v) for k,v in self.exobjs.items() if v is not None]:
                getimagelocationURI(sense)
                if hasattr(sense,'image'):
                    sense.image.scale(1,pixels=100,scaleto='height')
                else: #Don't keep examples without images
                    self.exobjs[glyph]=None
                    self.exids[glyph]=None
        else:
            self.exids={g:None for g in self.order}
            self.exobjs={g:None for g in self.order}
        self.buttons={} #some place to store these
        self.order_bits={}
        self.show_bits={}
        self.hide_vars={g:ui.BooleanVar(value=False) for g in self.order}
        for i in self.hide_vars.values():
            i.trace_add('write', self.update_shown)
        super(OrderAlphabet,self).__init__(parent,title=title)
        self.mainwindow=True
        self.set_up_chart_title()
        self.alphabet_config()
        self.chart_config()
        self._show_pictured_only() # calls update_shown>reflow_chart>?show_chart
        self.save_settings()
class SelectFromPicturableWords(ui.Window):
    """This allows users to select a picturable word for one grapheme"""
    def set_up_images(self):
        """This would look faster if we made one button at a time."""
        if len(self.examples) > 5:
            self.wait("Loading Images")
        for n,i in enumerate(self.examples.copy()):
            self.waitprogress(n*100//len(self.examples))
            if getimagelocationURI(i):
                # print(f"no image for {i.id}!")
                self.examples.remove(i)
            else:
                i.image.scale(1,pixels=100,scaleto='height')
        self.waitdone()
    def select(self,x,event=None):
        print('selected:',x)
        self.selected=x
        self.destroy()
        self.parent.deiconify
    def __init__(self, parent, db, glyph, ps='Noun'):
        self.imgdir=db.imgdir
        self.examples=[i for i in db.senses
                    if i.psvalue() == ps
                    if i.entry.lcvalue()
                    if i.illustrationvalue()
                    if glyph in i.entry.lcvalue()
                    ]
        # print([(i.entry.lcvalue(),i.illustrationvalue()) for i in self.examples])
        title="Alphabet Chart UI for Word Selection"
        super(SelectFromPicturableWords,self).__init__(parent,
                                                        title=title,
                                                        withdrawn=True)
        self.set_up_images()
        optionlist=[{'code':i.id,
                    'name':i.entry.lcvalue(),
                    'image':i.image.scaled}
                    for i in self.examples
                    if hasattr(i,'image')]
        # print(optionlist)
        ui.Label(self.frame,text=title,font='title',c=0,r=0)
        if optionlist:
            ui.Label(self.frame,text=f"Select a word to exemplify ‘{glyph}’",
                    c=0,r=1)
            ui.ScrollingButtonFrame(self.frame,
                            optionlist=optionlist,
                            command=self.select,
                            compound='left',
                            c=0,r=2
                            )
        else:
            ui.Label(self.frame,text=f"No examples for ‘{glyph}’!",c=0,r=1)
        self.deiconify()
def getimagelocationURI(sense):
    if hasattr(sense,'image') and isinstance(sense.image,ui.Image):
        return
    di=sense.illustrationURI()
    if file.exists(di):
        try:
            sense.image=ui.Image(di)
        except:
            return 1
    elif not sense.illustrationvalue():
        print("no illustration value!")
        return 1
    else:
        print(f"file {di} doesn't exist!")
        return 1
if __name__ == '__main__':
    try:
        _
    except:
        def _(x):
            return x
    filename="/home/kentr/Assignment/Tools/WeSay/Demo_en/Demo_en.lift"
    program={'name':'Alphabet UI module',
            'theme':'highcontrast',
            'db':lift.LiftXML(filename),#This provides imgdir and analang
        }
    r=ui.Root(program)
    r.title('Alphabet Chart UI')
    exids={"'": None, '-': None, 'B': None, 'I': None, 'O': None, 'P': None, 'a': 'face_50e60901-8869-495f-97cf-b9be6173f6b3', 'ai': None, 'au': None, 'ay': None, 'b': 'beard_4ad57748-4eab-49bd-ad58-72cf41e653bd', 'bb': None, 'c': 'cheek_3fb09846-1194-42a5-ac75-a48eeb9541f9', 'cc': None, 'ch': 'chest_0e7b3795-5a08-40c8-8b23-02f5879e7a3a', 'ck': None, 'ckw': None, 'd': 'body_791094f2-a82b-4650-81d8-c3b6145d2be4', 'dd': None, 'dw': None, 'e': 'neck_73d0f72c-abb2-4e6c-ac0e-122907026b06', 'ea': 'heart_626ba0f2-debb-40c2-92bd-2b0b819c28bb', 'eau': None, 'ee': None, 'ei': 'vein_56c65965-1cbe-4502-8479-fe5551b993cb', 'ey': None, 'f': None, 'ff': None, 'g': 'leg_0d765545-ed2a-4f74-aa37-4a5b7cd4b471', 'gg': None, 'gh': 'thigh_20efd25d-d864-465a-bb96-1dd47ffcef76', 'gn': None, 'gu': 'tongue_f62b2bdc-dad7-4800-9707-197bfebe108e', 'gw': None, 'h': 'hair (of head)_cfd6d8be-fe86-4b3b-9002-f0f59c89c162', 'hh': None, 'hw': None, 'i': None, 'ie': None, 'j': None, 'k': 'knee_150923de-c9a0-42b6-8106-ec01281ee523', 'kw': None, 'l': None, 'll': None, 'lw': None, 'm': None, 'mb': None, 'mm': None, 'mp': None, 'n': 'nose_c6327beb-5bb7-4ce5-9def-078dedbb79da', 'nd': None, 'nk': None, 'nn': None, 'nt': None, 'nw': None, 'ny': None, 'o': None, 'oa': None, 'oe': None, 'oi': None, 'oo': None, 'ou': None, 'ow': None, 'p': None, 'ph': None, 'pp': None, 'pt': None, 'q': None, 'qu': None, 'r': None, 'rh': None, 'rr': None, 'rw': None, 's': None, 'sc': None, 'sh': None, 'sl': None, 'ss': None, 'sw': None, 't': None, 'tch': None, 'th': None, 'thw': None, 'ts': None, 'tt': None, 'tw': None, 'u': None, 'ue': None, 'v': 'navel_d29fffce-fe19-474b-bd16-9e54058d1156', 'w': 'waist_358ed3cb-7f89-47a1-9d08-de6cd7416183', 'wh': None, 'x': None, 'y': None, 'yi': None, 'yw': None, 'z': None, 'zl': None, 'é': None}
    OrderAlphabet(r, program=program, exids=exids)
    r.mainloop()
    sys.exit()
