while True:
    try:
        from xml.etree.cElementTree import *
        break
    except ImportError:
        pass
    try:
        from xml.etree.ElementTree import *
        break
    except ImportError:
        pass
    try:
        from cElementTree import *
        break
    except ImportError:
        pass
    from ElementTree import *
    break

import base64, datetime, re, os

unmarshallers = {

    # collections
    "array": lambda x: [v.text for v in x],
    "dict": lambda x:
        dict((x[i].text, x[i+1].text) for i in range(0, len(x), 2)),
    "key": lambda x: x.text or "",

    # simple types
    "string": lambda x: x.text or "",
    "data": lambda x: base64.decodestring(x.text or ""),
    "date": lambda x:
        datetime.datetime(*map(int, re.findall("\d+", x.text))),
    "true": lambda x: True,
    "false": lambda x: False,
    "real": lambda x: float(x.text),
    "integer": lambda x: int(x.text),

}

def load(file):
    parser = iterparse(file)
    for action, elem in parser:
        unmarshal = unmarshallers.get(elem.tag)
        if unmarshal:
            data = unmarshal(elem)
            elem.clear()
            elem.text = data
        elif elem.tag != "plist":
           raise IOError("unknown plist type: %r" % elem.tag)
    return parser.root[0].text
