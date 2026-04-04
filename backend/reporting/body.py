class Report(object):
    def consultantcheck(self):
        self.program.settings.reloadstatusdata()
        self.bylocation=False
        self.tonegroupreportcomprehensive()
        self.bylocation=True
        self.tonegroupreportcomprehensive()
    def tonegroupreportcomprehensive(self,**kwargs):
        """Should set this to do all analyses upfront, then run all in the
        background"""
        kwargs['psprofiles']=self.psprofilestodo()
        kwargs['xlpr']=self.xlpstart(reporttype='MultisliceTone',**kwargs)
        log.info("Starting comprehensive reports for {profiles}".format(
                                                        profiles=kwargs['psprofiles']))
        kwargs['usegui']=False
        for kwargs['ps'] in kwargs['psprofiles']:
            for kwargs['profile'] in kwargs['psprofiles'][kwargs['ps']]:
                # self.tonegroupreport(**kwargs) #ps=ps,profile=profile)
                self.tonegroupreport(**kwargs) #ps=ps,profile=profile)
            """Not working:"""
            # with multiprocessing.Pool(processes=4) as pool:
            #     pool.map(self.tonegroupreport,[
            #             {'ps':ps,'profile':p,'usegui':False} for p in d[ps]])
        kwargs['xlpr'].close(me=self.program.me)
    def reportmulti(self,**kwargs):
        """This backgrounds multiple reports at a time, not multiple sections
        in one report"""
        # threading.Thread(target=self.tonegroupreport,kwargs=kwargs).start()
        start_time=nowruntime()
        log.info("reportmulti starting with fn {fn} and kwargs {kwargs} ".format(
                    fn=self.reportfn.__name__,kwargs=kwargs))
        kwargs['usegui']=False
        # log.info("reportmulti continuing with kwargs {}".format(kwargs))
        if hasattr(self.program.settings,'maxpss') and self.program.settings.maxpss:
            pss=self.program.slices.pss()[:self.program.settings.maxpss]
        else:
            pss=[self.program.slices.ps()]
        d={}
        for ps in pss:
            if (hasattr(self.program.settings,'maxprofiles') and
                    self.program.settings.maxprofiles):
                d[ps]=self.program.slices.profiles(ps=ps)[:self.program.settings.maxprofiles]
            else:
                d[ps]=[self.program.slices.profile()]
        log.info("Starting background reports for {reports}".format(reports=d))
        unbackground=[]
        all=[]
        for kwargs['ps'] in pss:
            for kwargs['profile'] in d[kwargs['ps']]:
                # kwargs['ps']=ps
                # kwargs['profile']=profile
                # log.info("reportmulti background with kwargs {}".format(kwargs))
                t=multiprocessing.Process(target=self.reportfn,
                                            kwargs=kwargs)
                t.start()
                log.info(_("Starting XLP background report with kwargs {kwargs}"
                            ).format(kwargs=kwargs))
                all+=[kwargs.copy()]
                time.sleep(0.2) #give it 200ms before checking if it returned already
                if not t.is_alive():
                    ErrorNotice(_("Looks like that didn't work; you may need "
                                    "to run a report first, or not do it in "
                                    "the background ({kwargs})."
                                ).format(kwargs=kwargs))
                    unbackground+=[kwargs.copy()]
        done=all[:]
        for k in unbackground:
            done.remove(k)
        logfinished(start_time,msg=_("setting up background reports {reports}").format(reports=done))
        log.info(_("Starting reports that didn't work in the background: {reports}").format(reports=unbackground))
        for kwargs in unbackground:
            # log.info("reportmulti unbackground with kwargs {}".format(kwargs))
            self.ui.wait(msg=kwargs)
            self.reportfn(**kwargs) #run what failed in background here
            self.ui.waitdone()
        logfinished(start_time,msg=_("all reports ({reports})").format(reports=all))
    def tonegroupreport(self,usegui=True,**kwargs):
        """This should iterate over at least some profiles; top 2-3?
        those with 2-4 verified frames? Selectable with radio buttons?"""
        start_time=nowruntime()
        #default=True redoes the UF analysis (removing any joining/renaming)
        ftype=kwargs.get('ftype',self.program.params.ftype())
        def examplestoXLP(examples,parent):
            # log.info("examples : {examples} ({type})".format(examples=examples,type=type(examples)))
            counts['senses']+=1
            for example in [e for e in examples if self.analang in e.forms]:
                # skip empty examples:
                # if self.analang not in example.forms:
                #     continue
                counts['examples']+=1
                if self.program.settings.audiolang in example.forms:
                    counts['audio']+=1
                self.nodetoXLP(example,parent=parent,listword=True,
                                                showgroups=showgroups)
        analysisOK,showgroups,timestamps=self.program.status.isanalysisOK(**kwargs)
        silent=kwargs.get('silent',False)
        default=kwargs.get('default',True)
        ps=kwargs.get('ps',self.program.slices.ps())
        profile=kwargs.get('profile',self.program.slices.profile())
        checks=self.program.status.checks(wsorted=True,**kwargs)
        if not checks:
            if 'profile' in kwargs:
                log.error("{ps} {profile} came up with no checks.".format(ps=ps,profile=profile))
                return
            self.getprofile(wsorted=True)
        startnotice=_("Starting report {ps} {profile}").format(ps=ps,profile=profile)
        log.info(startnotice)
        self.program.settings.storesettingsfile()
        waitmsg=_("{ps} {profile} Tone Report in Process\n({timestamps})").format(ps=ps,profile=profile,
                                                                timestamps=timestamps)
        if usegui:
            resultswindow=ResultWindow(self.parent,msg=waitmsg)
        bits=[str(self.reportbasefilename),
                rx.urlok(ps),
                rx.urlok(profile),
                'ToneReport']
        if not default:
            bits.append('mod')
        self.tonereportfile='_'.join(bits)+'.txt'
        checks=self.program.status.checks(wsorted=True,**kwargs)
        if not checks:
            error=_("Hey, sort some morphemes in at least one frame before "
                        "trying to make a tone report!")
            log.error(error)
            if usegui:
                resultswindow.waitdone()
                resultswindow.destroy()
                ErrorNotice(error)
            return
        start_time=nowruntime()
        counts={'senses':0,'examples':0, 'audio':0}
        self.makeanalysis(**kwargs)
        # log.info("Caller function: {fn}".format(fn=callerfn()))
        if analysisOK:
            log.info(_("Looks like the analysis is good; moving on."))
            self.analysis.donoUFanalysis() #based on (sense) UF fields
        elif callerfn() == 'run': #self.tonegroupreportmulti
            log.info(_("Sorry, the analysis isn't good, and we're running "
                    "in the background. That isn't going to work, so I'm "
                    "stopping here."))
            return
        else:
            log.info(_("Looks like the analysis isn't good, but we're not "
                    "in the background, so I'm doing a new analysis now."))
            self.analysis.do() #full analysis from scratch, output to UF fields
        """These are from LIFT, ordered by similarity for the report."""
        if not self.analysis.orderedchecks or not self.analysis.orderedUFs:
            log.error("Problem with checks: {checks} (in {ps} {profile})."
                    "".format(checks=checks,ps=ps,profile=profile))
            log.error("valuesbygroupcheck: {vbgc}, valuesbycheckgroup: {vbcg}"
                        "".format(vbgc=self.analysis.valuesbygroupcheck,
                                    vbcg=self.analysis.valuesbycheckgroup))
            log.error("Ordered checks is {checks}, ordered UFs: {ufs}"
                    "".format(checks=self.analysis.orderedchecks,
                            ufs=self.analysis.orderedUFs))
            log.error("comparisonUFs: {ufs}, comparisonchecks: {checks}"
                    "".format(ufs=self.analysis.comparisonUFs,
                            checks=self.analysis.comparisonchecks))
        grouplist=[i for i in self.analysis.orderedUFs
                if len(self.analysis.sensesbygroup[i]) >= self.minwords
                ]
        dontshow=[i for i in self.analysis.orderedUFs
                if len(self.analysis.sensesbygroup[i]) < self.minwords
                ]
        if dontshow:
            log.info("Not showing groups with less than {min} words: {groups}".format(
                                                        min=self.minwords,groups=dontshow))
        checks=self.analysis.orderedchecks
        r = open(self.tonereportfile, 'w', encoding='utf-8')
        title=_("Tone Report")
        if usegui:
            resultswindow.scroll=ui.ScrollingFrame(resultswindow.frame)
            resultswindow.scroll.grid(row=0,column=0)
            window=resultswindow.scroll.content
            window.row=0
        else:
            window=None
        if 'xlpr' in kwargs:
            xlpr=kwargs['xlpr']
            s1parent=s0=xlp.Section(xlpr,title=f'{ps} {profile}')
        else:
            s1parent=xlpr=self.xlpstart(reporttype='Tone',
                            ps=ps,
                            profile=profile,
                            # bylocation=self.bylocation,
                            default=default
                            )
            if not hasattr(xlpr,'node'):
                log.info(_("Problem creating report; see previous messages."))
                if kwargs.get('usegui'):
                    self.ui.waitdone()
                xlpr.cleanup()
                return
        title=_('Introduction to {ps} {profile}').format(ps=ps,profile=profile)
        s1=xlp.Section(s1parent,title=title)
        text=_("This report follows an analysis of sortings of {ps} morphemes "
        "(roots or affixes) across the following frames: {checks}. {name} stores these "
        "sortings in lift examples, which are output here, with any glossing "
        "and sound file links found in each lift sense example. "
        "Each group in "
        "this report is distinct from the others, in terms of its grouping "
        "across the multiple frames used. Sound files should be available "
        "through links, if the audio directory with those files is in the same "
        "directory as this file.").format(ps=ps,checks=checks,name=self.program.name)
        p1=xlp.Paragraph(s1,text=text)
        text=_("As a warning to the analyst who may not understand the "
        "implications of this *automated analysis*, you may have too few "
        "groupings here, particularly if you have sorted on fewer frames than "
        "necessary to distinguish all your underlying tone melodies. On the "
        "other hand, if your team has been overly precise, or if your database "
        "contains bad information (sorting information which is arbitrary or "
        "otherwise inappropriate for the language), then you likely have more "
        "groups here than you have underlying tone melodies. However, if you "
        "have avoided each of these two errors, this report should contain a "
        "decent draft of your underlying tone melody groups. It does not "
        "pretend to tell you what the values of those groups are, nor how "
        "those groups interact with morphology in interesting ways (hopefully "
        "you can do each of these better than a computer could).")
        p2=xlp.Paragraph(s1,text=text)
        def output(window,r,text):
            r.write(text+'\n')
            if usegui:
                ui.Label(window,text=text,
                        font=window.theme.fonts['report'],
                        row=window.row,column=0, sticky='w'
                        )
                window.row+=1
        t=_("Summary of Frames by {ps} {profile} Draft Underlying Melody").format(ps=ps,profile=profile)
        m=7 #only this many columns in a table
        # Don't bother with lanscape if we're splitting the table in any case.
        if m >= len(checks) > 6:
            landscape=True
        else:
            landscape=False
        s1s=xlp.Section(s1parent,t,landscape=landscape)
        caption=' '.join([ps,profile])
        ptext=_("The following table shows correspondences across sortings by "
                "tone frames, with a row for each unique pairing. ")
        if default == True:
            ptext+=_("This is a default report, where {self.program. "
                "intentionally splits these groups, so you can see wherever "
                "differences lie, even if those differences are likely "
                "meaningless (e.g., 'NA' means the user skipped sorting those "
                "words in that frame, but this will still distinguish one "
                "group from another). To help the qualified analyst navigate "
                "such a large selection of small slices of the data, the data "
                "is sorted (both here and in the section ordering) by "
                "similarity of groups. That similarity is structured, and "
                "it is provided here, so you can see the analysis of group "
                "relationships for yourself: {ufs}. "
                "And here are the structured similarity relationships for the "
                "Frames: {checks}"
                "").format(self.program.self.program.name,
                        ufs=str(self.analysis.comparisonUFs),
                        checks=str(self.analysis.comparisonchecks))
        else:
            ptext+=_("This is a non-default report, where a user has changed "
            "the default (hyper-split) groups created by {self.program..".format(
                                                        self.program.self.program.name))
        p0=xlp.Paragraph(s1s,text=ptext)
        self.analysis.orderedchecks=list(self.analysis.valuesbycheckgroup)
        for slice in range(int(len(self.analysis.orderedchecks)/m)+1):
            locslice=self.analysis.orderedchecks[slice*m:(slice+1)*m]
            if len(locslice) >0:
                self.buildXLPtable(s1s,caption+str(slice),
                        yterms=grouplist,
                        xterms=locslice,
                        values=lambda x,y:nn(unlist(
                self.analysis.valuesbygroupcheck[y][x],ignore=[None, 'NA']
                                            )),
                        ycounts=lambda x:len(self.analysis.sensesbygroup[x]),
                        xcounts=lambda y:len(self.analysis.valuesbycheck[y]))
        #Can I break this for multithreading?
        for group in grouplist: #These already include ps-profile
            log.info("building report for {group} ({idx}/{total}, n={n})".format(group=group,
                idx=grouplist.index(group)+1,total=len(grouplist),
                n=len(self.analysis.sensesbygroup[group])
                ))
            sectitle=f'\n{str(group)}'
            s1=xlp.Section(s1parent,title=sectitle)
            output(window,r,sectitle)
            l=list()
            for x in self.analysis.valuesbygroupcheck[group]:
                values=self.analysis.valuesbygroupcheck[group][x]
                # log.info("X Values: {} ({})".format(values,type(values)))
                l.append("{x}: {values}".format(x=x,values=', '.join(
                    [i for i in self.analysis.valuesbygroupcheck[group][x]
                                                            if i is not None]
                        )))
            if not l:
                l=[_('<no frames with a sort value>')]
            # spaces>nbsp in key:value, only between k:v pairs
            text=_('Values by frame: {values}'
                    ).format(values='; '.join([i.replace(' ',' ') for i in l]))
            log.info(text)
            p1=xlp.Paragraph(s1,text)
            output(window,r,text)
            if self.bylocation:
                textout=list()
                #This is better than checks, just whats there for this group
                for check in self.analysis.valuesbygroupcheck[group]:
                    id=rx.id('x'+sectitle+check)
                    values=self.analysis.valuesbygroupcheck[group][check]
                    # log.info("Values: {} ({})".format(values,type(values)))
                    headtext='{check}: {values}'.format(check=check,values=', '.join(
                                            [i for i in values if i is not None]
                                                            ))
                    e1=xlp.Example(s1,id,heading=headtext)
                    for sense in self.analysis.sensesbygroup[group]:
                        # sense=self.program.db.sensedict[sense]
                        #This is for window/text output only, not in XLP file
                        text=sense.formatted(self.analang,self.glosslangs)
                        #This is put in XLP file:
                        if check in sense.examples:
                            examples=[sense.examples[check]] #list just one here
                            examplestoXLP(examples,e1)
                        if text not in textout:
                            output(window,r,text)
                            textout.append(text)
                    if not e1.node.find('listWord'):
                        s1.node.remove(e1.node) #Don't show examples w/o data
            else:
                for sense in self.analysis.sensesbygroup[group]:
                    #This is put in XLP file:
                    examples=list(sense.examples.values())
                    log.info("{n} exs found: {examples}".format(n=len(examples), examples=examples))
                    if examples != []:
                        id=self.idXLP(sense)+'_examples'
                        headtext=text.replace('\t',' ')
                        e1=xlp.Example(s1,id,heading=headtext)
                        log.info(_("Asking for the following {n} examples from "
                                    "id {id}: {examples}"
                                    ).format(n=len(examples),id=sense.id,examples=examples))
                        examplestoXLP(examples,e1)
                    else:
                        self.nodetoXLP(sense.ftypes[ftype],
                                        parent=s1,
                                        showgroups=showgroups)
                    output(window,r,text)
        sectitle=_('{ps} {profile} Data Summary').format(ps=ps,profile=profile)
        s2=xlp.Section(s1parent,title=sectitle)
        try:
            eps='{val:.2}'.format(val=float(counts['examples']/counts['senses']))
        except ZeroDivisionError:
            eps=_("Div/0")
        try:
            audiopercent='{val:.2%}'.format(val=float(counts['audio']/counts['examples']))
        except ZeroDivisionError:
            audiopercent=_("Div/0%")
        ptext=_("This report contains {senses} senses, {examples} examples, and "
                "{audio} sound files. That is an average of {eps} examples/sense, and "
                "{audiopercent} of examples with sound files."
                "").format(senses=counts['senses'],examples=counts['examples'],audio=counts['audio'],
                            eps=eps,audiopercent=audiopercent)
        ps2=xlp.Paragraph(s2,text=ptext)
        if 'xlpr' not in kwargs:
            xlpr.close(me=self.program.me)
        text=_("Finished in {seconds} seconds.").format(seconds=nowruntime()-start_time)
        text=logfinished(start_time,msg=_("report {ps} {profile}").format(ps=ps,profile=profile))
        logfinished(start_time)
        output(window,r,text)
        text=_("(Report is also available at {file}").format(file=self.tonereportfile)
        output(window,r,text)
        r.close()
        if usegui:
            resultswindow.waitdone()
            if self.program.me:
                resultswindow.on_quit()
        self.program.status.last('report',update=True)
    def makeresultsframe(self):
        if hasattr(self.ui,'runwindow') and self.ui.runwindow.winfo_exists:
            self.results = ui.Frame(self.ui.runwindow.frame,width=800)
            self.results.grid(column=0,
                            row=self.ui.runwindow.frame.grid_info()['row']+1,
                            columnspan=5,
                            sticky=(ui.N, ui.S, ui.E, ui.W))
            self.results.scroll=ui.ScrollingFrame(self.results)
            self.results.scroll.grid(column=0, row=1)
            self.results.row=0
        else:
            log.error("Tried to get a results frame without a runwindow!")
    def background(self,fn,**kwargs):
        kwargs['usegui']=False
        t=multiprocessing.Process(target=fn,
                                    kwargs=kwargs)
        t.start()
        log.info(_("Starting XLP background report with kwargs {kwargs}"
                    ).format(kwargs=kwargs))
        time.sleep(0.2) #give it 200ms before checking if it returned already
        if not t.is_alive():
            msg=_("Looks like that didn't work; "
                            # "you may need "
                            # "to run a report first, or "
                            "trying again not in "
                            "the background ({kwargs})."
                        ).format(kwargs=kwargs)
            log.info(msg)
            # ErrorNotice(msg)
            fn(**kwargs)
    def getresults(self,**kwargs):
        def iterateUFgroups(parent,**kwargs):
            checks=[kwargs['check']]
            #Use this to distinguish "=" checks from "≠" checks, in that order
            if 'x' in kwargs['check'] and kwargs['cvt'] not in ['CV','VC']: #CV has no C=V...
                checks=[rx.sub('x','=',kwargs['check'],count=1)]+checks
            for kwargs['check'] in checks:
                self.docheckreport(parent,**kwargs) #this needs parent
            self.coocurrencetables(xlpr)
        log.info("getresults starting with kwargs {kwargs}".format(kwargs=kwargs))
        usegui=kwargs['usegui']=kwargs.get('usegui',True)
        # log.info("getresults continuing with kwargs {}".format(kwargs))
        if usegui:
            self.ui.getrunwindow()
            self.makeresultsframe() #not for now, causing problems
        kwargs['cvt']=kwargs.get('cvt',self.program.params.cvt())
        kwargs['ps']=kwargs.get('ps',self.program.slices.ps())
        kwargs['profile']=kwargs.get('profile',self.program.slices.profile())
        kwargs['check']=kwargs.get('check',self.program.params.check())
        self.adhocreportfileXLP='_'.join([str(self.reportbasefilename)
                                        ,str(kwargs['ps'])+'-'+str(kwargs['profile'])
                                        ,str(kwargs['check'])
                                        ,'ReportXLP.xml'])
        self.checkcounts={}
        log.info("Starting XLP report with these kwargs: {kwargs}".format(kwargs=kwargs))
        xlpr=self.xlpstart(**kwargs)
        if not hasattr(xlpr,'node'):
            log.info(_("Problem creating report; see previous messages."))
            if kwargs.get('usegui'):
                self.ui.waitdone()
            xlpr.cleanup()
            return
        """"Do I need this?"""
        print(_("Getting results of Search request"))
        c1 = 'Any'
        c2 = 'Any'
        """nn() here keeps None and {} from the output, takes one string,
        list, or tuple."""
        # kwargs['formstosearch']=self.formspsprofile(**kwargs)
        text=(_("{ps} roots of form {profile} by {check}").format(ps=kwargs['ps'],
                                                    profile=kwargs['profile'],
                                                    check=kwargs['check']))
        if usegui: #i.e., showing results in window
            ui.Label(self.results, text=text).grid(column=0, row=self.results.row)
            self.ui.runwindow.wait()
        si=xlp.Section(xlpr,text)
        if self.byUFgroup:
            self.makeanalysis()
            self.analysis.donoUFanalysis()
            ufgroupsnsenses=analysis.sensesbygroup.items()
            kwargs['sectlevel']=4
            t=_("{count} checks").format(count=self.program.params.cvtdict()[kwargs['cvt']]['sg'])
            for kwargs['ufgroup'],kwargs['ufsenses'] in ufgroupsnsenses:
                if 'ufgroup' in kwargs:
                    log.info("Going to run {sg} report for UF group {group}"
                            "".format(sg=self.program.params.cvtdict()[kwargs['cvt']]['sg'],
                                    group=kwargs['ufgroup']))
                sid=' '.join([t,"for",kwargs['ufgroup']])
                s2=xlp.Section(si,sid) #,level=2
                iterateUFgroups(s2,**kwargs)
        else:
            kwargs['ufgroup']=_("All")
            iterateUFgroups(si,**kwargs)
        xlpr.close(me=self.program.me)
        if usegui:
            self.ui.runwindow.waitdone()
            if not hasattr(self,'results'): #i.e., showing results in window
                self.ui.runwindow.on_quit()
        n=0
        for ps in self.checkcounts:
            for profile in self.checkcounts[ps]:
                for ufg in self.checkcounts[ps][profile]:
                    for check in self.checkcounts[ps][profile][ufg]:
                        for group in self.checkcounts[ps][profile][ufg][check]:
                            i=self.checkcounts[ps][profile][ufg][check][group]
                            if isinstance(i,int):
                                n+=i
                            else:
                                for g2 in i:
                                    i2=i[g2]
                                    if isinstance(i2,int):
                                        n+=i2
                                    else:
                                        log.info("Not sure what I'm dealing with! "
                                                "({i2})".format(i2=i2))
        if not n: #i.e., nothing was found above
            text=_("No results for {profile}/{check} ({ps})!").format(profile=kwargs['profile'],
                                                        check=kwargs['check'],
                                                        ps=kwargs['ps'])
            log.info(text)
            if usegui: #i.e., showing results in window
                ui.Label(self.results, text=text, column=0, row=self.results.row+1)
            return
    def buildXLPtable(self,parent,caption,yterms,xterms,values,ycounts=None,xcounts=None):
        #values should be a (lambda?) function that depends on x and y terms
        #ycounts should be a lambda function that depends on yterms
        log.info("Making table with caption {caption}".format(caption=caption))
        t=xlp.Table(parent,caption)
        rows=list(yterms)
        nrows=len(rows)
        cols=list(xterms)
        ncols=len(cols)
        if nrows == 0:
            return
        if ncols == 0:
            return
        for row in ['header']+list(range(nrows)):
            if row != 'header':
                row=rows[row]
            r=xlp.Row(t)
            for col in ['header']+list(range(ncols)):
                log.log(4,"row: {row}; col: {col}".format(row=row,col=col))
                if col != 'header':
                    col=cols[col]
                log.log(4,"row: {row}; col: {col}".format(row=row,col=col))
                if row == 'header' and col == 'header':
                    log.log(2,"header corner")
                    cell=xlp.Cell(r,content='',header=True)
                elif row == 'header':
                    log.log(2,"header row")
                    if xcounts is not None:
                        hxcontents=f'{col} ({xcounts(col)})'
                    else:
                        hxcontents=f'{col}'
                    cell=xlp.Cell(r,content=rx.linebreakwords(hxcontents),
                                header=True,
                                linebreakwords=True)
                elif col == 'header':
                    log.log(2,"header column")
                    if ycounts is not None:
                        hycontents=f'{row} ({ycounts(row)})'
                    else:
                        hycontents=f'{row}'
                    cell=xlp.Cell(r,content=hycontents,
                                header=True)
                else:
                    log.log(2,"Not a header")
                    try:
                        value=values(col,row)
                        log.log(2,"value ({col},{row}):{val}".format(col=col,row=row,
                                                        val=values(col,row)))
                    except KeyError:
                        log.info("Apparently no value for col:{col}, row:{row}"
                                "".format(col=col,row=row))
                        value=''
                    finally: # we need each cell to be there...
                        cell=xlp.Cell(r,content=value)
    def xlpstart(self,**kwargs):
        ps=kwargs.get('ps',self.program.slices.ps())
        profile=kwargs.get('profile',self.program.slices.profile())
        default=kwargs.get('default',True)
        check=kwargs.get('check',self.program.params.check())
        group=kwargs.get('group',self.program.status.group())
            #this is only for adhoc "big button" reports.

        if isinstance(self, Multislice) and 'psprofiles' in kwargs:
            reporttype=' '.join([ps+' ('+'-'.join(kwargs['psprofiles'][ps])+')'
                                    for ps in kwargs['psprofiles']
                                ])
            if len(reporttype) > 200: #this should be more than enough chars
                reporttype=' '.join([ps+' ('+kwargs['psprofiles'][ps][0]+'-etc)'
                                for ps in kwargs['psprofiles']][:1]+['etc'])

        else:
            reporttype=' '.join([ps,profile])
        if isinstance(self,Multicheck):
            reporttype+=' '+'-'.join(self.cvtstodo)
        elif not isinstance(self,Tone) or isinstance(self,Segments):
            reporttype+='-'+check
            if group and not 'x' in check:
                reporttype+='='+group
        else:
            if self.bylocation:
                reporttype+='Tone-bylocation'
            else:
                reporttype+='Tone'
        if self.byUFgroup:
                reporttype+='byUFgroup'
        bits=[str(self.reportbasefilename),rx.id(reporttype),"ReportXLP"]
        if not default:
            bits.append('mod')
        reportfileXLP='_'.join(bits)+'.xml'
        xlpreport=xlp.Report(reportfileXLP,reporttype,
                        self.program.settings.languagenames[self.analang],
                        self.program# who is calling this report?
                        )
        # langsalreadythere=[]
        if hasattr(xlpreport,'node'): #otherwise, this will fail
            for lang in set([self.analang]+self.glosslangs)-set([None]):
                xlpreport.addlang({'id':lang,
                                    'name': self.program.settings.languagenames[lang]})
        return xlpreport
    def wordsbypsprofilechecksubcheckp(self,parent,**kwargs):
        # log.info("Kwargs (wordsbypsprofilechecksubcheckp): {kwargs}".format(kwargs=kwargs))
        usegui=kwargs['usegui']=kwargs.get('usegui',True)
        cvt=kwargs['cvt']=kwargs.get('cvt',self.program.params.cvt())
        ps=kwargs['ps']=kwargs.get('ps',self.program.slices.ps())
        profile=kwargs['profile']=kwargs.get('profile',self.program.slices.profile())
        check=kwargs['check']=kwargs.get('check',self.program.params.check())
        group=kwargs['group']=kwargs.get('group',self.program.status.group())
        ftype=kwargs['ftype']=kwargs.get('ftype',self.program.params.ftype())
        skipthisone=False
        checkprose='{ps} {profile} {ufgroup} {check}={group}'.format(ps=kwargs['ps'],
                                    profile=kwargs['profile'],
                                    ufgroup=kwargs['ufgroup'],
                                    check=kwargs['check'],
                                    group=kwargs['group'])
        if ('x' in kwargs['check'] and hasattr(self,'groupcomparison')
                    and self.groupcomparison):
            checkprose+='-'+self.groupcomparison
        if group.isdigit() or (hasattr(self,'groupcomparison') and
                                self.groupcomparison.isdigit()):
            log.info(_("Skipping check {check} because it would break the regex"
                        "").format(check=checkprose))
            skipthisone=True
        if skipthisone:
            return
        # log.info(checkprose)
        """possibly iterating over all these parameters, used by buildregex"""
        self.buildregex(**kwargs)
        # log.info(f"{checkprose} (wordsbypsprofilechecksubcheckp-buildregex); \n"
        #             f"regex: {self.regex}")
        matches=set(self.sensesbyforminregex(self.regex,**kwargs))
        if 'ufsenses' in kwargs:
            matches=matches&set(kwargs['ufsenses'])
        if hasattr(self,'basicreported') and check in self.basicreported:
            # log.info("Removing {n} entries already found from {total} entries found "
            #         "by {check} check".format(n=len(self.basicreported[check]),
            #                             total=len(matches),
            #                             check=check))
            # log.info("Entries found ({}):".format(len(matches)))
            matches-=self.basicreported[check]
            # log.info("{} entries remaining.".format(len(matches)))
        ufg=kwargs['ufgroup']
        n=len(matches)
        # log.info("{n} matches found!: {matches}".format(n=len(matches),matches=matches))
        if 'x' not in check:
            ncheckssimple=len(check.split('=')) #how many syllables impacted
            chks=check.split('=')+[check] #each and all together
            for r in range(1,ncheckssimple): #make other splits (e.g., V2=V3)
                chks+=check.split('=',r)+check.rsplit('=',r)
            for c in set(chks): #get each bit, and whole, too
                try:
                    self.checkcounts[ps][profile][ufg][c][group]+=n
                except KeyError:
                    try:
                        self.checkcounts[ps][profile][ufg][c][group]=n
                    except KeyError:
                        try:
                            self.checkcounts[ps][profile][ufg][c]={group:n}
                        except KeyError:
                            try:
                                self.checkcounts[ps][profile][ufg]={c:{group:n}}
                            except KeyError:
                                try:
                                    self.checkcounts[ps][profile]={ufg:{c:{
                                                                    group:n}}}
                                except KeyError:
                                    self.checkcounts[ps]={profile:{ufg:{c:{
                                                                    group:n}}}}
                                    # log.info("ps: {ps}, profile: {profile}, check: {c}, "
                                    #         "group: {group}".format(ps=ps,profile=profile,c=c,group=group))
        if 'x' in check or len(check.split('=')) == 2:
            if 'x' in check:
                othergroup=self.groupcomparison
                c=check
            else: #if len(check.split('=')) == 2:
                """put X=Y data in XxY"""
                othergroup=group
                c=rx.sub('=','x',check, count=1) #copy V1=V2 into V1xV2
            setnesteddictval(self.checkcounts,n,ps,profile,ufg,c,group,othergroup)
        if n>0:
            titlebits='x'+ps+profile+check+group
            if 'x' in check:
                titlebits+='x'+othergroup
            if 'ufgroup' in kwargs:
                titlebits+=kwargs['ufgroup']
            id=rx.id(titlebits)
            rxcomment=("These items were found with this regex:\n"
                        f"{self.regex}")
            ex=xlp.Example(parent,id,heading=checkprose,comment=rxcomment)
            if hasattr(self,'basicreported') and '=' in check:
                # log.info(self.basicreported.keys())
                # log.info("Adding to basicreported for keys {keys}"
                #         "".format(keys=check.split('=')))
                for c in check.split('='):
                    # log.info("adding {n} matches".format(n=len(matches)))
                    setnesteddictval(self.basicreported,matches,c,addval=True)
            for sense in matches:
                node=sense.ftypes[ftype]
                self.nodetoXLP(node,parent=ex,listword=True) #showgroups?
                if usegui and hasattr(self,'results'): #i.e., showing results in window
                    self.results.row+=1
                    col=0
                    for t in [node.textvaluebylang(self.analang)]+[
                                node.glossbylang(l) for l in self.glosslangs]:
                        col+=1
                        ui.Label(self.results.scroll.content,
                                text=t, font='read',
                                anchor='w',padx=10, row=self.results.row,
                                column=col,
                                sticky='w')
    def wordsbypsprofilechecksubcheck(self,parent='NoXLPparent',**kwargs):
        """This function iterates across check and group values
        appropriate for the specified self.type, profile and check
        values (ps is irrelevant here).
        Because two functions called (buildregex and getframeddata) use
        check and group to do their work, they and their
        dependents would need to be changed to fit a new paradigm, if we
        were to change the variable here. So rather, we store the current
        check and group values, then iterate across logically
        possible values (as above), then restore the value."""
        """I need to find a way to limit these tests to appropriate
        profiles..."""
        kwargs['cvt']=kwargs.get('cvt',self.program.params.cvt()) #only send on one
        ps=kwargs.get('ps',self.program.slices.ps())
        kwargs['profile']=kwargs.get('profile',self.program.slices.profile())
        #CV checks depend on profile, too
        if isinstance(self,Multicheck):
            checksunordered=self.program.status.checks(**kwargs)
            checks=self.orderchecks(checksunordered)
            # log.info("Going to do these checks: {checks}".format(checks=checksunordered))
            log.info("Going to do checks in this order: {checks}".format(checks=checks))
        else:
            checks=[kwargs.get('check',self.program.params.check())]
            """check set here"""
        for kwargs['check'] in checks: #self.checkcodesbyprofile:
            """multithread here"""
            self.docheckreport(parent,**kwargs)
    def orderchecks(self,checklist):
        checks=sorted([i for i in checklist if '=' in i], key=len, reverse=True)
        checks+=sorted([i for i in checklist if '=' not in i
                                                if 'x' not in i], key=len)
        checks+=sorted([i for i in checklist if 'x' in i], key=len)
        return checks
    def docheckreport(self,parent,**kwargs):
        kwargs['cvt']=kwargs.get('cvt',self.program.params.cvt())
        kwargs['ps']=kwargs.get('ps',self.program.slices.ps())
        kwargs['profile']=kwargs.get('profile',self.program.slices.profile())
        kwargs['check']=kwargs.get('check',self.program.params.check())
        # log.info("docheckreport starting with kwargs {kwargs}".format(kwargs=kwargs))
        groups=self.program.status.groups(**kwargs)
        group=self.program.status.group()
        self.ncvts=rx.split('[=x]',kwargs['check'])
        if 'x' in kwargs['check']:
            log.debug('Hey, I cound a correspondence number!')
            if kwargs['cvt'] in ['V','C']:
                groupcomparisons=groups
            elif kwargs['cvt'] == 'CV':
                groups=self.program.status.groups(cvt='C')
                groupcomparisons=self.program.status.groups(cvt='V')
            elif kwargs['cvt'] == 'VC':
                groups=self.program.status.groups(cvt='V')
                groupcomparisons=self.program.status.groups(cvt='C')
            else:
                log.error("Sorry, I don't know how to compare cvt: {cvt}"
                                                    "".format(cvt=kwargs['cvt']))
            log.info("Going to run report for groups {groups}".format(groups=groups))
            log.info("With comparison groups {groups}".format(groups=groupcomparisons))
            for kwargs['group'] in groups:
                for self.groupcomparison in groupcomparisons:
                    if kwargs['group'] != self.groupcomparison:
                        # log.info(f"Going to compare {kwargs['group']} with "
                        #         f"{self.groupcomparison}")
                        self.wordsbypsprofilechecksubcheckp(parent,**kwargs)
        elif group:
            log.info("Going to run subcheckp just for group {group}".format(group=group))
            self.wordsbypsprofilechecksubcheckp(parent,group=group,**kwargs)
        elif groups:
            log.info("Going to run subcheckp for groups {groups}".format(groups=groups))
            for kwargs['group'] in groups:
                self.wordsbypsprofilechecksubcheckp(parent,**kwargs)
    def idXLP(self,node):
        """node here is either a ftype node or example"""
        id='x' #string!
        bits=[
            self.program.params.cvt(),
            self.program.slices.ps(),
            self.program.slices.profile(),
            ]
        try:
            bits.append(node.locationvalue()) #for examples
            bits.append(node.tonevalue())
        except AttributeError:
            try:
                bits.append(node.ftype) #for sense fields
            except AttributeError:
                bits.append(node.id) #for senses
        for lang in self.glosslangs:
            g=node.glossbylang(lang)
            if g:
                bits+=g
        for x in bits:
            if x is not None:
                id+=x
        return rx.id(id) #for either example or listword
    def nodetoXLP(self,node,parent,listword=False,showgroups=True):
        """This will likely only work when called by
        wordsbypsprofilechecksubcheck; but is needed because it must return if
        the word is found, leaving wordsbypsprofilechecksubcheck to continue"""
        """parent is an example in the XLP report"""
        """Node here should be a field/FormParent, including an example, but
        NOT a sense (FieldParent)"""
        id=self.idXLP(node)
        if listword == True:
            ex=xlp.ListWord(parent,id)
        else:
            exx=xlp.Example(parent,id) #the id goes here...
            ex=xlp.Word(exx) #This doesn't have an id
        audio=node.textvaluebylang(self.program.db.audiolang)
        form=node.textvaluebylang(self.analang)
        # log.info("Found form {form} and audio {audio}".format(form=form,audio=audio))
        if audio:
            # log.info("Found audio!")
            url=file.getdiredrelURLposix(self.reporttoaudiorelURL,audio)
            el=xlp.LinkedData(ex,self.analang,form,str(url))
        else:
            # log.info("Found audio not!")
            el=xlp.LangData(ex,self.analang,form)
        phonetic=node.parent.sense.textvaluebyftypelang('ph',self.analang)
        if self.program.settings.showoriginalorthographyinreports and phonetic:
            elph=xlp.LangData(ex,self.analang,phonetic)
        if hasattr(node,'tonevalue') and showgroups: #joined groups show each
            elt=xlp.LangData(ex,self.analang,node.tonevalue())
        for lang in self.glosslangs:
            if lang in node.parent.sense.glosses:
                xlp.Gloss(ex,lang,node.glossbylang(lang))
    def framedtoXLP(self,framed,parent,ftype,listword=False,showgroups=True):
        """This will likely only work when called by
        wordsbypsprofilechecksubcheck; but is needed because it must return if
        the word is found, leaving wordsbypsprofilechecksubcheck to continue"""
        """parent is an example in the XLP report"""
        id=self.idXLP(framed)
        if listword == True:
            ex=xlp.ListWord(parent,id)
        else:
            exx=xlp.Example(parent,id) #the id goes here...
            ex=xlp.Word(exx) #This doesn't have an id
        if (self.program.settings.audiolang in framed.forms and
                    ftype in framed.forms[self.program.settings.audiolang] and
                    framed.forms[self.program.settings.audiolang][ftype]):
            url=file.getdiredrelURLposix(self.reporttoaudiorelURL,
                                framed.forms[self.program.settings.audiolang][ftype])
            el=xlp.LinkedData(ex,self.analang,framed.forms[self.analang][ftype],
                                                                    str(url))
        else:
            el=xlp.LangData(ex,self.analang,framed.forms[self.analang][ftype])
        if self.program.settings.showoriginalorthographyinreports and (
                    'ph' in framed.forms[self.analang] and
                    framed.forms[self.analang]['ph']):
            elph=xlp.LangData(ex,self.analang,framed.forms[self.analang]['ph'])
        if hasattr(framed,'tonegroup') and showgroups: #joined groups show each
            elt=xlp.LangData(ex,self.analang,framed.tonegroup)
        for lang in self.glosslangs:
            if lang in framed.forms:
                xlp.Gloss(ex,lang,framed.forms[lang])
    def printcountssorted(self):
        #This is only used in the basic report
        log.info("Ranked and numbered syllable profiles, by lexical category:")
        nTotal=0
        nTotals={}
        for line in self.program.slices: #profilecounts:
            profile=line[0]
            ps=line[1]
            nTotal+=self.program.slices[line]
            if ps not in nTotals:
                nTotals[ps]=0
            nTotals[ps]+=self.program.slices[line]
        print('Profiled data:',nTotal)
        """Pull this?"""
        for ps in self.program.slices.pss():
            if ps == 'Invalid':
                continue
            log.info("Part of Speech {ps}:".format(ps=ps))
            for line in self.program.slices.valid(ps=ps):
                profile=line[0]
                ps=line[1]
                log.info("{profile}: {count}".format(profile=profile,count=self.program.slices[line]))
            print(ps,"(total):",nTotals[ps])
    def printprofilesbyps(self):
        #This is only used in the basic report
        log.info("Syllable profiles actually in senses, by lexical category:")
        for ps in self.profilesbysense:
            if ps in ['Invalid','analang']:
                continue
            print(ps, [i.id for i in self.profilesbysense[ps]])
    def psprofilestodo(self):
        if isinstance(self,Multislice):
            return {ps:self.program.slices.profiles(ps=ps)[:self.program.settings.maxprofiles]
                for ps in self.program.slices.pss()[:self.program.settings.maxpss]
                }
        else:
            return {self.program.slices.ps():[self.program.slices.profile()]}
    def basicreport(self,usegui=True,**kwargs):
        """This does both multiple slices (starting with largest) and
        multiple checks (all available per profile).
        These should be separated"""
        """We iterate across these values in this script, so we save current
        values here, and restore them at the end."""
        def iteratecvt(parent,**kwargs):
            if 'ufgroup' not in kwargs:
                kwargs['ufgroup']=_("All")
            for kwargs['cvt'] in self.cvtstodo:
                t=_("{count} checks").format(count=self.program.params.cvtdict()[
                                                        kwargs['cvt']]['sg'])
                # print(t)
                log.info(t)
                sid=' '.join([t,"for",kwargs['ufgroup'],kwargs['profile'],
                            kwargs['ps']+'s'])
                s34=xlp.Section(parent,sid,level=kwargs['sectlevel'])
                maxcount=rx.countxiny(kwargs['cvt'], kwargs['profile'])
                # re.subn(cvt, cvt, profile)[1]
                self.wordsbypsprofilechecksubcheck(s34,**kwargs)
        #Convert to iterate over local variables
        log.info("basicreport starting with kwargs {kwargs}".format(kwargs=kwargs))
        instr=_("The data in this report is given by most restrictive test "
                "first, followed by less restrictive tests (e.g., V1=V2 "
                "before V1 or V2). Additionally, each word only "
                "appears once per segment in a given position, so a word that "
                "occurs in a more restrictive environment will not appear in "
                "the later less restrictive environments. But where multiple "
                "examples of a segment type occur with different values, e.g., "
                "V1≠V2, those words will appear multiple times, e.g., for "
                "both V1=x and V2=y.")
        kwargs['usegui']=usegui
        if kwargs.get('usegui'): #i.e., showing results in window
            self.ui.wait(msg=_("Running {task}").format(task=_(self.tasktitle)))
        self.basicreportfile=''.join([str(self.reportbasefilename)
                                        ,'_',''.join(sorted(self.cvtstodo)[:2])
                                        ,'_MultisliceReport.txt'])
        kwargs['psprofiles']=self.psprofilestodo()
        log.info("kwargs['psprofiles']={profiles}".format(profiles=kwargs['psprofiles']))
        reporttype='Multislice '+'-'.join(self.cvtstodo)
        xlpr=self.xlpstart(**kwargs)
        if not hasattr(xlpr,'node'):
            log.info(_("Problem creating report; see previous messages."))
            if kwargs.get('usegui'):
                self.ui.waitdone()
            xlpr.cleanup()
            return
        si=xlp.Section(xlpr,"Introduction")
        p=xlp.Paragraph(si,instr)
        sys.stdout = open(self.basicreportfile, 'w', encoding='utf-8')
        print(instr)
        log.info(instr)
        #There is no runwindow here...
        self.basicreported={}
        self.checkcounts={}
        # self.printprofilesbyps() #don't really need this
        # self.printcountssorted() #don't really need this
        t=_("This report covers {pss} Grammatical categories, "
            "with {profiles} syllable profiles in each. "
            "This is of course configurable, but I assume you don't want "
            "everything."
            "").format(pss=_("the top {n}").format(n=self.program.settings.maxpss)
                        if self.program.settings.maxpss
                        else _('all'), #fix this!
                        profiles=_("the top {n}").format(n=self.program.settings.maxprofiles)
                                    if self.program.settings.maxprofiles
                                    else _('all'))
        log.info(t)
        print(t)
        p=xlp.Paragraph(si,t)
        for kwargs['ps'] in kwargs['psprofiles']:
            profiles=kwargs['psprofiles'][kwargs['ps']]
            t=_("{ps} data: (profiles: {profiles})").format(ps=kwargs['ps'],profiles=profiles)
            log.info(t)
            print(t)
            s1=xlp.Section(xlpr,t)
            t=_("This section covers the following top syllable profiles "
                "which are found in {ps}s: {profiles}").format(ps=kwargs['ps'],profiles=profiles)
            p=xlp.Paragraph(s1,t)
            log.info(t)
            for kwargs['profile'] in profiles:
                # kwargs['formstosearch']=self.formspsprofile(**kwargs)
                t=f"{kwargs['profile']} {kwargs['ps']}s"
                s2=xlp.Section(s1,t,level=2)
                log.info(t)
                if self.byUFgroup:
                    self.makeanalysis(**kwargs)
                    self.analysis.donoUFanalysis()
                    ufgroupsnids=[(i,j) for i,j in
                                self.analysis.sensesbygroup.items()
                                #don't report small groups
                                if len(j) >= self.minwords]
                    kwargs['sectlevel']=4
                    for kwargs['ufgroup'],kwargs['ufsenses'] in ufgroupsnids:
                        if 'ufgroup' in kwargs:
                            log.info("Going to run report for UF group {group}"
                                    "".format(group=kwargs['ufgroup']))
                        sid=' '.join([t,"for",kwargs['ufgroup']])
                        s3=xlp.Section(s2,sid,level=3)
                        iteratecvt(parent=s3,**kwargs)
                        # for check in self.checks: #self.checkcodesbyprofile:
                        #     """multithread here"""
                        #     self.docheckreport(parent,check=check,cvt=cvt,**kwargs)
                else:
                    kwargs['sectlevel']=3
                    iteratecvt(parent=s2,**kwargs)
        self.coocurrencetables(xlpr)
        log.info(self.checkcounts)
        xlpr.close(me=self.program.me)
        sys.stdout.close()
        sys.stdout=sys.__stdout__ #In case we want to not crash afterwards...:-)
        if kwargs.get('usegui'):
            self.ui.waitdone()
    def coocurrencetables(self,xlpr):
        t=_("Summary Co-ocurrence Tables")
        s1s=xlp.Section(xlpr,t)
        for ps in self.checkcounts:
            s2s=xlp.Section(s1s,ps,level=2)
            for profile in self.checkcounts[ps]:
                s3s=xlp.Section(s2s,' '.join([ps,profile]),level=3)
                log.info("names used ({ps}-{profile}): {keys}".format(ps=ps,profile=profile,
                                keys=self.checkcounts[ps][profile].keys()))
                for ufg in self.checkcounts[ps][profile]:
                    checks=self.orderchecks(self.checkcounts[ps][profile][ufg])
                    columncounts={}
                    # Divide checks into those with multiple columns, and others
                    xchecks=[i for i in checks if 'x' in i]
                    # eventually, this should have logic to see how wide each
                    # table is, and whether it makes sense to put it where.
                    # short tables should go next to short tables, but no more
                    # than two (or one) wide table in a row
                    if len(xchecks)>4: #only so many tables wide on a page
                        xchecksVx=[i for i in xchecks if i.startswith('V')]
                        xchecksCx=[i for i in xchecks if (not i.startswith('V')
                                                        and i.startswith('Cx'))]
                        xchecksCyx=[i for i in xchecks if (not i.startswith('V')
                                                    and not i.startswith('Cx'))]
                    else:
                        xchecksVx=xchecks
                        xchecksCx=[]
                        xchecksCyx=[]
                    onecolchecks=[i for i in checks if 'x' not in i]
                    # Put all single column tables into one dataset:
                    for check in onecolchecks:
                        counts=self.checkcounts[ps][profile][ufg][check]
                        for row in counts:
                            try:
                                columncounts[row][check]=counts[row]
                            except (KeyError,UnboundLocalError):
                                try:
                                    columncounts[row]={check:counts[row]}
                                except (KeyError,UnboundLocalError):
                                    columncounts={row:{check:counts[row]}}
                    # Test the other checks, to see if any is wider than tall:
                    for xchecks in [i for i in
                                        [xchecksVx,xchecksCx,xchecksCyx] if i]:
                        wide=False
                        for check in xchecks:
                            counts=self.checkcounts[ps][profile][ufg][check]
                            for r in [i for i in counts if counts[i]]:
                                if len([i for i in counts[r] if counts[r][i]]
                                        )>len([i for i in counts if counts[i]]):
                                        wide=True
                        if not wide:
                            #if all are not wide, join them into one row
                            caption=' '.join([ufg,ps,profile,check])
                            table=xlp.Table(s3s,caption+' Correspondences')
                            row=xlp.Row(table)
                            for check in xchecks:
                                counts=self.checkcounts[ps][profile][ufg][check]
                                if (len(list(counts)) and
                                        len([counts[k] for k in counts])):
                                    cell=xlp.Cell(row)
                                    caption=' '.join([ufg,ps,profile,check])
                                    tableb=xlp.Table(cell,caption,numbered=False)
                                    log.debug("Counts by ({ufg}-{check}) check: {counts}".format(
                                                                    ufg=ufg,
                                                                    check=check,
                                                                    counts=counts))
                                    self.coocurrencetable(tableb,check,counts)
                        else:
                            #if they are wide, just leave them in their own tables:
                            for check in xchecks:
                                counts=self.checkcounts[ps][profile][ufg][check]
                                if (len(list(counts)) and
                                        len([counts[k] for k in counts])):
                                    log.debug("Counts by ({ufg}-{check}) check: {counts}".format(
                                                                        ufg=ufg,
                                                                        check=check,
                                                                        counts=counts))
                                    caption=' '.join([ufg,ps,profile,check])
                                    table=xlp.Table(s3s,caption+' Correspondences')
                                    self.coocurrencetable(table,check,counts)
                    #Finally, do all single column tables in one table:
                    if (columncounts and len(list(columncounts)) and
                            len([columncounts[k] for k in columncounts])):
                        log.debug("Counts by ({ufg}-{check}) check: {counts}".format(ufg=ufg,
                                                            check=check,counts=columncounts))
                        caption=' '.join([ufg,ps,profile,check])
                        table=xlp.Table(s3s,caption)
                        self.coocurrencetable(table,'x',columncounts)
    def coocurrencetable(self,table,check,counts):
        """This needs to work with an additional layer, for UF groups"""
        """Basic report doesn't seem to put out any data"""
        if 'x' in check:
            rows=[r for r,c in counts.items()
                    if [c[v] for v in c
                        if c[v]
                        ]
                ]
            cols=sorted(set(ck
                            for r,c in counts.items()
                            for ck,cv in c.items()
                            if c[ck]
                            ))
        else:
            rows=[r for r,c in counts.items()
                    if c
                ]
            cols=[check]
        maxcols=20
        if not rows:
            table.destroy()
            return
        if len(cols) >maxcols: #break table
            ncols=int(len(cols)/2)+1
            colsa=cols[:ncols]
            colsb=cols[ncols:]
            countsa={r:{ck:c[ck]
                        for ck,cv in c.items()
                        if ck in colsa
                        } for r,c in counts.items()
                    }
            countsb={r:{ck:c[ck]
                        for ck,cv in c.items()
                        if ck in colsb
                        } for r,c in counts.items()
                    }
            table1row=xlp.Row(table)
            table1cell=xlp.Cell(table1row)
            table1=xlp.Table(table1cell,numbered=False)
            self.coocurrencetable(table1,check,countsa)
            table2row=xlp.Row(table)
            table2cell=xlp.Cell(table2row)
            table2=xlp.Table(table2cell,numbered=False)
            self.coocurrencetable(table2,check,countsb)
            return
        for x1 in ['header']+rows:
            h=xlp.Row(table)
            for x2 in ['header']+cols:
                # log.debug("x1: {}; x2: {}".format(x1,x2))
                # if x1 != 'header' and x2 not in ['header','n']:
                #     log.debug("value: {}".format(self.checkcounts[
                #         ps][profile][name][x1][x2]))
                if x1 == 'header' and x2 == 'header':
                    # log.debug("header corner")
                    # cell=xlp.Cell(h,content=name,header=True)
                    cell=xlp.Cell(h,content=check,header=True)
                elif x1 == 'header':
                    # log.debug("header row")
                    cell=xlp.Cell(h,content=x2,header=True)
                elif x2 == 'header':
                    # log.debug("header column")
                    cell=xlp.Cell(h,content=x1,header=True)
                else:
                    # log.debug("Not a header")
                    if x2 == check:
                        value=counts[x1]
                    else:
                        try:
                            value=counts[x1][x2]
                        except KeyError:
                            value=''
                    if not value:
                        value=''
                    cell=xlp.Cell(h,content=value)
    def __init__(self):
        self.reportbasefilename=self.program.settings.reportbasefilename
        self.reporttoaudiorelURL=self.program.settings.reporttoaudiorelURL
        self.distinguish=self.program.settings.distinguish
        self.profilesbysense=self.program.settings.profilesbysense
        if self.program.settings.minimumwordstoreportUFgroup:
            self.minwords=self.program.settings.minimumwordstoreportUFgroup
        else: #provide a default, return to settings file for modification
            self.minwords=self.program.settings.minimumwordstoreportUFgroup=3
        self.s=self.program.settings.s
        self.byUFgroup=False
        if not isinstance(self,Multicheck) and not self.program.params.check():
            self.getcheck()
