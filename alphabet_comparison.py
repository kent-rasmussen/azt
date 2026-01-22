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
import glob
import math
# if __name__ == '__main__':
#     global _
#     try:
#         _
#     except NameError:
#         def _(x): 
#             return x
# Local module imports (assuming we are in the same directory)
import logsetup
import file
import lift
import ui_tkinter as ui
import alphabet_comparison_pdf
from alphabet_chart import SelectFromPicturableWords, getimagelocationURI

log = logsetup.getlog(__name__)

SETTINGS_FILE = "alphabet_comparison_settings.json"

class ImageSelector(ui.Window):
    def select_image(self, path):
        log.info(f"Selected image: {path}")
        self.selected_image = path
        self.destroy()

    def browse_and_select(self):
        try:
            from tkinter import filedialog
            import shutil
        except ImportError:
            log.error("Could not import filedialog")
            return
            
        file_path = filedialog.askopenfilename(
            parent=self,
            title=_("Select Image File"),
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.svg"), ("All files", "*.*")]
        )
        
        if file_path and os.path.exists(file_path):
            # Target directory
            # self.image_dir_path is stored during init now
            if not getattr(self, 'image_dir_path', None):
                 # Fail safe if init changed
                 possible_roots = [
                    os.path.dirname(__file__),
                    os.getcwd(),
                 ]
                 for root in possible_roots:
                    candidate = os.path.join(root, 'images', 'toselect', self.folder_name)
                    if os.path.exists(os.path.dirname(candidate)): # at least parent exists
                         self.image_dir_path = candidate
                         break
            
            if self.image_dir_path:
                if not os.path.exists(self.image_dir_path):
                    try:
                        os.makedirs(self.image_dir_path)
                    except Exception as e:
                        log.error(f"Could not create directory {self.image_dir_path}: {e}")
                        return

                target_name = os.path.basename(file_path)
                target_path = os.path.join(self.image_dir_path, target_name)
                
                # Copy file
                try:
                    shutil.copy2(file_path, target_path)
                    log.info(f"Copied {file_path} to {target_path}")
                    self.select_image(target_path)
                except Exception as e:
                    log.error(f"Error copying file: {e}")
                    ui.messagebox.showerror(_("Error"), f"Could not copy file: {e}")

    def __init__(self, parent, title="Select Image", folder="covers"):
        super().__init__(parent, title=title)
        self.selected_image = None
        self.folder_name = folder
        
        # Find images
        # Try to locate the directory
        possible_roots = [
            os.path.dirname(__file__),
            os.getcwd(),
            os.path.join(file.gethome(), '.gemini'), # fallback?
        ]
        
        image_dir = None
        for root in possible_roots:
            candidate = os.path.join(root, 'images', 'toselect', folder)
            if os.path.exists(candidate):
                image_dir = candidate
                break
        
        # Fallback search if not found directly
        if not image_dir:
             # Just try current directory if all else fails
             image_dir = f"images/toselect/{folder}"
        
        self.image_dir_path = image_dir # Store for browse

        self.images = []
        if os.path.exists(image_dir):
            types = ('*.jpg', '*.jpeg', '*.png', '*.svg')
            for t in types:
                self.images.extend(glob.glob(os.path.join(image_dir, t)))
        
        # Fallback to general 'images/toselect' if specific folder empty/missing
        if not self.images:
            fallback_dir = os.path.dirname(image_dir)
            if os.path.exists(fallback_dir) and folder != 'covers': # covers usually strict
                 for t in ('*.jpg', '*.jpeg', '*.png', '*.svg'):
                     self.images.extend(glob.glob(os.path.join(fallback_dir, t)))

        # Browse Button at top
        ui.Button(self.frame, text=_("Browse for other file..."), command=self.browse_and_select, r=0, c=0, colspan=3, sticky='ew')

        if not self.images:
            ui.Label(self.frame, text=_("No images found in {dir}").format(dir=image_dir), r=1, c=0)
            return

        # Grid view
        scroll = ui.ScrollingFrame(self.frame, r=1, c=0, sticky='nsew', colspan=3)
        columns = 3
        for i, img_path in enumerate(self.images):
            r, c = divmod(i, columns)
            f = ui.Frame(scroll.content, r=r, c=c, padx=5, pady=5)
            
            # Helper to load image
            try:
                img = ui.Image(img_path)
                img.scale(1, pixels=300, scaleto='height')
                ui.Button(f, image=img.scaled, 
                         command=partial(self.select_image, img_path),
                         r=0, c=0)
            except Exception as e:
                log.error(f"Error loading image {img_path}: {e}")
                ui.Button(f, text=os.path.basename(img_path), 
                         command=partial(self.select_image, img_path),
                         r=0, c=0)

