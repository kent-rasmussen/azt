#!/usr/bin/env python3
# coding=UTF-8
from xml.etree import ElementTree as ET
import rx
import file
import logging
log = logging.getLogger(__name__)
class Report(object):
    def __init__(self,filename,langname):
        self.filename=filename
        self.stylesheetdir=file.getstylesheetdir(filename)
        # self.tree=ET.ElementTree(ET.Element('lingPaper'))
        self.node=ET.Element('lingPaper') #self.tree.getroot()
        self.title="Generic A→Z+T output report for {}".format(langname)
        self.authors=[{'name':'Kent Rasmussen',
                        'affiliation':'SIL Cameroun',
                        'Email':'kent_rasmussen@sil.org'},
                        {'name':'A→Z+T',
                        'Email': 'https://github.com/kent-rasmussen/azt'}
                        ]
        self.langlist=list()
        self.frontmatter()
        log.info("Done initializing Report")
    def close(self):
        log.info("Done; setting back matter, etc, now.")
        self.backmatter()
        self.languages()
        self.xlptypes()
        self.stylesheet()
        self.write()
    def write(self):
        """This writes changes to XML which can be read by XXE as XLP."""
        doctype=self.node.tag
        with open(self.filename, 'wb') as f:
            f.write('<?xml version="1.0" encoding="UTF-8" ?>'
                    '<!DOCTYPE {} PUBLIC "-//XMLmind//DTD XLingPap//EN"'
                    ' "XLingPap.dtd">'.format(doctype).encode('utf8'))
            # ElementTree.ElementTree(tree).write(f, 'utf-8')
            #in 3.9: self.tree=ET.indent(ET.ElementTree(self.node))
            indent(self.node)
            self.tree=ET.ElementTree(self.node)
            self.tree.write(f, encoding="UTF-8")
    def frontmatter(self):
        fm=ET.SubElement(self.node, 'frontMatter')
        ti=ET.SubElement(fm, 'title')
        ti.text=_(self.title)
        for author in self.authors:
            au=ET.SubElement(fm, 'author')
            au.text=_(author['name'])
            if 'affiliation' in author:
                af=ET.SubElement(fm, 'affiliation')
                af.text=_(author['affiliation'])
            if 'Email' in author:
                ae=ET.SubElement(fm, 'emailAddress')
                ae.text=_(author['Email'])
    def backmatter(self):
        bm=ET.SubElement(self.node, 'backMatter')
        en=ET.SubElement(bm, 'endnotes')
        ref=ET.SubElement(bm, 'references')
    def languages(self):
        lgs=ET.SubElement(self.node, 'languages')
        for lang in self.langlist:
            self.language(lgs,lang['id'], lang['name'])
    def language(self, parent, id, name):
        lg=ET.SubElement(parent, 'language',
            attrib={'id':id, 'name':name,
                    'font-family':'Charis SIL',
                    'XeLaTeXSpecial':"graphite font-feature='Hide tone contour "
                    "staves=True' font-feature='Literacy alternates=True'"
                    })
    def addlang(self, lang):
        if 'id' in lang and 'name' in lang:
            self.langlist+=[lang]
        else:
            log.error("Hey, not sure how this language is formatted! "
                                                            "({})".format(lang))
    def xlptypes(self):
        tps=ET.SubElement(self.node, 'types')
        allxlptypes=[{'id':'tBold','font-weight':"bold"},
                {'id':'tBoldItalic','font-weight':"bold",'font-style':"italic"},
                {'id':'tPhonetic', 'after':"]", 'before':"["}
                ]
        for t in allxlptypes:
            self.xlptype(tps,t)
    def xlptype(self, parent, t):
        tp=ET.SubElement(parent, 'type',attrib=t)
        # <type
        # XeLaTeXSpecial="graphite font-feature='Hide tone contour staves=True'"
        # after="]"
        # before="["
        # font-family="Charis SIL"
        # font-style="normal"
        # id="tPhonetic"
        # >
        # <?xml version="1.0"?>
        # <types
        # ><comment
        # >The following types are provided as pre-set examples. You may well want to create your own types that refer to one or more of these. You do that by typing in the names of the types in the types attribute of your type.</comment
        # ><type
        # font-weight="bold"
        # id="tBold"
        # ></type
        # ><type
        # font-style="italic"
        # font-weight="bold"
        # id="tBoldItalic"
        # ></type
        # ><type
        # font-weight="bold"
        # id="tEmphasis"
        # ></type
        # ><type
        # id="tGrammaticalGloss"
        # types="tSmallCaps"
        # ></type
        # ><type
        # font-style="italic"
        # id="tItalic"
        # ></type
        # ><type
        # cssSpecial="text-decoration:none"
        # id="tNoOverline"
        # xsl-foSpecial="text-decoration=&quot;no-overline&quot;"
        # ></type
        # ><type
        # font-variant="normal"
        # id="tNoSmallCaps"
        # ></type
        # ><type
        # cssSpecial="text-decoration:none"
        # id="tNoStrikethrough"
        # xsl-foSpecial="text-decoration=&quot;no-line-through&quot;"
        # ></type
        # ><type
        # cssSpecial="text-decoration:none"
        # id="tNoUnderline"
        # xsl-foSpecial="text-decoration=&quot;no-underline&quot;"
        # ></type
        # ><type
        # cssSpecial="text-decoration:overline"
        # id="tOverline"
        # xsl-foSpecial="text-decoration=&quot;overline&quot;"
        # ></type
        # ><type
        # font-style="normal"
        # font-variant="normal"
        # font-weight="normal"
        # id="tRegular"
        # ></type
        # ><type
        # font-family="Charis SIL Small Caps"
        # id="tSmallCaps"
        # ></type
        # ><type
        # XeLaTeXSpecial="line-through"
        # cssSpecial="text-decoration:line-through"
        # id="tStrikethrough"
        # xsl-foSpecial="text-decoration=&quot;line-through&quot;"
        # ></type
        # ><type
        # XeLaTeXSpecial="subscript"
        # cssSpecial="vertical-align:sub;"
        # font-size="65%"
        # id="tSubscript"
        # xsl-foSpecial="baseline-shift='sub'"
        # ></type
        # ><type
        # XeLaTeXSpecial="superscript"
        # cssSpecial="vertical-align:super;"
        # font-size="65%"
        # id="tSuperscript"
        # xsl-foSpecial="baseline-shift='super'"
        # ></type
        # ><type
        # XeLaTeXSpecial="underline"
        # cssSpecial="text-decoration:underline"
        # id="tUnderline"
        # xsl-foSpecial="text-decoration=&quot;underline&quot;"
        # ></type
        # ><comment
        # >Add your custom types here.</comment
        # ></types
        # >
    def stylesheet(self):
        if hasattr(self,'stylesheetdir'):
            print('self.stylesheetdir:',self.stylesheetdir)
        stylesheetname='CannedPaperStylesheet.xml'
        url=file.getdiredurl(self.stylesheetdir,stylesheetname)
        tree = ET.parse(url)
        stylesheet = tree.getroot()
        self.styled=ET.Element('xlingpaper')
        self.styled.set('version','2.24.0')
        sp=ET.SubElement(self.styled,'styledPaper')
        sp.append(self.node)
        sp.append(stylesheet)
        self.node=self.styled
