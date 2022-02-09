<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0" xmlns:tex="http://getfo.sourceforge.net/texml/ns1">
    <xsl:output encoding="UTF-8" indent="no" method="text"/>
    <!-- 
        A transform to produce TeXML-like output.  (see http://getfo.org/texml/)
        This version has some extensions for formatting white space (more finely as far as I can tell).
        The main reason for not using TeXML itself is that TeXML requires Python and I do not want to 
        force XLingPaper users to have to install a version of Python for TeXML when that version may 
        conflict with other versions of Python they already have installed.  Furthermore, this approach
        makes the installation package much smaller (we do not need to include Python).
        
        This transform does not convert TeX special characters.  It only handles the <tex:*> elements.
        See TeXMLLikeCharConv.c for the TeX special characters conversion tool (which should be run
        before this transform).
    -->
    <xsl:template match="/tex:TeXML">
        <xsl:apply-templates/>
    </xsl:template>
    <!-- 
        cmd
    -->
    <xsl:template match="tex:cmd">
        <xsl:if test="@nl1='1'">
            <xsl:text>&#x0a;</xsl:text>
        </xsl:if>
        <xsl:text>\</xsl:text>
        <xsl:value-of select="@name"/>
        <xsl:apply-templates/>
        <xsl:if test="not(tex:parm)">
            <xsl:choose>
                <xsl:when test="@sp='1'">
                    <xsl:text>&#x20;</xsl:text>
                </xsl:when>
                <xsl:when test="@gr='0'"/>
                <xsl:otherwise>
                    <xsl:text>{}</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:if test="@nl2='1'">
            <xsl:text>&#x0a;</xsl:text>
        </xsl:if>
    </xsl:template>
    <xsl:template match="tex:cmd[@name='XeTeXpdffile' or @name='XeTeXpicfile']">
        <xsl:text>\</xsl:text>
        <xsl:value-of select="@name"/>
        <xsl:call-template name="NormalizeFileNameCharacters"/>
        <xsl:if test="not(tex:parm)">
            <xsl:choose>
                <xsl:when test="@sp='1'">
                    <xsl:text>&#x20;</xsl:text>
                </xsl:when>
                <xsl:when test="@gr='0'"/>
                <xsl:otherwise>
                    <xsl:text>{}</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:if test="@nl2='1'">
            <xsl:text>&#x0a;</xsl:text>
        </xsl:if>
    </xsl:template>
    <!-- fix up tilde in url so the actual URL is correct -->
    <xsl:template
        match="text()[contains(.,'\textasciitilde{}') and preceding-sibling::node()[1][name()='tex:spec' and @cat='bg'] and preceding-sibling::node()[2][.='href'] and preceding-sibling::node()[3][name()='tex:spec' and @cat='esc']]">
        <xsl:variable name="sBefore" select="substring-before(.,'\textasciitilde{}')"/>
        <xsl:variable name="sAfter" select="substring-after(.,'\textasciitilde{}')"/>
        <xsl:value-of select="$sBefore"/>
        <xsl:text>~</xsl:text>
        <xsl:value-of select="$sAfter"/>
    </xsl:template>
    <xsl:template name="NormalizeColumnFormatingCharacters">
        <!-- There are some characters that can occur in a XeLaTeXSpecial/@column-formatting attribute which will make TeX stop if used as they
            come out of the character conversion process.  So we need to change them back here to the plain
            character so XeLaTeX/XeTeX will work.
        -->
        <xsl:variable name="sLeftBraceChanged">
            <xsl:call-template name="FindAndReplace">
                <xsl:with-param name="sStringToMakeChangesIn" select="text()"/>
                <xsl:with-param name="sFind" select="'\{'"/>
                <xsl:with-param name="sReplace" select="'{'"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="sRightBraceChanged">
            <xsl:call-template name="FindAndReplace">
                <xsl:with-param name="sStringToMakeChangesIn" select="$sLeftBraceChanged"/>
                <xsl:with-param name="sFind" select="'\}'"/>
                <xsl:with-param name="sReplace" select="'}'"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="sVerticalBarChanged">
            <xsl:call-template name="FindAndReplace">
                <xsl:with-param name="sStringToMakeChangesIn" select="$sRightBraceChanged"/>
                <xsl:with-param name="sFind" select="'\textbar{}'"/>
                <xsl:with-param name="sReplace" select="'|'"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:value-of select="$sVerticalBarChanged"/>
    </xsl:template>
    <xsl:template name="NormalizeFileNameCharacters">
        <!-- There are some characters that can occur in file names which will make TeX stop if used as they
            come out of the character conversion process.  So we need to change them back here to the plain
            character so XeLaTeX/XeTeX will find the file.
        -->
        <xsl:variable name="sLeftBraceChanged">
            <xsl:call-template name="FindAndReplace">
                <xsl:with-param name="sStringToMakeChangesIn" select="text()"/>
                <xsl:with-param name="sFind" select="'\%7B'"/>
                <xsl:with-param name="sReplace" select="'{'"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="sRightBraceChanged">
            <xsl:call-template name="FindAndReplace">
                <xsl:with-param name="sStringToMakeChangesIn" select="$sLeftBraceChanged"/>
                <xsl:with-param name="sFind" select="'\%7D'"/>
                <xsl:with-param name="sReplace" select="'}'"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="sAmpersandChanged">
            <xsl:call-template name="FindAndReplace">
                <xsl:with-param name="sStringToMakeChangesIn" select="$sRightBraceChanged"/>
                <xsl:with-param name="sFind" select="'\&amp;'"/>
                <xsl:with-param name="sReplace" select="'&amp;'"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="sCrossHatchChanged">
            <xsl:call-template name="FindAndReplace">
                <xsl:with-param name="sStringToMakeChangesIn" select="$sAmpersandChanged"/>
                <xsl:with-param name="sFind" select="'\%23'"/>
                <xsl:with-param name="sReplace" select="'#'"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="sCaretChanged">
            <xsl:call-template name="FindAndReplace">
                <xsl:with-param name="sStringToMakeChangesIn" select="$sCrossHatchChanged"/>
                <xsl:with-param name="sFind" select="'\%5E'"/>
                <xsl:with-param name="sReplace" select="'^'"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="sUnderscoreChanged">
            <xsl:call-template name="FindAndReplace">
                <xsl:with-param name="sStringToMakeChangesIn" select="$sCaretChanged"/>
                <xsl:with-param name="sFind" select="'\_'"/>
                <xsl:with-param name="sReplace" select="'_'"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="sLeftSquareBracketChanged">
            <xsl:call-template name="FindAndReplace">
                <xsl:with-param name="sStringToMakeChangesIn" select="$sUnderscoreChanged"/>
                <xsl:with-param name="sFind" select="'\%5B'"/>
                <xsl:with-param name="sReplace" select="'['"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="sRightSquareBracketChanged">
            <xsl:call-template name="FindAndReplace">
                <xsl:with-param name="sStringToMakeChangesIn" select="$sLeftSquareBracketChanged"/>
                <xsl:with-param name="sFind" select="'\%5D'"/>
                <xsl:with-param name="sReplace" select="']'"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:value-of select="$sRightSquareBracketChanged"/>
    </xsl:template>
    <!-- 
        env
    -->
    <xsl:template match="tex:env">
        <xsl:choose>
            <xsl:when test="@nlb1='0'"/>
            <xsl:otherwise>
                <xsl:text>&#x0a;</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:text>\begin{</xsl:text>
        <xsl:value-of select="@name"/>
        <xsl:text>}</xsl:text>
        <xsl:choose>
            <xsl:when test="@nlb2='0'"/>
            <xsl:otherwise>
                <xsl:text>&#x0a;</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:apply-templates/>
        <xsl:choose>
            <xsl:when test="@nle1='1'">
                <xsl:text>&#x0a;</xsl:text>
            </xsl:when>
            <xsl:otherwise/>
        </xsl:choose>
        <xsl:text>\end{</xsl:text>
        <xsl:value-of select="@name"/>
        <xsl:text>}</xsl:text>
        <xsl:choose>
            <xsl:when test="@nle2='0'"/>
            <xsl:otherwise>
                <xsl:text>&#x0a;</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- 
        group
    -->
    <xsl:template match="tex:group">
        <xsl:text>{</xsl:text>
        <xsl:apply-templates/>
        <xsl:text>}</xsl:text>
    </xsl:template>
    <!-- 
        opt
    -->
    <xsl:template match="tex:opt">
        <xsl:text>[</xsl:text>
        <xsl:apply-templates/>
        <xsl:text>]</xsl:text>
    </xsl:template>
    <!-- 
        parm
    -->
    <xsl:template match="tex:parm">
        <xsl:text>{</xsl:text>
        <xsl:choose>
            <xsl:when test="parent::tex:env[@name='longtable' or @name='tabular'] and preceding-sibling::*[1][name()='tex:opt'] and count(preceding-sibling::*)=1">
                <xsl:choose>
                    <xsl:when test="contains(.,'\textbar{}') or contains(.,'\{') or contains(.,'\}')">
                        <xsl:call-template name="NormalizeColumnFormatingCharacters"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:apply-templates/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:text>}</xsl:text>
    </xsl:template>
    <!-- 
        spec
    -->
    <xsl:template match="tex:spec">
        <xsl:if test="@nl1='1'">
            <xsl:text>&#x0a;</xsl:text>
        </xsl:if>
        <xsl:choose>
            <xsl:when test="@cat='esc'">
                <xsl:text>\</xsl:text>
            </xsl:when>
            <xsl:when test="@cat='bg'">
                <xsl:text>{</xsl:text>
            </xsl:when>
            <xsl:when test="@cat='eg'">
                <xsl:text>}</xsl:text>
            </xsl:when>
            <xsl:when test="@cat='lsb'">
                <xsl:text>[</xsl:text>
            </xsl:when>
            <xsl:when test="@cat='rsb'">
                <xsl:text>]</xsl:text>
            </xsl:when>
            <xsl:when test="@cat='mshift'">
                <xsl:text>$</xsl:text>
            </xsl:when>
            <xsl:when test="@cat='align'">
                <xsl:text>&amp;</xsl:text>
            </xsl:when>
            <xsl:when test="@cat='parm'">
                <xsl:text>#</xsl:text>
            </xsl:when>
            <xsl:when test="@cat='sup'">
                <xsl:text>^</xsl:text>
            </xsl:when>
            <xsl:when test="@cat='sub'">
                <xsl:text>_</xsl:text>
            </xsl:when>
            <xsl:when test="@cat='tilde'">
                <xsl:text>~</xsl:text>
            </xsl:when>
            <xsl:when test="@cat='comment'">
                <xsl:text>%</xsl:text>
            </xsl:when>
            <xsl:when test="@cat='vert'">
                <xsl:text>|</xsl:text>
            </xsl:when>
            <xsl:when test="@cat='lt'">
                <xsl:text>&lt;</xsl:text>
            </xsl:when>
            <xsl:when test="@cat='gt'">
                <xsl:text>&gt;</xsl:text>
            </xsl:when>
            <xsl:when test="@cat='nl'">
                <xsl:text>&#x0a;</xsl:text>
            </xsl:when>
            <xsl:when test="@cat='space'">
                <xsl:text> </xsl:text>
            </xsl:when>
            <xsl:when test="@cat='nil'">
                <xsl:text/>
            </xsl:when>
        </xsl:choose>
        <xsl:if test="@nl2='1'">
            <xsl:text>&#x0a;</xsl:text>
        </xsl:if>
    </xsl:template>
    <!-- Following taken from http://www.xml.com/pub/a/2002/06/05/transforming.html on March 30, 2010 
           I changed the template and parameter names to ones more meaningful to me -->
    <xsl:template name="FindAndReplace">
        <xsl:param name="sStringToMakeChangesIn"/>
        <xsl:param name="sFind"/>
        <xsl:param name="sReplace"/>
        <xsl:choose>
            <xsl:when test="contains($sStringToMakeChangesIn,$sFind)">
                <xsl:value-of select="concat(substring-before($sStringToMakeChangesIn,$sFind),
                    $sReplace)"/>
                <xsl:call-template name="FindAndReplace">
                    <xsl:with-param name="sStringToMakeChangesIn" select="substring-after($sStringToMakeChangesIn,$sFind)"/>
                    <xsl:with-param name="sFind" select="$sFind"/>
                    <xsl:with-param name="sReplace" select="$sReplace"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sStringToMakeChangesIn"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>
