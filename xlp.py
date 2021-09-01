#!/usr/bin/env python3
# coding=UTF-8
from xml.etree import ElementTree as ET
import xmlfns
import rx
import file
import logging
log = logging.getLogger(__name__)
class Report(object):
    def __init__(self,filename,report,langname):
        self.filename=filename
        self.stylesheetdir=file.getstylesheetdir(filename)
        # self.tree=ET.ElementTree(ET.Element('lingPaper'))
        self.node=ET.Element('lingPaper') #self.tree.getroot()
        self.title="{} A→Z+T output report for {}".format(report,langname)
        log.info("Starting XLingPaper report file at {} with title '{}'".format(
                                                        filename,self.title))
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
        # self.compile() #This isn't working yet.
    def write(self):
        """This writes changes to XML which can be read by XXE as XLP."""
        doctype=self.node.tag
        with open(self.filename, 'wb') as f:
            f.write('<?xml version="1.0" encoding="UTF-8" ?>'
                    '<!DOCTYPE {} PUBLIC "-//XMLmind//DTD XLingPap//EN"'
                    ' "XLingPap.dtd">'.format(doctype).encode('utf8'))
            # ElementTree.ElementTree(tree).write(f, 'utf-8')
            #in 3.9: self.tree=ET.indent(ET.ElementTree(self.node))
            xmlfns.indent(self.node)
            self.tree=ET.ElementTree(self.node)
            self.tree.write(f, encoding="UTF-8")
    def compile(self):
        import lxml.etree
        self.transformsdir=file.gettransformsdir()
        dom = lxml.etree.parse(self.filename)
        log.info(self.filename)
        # xslt = lxml.etree.parse(xsl_filename)
        # transform = lxml.etree.XSLT(xslt)
        transform={}
        outfile=self.filename+'out'
        xslts=[
            (1,'XLingPapRemoveAnyContent.xsl'),
            (2,'XLingPapXeLaTeX1.xsl'),
            (3,'XLingPapPublisherStylesheetXeLaTeX.xsl'),
            (4,'TeXMLLike.xsl')
            ]
        for n,xslt in xslts:
            trans=lxml.etree.parse(str(self.transformsdir)+'/'+xslt)
            transform[n] = lxml.etree.XSLT(trans)
        # transform = lxml.etree.XSLT(lxml.etree.parse(xsl_filename))
        newdom = transform[1](dom)
        with open(outfile+'a', 'wb') as f:
            f.write(lxml.etree.tostring(newdom, pretty_print=True))
        # newdom2 = transform[2](newdom1) #not used; always using stylesheets!
        dom=newdom
        newdom = transform[3](dom)
        # except lxml.etree.XSLTApplyError:
        #     log.error("Looks like a problem applying an XSLT.")
        with open(outfile+'b', 'wb') as f:
            f.write(lxml.etree.tostring(newdom, pretty_print=True))
        dom=newdom
        # Convert this to pure XeLaTeX form *here*, using converted java classes
        # log.info("dom1:{},newdom1:{}".format(dom,newdom))
        newdom = transform[4](dom)
        # log.info("dom2:{},newdom2:{}".format(dom,newdom))
        with open(outfile+'.tex', 'wb') as f:
            f.write(lxml.etree.tostring(newdom, pretty_print=True))
        #This doesn't do anything yet, but needs to
        # Apply transforms/XLingPapRemoveAnyContent.xsl to the input to deal with any content control.
        # To the result of this, apply either transforms/XLingPapXeLaTeX1.xsl (for an input without a style sheet) or transforms/XLingPapPublisherStylesheetXeLaTeX.xsl (for an input with a style sheet).
        # Convert this to pure XeLaTeX form:
        #     A Java class that reads the input and changes certain sequences to what they need to be for XeLaTeX .  The class name is TeXMLLikeCharacterConversion (and it's in the file named TeXMLLikeCharacterConversion.java).
        #     The result of this is processed by transforms/TeXMLLike.xsl.  The output is plain (XeLaTeX ) text.
        #     Another Java class that reads the output of that transform and makes sure all IDs are in a form that XeLaTeX can handle.  The class name is NonASCIIIDandIDREFConversion (and it's in the file named NonASCIIIDandIDREFConversion.java).
        # Run this XeLaTeX form through xelatex.  The result is the PDF.
        #     DoTeXPDF (Linux/Mac) or DoTeXPDF.bat (Windows)
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
        XeLaTeXSpecial=("graphite font-feature='Hide tone contour staves=True' "
                                "font-feature='Literacy alternates=True'")
        lg=ET.SubElement(parent, 'language',
            attrib={'id':id, 'name':name,
                    'font-family':'Charis SIL',
                    'XeLaTeXSpecial':XeLaTeXSpecial})
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
    def __init__(self,parent,title="No Section Title!",level=1):
        id=rx.id(title)
        name='section'+str(level)
        self.node=ET.SubElement(parent.node,name,attrib={'id':id})
        st=SecTitle(self,title) #I always need this
class SecTitle(ET.Element):
    def __init__(self,parent,text):
        self.node=ET.SubElement(parent.node,'secTitle')
        self.node.text=text
class Paragraph(ET.Element):
    def __init__(self,parent,text='No Paragraph text!'):
        self.node=ET.SubElement(parent.node,'p')
        self.node.text=text
class Example(ET.Element):
    def __init__(self,parent,id,heading=None):
        rxid=rx.id(id)
        self.node=ET.SubElement(parent.node,'example',attrib={'num':rxid})
        if heading is not None:
            headnode=ET.SubElement(self.node,'exampleHeading')
            headnode.text=heading

class Table(ET.Element):
    """<tablenumbered id="nt-ndk-melodies">
            <table border="1">
                <caption/>
                <tr><td/></tr>
            </table>
        </tablenumbered>"""
    def __init__(self,parent,caption):
        id=rx.id('nt'+caption)
        self.numbered=ET.SubElement(parent.node,'tablenumbered',attrib={'id':id})
        self.node=ET.SubElement(self.numbered,'table')
        self.caption=ET.SubElement(self.node,'caption')
        self.caption.text=caption
class Row(ET.Element):
    def __init__(self,parent):
        self.node=ET.SubElement(parent.node,'tr')
class Cell(ET.Element):
    def __init__(self,parent,content,header=False,linebreakwords=False):
        if header == False:
            tag='td'
        elif header == True:
            tag='th'
        else:
            log.error("Not sure what kind of cell you're looking for: {}"
                        "".format(header))
        self.node=ET.SubElement(parent.node,tag)
        if linebreakwords == True:
            for i in content.split(): #this returns a list, even one ['word',].
                if self.node.text != None:
                    br=Linebreak(self)
                    br.node.tail=i
                else:
                    self.node.text=i
        else:
            self.node.text=str(content)
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
        self.node=ET.SubElement(parent.node,'link',attrib={'href':url})
        if phonetic == True:
            ph=XLPobject(self,'tPhonetic',text)
        else:
            self.node.text=text
class Linebreak(ET.Element):
    def __init__(self,parent):
        self.node=ET.SubElement(parent.node,'br')
if __name__ == "__main__":
    def _(x):
        return str(x)
    print('trying manual report generation...')
    d=Report('filetest.xml',"a non-language","Language Name")
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
    d.close()
    # d.write()
