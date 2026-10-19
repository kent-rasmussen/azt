#!/usr/bin/env python3
# coding=UTF-8
from utilities.i18n import _
from utilities import logsetup
log=logsetup.getlog(__name__)
from xml.etree import ElementTree as ET
from utilities import xmlfns,rx,file,times

import subprocess
import pathlib
import os
def ascii_id(x):
    """XLingPaper's NonASCIIIDandIDREFConversion: each character above 127
    becomes its code point in upper-case hex, as TeX labels need."""
    return ''.join(c if ord(c)<128 else '{:X}'.format(ord(c)) for c in x)
def ascii_ids(root):
    """Convert every id, and every attribute that refers to one, the same
    way, so references still land. A value counts as a reference when it
    (or each word of it) is an id in this document."""
    # The ID attributes this program writes: sections' id, examples' num,
    # list words' letter (see Section, Example, ListWord below).
    ids={el.get(a) for el in root.iter() if isinstance(el.tag,str)
                   for a in ('id','num','letter') if el.get(a)}
    bad={i for i in ids if ascii_id(i)!=i}
    if not bad:
        return root
    for el in root.iter():
        if not isinstance(el.tag,str):
            continue
        for k,v in el.attrib.items():
            words=v.split()
            if words and all(w in ids for w in words) \
                    and any(w in bad for w in words):
                el.set(k,' '.join(ascii_id(w) for w in words))
    return root