class DescriptionEditor(ui.Window):
    def save(self):
        val = self.text_widget.get("1.0", "end-1c")
        self.parent.description_var.set(val)
        self.parent.save_settings_file()
        self.destroy()

    def __init__(self, parent):
        super().__init__(parent, title=_("Edit Description"))
        self.parent = parent
        
        ui.Label(self.frame, text=_("Enter descriptive text for the imprint page:"), r=0, c=0)
        
        # Using standard Tkinter text widget directly if ui wrapper not available or complex
        # ui_tkinter usually has Text or similar. Assuming ui.Text exists or falling back to Frame+tk.Text
        # Checking ui_tkinter usage... usually ui.Text isn't standard in minimal wrapper, 
        # let's assume we can access tk widget via ui.Frame or similar if needed. 
        # But wait, ui.Label/EntryField exist. Let's try ui.Text if it exists in library, 
        # otherwise use a simple specialized Frame.
        
        self.text_frame = ui.Frame(self.frame, r=1, c=0)
        import tkinter as tk
        self.text_widget = tk.Text(self.text_frame, height=10, width=40)
        self.text_widget.pack()
        
        current_val = self.parent.description_var.get()
        self.text_widget.insert("1.0", current_val)
        
        ui.Button(self.frame, text=_("Save"), command=self.save, r=2, c=0)

