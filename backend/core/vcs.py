# coding=UTF-8
from utilities.i18n import _

from utilities import logsetup
log=logsetup.getlog(__name__)

import sys
import collections

# import re
# import datetime
# import tkinter as tk
from utilities.utilities import *
from utilities import file, htmlfns
from io_put import lift
# import time
# import webbrowser
import os, platform
import subprocess
# import threading
# import json
# import itertools
# import inspect
# import multiprocessing

from utilities.error_handler import notify_error as ErrorNotice

from settings import Settings

class Repository(object):
    """SuperClass for Repository classes"""
    def legalize(self,s):
        # space, tilde ~, caret ^, or colon :
        # question-mark ?, asterisk *, or open bracket [
        # '@{','\'
        return s.replace(' ','_').replace('/','_').replace(':','_').replace('*','_'
                ).replace('?','_').replace('"','_').replace('<','_').replace('>','_'
                ).replace('|','_').replace('~','_').replace('^','_').replace('[','_'
                ).replace('@{','_').replace('\\','_')
    def checkout(self,branchname=None):
        args=['checkout']
        if not branchname:
            branchname=self.legalize(f"work_from_{self.username}")
        if self.branch_exists(branchname):
            if branchname != self.main and not self.remove_branch(branchname):
                return self.checkout(branchname+'_')
        else:
            args.append('-b')
        args.append(branchname)
        r=self.do(args)
        log.info(r)
        self.branchname() #because this changes
        # if r:
        #     r=self.pull()
        #     log.info(r)
        return r
    def branch_exists(self,branchname):
        return self.do(['branch','--list',branchname])
    def remove_branch(self,branchname):
        return self.do(['branch','-d',branchname])
    def add(self,file,force=False):
        #This function must be used to see changes
        # log.info("self.bare: {}".format(self.bare))
        if not self.bare:
            if not self.alreadythere(file):
                log.info(_("Adding {file}, which is not already there.").format(file=file))
                self.files+=[file] #keep this up to date
                # self.getfiles() #this was more work
            else:
                log.info(_("Adding {file}, which is already there.").format(file=file))
            args=['add', str(file)]
            if force:
                args.insert(1, '-f')
            self.do(args)
        # else:
        #     log.info(_("Not adding {file} to bare repo {url}").format(file=file,url=self.url))
    def commitconfirm(self,diff): #don't run the diff again...
        def ok(event=None):
            self.commitconfirmed=nowruntime()
            yes.destroy()
        def notok(event=None):
            self.commitdenied=nowruntime()
            w.on_quit()
        def recent(x):
            if (x-nowruntime()).total_seconds()<5*60:
                return True
        if hasattr(self,'commitconfirmed') and recent(self.commitconfirmed):
            log.info(_("Asked for commit confirm; returning auto True"))
            return True
        elif hasattr(self,'commitdenied') and recent(self.commitdenied):
            log.info(_("Asked for commit confirm; returning auto False"))
            return False
        log.info(_("Asked for commit confirm; asking user"))
        w, yes = self.program.vcs_ui.confirm_commit(
            diff, self.repotypename, ok, notok)
        yes.wait_window(yes)
        if not w.exitFlag.istrue():
            w.on_quit()
            log.info(_("Me not committing when asked to by {name}").format(
                                                            name=self.program.name))
            return True
    def commit_would_conflict(self):
        pass
        """git fetch origin
        git merge --no-commit <branch>
        git merge --abort"""
    def commit(self,file=None):
        #I may need to rearrange these args:
        if self.bare or self.code == 'hg': #don't commit here, at least for now
            return True
        if not file and self.code == 'git':
            file='-a' # 'git commit -a' is equivalent to 'hg commit'.
        args=['commit', '-m', 'Autocommit from AZT', file]
        #don't try to commit without changes; it clogs the log
        diff=self.diff()
        diffcached=self.diff(cached=True)
        difftext=''
        for d in [diff,diffcached]:
            if d:
                difftext+=d
        if '=======' in difftext:
            ErrorNotice(f"Merge needs to happen! {difftext}",wait=True)
            return
        if difftext and (not self.program.me or self.commitconfirm(difftext)):
            r=self.do([i for i in args if i is not None])
            log.info("commit return: {}".format(r))
            return r
        # if theres no diff, or I don't want to commit, still share commits:
        return True
    def diff(self,cached=False):
        if not self.bare:
            args=['diff']
            if cached:
                args+=['--cached']
            args+=['--stat']
            return self.do(args)
        # log.info("{} diff returned {}".format(self.repotypename,r))
    def status(self):
        args=['status']
        log.info(self.do(args))
    def clonefromUSB(self,directory):
        log.info(_("Preparing to clone to {dir} from USB repo").format(dir=directory))
        #this should be a pathlib object
        # log.info("Continuing to clone to {} from USB repo".format(directory))
        # this needs from-to args
        args=['clone', self.nonbareclonearg, self.url, self.abs_path(directory)]
        msg=_("Copying from {source} to {dest}; this may take some time."
                    "").format(source=self.url, dest=directory)
        log.info(msg)
        w=self.program.vcs_ui.show_wait(msg)
        log.info(self.do(args))
        w.close()
    def clonetoUSB(self,event=None):
        # log.info("Trying to run clonetoUSB")
        directory=self.abs_path(self.clonetobaredirname())
        log.info(_("directory: {dir}").format(dir=directory))
        if directory:
            self.mark_safe(directory)
            if not self.addifis(directory):
                args=['clone', self.bareclonearg, '.', directory] #this needs from-to
                msg=_("Copying to {dir}; this may take some time."
                            "").format(dir=directory)
                w=self.program.vcs_ui.show_wait(msg)
                log.info(self.do(args))
                self.addremote(directory)
                w.close()
            else:
                log.info(_("Found a related repository; added to settings."))
        else:
            log.info(_("No directory given; not cloning."))
    def log(self):
        args=['log']
        log.info(self.do(args))
    def commithashes(self,url=None):
        r=self.do(['log', '--format=%H'],url=url)
        if not url:
            url=self.url
        if r and 'fatal' not in r:
            log.info(_("Found {count} commits for {url}").format(count=len(r),url=url))
            return r.split('\n')
        else:
            log.info(_("Found no commits; is {url} a {repo} repo?").format(url=url,
                                                            repo=self.repotypename))
            # log.info("commithashes: {}".format(r))
            if r:
                return r #need to pass errors for processing
            else:
                return []
    def undo_pull(self):
        self.do(['reset','--hard','@{1}'])
    def share(self,remotes=None,noclone=False,nocommit=False):
        if not remotes:
            remotes=self.findpresentremotes() #do once
        if not remotes and not noclone:
            self.clonetoUSB()
        r=False
        if not nocommit:
            r=self.commit() #should always before pulling, at least here
        if nocommit|bool(r):
            r=self.pull(remotes)
        if r:
            r=self.push(remotes)
        return r #ok if we don't track results for each
    def fetch(self,remotes=None,noclone=False):
        if not remotes:
            remotes=self.findpresentremotes() #do once
        if not remotes and not noclone:
            self.clonetoUSB()
            return
        for remote in remotes:
            if self.code == 'git':
                args=['fetch',remote]
            elif self.code == 'hg':
                args=['pull',remote]
            # log.info("Pulling: {}".format(args))
            r=self.do(args)
            # log.info("Pull return: {}".format(r))
        return r #if we want results for each, do this once for each
    def try_pull_main(self,remotes):
        if self.branch == self.main:
            return
        try:
            r=self.pull(remotes,branch=self.main)
            log.info(_("Pulled from {repo} {branch} ; {result}").format(
                        repo=self.repotypename,
                        branch=self.main,
                        result=r))
            old_branch=self.branch
            self.checkout(self.main)
            self.remove_branch(old_branch) #only if fully merged
        except Exception as err:
            self.undo_pull()
    def pull(self,remotes=None,branch=None):
        if not branch:
            branch=self.branch
        if not remotes:
            remotes=self.findpresentremotes() #do once
        if not remotes:
            log.info(_("Couldn't find a local drive to pull from via {repo}; "
                    "giving up").format(repo=self.repotypename))
            return
        for remote in remotes:
            if self.code == 'git':
                args=['pull',str(remote),branch]
            elif self.code == 'hg':
                args=['pull','-u',str(remote),branch]
            log.info("Pulling: {}".format(args))
            self.try_pull_main(str(remote))
            r=self.do(args)
            log.info("Pull return: {}".format(r))
            if "Automatic merge failed" in r:
                self.undo_pull()
                self.checkout()
                self.push(remotes,setupstream=True)
                return self.pull(remotes)
        return r #if we want results for each, do this once for each
    def push(self,remotes=None,setupstream=False):
        if not remotes:
            remotes=self.findpresentremotes() #do once
        if not remotes:
            log.info(_("Couldn't find a local drive to push to via {repo}; "
                    "giving up").format(repo=self.repotypename))
            return
        for remote in remotes:
            args=['push']
            if setupstream:
                args+=['--set-upstream']
            args+=[remote,self.branch+':'+self.branch] #don't push across branches
            r=self.do(args)
            if r and 'The current branch master has no upstream branch.' in r:
                r=self.push(remotes=[remote],
                            #always keep branch names aligned.
                            setupstream=True)
            # log.info(r)
        return r #ok if we don't track results for each
    def isrelated(self,directory):
        # log.info("Checking if {} \n\tis related to {}".format(directory,
        #                                                         self.url))
        # log.info(self.remotenames)
        if self.remotenames and directory in self.remotenames:
            log.info(_("Found {dir} in settings; assuming related").format(dir=directory))
            return True #This should always be
        #Git doesn't seem to care if repos are related, but I do...
        thatrepohashes=self.commithashes(directory)
        # log.info(thatrepohashes)
        if thatrepohashes and 'fatal: not a git repository' in thatrepohashes:
            return False
        if thatrepohashes and 'does not have any commits yet' in thatrepohashes:
            thatrepohashes=[]
        thisrepohashes=self.commithashes()
        # log.info(thisrepohashes)
        if thisrepohashes and 'fatal: not a git repository' in thisrepohashes:
            return False
        if thisrepohashes and 'does not have any commits yet' in thisrepohashes:
            thisrepohashes=[]
        # with open(rx.urlok(self.url),'a') as f:
        #     for l in thisrepohashes:
        #         f.write(l+'\n')
        # with open(rx.urlok(directory),'a') as f:
        #     for l in thatrepohashes:
        #         f.write(l+'\n')
        commonhashes=set(thisrepohashes)&set(thatrepohashes)
        log.info(_("found {count} common commits: {hashes}").format(count=len(commonhashes),
                                                    hashes=list(commonhashes)[:10]))
        if len(commonhashes) >1: #just in case we find one...
            return True
        elif not len(thatrepohashes):
            log.info(_("Repository at {dir} looks empty, so I'm assuming you "
            "just initialized it").format(dir=directory))
            log.info("This use case should probably go away!! Are we "
                "initializing empty repos somewhere, or asking the user to?")
            return True
        error=_("The directory {dir} doesn't seem to have a repository related "
                "to {url}; removing.").format(dir=directory,url=self.url)
        log.info(error)
        self.removeremote(directory)
    def addifis(self,directory):
        # N.B.: I think file.exists will always fail for internet repos
        # For now, add them to git
        if isinterneturl(str(directory)): #don't rigorously test this yet; would require internet
            self.addremote(directory)
            return str(directory)
        if directory and file.exists(directory):
            # log.info("Found existing directory: {}".format(directory))
            if self.isrelated(directory):
                log.info("Found related repository: {}".format(directory))
                self.addremote(directory)
                return str(directory)
            else:
                self.removeremote(directory) #don't clutter settings
    def clonetobaredirname(self):
        d=file.getfile(file.getmediadirectory())
        if d:
            if d == d.with_suffix('.'+self.code):
                return d
            else:
                return d.joinpath(self.url).with_suffix('.'+self.code)
    def findpresentremotes(self,remote=None,firsttry=True):
        def clonetoUSB(event=None):
            # log.info("Trying to event clonetoUSB")
            self.clonetoUSB()
        l=[]
        remotesinsettings=self.remoteurls().values()
        # log.info("remotesinsettings: {}".format(remotesinsettings))
        #add to list only what is there now AND related
        # the related test will remove it if there AND NOT related.
        # Otherwise, we leave it for later, in case it just isn't there now.
        l.extend([d for d in remotesinsettings if self.addifis(d)])
        if self.remotenames:
            # log.info("self.remotenames: {}".format(self.remotenames))
            l.extend(self.remotenames)
        # log.info("remotesinsettings there: {}".format(l))
        if l:
            log.info(_("returning remotes:{remotes}").format(remotes=l))
            return [self.abs_path(i) for i in l]
        # If we're still here, offer the user one chance to plug in a drive.
        # but just do this once; don't annoy the user.
        elif self.code == 'git' and firsttry: # and me:
            # Show this only once per run, if a user doesn't have settings
            if remotesinsettings or not self.directorydontask:
                self.program.taskchooser.withdraw()
                text=_(
                "Please insert your {desc} USB now." #, if you have it
                "").format(desc=self.description)
                # clonetoUSB here will ask for a directory to put it, but won't
                # clone if the target would be there, related or not.
                # Either way, we check again for present remotes, so the cost
                # of clicking this button (instead of 'exit') when you have a
                # drive already set up is an extra file dialog —hopefully OK.
                button=(_("Create new USB"),clonetoUSB)
                if not self.program.Demo:
                    e=ErrorNotice(text,
                            title=_("No {repo} {desc} USB backup found"
                                    ).format(repo=self.repotypename,
                                            desc=self.description),
                            button=button,
                            image='USBdrive',
                            wait=True
                            )
                # log.info(self.remoteurls())
                # log.info(self.remoteurls().values())
                #At this point, the user will have cloned or not already.
                if self.remoteurls().values(): #this will have new clone value
                    return self.findpresentremotes(firsttry=False)
                else: #if still nothing, don't ask again on this run.
                    self.directorydontask=True
                    return [] #must return an interable, in any case
            else:
                return []
        else:
            return []
    def root(self):
        args=['root']
        self.root=self.do(args)
    def getfiles(self):
        args=self.leaveunicodealonesargs()
        args+=[self.lsfiles]
        # log.info("{} getfiles args: {}".format(self.code,args))
        r=self.do(args)
        if r:
            self.files=[file.getfile(i) for i in r.split('\n')]
        else:
            self.files=[]
    def do(self,args,**kwargs):
        # log.info("do args: {}".format(args))
        iwascalledby=callerfn()
        # log.info("iwascalledby1 {}".format(iwascalledby))
        if (not hasattr(self,'branch') and
                    'init' not in args and
                    iwascalledby != 'isbare'): #This calls before branchname...
            # log.info("do args: {}".format(args))
            # log.info("branch: {}".format(self.branch))
            return #don't try to do things without an actual repo
        cmd=[self.cmd,self.pwd] #-R
        if 'url' in kwargs and kwargs['url']:
            cmd.extend([str(kwargs['url'])])
        else:
            cmd.extend([str(self.url)])
        try:
            cmd.extend(self.usernameargs)
        except AttributeError as e:
            if hasattr(self,'files'): #only complain if initialized
                log.info(_("usernameargs not found ({error})").format(error=e))
                    # "; OK if initializing "
                    # "the repo."
                    # "\nYou may also get a 'fatal: not a git repository...' "
                    # "notice, if the repo isn't there yet. "
        cmd.extend([a for a in args if a]) #don't give null args
        # log.info("{} cmd args: {}".format(self.code,cmd))
        try:
            output=subprocess.check_output(cmd,
                                            stderr=subprocess.STDOUT,
                                            shell=False)
            # log.info("Command output: \n{}; {}".format(output,type(output)))
        except subprocess.CalledProcessError as e:
            output=stouttostr(e.output)
            # log.info("Error output: \n{}; {}".format(output,type(output)))
            if self.program.me and (iwascalledby in ['pull'] and
                        'rejected' not in output and
                        self.code == 'git'):
                log.info(_("Call to {repo} ({args}) gave error: \n{output}\nMerging.").format(
                                                        repo=self.repotypename,
                                                        args=' '.join(args),
                                                        output=output))
                if output and 'fatal' not in output:
                    r=self.mergetool(**kwargs)
                    if r and 'fatal' not in r:
                        self.pull(**kwargs)
            if 'The current branch master has no upstream branch.' in output:
                log.info(_("iwascalledby {caller}, but don't have upstream."
                            "").format(caller=iwascalledby))
                if iwascalledby not in ['push']:
                    try:
                        assert self.code == 'git' #don't give hg notices here
                        ErrorNotice(output)
                    except (RuntimeError,AssertionError):
                        log.info(output)
                return output
            if iwascalledby in ['pull']: #needed for logic and reporting
                return output
            if iwascalledby not in ['getusernameargs','log']:
                txt=_("Call to {repo} ({args}) gave error: \n{output}").format(
                                                        repo=self.repotypename,
                                                        args=' '.join(
                                                        [str(i) for i in
                                                        args #one or the other
                                                        # cmd #this gives git ...
                                                        ]),
                                                        output=output)
                try:
                    assert self.code == 'git' #don't give hg notices here
                    #these are states we don't want to bother the user with:
                    assert output #git config core.bare gives zero error output
                    assert iwascalledby not in ['fetch']
                    assert 'ot a git repository' not in output
                    assert 'unknown option' not in output
                    assert 'does not have any commits yet' not in output
                    assert 'error: No such remote ' not in output
                    ErrorNotice(txt)
                except (RuntimeError,AssertionError):
                    log.info(txt)
                    return output
            return
        except Exception as e:
            text=_("Call to {repo} ({args}) failed: {error}"
                ).format(
                                                        repo=self.repotypename,
                                                        args=args,
                                                        error=e)
            try:
                text+=" ({output})".format(output=output)
            except:
                pass
            try:
                assert self.code == 'git' #don't give hg notices here
                ErrorNotice(text)
            except (RuntimeError,AssertionError):
                log.info(text)
            return
        t=stouttostr(output)
        # log.info("iwascalledby2 {}".format(iwascalledby))
        if iwascalledby in ['commithashes', #never log these, even w/output
                            'lastcommitdate',
                            'lastcommitdaterelative'
                            ]:
            pass
        elif t and iwascalledby not in ['diff', #These give massive output!
                                        'getfiles',
                                        ]:
            log.info(_("{repo} {caller} {args}: {output}").format(repo=self.repotypename,
                                            caller=iwascalledby,args=args[1:],output=t))
        elif iwascalledby not in ['add', #these should log only w/output
                                    'commit',
                                    ]:
            log.info(_("{repo} {caller} {args} OK").format(repo=self.repotypename,
                                            caller=iwascalledby,args=args[1:]))
        return t
    def alreadythere(self,url):
        self.getfiles()
        if file.getreldir(self.url,url) in self.files: # as str
            # log.info(_("URL {url} is already in repo {repo}").format(url=url,repo=self.url))
            return True
        # else:
        #     log.info(_("URL {url} is not already in repo {repo}:\n{files}"
        #                 "").format(url=url,repo=self.url,files=self.files))
    def ignore(self,expression):
        if not hasattr(self,'ignored') or expression not in self.ignored:
            self.ignored.append(expression)
            self.write_ignore_contents()
    def unignore(self,expression):
        if hasattr(self,'ignored') and expression in self.ignored:
            self.ignored.remove(expression)
            self.write_ignore_contents()
    def ignorecheck(self):
        self.ignorefile=file.getdiredurl(self.url,'.'+self.code+'ignore')
        self.getignorecontents() #make sure this is up to date
        """These should all be ignored"""
        for x in self.ignorelist():
            self.ignore(x)
        self.add(self.ignorefile)
        # self.commit() #unnecessary on most occasions, can cause merge conflicts
    def getignorecontents(self):
        #This reads file contents to attribute
        try: #in case the file doesn't exist yet
            with open(self.ignorefile) as f:
                self.ignored=[i.rstrip() for i in f.readlines()]
            # log.info("self.ignored for {} now {}".format(self.code,self.ignored))
        except FileNotFoundError as e:
            log.info(_("Hope this is OK: {error}").format(error=e))
            self.ignored=[]
    def write_ignore_contents(self):
        with open(self.ignorefile,'w') as f:
            for i in self.ignored:
                f.write(i+'\n')
    def exists(self,f=None):
        if not f:
            f=self.deltadir
            log.info(_("Checking repo existence via {path}").format(path=f))
        return file.exists(f)
    def exewarning(self):
        if self.repotypename == 'Mercurial' and not self.exists():
            log.info(_("No {0} repo, nor {0} executable; moving on."
                       ).format(self.repotypename))
            return
        self.program.vcs_ui.show_exe_warning(self)
    def getusernameargs(self):
        #This populates self.usernameargs, once per init.
        self.useremail=None
        self.username=self.do(self.argstogetusername)
        if hasattr(self,'argstogetuseremail'):
            self.useremail=self.do(self.argstogetuseremail)
        if self.username:
            log.info(_("Using {repo} username '{name}'").format(repo=self.repotypename,
                                                                name=self.username))
            if self.useremail:
                log.info(_("Using {repo} useremail '{email}'").format(repo=self.repotypename,email=self.useremail))
        else:
            self.username='-'.join([self.program.name,os.getlogin(),self.program.hostname])
            log.info(_("No {repo} username found; using '{name}'"
                    "").format(repo=self.repotypename,name=self.username))
        if not self.useremail:
            self.useremail=self.program.name+'-'+os.getlogin()+'@'+self.program.hostname
            log.info(_("No {repo} useremail found; using '{email}'"
            "").format(repo=self.repotypename,email=self.useremail))
        self.usernameargs=self.argstoputuserids(self.username,self.useremail)
    def addUSBremote(self):
        # This should be a directory (or parent) with existing repo
        self.addremote(self.clonetobaredirname())
    def addremote(self,remote):
        #This may take in paths, but needs to compare strings
        remotes=self.remoteurls()
        # log.info("remote: {}; type: {}".format(remote,type(remote)))
        # log.info("remotes: {}; types: {}".format(remotes.values(),
        #                                     type(list(remotes.values())[-1])))
        if not remote or str(remote) in remotes.values(): # compare str w str
            return
        for key in ['Thing'+str(i) for i in range(1,20)]:
            if key not in remotes: #don't overwrite keys
                log.info(_("Setting {key} key with {value} value").format(key=key,value=remote))
                remotes[key]=str(remote)
                self.remoteurls(remotes) #save
                log.info(_("URL Settings now {urls}").format(urls=self.remoteurls()))
                return
    def localremotes(self):
        return [i for d in self.remoteurls().values()
                for i in [self.addifis(d)]
                if i
                if not self.isinternet(i)]
    def isinternet(self,remote):
        log.info(_("self.remotenames: {names}; remote: {remote}").format(names=self.remotenames,remote=remote))
        if remote in self.remotenames:
            remote=self.getremotenameurl(remote)
        if isinterneturl(str(remote)):
            return True
    def removeremote(self,remote):
        # This is one of two functions that touch self._remotes directly
        for k,v in self.remoteurls().items():
            if v == remote:
                del self._remotes[k]
    def remoteurls(self,remotes=None):
        # This is one of two functions that touch self._remotes directly
        # This returns a copy of the dict, so don't operate on it directly.
        # Rather, read and write using this function.
        # log.info("returning remote urls: {}".format(getattr(self,'_remotes',{})))
        if remotes and type(remotes) is dict:
            self._remotes=remotes
        elif remotes:
            log.info(_("You passed me a remotes value that isn't a dict?"))
        else:
            return getattr(self,'_remotes',{}).copy() #so I can iterate and change
    def branchname(self):
        # This reads from file, not git/hg
        if self.bare:
            repoheadfile=self.branchnamefile
        else:
            repoheadfile='.'+self.code+'/'+self.branchnamefile
        log.info(_("Looking for {repo} branch name in {file}").format(repo=self.repotypename,
                                                            file=repoheadfile))
        try:
            with file.getdiredurl(self.url,repoheadfile).open() as f:
                c=f.read()
                # log.info("Found repo head info {}".format(c))
                if c:
                    self.branch=c.split('/')[-1].strip()
                    log.info(_("Found branch: {branch}").format(branch=self.branch))
            # return self.branch
        except Exception as e:
            log.error(_("Problem finding branch name: {error}").format(error=e))
    def setdescription(self):
        self.description=_("language data")
    def populate(self):
        #this is done on normal __init__, or after an init later on.
        #These are things that need an actual repository there
        self.bare=bool(self.isbare())
        log.info(_("Repo {url} is bare: {bare}").format(url=self.url,bare=self.bare))
        self.remotenames=self.getremotenames()
        self.branchname() #This is needed for the following
        self.getusernameargs()
        self.getfiles()
        self.ignorecheck()
        try:
            log.info(_("{repo} repository object initialized on branch {branch} at {url} "
                    "for {desc}, with {count} files."
                    "").format(repo=self.repotypename, branch=self.branch, url=self.url,
                        desc=self.description, count=len(self.files)))
        except FileNotFoundError:
            log.info(_("{repo} repository object initialized at {url} "
                    "for {desc}, with {count} files."
                    "").format(repo=self.repotypename, url=self.url,
                        desc=self.description, count=len(self.files)))
    def abs_path(self,url):
        # log.info(f"abs_path given {url}")
        if not url:
           log.info(f"returning nothing for nothing: {url} ({type(url)})") 
           return
        if isinterneturl(str(url)):
            return str(url) #assume this is already fully qualified
        try:
            url=url.resolve() #if already pathlib.Path
            return url.resolve()
        except Exception: #if not already pathlib.Path
            url=file.getfile(url).resolve()
        log.info(f"abs_path returning {url} ({type(url)})")
        return url
    def __init__(self, program, url=None):
        super().__init__()
        self.program=program
        self.main='main'
        # Source Repos get self.url from GitReadOnly
        self.url = url if url else program.data_directory
        self.repotypename=self.__class__.__name__
        self.thisos=platform.system()
        self.directorydontask=False #set on init, track first request rejection
        # For testing:
        # self.thisos='Windows'
        if self.thisos == 'Linux':
            self.installpage=('https://github.com/kent-rasmussen/azt/blob/main/'
                                'docs/SIMPLEINSTALL_LINUX.md')
        elif self.thisos == 'Windows':
            self.installpage=('https://github.com/kent-rasmussen/azt/blob/main/'
                                'docs/SIMPLEINSTALL.md')
        self.deltadir=file.getdiredurl(self.url,'.'+self.code)
        self.cmd=file.findexecutable(self.code)
        if not self.cmd:
            log.info(_("No {repo} executable found!").format(repo=self.repotypename))
            self.exewarning() #needs self.deltadir
            return
        self.setdescription()
        if (not file.exists(self.deltadir) # and self.code == 'git':
            and str(self.url).endswith('.'+self.code)):# or self.code == 'hg':
            self.deltadir=self.url
        if not file.exists(self.deltadir):
            log.info(_("Not a {repo} repo ({url})? Returning").format(repo=self.repotypename,
                                                            url=self.url))
            return
        if not self.cmd:
            log.info(_("Found no {repo} executable!").format(repo=self.repotypename))
            self.exewarning()
            return #before getting a file list!
        self.populate() #get files, etc.

