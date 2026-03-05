
class TaskDressing:
    def setcontext(self):
        print("TaskDressing.setcontext")

class Sound:
    def setcontext(self):
        print("Sound.setcontext")
        TaskDressing.setcontext(self)

class Record(Sound):
    def setcontext(self):
        print("Record.setcontext")
        Sound.setcontext(self)

class Segments:
    def setcontext(self):
        print("Segments.setcontext")
        TaskDressing.setcontext(self) # The current bug

class WordCollectionwRecordings(Segments, Record):
    pass

print("--- Current behavior (Broken) ---")
w = WordCollectionwRecordings()
w.setcontext()

class SegmentsFixed:
    def setcontext(self):
        print("Segments.setcontext (Fixed)")
        # This is what super() does in multiple inheritance
        if hasattr(super(), 'setcontext'):
            super().setcontext()
        else:
            print("No more setcontext in MRO")

class RecordFixed(Sound):
    def setcontext(self):
        print("Record.setcontext (Fixed)")
        if hasattr(super(), 'setcontext'):
            super().setcontext()

class SoundFixed:
    def setcontext(self):
        print("Sound.setcontext (Fixed)")
        if hasattr(super(), 'setcontext'):
            super().setcontext()

class WordCollectionwRecordingsFixed(SegmentsFixed, RecordFixed, TaskDressing):
    pass

print("\n--- Fixed behavior (Using super) ---")
wf = WordCollectionwRecordingsFixed()
wf.setcontext()

print("\n--- MRO of Fixed ---")
import pprint
pprint.pprint(WordCollectionwRecordingsFixed.mro())
