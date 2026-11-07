# coding=UTF-8
"""sameSort sets: senses a user (or the text-word import) says are one word for sorting.

Each member sense carries `<trait name="sameSort" value="<set id>"/>` (lift.Sense.samesortvalue); the id
is minted here and means nothing outside A−Z+T. Design: ~/.ontrack/agenda/azt/verify_page_join_same_word.md.

- Every sort-engine write for a sense goes to each member of its set (`members`), so members keep their
  own full copy of the sorting data: leaving a set loses nothing.
- Pages show one item per set (`representatives`), with the set's size beside it.
- A sense in no set is a set of one: `members(sense)` is `[sense]`, so call sites never branch.
"""
import uuid

from utilities import logsetup
log = logsetup.getlog(__name__)


class SameSort:
    def build(self):
        """{set id: [senses]}, from the traits in the lexicon; once per open, and kept up to date by
        join/leave."""
        self.sets = {}
        for sense in self.program.db.senses:
            setid = sense.samesortvalue()
            if setid:
                self.sets.setdefault(setid, []).append(sense)
        # A set of one is no set (its partner left, or a file was edited by hand).
        for setid in [k for k, v in self.sets.items() if len(v) < 2]:
            self.sets.pop(setid)[0].samesortvalue('')
        log.info("sameSort: {n} sets, {m} senses".format(
                    n=len(self.sets), m=sum(len(v) for v in self.sets.values())))

    def members(self, sense):
        """Every sense sorted with this one, this one first; [sense] if it is in no set."""
        setid = sense.samesortvalue()
        if not setid or setid not in self.sets:
            return [sense]
        return [sense] + [s for s in self.sets[setid] if s is not sense]

    def size(self, sense):
        return len(self.members(sense))

    def representatives(self, senses):
        """One sense per set among `senses` (the first met), in order; senses in no set pass through."""
        seen = set()
        out = []
        for sense in senses:
            setid = sense.samesortvalue()
            if setid in self.sets:
                if setid in seen:
                    continue
                seen.add(setid)
            out.append(sense)
        return out

    def join(self, a, b):
        """Put a's set and b's set together. The larger keeps its id, so the fewest senses are
        rewritten. Returns the set id."""
        ma, mb = self.members(a), self.members(b)
        if any(s in mb for s in ma):
            return a.samesortvalue()
        keep, move = (ma, mb) if len(ma) >= len(mb) else (mb, ma)
        setid = keep[0].samesortvalue() or uuid.uuid4().hex
        self.sets.pop(move[0].samesortvalue(), None)
        for sense in keep + move:
            sense.samesortvalue(setid)  # a no-op for keep's members if it already had the id
        self.sets[setid] = keep + move
        log.info("sameSort: joined {n} senses into {setid}".format(n=len(move), setid=setid))
        return setid

    def leave(self, sense):
        """Take one sense out of its set; it keeps its sorting data. A set left with one member
        stops being a set."""
        setid = sense.samesortvalue()
        if not setid:
            return
        sense.samesortvalue('')
        rest = [s for s in self.sets.get(setid, []) if s is not sense]
        if len(rest) < 2:
            for s in rest:
                s.samesortvalue('')
            self.sets.pop(setid, None)
        else:
            self.sets[setid] = rest
        log.info("sameSort: {id} left {setid}".format(id=sense.id, setid=setid))

    def __init__(self, program):
        self.program = program
        program.samesort = self
        self.build()


def representatives(program, senses):
    """One sense per sameSort set among `senses`: what to loop over when each call fans out to the
    whole set anyway (looping over every member would write each set once per member)."""
    index = getattr(program, 'samesort', None)
    return index.representatives(senses) if index else list(senses)


def marked(program, sense, text):
    """A sense's display text, with its set's size after it ('×12') when it stands for more than one
    occurrence; no words, so nothing to translate."""
    n = len(members(program, sense))
    return f"{text} ×{n}" if n > 1 else text


def members(program, sense):
    """The senses a write for `sense` goes to: its sameSort set, or [sense] when the lexicon has no
    sets (or the index isn't built yet)."""
    index = getattr(program, 'samesort', None)
    return index.members(sense) if index else [sense]


def join(program, dragged, target):
    """The verify page's drag-join: `dragged`'s set and `target`'s become one. Returns the set id, or
    None when there is no index."""
    index = getattr(program, 'samesort', None)
    if index is None:
        return None
    return index.join(dragged, target)


def covered_by(program, shown, senses):
    """Those of `senses` that some row in `shown` already stands for (is in that row's set)."""
    ids = {id(m) for s in shown for m in members(program, s)}
    return [s for s in senses if id(s) in ids]


def split(program, sense, shown):
    """Take `sense` out of its set (the members list behind ×N). Returns the senses that now need rows
    of their own on a page showing `shown`: `sense` itself, unless it was the row; and when it was,
    one of the rest, to stand for what is left of the set."""
    index = getattr(program, 'samesort', None)
    if index is None:
        return []
    before = members(program, sense)
    index.leave(sense)
    covered = {id(s) for s in covered_by(program, shown, before)}
    return [s for s in representatives(program, before) if id(s) not in covered]
