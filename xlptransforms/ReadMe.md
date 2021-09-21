The XSL transforms and DTDs in this folder are from https://github.com/sillsdev/XLingPap, retrieved on September 1, 2021. While that site was not accompanied by a license, it links to software.sil.org/xlingpaper/, which contains in its footer the text:

`This software is free to use, modify and redistribute according to the terms of the MIT License`

That text contains a link to https://en.wikipedia.org/wiki/MIT_License, which under "License terms" contains the following boilerplate:

Copyright (c) `<year> <copyright holders>`

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

I have furthermore clarified with the author that I have permission to modify and redistribute this material with this larger repository.

Modifications I have made so far are limited to implementing the exslt.org nodeset function, by
- Adding `xmlns:exsl="http://exslt.org/common"` to the opening declaration
- Converting XSLT 1.0 result tree fragments like
      - select="$childDoc/root/node()"
to node sets like
      - select="exsl:node-set($childDoc)/root/node()"
