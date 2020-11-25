# coding=UTF-8
import rx
class Base():
    pass
def debug():
    for ps in profiles.__iter__():
        print(ps,len(profiles[ps]),profiles[ps])
def get(db,nsyls=None):
    import time
    """db should be a lift object here, for now"""
    print("Generating theoretical syllable profiles")
    theoretical=gen(nsyls=nsyls)
    #print(theoretical)
    print("Checking real words against theoretical syllable profiles ")
    start_time=time.time() #move this to function?
    words(db,theoretical) #sets db.profileswdatabyentry, db.profileswdatabysense
    # print(db.profileswdata)
    # print(db.profileswdata[None])
    # print(len(db.profileswdata[None]))
    # print(db.profileswdata.keys())
    # print(db.profileswdata['Verbe'])
    # print(db.profileswdata['Nom']['CVCV'])
    # print(db.profileswdata['Verbe']['CVCV'])
    print("Finished generating db.profileswdatabyentry and profileswdatabysense "
            "in "+str(time.time() - start_time)+" seconds.")
    #was: output=words(self,theoretical)
    #print(output)
    #exit()
    #was: self.profiles=cull(self,output,theoretical)
    #was: self.profiles=cull(self,output,theoretical)
    print("Reducing profile sets to those that match real entries")
    db.profilesbyentry=cull(db,db.profileswdatabyentry)
    # for ps in db.profilesbyentry:
    #     print(db.profilesbyentry[ps])
    print("Reducing profile sets to those that match real senses")
    db.profilesbysense=cull(db,db.profileswdatabysense)
    # for ps in db.profilesbysense:
    #     print(db.profilesbysense[ps])
    print('Done setting up syllable profiles.')
def gen(nsyls=None): # i should add self here, for lift variable reference..
    syllables=['V','CV','CVV','CVC']
    #warning: over 3 adds 30 seconds to startup time..
    if nsyls == None:
        nsyls=2 #default if syls=None; much faster, and 2+ isn't always wanted.
    else:
        nsyls=nsyls
    print("Looking for words of",nsyls,"syllables.")
    profilestheoretical=syllables[:]
    for s in range(1,nsyls):
        """iterate over syllables adding to total profilestheoretical"""
        profilestheoreticallist=profilestheoretical[:]
        for syl in syllables:
            for prof in profilestheoreticallist:
                profilestheoretical.append(prof+syl)
    def debugnums():
        print('logical possiblities generated:',len(list(profilestheoretical)))
        print('less repetitions:',len(list(dict.fromkeys(profilestheoretical))))
    debugnums()
    return list(dict.fromkeys(profilestheoretical))

def wordsbypsprofile(db,ps,profile,regex=None):
    print("Running wordsbypsprofile...",ps,profile)
    if regex is None:
        regex=rx.fromCV(db, profile, word=True, compile=True)
    if ps not in db.profileswdatabyentry:
        db.profileswdatabyentry[ps]={}
    if ps not in db.profileswdatabysense:
        db.profileswdatabysense[ps]={}
    """This finds all entries that match the regex."""
    guidoutput=db.guidformsbyregex(regex,ps)
    senseidoutput=db.senseidformsbyregex(regex,ps)
    print('guidoutput:',len(guidoutput))
    print('senseidoutput:',len(senseidoutput))
    print('db.profiledsenseids:',len(db.profiledsenseids),db.profiledsenseids)
    for output in senseidoutput:
        print(output)
        # print(output.items())
    """This removes from the current output any entries already found."""
    guidDict = { key:value for (key,value) in guidoutput.items()
                            if key not in db.profiledguids} #later:+invalidguids}
    guidoutput=guidDict
    senseidDict = { key:value for (key,value) in senseidoutput.items()
                            if key not in db.profiledsenseids} #later:+invalidsenseids}
    senseidoutput=senseidDict
    print('len(senseidoutput)',len(senseidoutput))
    if len(guidoutput) >0:
        print(profile,'entries found:',len(guidoutput))
        if profile not in db.profileswdatabyentry[ps]:
            db.profileswdatabyentry[ps][profile]={}
        db.profileswdatabyentry[ps][profile]=guidoutput
        db.profiledguids+=db.profileswdatabyentry[ps][profile].keys()
    if len(senseidoutput) >0:
        print(profile,'senses found:',len(senseidoutput))
        if profile not in db.profileswdatabysense[ps]:
            db.profileswdatabysense[ps][profile]={}
        db.profileswdatabysense[ps][profile]=senseidoutput
        db.profiledsenseids+=db.profileswdatabysense[ps][profile].keys()