class ContributorsManager(ui.Window):
    def add_contributor(self, event=None):
        name = self.entry_var.get().strip()
        if name:
            self.contributors.append(name)
            self.listbox.insert("end", name)
            self.entry_var.set("")
            self.save()

    def save(self):
        # Update settings
        self.program['settings'].alphabet_contributors(self.contributors)
        # Force save (main.py settings logic handles persistence via 'settings.contributors(val)')
        # But we might need to trigger a file write if it doesn't happen automatically on set
        # The main.py Setting.contributors is a method that sets a private var.
        # It relies on specific save triggers usually.
        # We'll trust the main app flow or trigger a save if available.
        if hasattr(self.program['settings'], 'storesettingsfile'):
             self.program['settings'].storesettingsfile(setting='contributors')

    def __init__(self, parent, program):
        super().__init__(parent, title=_("People Involved"))
        self.program = program
        self.contributors = self.program['settings'].alphabet_contributors() # Get list
        if not isinstance(self.contributors, list):
             self.contributors = []

        ui.Label(self.frame, text=_("Contributors"), font='title', r=0, c=0, colspan=2)
        
        self.listbox = ui.ListBox(self.frame, r=1, c=0, colspan=2, width=30, height=10)
        for name in self.contributors:
            self.listbox.insert("end", name)
            
        self.entry_var = ui.StringVar()
        ui.EntryField(self.frame, textvariable=self.entry_var, r=2, c=0)
        ui.Button(self.frame, text=_("Add"), command=self.add_contributor, r=2, c=1)
        
        ui.Label(self.frame, text=_("Names cannot be removed once added."), font='small', r=3, c=0, colspan=2)


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
        
        # Persisted UI State
        self.title_var = ui.StringVar()
        self.copyright_var = ui.StringVar()
        self.description_var = ui.StringVar()
        # Initialize from global settings
        if 'alphabet_copyright' in self.program['settings'].settings['alphabet']['attributes']:
             self.copyright_var.set(self.program['settings'].alpha_copyright())
        
        self.selected_cover_path = None
        self.selected_logo_path = None
        
        # Load persisted settings (local)
        self.settings = self.load_settings()
        self.title_var.set(self.settings.get('booklet_title', ''))
        self.selected_cover_path = self.settings.get('cover_image', None)
        self.selected_logo_path = self.settings.get('logo_image', None)
        self.description_var.set(self.settings.get('description_text', ''))

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
    def open_cover_selector(self):
        w = ImageSelector(self, title=_("Select Cover Image"), folder="covers")
        w.wait_window(w)
        if w.selected_image:
            self.selected_cover_path = w.selected_image
            self.update_cover_button()
            self.save_settings_file() # Save cover choice

    def update_cover_button(self):
        if self.selected_cover_path:
            txt = ""
            try:
                # Show thumbnail on button if possible? or just text
                img = ui.Image(self.selected_cover_path)
                img.scale(1, pixels=100, scaleto='height')
                self.cover_btn.configure(text=txt, image=img.scaled, compound='left')
                self.cover_btn.image = img # Keep reference!
            except:
                self.cover_btn.configure(text=txt + f" ({os.path.basename(self.selected_cover_path)})", image='', compound='none')
        else:
            self.cover_btn.configure(text=_("Select Cover"), image='', compound='none')

    def open_logo_selector(self):
        w = ImageSelector(self, title=_("Select Logo"), folder="logos")
        w.wait_window(w)
        if w.selected_image:
            self.selected_logo_path = w.selected_image
            self.update_logo_button()
            self.save_settings_file() # Save logo choice

    def update_logo_button(self):
        if self.selected_logo_path:
            txt = ""
            try:
                img = ui.Image(self.selected_logo_path)
                img.scale(1, pixels=100, scaleto='height')
                self.logo_btn.configure(text=txt, image=img.scaled, compound='left')
                self.logo_btn.image = img # Keep reference!
            except:
                self.logo_btn.configure(text=txt + f" ({os.path.basename(self.selected_logo_path)})", image='', compound='none')
        else:
            self.logo_btn.configure(text=_("Select Logo"), image='', compound='none')

    def open_description_editor(self):
        DescriptionEditor(self)

    def open_contributors(self):
        # Ensure settings are loaded before managing
        if hasattr(self.program['settings'], 'loadsettingsfile'):
             self.program['settings'].loadsettingsfile(setting='contributors')
        ContributorsManager(self, self.program)

    def save_copyright(self, *args):
        # Update global setting
        self.program['settings'].alpha_copyright(self.copyright_var.get())
        # Ideally trigger a save, similar to ContributorsManager
        if hasattr(self.program['settings'], 'storesettingsfile'):
             self.program['settings'].storesettingsfile(setting='alphabet')
        self.copyright_config.grid_remove()
        self.copyright_label.grid()
    def edit_copyright(self,event=None):
        self.copyright_label.grid_remove()
        self.copyright_config.grid()
        self.copyright_config.bind("<Return>", self.save_copyright)
    def save_title(self, event=None):
        self.save_settings_file()
        self.title_config.grid_remove()
        self.title_label.grid()
        self.title_label.bind("<Button-1>", self.edit_title)
    def edit_title(self,event=None):
        self.title_label.grid_remove()
        self.title_config.grid()
        self.title_config.bind("<Return>", self.save_title)

    def setup_ui(self):
        # Top Config Frame
        config_frame = ui.Frame(self.frame, r=0, c=0, sticky='ew', border=1, relief='groove')
        
        # Row 0: Basic Config (Title)
        self.title_config=ui.Frame(config_frame, r=0, c=0, columnspan=2, sticky='w')
        ui.Label(self.title_config, text=_("Title:"), r=0, c=0)
        ui.EntryField(self.title_config, textvariable=self.title_var,
                        width=len(self.title_var.get())+3, r=0, c=1)
        ui.Button(self.title_config,text=_("OK"),command=self.save_title,r=0, c=2)
        self.title_label=ui.Label(config_frame, textvariable=self.title_var, 
                                 font='title', r=0, c=0, columnspan=2, sticky='w')
        self.title_label.bind('<Button-1>',self.edit_title)
        self.save_title()

        # Row 1: Images
        self.cover_config=ui.Frame(config_frame, r=1, c=0)
        self.cover_btn = ui.Button(self.cover_config, command=self.open_cover_selector, 
                                r=0, c=2)
        self.update_cover_button()
        
        self.logo_config = ui.Frame(config_frame, r=1, c=1)
        self.logo_btn = ui.Button(self.logo_config, command=self.open_logo_selector, r=0, c=0)
        self.update_logo_button()

        # Row 2: People/Text
        self.contributors_config=ui.Frame(config_frame, r=2, c=0, sticky='w')
        ui.Button(self.contributors_config, text=_("Contributors..."), command=self.open_contributors, r=0, c=0)
        
        self.desc_config = ui.Frame(config_frame, r=2, c=1, sticky='w')
        ui.Button(self.desc_config, text=_("Description Text..."), command=self.open_description_editor, r=0, c=0)

        # Row 3: Copyright
        ui.Label(config_frame, text=_("© "), r=3, c=0, sticky='e')
        self.copyright_config=ui.Frame(config_frame, r=3, c=1, sticky='w')
        ui.EntryField(self.copyright_config, textvariable=self.copyright_var, width=20, r=0, c=1)
        ui.Button(self.copyright_config,text=_("OK"),command=self.save_copyright,r=0, c=2)
        self.copyright_label=ui.Label(config_frame, textvariable=self.copyright_var,
                                    r=3, c=1, sticky='w')
        self.copyright_label.bind('<Button-1>',self.edit_copyright)
        self.save_copyright()

        # Pages Frame
        self.pageframesFrame=ui.Frame(self.frame, r=1, c=0, sticky='nsew')
        self.add_more_button=ui.Button(self.pageframesFrame, 
                                        text="+2 Pages", 
                                        command=self.add_pages)
        self.pageFrames=[]
        self.add_pages(*self.settings.get('pages',['a']))

        # Bottom Frame
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
        # Update extra fields
        self.settings['booklet_title'] = self.title_var.get()
        self.settings['cover_image'] = self.selected_cover_path
        self.settings['logo_image'] = self.selected_logo_path
        self.settings['description_text'] = self.description_var.get()
        
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
        
        # Gather all needed info
        if hasattr(self.program['settings'], 'loadsettingsfile'):
             # Ensure loaded (double-check for persistence issues)
             self.program['settings'].loadsettingsfile(setting='contributors')
        contributors_list = self.program['settings'].alphabet_contributors()
        copyright_text = self.copyright_var.get()
        title_text = self.title_var.get()
        description_text = self.description_var.get()
        
        # Made with attribution (as per plan, using program defaults, passed here for flexibility or added in PDF module)
        # We'll pass it into options
        made_with = f"Made with {self.program['name']} ({self.program['url']})"
        
        alphabet_comparison_pdf.create_comparison_chart(
            filepath, *pages, 
            prose_count=self.prose_count_var.get(),
            title=title_text,
            cover_image=self.selected_cover_path,
            logo_image=self.selected_logo_path,
            contributors=contributors_list,
            description=description_text,
            copyright_text=copyright_text,
            made_with=made_with
        )
        log.info(f"Generated {filepath}")
        
    def on_close(self):
        self.destroy()
        sys.exit()

