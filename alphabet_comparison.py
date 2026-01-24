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
        # Ensure image is in self.target_dir
        if self.target_dir and os.path.dirname(path) != self.target_dir:
            try:
                if not os.path.exists(self.target_dir):
                    os.makedirs(self.target_dir)
                filename = os.path.basename(path)
                target_path = os.path.join(self.target_dir, filename)
                
                # Copy if not same
                if path != target_path:
                    import shutil
                    shutil.copy2(path, target_path)
                    log.info(f"Copied {path} to {target_path}")
                    path = target_path
            except Exception as e:
                log.error(f"Could not copy selected image to target dir: {e}")
                
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
             self.select_image(file_path)

    def __init__(self, parent, title="Select Image", folder="covers", base_dir=None, exclude=None):
        super().__init__(parent, title=title)
        self.selected_image = None
        self.folder_name = folder
        
        # Target directory (Project Data)
        # We treat base_dir AS the target directory (e.g. .../images/booklet)
        self.target_dir = base_dir 
        if self.target_dir and not os.path.exists(self.target_dir):
             try:
                 os.makedirs(self.target_dir)
             except:
                 pass

        self.images = []
        
        # 1. Scan Target Directory (Project specific)
        if self.target_dir and os.path.exists(self.target_dir):
            types = ('*.jpg', '*.jpeg', '*.png', '*.svg')
            for t in types:
                self.images.extend(glob.glob(os.path.join(self.target_dir, t)))
                
        # 2. Scan Program Defaults
        possible_roots = [
            os.path.dirname(__file__),
            os.getcwd(),
            os.path.join(file.gethome(), '.gemini'), 
        ]
        
        program_dir = None
        for root in possible_roots:
            candidate = os.path.join(root, 'images', 'toselect', folder)
            if os.path.exists(candidate):
                program_dir = candidate
                break
        
        if not program_dir:
             program_dir = f"images/toselect/{folder}"
        
        if os.path.exists(program_dir):
             types = ('*.jpg', '*.jpeg', '*.png', '*.svg')
             for t in types:
                 found = glob.glob(os.path.join(program_dir, t))
                 # Only add if not already in list (by filename?) 
                 # Actually, allow distinct paths. Visuals will show dupes if same file exists in both.
                 # Prioritize project images (already added).
                 self.images.extend(found)
        
        # Filter exclusions
        if exclude:
            # Normalize for comparison? Just checking basenames or full paths might be tricky 
            # if one is absolute and other is relative or different dirs.
            # Let's assume absolute paths if possible, or basenames if that's safer for "same image".
            # User request: "if a file is selected for the logo, filter it out from the cover selection"
            # It's likely the same file if it's in the booklet dir.
            # Let's filter by checking if path is in exclude list.
            filtered = []
            exclude_set = set(os.path.abspath(p) for p in exclude if p)
            # Also exclude by filename if it helps avoid visual duplicates?
            # But the requirement is about the LOGO file.
            
            for img in self.images:
                abs_img = os.path.abspath(img)
                if abs_img not in exclude_set:
                     filtered.append(img)
            self.images = filtered

        # Compatibility/Fallback for image_dir_path usage in browse (though browse now calls select_image)
        self.image_dir_path = self.target_dir if self.target_dir else program_dir

        # Browse Button at top
        ui.Button(self.frame, text=_("Browse for other file..."), command=self.browse_and_select, r=0, c=0, colspan=3, sticky='ew')
        
        if not self.images:
            ui.Label(self.frame, text=_("No images found."), r=1, c=0)
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
        self.title_var.set(self.settings.get('booklet_title', 'Our Alphabet'))
        self.selected_cover_path = self.settings.get('cover_image', None)
        self.selected_logo_path = self.settings.get('logo_image', None)
        self.selected_logo_path = self.settings.get('logo_image', None)
        self.description_var.set(self.settings.get('description_text', ''))
        
        self.font_var = ui.StringVar()
        self.font_var.set(self.settings.get('booklet_font', 'Charis'))

        # UI Layout
        self.setup_ui()
        
    def toggle_font(self):
        current = self.font_var.get()
        new = "Andika" if current == "Charis" else "Charis"
        self.font_var.set(new)
        self.font_btn.config(text=new)
        self.save_settings_file()

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
        # Calculate base dir: reportdir/../images/booklet
        # This is where we want to save selected images
        base_dir = os.path.join(os.path.dirname(self.db.reportdir), 'images', 'booklet')
        # We pass this as base_dir. ImageSelector will treat this as target.
        # We pass folder="covers" so it looks in program's images/toselect/covers
        # and copies TO base_dir.
        # Wait, my ImageSelector logic uses base_dir as target. 
        # And searches program's defaults based on 'folder'.
        # So passing folder="covers" is correct for finding defaults.
        # Passing base_dir=.../images/booklet is correct for target.
        exclude = []
        if self.selected_logo_path:
             exclude.append(self.selected_logo_path)
             
        w = ImageSelector(self, title=_("Select Cover Image"), folder="covers", base_dir=base_dir, exclude=exclude)
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
        try:
            from tkinter import filedialog
            import shutil
        except ImportError:
            return

        file_path = filedialog.askopenfilename(
            parent=self,
            title=_("Select Logo File"),
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.svg"), ("All files", "*.*")]
        )
        
        if file_path and os.path.exists(file_path):
             # Target dir
             base_dir = os.path.join(os.path.dirname(self.db.reportdir), 'images', 'booklet')
             if not os.path.exists(base_dir):
                 try:
                     os.makedirs(base_dir)
                 except:
                     pass
             
             filename = os.path.basename(file_path)
             target_path = os.path.join(base_dir, filename)
             
             try:
                 if file_path != target_path:
                     shutil.copy2(file_path, target_path)
                     log.info(f"Copied logo to {target_path}")
                     self.selected_logo_path = target_path
                 else:
                     self.selected_logo_path = file_path
                     
                 self.update_logo_button()
                 self.save_settings_file()
             except Exception as e:
                 log.error(f"Error copying logo: {e}")
                 ui.messagebox.showerror(_("Error"), f"Could not copy file: {e}")

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
        self.copyright_entry_widget['width']=len(self.copyright_var.get())+3
        self.copyright_config.grid()
        self.copyright_config.bind("<Return>", self.save_copyright)
    def save_title(self, event=None):
        self.save_settings_file()
        self.title_config.grid_remove()
        self.title_label.grid()
        self.title_label.bind("<Button-1>", self.edit_title)
    def edit_title(self,event=None):
        self.title_label.grid_remove()
        self.title_entry_widget['width']=len(self.title_var.get())+3
        self.title_config.grid()
        self.title_config.bind("<Return>", self.save_title)

    def setup_ui(self):
        # Top Config Frame
        config_frame = ui.Frame(self.frame, r=0, c=0, sticky='ew', border=1, relief='groove')
        config_frame_cols=6
        # Row 0: Basic Config (Title)
        title_grid={'r':0, 'c':0, 'columnspan':config_frame_cols, 'sticky':'ew'}
        self.title_config=ui.Frame(config_frame, **title_grid)
        ui.Label(self.title_config, text=_("Title:"), r=0, c=0)
        self.title_entry_widget = ui.EntryField(self.title_config, textvariable=self.title_var,
                        width=len(self.title_var.get())+3, r=0, c=1)
        self.title_entry_widget.bind('<Return>', self.save_title)
        ui.Button(self.title_config,text=_("OK"),command=self.save_title,r=0, c=2)
        self.title_label=ui.Label(config_frame, textvariable=self.title_var, 
                                 font='title', **title_grid)
        self.title_label.bind('<Button-1>',self.edit_title)
        if self.title_var.get():
            self.save_title()
        else:
            self.edit_title()
        # Row 1: Images
        self.cover_config=ui.Frame(config_frame, r=1, c=1, sticky='ew')
        self.cover_btn = ui.Button(self.cover_config, command=self.open_cover_selector, 
                                r=0, c=2)
        self.update_cover_button()
        
        self.logo_config = ui.Frame(config_frame, r=1, c=2, sticky='ew')
        self.logo_btn = ui.Button(self.logo_config, command=self.open_logo_selector, r=0, c=0)
        self.update_logo_button()

        # Row 2: People/Text
        self.contributors_config=ui.Frame(config_frame, r=1, c=3, sticky='ew')
        ui.Button(self.contributors_config, text=_("Contributors")+'...', command=self.open_contributors, r=0, c=0)
        
        self.desc_config = ui.Frame(config_frame, r=1, c=4, sticky='ew')
        ui.Button(self.desc_config, text=_("Description Text")+'...', command=self.open_description_editor, r=0, c=0)

        # Font Switcher
        self.font_config = ui.Frame(config_frame, r=1, c=5)
        self.font_btn = ui.Button(self.font_config, text=self.font_var.get(), command=self.toggle_font, r=0, c=0)

        # Row 3: Copyright
        copyright_grid={'r':3, 'c':1, 'columnspan':config_frame_cols-1, 'sticky':'ew'}
        ui.Label(config_frame, text=_("© "), r=3, c=0, sticky='ew')
        self.copyright_config=ui.Frame(config_frame, **copyright_grid)
        self.copyright_entry_widget = ui.EntryField(self.copyright_config, textvariable=self.copyright_var, width=20, r=0, c=1)
        self.copyright_entry_widget.bind('<Return>', self.save_copyright)
        ui.Button(self.copyright_config,text=_("OK"),command=self.save_copyright,r=0, c=2)
        self.copyright_label=ui.Label(config_frame, textvariable=self.copyright_var,
                                    **copyright_grid)
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
        
        # --- Extra Text Pages ---
        extra_pages = []
        texts_dir = None
        # Look for 'texts' or 'textes' sibling to reports
        parent_dir = os.path.dirname(self.db.reportdir)
        for folder in ['texts', 'textes']:
            candidate = os.path.join(parent_dir, folder)
            if os.path.exists(candidate) and os.path.isdir(candidate):
                texts_dir = candidate
                break
        
        if texts_dir:
            from glob import glob
            txt_files = sorted(glob(os.path.join(texts_dir, "*.txt")))
            for txt_path in txt_files:
                try:
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    if not lines: continue
                    title = lines[0].strip()
                    body = "".join(lines[1:]).strip()
                    
                    # Look for matching image
                    base_name = os.path.splitext(os.path.basename(txt_path))[0]
                    img_path = None
                    for ext in ['.jpg', '.jpeg', '.png', '.svg']:
                        img_cand = os.path.join(texts_dir, base_name + ext)
                        if os.path.exists(img_cand):
                            img_path = img_cand
                            break
                    
                    # We'll let the PDF generator split this if it's too long, 
                    # but for signatures we need to know how many pages it TAKES.
                    # This is tricky. Let's assume for now one side per text unless we 
                    # implement a pre-split helper in the PDF module.
                    extra_pages.append({
                        'type': 'extra_text',
                        'title': title,
                        'text': body,
                        'image': img_path
                    })
                except Exception as e:
                    log.error(f"Error reading extra text file {txt_path}: {e}")

        page_names=[i['symbol'] for i in pages]
        suffix = "wTexts" if extra_pages else ""
        filename = '_'.join([_("Booklet"),*page_names,f'{suffix}[{self.db.analang}]{self.font_var.get()}.pdf'])
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
        
        # Determine Font
        font_name = getattr(self, 'font_var', ui.StringVar(value='Charis')).get()

        alphabet_comparison_pdf.create_comparison_chart(
             filepath, *pages, 
             extra_pages=extra_pages,
             prose_count=self.prose_count_var.get(),
             title=title_text,
             cover_image=self.selected_cover_path,
             logo_image=self.selected_logo_path,
             contributors=contributors_list,
             description=description_text,
             copyright_text=copyright_text,
             made_with=made_with,
             font_name=font_name
        )
        log.info(f"Generated {filepath}")
        
        try:
            from utilities import open_file
            open_file(filepath)
        except Exception as e:
            log.warning(f"Could not open PDF automatically: {e}")
        
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