def words(db,profiles):
    db.profileswdatabyentry={}
    db.profileswdatabysense={}
    db.profiledguids=[]
    db.profiledsenseids=[]
    """These profiles need to be ordered from simple to complex, so we don't
    get an entry in a more complex profile than necessary."""
    guids=list()
    senseids=list()
    """Before doing anything else, find all the invalid entries."""
    """yes, this puts these entries one level up, but theyre invalid, and
    shouldn't depend on CV profile."""
    profile='Invalid'
    invalidguids=[]#db.guidsinvalid #list(output[profile].keys())
    invalidsenseids=[]#db.senseidsinvalid
    def debuginvalid():
        for guid in guids:
            print(guid,':',db.formbyid(guid),'\t:',db.glossbyid(guid))
    print(len(invalidguids), 'invalid entries found (earlier).')
    print("This can take awhile; please wait ... and consider why it does...")
    for regexCV in profiles:
        regex=rx.fromCV(db,regexCV, word=True, compile=True) # this has ^ and $...
        for ps in db.pss: #+[None]: Not doing this for now, to save loading time.
            wordsbypsprofile(db,ps,regexCV,regex)
    print(str(len(db.profiledguids))+" guids found in syllable profiles.")
    print(str(len(invalidguids))+" guids found with invalid data.")
    print(str(len(db.profiledsenseids))+" senseids found in syllable profiles.")
    print(str(len(invalidsenseids))+" senseids found with invalid data.")
def cull(db,output): #, theoretical): #set this to check profiles first
    profilestrimmed={}
    for ps in output.keys(): # #self.pss():
        profilestrimmed[ps]=list(output[ps].keys())
        #for regexCV in output[ps].keys(): #theoretical:
        #    if len(list(output[ps][regexCV].keys())) > 0 :
        #        profilestrimmed[ps].append(regexCV)
    return profilestrimmed
# def cullwords(self,output):
#    outputtrimmed={}
#    for ps in self.pss():
#        outputtrimmed[ps]={}
#        for regexCV in self.profiles[ps]:
#            outputtrimmed[ps][regexCV]=output[ps][regexCV]
#    return outputtrimmed
def printwords(db):
    """This assumes profiles have already been generated."""
    for ps in db.profileswdata: #lift.pss():
        if ps == 'Invalid':
            for line in db.profileswdata[ps]:
                print(ps+": "+str(line))
        else:
            for regexCV in db.profileswdata[ps]:
                for line in db.profileswdata[ps][regexCV]:
                    print(ps,":",regexCV,":"+str(line))
def printcountssorted(db):
    print("Ranked and numbered syllable profiles, by grammatical category:")
    wcounts={}
    allkeys=[]
    for k in db.profileswdatabyentry.keys():
        allkeys+=db.profileswdatabyentry[k].keys()
    print('Profiled data:',len(allkeys))
    for ps in db.profileswdatabyentry.keys():
        if ps == 'Invalid':
            print(ps,'entries found:',len(db.profileswdatabyentry['Invalid'].keys()))
        else:
            print(str(ps)+" (total): "+str(db.wordcountbyps(ps)))
            wcounts[ps]=list()
            pscount=0
            for profile in db.profileswdatabyentry[ps].keys():
                count=len(db.profileswdatabyentry[ps][profile].keys())
                pscount+=count
                wcounts[ps].append((count, profile))
            for line in sorted(wcounts[ps], reverse=True):
                print(line[0],line[1])
            print('Profiled '+str(ps)+' count: '+str(pscount))
def printprofilesbyps(db):
    print("Syllable profiles actually in entries, by grammatical category:")
    for ps in db.profileswdatabyentry.keys():
        if ps is 'Invalid':
            continue
        print(ps, db.profilesbyentry[ps])
    print("Syllable profiles actually in senses, by grammatical category:")
    for ps in db.profileswdatabysense.keys():
        if ps is 'Invalid':
            continue
        print(ps, db.profilesbysense[ps])

if __name__ == "__main__":
    #b=Base()
    output=gen(nsyls=2)
    #output=b.gen() #will use default (5) if not specified.
    print(len(output))
    print(output)