class Section(ET.Element):
    def __init__(self,parent,title,level=1):
        id=rx.id(title)
        name='section'+str(level)
        self.node=ET.SubElement(parent.node,name,attrib={'id':id})
        st=SecTitle(self,title) #I always need this
class SecTitle(ET.Element):
    def __init__(self,parent,text):
        self.node=ET.SubElement(parent.node,'secTitle')
        self.node.text=text
class Paragraph(ET.Element):
    def __init__(self,parent,text):
        self.node=ET.SubElement(parent.node,'p')
        self.node.text=text
class Example(ET.Element):
    def __init__(self,parent,id):
        rxid=rx.id(id)
        self.node=ET.SubElement(parent.node,'example',attrib={'num':rxid})

class Word(ET.Element):
    def __init__(self,parent):
        self.node=ET.SubElement(parent.node,'word')

class ListWord(ET.Element):
    def __init__(self,parent,id):
        rxid=rx.id(id)
        self.node=ET.SubElement(parent.node,'listWord',attrib={'letter':rxid})

class LangData(ET.Element):
    def __init__(self,parent,lang,text,phonetic=False):
        self.node=ET.SubElement(parent.node,'langData',attrib={'lang':lang})
        if phonetic == True:
            ph=XLPobject(self,'tPhonetic',text)
        else:
            self.node.text=text

class LinkedData(ET.Element):
    def __init__(self,parent,lang,text,url,phonetic=False):
        self.node=ET.SubElement(parent.node,'langData',attrib={'lang':lang})
        l=Link(self,url,text,phonetic=phonetic)

class Gloss(ET.Element):
    def __init__(self,parent,lang,text):
        self.node=ET.SubElement(parent.node,'gloss',attrib={'lang':lang})
        self.node.text=text

class XLPobject(ET.Element):
    def __init__(self,parent,typ,text):
        self.node=ET.SubElement(parent.node, 'object',attrib={'type':typ})
        self.node.text=text

class Link(ET.Element):
    def __init__(self,parent,url,text,phonetic=False):
        self.node=ET.SubElement(parent.node,'link',attrib={'href':'audio/'+url})
        if phonetic == True:
            ph=XLPobject(self,'tPhonetic',text)
        else:
            self.node.text=text
def indent(elem, level=0):
    """from http://effbot.org/zone/element-lib.htm#prettyprint"""
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
if __name__ == "__main__":
    def _(x):
        return str(x)
    print('trying manual report generation...')
    d=Report('filetest.xml',"a non-language")
    s1=Section(d,"Section One title")
    t="This is the first paragraph in the report."
    p=Paragraph(s1,t)
    e=Example(s1,'x1')
    ew=Word(e)
    # el=LangData(ew,'gnd','baba')
    lang={'id':'gnd', 'name': 'Zulgo'}
    d.addlang(lang)
    es=LinkedData(ew,lang['id'],'baba','Noun_d4410d1a-bba0-4c9e-823c-4566'
                '2abea150_lexical-unit_goŋ_roof_.wav',phonetic=True)
    es=LangData(ew,lang['id'],'˦˦ ˨˨',)
    lang={'id':'en', 'name': 'English'}
    d.addlang(lang)
    eg=Gloss(ew,lang['id'],'father')
    t="This is a second paragraph in the report, after an example."
    p=Paragraph(s1,t)
    e=Example(s1,'x2')
    elw=ListWord(e,'linked')
    # el=LangData(ew,'gnd','baba')
    lang={'id':'gnd', 'name': 'Zulgo'}
    es=LinkedData(elw,'gnd','baba','Noun_d4410d1a-bba0-4c9e-823c-45662abe'
                                        'a150_lexical-unit_goŋ_roof_.wav')
    es=LangData(elw,lang['id'],'˦˦ ˨˨',)
    eg=Gloss(elw,'en','father')
    elw=ListWord(e,'Not linked')
    # el=LangData(ew,'gnd','baba')
    es=LangData(elw,'gnd','baba')
    es=LangData(elw,'gnd','˨˨ ˦˦',phonetic=True)
    eg=Gloss(elw,'en','father')
    d.finish()
    d.write()
