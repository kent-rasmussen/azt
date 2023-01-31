from xml.etree import ElementTree as ET

def iselement(n):
    return isinstance(n,ET.Element)
def prettyprint(node):
    # This fn is for seeing the Element contents before writing them (in case of
    # ElementTree errors that aren't otherwise understandable).
    if not isinstance(node,ET.Element):
        log.info("didn't prettyprint {}".format(node))
        return
    t=0
    lines=[]
    def do(node,t):
            line="{}{} {}: {}".format('\t'*t,node.tag,node.attrib,
                    "" if node.text is None
                    or set(['\n','\t',' ']).issuperset(node.text)
                    else node.text)
            lines.append(line)
            log.info(line)
            t=t+1
            for child in node:
                do(child,t)
            t=t-1
    do(node,t)
    return '\n'.join(lines)
