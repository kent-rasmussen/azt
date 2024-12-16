#!/usr/bin/env python3
# coding=UTF-8
from xml.etree import ElementTree as ET
import xmlfns
import rx
import file
import logsetup
log=logsetup.getlog(__name__)
# logsetup.setlevel('INFO',log) #for this file
logsetup.setlevel('DEBUG',log) #for this file
import time
import subprocess
try:
    _
except:
    def _(x):
        return x
class Report(object):
    def __init__(self,filename,report,langname,program):
        #use program, if only for it's name
        if 'name' not in program:
            log.error("the program argument to xlp.Report needs a 'name' key")
            exit()
        self.start_time=time.time()
        self.filename=filename
        self.tmpfile=self.filename+'.tmp'
        if file.exists(self.tmpfile):
            log.info(_("Report {} already in process; not doing again."
                    ).format(self.filename))
            return
        open(self.tmpfile, 'wb').close()
        self.stylesheetdir=file.getstylesheetdir(filename)
        # self.tree=ET.ElementTree(ET.Element('lingPaper'))
        self.node=ET.Element('lingPaper') #self.tree.getroot()
        self.title="{} {} output report for {}".format(report,
                                                        program['name'],
                                                        langname)
        log.info("Starting XLingPaper report file at {} with title '{}'".format(
                                                        filename,self.title))
        self.authors=[{'name':'Kent Rasmussen',
                        'affiliation':'SIL International',
                        'Email':'kent_rasmussen@sil.org'},
                        {'name':program['name'],
                        'Email': 'https://github.com/kent-rasmussen/azt'}
                        ]
        self.langlist=list()
        self.frontmatter()
        log.info("Done initializing Report")
    def close(self,me=False):
        log.info("Done; setting back matter, etc, now.")
        self.backmatter()
        self.languages()
        self.xlptypes()
        self.stylesheet()
        self.write()
        self.cleanup()
        t=time.time()-self.start_time
        # m=int(t/60)
        # s=t%60
        log.info("Finished in {:1.0f} minutes, {:2.3f} seconds.".format(*divmod(t,60)))
        if me:
            self.compile() #This isn't working yet.
    def cleanup(self):
        file.remove(self.tmpfile)
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
        try:
            import lxml.etree
        except:
            log.info(_("Couldn't find/import lxml, so not compiling report."))
            return
        """from http://xmlsoft.org/XSLT/python.html:
        This is a basic test of XSLT interfaces: loading a stylesheet and a document, transforming the document and saving the result.

        import libxml2
        import libxslt <===I can't get this to work (no longer maintained?)

        styledoc = libxml2.parseFile("test.xsl")
        style = libxslt.parseStylesheetDoc(styledoc)
        doc = libxml2.parseFile("test.xml")
        result = style.applyStylesheet(doc, None)
        style.saveResultToFilename("foo", result, 0)
        style.freeStylesheet()
        doc.freeDoc()
        result.freeDoc()

        note the need to explicitely deallocate documents with freeDoc() except for the stylesheet document which is freed when its compiled form is garbage collected.
        """
        self.transformsdir=file.gettransformsdir()
        dom = lxml.etree.parse(self.filename)
        log.info(self.filename)
        # xslt = lxml.etree.parse(xsl_filename)
        # transform = lxml.etree.XSLT(xslt)
        transform={}
        outfile=self.filename #base for multiple files, below
        xslts=[
            (1,'XLingPapRemoveAnyContent.xsl'),
            (2,'XLingPapXeLaTeX1.xsl'),
            (3,'XLingPapPublisherStylesheetXeLaTeX.xsl'),
            (4,'TeXMLLike.xsl')
            ]
        for n,xslt in xslts:
            try:
                trans=lxml.etree.parse(str(self.transformsdir)+'/'+xslt)
            except lxml.etree.XMLSyntaxError as e:
                for entry in e.error_log:
                    log.error("{}: {} ({})".format(entry.domain_name,
                                            entry.type_name, entry.filename))
            transform[n] = lxml.etree.XSLT(trans)
            for error in transform[n].error_log:
                log.error("XSLT Error {}: {} ({})".format(error.message,
                                                    error.line,
                                                    error.filename))
        newdom = transform[1](dom)
        newdom.write_output(outfile+'a')
        # newdom2 = transform[2](newdom1) #not used; always using stylesheets!
        dom=newdom
        try:
            newdom = transform[3](dom)
            newdom.write_output(outfile+'b')
        except:
            for error in transform[3].error_log:
                log.error("XSLT Error {}: {} ({})".format(error.message,
                                                    error.line,
                                                    error.filename))
        dom=newdom
        # Convert this to pure XeLaTeX form *here*, using converted java classes
        # A Java class that reads the input and changes certain sequences to
        # what they need to be for XeLaTeX .  The class name is
        # TeXMLLikeCharacterConversion (and it's in the file named
        # TeXMLLikeCharacterConversion.java).
        newdom=rx.texmllike(str(dom))
        with open(outfile+'c', 'wb') as f:
            f.write(newdom.encode('utf_8'))
        dom = lxml.etree.parse(outfile+'c') #this is where this currently breaks
        try:
            texfile=outfile.replace('.xml','.tex')
            outdir=file.getfilenamedir(outfile)
            newdom = transform[4](dom)
            log.info("writing to tex file {}".format(texfile))
            newdom.write_output(texfile)
        except:
            for error in transform[4].error_log:
                log.error("XSLT Error {}: {} ({})".format(error.message,
                                                    error.line,
                                                    error.filename))
        xetexargs=[
                    # "/usr/texbinxlingpaper/xelatex",
                    # "/usr/local/xlingpapertexbin/xelatex",
                    "xelatex",
                    "--interaction=nonstopmode","-output-directory",
                    outdir, texfile]
        try:
            subprocess.run(xetexargs,shell=False) # was call
            # subprocess.call(xetexargs,shell=False) #does twice help?
            exts=[
                'tex',
                'out','aux','log',
                'xmla','xmlb','xmlc'
                ]
            # exts+=['xmla','xmlb','xmlc','tex'] #once this is working...
            for ext in exts:
                file.remove(outfile.replace('.xml', '.'+ext))
        except Error as e:
            log.info("The call to xelatex didn't work: {}".format(e))
        # Another Java class that reads the output of that transform and makes
        # sure all IDs are in a form that XeLaTeX can handle.  The class name
        # is NonASCIIIDandIDREFConversion (and it's in the file named
        # NonASCIIIDandIDREFConversion.java).
        # Hopefully this will be enough:
        #     StringBuffer sb = new StringBuffer();
    	# for (int i = 0; i < id.length(); i++) {
    	#     int code = id.codePointAt(i);
    	#     if (code > 127) {
    	# 	sb.append((Integer.toHexString(code)).toUpperCase());
    	#     } else {
    	# 	sb.append(id.charAt(i));
    	#     }
    	# }
    	# return sb.toString();
        # }
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
        options=[('',''),
                ('-et',' (phonetic)'),
                ('-em',' (phonemic)'),
                ('-orth',' (orthographic)')]
        for lang in self.langlist:
            for code,name in options:
                self.language(lgs,lang['id']+code, lang['name']+name)
    def language(self, parent, id, name):
        XeLaTeXSpecial=("graphite font-feature='Hide tone contour staves=True' "
                                "font-feature='Literacy alternates=True'")
        if name.startswith('am-') or name == 'am':
            ffam='Abyssinica SIL'
        else:
            ffam='Charis SIL'
        lg=ET.SubElement(parent, 'language',
            attrib={'id':id, 'name':name,
                    'font-family':ffam,
                    'XeLaTeXSpecial':XeLaTeXSpecial})
    def addlang(self, lang):
        #This is called by the report; should it be generated?
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
        #This should add overrides for each language listed under languages:
        # <langDataLayout
        # language="gnd-orth"
        # ><langDataInExampleLayout
        # textafter="&gt;"
        # textbefore="&lt;"
        # textbeforeafterusesfontinfo="no"
        # ></langDataInExampleLayout
        # ><langDataInTableLayout
        # textbeforeafterusesfontinfo="no"
        # ></langDataInTableLayout
        # ><langDataInProseLayout
        # textafter="&gt;"
        # textbefore="&lt;"
        # textbeforeafterusesfontinfo="no"
        # ></langDataInProseLayout
        # ></langDataLayout
        # ><langDataLayout
        # language="gnd-em"
        # ><langDataInExampleLayout
        # textafter="/"
        # textbefore="/"
        # textbeforeafterusesfontinfo="no"
        # ></langDataInExampleLayout
        # ><langDataInTableLayout
        # textbeforeafterusesfontinfo="no"
        # ></langDataInTableLayout
        # ><langDataInProseLayout
        # textafter="/"
        # textbefore="/"
        # textbeforeafterusesfontinfo="no"
        # ></langDataInProseLayout
        # ></langDataLayout
        # ><langDataLayout
        # language="gnd-et"
        # ><langDataInExampleLayout
        # textafter="]"
        # textbefore="["
        # textbeforeafterusesfontinfo="no"
        # ></langDataInExampleLayout
        # ><langDataInTableLayout
        # textbeforeafterusesfontinfo="no"
        # ></langDataInTableLayout
        # ><langDataInProseLayout
        # textafter="]"
        # textbefore="["
        # textbeforeafterusesfontinfo="no"
        # ></langDataInProseLayout
        # ></langDataLayout
        # >

