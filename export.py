#!/usr/bin/env python3
# coding=UTF-8
import logsetup
log=logsetup.getlog(__name__)
logsetup.setlevel('DEBUG',log) #for this file
log.info(f"Importing {__name__}")
import file
try: #Allow this module to be used without translation
    _
except NameError:
    def _(x):
        return x
class Exporter(object):
    """This class contains most of what is needed to pull data out of lift
    to create a tarball for ASR training."""
    def report(self):
        self.data=[]
        todo=len(self.lift.senses)
        for s in self.lift.senses:
            self.data.extend(self.getdatafromsense(s))
            yield self.lift.senses.index(s)/todo
        self.data=list(set(self.data))
        check=self.check
        if not check:
            if hasattr(self,'no_verify_check') and self.no_verify_check:
                check=_("unchecked lexical")
            elif hasattr(self,'no_verify_check'):
                check=_("Fully checked lexical")
            else:
                check=_("example (unsorted)")
        text=f"Ready to export {len(self.data)} lines of {check} data"
        log.info(text)
        self.info='\n'.join([i for i in [text,self.checkmax()] if i])
    def checkmax(self):
        if not hasattr(self,'max_rows_total') or not self.max_rows_total:
            return
        text=f"Will only export maximum ({self.max_rows_total}) rows of data "
        f" (of {len(self.data)} total)"
        if self.max_rows_total< len(self.data):
            log.info(text)
            return text
    def export(self):
        self.checkmax()
        if not hasattr(self,'max_rows_total') or not self.max_rows_total:
            self.max_rows_total=len(self.data)
        if not hasattr(self,'max_rows_per_file') or not self.max_rows_per_file:
            self.max_rows_per_file=len(self.data)
        data=self.data[:self.max_rows_total]
        ndata=len(data)
        groupsize=min(ndata,self.max_rows_per_file) #make at least one group...
        #always round up:
        ngroups=int(ndata/groupsize) + bool(ndata%groupsize)
        type=self.__class__.__name__.lower()
        check=self.check
        tarname=f'{self.analang}_{type}'
        if check:
            tarname+=f'_{check}'
        else:
            check='sentence'
        tarname+=f'_{ndata}'
        done=0
        yield done #progress
        for n in range(ngroups):
            if self.max_rows_per_file < ndata:
                archivename=f'{tarname}_{str(n)}'
            else:
                archivename=tarname
            t=file.TarBall(outputdir=self.save_dir,
                            archivename=archivename,
                            metadata_header=f'file_name,{check}')
            log.info(f"working on set {n*groupsize}:{min((n+1)*groupsize,ndata)} "
                    f"({len(data[n*groupsize:(n+1)*groupsize])} of "
                    f"{min(ndata,self.max_rows_total)})")
            for i in t.populate(data[n*groupsize:min((n+1)*groupsize,ndata)]):
                done+=1
                yield done/ndata
        print(_("Done with {}.").format(type))
    def __init__(self, **kwargs): #lift, analang, audiolang, audiodir):
        needed=set(['lift', 'analang', 'audiolang', 'audiodir'])
        kwargset=set(kwargs)
        if not kwargset.issuperset(needed):
            print(f"Missing {needed-kwargset} ({needed&kwargset} != {len(needed)}); "
                    f"can't make {self.__class__.__name__}")
            return
        for k in kwargs:
            print(k,kwargs[k])
            setattr(self,k,kwargs[k])
        self.check=kwargs.get('check',None) #in case not specified
        super(Exporter, self).__init__()

class Lexicon(Exporter):
    """This exports lexical entries with sound files and certain checking
    levels."""
    def getdatafromsense(self,sense):
        return sense.lexicalformsforASRtraining(
                                        no_verify_check=self.no_verify_check,
                                        check=self.check
                                        )
    def __init__(self, *args, **kwargs):
        super(Lexicon, self).__init__(*args, **kwargs)
        self.no_verify_check=self.analang in ['gnd']
        print(f"working with no_verify_check: {self.no_verify_check}")
class Examples(Exporter):
    """This exports Examples (from senses) with sound files."""

    def getdatafromsense(self,sense):
        return sense.examplesforASRtraining()
    def __init__(self, *args, **kwargs):
        super(Examples, self).__init__(*args, **kwargs)
if __name__ == '__main__':
    import lift
    l=Examples(lift=lift.Lift("/home/kentr/Assignment/Tools/WeSay/gnd/gnd.lift"),
            analang='gnd',
            audiolang='gnd-Zxxx-x-audio',
            audiodir='/home/kentr/Assignment/Tools/WeSay/gnd/audio',
            save_dir='/home/kentr/bin/raspy/newASR/training_data/',
            max_rows_total=120,
            max_rows_per_file=50,
            # check='V1'
            # check='V2'
            # check='C1'
        )
    for i in l.report():
        print(i)
    for i in l.export():
        print(i)
