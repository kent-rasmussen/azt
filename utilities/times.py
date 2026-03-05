#!/usr/bin/env python3
# coding=UTF-8
import datetime

def now():
    try:
        # Python 3.11+
        return datetime.datetime.now(datetime.UTC)
    except AttributeError as e:
        # Python <=3.11
        return datetime.datetime.utcnow()
def modified(file):
    return datetime.datetime.fromtimestamp(file.stat().st_mtime, tz=datetime.timezone.utc)
def fixnaivedatetime(d): #needed?
    """Assume naive was made wrt UTC (as has been my practice)"""
    return d.replace(tzinfo=datetime.timezone.utc)
if __name__ == '__main__':
    from utilities import file
    f=file.getfile(__file__)
    print("It is now",now())
    print("This file was last modified at",modified(f))