class Section(ET.Element):
    def __init__(self,parent,title="No Section Title!",level=None,landscape=False):
        id=rx.id(title)
        if level: #this shouldn't happen
            self.level=level
        elif hasattr(parent,'level'): #this should manage most cases
            self.level=parent.level+1
        else:
            self.level=1
        name='section'+str(self.level)
        attribs={'id':id}
        if landscape:
            attribs['showinlandscapemode']='yes'
        self.node=ET.SubElement(parent.node,name,attrib=attribs)
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
    def destroy(self):
        if hasattr(self,'numbered'):
            self.parent.node.remove(self.numbered)
        else:
            self.parent.node.remove(self.node)
    def __init__(self,parent,caption=None,numbered=True):
        self.parent=parent
        if numbered:
            id=rx.id('nt'+caption)
            self.numbered=ET.SubElement(parent.node,'tablenumbered',attrib={'id':id})
            self.node=ET.SubElement(self.numbered,'table')
        else:
            self.node=ET.SubElement(parent.node,'table')
        if caption:
            self.caption=ET.SubElement(self.node,'caption')
            self.caption.text=caption
class Row(ET.Element):
    def __init__(self,parent):
        self.node=ET.SubElement(parent.node,'tr')
class Cell(ET.Element):
    def __init__(self,parent,content='',header=False,linebreakwords=False):
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
        """<mediaObject src="../audio/Nouncitationbackdos.wav"></mediaObject>
        <lingPaper includemediaobjects='yes' />
        """
class Linebreak(ET.Element):
    def __init__(self,parent):
        self.node=ET.SubElement(parent.node,'br')

if __name__ == "__main__":
    def _(x):
        return str(x)
    print('trying manual report generation...')
    d=Report('filetest.xml',"a non-language","Language Name >")
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