class Mercurial(Repository):
    def ignorelist(self):
        return ['*.pdf','*.xcf',
                '*.hg','*~',
                ]
    def leaveunicodealonesargs(self):
        return []
    def argstoputuserids(self,username,email):
        return ['--config','ui.username={username}'.format(username=username)] # just one field
    def choruscheck(self):
        rescues=[]
        for file in self.files:
            if str(file).endswith('.ChorusRescuedFile'):
                rescues.append(file)
        if rescues:
            error=_("You have the following files (in {url}) that need to be "
                    "resolved from Chorus merges:\n {files}"
                    "").format(url=self.url,files='\n'.join(rescues))
            log.error(error)
            ErrorNotice(error,title=_("Chorus Rescue files found!"))
            if self.program.me:
                exit()
    def makebare(self):
        args=['update', 'null']
    def isbare(self):
        # any return implies a working directory parent (not bare)
        return not self.do(['parent'])
    def getremotenames(self):
        pass
    def mark_safe(self,directory):
        pass
    def __init__(self, program, url=None):
        self.code='hg'
        self.branchnamefile='branch'
        # self.cmd=self.program.hg
        self.wdownloadsurl='https://www.mercurial-scm.org/wiki/Download'
        self.wexename='Mercurial-6.0-x64.exe'
        self.wexeurl=('https://www.mercurial-scm.org/release/windows/{exe}'
                        ''.format(exe=self.wexename))
        self.pwd='--cwd'
        self.lsfiles='files'
        self.argstogetusername=['config', 'ui.username']
        self.bareclonearg='-U'
        self.nonbareclonearg=''
        super().__init__(program, url)
        # These files are just ignored in git, but if Chorus put something
        # there, we want to know
        if hasattr(self,'files'):
            self.choruscheck()
        else:
            self=None

