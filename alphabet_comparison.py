#!/usr/bin/env python3
# coding=UTF-8
"""
UI for Alphabet Comparison Chart generation.
Allows selecting two symbols (C/C or V/V) and 3 examples for each.
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

class PageSetup(ui.Window):
    def __init__(self, parent, **kwargs):
        title = "Alphabet Comparison Setup"
        self.parent = parent
        if not hasattr(self,'program'): #i.e., from calling class
            self.program=parent.program#kwargs.get('program',{})
        self.db = self.program.get('db')
        super().__init__(parent, title=title)
        
        # Data
        if 'alphabet' in self.program:
            glyphdict=self.program['alphabet'].glyphdict()
        else:
            glyphdict=self.program['glyphdict']
        self.symbols = [i for j in glyphdict.values() for i in j]
        self.vowels = list(glyphdict['V']) #self.identify_vowels()
        self.consonants = list(glyphdict['C']) #[s for s in self.symbols if s not in self.vowels]
        
        # State
        self.sym1_var = ui.StringVar()
        self.sym2_var = ui.StringVar()
        self.prose_count_var = ui.IntVar(value=20)
        
        # Store example IDs: { 'sym1': [id1, id2, id3], 'sym2': [id1, id2, id3] }
        # Only for current session/selection
        self.current_examples = {
            'left': [None, None, None],
            'right': [None, None, None]
        }
        
        # Load persisted settings
        self.settings = self.load_settings()
        
        # UI Layout
        self.setup_ui()
        
        # Traces
        self.sym1_var.trace_add('write', self.on_sym1_changed)
        self.sym2_var.trace_add('write', self.on_sym2_changed)
        
        # Restore last session
        if self.settings.get('last_sym1'):
            self.sym1_var.set(self.settings['last_sym1'])
        if self.settings.get('last_sym2'):
            self.sym2_var.set(self.settings['last_sym2'])
            
    def collect_symbols(self):
        """Collects all symbols from the LIFT database."""
        # Similar logic to alphabet_chart.py
        if 's' in dir(self.db) and self.db.analang in self.db.s:
             # self.db.s[lang] is dict of glyphs?
             # actually alphabet_chart says:
             # self.order=[i for j in self.db.s[self.db.analang].values() for i in j]
             try:
                 return sorted({i for j in self.db.s[self.db.analang].values() for i in j})
             except:
                 pass
        # Fallback or if structure differs
        return []

    # def identify_vowels(self):
    #     """Heuristic to identify vowels. 
    #      Ideally this comes from a profile or settings, but for now strict list or user config."""
    #     # Simple default list + anything defined in program settings if available
    #     # TODO: Check if there's a better source in `self.db` or `program`.
    #     defaults = {'a', 'e', 'i', 'o', 'u', 'ä', 'ö', 'ü', 'à', 'è', 'ì', 'ò', 'ù'}
    #     return {s for s in self.symbols if s.lower() in defaults} 

    def is_vowel(self, sym):
        return sym in self.vowels

    def setup_ui(self):
        # 1. Symbol Selection Frame
        frame_top = ui.Frame(self.frame, r=0, c=0, sticky='ew')
        
        ui.Label(frame_top, text="Left Page", c=0, r=0)
        self.cb_sym1 = ui.ListBox(frame_top, command=self.on_sym1_select,
                                 font='read',
                                 optionlist=self.symbols, c=0, r=1)
        
        ui.Label(frame_top, text="Right Page", c=2, r=0)
        self.cb_sym2 = ui.ListBox(frame_top, command=self.on_sym2_select,
                                 font='big',
                                 optionlist=self.symbols, c=2, r=1) # Values updated dynamically
                                 
        # 2. Example Selection Frame (Split Left/Right)
        frame_examples = ui.Frame(self.frame, r=1, c=0, sticky='news')
        
        # Left Side (Sym1)
        self.frame_left = ui.Label(frame_examples, text="Left Examples", c=0, r=0, sticky='n')
        self.btn_left = []
        for i in range(3):
            b = ui.Button(self.frame_left, text=f"Select Example {i+1}", 
                          choice=('left', i),
                          command=self.select_example,
                          r=i, c=0, sticky='ew')
            self.btn_left.append(b)
            
        # Right Side (Sym2)
        self.frame_right = ui.Label(frame_examples, text="Right Examples", c=1, r=0, sticky='n')
        self.btn_right = []
        for i in range(3):
            b = ui.Button(self.frame_right, text=f"Select Example {i+1}", 
                          choice=('right', i),
                          command=self.select_example,
                          r=i, c=0, sticky='ew')
            self.btn_right.append(b)

        # 3. Settings & Actions
        frame_bottom = ui.Frame(self.frame, r=2, c=0, sticky='ew')
        
        ui.Label(frame_bottom, text="Repetitions:", c=0, r=0)
        ui.EntryField(frame_bottom, textvariable=self.prose_count_var, width=5, c=1, r=0)
        
        ui.Button(frame_bottom, text="PDF", command=self.generate_pdf, c=2, r=0)
        # ui.Button(frame_bottom, text="Close", command=self.on_close, c=3, r=0)

    def on_sym1_select(self, event=None):
        if self.cb_sym1.curselection():
            val = self.cb_sym1.get(self.cb_sym1.curselection()[0])
            self.sym1_var.set(val)

    def on_sym2_select(self, event=None):
        if self.cb_sym2.curselection():
            val = self.cb_sym2.get(self.cb_sym2.curselection()[0])
            self.sym2_var.set(val)

    def on_sym1_changed(self, *args):
        sym1 = self.sym1_var.get()
        if not sym1: return
        
        # Update Sym2 options based on type
        if self.is_vowel(sym1):
            valid_b=self.vowels[:]
        else:
            valid_b=self.consonants[:]
        if sym1 in valid_b: 
            valid_b.remove(sym1)
        self.cb_sym2.delete(0, "end")
        for i in valid_b:
            self.cb_sym2.insert("end", i)
        # self.cb_sym2['listvariable'].set(valid_b)
        
        # Update Title
        self.frame_left.config(text=f"Examples for '{sym1}'")
        
        # Load stored examples if any
        self.restore_examples('left', sym1)
        
        # Clear/Reset Sym2 if it's now invalid
        # curr_sym2 = 
        if self.sym2_var.get() not in valid_b:
            self.sym2_var.set('')
        # if curr_sym2 and (self.is_vowel(curr_sym2) != is_v or curr_sym2 == sym1):
        #      self.sym2_var.set('')
        
        self.save_current_settings()

    def on_sym2_changed(self, *args):
        sym2 = self.sym2_var.get()
        if sym2:
            self.frame_right.config(text=f"Examples for '{sym2}'")
            self.restore_examples('right', sym2)
        self.save_current_settings()

    def select_example(self, selection):
        side, index = selection
        # self.cb_sym1
        # sym = self.sym1_var.get() if side == 'left' else self.sym2_var.get()
        if side == 'left':
            box=self.cb_sym1
        else:
            box=self.cb_sym2
        if box.curselection():
            sym = box.get(box.curselection()[0]) 
        else:
            sym = ''
        print("side:", side, "index:", index, "sym:", sym)
        if not sym:
            return
            
        # Temporarily withdraw to show selection dialog
        self.withdraw()
        
        w = SelectFromPicturableWords(self, self.db, sym)
        w.wait_window(w)
        
        if hasattr(w, 'selected'):
            sense_id = w.selected
            self.current_examples[side][index] = sense_id
            self.update_button(side, index, sense_id)
            self.save_examples(side, sym)
            
        self.deiconify()

    def update_button(self, side, index, sense_id):
        btn = self.btn_left[index] if side == 'left' else self.btn_right[index]
        
        if sense_id and sense_id in self.db.sensedict:
            sense = self.db.sensedict[sense_id]
            word = sense.entry.lcvalue()
            
            # Prepare image
            getimagelocationURI(sense)
            if hasattr(sense, 'image') and sense.image:
                sense.image.scale(1, pixels=50, scaleto='height')
                btn.config(text=word, image=sense.image.scaled, compound='left')
            else:
                btn.config(text=word, image='', compound='none')
        else:
            btn.config(text=f"Select Example {index+1}", image='', compound='none')

    def save_examples(self, side, sym):
        """Save current examples for this symbol to settings."""
        key = f"examples_{sym}"
        self.settings[key] = self.current_examples[side]
        self.save_settings_file()

    def restore_examples(self, side, sym):
        """Restore examples for this symbol from settings."""
        key = f"examples_{sym}"
        saved_ids = self.settings.get(key, [None, None, None])
        
        # Ensure list is length 3
        if len(saved_ids) < 3:
            saved_ids.extend([None]*(3-len(saved_ids)))
        
        self.current_examples[side] = saved_ids
        
        for i, sense_id in enumerate(saved_ids):
            self.update_button(side, i, sense_id)

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
            
    def save_current_settings(self):
        self.settings['last_sym1'] = self.sym1_var.get()
        self.settings['last_sym2'] = self.sym2_var.get()
        self.save_settings_file()
        
    def generate_pdf(self):
        sym1 = self.sym1_var.get()
        sym2 = self.sym2_var.get()
        
        if not sym1 or not sym2:
            return # Maybe show error
            
        def prepare_data(sym, ex_ids):
            items = []
            for eid in ex_ids:
                if eid and eid in self.db.sensedict:
                    sense = self.db.sensedict[eid]
                    word = sense.entry.lcvalue()
                    uri = sense.illustrationURI()
                    items.append((sym, word, uri))
            return {'symbol': sym, 'items': items}
            
        left_data = prepare_data(sym1, self.current_examples['left'])
        right_data = prepare_data(sym2, self.current_examples['right'])
        
        filename = f"Comparison_{sym1}_vs_{sym2}_{self.db.analang}.pdf"
        filepath = file.getdiredurl(self.db.reportdir, filename)
        
        alphabet_comparison_pdf.create_comparison_chart(
            filepath, left_data, right_data, 
            prose_count=self.prose_count_var.get()
        )
        # Maybe show success message or open file
        log.info(f"Generated {filepath}")
        
    def on_close(self):
        self.save_current_settings()
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
