"""Read a function's CODE, without the prose that describes it.

Dozens of tests here assert on source text, and the recurring way they fail is
by matching their own subject's explanation of itself. Three failed on their
first run for exactly that (2026-09-30) — `sensesbyps` and `slices.ps()` found
in the comment saying they had gone — and
`test_changing_the_form_realigns_the_check` failed the same afternoon by
finding `reload_for_word_check` in the comment eight lines ABOVE the call, and
so concluding the call came first.

CLAUDE.md says it as a rule: "Careful, when writing tests, to not write scans
that can't tell code from the prose describing it." This is that, once.

SPACING IS PRESERVED, because callers split on source text like `cvt()=='S'`.
An early version rebuilt the source by joining tokens, which turned that into
`params . cvt ( ) == 'S'` and made the split find nothing. So comments are
BLANKED IN PLACE at the column the tokenizer reports, leaving every other
character where it was — offsets into the result stay meaningful, which is
what an ordering assertion needs.

The tokenizer rather than `line.split('#')`, because `'#C'` is a real string
literal in this code — the word-initial syllable primitive — and a naive split
would cut those lines in half.
"""
import inspect
import io
import tokenize


def code(fn):
    """`fn`'s source with its comments and docstring removed."""
    src = inspect.getsource(fn)
    lines = src.splitlines()
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                row, col = tok.start
                lines[row - 1] = lines[row - 1][:col]
    except (tokenize.TokenError, IndentationError):
        pass  # leave the source as it is; the caller's assertions still read
    text = '\n'.join(lines)
    doc = inspect.getdoc(fn)
    if doc:
        for line in doc.splitlines():
            if line.strip():
                text = text.replace(line, '')
    return text