class Git(Repository):
    def stash(self):
        r=self.do(['stash'])
        return r
    def unstash(self):
        r=self.do(['stash', 'apply'])
        return r
    def ignorelist(self):
        return ['*.pdf','*.xcf',
                'XLingPaperPDFTemp/**',
                '*backupBeforeLx2LcConversion',
                './*.txt', '*.7z', '*.zip','*ori',
                '__pycache__/**', '*(copy)*',
                'lift_url.py',
                'ui_lang.py',
                '*~',
                'userlogs/**',
                'test*wav',
                'excess/**',
                'images/archive/**',
                'images/scaled/**',
                'reports/**',
                '*.ChorusNotes',
                '*.WeSayUserMemory',
                '*.WeSayConfig*',
                '*.WeSayUserConfig',
                '*.ChorusRescuedFile',
                '*.git',
                # '*.ini',
                # '*lift.*',
                '*.lift*txt',
                ]
    def mergetool(self,**kwargs):
        args=['mergetool', '--tool=xmlmeld']
        r=self.do(args,**kwargs)
        log.info(r)
        return r
        # git mergetool --tool=<tool>' may be set to one of the following:
		# araxis
		# kdiff3
		# meld
    def makebare(self):
        args=['config', '--bool', 'core.bare', 'true']
    def isbare(self):
        # log.info("Running isbare")
        r=self.do(['config', 'core.bare'])
        # log.info("isbare returns {}".format(r))
        if r != 'false': # if it is, don't return, i.e., False.
            return r # pass on the config value, if not 'false', which == True
    def leaveunicodealonesargs(self):
        return ['-c','core.quotePath=false']
    def argstoputuserids(self,username,email):
        return ['-c', 'user.name={name}'.format(name=username),
                '-c', 'user.email={email}'.format(email=str(email))]
    def init(self):
        args=['init', '--initial-branch=main']
        r=self.do(args)
        if 'unknown option' in r:
            args=['init']
            r=self.do(args)
        log.info(_("init: {result}").format(result=r))
        self.populate() #because this won't have been done yet
        # git config branch.$branchname.mergeoptions '-X ignore-space-change'
    def lastcommitdate(self):
        args=['log', '-1', '--format=%cd']
        r=self.do(args)
        # log.info(r)
        return r
    def lastcommitdaterelative(self):
        args=['log', '-1', '--format=%ar']
        r=self.do(args)
        # log.info(r)
        return r
    def getremotenames(self):
        args=['remote']
        r=self.do(args)
        if r:
            r=r.split('\n')
        else:
            r=[] # This should always be iterable
        log.info(_("Using these remotes: {remotes}").format(remotes=r))
        return r
    def getremotenameurl(self,remotename):
        args=['remote', 'get-url', remotename]
        r=self.do(args)
        if 'error: No such remote ' not in r:
            return r
    def mark_safe(self,directory=None):
        if not directory:
            directory=self.url
        directory=self.abs_path(directory)
        if directory in self.get_all_safe():
            log.info(_("Mark_safe: {directory} already safe").format(directory=directory))
            return
        args=['config', '--global', '--add', 'safe.directory', str(directory)]
        r=self.do(args)
        if r:
            log.info(_("Mark_safe returned {result} for {directory}").format(result=r,directory=directory))
    def get_all_safe(self):
        args=['config', '--get-all', 'safe.directory']
        r=self.do(args)
        if r:
            r=[self.abs_path(i) for i in r.split('\n') if r]
        if r:
            log.info(_("get_all_safe returned {result}").format(result=r)) #str
            return r
        else:
            return []
    def __init__(self, program, url=None):
        # self.url=url
        self.code='git'
        self.branchnamefile='HEAD'
        self.wdownloadsurl='https://git-scm.com/download/win'
        self.wexename='Git-2.33.0.2-64-bit.exe'
        self.wexeurl=('https://github.com/git-for-windows/git/releases/'
                        'download/v2.33.0.windows.2/{exe}').format(exe=self.wexename)
        self.pwd='-C'
        self.lsfiles='ls-files'
        self.argstogetusername=['config', '--get', 'user.name']
        self.argstogetuseremail=['config', '--get', 'user.email']
        self.bareclonearg='--bare'
        self.nonbareclonearg=''
        super().__init__(program, url)
        self.unignore('*.ini') #used to ignore this
        self.unignore('*.txt') #used to ignore this
        self.mark_safe()

