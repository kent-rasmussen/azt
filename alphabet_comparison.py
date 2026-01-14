#!/usr/bin/env python3
# coding=UTF-8
"""
UI for Alphabet Comparison Booklet generation.
Allows selecting comparative pages (C/C or V/V) with 3 examples for each.
"""
import os
import sys
import json
import logging
from functools import partial

# Local module imports (assuming we are in the same directory)
import logsetup
import file
import lift
import ui_tkinter as ui
import alphabet_comparison_pdf
from alphabet_chart import SelectFromPicturableWords, getimagelocationURI

log = logsetup.getlog(__name__)

SETTINGS_FILE = "alphabet_comparison_settings.json"

class PageFrameUI(ui.Frame):
    def select_example(self, index):
        log.info("Calling select_example")
        if self.glyph_choice.curselection():
            sym = self.glyph_choice.get(self.glyph_choice.curselection()[0]) 
        else:
            sym = ''
        print("index:", index, "sym:", sym)
        if not sym:
            return
            
        # Temporarily withdraw to show selection dialog
        self.parent.withdraw()
        
        w = SelectFromPicturableWords(self, self.parent.db, sym)
        w.wait_window(w)
        
        if hasattr(w, 'selected'):
            sense_id = w.selected
            self.current_examples[index] = sense_id
            self.update_button(index, sense_id)
            self.parent.save_examples()
            
        self.parent.deiconify()
    def update_button(self, index, sense_id):
        btn = self.exs[index]
        
        if sense_id and sense_id in self.parent.db.sensedict:
            sense = self.parent.db.sensedict[sense_id]
            word = sense.entry.lcvalue()
            
            # Prepare image
            getimagelocationURI(sense)
            if hasattr(sense, 'image') and sense.image:
                sense.image.scale(1, pixels=50, scaleto='height')
                btn.config(text=word, image=sense.image.scaled, compound='left')
            else:
                btn.config(text=word, image='', compound='none')
        else:
            btn.config(text=f"Select Example", image='', compound='none')
    
    def restore_examples(self):
        """Restore examples for this symbol from settings."""
        saved_ids = self.parent.settings.get(self.glyph, [None, None, None])
        
        # Ensure list is length 3
        if len(saved_ids) < 3:
            saved_ids.extend([None]*(3-len(saved_ids)))
        
        self.current_examples = saved_ids
        
        for i, sense_id in enumerate(saved_ids):
            self.update_button(i, sense_id)
    def on_select(self,event=None):
        if sel:=self.glyph_choice.curselection():
            self.glyph=self.glyph_choice.get(sel[0])
        else:
            self.glyph=None
        self.restore_examples()
        self.parent.save_pages()
    def reset_choices(self,valid_b):
        self.glyph_choice.delete(0, "end")
        for i in valid_b:
            self.glyph_choice.insert("end", i)
    def index(self):
        return self.parent.pageFrames.index(self)
    def __init__(self, parent, glyph=None,**kwargs):
        super().__init__(parent.pageframesFrame, **kwargs) #gui parent
        self.parent = parent # parent object
        self.glyph = glyph # Make available to parent
        self.glyph_choice = ui.ListBox(self, command=self.on_select,
                                 font='readbig', height=4, width=5,
                                 optionlist=self.parent.symbols[:], r=0)
        self.exs = [ui.Button(self, choice=i,
                                command=self.select_example,
                                r=i+1, sticky='ew')
                            for i in range(3)
                ]
        if glyph and glyph in self.glyph_choice.get(0, "end"):
            self.glyph_choice.selection_set(self.glyph_choice.get(0, "end").index(glyph))
        self.restore_examples()
