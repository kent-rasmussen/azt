#!/usr/bin/env python3
# coding=UTF-8
"""This file runs the actual GUI for lexical file manipulation/checking"""


# import do
import profiles
#import sys
#import re
#import globalvariables
#import numpy
import locale
import gettext
try: #Allow this module to be used without translation
    _
except NameError:
    def _(x):
        return x
#class Check(object):
#    pass
def doprofiles(db):
    profiles.printcountssorted(db)
def doprofilesbyps(db):
    profiles.printprofilesbyps(db)
def doprintwords(db):
    profiles.printwords(db)
"""This fuctionality is in words()"""
#def isguidinvaliddata(self,guid):
#    """This checks to see if a guid is listed in the profile data"""
#    x=0
#    for psdata in self.profileswdata.values():
#        for profiledata in psdata.values():
#            if re.search(' ',guid): #, in profiledata.keys(): #(contains space, etc.)
#                return #if we find it, stop
#    return guid #if we don't find it, return the guid.
"""Removed this to remove do; do I need it?"""
# def getbypsregex(db,ps,regex):
#     regex=do.makeregex(regex, word=False, compile=True) #basically, just compile.
#     guids=db.guidformsbyregex(ps,regex).keys() #idsbylexemeregexnps
#     for guid in guids:
#         printentry(db,guid)
#     print(len(guids), 'entries found.')
def printsense(db,match,ps=None,lang=None):
    senseid=match[0]
    form=match[1]
    glossordefn=db.glossordefn(senseid=senseid,lang=db.glosslang)
    if len(glossordefn) >= 1: #if it's an empty list
        glossordefn = glossordefn[0]
    print('\t',form,"'"+str(glossordefn)+"'","("+str(ps)+")")
def printentry(db,match,ps=None,lang=None):
    guid=match[0]
    form=match[1]
    glossordefn=db.glossordefn(guid=guid,lang=db.glosslang)
    if len(glossordefn) >= 1: #if it's an empty list
        glossordefn = glossordefn[0]
    print('\t',form,"'"+str(glossordefn)+"'","("+str(ps)+")")
def isguidinprofiledata(db,guid):
    """This checks to see if a guid is listed in the profile data"""
    x=0
    #print(lift.profileswdata.keys())
    for ps in db.profileswdata.keys():
        if ps == 'Invalid':
            continue
        else:
            #print(lift.profileswdata[ps].keys())
            for profile in db.profileswdata[ps].keys():
                if guid in list(db.profileswdata[ps][profile].keys())+list(db.profileswdata['Invalid'].keys()):
                    return #if we find it, stop
    return guid #if we don't find it, return the guid.
def wordsbypsprofilechecksubcheck(check,pss=None,profs=None,checks=None,subchecks=None,nsyls=None):
    """I need to find a way to limit these tests to appropriate profiles..."""
    print('Running wordsbypsprofilechecksubcheck')#pss=('Nom','Verbe')
    #profiles=('CVCVC',)
    #checks=('V1','V1=V2','V1=V2=V3')
    #print(lift.vowels)
    #check=Check(nsyls=nsyls) #from lift_do
    db=check.db
    # profiles.printprofilesbyps(db)
    # profiles.printcountssorted(db)
    subchecks=db.v[db.analang] #('a',) just the vowels, not method or regex
    #print(subchecks)
    check.type='V'
    for check.profile in profs:
        for check.name in checks:
            if len(check.name) == 1:
                print(_("Error!"),checks,_("Doesn't seem to be list formatted."))
            for check.subcheck in subchecks:
                print(check.ps,check.profile,check.name,check.subcheck,':')
                check.buildregex()
                for check.ps in pss:
                #print(check.regexCV)
                #exit()
                #self.regex=self.exib.cvregex(self.regexCV, word=True, compile=True)
                    for match in db.guidformsbyregex(check.regex,ps=check.ps).items(): #db.idsbylexemeregexnps(check.ps,check.regex).keys(): #compiled!
                        # print(match) #entry=lift.Entry(lift,guid)
                        printentry(db,match,ps=check.ps)
                    for match in db.senseidformsbyregex(check.regex,ps=check.ps).items(): #db.idsbylexemeregexnps(check.ps,check.regex).keys(): #compiled!
                        # print(match) #entry=lift.Entry(lift,guid)
                        printsense(db,match,ps=check.ps)
                        #print('\t',guid,entry.citation,"'"+str(entry.gloss)+"'","("+str(entry.ps)+")" )
