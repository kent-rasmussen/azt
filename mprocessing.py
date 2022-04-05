#!/usr/bin/env python3
# coding=UTF-8
import threading
import multiprocessing
    q.put((name,img))
manager = multiprocessing.Manager()
return_dict = manager.dict()
q=multiprocessing.Queue()
# self.threads[name]=multiprocessing.Process(target=mkimg,
#                                 args=(name,relurl,q))
# self.threads[name]=threading.Thread(target=mkimg, args=(name,relurl))
self.threads[name].start()
for t in self.threads:
    for k,v in q.get():
        self.photo[k]=v
    self.threads[t].join()
class MyMultiprocessor():
    def __init__(self):
        self.processes=[]
        self.queue=Queue()
        self.returndict={}
    def run(self, fn, *args, **kwargs):
        """the first arg should be a unique process identifier (name)"""
        """The process should return a tuple (name, return)"""
        p.multiprocessing.Process(target=fn, args=args)
        self.processes.append(p)
        p.start()
        for t in self.processes:
            for k,v in self.queue.get():
                self.returndict[k]=v
            t.join()
        return self.returndict