class GitReadOnly(Git):
    def exewarning(self):
        pass #don't worry about it for this one
    def share(self,event=None):
        """This method should only ever pull or push, depending on who
        is doing it"""
        # this will mostly operate on all present sources (internet and USB),
        # reporting failures as appropriate. I hope users will be OK with that
        r={}
        if self.program.me: #no one else should push changes
            method=Repository.push
            # This doesn't mind if there is no USB:
            remotes=self.localremotes() #don't publish to internet this way
            log.info(_("remotes: {remotes}").format(remotes=remotes))
            for remote in remotes: #iterate here to keep results
                r[remote+'/'+self.branch]=method(self,remotes=[remote])
            # self.stash()
            self.switchbranches()
            for remote in remotes: #iterate here to keep results
                r[remote+'/'+self.branch]=method(self,remotes=[remote])
            self.switchbranches()
            # self.unstash()
        else:
            method=Repository.pull
            #make sure we at least try the github remote:
            # User is asked for a USB if nothing is found here:
            remotes=self.findpresentremotes(firsttry=False) #don't ask
            homeurl=self.program.url+'.git'
            remotes.extend([homeurl])
            log.info(_("remotes: {remotes}").format(remotes=remotes))
            self.fetch(remotes)
            for remote in remotes:
                r[remote+'/'+self.branch]=method(self,remotes=[remote])
        return r
        remotes=self.findpresentremotes() #do once
        if not remotes:
            return
        branches = ['main',self.program.testversionname]
        fns = [self.testversion, self.reverttomain]
        if self.branch != 'main':
            branches.reverse()
            fns.reverse()
        try:
            for i in range(2):
                log.info(_("Running index {index} ({branch} {fn})").format(index=i,branch=branches[i],fn=fns[i]))
                #not pulling here, as not sharing in that direction.
                r=Repository.push(self,remotes=remotes,branch=branches[i])
                if r:
                    r=fns[i]()
        except Exception as e:
            ErrorNotice(e)
    def switchbranches(self):
        if self.branch == 'main':
            self.testversion()
        else:
            self.reverttomain()
    def reverttomain(self,event=None):
        r=self.checkout('main')
        """need to also
        git reset --hard origin/main
        """
        log.info(r)
        if self.branch == 'main':
            return True
        else:
            ErrorNotice(r)
    def testversion(self,event=None):
        r=self.checkout(self.program.testversionname)
        log.info(r)
        if self.branch == self.program.testversionname:
            return True
        else:
            ErrorNotice(r)
    def add(self,file):
        pass
    def commit(self,file=None):
        pass
    def setdescription(self):
        self.description=_("AZT source")
    def unignore(self,expression):
        pass #don't mess with this repo!
    def __init__(self, program, url=None):
        self.program=program
        if url is None: 
            if hasattr(program,'aztdir'):
                url=program.aztdir
            else:
                raise ValueError(_("No url provided to {class_name} and program "
                                    "has no aztdir").format(class_name=self.__class__.__name__,program=program.name))
        super().__init__(program, url)