class PageSetup(ui.Window):
    def __init__(self, parent, **kwargs):
        title = "Alphabet Comparison Setup"
        self.parent = parent
        if not hasattr(self,'program'): #i.e., from calling class
            self.program=parent.program
        self.db = self.program.get('db')
        super().__init__(parent, title=title)
        self.fpr=6 #even allows pairs together
        
        # Data
        if 'alphabet' in self.program:
            glyphdict=self.program['alphabet'].glyphdict()
        else:
            glyphdict=self.program['glyphdict']
        self.symbols = [i for j in glyphdict.values() for i in j]
        self.vowels = list(glyphdict['V']) 
        self.consonants = list(glyphdict['C'])
        self.prose_count_var = ui.IntVar(value=20)
        
        # Load persisted settings
        self.settings = self.load_settings()
        
        # UI Layout
        self.setup_ui()
        
    def n_pages(self):
        return len(self.pageframesFrame.winfo_children())-1

    def add_pages(self,*glyphs):
        if not glyphs:
            glyphs=[None,None]#always start with, or add, two pages
        self.pageFrames.extend([PageFrameUI(self, glyph, 
                                    r=self.n_pages()//self.fpr, 
                                    c=self.n_pages()%self.fpr, 
                                    sticky='nsew', 
                                    border=1)
                                for glyph in glyphs
                                ])
        self.add_more_button.grid(row=self.n_pages()//self.fpr, 
                                column=self.n_pages()%self.fpr, 
                                )
    def setup_ui(self):
        self.pageframesFrame=ui.Frame(self.frame, r=0, c=0, sticky='nsew')
        self.add_more_button=ui.Button(self.pageframesFrame, 
                                        text="+2 Pages", 
                                        command=self.add_pages)
        self.pageFrames=[]
        self.add_pages(*self.settings.get('pages',[]))

        # 3. Settings & Actions
        frame_bottom = ui.Frame(self.frame, r=2, c=0, sticky='ew')
        
        ui.Label(frame_bottom, text="Repetitions:", c=0, r=0)
        ui.EntryField(frame_bottom, textvariable=self.prose_count_var, width=5, c=1, r=0)
        
        ui.Button(frame_bottom, text="PDF", command=self.generate_pdf, c=2, r=0)

    def on_glyph_change(self, page):
        log.info(f"Page {page.index()} changed (on_glyph_change)")
        if page not in self.pageFrames:
            log.info(f"Page {page} not in {self.pageFrames}")
            return
        index=self.pageFrames.index(page)
        if index%2:
            log.info(f"Page {index} is an odd (right hand) page")
            return
        else:
            log.info(f"Page {index} is an even (left hand) page; restricting the next")

        if page.glyph in self.vowels:
            valid_b=self.vowels[:]
        elif page.glyph in self.consonants:
            valid_b=self.consonants[:]
        else:
            valid_b=self.symbols[:]
        if page.glyph in valid_b: 
            valid_b.remove(page.glyph)
        self.pageFrames[index+1].reset_choices(valid_b)
        log.info(f"Page {index} change finished, with page {index+1} constrained to {valid_b}")

    def save_pages(self):
        """Save current page list to settings."""
        self.settings['pages'] = [i.glyph for i in self.pageFrames]
        self.save_settings_file()

    def save_examples(self):
        """Save current examples for each symbol to settings."""
        example_dict={i.glyph:i.current_examples for i in self.pageFrames}
        self.settings.update(example_dict)
        self.save_settings_file()
    
    def load_settings(self):
        try:
            path = file.getdiredurl(self.db.reportdir, SETTINGS_FILE)
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            log.warning(f"Could not load settings: {e}")
        return {}

    def save_settings_file(self):
        try:
            path = file.getdiredurl(self.db.reportdir, SETTINGS_FILE)
            with open(path, 'w') as f:
                json.dump(self.settings, f)
        except Exception as e:
            log.warning(f"Could not save settings: {e}")
            
    def generate_pdf(self):
        def prepare_data(page):
            items = []
            for eid in page.current_examples:
                if eid and eid in self.db.sensedict:
                    sense = self.db.sensedict[eid]
                    word = sense.entry.lcvalue()
                    uri = sense.illustrationURI()
                    items.append((page.glyph, word, uri))
            return {'symbol': page.glyph, 'items': items}
            
        pages=[prepare_data(i) for i in self.pageFrames if i.glyph]
        page_names=[i['symbol'] for i in pages]
        filename = '_'.join([_("Booklet"),*page_names,f'[{self.db.analang}].pdf'])
        filepath = file.getdiredurl(self.db.reportdir, filename)
        
        alphabet_comparison_pdf.create_comparison_chart(
            filepath, *pages, 
            prose_count=self.prose_count_var.get()
        )
        log.info(f"Generated {filepath}")
        
    def on_close(self):
        self.destroy()
        sys.exit()

if __name__ == '__main__':
    # Demo Mock if run directly
    try:
        # Assuming run from raspy/azt folder with env
        try:
            _
        except:
            def _(x): return x
        filename = "/home/kentr/Assignment/Tools/WeSay/Demo_en/Demo_en.lift"
        if not os.path.exists(filename):
             # Try to find a local lift file to test
             import glob
             lifts = glob.glob("*.lift")
             if lifts: filename = lifts[0]
             
        program = {
            'name': 'Compare UI',
            'theme': 'highcontrast',
            'db': lift.LiftXML(filename),
            'glyphdict': {'V': ['a', 'e', 'i', 'o', 'u'], 'C': ['b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'y', 'z']}
        }
        r = ui.Root(program)
        r.title('Alphabet Comparison')
        PageSetup(r)
        r.mainloop()
    except Exception as e:
        print(f"Error running app: {e}")
        import traceback
        traceback.print_exc()