def wordsnotinregexes(lift,showwords=True):
    import time
    print(_("Checking for words not covered by current processing."))
    print(_("This includes data in regexes, or with invalid characters or no ps."))
    print(_("This can take some time."))
    start_time=time.time()
    missingnum=0
    maxmissingnum=0 #20
    missingguids=list()
    for guid in lift.guids():
        #print(guid)
        """Put earlier!"""
        #self.profileswdata['invalid']=(isguidinvaliddata(self,guid)) #guids not in data.
        missingguids.append(isguidinprofiledata(lift,guid)) #guids not in data.
    for guid in missingguids:
        if guid is not None:
            missingnum+=1
            if showwords == True:
                printentry(lift,guid)
                #print(guid,self.formbyid(guid),"'"+str(self.glossbyid(guid))+"'","("+str(self.psbyid(guid))+")")
            if (missingnum>maxmissingnum) and (maxmissingnum != 0):
                return
    print(_("Found ")+str(missingnum)+_(" words not covered by current regexs in ")+
            str(time.time() - start_time)+_(" seconds."))
if __name__ == "__main__":
    """These modules are needed to test/run these reports"""
    import lift
    import lift.file
    import time
    import setdefaults
    start_time=time.time() #move this to function?
    def makelift(nsyls=None): #only do this if not calling lift.Check()!!
        filename=lift.file.getfilename()
        return lift.Lift(filename,nsyls=nsyls)
    def makeentry(lift,guid): #not sure why I have this..
        return lift.Entry(lift,guid)
    def nsylcheck(x):
        for nsyls in range(1,x+1):
            print("working on "+str(nsyls)+" syllables")
            makelift(nsyls=nsyls)
    def debug():
        print(filename)
        V=lift.v
        C=lift.c
        print('V='+V)
        print('C='+C)
        print("CV: "+regex.fromCV('CV'))
    """This doesn't need lift=, below..."""
    """If you call lift and Check(), you will load the lift file twice."""
    """I might want these to set up the following:"""
    #nsyls=2
    #db=makelift(nsyls=nsyls) #only do this if not calling lift.Check()!!
    """Think about when to do the profiles, as it takes awhile."""
    """For instance, if you're calling a Check, that will be done later,
    and you may not have what you need now to do it. (e.g., defaults)"""
    #profiles.get(db, nsyls=nsyls) #what classes/functions require this?
    """This configured reports I want to run from time to time"""
    def getbyregex(db):
        regex=' +'
        ps='Nom'
        getbypsregex(db,ps,regex)
    """Call them here"""
    #original_stdout = sys.stdout
    #with open('report.txt', 'w') as f:
    #    sys.stdout = f # Change the standard output to the file we created.
    # basicreport(nsyls=2) #don't compile lift first. Just run this.
    #    sys.stdout = original_stdout
    #profiles.printcountssorted(db)
    #wordsnotinregexes(lift) #,showwords=False
    # printwords(lift)
    #profilesbyps(lift)
    #profiles(lift)
    """8 syllables can take 30 minutes to run, so compare your output on
    earlier syllables to see if you're getting any more words..."""
    #nsylcheck(8) #how many syllables do you want to check for?
    """make lift.get.lift functions to
        output (val,n) tuples
        order by n and output val to list"""
    #form=lift.formsbyps(None)
    #print(str(form))
    """These are for debugging"""
    #form=lift.formsbyregex(None)
    #exit()
    #guid='3206f7aa-73a8-4bbf-a696-2b0f3b5fc4b5'
    #entry=lift.Entry(lift,guid)
    #gloss=entry.get.gloss(entry,lift.glosslang)
    #print('by entry:',gloss)
    #gloss=lift.glossbyid(guid)
    #print('from lift:',gloss)
    def test():
        import timeit #for testing; remove in production
        print("starting test (takes more time!)")
        times=1
        print(str(timeit.timeit(makelift, number=times))+"("+str(times)+" times)")
    #print('Analysis languages: '+str(lift.analangs()))
    #print('Gloss languages: '+str(lift.glosslangs()))
    print("Finished in "+str(time.time() - start_time)+" seconds.")