if __name__ == '__main__':
    # Demo Mock if run directly
    # global _
    try:
        _
    except NameError:
        def _(x): 
            return x
    try:
        # Assuming run from raspy/azt folder with env
        filename = "/home/kentr/Assignment/Tools/WeSay/Demo_en/Demo_en.lift"
        if not os.path.exists(filename):
             # Try to find a local lift file to test
             import glob
             lifts = glob.glob("*.lift")
             if lifts: filename = lifts[0]
             
        # Mock settings class for testing global settings interaction
        class MockSettings:
            def __init__(self):
                self.settings = {'alphabet':{'attributes':['alphabet_copyright']}}
                self._contributors = ["John Doe", "Jane Smith"]
                self._copyright = "© 2023 Community"
            def contributors(self, val=None):
                if val: self._contributors=val
                return self._contributors
            def alphabet_copyright(self, val=None):
                if val: self._copyright=val
                return self._copyright
            def storesettingsfile(self, setting=''):
                print(f"Mock saving {setting}")

        program = {
            'name': 'Compare UI',
            'theme': 'highcontrast',
            'db': lift.LiftXML(filename),
            'glyphdict': {'V': ['a', 'e', 'i', 'o', 'u'], 'C': ['b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'y', 'z']},
            'settings': MockSettings(),
            'url': 'http://example.com'
        }
        r = ui.Root(program)
        r.title('Alphabet Comparison')
        PageSetup(r)
        r.mainloop()
    except Exception as e:
        print(f"Error running app: {e}")
        import traceback
        traceback.print_exc()