# from utilities.utilities import LazyGlobal
# globals()['_'] = LazyGlobal('_')
class Report(object):
    def __init__(self,filename,report,langname,program):
        #use program, if only for it's name
        if not hasattr(program, 'name'):
            raise AttributeError(_("the program argument to xlp.Report needs a ‘name’ attribute"))
        self.start_time=times.now()
        self.filename=filename
        self.tmpfile=self.filename+'.tmp'
        if file.exists(self.tmpfile):
            # In-process sentinel (cleared by close()->cleanup()). A crashed
            # run never reaches cleanup, so honor only a FRESH sentinel (a
            # genuinely concurrent report); clear a stale one and carry on —
            # otherwise one crash blocks this report forever.
            import os as _os
            try:
                age=times.now().timestamp()-_os.path.getmtime(self.tmpfile)
            except OSError:
                age=0
            if age < 3600:
                log.info(_("Report {} already in process; not doing again."
                        ).format(self.filename))
                return
            log.info(_("Clearing stale report lock {} (left by a crashed "
                        "run).").format(self.tmpfile))
            file.remove(self.tmpfile)
        open(self.tmpfile, 'wb').close()
        self.stylesheetdir=file.getstylesheetdir(filename)
        if self.stylesheetdir and not file.exists(self.stylesheetdir):
            log.error(self.stylesheetdir)
            self.stylesheetdir=None
        # self.tree=ET.ElementTree(ET.Element('lingPaper'))
        self.node=ET.Element('lingPaper') #self.tree.getroot()
        self.title="{} {} output report for {}".format(report,
                                                        program.name,
                                                        langname)
        log.info(_("Starting XLingPaper report file at {} with title ‘{}’").format(
                                                        filename,self.title))
        self.authors=[{'name':'Kent Rasmussen',
                        'affiliation':'SIL International',
                        'Email':'kent_rasmussen@sil.org'},
                        {'name':program.name,
                        'Email': 'https://github.com/kent-rasmussen/azt'}
                        ]
        self.langlist=list()
        self.frontmatter()
        log.info(_("Done initializing Report"))
    def close(self,me=False):
        log.info(_("Done; setting back matter, etc, now."))
        try:
            self.backmatter()
            self.languages()
            self.xlptypes()
            self.stylesheet()
            self.write()
        finally:
            self.cleanup() #ALWAYS drop the .tmp sentinel — a crash here used
            #               to leave it behind, blocking every future run
        t=times.now()-self.start_time
        # m=int(t/60)
        # s=t%60
        log.info(_("Finished in {:1.0f} minutes, {:2.3f} seconds."
                ).format(*divmod(t.total_seconds(),60)))
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
        except ImportError:
            log.info(_("Couldn’t find/import lxml, so not compiling report."))
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
        # EVERY STEP SAYS WHETHER IT WORKED, and stops the chain if not. This
        # used to swallow a failed step and hand the step before's output to
        # the next one, so a failure surfaced (if at all) several steps
        # later; and it deleted xelatex's .log whether or not it worked.
        import shutil
        etree=lxml.etree
        def xslt_errors(t):
            for e in (getattr(t,'error_log',None) or []):
                log.error("XSLT {}: {} (line {}, {})".format(
                            e.level_name,e.message,e.line,e.filename))
        self.transformsdir=file.gettransformsdir()
        if not file.exists(self.transformsdir):
            log.error(_("No PDF: {}").format(self.transformsdir))
            return
        outfile=str(self.filename) #base for the intermediate files, below
        outdir=str(file.getfilenamedir(outfile))
        stem=outfile[:-len('.xml')] if outfile.endswith('.xml') else outfile
        texfile=stem+'.tex'
        # A styled paper (publisher stylesheet attached, see stylesheet())
        # goes through the publisher transform; a plain one through the plain
        # XeLaTeX transform. This always used the publisher one, which needs
        # the stylesheet that was never found (file.getstylesheetdir).
        styled=getattr(self,'styled',None) is not None
        steps=[('XLingPapRemoveAnyContent.xsl','a'),
               ('XLingPapPublisherStylesheetXeLaTeX.xsl' if styled
                    else 'XLingPapXeLaTeX1.xsl','b')]
        # Where XLingPaper keeps its table-of-contents and index scratch; the
        # defaults are paths on the XLingPaper author's machine.
        params={'sMainSourcePath':etree.XSLT.strparam(outdir),
                'sMainSourceFile':etree.XSLT.strparam(
                                                pathlib.Path(stem).name)}
        # THE CONTENTS AND INDEX TAKE TWO ROUNDS, as in XLingPaper. The
        # transform READS <outdir>/XLingPaperPDFTemp/<name>.toc and .idx for
        # page numbers; the TeX it writes has xelatex WRITE those same files
        # (XML: <toc><tocline ref= page=/></toc>, \jobname.toc) into its
        # output directory. So: transform, xelatex into XLingPaperPDFTemp,
        # transform again with the real files, xelatex again. Before the
        # first round there are none, and a missing one stops the transform
        # ("Cannot resolve URI", 2026-10-16), so it starts with empty ones.
        name=pathlib.Path(stem).name
        pdftemp=pathlib.Path(outdir,'XLingPaperPDFTemp')
        pdftemp.mkdir(exist_ok=True)
        for ext,root_tag in (('.toc','toc'),('.idx','idx')):
            (pdftemp/(name+ext)).write_text('<{}/>'.format(root_tag),
                                             encoding='utf-8')
        # WITH THE DTD'S DEFAULT ATTRIBUTES, which the transforms test for
        # (XXE supplies them in XLingPaper proper). The report names
        # "XLingPap.dtd" relative to itself; the copy is in transformsdir.
        transformsdir=pathlib.Path(self.transformsdir)
        class _ShippedDTDs(etree.Resolver):
            def resolve(self,url,pubid,context):
                p=transformsdir/str(url).replace('\\','/').rsplit('/',1)[-1]
                if p.exists():
                    return self.resolve_filename(str(p),context)
        parser=etree.XMLParser(load_dtd=True,attribute_defaults=True,
                               no_network=True)
        parser.resolvers.add(_ShippedDTDs())
        try:
            dom=etree.parse(outfile,parser)
        except etree.XMLSyntaxError as e:
            log.info(_("Reading the report with its DTD failed ({}); reading "
                        "it without defaults").format(e))
            try:
                dom=etree.parse(outfile)
            except etree.XMLSyntaxError as e:
                log.error(_("No PDF: the report XML doesn’t parse: {}"
                            ).format(e))
                return
        ascii_ids(dom.getroot())
        source=dom
        def to_tex():
            """The report → TeX, reading whatever .toc/.idx are in
            XLingPaperPDFTemp now. True if texfile was written."""
            dom=source
            for n,(xslt,ext) in enumerate(steps):
                t=None
                try:
                    t=etree.XSLT(etree.parse(
                                str(pathlib.Path(self.transformsdir,xslt))))
                    dom=t(dom,**(params if n else {}))
                except (etree.XSLTParseError,etree.XSLTApplyError,
                        etree.XMLSyntaxError) as e:
                    log.error(_("No PDF: {xslt} failed: {e}").format(
                                                            xslt=xslt,e=e))
                    xslt_errors(t)
                    return False
                xslt_errors(t) #warnings, if it ran
                dom.write_output(outfile+ext)
            # TeXMLLikeCharacterConversion: TeX's special characters in the
            # TEXT only (the stylesheets write real specials as tex:spec).
            root=dom.getroot()
            rx.texmllike_tree(root)
            with open(outfile+'c','wb') as f:
                f.write(etree.tostring(root,encoding='utf-8'))
            t=None
            try:
                t=etree.XSLT(etree.parse(
                        str(pathlib.Path(self.transformsdir,'TeXMLLike.xsl'))))
                tex=t(root)
            except (etree.XSLTParseError,etree.XSLTApplyError) as e:
                log.error(_("No PDF: TeXMLLike.xsl failed: {}").format(e))
                xslt_errors(t)
                return False
            tex.write_output(texfile)
            log.info(_("Wrote TeX file {}").format(texfile))
            return True
        def run_xelatex(round):
            """xelatex into XLingPaperPDFTemp. True if it finished."""
            args=[xelatex,"-interaction=nonstopmode","-halt-on-error",
                  "-output-directory",str(pdftemp),texfile]
            try:
                r=subprocess.run(args,shell=False,capture_output=True,
                                 text=True,errors='replace',timeout=600)
            except (OSError,subprocess.TimeoutExpired) as e:
                log.error(_("No PDF: xelatex didn’t run: {}").format(e))
                return False
            if r.returncode:
                log.error(_("No PDF: xelatex stopped (round {round}, exit "
                            "{code}). Its log is kept at {log}. Last lines:\n"
                            "{tail}").format(round=round,code=r.returncode,
                                log=pdftemp/(name+'.log'),
                                tail='\n'.join(r.stdout.splitlines()[-25:])))
                return False #keep every intermediate file, to see why
            return True
        if not to_tex():
            return
        xelatex=shutil.which('xelatex')
        if not xelatex:
            log.error(_("No PDF: xelatex isn’t installed, or isn’t on the "
                        "PATH. The TeX file is at {}").format(texfile))
            return
        # Round 1 writes the page numbers; round 2 uses them.
        if not (run_xelatex(1) and to_tex() and run_xelatex(2)):
            return
        pdf=pdftemp/(name+'.pdf')
        if not pdf.exists():
            log.error(_("No PDF: xelatex finished but wrote no {}"
                        ).format(pdf))
            return
        os.replace(str(pdf),stem+'.pdf')
        log.info(_("PDF written: {}").format(stem+'.pdf'))
        from utilities.utilities import show_finished_pdf
        show_finished_pdf(stem+'.pdf')
        for ext in ('.tex','.xmla','.xmlb','.xmlc'):
            file.remove(stem+ext)
        shutil.rmtree(str(pdftemp),ignore_errors=True)
        # NOT DONE (the old pipeline's last line, kept as found:) # was call
        # DONE NOW as ascii_ids(), on the source ids and their references:
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
            log.error(_("Hey, not sure how this language is formatted! "
                                                            "({})").format(lang))
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
        if not getattr(self,'stylesheetdir',None):
            # init found no stylesheet dir (logged there) and set None;
            # the report is written unstyled rather than dying here —
            # this used to crash close() BEFORE write(), so the whole
            # report silently never landed on disk.
            log.info(_("No stylesheet directory; writing report unstyled."))
            return
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
    def __init__(self,parent,title=_("No Section Title!"),level=None,landscape=False):
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
    def __init__(self,parent,text=_('No Paragraph text!')):
        self.node=ET.SubElement(parent.node,'p')
        self.node.text=text
class Example(ET.Element):
    def __init__(self,parent,id,heading=None,comment=None):
        rxid=rx.id(id)
        self.node=ET.SubElement(parent.node,'example',attrib={'num':rxid})
        if heading is not None:
            headnode=ExampleHeading(self,heading,comment=comment)
class ExampleHeading():
    def __init__(self,parent,text,comment=None):
        # A comment cannot go anywhere in an example but in a heading;
        # if we need this without one, this should be reworked
        self.node=ET.SubElement(parent.node,'exampleHeading')
        self.node.text=text
        if comment:
            Comment(self,'\n'+comment)
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
            log.error(_("Not sure what kind of cell you’re looking for: {}"
                        ).format(header))
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

class Comment(ET.Element):
    def __init__(self,parent,text):
        self.node=ET.SubElement(parent.node,'comment') #,attrib={'lang':lang}
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
    from dummy import App
    program=App()
    d=Report('filetest.xml',"a non-language","Language Name >",program)
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
