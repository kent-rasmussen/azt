<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:tex="http://getfo.sourceforge.net/texml/ns1" xmlns:saxon="http://icl.com/saxon" version="1.1"
xmlns:exsl="http://exslt.org/common">
    <!-- 
    XLingPapXeLaTeXCommon.xsl
    Contains called templates common to many of the XeLaTeX-oriented transforms.
    -->
    <!-- ===========================================================
        Variables
        =========================================================== -->
    <!-- following is here to get thesis submission style to get correct margins -->
    <xsl:variable name="publisherStyleSheet" select="//publisherStyleSheet[1]"/>
    <xsl:variable name="documentLayoutInfo" select="exsl:node-set($publisherStyleSheet)/contentLayout"/>
    <!--    <xsl:variable name="backMatterLayoutInfo" select="exsl:node-set($publisherStyleSheet)/backMatterLayout"/>-->
    <xsl:variable name="pageLayoutInfo" select="exsl:node-set($publisherStyleSheet)/pageLayout"/>
    <xsl:variable name="sDigits" select="'1234567890 _-'"/>
    <xsl:variable name="sLetters" select="'ABCDEFGHIJZYX'"/>
    <xsl:variable name="sIDcharsToMap" select="'_'"/>
    <xsl:variable name="sIDcharsMapped" select="';'"/>
    <xsl:variable name="sPercent20" select="'%20'"/>
    <xsl:variable name="sBulletPoint" select="'&#x2022;'"/>
    <xsl:variable name="sInterlinearMaxNumberOfColumns" select="'50'"/>
    <xsl:variable name="bHasChapter">
        <xsl:choose>
            <xsl:when test="$chapters">
                <xsl:text>Y</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>N</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="sBasicPointSize">
        <xsl:choose>
            <xsl:when test="string-length(exsl:node-set($pageLayoutInfo)/basicPointSize)&gt;0">
                <xsl:value-of select="string(exsl:node-set($pageLayoutInfo)/basicPointSize)"/>
            </xsl:when>
            <xsl:when test="$bHasChapter='Y'">
                <xsl:text>10</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>12</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="bHasContents">
        <xsl:choose>
            <xsl:when test="$contents">
                <xsl:text>Y</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>N</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="bHasIndex">
        <xsl:choose>
            <xsl:when test="//index">
                <xsl:text>Y</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>N</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="sLdquo">&#8220;</xsl:variable>
    <xsl:variable name="sRdquo">&#8221;</xsl:variable>
    <xsl:variable name="sSingleQuote">
        <xsl:text>'</xsl:text>
    </xsl:variable>
    <xsl:variable name="iExampleCount" select="count(//example)"/>
    <xsl:variable name="iNumberWidth">
        <xsl:choose>
            <xsl:when test="$sFOProcessor='TeX'">
                <!-- units are ems so the font and font size can be taken into account -->
                <xsl:choose>
                    <xsl:when test="string-length(exsl:node-set($documentLayoutInfo)/exampleLayout/@exampleNumberMaxWidthInEms) &gt; 0">
                        <xsl:value-of select="exsl:node-set($documentLayoutInfo)/exampleLayout/@exampleNumberMaxWidthInEms"/>
                    </xsl:when>
                    <xsl:when test="exsl:node-set($documentLayoutInfo)/exampleLayout/@allowNumberingOver999='yes'">
                        <xsl:text>3.0</xsl:text>
                    </xsl:when>
                    <xsl:when test="exsl:node-set($documentLayoutInfo)/exampleLayout/@showChapterNumberBeforeExampleNumber='yes' and exsl:node-set($documentLayoutInfo)/exampleLayout/@startNumberingOverAtEachChapter='yes'">
                        <xsl:text>3.1</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>2.75</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="$sFOProcessor='XEP'">
                <!-- units are ems so the font and font size can be taken into account -->
                <xsl:text>2.75</xsl:text>
            </xsl:when>
            <xsl:when test="$sFOProcessor='XFC'">
                <!--  units are inches because "XFC is not a renderer. It has a limited set of font metrics and therefore handles 'em' units in a very approximate way."
                    (email of August 10, 2007 from Jean-Yves Belmonte of XMLmind)-->
                <xsl:text>0.375</xsl:text>
            </xsl:when>
            <!--  if we can ever get FOP to do something reasonable for examples and interlinear, we'll add a 'when' clause here -->
        </xsl:choose>
        <!-- Originally thought we should vary the width depending on number of examples.  See below.  But that means
            as soon as one adds the 10th example or the 100th example, then all of a sudden the width available for the
            content of the example will change.  Just using a size for three digits. 
            <xsl:choose>
            <xsl:when test="$iExampleCount &lt; 10">1.5</xsl:when>
            <xsl:when test="$iExampleCount &lt; 100">2.25</xsl:when>
            <xsl:otherwise>3</xsl:otherwise>
            </xsl:choose>
        -->
    </xsl:variable>
    <!-- following used to calculate width of an example table.  NB: we assume all units will be the same -->
    <xsl:variable name="iIndent">
        <xsl:value-of select="number(substring($sBlockQuoteIndent,1,string-length($sBlockQuoteIndent) - 2))"/>
    </xsl:variable>
    <xsl:variable name="iExampleWidth">
        <!--        <xsl:value-of select="number($iPageWidth - 2 * $iIndent - $iPageOutsideMargin - $iPageInsideMargin)"/>-->
        <xsl:value-of select="number($iPageWidth - $iPageOutsideMargin - $iPageInsideMargin)"/>
    </xsl:variable>
    <xsl:variable name="sExampleWidth">
        <xsl:value-of select="$iExampleWidth"/>
        <xsl:text>pt</xsl:text>
        <!--        <xsl:value-of select="substring($sPageWidth,string-length($sPageWidth) - 1)"/>-->
    </xsl:variable>
    <xsl:variable name="iPageTopMargin">
        <xsl:call-template name="ConvertToPoints">
            <xsl:with-param name="sValue" select="$sPageTopMargin"/>
            <xsl:with-param name="iValue" select="number(substring($sPageTopMargin,1,string-length($sPageTopMargin) - 2))"/>
        </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="iPageBottomMargin">
        <xsl:call-template name="ConvertToPoints">
            <xsl:with-param name="sValue" select="$sPageBottomMargin"/>
            <xsl:with-param name="iValue" select="number(substring($sPageBottomMargin,1,string-length($sPageBottomMargin) - 2))"/>
        </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="iHeaderMargin">
        <xsl:call-template name="ConvertToPoints">
            <xsl:with-param name="sValue" select="$sHeaderMargin"/>
            <xsl:with-param name="iValue" select="number(substring($sHeaderMargin,1,string-length($sHeaderMargin) - 2))"/>
        </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="iFooterMargin">
        <xsl:call-template name="ConvertToPoints">
            <xsl:with-param name="sValue" select="$sFooterMargin"/>
            <xsl:with-param name="iValue" select="number(substring($sFooterMargin,1,string-length($sFooterMargin) - 2))"/>
        </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="sInterlinearInitialHorizontalOffset">-.5pt</xsl:variable>
    <xsl:variable name="sTeXInterlinearSourceWidth" select="'XLingPaperinterlinearsourcewidth'"/>
    <xsl:variable name="sTeXInterlinearSourceGapWidth" select="'XLingPaperinterlinearsourcegapwidth'"/>
    <xsl:variable name="sTeXAbbrBaselineskip" select="'XLingPaperabbrbaselineskip'"/>
    <xsl:variable name="sRendererIsGraphite" select="'Renderer=Graphite'"/>
    <xsl:variable name="sGraphite" select="'graphite'"/>
    <xsl:variable name="sFontFeature" select="'font-feature='"/>
    <xsl:variable name="sFontScript" select="'Script='"/>
    <xsl:variable name="sFontScriptLower" select="'script='"/>
    <xsl:variable name="sFontLanguage" select="'language='"/>
    <xsl:variable name="sUppercaseAtoZ" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'"/>
    <xsl:variable name="sLowercaseAtoZ" select="'abcdefghijklmnopqrstuvwxyz'"/>
    <xsl:variable name="bAutomaticallyWrapInterlinears" select="//lingPaper/@automaticallywrapinterlinears"/>
    <xsl:variable name="bEndnoteRefIsDirectLinkToEndnote" select="'N'"/>
    <xsl:variable name="sListLayoutSpaceBetween" select="normalize-space(exsl:node-set($contentLayoutInfo)/listLayout/@spacebetween)"/>
    <xsl:variable name="topLevelTables" select="//table[not(ancestor::table)]"/>
    <xsl:variable name="fTablesCanWrap">
        <xsl:for-each select="$topLevelTables">
            <xsl:if
                test="not(descendant::*[string-length(@width)&gt;0]) and not(descendant::table) and not(descendant::*[string-length(@colspan)&gt;0]) and not(descendant::*[string-length(@rowspan)&gt;0]) and not(count(tr[1]/td | tr[1]/th)&gt; 26)">
                <xsl:text>Y</xsl:text>
            </xsl:if>
        </xsl:for-each>
    </xsl:variable>
    <xsl:variable name="sHangingIndentInitialIndent" select="normalize-space(exsl:node-set($pageLayoutInfo)/hangingIndentInitialIndent)"/>
    <xsl:variable name="sHangingIndentNormalIndent" select="normalize-space(exsl:node-set($pageLayoutInfo)/hangingIndentNormalIndent)"/>
    <xsl:variable name="sSingleSpacingCommand">
        <xsl:choose>
            <xsl:when test="$sBasicPointSize!=$sLaTeXBasicPointSize and $sLineSpacing and $sLineSpacing!='single'">
                <xsl:text>XLingPapersinglespacing</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>singlespacing</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="sInitialGroupIndent" select="exsl:node-set($contentLayoutInfo)/interlinearTextLayout/@indentOfInitialGroup"/>
    <xsl:variable name="sAdjustIndentOfNonInitialFreeLineBy" select="normalize-space(exsl:node-set($contentLayoutInfo)/freeLayout/@adjustIndentOfNonInitialLineBy)"/>
    <xsl:variable name="fFooterUsesDots" select="//headerFooterPageStyles[descendant::footer/@ruleabovepattern='dots']"/>
    <xsl:variable name="fHeaderUsesDots" select="//headerFooterPageStyles[descendant::header/@rulebelowpattern='dots']"/>
    <!-- not sure why we need to adjust the values with the arbitrary 50, but it does seem to work -->
    <xsl:variable name="iTableInLandscapeWidth" select="number($iPageHeight - $iPageBottomMargin - $iPageTopMargin - $iHeaderMargin - $iFooterMargin - 50)"/>
    <xsl:variable name="iTableInPortraitWidth" select="number($iPageWidth - $iPageOutsideMargin - $iPageInsideMargin)"/>
    <!--
        citation (bookmarks)
    -->
    <xsl:template match="citation" mode="bookmarks">
        <xsl:call-template name="OutputCitationContents">
            <xsl:with-param name="refer" select="id(@ref)"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        citation (contents)
    -->
    <xsl:template match="citation" mode="contents">
        <xsl:call-template name="OutputCitationContents">
            <xsl:with-param name="refer" select="id(@ref)"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        citation (InMarker)
    -->
    <xsl:template match="citation" mode="InMarker">
        <xsl:call-template name="OutputCitationContents">
            <xsl:with-param name="refer" select="id(@ref)"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        genericRef (InMarker)
    -->
    <xsl:template match="genericRef" mode="InMarker">
        <xsl:call-template name="OutputGenericRef"/>
    </xsl:template>
    <xsl:template match="genericRef" mode="contents" priority="100">
        <xsl:call-template name="OutputGenericRef"/>
    </xsl:template>
    <!--
        genericTarget
    -->
    <xsl:template match="genericTarget">
        <!--        <tex:spec cat="esc"/>
        <xsl:text>raisebox</xsl:text>
        <tex:spec cat="bg"/>
        <tex:spec cat="esc"/>
        <xsl:text>baselineskip</xsl:text>
        <tex:spec cat="eg"/>
        <tex:spec cat="lsb"/>
        <xsl:text>0pt</xsl:text>
        <tex:spec cat="rsb"/>
        <tex:spec cat="bg"/>
        -->
        <xsl:choose>
            <xsl:when test="ancestor::dt">
                <xsl:call-template name="DoInternalTargetBegin">
                    <xsl:with-param name="sName" select="@id"/>
                    <xsl:with-param name="fDoRaisebox" select="'N'"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="DoInternalTargetBegin">
                    <xsl:with-param name="sName" select="@id"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="DoInternalTargetEnd"/>
        <!--        <tex:spec cat="eg"/>-->
    </xsl:template>
    <!-- ===========================================================
        Hanging indent paragraph
        =========================================================== -->
    <xsl:template match="hangingIndent">
        <xsl:variable name="sThisInitialIndent" select="normalize-space(@initialIndent)"/>
        <xsl:variable name="sThisHangingIndent" select="normalize-space(@hangingIndent)"/>
        <xsl:if test="contains(@XeLaTeXSpecial,'clearpage')">
            <tex:cmd name="clearpage" gr="0" nl2="0"/>
        </xsl:if>
        <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak')">
            <tex:cmd name="pagebreak" gr="0" nl2="0"/>
        </xsl:if>
        <xsl:if test="parent::chart and ancestor::example">
            <!-- Override the example macro's interline penalty; if we do not
                 then sequences of example/chart/hangingIndent do not break at
                 page boundaries.
            -->
            <tex:spec cat="esc"/>
            <xsl:text>interlinepenalty0</xsl:text>
        </xsl:if>
        <tex:spec cat="bg"/>
        <tex:cmd name="hangafter" gr="0"/>
        <xsl:text>1</xsl:text>
        <tex:cmd name="relax" gr="0" nl2="1"/>
        <tex:cmd name="hangindent" gr="0"/>
        <xsl:choose>
            <xsl:when test="string-length($sThisHangingIndent) &gt; 0">
                <xsl:value-of select="$sThisHangingIndent"/>
            </xsl:when>
            <xsl:when test="string-length($sHangingIndentNormalIndent) &gt; 0">
                <xsl:value-of select="$sHangingIndentNormalIndent"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>1em</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <tex:cmd name="relax" gr="0" nl2="1"/>
        <xsl:choose>
            <xsl:when test="string-length($sThisInitialIndent) &gt; 0">
                <tex:cmd name="parindent" gr="0"/>
                <xsl:value-of select="$sThisInitialIndent"/>
                <tex:cmd name="indent"/>
            </xsl:when>
            <xsl:when test="string-length($sHangingIndentInitialIndent) &gt; 0">
                <tex:cmd name="parindent" gr="0"/>
                <xsl:value-of select="$sHangingIndentInitialIndent"/>
                <tex:cmd name="indent"/>
            </xsl:when>
            <xsl:otherwise>
                <tex:cmd name="noindent"/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:apply-templates/>
        <tex:cmd name="par" nl2="1"/>
        <tex:spec cat="eg"/>
    </xsl:template>
    <!-- ===========================================================
        Block hyphenation in langData in p, pc, and hanging indent paragraphs
        =========================================================== -->
    <xsl:template match="text()[parent::langData and string-length(normalize-space(//lingPaper/@xml:lang))&gt;0]">
        <xsl:choose>
            <xsl:when test="ancestor::p or ancestor::pc or ancestor::hangingIndent">
                <xsl:call-template name="BlockAnyHyphenationOfText">
                    <xsl:with-param name="sList" select="."/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="."/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <xsl:template name="BlockAnyHyphenationOfText">
        <xsl:param name="sList"/>
        <xsl:variable name="sNewList" select="concat(normalize-space($sList),' ')"/>
        <xsl:variable name="sFirst" select="substring-before($sNewList,' ')"/>
        <xsl:variable name="sRest" select="substring-after($sNewList,' ')"/>
        <xsl:if test="string-length($sFirst)&gt;0">
            <tex:cmd name="mbox">
                <tex:parm>
                    <xsl:value-of select="$sFirst"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:if test="$sRest">
            <xsl:text> </xsl:text>
            <xsl:call-template name="BlockAnyHyphenationOfText">
                <xsl:with-param name="sList" select="$sRest"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!-- ===========================================================
        QUOTES
        =========================================================== -->
    <xsl:template match="q">
        <xsl:call-template name="DoQuoteTextBefore"/>
        <xsl:call-template name="DoType"/>
        <xsl:apply-templates/>
        <xsl:call-template name="DoTypeEnd"/>
        <xsl:call-template name="DoQuoteTextAfter"/>
    </xsl:template>
    <xsl:template match="blockquote">
        <!--  following did not work      <tex:group>
            <tex:cmd name="leftskip" gr="0" nl1="1"/>
            <xsl:value-of select="normalize-space($sBlockQuoteIndent)"/>
            <tex:cmd name="relax" gr="0" nl2="1"/>
            <tex:cmd name="rightskip" gr="0"/>
            <xsl:value-of select="normalize-space($sBlockQuoteIndent)"/>
            <tex:cmd name="relax" gr="0" nl2="1"/>
            <tex:cmd name="vspace" nl2="1">
                <tex:parm>
                    <xsl:value-of select="$sBasicPointSize"/>
                    <xsl:text>pt</xsl:text>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="small">
                <tex:parm>
-->
        <xsl:if test="contains(@XeLaTeXSpecial,'clearpage')">
            <tex:cmd name="clearpage" gr="0" nl2="0"/>
        </xsl:if>
        <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak')">
            <tex:cmd name="pagebreak" gr="0" nl2="0"/>
        </xsl:if>
        <!--        <tex:env name="quotation">-->
        <xsl:if test="parent::li">
            <tex:cmd name="setlength">
                <tex:parm>
                    <tex:cmd name="XLingPaperbqtemp" gr="0" nl2="0"/>
                </tex:parm>
                <tex:parm>
                    <tex:cmd name="XLingPapertempdim" gr="0" nl2="0"/>
                    <xsl:text>+</xsl:text>
                    <tex:cmd name="XLingPaperlistitemindent" gr="0" nl2="0"/>
                    <xsl:text>+</xsl:text>
                    <xsl:value-of select="$sBlockQuoteIndent"/>
                    <xsl:if test="count(ancestor::*[name()='ol' or name()='ul'])=1">
                        <xsl:text>+</xsl:text>
                        <tex:cmd name="parindent" gr="0" nl2="0"/>
                    </xsl:if>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <tex:cmd name="XLingPaperblockquote">
            <tex:parm>
                <xsl:choose>
                    <xsl:when test="parent::li">
                        <tex:cmd name="XLingPaperbqtemp" gr="0" nl2="0"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$sBlockQuoteIndent"/>
                    </xsl:otherwise>
                </xsl:choose>
            </tex:parm>
            <tex:parm>
                <xsl:value-of select="$sBlockQuoteIndent"/>
            </tex:parm>
            <tex:parm>
                <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespaceblockquotes='yes'">
                    <tex:spec cat="bg"/>
                    <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
                    <tex:cmd name="vspace">
                        <tex:parm>
                            <!-- I do not know why these values are needed, but they are... -->
                            <xsl:choose>
                                <xsl:when test="$sLineSpacing='double'">
                                    <xsl:text>-1.3</xsl:text>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>-1.75</xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                            <tex:spec cat="esc"/>
                            <xsl:text>baselineskip</xsl:text>
                        </tex:parm>
                    </tex:cmd>
                </xsl:if>
                <!--                    <xsl:call-template name="DoType"/>  this kind cannot cross paragraph boundaries, so have to do it in p-->
                <xsl:call-template name="OutputTypeAttributes">
                    <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
                </xsl:call-template>
                <xsl:apply-templates/>
                <xsl:call-template name="OutputTypeAttributesEnd">
                    <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
                </xsl:call-template>
                <xsl:if test="count(child::*)=1 and child::*[1][name()='langData' or name()='gloss' or name()='object']">
                    <tex:cmd name="par"/>
                </xsl:if>
                <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespaceblockquotes='yes'">
                    <tex:spec cat="eg"/>
                </xsl:if>
            </tex:parm>
            <tex:parm>
                <xsl:variable name="sSpaceBefore" select="normalize-space(exsl:node-set($documentLayoutInfo)/blockQuoteLayout/@spacebefore)"/>
                <xsl:choose>
                    <xsl:when test="string-length($sSpaceBefore)&gt;0">
                        <xsl:value-of select="$sSpaceBefore"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <tex:cmd name="baselineskip" gr="0"/>
                    </xsl:otherwise>
                </xsl:choose>
            </tex:parm>
            <tex:parm>
                <xsl:variable name="sSpaceAfter" select="normalize-space(exsl:node-set($documentLayoutInfo)/blockQuoteLayout/@spaceafter)"/>
                <xsl:choose>
                    <xsl:when test="string-length($sSpaceAfter)&gt;0">
                        <xsl:value-of select="$sSpaceAfter"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <tex:cmd name="baselineskip" gr="0"/>
                    </xsl:otherwise>
                </xsl:choose>
            </tex:parm>
        </tex:cmd>
        <!--                    <xsl:call-template name="DoTypeEnd"/>-->
        <!--        </tex:env>-->
        <!--</tex:parm>
            </tex:cmd>
            <tex:cmd name="vspace" nl2="1">
                <tex:parm>
                    <xsl:value-of select="$sBasicPointSize"/>
                    <xsl:text>pt</xsl:text>
                </tex:parm>
            </tex:cmd>
        </tex:group>-->
    </xsl:template>
    <!-- 
       initial text in a block quote
-->
    <xsl:template match="text()[parent::blockquote][string-length(normalize-space(.))&gt;0]">
        <xsl:value-of select="."/>
        <xsl:if
            test="following-sibling::*[1][name()='p'or name()='pc' or name()='example' or name()='table' or name()='tablenumbered' or name()='chart' or name()='figure' or name()='tree' or name()='ol' or name()='ul' or name()='dl']">
            <!-- any chunk item following requires a \par here -->
            <xsl:choose>
                <xsl:when test="ancestor::td">
                    <tex:cmd name="vskip" gr="0"/>
                    <xsl:text>0pt</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <tex:cmd name="par"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:if test="count(following-sibling::*)=0">
            <!-- if all there is is text, still need a \par -->
            <xsl:choose>
                <xsl:when test="ancestor::td">
                    <tex:cmd name="vskip" gr="0"/>
                    <xsl:text>0pt</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <tex:cmd name="par"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!-- ===========================================================
        PROSE TEXT
        =========================================================== -->
    <xsl:template match="prose-text">
        <xsl:choose>
            <xsl:when test="exsl:node-set($documentLayoutInfo)/prose-textTextLayout">
                <xsl:variable name="sSpaceBefore" select="normalize-space(exsl:node-set($documentLayoutInfo)/prose-textTextLayout/@spacebefore)"/>
                <xsl:if test="string-length($sSpaceBefore)&gt;0">
                    <tex:cmd name="vspace">
                        <tex:parm>
                            <xsl:value-of select="$sSpaceBefore"/>
                        </tex:parm>
                    </tex:cmd>
                </xsl:if>
                <xsl:variable name="sSpaceAfter" select="normalize-space(exsl:node-set($documentLayoutInfo)/prose-textTextLayout/@spaceafter)"/>
                <tex:group>
                    <xsl:call-template name="OutputTypeAttributes">
                        <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
                    </xsl:call-template>
                    <xsl:variable name="sStartIndent" select="normalize-space(exsl:node-set($documentLayoutInfo)/prose-textTextLayout/@start-indent)"/>
                    <xsl:if test="string-length($sStartIndent)&gt;0">
                        <tex:cmd name="leftskip" gr="0" nl1="1" nl2="0"/>
                        <xsl:value-of select="$sStartIndent"/>
                        <tex:cmd name="relax" gr="0" nl2="0"/>
                        <tex:spec cat="comment"/>
                        <xsl:text> left glue for indent</xsl:text>
                    </xsl:if>
                    <xsl:variable name="sEndIndent" select="normalize-space(exsl:node-set($documentLayoutInfo)/prose-textTextLayout/@end-indent)"/>
                    <xsl:if test="string-length($sEndIndent)&gt;0">
                        <tex:cmd name="rightskip" gr="0" nl1="1" nl2="0"/>
                        <xsl:value-of select="$sEndIndent"/>
                        <tex:cmd name="relax" gr="0" nl2="0"/>
                        <tex:spec cat="comment"/>
                    </xsl:if>
                    <tex:cmd name="interlinepenalty10000" gr="0" nl1="1" nl2="0"/>
                    <tex:spec cat="comment"/>
                    <tex:cmd name="leavevmode" gr="0" nl1="1" nl2="0"/>
                    <tex:cmd name="hskip" gr="0" nl2="0"/>
                    <xsl:text>-</xsl:text>
                    <tex:cmd name="parindent" gr="0" nl2="0"/>
                    <tex:spec cat="bg"/>
                    <xsl:apply-templates/>
                    <tex:spec cat="eg"/>
                    <tex:cmd name="nobreak" gr="0" nl2="1"/>
                    <xsl:call-template name="OutputTypeAttributesEnd">
                        <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
                    </xsl:call-template>
                </tex:group>
                <xsl:if test="string-length($sSpaceAfter)&gt;0">
                    <tex:cmd name="vspace">
                        <tex:parm>
                            <xsl:value-of select="$sSpaceAfter"/>
                        </tex:parm>
                    </tex:cmd>
                </xsl:if>
            </xsl:when>
            <xsl:otherwise>
                <tex:env name="quotation">
                    <!--                    <xsl:call-template name="DoType"/>  this kind cannot cross paragraph boundaries, so have to do it in p-->
                    <xsl:call-template name="OutputTypeAttributes">
                        <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
                    </xsl:call-template>
                    <xsl:apply-templates/>
                    <xsl:call-template name="OutputTypeAttributesEnd">
                        <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
                    </xsl:call-template>
                    <!--                    <xsl:call-template name="DoTypeEnd"/>-->
                </tex:env>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- ===========================================================
      LISTS
      =========================================================== -->
    <xsl:template match="ol">
        <xsl:choose>
            <xsl:when test="count(li) &gt; 0">
                <xsl:variable name="sThisItemWidth">
                    <xsl:call-template name="GetItemWidth"/>
                </xsl:variable>
                <xsl:choose>
                    <xsl:when test="count(ancestor::ul | ancestor::ol) = 0 or parent::endnote">
                        <xsl:if test="parent::definition">
                            <xsl:call-template name="DoTypeEnd">
                                <xsl:with-param name="type" select="../@type"/>
                            </xsl:call-template>
                        </xsl:if>
                        <tex:group>
                            <tex:spec cat="esc"/>
                            <xsl:text>parskip .5pt plus 1pt minus 1pt
                    </xsl:text>
                            <xsl:choose>
                                <xsl:when test="parent::definition and ancestor::p">
                                    <xsl:text>&#x0a;</xsl:text>
                                </xsl:when>
                                <xsl:when test="parent::chart/preceding-sibling::*[1][name()='exampleHeading']">
                                    <!-- do nothing -->
                                </xsl:when>
                                <xsl:when test="name(preceding-sibling::*[1])='secTitle'">
                                    <!-- Do nothing so there is not extra preceding space if list is first element in section/chapter/part (after secTitle) -->
                                </xsl:when>
                                <xsl:when test="name(preceding-sibling::*[1])='blockquote'">
                                    <!-- Do nothing so there is not extra preceding space if list is first element after a blockquot -->
                                </xsl:when>
                                <xsl:otherwise>
                                    <tex:cmd name="vspace" nl1="1" nl2="1">
                                        <tex:parm>
                                            <xsl:call-template name="VerticalSkipAroundList"/>
                                        </tex:parm>
                                    </tex:cmd>
                                </xsl:otherwise>
                            </xsl:choose>
                            <xsl:if test="parent::definition">
                                <xsl:call-template name="DoType">
                                    <xsl:with-param name="type" select="../@type"/>
                                </xsl:call-template>
                            </xsl:if>
                            <xsl:if test="string-length(@numberFormat) &gt; 0">
                                <xsl:call-template name="SetTeXCommand">
                                    <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
                                    <xsl:with-param name="sCommandToSet">
                                        <xsl:call-template name="GetDynamicListItemName"/>
                                    </xsl:with-param>
                                    <xsl:with-param name="sValue">
                                        <xsl:call-template name="GetListItemWidthPattern">
                                            <xsl:with-param name="sNumberFormat" select="@numberFormat"/>
                                        </xsl:call-template>
                                        <xsl:text>.</xsl:text>
                                        <tex:spec cat="esc"/>
                                        <xsl:text>&#x20;</xsl:text>
                                    </xsl:with-param>
                                </xsl:call-template>
                            </xsl:if>
                            <xsl:apply-templates>
                                <xsl:with-param name="sListItemWidth">
                                    <tex:spec cat="esc"/>
                                    <xsl:value-of select="$sThisItemWidth"/>
                                </xsl:with-param>
                                <xsl:with-param name="sListItemIndent">
                                    <xsl:choose>
                                        <xsl:when test="ancestor::example">
                                            <tex:spec cat="esc"/>
                                            <xsl:text>XLingPaperlistinexampleindent</xsl:text>
                                        </xsl:when>
                                        <xsl:when test="$sListInitialHorizontalOffset!='0pt'">
                                            <xsl:value-of select="$sListInitialHorizontalOffset"/>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <!--<tex:spec cat="esc"/>
                                    <xsl:value-of select="$sThisItemWidth"/> default should be paragraph indent -->
                                            <tex:cmd name="parindent"/>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </xsl:with-param>
                            </xsl:apply-templates>
                            <xsl:if test="parent::definition">
                                <xsl:call-template name="DoTypeEnd">
                                    <xsl:with-param name="type" select="../@type"/>
                                </xsl:call-template>
                            </xsl:if>
                            <tex:cmd name="vspace" nl1="1" nl2="1">
                                <tex:parm>
                                    <xsl:call-template name="VerticalSkipAroundList"/>
                                </tex:parm>
                            </tex:cmd>
                        </tex:group>
                        <xsl:if test="parent::definition">
                            <xsl:call-template name="DoType">
                                <xsl:with-param name="type" select="../@type"/>
                            </xsl:call-template>
                        </xsl:if>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="HandleEmbeddedListItem">
                            <xsl:with-param name="sThisItemWidth" select="$sThisItemWidth"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <!-- do nothing -->
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        HandleAbbreviationsInTableColumnSpecColumns
    -->
    <xsl:template name="HandleAbbreviationsInTableColumnSpecColumns">
        <xsl:call-template name="HandleColumnWidth">
            <xsl:with-param name="sWidth" select="normalize-space(@abbrWidth)"/>
            <xsl:with-param name="sDefaultSpec" select="'l'"/>
        </xsl:call-template>
        <xsl:if test="not(exsl:node-set($contentLayoutInfo)/abbreviationsInTableLayout/@useEqualSignsColumn) or exsl:node-set($contentLayoutInfo)/abbreviationsInTableLayout/@useEqualSignsColumn!='no'">
            <xsl:call-template name="HandleColumnWidth">
                <xsl:with-param name="sWidth" select="normalize-space(@equalsWidth)"/>
                <xsl:with-param name="sDefaultSpec" select="'c'"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="HandleColumnWidth">
            <xsl:with-param name="sWidth" select="normalize-space(@definitionWidth)"/>
            <xsl:with-param name="sDefaultSpec" select="'l'"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        HandleAnyExampleHeadingAdjustWithISOCode
    -->
    <xsl:template name="HandleAnyExampleHeadingAdjustWithISOCode">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:if
            test="exsl:node-set($lingPaper)/@showiso639-3codeininterlinear='yes' and not(contains($bListsShareSameCode,'N')) or ancestor-or-self::example/@showiso639-3codes='yes' and not(contains($bListsShareSameCode,'N'))">
            <xsl:choose>
                <xsl:when test="exampleHeading[following-sibling::listInterlinear or following-sibling::interlinear]">
                    <xsl:call-template name="CalculateExampleAndExampleHeadingHeights">
                        <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:when test="child::*[1][name()='interlinear' and child::*[1][name()='exampleHeading']]">
                    <xsl:call-template name="CalculateExampleAndExampleHeadingHeights">
                        <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <!-- do nothing -->
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleAnyInterlinearAlignedWordSkipOverride
    -->
    <xsl:template name="HandleAnyInterlinearAlignedWordSkipOverride">
        <xsl:if test="exsl:node-set($lingPaper)/@automaticallywrapinterlinears='yes'">
            <xsl:if test="contains(@XeLaTeXSpecial,'interlinear-aligned-word-skip')">
                <xsl:variable name="sValue">
                    <xsl:call-template name="GetXeLaTeXSpecialCommand">
                        <xsl:with-param name="sAttr" select="'interlinear-aligned-word-skip='"/>
                        <xsl:with-param name="sDefaultValue" select="''"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:if test="string-length($sValue) &gt; 0">
                    <tex:cmd name="XLingPaperinterwordskip" gr="0"/>
                    <xsl:text>=</xsl:text>
                    <xsl:copy-of select="$sValue"/>
                </xsl:if>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleAnyInterlinearAlignedWordSkipOverrideEnd
    -->
    <xsl:template name="HandleAnyInterlinearAlignedWordSkipOverrideEnd">
        <xsl:if test="exsl:node-set($lingPaper)/@automaticallywrapinterlinears='yes'">
            <xsl:if test="contains(@XeLaTeXSpecial,'interlinear-aligned-word-skip')">
                <xsl:variable name="sValue">
                    <xsl:call-template name="GetXeLaTeXSpecialCommand">
                        <xsl:with-param name="sAttr" select="'interlinear-aligned-word-skip='"/>
                        <xsl:with-param name="sDefaultValue" select="''"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:if test="string-length($sValue) &gt; 0">
                    <xsl:call-template name="SetDefaultXLingPaperInterWordSkip"/>
                </xsl:if>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleColumnWidth
    -->
    <xsl:template name="HandleColumnWidth">
        <xsl:param name="sWidth"/>
        <xsl:param name="sDefaultSpec"/>
        <xsl:choose>
            <xsl:when test="string-length($sWidth) &gt; 0">
                <xsl:text>p</xsl:text>
                <tex:spec cat="bg"/>
                <xsl:choose>
                    <xsl:when test="contains($sWidth,'%')">
                        <xsl:call-template name="GetColumnWidthBasedOnPercentage">
                            <xsl:with-param name="iPercentage" select="substring-before(normalize-space($sWidth),'%')"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$sWidth"/>
                    </xsl:otherwise>
                </xsl:choose>
                <tex:spec cat="eg"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sDefaultSpec"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        HandleEmbeddedListItem
    -->
    <xsl:template name="HandleEmbeddedListItem">
        <xsl:param name="sThisItemWidth"/>
        <xsl:variable name="myEndnote" select="ancestor::endnote"/>
        <xsl:variable name="myAncestorLists" select="ancestor::ol | ancestor::ul"/>
        <xsl:call-template name="DoTypeForLI">
            <xsl:with-param name="myAncestorLists" select="$myAncestorLists"/>
            <xsl:with-param name="myEndnote" select="$myEndnote"/>
            <xsl:with-param name="bIsEnd" select="'Y'"/>
        </xsl:call-template>
        <xsl:if test="not(parent::blockquote)">
            <!-- if parent is blockquote, we do not want to close off the content of the blockquote -->
            <tex:spec cat="eg"/>
        </xsl:if>
        <!--        <tex:cmd name="par" nl2="1"/>-->
        <tex:spec cat="bg"/>
        <xsl:call-template name="DoTypeForLI">
            <xsl:with-param name="myAncestorLists" select="$myAncestorLists"/>
            <xsl:with-param name="myEndnote" select="$myEndnote"/>
            <xsl:with-param name="bBracketsOnly" select="'Y'"/>
        </xsl:call-template>
        <xsl:if test="string-length(@numberFormat) &gt; 0">
            <xsl:call-template name="SetTeXCommand">
                <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
                <xsl:with-param name="sCommandToSet">
                    <xsl:call-template name="GetDynamicListItemName"/>
                </xsl:with-param>
                <xsl:with-param name="sValue">
                    <xsl:call-template name="GetListItemWidthPattern">
                        <xsl:with-param name="sNumberFormat" select="@numberFormat"/>
                    </xsl:call-template>
                    <xsl:text>.</xsl:text>
                    <tex:spec cat="esc"/>
                    <xsl:text>&#x20;</xsl:text>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'setlength'"/>
            <xsl:with-param name="sCommandToSet" select="'XLingPaperlistitemindent'"/>
            <xsl:with-param name="sValue">
                <xsl:for-each select="ancestor::ol | ancestor::ul">
                    <xsl:sort select="position()" order="descending"/>
                    <tex:spec cat="esc" gr="0" nl2="0"/>
                    <xsl:call-template name="GetItemWidth"/>
                    <xsl:text> + </xsl:text>
                    <xsl:if test="position() = last()">
                        <xsl:choose>
                            <xsl:when test="ancestor::example">
                                <tex:spec cat="esc" gr="0" nl2="0"/>
                                <xsl:text>XLingPaperlistinexampleindent</xsl:text>
                            </xsl:when>
                            <xsl:when test="$sListInitialHorizontalOffset!='0pt'">
                                <xsl:value-of select="$sListInitialHorizontalOffset"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <!--<tex:spec cat="esc"/>
                                    <xsl:value-of select="$sThisItemWidth"/> default should be paragraph indent -->
                                <tex:cmd name="parindent"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:if>
                </xsl:for-each>
            </xsl:with-param>
        </xsl:call-template>
        <xsl:apply-templates>
            <xsl:with-param name="sListItemWidth">
                <tex:spec cat="esc"/>
                <xsl:value-of select="$sThisItemWidth"/>
            </xsl:with-param>
            <xsl:with-param name="sListItemIndent">
                <tex:spec cat="esc"/>
                <xsl:text>XLingPaperlistitemindent</xsl:text>
            </xsl:with-param>
        </xsl:apply-templates>
        <xsl:if test="parent::blockquote">
            <!-- if parent is blockquote, we now want to close off the content of the blockquote -->
            <tex:spec cat="eg"/>
        </xsl:if>
    </xsl:template>
    <xsl:template name="DoTypeForLI">
        <xsl:param name="myAncestorLists"/>
        <xsl:param name="myEndnote"/>
        <xsl:param name="bIsEnd" select="'N'"/>
        <xsl:param name="bBracketsOnly" select="'N'"/>
        <xsl:for-each select="$myAncestorLists">
            <xsl:sort order="descending"/>
            <xsl:choose>
                <xsl:when test="$myEndnote">
                    <xsl:variable name="current" select="."/>
                    <xsl:if test="exsl:node-set($myEndnote)/descendant::* = $current">
                        <xsl:call-template name="DoTypeForLiGivenList">
                            <xsl:with-param name="bIsEnd" select="$bIsEnd"/>
                            <xsl:with-param name="bBracketsOnly" select="$bBracketsOnly"/>
                        </xsl:call-template>
                    </xsl:if>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="DoTypeForLiGivenList">
                        <xsl:with-param name="bIsEnd" select="$bIsEnd"/>
                        <xsl:with-param name="bBracketsOnly" select="$bBracketsOnly"/>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>
    <xsl:template name="DoTypeForLiGivenList">
        <xsl:param name="bIsEnd"/>
        <xsl:param name="bBracketsOnly" select="'N'"/>
        <xsl:choose>
            <xsl:when test="$bIsEnd='Y'">
                <xsl:call-template name="DoTypeEnd">
                    <xsl:with-param name="type" select="@type"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$bBracketsOnly='Y'">
                <xsl:call-template name="DoTypeBracketsOnly">
                    <xsl:with-param name="type" select="@type"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="DoType">
                    <xsl:with-param name="type" select="@type"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <xsl:template match="ul">
        <xsl:choose>
            <xsl:when test="count(li) &gt; 0">
                <xsl:choose>
                    <xsl:when test="count(ancestor::ul | ancestor::ol) = 0 or parent::endnote">
                        <xsl:if test="parent::definition">
                            <xsl:call-template name="DoTypeEnd">
                                <xsl:with-param name="type" select="../@type"/>
                            </xsl:call-template>
                        </xsl:if>
                        <tex:group>
                            <tex:spec cat="esc"/>
                            <xsl:text>parskip .5pt plus 1pt minus 1pt
</xsl:text>
                            <xsl:choose>
                                <xsl:when test="parent::definition and ancestor::p">
                                    <xsl:text>&#x0a;</xsl:text>
                                </xsl:when>
                                <xsl:when test="parent::chart/preceding-sibling::*[1][name()='exampleHeading']">
                                    <!-- do nothing -->
                                </xsl:when>
                                <xsl:when test="name(preceding-sibling::*[1])='secTitle'">
                                    <!-- Do nothing so there is not extra preceding space if list is first element in section/chapter/part (after secTitle) -->
                                </xsl:when>
                                <xsl:when test="name(preceding-sibling::*[1])='blockquote'">
                                    <!-- Do nothing so there is not extra preceding space if list is first element after a blockquot -->
                                </xsl:when>
                                <xsl:otherwise>
                                    <tex:cmd name="vspace" nl1="1" nl2="1">
                                        <tex:parm>
                                            <xsl:call-template name="VerticalSkipAroundList"/>
                                        </tex:parm>
                                    </tex:cmd>
                                </xsl:otherwise>
                            </xsl:choose>
                            <xsl:if test="parent::definition">
                                <xsl:call-template name="DoType">
                                    <xsl:with-param name="type" select="../@type"/>
                                </xsl:call-template>
                            </xsl:if>
                            <xsl:apply-templates>
                                <xsl:with-param name="sListItemIndent">
                                    <xsl:choose>
                                        <xsl:when test="ancestor::example">
                                            <tex:spec cat="esc"/>
                                            <xsl:text>XLingPaperlistinexampleindent</xsl:text>
                                        </xsl:when>
                                        <xsl:when test="$sListInitialHorizontalOffset!='0pt'">
                                            <xsl:value-of select="$sListInitialHorizontalOffset"/>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <!--<tex:spec cat="esc"/>
                                        <xsl:text>XLingPaperbulletlistitemwidth</xsl:text> default should be paragraph indent -->
                                            <tex:cmd name="parindent"/>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </xsl:with-param>
                            </xsl:apply-templates>
                            <xsl:if test="parent::definition">
                                <xsl:call-template name="DoTypeEnd">
                                    <xsl:with-param name="type" select="../@type"/>
                                </xsl:call-template>
                            </xsl:if>
                            <tex:cmd name="vspace" nl1="1" nl2="1">
                                <tex:parm>
                                    <xsl:call-template name="VerticalSkipAroundList"/>
                                </tex:parm>
                            </tex:cmd>
                            <xsl:if test="parent::definition">
                                <xsl:call-template name="DoType">
                                    <xsl:with-param name="type" select="../@type"/>
                                </xsl:call-template>
                            </xsl:if>
                        </tex:group>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="HandleEmbeddedListItem">
                            <xsl:with-param name="sThisItemWidth" select="'XLingPaperbulletlistitemwidth'"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <!-- do nothing -->
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <xsl:template name="VerticalSkipAroundList">
        <xsl:variable name="nearestRelevantElement" select="ancestor::*[name()='endnote' or name()='example'][1]"/>
        <xsl:if test="name($nearestRelevantElement)='example'">
            <xsl:text>-</xsl:text>
        </xsl:if>
        <tex:cmd name="baselineskip" gr="0" nl2="0"/>
    </xsl:template>
    <xsl:template match="li">
        <xsl:param name="sListItemWidth">
            <tex:spec cat="esc"/>
            <xsl:text>XLingPaperbulletlistitemwidth</xsl:text>
        </xsl:param>
        <xsl:param name="sListItemIndent" select="'1em'"/>
        <!--<tex:spec cat="bg"/>
        <!-\- use hanging indent so all material within the li starts out indented (e.g. p elements and text) -\->
        <tex:spec cat="esc"/>
        <xsl:text>hangindent</xsl:text>
        <tex:spec cat="esc"/>
        <xsl:value-of select="$sListItemIndent"/>
        <tex:cmd name="relax" gr="0" nl2="1"/>
        <tex:spec cat="esc"/>
        <xsl:text>hangafter0</xsl:text>
        <tex:cmd name="relax" gr="0" nl2="1"/>-->
        <tex:spec cat="bg" nl1="1"/>
        <!--        <tex:spec cat="esc"/>
        <xsl:text>newdimen</xsl:text>
        <tex:spec cat="esc"/>
        <xsl:text>XLingPapertempdim</xsl:text>
-->
        <tex:cmd name="setlength">
            <tex:parm>
                <tex:spec cat="esc"/>
                <xsl:text>XLingPapertempdim</xsl:text>
            </tex:parm>
            <tex:parm>
                <xsl:copy-of select="$sListItemWidth"/>
                <xsl:text>+</xsl:text>
                <xsl:copy-of select="$sListItemIndent"/>
            </tex:parm>
        </tex:cmd>
        <tex:spec cat="esc"/>
        <xsl:text>leftskip</xsl:text>
        <tex:spec cat="esc"/>
        <xsl:text>XLingPapertempdim</xsl:text>
        <!--        <xsl:copy-of select="$sListItemIndent"/>-->
        <tex:cmd name="relax" gr="0" nl2="1"/>
        <!--        <tex:spec cat="esc"/>
            <xsl:text>parindent</xsl:text>
            <tex:spec cat="esc"/>
            <xsl:text>XLingPapertempdim</xsl:text>
            <!-\-        <xsl:copy-of select="$sListItemIndent"/>-\->
            <tex:cmd name="relax" gr="0" nl2="1"/>
        -->
        <tex:spec cat="esc"/>
        <xsl:text>interlinepenalty10000</xsl:text>
        <tex:cmd name="XLingPaperlistitem" nl1="1">
            <tex:parm>
                <xsl:copy-of select="$sListItemIndent"/>
            </tex:parm>
            <tex:parm>
                <xsl:copy-of select="$sListItemWidth"/>
            </tex:parm>
            <tex:parm>
                <xsl:choose>
                    <xsl:when test="parent::ul">
                        <xsl:value-of select="$sBulletPoint"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="GetOrderedListItemNumberOrLetter"/>
                    </xsl:otherwise>
                </xsl:choose>
            </tex:parm>
            <tex:parm>
                <xsl:if test="string-length(normalize-space(@id)) &gt; 0">
                    <xsl:call-template name="DoInternalTargetBegin">
                        <xsl:with-param name="sName" select="@id"/>
                    </xsl:call-template>
                    <xsl:call-template name="DoInternalTargetEnd"/>
                </xsl:if>
                <xsl:call-template name="HandleTypesForLi"/>
            </tex:parm>
        </tex:cmd>
        <xsl:if test="following-sibling::*[1][name()='li'] and string-length($sListLayoutSpaceBetween) &gt; 0">
            <tex:cmd name="vspace">
                <tex:parm>
                    <xsl:value-of select="$sListLayoutSpaceBetween"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <tex:spec cat="eg"/>
    </xsl:template>
    <xsl:template name="HandleTypesForLi">
        <xsl:variable name="myEndnote" select="ancestor::endnote"/>
        <xsl:variable name="myAncestorLists" select="ancestor::ol | ancestor::ul"/>
        <xsl:call-template name="DoTypeForLI">
            <xsl:with-param name="myAncestorLists" select="$myAncestorLists"/>
            <xsl:with-param name="myEndnote" select="$myEndnote"/>
        </xsl:call-template>
        <xsl:apply-templates/>
        <xsl:call-template name="DoTypeForLI">
            <xsl:with-param name="myAncestorLists" select="$myAncestorLists"/>
            <xsl:with-param name="myEndnote" select="$myEndnote"/>
            <xsl:with-param name="bIsEnd" select="'Y'"/>
        </xsl:call-template>
    </xsl:template>
    <xsl:template match="text()[parent::li and count(preceding-sibling::*) &gt; 0]">
        <!--        <xsl:call-template name="HandleTypesForLi"/>-->
        <xsl:variable name="myEndnote" select="ancestor::endnote"/>
        <xsl:variable name="myAncestorLists" select="ancestor::ol | ancestor::ul"/>
        <xsl:call-template name="DoTypeForLI">
            <xsl:with-param name="myAncestorLists" select="$myAncestorLists"/>
            <xsl:with-param name="myEndnote" select="$myEndnote"/>
        </xsl:call-template>
        <xsl:value-of select="."/>
        <xsl:call-template name="DoTypeForLI">
            <xsl:with-param name="myAncestorLists" select="$myAncestorLists"/>
            <xsl:with-param name="myEndnote" select="$myEndnote"/>
            <xsl:with-param name="bIsEnd" select="'Y'"/>
        </xsl:call-template>
    </xsl:template>
    <xsl:template match="dl">
        <xsl:if test="count(dt) &gt; 0">
            <xsl:call-template name="OKToBreakHere"/>
            <tex:env name="description">
                <!-- unsuccessful attempt to get space between embedded lists to be more like the normal spacing
            <xsl:if test="count(ancestor::ul | ancestor::ol) &gt; 0">
            <tex:cmd name="vspace*">
            <tex:parm>
            <xsl:text>-.25</xsl:text>
            <tex:cmd name="baselineskip" gr="0" nl2="0"/>
            </tex:parm>
            </tex:cmd>
            </xsl:if>
         -->
                <xsl:call-template name="SetListLengths"/>
                <xsl:call-template name="DoType"/>
                <xsl:if test="exsl:node-set($contentLayoutInfo)/definitionListLayout/@useRaggedRight='yes'">
                    <tex:cmd name="raggedright" gr="0"/>
                </xsl:if>
                <xsl:apply-templates/>
            </tex:env>
            <xsl:if test="following-sibling::*[1][name()='p']">
                <tex:cmd name="par" nl2="1"/>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <xsl:template match="dt">
        <xsl:choose>
            <xsl:when test="count(following-sibling::dt) &lt;= 1">
                <xsl:call-template name="DoNotBreakHere"/>
            </xsl:when>
            <xsl:when test="count(preceding-sibling::dt) &lt;= 1">
                <xsl:call-template name="DoNotBreakHere"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="OKToBreakHere"/>
            </xsl:otherwise>
        </xsl:choose>
        <tex:cmd name="item" nl2="1">
            <tex:opt>
                <xsl:if test="indexedItem[not(ancestor::comment)] or indexedRangeBegin[not(ancestor::comment)] or indexedRangeEnd[not(ancestor::comment)]">
                    <tex:spec cat="bg"/>
                </xsl:if>
                <xsl:apply-templates/>
                <xsl:if test="indexedItem[not(ancestor::comment)] or indexedRangeBegin[not(ancestor::comment)] or indexedRangeEnd[not(ancestor::comment)]">
                    <tex:spec cat="eg"/>
                </xsl:if>
            </tex:opt>
            <tex:parm>
                <xsl:variable name="mydt" select="."/>
                <xsl:apply-templates select="following-sibling::dd[1][name()='dd']" mode="dt">
                    <xsl:with-param name="mydt" select="$mydt"/>
                </xsl:apply-templates>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <xsl:template match="dd" mode="dt">
        <xsl:param name="mydt"/>
        <xsl:if test="parent::dl/@showddOnNewLineInPDF='yes'">
            <tex:cmd name="hfill" gr="0"/>
            <tex:spec cat="esc"/>
            <tex:spec cat="esc"/>
        </xsl:if>
        <xsl:apply-templates/>
        <xsl:if test="count(preceding-sibling::dd[preceding-sibling::dt[1]=$mydt])=0">
            <xsl:for-each select="following-sibling::dd[preceding-sibling::dt[1]=$mydt]">
                <xsl:apply-templates select="self::*" mode="dt">
                    <xsl:with-param name="mydt" select="$mydt"/>
                </xsl:apply-templates>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <!--
        word
    -->
    <xsl:template match="word">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:choose>
            <xsl:when test="not(descendant::word)">
                <xsl:call-template name="OutputWordOrSingle"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="sIsoCode">
                    <xsl:call-template name="GetISOCode"/>
                </xsl:variable>
                <xsl:call-template name="PrepareListForLongtable">
                    <xsl:with-param name="sIsoCode" select="$sIsoCode"/>
                    <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                </xsl:call-template>
                <tex:env name="longtable" nl1="1">
                    <tex:parm>
                        <xsl:text>*</xsl:text>
                        <tex:spec cat="bg"/>
                        <xsl:variable name="iColCount" select="count(langData) + count(gloss)"/>
                        <xsl:value-of select="$iColCount"/>
                        <tex:spec cat="eg"/>
                        <tex:spec cat="bg"/>
                        <xsl:call-template name="CreateColumnSpecDefaultAtExpression"/>
                        <xsl:text>l@</xsl:text>
                        <tex:spec cat="bg"/>
                        <tex:spec cat="esc"/>
                        <tex:spec cat="space"/>
                        <tex:spec cat="eg"/>
                        <tex:spec cat="eg"/>
                        <xsl:text>l</xsl:text>
                    </tex:parm>
                    <xsl:call-template name="OutputListLevelISOCode">
                        <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                        <xsl:with-param name="sIsoCode" select="$sIsoCode"/>
                    </xsl:call-template>
                    <!-- not sure if the following is the best or even needed...
                        <tex:cmd name="hspace*">
                        <tex:parm>-2.5pt</tex:parm>
                        </tex:cmd>  -->
                    <xsl:call-template name="OutputWordOrSingle"/>
                    <!-- remaining rows -->
                    <xsl:apply-templates select="word">
                        <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                    </xsl:apply-templates>
                </tex:env>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <xsl:template match="word[parent::word or ancestor::listWord]">
        <xsl:param name="bListsShareSameCode"/>
        <tex:spec cat="esc"/>
        <tex:spec cat="esc"/>
        <xsl:if test="ancestor::listWord">
            <!-- letter column -->
            <tex:spec cat="align"/>
        </xsl:if>
        <xsl:if test="ancestor::listWord and contains($bListsShareSameCode,'N')">
            <!-- need another column for the ISO code -->
            <tex:spec cat="align"/>
        </xsl:if>
        <xsl:call-template name="OutputWordOrSingle"/>
        <xsl:apply-templates select="word">
            <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
        </xsl:apply-templates>
    </xsl:template>
    <!--
        listWord
    -->
    <xsl:template match="listWord">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:if test="parent::example and count(preceding-sibling::listWord) = 0">
            <xsl:call-template name="OutputList">
                <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--
        secTitle
    -->
    <xsl:template match="secTitle" mode="InMarker">
        <!--        <xsl:apply-templates select="child::node()[name()!='endnote']"/>-->
        <xsl:apply-templates mode="InMarker"/>
    </xsl:template>
    <xsl:template match="secTitle">
        <xsl:apply-templates/>
    </xsl:template>
    <!--
        title
    -->
    <xsl:template match="title" mode="InMarker">
        <xsl:apply-templates mode="InMarker"/>
    </xsl:template>
    <xsl:template match="title[ancestor::chapterInCollection]">
        <xsl:apply-templates/>
    </xsl:template>
    <!--
        single
    -->
    <xsl:template match="single">
        <xsl:call-template name="OutputWordOrSingle"/>
    </xsl:template>
    <!--
        listSingle
    -->
    <xsl:template match="listSingle">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:if test="parent::example and count(preceding-sibling::listSingle) = 0">
            <xsl:call-template name="OutputList">
                <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--
        interlinear
    -->
    <xsl:template match="interlinear">
        <xsl:param name="originalContext"/>
        <xsl:param name="sTextInfoContent"/>
        <xsl:call-template name="HandleAnyInterlinearAlignedWordSkipOverride"/>
        <xsl:choose>
            <xsl:when test="parent::interlinear-text">
                <xsl:choose>
                    <xsl:when test="contains(@XeLaTeXSpecial,'clearpage')">
                        <tex:cmd name="clearpage" gr="0" nl2="0"/>
                    </xsl:when>
                    <xsl:when test="contains(@XeLaTeXSpecial,'pagebreak')">
                        <tex:cmd name="pagebreak" gr="0" nl2="0"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:variable name="sSpaceBetweenUnits">
                            <xsl:value-of select="normalize-space(exsl:node-set($documentLayoutInfo)/interlinearTextLayout/@spaceBetweenUnits)"/>
                        </xsl:variable>
                        <xsl:if test="string-length($sSpaceBetweenUnits) &gt; 0 and count(preceding-sibling::interlinear) &gt; 0">
                            <tex:cmd name="vspace">
                                <tex:parm>
                                    <xsl:value-of select="$sSpaceBetweenUnits"/>
                                </tex:parm>
                            </tex:cmd>
                        </xsl:if>
                        <xsl:if test="$bAutomaticallyWrapInterlinears!='yes'">
                            <tex:cmd name="XLingPaperneedspace" nl2="1">
                                <tex:parm>
                                    <!-- try to guess the number of lines in the first bundle and then add 1 for the title-->
                                    <xsl:value-of select="count(lineGroup[1]/line) + count(free) + count(literal) + count(exampleHeading) + 1"/>
                                    <tex:cmd name="baselineskip" gr="0" nl2="0"/>
                                </tex:parm>
                            </tex:cmd>
                        </xsl:if>
                        <!--                    now using \nobreak command to keep the title/number with what follows.  (2015.12.30)    
                        <tex:cmd name="XLingPaperneedspace" nl2="1">
                            <tex:parm>
                                <!-\- try to guess the number of lines in the first bundle and then add 1 for the title-\->
                                <xsl:variable name="iFirstSetOfLines">
                                    <xsl:choose>
                                        <xsl:when test="$bAutomaticallyWrapInterlinears='yes'">
                                            <xsl:value-of select="count(exampleHeading) + count(lineGroup[1]/line)  + count(free) + count(literal) + 1"/>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <xsl:value-of select="count(lineGroup[1]/line) + count(free) + count(literal) + count(exampleHeading) + 1"/>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </xsl:variable>
                                <!-\-                     <xsl:text>3</xsl:text>-\->
                                <xsl:value-of select="$iFirstSetOfLines"/>
                                <tex:cmd name="baselineskip" gr="0" nl2="0"/>
                            </tex:parm>
                        </tex:cmd>-->
                    </xsl:otherwise>
                </xsl:choose>
                <tex:cmd name="noindent" gr="0"/>
                <xsl:if test="$sBasicPointSize=$sLaTeXBasicPointSize">
                    <!-- need a group to prevent text fonts from being small, too -->
                    <tex:spec cat="bg"/>
                    <tex:cmd name="small" gr="0"/>
                </xsl:if>
                <tex:spec cat="bg"/>
                <!-- default formatting is bold -->
                <tex:spec cat="esc"/>
                <xsl:text>textbf</xsl:text>
                <tex:spec cat="bg"/>
                <xsl:call-template name="DoInternalTargetBegin">
                    <xsl:with-param name="sName" select="@text"/>
                </xsl:call-template>
                <xsl:call-template name="GetInterlinearTextShortTitleAndNumber"/>
                <xsl:call-template name="DoInternalTargetEnd"/>
                <tex:spec cat="eg"/>
                <tex:spec cat="eg"/>
                <xsl:if test="string-length($sTextInfoContent)=0 and preceding-sibling::*[1][name()='textInfo'] and string-length(../@text) &gt; 0">
                    <!-- If the text info has nothing to output and the interlinear-text has a text ID and
                         this is the very first line in the interlinear, insert the hyperlink to the interlinear-text text id.
                         If we try and insert the interlinear-text text id before, then the first line gets indented for some reason.
                         So we do it here.
                    -->
                    <xsl:call-template name="DoInternalTargetBegin">
                        <xsl:with-param name="sName" select="../@text"/>
                    </xsl:call-template>
                    <xsl:call-template name="DoInternalTargetEnd"/>
                </xsl:if>
                <xsl:choose>
                    <xsl:when test="$bAutomaticallyWrapInterlinears='yes'">
                        <tex:cmd name="par" gr="0"/>
                        <tex:cmd name="nobreak" gr="0" nl2="1"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <tex:cmd name="par" gr="0" nl2="1"/>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:if test="$sBasicPointSize=$sLaTeXBasicPointSize">
                    <tex:spec cat="eg"/>
                </xsl:if>
                <!--                <tex:cmd name="leftskip" gr="0" nl2="0"/>-->
                <!--                <tex:spec cat="esc"/>-->
                <!--                <tex:spec cat="esc"/>-->
                <xsl:choose>
                    <xsl:when test="$bAutomaticallyWrapInterlinears='yes'">
                        <!-- if we enclose every one within a group, then any example headings show properly indented. -->
                        <tex:spec cat="bg"/>
                        <tex:spec cat="esc"/>
                        <xsl:text>hangindent2em</xsl:text>
                        <tex:cmd name="relax" gr="0" nl2="1"/>
                        <tex:spec cat="esc"/>
                        <xsl:text>hangafter1</xsl:text>
                        <tex:cmd name="relax" gr="0" nl2="1"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <tex:cmd name="hangindent" gr="0" nl2="0"/>
                        <xsl:value-of select="$sParagraphIndent"/>
                        <tex:cmd name="noindent" gr="0" nl2="0"/>
                        <tex:cmd name="hspace*" nl2="0">
                            <tex:parm>
                                <xsl:value-of select="$sParagraphIndent"/>
                            </tex:parm>
                        </tex:cmd>
                    </xsl:otherwise>
                </xsl:choose>
                <!-- this keeps the entire interlinear on the same page, even if parts of it could easily fit
                    <tex:cmd name="nopagebreak" gr="0" nl2="0"/>-->
                <xsl:call-template name="OutputInterlinear">
                    <xsl:with-param name="mode" select="'NoTextRef'"/>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
                <tex:cmd name="par" gr="0" nl2="1"/>
                <xsl:if test="$bAutomaticallyWrapInterlinears='yes'">
                    <xsl:if test="not(free)">
                        <!-- when there is no free, then we need to set the penalty low so it won't try and
                             keep this and all similar interlinears on the same page -->
                        <tex:cmd name="penalty1" gr="0" nl2="1"/>
                    </xsl:if>
                    <!-- this needs to be after the \par or a long final free will not wrap correctly -->
                    <tex:spec cat="eg"/>
                </xsl:if>
            </xsl:when>
            <xsl:when test="parent::td">
                <!-- when we are in a table, any attempt to insert a new row for a free translation 
                    causes a Missing \endgroup message. By embedding the interlinear within
                    a tabular, we avoid that problem (although, the interlinear may be indented a
                    bit more than we'd like). -->
                <tex:env name="tabular">
                    <tex:opt>t</tex:opt>
                    <tex:spec cat="bg"/>
                    <xsl:text>@</xsl:text>
                    <tex:spec cat="bg"/>
                    <tex:spec cat="eg"/>
                    <xsl:text>l@</xsl:text>
                    <tex:spec cat="bg"/>
                    <tex:spec cat="eg"/>
                    <tex:spec cat="eg"/>
                    <xsl:call-template name="OutputInterlinear">
                        <xsl:with-param name="originalContext" select="$originalContext"/>
                    </xsl:call-template>
                </tex:env>
            </xsl:when>
            <xsl:when test="$bAutomaticallyWrapInterlinears='yes' and $sInterlinearSourceStyle='AfterFirstLine'">
                <xsl:choose>
                    <xsl:when test="parent::example">
                        <xsl:call-template name="DoAnyInterlinearWrappedWithSourceAfterFirstLine">
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:when test="parent::listInterlinear and ../parent::example">
                        <xsl:call-template name="DoAnyInterlinearWrappedWithSourceAfterFirstLine"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="OutputInterlinear">
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="OutputInterlinear">
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        interlinearRef
    -->
    <xsl:template match="interlinearRef">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:variable name="bHasExampleHeading">
            <xsl:choose>
                <xsl:when test="preceding-sibling::*[1][name()='exampleHeading']">
                    <xsl:text>Y</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>N</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="originalContext" select="."/>
        <xsl:for-each select="key('InterlinearReferenceID',@textref)[1]">
            <xsl:choose>
                <xsl:when test="$bAutomaticallyWrapInterlinears='yes' and $sInterlinearSourceStyle='AfterFirstLine'">
                    <xsl:call-template name="DoInterlinearWrappedWithSourceAfterFirstLine">
                        <xsl:with-param name="bHasExampleHeading" select="$bHasExampleHeading"/>
                        <xsl:with-param name="originalContext" select="$originalContext"/>
                        <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates>
                        <xsl:with-param name="bHasExampleHeading" select="$bHasExampleHeading"/>
                        <xsl:with-param name="originalContext" select="$originalContext"/>
                        <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                    </xsl:apply-templates>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>
    <!--
        lineGroup
    -->
    <xsl:template match="lineGroup">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:param name="bHasExampleHeading"/>
        <xsl:param name="originalContext"/>
        <xsl:choose>
            <xsl:when test="$bAutomaticallyWrapInterlinears='yes'">
                <xsl:call-template name="DoWrapableInterlinearLineGroup">
                    <xsl:with-param name="bHasExampleHeading" select="$bHasExampleHeading"/>
                    <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="DoInterlinearLineGroup">
                    <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <xsl:template match="lineGroup" mode="NoTextRef">
        <xsl:choose>
            <xsl:when test="$bAutomaticallyWrapInterlinears='yes'">
                <xsl:call-template name="DoWrapableInterlinearLineGroup">
                    <xsl:with-param name="mode" select="'NoTextRef'"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="DoInterlinearLineGroup">
                    <xsl:with-param name="mode" select="'NoTextRef'"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        line
    -->
    <xsl:template match="line">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:param name="originalContext"/>
        <xsl:call-template name="DoInterlinearLine">
            <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
            <xsl:with-param name="originalContext" select="$originalContext"/>
        </xsl:call-template>
    </xsl:template>
    <xsl:template match="line" mode="NoTextRef">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:call-template name="DoInterlinearLine">
            <xsl:with-param name="mode" select="'NoTextRef'"/>
            <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        conflatedLine
    -->
    <xsl:template match="conflatedLine">
        <tr style="line-height:87.5%">
            <td valign="top">
                <xsl:if test="name(..)='interlinear' and position()=1">
                    <xsl:call-template name="OutputExampleNumber"/>
                </xsl:if>
            </td>
            <xsl:apply-templates/>
        </tr>
    </xsl:template>
    <!--
        lineSet
    -->
    <xsl:template match="lineSet">
        <xsl:choose>
            <xsl:when test="name(..)='conflation'">
                <tr>
                    <xsl:if test="@letter">
                        <td valign="top">
                            <xsl:element name="a">
                                <xsl:attribute name="name">
                                    <xsl:value-of select="@letter"/>
                                </xsl:attribute>
                                <xsl:apply-templates select="." mode="letter"/>.</xsl:element>
                        </td>
                    </xsl:if>
                    <td>
                        <table>
                            <xsl:apply-templates/>
                        </table>
                    </td>
                </tr>
            </xsl:when>
            <xsl:otherwise>
                <td>
                    <table>
                        <xsl:apply-templates/>
                    </table>
                </td>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        conflation
    -->
    <xsl:template match="conflation">
        <xsl:variable name="sCount" select="count(descendant::*[lineSetRow])"/>
        <!--  sCount = <xsl:value-of select="$sCount"/> -->
        <td>
            <img align="middle">
                <xsl:attribute name="src">
                    <xsl:text>LeftBrace</xsl:text>
                    <xsl:value-of select="$sCount"/>
                    <xsl:text>.png</xsl:text>
                </xsl:attribute>
            </img>
        </td>
        <td>
            <table>
                <xsl:apply-templates/>
            </table>
        </td>
        <td>
            <img align="middle">
                <xsl:attribute name="src">
                    <xsl:text>RightBrace</xsl:text>
                    <xsl:value-of select="$sCount"/>
                    <xsl:text>.png</xsl:text>
                </xsl:attribute>
            </img>
        </td>
    </xsl:template>
    <!--
        lineSetRow
    -->
    <xsl:template match="lineSetRow">
        <tr style="line-height:87.5%">
            <xsl:for-each select="wrd">
                <xsl:element name="td">
                    <xsl:attribute name="class">
                        <xsl:value-of select="@lang"/>
                    </xsl:attribute>
                    <xsl:apply-templates/>
                </xsl:element>
            </xsl:for-each>
        </tr>
    </xsl:template>
    <!--
        free
    -->
    <xsl:template match="free">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:param name="originalContext"/>
        <xsl:call-template name="DoInterlinearFree">
            <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
            <xsl:with-param name="originalContext" select="$originalContext"/>
        </xsl:call-template>
    </xsl:template>
    <xsl:template match="free" mode="NoTextRef">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:call-template name="DoInterlinearFree">
            <xsl:with-param name="mode" select="'NoTextRef'"/>
            <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
        </xsl:call-template>
    </xsl:template>
    <xsl:template match="free[string-length(normalize-space(.))=0]"/>
    <!--
        literal
    -->
    <xsl:template match="literal">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:param name="originalContext"/>
        <xsl:call-template name="DoInterlinearFree">
            <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
            <xsl:with-param name="originalContext" select="$originalContext"/>
        </xsl:call-template>
    </xsl:template>
    <xsl:template match="literal" mode="NoTextRef">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:call-template name="DoInterlinearFree">
            <xsl:with-param name="mode" select="'NoTextRef'"/>
            <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        listInterlinear
    -->
    <xsl:template match="listInterlinear">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:if test="parent::example and count(preceding-sibling::listInterlinear) = 0">
            <xsl:call-template name="OutputList">
                <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!-- ================================ -->
    <!--
        phrase
    -->
    <xsl:template match="phrase">
        <xsl:choose>
            <xsl:when test="position() != 1">
                <tex:cmd name="par" gr="0" nl2="1"/>
                <xsl:apply-templates/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <xsl:template match="phrase" mode="NoTextRef">
        <xsl:choose>
            <xsl:when test="position() != 1">
                <tex:cmd name="par" gr="0" nl2="1"/>
                <xsl:apply-templates/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        phrase/item
    -->
    <xsl:template match="phrase/item">
        <xsl:choose>
            <xsl:when test="@type='txt'">
                <xsl:call-template name="OutputFontAttributes">
                    <xsl:with-param name="language" select="key('LanguageID',@lang)"/>
                    <xsl:with-param name="originalContext" select="."/>
                </xsl:call-template>
                <xsl:apply-templates/>
                <xsl:call-template name="OutputFontAttributesEnd">
                    <xsl:with-param name="language" select="key('LanguageID',@lang)"/>
                    <xsl:with-param name="originalContext" select="."/>
                </xsl:call-template>
                <tex:cmd name="par" gr="0" nl2="1"/>
            </xsl:when>
            <xsl:when test="@type='gls'">
                <xsl:choose>
                    <xsl:when test="count(../preceding-sibling::phrase) &gt; 0">
                        <xsl:call-template name="OutputFontAttributes">
                            <xsl:with-param name="language" select="key('LanguageID',@lang)"/>
                            <xsl:with-param name="originalContext" select="."/>
                        </xsl:call-template>
                        <xsl:apply-templates/>
                        <xsl:call-template name="OutputFontAttributesEnd">
                            <xsl:with-param name="language" select="key('LanguageID',@lang)"/>
                            <xsl:with-param name="originalContext" select="."/>
                        </xsl:call-template>
                        <tex:cmd name="par" gr="0" nl2="1"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="OutputFontAttributes">
                            <xsl:with-param name="language" select="key('LanguageID',@lang)"/>
                            <xsl:with-param name="originalContext" select="."/>
                        </xsl:call-template>
                        <xsl:apply-templates/>
                        <xsl:call-template name="OutputFontAttributesEnd">
                            <xsl:with-param name="language" select="key('LanguageID',@lang)"/>
                            <xsl:with-param name="originalContext" select="."/>
                        </xsl:call-template>
                        <tex:cmd name="par" gr="0" nl2="1"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="@type='note'">
                <xsl:text>Note: </xsl:text>
                <xsl:call-template name="OutputFontAttributes">
                    <xsl:with-param name="language" select="key('LanguageID',@lang)"/>
                    <xsl:with-param name="originalContext" select="."/>
                </xsl:call-template>
                <xsl:apply-templates/>
                <xsl:call-template name="OutputFontAttributesEnd">
                    <xsl:with-param name="language" select="key('LanguageID',@lang)"/>
                    <xsl:with-param name="originalContext" select="."/>
                </xsl:call-template>
                <tex:cmd name="par" gr="0" nl2="1"/>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--
        words
    -->
    <xsl:template match="words">
        <xsl:apply-templates/>
        <tex:cmd name="par" gr="0" nl2="1"/>
    </xsl:template>
    <!--
        iword
    -->
    <xsl:template match="iword">
        <xsl:choose>
            <xsl:when test="count(preceding-sibling::iword)=0">
                <tex:cmd name="raggedright" gr="0" nl2="0"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>&#x20;</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <tex:cmd name="leavevmode" gr="0" nl2="0"/>
        <tex:cmd name="hbox">
            <tex:parm>
                <tex:env name="tabular" nl1="0">
                    <tex:opt>t</tex:opt>
                    <tex:parm>
                        <xsl:text>@</xsl:text>
                        <tex:spec cat="bg"/>
                        <tex:spec cat="eg"/>
                        <xsl:text>l@</xsl:text>
                        <tex:spec cat="bg"/>
                        <tex:spec cat="eg"/>
                    </tex:parm>
                    <xsl:apply-templates/>
                </tex:env>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--
        iword/item[@type='txt']
    -->
    <xsl:template match="iword/item[@type='txt']">
        <!--<tex:group>-->
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="key('LanguageID',@lang)"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:apply-templates/>
        <xsl:text>&#160;</xsl:text>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="key('LanguageID',@lang)"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <!--</tex:group>-->
        <tex:spec cat="esc" gr="0" nl2="0"/>
        <tex:spec cat="esc" gr="0" nl2="1"/>
    </xsl:template>
    <!--
        iword/item[@type='gls']
    -->
    <xsl:template match="iword/item[@type='gls']">
        <!--      <tex:group>-->
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="key('LanguageID',@lang)"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:if test="string(.)">
            <xsl:apply-templates/>
            <xsl:text>&#160;</xsl:text>
        </xsl:if>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="key('LanguageID',@lang)"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <!--      </tex:group>-->
        <tex:spec cat="esc" gr="0" nl2="0"/>
        <tex:spec cat="esc" gr="0" nl2="1"/>
    </xsl:template>
    <!--
        iword/item[@type='pos']
    -->
    <xsl:template match="iword/item[@type='pos']">
        <!--      <tex:group>-->
        <xsl:if test="string(.)">
            <xsl:apply-templates/>
            <xsl:text>&#160;</xsl:text>
        </xsl:if>
        <!--      </tex:group>-->
        <tex:spec cat="esc" gr="0" nl2="0"/>
        <tex:spec cat="esc" gr="0" nl2="1"/>
    </xsl:template>
    <!--
        iword/item[@type='punct']
    -->
    <xsl:template match="iword/item[@type='punct']">
        <!--<tex:group>-->
        <xsl:if test="string(.)">
            <xsl:apply-templates/>
            <xsl:text>&#160;</xsl:text>
        </xsl:if>
        <!--               </tex:group>-->
        <tex:spec cat="esc" gr="0" nl2="0"/>
        <tex:spec cat="esc" gr="0" nl2="1"/>
    </xsl:template>
    <!--
        morphemes
    -->
    <xsl:template match="morphemes">
        <!--      <tex:group>-->
        <xsl:apply-templates/>
        <!--               </tex:group>-->
        <tex:spec cat="esc" gr="0" nl2="0"/>
        <tex:spec cat="esc" gr="0" nl2="1"/>
    </xsl:template>
    <!--
        morphset
    -->
    <xsl:template match="morphset">
        <xsl:apply-templates/>
    </xsl:template>
    <!--
        morph
    -->
    <xsl:template match="morph">
        <tex:env name="tabular">
            <tex:opt>t</tex:opt>
            <tex:parm>
                <xsl:text>@</xsl:text>
                <tex:spec cat="bg"/>
                <tex:spec cat="eg"/>
                <xsl:text>l@</xsl:text>
                <tex:spec cat="bg"/>
                <tex:spec cat="eg"/>
            </tex:parm>
            <xsl:apply-templates/>
        </tex:env>
    </xsl:template>
    <!--
        morph/item
    -->
    <xsl:template match="morph/item[@type!='hn' and @type!='cf']">
        <!--<tex:group>-->
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="key('LanguageID',@lang)"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:apply-templates/>
        <xsl:text>&#160;</xsl:text>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="key('LanguageID',@lang)"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <!--               </tex:group>-->
        <tex:spec cat="esc" gr="0" nl2="0"/>
        <tex:spec cat="esc" gr="0" nl2="1"/>
    </xsl:template>
    <!--
        morph/item[@type='hn']
    -->
    <!-- suppress homograph numbers, so they don't occupy an extra line-->
    <xsl:template match="morph/item[@type='hn']"/>
    <!-- This mode occurs within the 'cf' item to display the homograph number from the following item.-->
    <xsl:template match="morph/item[@type='hn']" mode="hn">
        <xsl:apply-templates/>
    </xsl:template>
    <!--
        morph/item[@type='cf']
    -->
    <xsl:template match="morph/item[@type='cf']">
        <!--      <tex:group>-->
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="key('LanguageID',@lang)"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:apply-templates/>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="key('LanguageID',@lang)"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:variable name="homographNumber" select="following-sibling::item[@type='hn']"/>
        <xsl:if test="$homographNumber">
            <tex:cmd name="textsubscript">
                <tex:parm>
                    <xsl:apply-templates select="$homographNumber" mode="hn"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:text>&#160;</xsl:text>
        <!--      </tex:group>-->
        <tex:spec cat="esc" gr="0" nl2="0"/>
        <tex:spec cat="esc" gr="0" nl2="1"/>
    </xsl:template>
    <!-- ================================ -->
    <!--
        definition
    -->
    <xsl:template match="definition">
        <!--        <xsl:template match="definition[not(parent::example)]">-->
        <tex:group>
            <xsl:call-template name="DoType"/>
            <xsl:call-template name="OutputTypeAttributes">
                <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
            </xsl:call-template>
            <xsl:apply-templates/>
            <xsl:call-template name="OutputTypeAttributesEnd">
                <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
            </xsl:call-template>
            <xsl:call-template name="DoTypeEnd"/>
        </tex:group>
    </xsl:template>
    <!--
        listDefinition
    -->
    <xsl:template match="listDefinition">
        <xsl:if test="parent::example and count(preceding-sibling::listDefinition) = 0">
            <xsl:call-template name="OutputList"/>
        </xsl:if>
    </xsl:template>
    <!--
        chart
    -->
    <xsl:template match="chart">
        <xsl:if test="not(ancestor::figure or ancestor::tablenumbered or ancestor::example)">
            <tex:cmd name="vspace" nl1="1">
                <tex:parm>
                    <xsl:call-template name="GetCurrentPointSize">
                        <xsl:with-param name="bAddGlue" select="'Y'"/>
                    </xsl:call-template>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak')">
            <tex:cmd name="pagebreak"/>
        </xsl:if>
        <xsl:if test="contains(@XeLaTeXSpecial,'clearpage')">
            <tex:cmd name="clearpage"/>
        </xsl:if>
        <xsl:call-template name="DoType"/>
        <xsl:call-template name="OutputTypeAttributes">
            <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
        </xsl:call-template>
        <xsl:if test="contains(@XeLaTeXSpecial,'singlespacing')">
            <tex:spec cat="bg"/>
            <tex:cmd name="{$sSingleSpacingCommand}" nl2="0"/>
            <xsl:if test="not(img or ul or ol or dl) and descendant-or-self::br and $sLineSpacing and $sLineSpacing!='single'">
                <!-- It's mainly text that has br elements; we'll use \par for the br elements, but we also need a noindent -->
                <tex:cmd name="noindent"/>
            </xsl:if>
        </xsl:if>
        <xsl:apply-templates/>
        <xsl:if test="contains(@XeLaTeXSpecial,'singlespacing')">
            <tex:spec cat="eg"/>
        </xsl:if>
        <xsl:call-template name="OutputTypeAttributesEnd">
            <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
        </xsl:call-template>
        <xsl:call-template name="DoTypeEnd"/>
        <xsl:if test="not(ancestor::example) and not(child::img) and string-length(.) &gt; 0">
            <xsl:choose>
                <xsl:when test="$sLineSpacing and $sLineSpacing!='single' and contains(@XeLaTeXSpecial,'singlespacing')">
                    <tex:cmd name="par"/>
                </xsl:when>
                <xsl:when test="dl|ol|ul">
                    <!-- do nothing or PDF will fail to be produced -->
                </xsl:when>
                <xsl:otherwise>
                    <tex:spec cat="esc"/>
                    <tex:spec cat="esc"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--
        tree
    -->
    <xsl:template match="tree">
        <xsl:call-template name="DoType"/>
        <xsl:call-template name="OutputTypeAttributes">
            <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
        </xsl:call-template>
        <xsl:apply-templates/>
        <xsl:call-template name="OutputTypeAttributesEnd">
            <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
        </xsl:call-template>
        <xsl:call-template name="DoTypeEnd"/>
    </xsl:template>
    <!--
        table
    -->
    <xsl:template match="table">
        <!--  If this is in an example, an embedded table, or within a list, then there's no need to add extra space around it. -->
        <xsl:choose>
            <xsl:when test="not(parent::example) and not(ancestor::table) and not(ancestor::li) and not(ancestor::framedUnit)">
                <!-- longtable does this effectively anyway
                    <tex:cmd name="vspace">
                    <tex:parm><xsl:value-of select="$sBasicPointSize"/>
                    <xsl:text>pt</xsl:text></tex:parm>
                    </tex:cmd> -->
                <xsl:if test="contains(@XeLaTeXSpecial,'clearpage')">
                    <tex:cmd name="clearpage" gr="0" nl2="0"/>
                </xsl:if>
                <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak')">
                    <tex:cmd name="pagebreak" gr="0" nl2="0"/>
                </xsl:if>
                <tex:cmd name="hspace*">
                    <tex:parm>
                        <xsl:value-of select="$sBlockQuoteIndent"/>
                    </tex:parm>
                </tex:cmd>
                <xsl:if test="not(ancestor::tablenumbered) and $sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacetables='yes'">
                    <xsl:if test="not(ancestor::endnote and exsl:node-set($lineSpacing)/@singlespaceendnotes='yes')">
                        <tex:spec cat="bg"/>
                        <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
                    </xsl:if>
                </xsl:if>
                <!-- Do we want this? 
                    <xsl:attribute name="end-indent">
                    <xsl:value-of select="$sBlockQuoteIndent"/>
                    </xsl:attribute>
                -->
            </xsl:when>
            <!-- not needed
                <xsl:when test="ancestor::li">
                <xsl:attribute name="space-before">
                <xsl:value-of select="$sBasicPointSize div 2"/>pt</xsl:attribute>
                </xsl:when>
            -->
        </xsl:choose>
        <!-- try to get font stuff set before we do the table so it applies throughout the table -->
        <!-- 
            <xsl:if test="parent::example">
            <tex:cmd name="hspace*">
            <tex:parm><xsl:value-of select="$sBlockQuoteIndent"/></tex:parm>
            </tex:cmd>
            <tex:cmd name="hspace*">
            <tex:parm>1.5em</tex:parm>
            </tex:cmd>
            
            <tex:cmd name="parbox">
            <tex:opt>b</tex:opt>
            <tex:parm><xsl:value-of select="$iExampleWidth"/>
            <xsl:text>in</xsl:text>
            </tex:parm> 
            </tex:cmd>
            </xsl:if>
        -->
        <!-- new example handling: trying without all this 
            <xsl:choose>
            <xsl:when test="parent::example">
            <tex:spec cat="align"/>
            <xsl:call-template name="SingleSpaceAdjust"/>
            </xsl:when>
            <xsl:otherwise>
        -->
        <tex:spec cat="bg"/>
        <!-- 
            </xsl:otherwise>
            </xsl:choose>
        -->
        <!-- 
            <xsl:if test="parent::example">
            <tex:cmd name="vspace*">
            <tex:parm>-5.25ex</tex:parm>
            </tex:cmd>
            </xsl:if>
        -->
        <xsl:call-template name="DoType"/>
        <xsl:call-template name="OutputTypeAttributes">
            <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
        </xsl:call-template>
        <!-- Is this the right spot for this? -->
        <xsl:if test="descendant-or-self::endnote and not(ancestor::table) or descendant-or-self::endnoteRef and not(ancestor::table)">
            <!-- longtable allows \footnote, but if the column spec has a 'p' for the column a footnote is in, 
                then one cannot overtly say what the footnote number should be. 
                Therefore, we must set the footnote counter here.
            -->
            <xsl:call-template name="SetLaTeXFootnoteCounter">
                <xsl:with-param name="bInTableNumbered">
                    <xsl:choose>
                        <xsl:when test="ancestor::tablenumbered">
                            <xsl:text>Y</xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>N</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="CalculateTableCellWidths"/>
        <xsl:call-template name="OutputTable"/>
        <xsl:call-template name="OutputTypeAttributesEnd">
            <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
        </xsl:call-template>
        <xsl:call-template name="DoTypeEnd"/>
        <!--   with new ay of handling examples, trying without this     <xsl:if test="not(parent::example)">-->
        <tex:spec cat="eg"/>
        <!--        </xsl:if>-->
        <xsl:choose>
            <xsl:when test="not(parent::example) and not(ancestor::table) and not(ancestor::li)">
                <!-- longtable does this effectively anyway
                    <tex:cmd name="vspace" nl2="1">
                    <tex:parm><xsl:value-of select="$sBasicPointSize"/>
                    <xsl:text>pt</xsl:text></tex:parm>
                    </tex:cmd> -->
                <xsl:if test="not(ancestor::tablenumbered) and $sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacetables='yes'">
                    <xsl:choose>
                        <xsl:when test="ancestor::framedUnit">
                            <!-- do nothing -->
                        </xsl:when>
                        <xsl:when test="not(ancestor::endnote and exsl:node-set($lineSpacing)/@singlespaceendnotes='yes')">
                            <tex:spec cat="eg"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:if>
                <tex:spec cat="nl"/>
            </xsl:when>
            <!-- not needed 
                <xsl:when test="ancestor::li">
                <xsl:attribute name="space-after">
                <xsl:value-of select="$sBasicPointSize div 2"/>pt</xsl:attribute>
                </xsl:when>
            -->
        </xsl:choose>
    </xsl:template>
    <!--
        headerRow for a table
    -->
    <xsl:template match="headerRow">
        <!--
            not using
        -->
    </xsl:template>
    <!--
        headerCol for a table
    -->
    <xsl:template match="th | headerCol">
        <xsl:param name="iBorder" select="0"/>
        <xsl:variable name="bInARowSpan">
            <xsl:call-template name="DetermineIfInARowSpan"/>
        </xsl:variable>
        <xsl:if test="contains($bInARowSpan,'Y')">
            <xsl:call-template name="DoRowSpanAdjust">
                <xsl:with-param name="sList" select="$bInARowSpan"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="DoCellAttributes">
            <xsl:with-param name="iBorder" select="$iBorder"/>
            <xsl:with-param name="bInARowSpan" select="$bInARowSpan"/>
        </xsl:call-template>
        <xsl:if test="string-length(normalize-space(@width)) &gt; 0">
            <!-- the user has specifed a width, so chances are that justification of the header will look stretched out; 
                force ragged right s a deafult
            -->
            <xsl:choose>
                <xsl:when test="@align='right'">
                    <tex:spec cat="esc"/>
                    <xsl:text>raggedleft </xsl:text>
                </xsl:when>
                <xsl:when test="@align='center'">
                    <xsl:if test="not(@colspan) or @colspan=1 or @width">
                        <tex:cmd name="vspace">
                            <tex:parm>
                                <xsl:text>-1.7</xsl:text>
                                <tex:cmd name="baselineskip" gr="0"/>
                            </tex:parm>
                        </tex:cmd>
                        <tex:spec cat="esc"/>
                        <xsl:text>center </xsl:text>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="@align='justify'">
                    <!-- do nothing -->
                </xsl:when>
                <xsl:otherwise>
                    <tex:spec cat="esc"/>
                    <xsl:text>raggedright </xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:call-template name="FormatTHContent"/>
        <xsl:call-template name="DoCellAttributesEnd"/>
        <xsl:if test="following-sibling::th | following-sibling::td | following-sibling::col">
            <tex:spec cat="align"/>
        </xsl:if>
    </xsl:template>
    <!--
        row for a table
    -->
    <xsl:template match="tr | row">
        <xsl:param name="iBorder" select="0"/>
        <!-- 
            <xsl:call-template name="OutputTypeAttributes">
            <xsl:with-param name="sList" select="@xsl-foSpecial"/>
            </xsl:call-template>
        -->
        <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak')">
            <tex:cmd name="pagebreak" gr="0"/>
        </xsl:if>
        <xsl:call-template name="CreateHorizontalLine">
            <xsl:with-param name="iBorder" select="$iBorder"/>
        </xsl:call-template>
        <xsl:if test="contains(@XeLaTeXSpecial,'line-before')">
            <tex:cmd name="midrule" gr="0"/>
        </xsl:if>
        <!--      <xsl:call-template name="DoType"/>-->
        <xsl:call-template name="DoRowBackgroundColor"/>
        <xsl:apply-templates>
            <xsl:with-param name="iBorder" select="$iBorder"/>
        </xsl:apply-templates>
        <tex:spec cat="esc"/>
        <tex:spec cat="esc"/>
        <xsl:if test="contains(ancestor::table[1]/@XeLaTeXSpecial,'row-separation') or contains(@XeLaTeXSpecial,'row-separation')">
            <tex:spec cat="lsb"/>
            <xsl:choose>
                <xsl:when test="contains(@XeLaTeXSpecial,'row-separation')">
                    <xsl:call-template name="HandleXeLaTeXSpecialCommand">
                        <xsl:with-param name="sPattern" select="'row-separation='"/>
                        <xsl:with-param name="default" select="'0pt'"/>
                    </xsl:call-template>
                    <tex:spec cat="rsb"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:for-each select="ancestor::table[1][@XeLaTeXSpecial]">
                        <xsl:call-template name="HandleXeLaTeXSpecialCommand">
                            <xsl:with-param name="sPattern" select="'row-separation='"/>
                            <xsl:with-param name="default" select="'0pt'"/>
                        </xsl:call-template>
                        <tex:spec cat="rsb"/>
                    </xsl:for-each>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:if test="contains(@XeLaTeXSpecial,'line-after')">
            <tex:cmd name="midrule" gr="0"/>
        </xsl:if>
        <xsl:if test="position()=last()">
            <xsl:call-template name="CreateHorizontalLine">
                <xsl:with-param name="iBorder" select="$iBorder"/>
                <xsl:with-param name="bIsLast" select="'Y'"/>
            </xsl:call-template>
        </xsl:if>
        <tex:spec cat="comment" nl2="1"/>
    </xsl:template>
    <!--
        col for a table
    -->
    <xsl:template match="td | col">
        <xsl:param name="iBorder" select="0"/>
        <xsl:variable name="bInARowSpan">
            <xsl:call-template name="DetermineIfInARowSpan"/>
        </xsl:variable>
        <xsl:if test="contains($bInARowSpan,'Y')">
            <xsl:call-template name="HandleFootnotesInTableHeader"/>
            <xsl:call-template name="DoRowSpanAdjust">
                <xsl:with-param name="sList" select="$bInARowSpan"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="DoCellAttributes">
            <xsl:with-param name="iBorder" select="$iBorder"/>
            <xsl:with-param name="bInARowSpan" select="$bInARowSpan"/>
        </xsl:call-template>
        <xsl:if test="../../caption and count(preceding-sibling::td) = 0 and count(../preceding-sibling::tr[td]) = 0 and not(exsl:node-set($backMatterLayoutInfo)/useEndNotesLayout)">
            <xsl:variable name="bCaptionIsBeforeTablenumbered">
                <xsl:call-template name="CaptionIsBeforeTablenumbered"/>
            </xsl:variable>
            <xsl:if test="not(ancestor::tablenumbered) or $bCaptionIsBeforeTablenumbered='Y'">
                <xsl:for-each select="../../caption">
                    <xsl:for-each select="descendant-or-self::endnote">
                        <xsl:apply-templates select=".">
                            <xsl:with-param name="sTeXFootnoteKind" select="'footnotetext'"/>
                        </xsl:apply-templates>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:if>
        </xsl:if>
        <xsl:variable name="parentTablesFirstRow" select="ancestor::table[1]/tr[1]"/>
        <xsl:variable name="colSpansInTable" select="exsl:node-set($parentTablesFirstRow)/td[@colspan] | exsl:node-set($parentTablesFirstRow)/th[@colspan]"/>
        <xsl:variable name="rowSpansInTable" select="exsl:node-set($parentTablesFirstRow)/td[@rowspan] | exsl:node-set($parentTablesFirstRow)/th[@rowspan]"/>
        <xsl:variable name="widthsInFirstRowOfTable" select="exsl:node-set($parentTablesFirstRow)/td[@width] | exsl:node-set($parentTablesFirstRow)/th[@width]"/>
        <xsl:variable name="iPosition" select="count(preceding-sibling::td) + count(preceding-sibling::th) + 1"/>
        <xsl:variable name="widthForThisCell" select="exsl:node-set($parentTablesFirstRow)/*[position()=$iPosition]/@width"/>
        <xsl:if test="string-length(normalize-space(@width)) &gt; 0 or string-length(normalize-space($widthForThisCell)) &gt; 0">
                <!-- the user has specifed a width, so chances are that justification of the header will look stretched out;
                force ragged right as default
            -->
            <xsl:choose>
                <xsl:when test="@align='right'">
                    <tex:spec cat="esc"/>
                    <xsl:text>raggedleft </xsl:text>
                </xsl:when>
                <xsl:when test="@align='center'">
                    <xsl:if test="not(@colspan) or @colspan=1 or @width">
                        <tex:cmd name="vspace">
                            <tex:parm>
                                <xsl:text>-1.7</xsl:text>
                                <tex:cmd name="baselineskip" gr="0"/>
                            </tex:parm>
                        </tex:cmd>
                        <tex:spec cat="esc"/>
                        <xsl:text>center </xsl:text>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="@align='justify'">
                    <!-- do nothing -->
                </xsl:when>
                <xsl:otherwise>
                    <tex:spec cat="esc"/>
                    <xsl:text>raggedright </xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:call-template name="FormatTDContent">
            <xsl:with-param name="bInARowSpan" select="$bInARowSpan"/>
        </xsl:call-template>
        <xsl:call-template name="DoCellAttributesEnd"/>
        <!-- if this td has a rowspan, any endnotes in it will not have their text appear at the bottom of the page; make it happen -->
        <xsl:if test="@rowspan &gt; 0 and descendant-or-self::endnote">
            <xsl:for-each select="descendant-or-self::endnote">
                <xsl:apply-templates select=".">
                    <xsl:with-param name="sTeXFootnoteKind" select="'footnotetext'"/>
                </xsl:apply-templates>
                <tex:cmd name="addtocounter">
                    <tex:parm>footnote</tex:parm>
                    <tex:parm>
                        <xsl:text>1</xsl:text>
                    </tex:parm>
                </tex:cmd>
            </xsl:for-each>
        </xsl:if>
        <xsl:if test="following-sibling::td | following-sibling::col">
            <!--  What was this for???  2009.12.04            <xsl:text>&#xa0;</xsl:text>-->
            <tex:spec cat="align"/>
        </xsl:if>
    </xsl:template>
    <!--
        caption for a table
    -->
    <xsl:template match="caption | endCaption">
        <xsl:param name="iNumCols" select="2"/>
        <xsl:if test="not(ancestor::tablenumbered)">
            <xsl:if test="not(ancestor::figure) and name()='endCaption'">
                <xsl:variable name="sTableCaptionSeparation" select="normalize-space(exsl:node-set($contentLayoutInfo)/tableCaptionLayout/@spaceBetweenTableAndCaption)"/>
                <xsl:if test="string-length($sTableCaptionSeparation) &gt; 0">
                    <tex:spec cat="esc"/>
                    <tex:spec cat="esc"/>
                    <tex:spec cat="lsb"/>
                    <xsl:value-of select="$sTableCaptionSeparation"/>
                    <tex:spec cat="rsb"/>
                </xsl:if>
            </xsl:if>
            <tex:cmd name="multicolumn">
                <tex:parm>
                    <xsl:value-of select="$iNumCols"/>
                </tex:parm>
                <tex:parm>
                    <xsl:call-template name="CreateColumnSpec">
                        <xsl:with-param name="sAlignDefault" select="'c'"/>
                    </xsl:call-template>
                </tex:parm>
                <tex:parm>
                    <xsl:call-template name="DoType"/>
                    <xsl:choose>
                        <xsl:when test="exsl:node-set($contentLayoutInfo)/tableCaptionLayout">
                            <xsl:call-template name="OutputFontAttributes">
                                <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/tableCaptionLayout"/>
                            </xsl:call-template>
                            <xsl:value-of select="exsl:node-set($contentLayoutInfo)/tableCaptionLayout/@textbefore"/>
                            <xsl:apply-templates/>
                            <xsl:value-of select="exsl:node-set($contentLayoutInfo)/tableCaptionLayout/@textafter"/>
                            <xsl:call-template name="OutputFontAttributesEnd">
                                <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/tableCaptionLayout"/>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <tex:cmd name="textbf">
                                <tex:parm>
                                    <xsl:apply-templates/>
                                </tex:parm>
                            </tex:cmd>
                        </xsl:otherwise>
                    </xsl:choose>
                    <xsl:call-template name="DoTypeEnd"/>
                </tex:parm>
            </tex:cmd>
            <tex:spec cat="esc"/>
            <tex:spec cat="esc"/>
            <xsl:if test="not(ancestor::figure) and name()='caption'">
                <xsl:variable name="sTableCaptionSeparation" select="normalize-space(exsl:node-set($contentLayoutInfo)/tableCaptionLayout/@spaceBetweenTableAndCaption)"/>
                <xsl:if test="string-length($sTableCaptionSeparation) &gt; 0">
                    <tex:spec cat="lsb"/>
                    <xsl:value-of select="$sTableCaptionSeparation"/>
                    <tex:spec cat="rsb"/>
                </xsl:if>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--
        exampleHeading
    -->
    <xsl:template match="exampleHeading">
        <xsl:param name="bCalculateHeight" select="'N'"/>
        <xsl:choose>
            <xsl:when test="$bAutomaticallyWrapInterlinears='yes' and following-sibling::*[1][name()='interlinear' or name()='interlinearRef' or name()='listInterlinear']">
                <xsl:call-template name="DoExampleHeadingWhenWrappable">
                    <xsl:with-param name="bCalculateHeight" select="$bCalculateHeight"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$bAutomaticallyWrapInterlinears='yes' and parent::*[name()='interlinear' or name()='listInterlinear']">
                <xsl:call-template name="DoExampleHeadingWhenWrappable">
                    <xsl:with-param name="bCalculateHeight" select="$bCalculateHeight"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <!--      2011.11.15          <xsl:apply-templates/>-->
                <xsl:call-template name="DoExampleHeadingWhenWrappable">
                    <xsl:with-param name="bCalculateHeight" select="$bCalculateHeight"/>
                </xsl:call-template>
                <xsl:choose>
                    <xsl:when test="$bAutomaticallyWrapInterlinears='yes' and following-sibling::*[1][name()='lineGroup']">
                        <tex:cmd name="newline" gr="0" nl2="1"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:if test="following-sibling::*[1][name()='single' or name()='word' or name()='chart' or name()='definition' or name()='tree']">
                            <tex:spec cat="esc"/>
                            <tex:spec cat="esc"/>
                            <xsl:text>*
</xsl:text>
                        </xsl:if>
                        <!-- 2011.11.15                        <xsl:call-template name="CreateBreakAfter">
                            <xsl:with-param name="example" select="parent::excample"/>
                        </xsl:call-template>
-->
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        endnote in li
    -->
    <xsl:template match="endnote[parent::li]">
        <xsl:param name="sTeXFootnoteKind" select="'footnote'"/>
        <!-- need to end any type attributes in effect, do the endnote, and then re-start any type attributes-->
        <xsl:call-template name="DoTypeEnd">
            <xsl:with-param name="type" select="../../@type"/>
        </xsl:call-template>
        <xsl:call-template name="DoEndnote">
            <xsl:with-param name="sTeXFootnoteKind" select="$sTeXFootnoteKind"/>
        </xsl:call-template>
        <xsl:call-template name="DoType">
            <xsl:with-param name="type" select="../../@type"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        ...Ref (InMarker)
    -->
    <xsl:template match="appendixRef" mode="InMarker">
        <xsl:apply-templates select=".">
            <xsl:with-param name="fDoHyperlink" select="'N'"/>
        </xsl:apply-templates>
    </xsl:template>
    <xsl:template match="appendixRef" mode="bookmarks">
        <xsl:apply-templates select=".">
            <xsl:with-param name="fDoHyperlink" select="'N'"/>
        </xsl:apply-templates>
    </xsl:template>
    <xsl:template match="comment" mode="InMarker"/>
    <xsl:template match="endnote" mode="InMarker"/>
    <xsl:template match="endnoteRef" mode="InMarker"/>
    <xsl:template match="exampleRef" mode="InMarker">
        <xsl:apply-templates select=".">
            <xsl:with-param name="fDoHyperlink" select="'N'"/>
        </xsl:apply-templates>
    </xsl:template>
    <xsl:template match="exampleRef" mode="bookmarks">
        <xsl:apply-templates select=".">
            <xsl:with-param name="fDoHyperlink" select="'N'"/>
        </xsl:apply-templates>
    </xsl:template>
    <xsl:template match="genericTarget" mode="InMarker"/>
    <xsl:template match="indexedItem" mode="InMarker"/>
    <xsl:template match="indexedRangeBegin" mode="InMarker"/>
    <xsl:template match="link" mode="InMarker"/>
    <xsl:template match="q" mode="InMarker"/>
    <xsl:template match="sectionRef" mode="InMarker">
        <xsl:apply-templates select=".">
            <xsl:with-param name="fDoHyperlink" select="'N'"/>
        </xsl:apply-templates>
    </xsl:template>
    <xsl:template match="sectionRef" mode="bookmarks">
        <xsl:apply-templates select=".">
            <xsl:with-param name="fDoHyperlink" select="'N'"/>
        </xsl:apply-templates>
    </xsl:template>
    <!--
        indexedItem or indexedRangeBegin
    -->
    <xsl:template match="indexedItem[not(ancestor::comment)] | indexedRangeBegin[not(ancestor::comment)]">
        <xsl:param name="bInMarker" select="'N'"/>
        <xsl:if test="$bInMarker='N'">
            <xsl:call-template name="CreateAddToIndex">
                <xsl:with-param name="id">
                    <xsl:call-template name="CreateIndexedItemID">
                        <xsl:with-param name="sTermId" select="@term"/>
                    </xsl:call-template>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--
        indexedRangeEnd
    -->
    <xsl:template match="indexedRangeEnd[not(ancestor::comment)]">
        <xsl:call-template name="CreateAddToIndex">
            <xsl:with-param name="id">
                <xsl:call-template name="CreateIndexedItemID">
                    <xsl:with-param name="sTermId" select="@begin"/>
                </xsl:call-template>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--
        term
    -->
    <xsl:template match="term" mode="InIndex">
        <xsl:apply-templates/>
    </xsl:template>
    <!-- ===========================================================
        BR
        =========================================================== -->
    <xsl:template match="br">
        <xsl:choose>
            <xsl:when test="ancestor::figure and parent::chart and not(following-sibling::text()) and not(following-sibling::*)">
                <!-- do nothing when it is the last thing in a chart - XeLaTeX will fail if we output the \\ -->
            </xsl:when>
            <xsl:when test="ancestor::caption and not(ancestor::tablenumbered)">
                <!-- do nothing when it is in a caption in a regular table - XeLaTeX will fail if we output the \\ -->
            </xsl:when>
            <xsl:when test="ancestor::chart and not(ancestor::table or ancestor::example) and $sLineSpacing and $sLineSpacing!='single' and ancestor::chart[contains(@XeLaTeXSpecial,'singlespacing')]">
                <tex:cmd name="par"/>
                <xsl:if test="following-sibling::text()">
                    <tex:cmd name="noindent"/>
                </xsl:if>
            </xsl:when>
            <xsl:when test="ancestor::langData or ancestor::td or ancestor::th or ancestor::gloss">
                <!-- these all are using the \vbox{\hbox{}\hbox{}} approach -->
                <tex:spec cat="eg"/>
                <tex:spec cat="esc"/>
                <xsl:text>hbox</xsl:text>
                <tex:spec cat="bg"/>
                <tex:cmd name="strut"/>
            </xsl:when>
            <xsl:when test="ancestor::listDefinition">
                <tex:spec cat="eg"/>
                <tex:spec cat="esc"/>
                <tex:spec cat="esc"/>
                <tex:spec cat="align"/>
                <tex:spec cat="bg"/>
            </xsl:when>
            <xsl:when test="parent::li and preceding-sibling::*[1][name()='example' and child::*[1][name()='table']]">
                <!-- do nothing -->
            </xsl:when>
            <xsl:when test="not(ancestor-or-self::td) and not(ancestor-or-self::th) and not(preceding-sibling::*[1][name()='table'])">
                <xsl:variable name="previousTextOrBr" select="preceding-sibling::text()[1] | preceding-sibling::*[1][name()='br']"/>
                <xsl:if test="name(exsl:node-set($previousTextOrBr)[2])='br'">
                    <!--                    <xsl:if test="name(exsl:node-set($previousTextOrBr)[2])='br' or name(exsl:node-set($previousTextOrBr)[1])='br'">-->
                    <!-- two <br/>s in a row need some content; use a non-breaking space -->
                    <xsl:text>&#xa0;</xsl:text>
                </xsl:if>
                <xsl:if test="name(exsl:node-set($previousTextOrBr)[1])='br' and count($previousTextOrBr)=1">
                    <!--                    <xsl:if test="name(exsl:node-set($previousTextOrBr)[2])='br' or name(exsl:node-set($previousTextOrBr)[1])='br'">-->
                    <!-- two <br/>s in a row need some content; use a non-breaking space -->
                    <xsl:text>&#xa0;</xsl:text>
                </xsl:if>
                <xsl:if test="preceding-sibling::*[1][name()='img']">
                    <xsl:text>&#xa0;</xsl:text>
                </xsl:if>
                <tex:spec cat="esc"/>
                <tex:spec cat="esc"/>
            </xsl:when>
            <xsl:when test="ancestor::th[1][string-length(@width) &gt; 0]">
                <tex:spec cat="esc"/>
                <tex:spec cat="esc"/>
            </xsl:when>
            <xsl:otherwise/>
        </xsl:choose>
    </xsl:template>
    <xsl:template match="abbreviationsShownHere">
        <xsl:choose>
            <xsl:when test="ancestor::endnote">
                <xsl:choose>
                    <xsl:when test="parent::p">
                        <xsl:call-template name="HandleAbbreviationsInCommaSeparatedList"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="HandleAbbreviationsInCommaSeparatedList"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="not(ancestor::p)">
                <!-- ignore any other abbreviationsShownHere in a p except when also in an endnote; everything else goes in a table -->
                <xsl:call-template name="HandleAbbreviationsInTable"/>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <xsl:template match="abbrDefinition"/>
    <xsl:template match="abbrTerm"/>
    <xsl:template match="abbrRef" mode="bookmarks">
        <xsl:apply-templates select="self::*">
            <xsl:with-param name="bInMarker" select="'Y'"/>
        </xsl:apply-templates>
    </xsl:template>
    <xsl:template match="abbrRef" mode="contents">
        <xsl:apply-templates select="self::*">
            <xsl:with-param name="bInMarker" select="'Y'"/>
        </xsl:apply-templates>
    </xsl:template>
    <xsl:template match="abbrRef" mode="InMarker">
        <xsl:apply-templates select="self::*">
            <xsl:with-param name="bInMarker" select="'Y'"/>
        </xsl:apply-templates>
    </xsl:template>
    <!-- ===========================================================
        keyTerm
        =========================================================== -->
    <xsl:template match="keyTerm">
        <tex:group>
            <xsl:call-template name="DoType"/>
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="."/>
                <xsl:with-param name="originalContext" select="."/>
            </xsl:call-template>
            <xsl:if test="not(@font-style) and not(key('TypeID',@type)/@font-style)">
                <tex:spec cat="esc"/>
                <xsl:text>textit</xsl:text>
                <tex:spec cat="bg"/>
            </xsl:if>
            <xsl:apply-templates/>
            <xsl:if test="not(@font-style) and not(key('TypeID',@type)/@font-style)">
                <tex:spec cat="eg"/>
            </xsl:if>
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="."/>
                <xsl:with-param name="originalContext" select="."/>
            </xsl:call-template>
            <xsl:call-template name="DoTypeEnd"/>
        </tex:group>
    </xsl:template>
    <!-- ===========================================================
        FRAMEDUNIT
        =========================================================== -->
    <xsl:template match="framedUnit">
        <tex:env name="mdframed">
            <tex:opt>
                <xsl:variable name="framedtype" select="key('FramedTypeID',@framedtype)"/>
                <xsl:text>backgroundcolor=</xsl:text>
                <xsl:variable name="sColor" select="normalize-space(exsl:node-set($framedtype)/@backgroundcolor)"/>
                <xsl:choose>
                    <xsl:when test="string-length($sColor) &gt; 0">
                        <xsl:call-template name="GetFramedTypeBackgroundColorName">
                            <xsl:with-param name="sId" select="@framedtype"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>white</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:text>,skipabove=</xsl:text>
                <xsl:call-template name="SetFramedTypeItem">
                    <xsl:with-param name="sAttributeValue" select="normalize-space(exsl:node-set($framedtype)/@spacebefore)"/>
                    <xsl:with-param name="bUseBaselineskipAsDefault" select="'Y'"/>
                </xsl:call-template>
                <xsl:text>,skipbelow=</xsl:text>
                <xsl:call-template name="SetFramedTypeItem">
                    <xsl:with-param name="sAttributeValue" select="normalize-space(exsl:node-set($framedtype)/@spaceafter)"/>
                    <xsl:with-param name="bUseBaselineskipAsDefault" select="'Y'"/>
                </xsl:call-template>
                <xsl:text>,innermargin=</xsl:text>
                <xsl:call-template name="SetFramedTypeItem">
                    <xsl:with-param name="sAttributeValue" select="normalize-space(exsl:node-set($framedtype)/@indent-before)"/>
                    <xsl:with-param name="sDefaultValue">.125in</xsl:with-param>
                </xsl:call-template>
                <xsl:text>,outermargin=</xsl:text>
                <xsl:call-template name="SetFramedTypeItem">
                    <xsl:with-param name="sAttributeValue" select="normalize-space(exsl:node-set($framedtype)/@indent-after)"/>
                    <xsl:with-param name="sDefaultValue">.125in</xsl:with-param>
                </xsl:call-template>
                <xsl:text>,innertopmargin=</xsl:text>
                <xsl:call-template name="SetFramedTypeItem">
                    <xsl:with-param name="sAttributeValue" select="normalize-space(exsl:node-set($framedtype)/@innertopmargin)"/>
                    <xsl:with-param name="bUseBaselineskipAsDefault" select="'Y'"/>
                </xsl:call-template>
                <xsl:text>,innerbottommargin=</xsl:text>
                <xsl:call-template name="SetFramedTypeItem">
                    <xsl:with-param name="sAttributeValue" select="normalize-space(exsl:node-set($framedtype)/@innerbottommargin)"/>
                    <xsl:with-param name="bUseBaselineskipAsDefault" select="'Y'"/>
                </xsl:call-template>
                <xsl:text>,innerleftmargin=</xsl:text>
                <xsl:call-template name="SetFramedTypeItem">
                    <xsl:with-param name="sAttributeValue" select="normalize-space(exsl:node-set($framedtype)/@innerleftmargin)"/>
                    <xsl:with-param name="sDefaultValue">.125in</xsl:with-param>
                </xsl:call-template>
                <xsl:text>,innerrightmargin=</xsl:text>
                <xsl:call-template name="SetFramedTypeItem">
                    <xsl:with-param name="sAttributeValue" select="normalize-space(exsl:node-set($framedtype)/@innerrightmargin)"/>
                    <xsl:with-param name="sDefaultValue">.125in</xsl:with-param>
                </xsl:call-template>
                <xsl:text>,align=</xsl:text>
                <xsl:call-template name="SetFramedTypeItem">
                    <xsl:with-param name="sAttributeValue" select="normalize-space(exsl:node-set($framedtype)/@align)"/>
                    <xsl:with-param name="sDefaultValue">left</xsl:with-param>
                </xsl:call-template>
            </tex:opt>
            <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespaceframedunits='yes'">
                <tex:spec cat="bg"/>
                <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
                <tex:cmd name="vspace">
                    <tex:parm>
                        <!-- I do not know why these values are needed, but they are... -->
                        <xsl:choose>
                            <xsl:when test="$sLineSpacing='double'">
                                <xsl:text>-1.3</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>-1.75</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                        <tex:spec cat="esc"/>
                        <xsl:text>baselineskip</xsl:text>
                    </tex:parm>
                </tex:cmd>
            </xsl:if>
            <xsl:apply-templates/>
            <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespaceframedunits='yes'">
                <tex:spec cat="eg"/>
            </xsl:if>
        </tex:env>
        <xsl:if test="name(following-sibling::*[1])='p'">
            <tex:cmd name="par"/>
        </xsl:if>
    </xsl:template>
    <!-- ===========================================================
        LANDSCAPE
        =========================================================== -->
    <xsl:template match="landscape">
        <tex:cmd name="landscape" gr="0" nl2="1"/>
        <xsl:apply-templates/>
        <xsl:if test="contains(../@XeLaTeXSpecial,'fix-final-landscape')">
            <tex:cmd name="XLingPaperendtableofcontents" gr="0"/>
        </xsl:if>
        <tex:cmd name="endlandscape" gr="0" nl2="1"/>
    </xsl:template>
    <!-- ===========================================================
        OBJECT
        =========================================================== -->
    <!-- bookmarks -->
    <xsl:template match="object" mode="bookmarks">
        <xsl:variable name="type" select="key('TypeID',@type)"/>
        <xsl:for-each select="$type">
            <xsl:value-of select="@before"/>
        </xsl:for-each>
        <xsl:apply-templates mode="bookmarks"/>
        <xsl:for-each select="$type">
            <xsl:value-of select="@after"/>
        </xsl:for-each>
    </xsl:template>
    <!-- InMarker -->
    <xsl:template match="object" mode="InMarker">
        <xsl:apply-templates select="self::*"/>
    </xsl:template>
    <xsl:template match="object" mode="Use">
        <xsl:apply-templates select="self::*"/>
    </xsl:template>
    <!-- no mode -->
    <xsl:template match="object">
        <xsl:param name="originalContext"/>
        <xsl:param name="bReversing" select="'N'"/>
        <xsl:variable name="type" select="key('TypeID',@type)"/>
        <tex:spec cat="bg"/>
        <xsl:call-template name="DoType">
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:for-each select="$type">
            <xsl:value-of select="@before"/>
        </xsl:for-each>
        <xsl:choose>
            <xsl:when test="$bReversing = 'Y'">
                <xsl:apply-templates select="node()" mode="reverse">
                    <xsl:sort select="position()" order="descending"/>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:apply-templates>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates>
                    <xsl:with-param name="originalContext"/>
                </xsl:apply-templates>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:for-each select="$type">
            <xsl:value-of select="@after"/>
        </xsl:for-each>
        <xsl:call-template name="DoTypeEnd">
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <tex:spec cat="eg"/>
    </xsl:template>
    <!-- ===========================================================
        GLOSS
        =========================================================== -->
    <xsl:template match="gloss" mode="InMarker">
        <xsl:apply-templates select="self::*">
            <xsl:with-param name="bInMarker" select="'Y'"/>
        </xsl:apply-templates>
    </xsl:template>
    
    <!-- ===========================================================
        IMG
        =========================================================== -->
    <xsl:template match="img" mode="InMarker">
        <xsl:apply-templates select="self::*"/>
    </xsl:template>
    <xsl:template match="img[not(ancestor::headerFooterPageStyles) or parent::fixedText]">
        <xsl:call-template name="HandleImg"/>
    </xsl:template>

    <!-- ===========================================================
        mediaObject
        =========================================================== -->
    <xsl:template match="mediaObject">
        <xsl:param name="fIgnoreMediaObjectInsertion" select="'N'"/>
        <xsl:if test="//lingPaper/@includemediaobjects='yes'">
            <xsl:variable name="sImgFile" select="normalize-space(translate(@src,'\','/'))"/>
            <xsl:variable name="sAdjustedImageFile">
                <xsl:call-template name="CreateAdjustedImageFile">
                    <xsl:with-param name="sImgFile" select="$sImgFile"/>
                </xsl:call-template>
            </xsl:variable>
            <tex:group>
                <xsl:variable name="sFontSize" select="normalize-space(@font-size)"/>
                <xsl:choose>
                    <xsl:when test="string-length($sFontSize) &gt; 0">
                        <xsl:call-template name="HandleFontSize">
                            <xsl:with-param name="sSize" select="$sFontSize"/>
                            <xsl:with-param name="sFontFamily" select="$sMediaObjectFontFamily"/>
                            <xsl:with-param name="language" select="."/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <tex:cmd name="fontspec">
                            <tex:parm>
                                <xsl:value-of select="$sMediaObjectFontFamily"/>
                            </tex:parm>
                        </tex:cmd>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:choose>
                    <xsl:when test="$fIgnoreMediaObjectInsertion='Y'">
                        <xsl:call-template name="GetMediaObjectSymbolCode"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <tex:cmd name="textattachfile">
                            <xsl:variable name="sFontColor" select="normalize-space(@color)"/>
                            <xsl:variable name="sColorCode">
                                <xsl:call-template name="GetColorCodeToUse">
                                    <xsl:with-param name="sFontColor" select="$sFontColor"/>
                                </xsl:call-template>
                            </xsl:variable>
                            <tex:opt>
                                <xsl:text>color= </xsl:text>
                                <xsl:value-of select="translate($sColorCode,',',' ')"/>
                            </tex:opt>
                            <tex:parm>
                                <xsl:value-of select="$sAdjustedImageFile"/>
                            </tex:parm>
                            <tex:parm>
                                <xsl:call-template name="GetMediaObjectSymbolCode"/>
                            </tex:parm>
                        </tex:cmd>
                    </xsl:otherwise>
                </xsl:choose>
            </tex:group>
        </xsl:if>
    </xsl:template>
    <!-- ===========================================================
        INTERLINEAR TEXT
        =========================================================== -->
    <!--  
        interlinear-text
    -->
    <xsl:template match="interlinear-text">
        <tex:spec cat="bg"/>
        <xsl:if test="$bAutomaticallyWrapInterlinears='yes'">
            <xsl:call-template name="SetClubWidowPenalties">
                <xsl:with-param name="iPenalty" select="'10'"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:if test="$sLineSpacing and $sLineSpacing!='single'">
            <tex:spec cat="bg"/>
            <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:if test="preceding-sibling::p[1] or preceding-sibling::pc[1]">
            <tex:cmd name="vspace">
                <tex:parm>
                    <tex:cmd name="baselineskip" gr="0"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:call-template name="SetFootnoteCounterIfNeeded"/>
        <xsl:call-template name="HandleAnyInterlinearAlignedWordSkipOverride"/>
        <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak')">
            <tex:cmd name="pagebreak" gr="0" nl2="0"/>
        </xsl:if>
        <xsl:variable name="sTextInfoContent" select="concat(string(textInfo/textTitle),string(textInfo/source),textInfo/genres/genre)"/>
        <xsl:apply-templates>
            <xsl:with-param name="sTextInfoContent" select="$sTextInfoContent"/>
        </xsl:apply-templates>
        <xsl:if test="$sLineSpacing and $sLineSpacing!='single'">
            <tex:spec cat="eg"/>
        </xsl:if>
        <xsl:if test="$bAutomaticallyWrapInterlinears='yes'">
            <xsl:call-template name="SetClubWidowPenalties"/>
        </xsl:if>
        <tex:spec cat="eg"/>
    </xsl:template>
    <!--  
        textInfo
    -->
    <xsl:template match="textInfo">
        <xsl:param name="sTextInfoContent"/>
        <xsl:if test="string-length(../@text) &gt; 0 and string-length($sTextInfoContent) &gt; 0">
            <xsl:call-template name="DoInternalTargetBegin">
                <xsl:with-param name="sName" select="../@text"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:apply-templates/>
        <xsl:if test="string-length(../@text) &gt; 0 and string-length($sTextInfoContent) &gt; 0">
            <xsl:call-template name="DoInternalTargetEnd"/>
        </xsl:if>
    </xsl:template>
    <!--  
        textTitle
    -->
    <xsl:template match="textTitle">
        <tex:group>
            <tex:cmd name="centering">
                <tex:parm>
                    <!--            <xsl:call-template name="AdjustForBeginOfLaTeXEnvironment"/>-->
                    <tex:cmd name="large" gr="0"/>
                    <!-- default formatting is bold -->
                    <tex:spec cat="esc"/>
                    <xsl:text>textbf</xsl:text>
                    <tex:spec cat="bg"/>
                    <xsl:apply-templates/>
                    <xsl:variable name="contentOfThisElement">
                        <xsl:apply-templates/>
                    </xsl:variable>
                    <tex:spec cat="esc"/>
                    <tex:spec cat="esc"/>
                    <tex:spec cat="eg"/>
                </tex:parm>
            </tex:cmd>
        </tex:group>
    </xsl:template>
    <!--  
        source
    -->
    <xsl:template match="source">
        <tex:group>
            <tex:cmd name="centering">
                <tex:parm>
                    <!--            <xsl:call-template name="AdjustForBeginOfLaTeXEnvironment"/>-->
                    <!-- default formatting is italic -->
                    <tex:spec cat="esc"/>
                    <xsl:text>textit</xsl:text>
                    <tex:spec cat="bg"/>
                    <xsl:apply-templates/>
                    <tex:spec cat="esc"/>
                    <tex:spec cat="esc"/>
                    <tex:spec cat="eg"/>
                </tex:parm>
            </tex:cmd>
        </tex:group>
    </xsl:template>
    <!--  
        AdjustFootnoteNumberPerInterlinearRefs
    -->
    <xsl:template name="AdjustFootnoteNumberPerInterlinearRefs">
        <xsl:param name="originalContext"/>
        <xsl:param name="iAdjust" select="0"/>
        <tex:cmd name="setcounter">
            <tex:parm>
                <xsl:text>footnote</xsl:text>
            </tex:parm>
            <tex:parm>
                <xsl:call-template name="GetFootnoteNumber">
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                    <xsl:with-param name="iAdjust" select="$iAdjust"/>
                </xsl:call-template>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        AdjustForISOCodeInExampleNumber
    -->
    <xsl:template name="AdjustForISOCodeInExampleNumber">
        <xsl:param name="sIsoCode"/>
        <xsl:choose>
            <xsl:when test="contains($sIsoCode,'-')">
                <xsl:text>-1.88</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>-.9</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <tex:cmd name="baselineskip" gr="0" nl2="0"/>
    </xsl:template>
    <!--  
        AdjustLayoutParameterUnitName
    -->
    <xsl:template name="AdjustLayoutParameterUnitName">
        <xsl:param name="sLayoutParam"/>
        <xsl:choose>
            <xsl:when test="$iMagnificationFactor!=1">
                <xsl:variable name="iLength" select="string-length(normalize-space($sLayoutParam))"/>
                <xsl:value-of select="substring($sLayoutParam,1, $iLength - 2)"/>
                <xsl:text>true</xsl:text>
                <xsl:value-of select="substring($sLayoutParam, $iLength - 1)"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sLayoutParam"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        ApplyTemplatesPerTextRefMode
    -->
    <xsl:template name="ApplyTemplatesPerTextRefMode">
        <xsl:param name="mode"/>
        <xsl:param name="bListsShareSameCode"/>
        <xsl:param name="originalContext"/>
        <xsl:choose>
            <xsl:when test="$mode='NoTextRef'">
                <xsl:apply-templates mode="NoTextRef">
                    <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                </xsl:apply-templates>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="*[name() !='interlinearSource']">
                    <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:apply-templates>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        BoxUpWrdsInAllLinesInLineGroup
    -->
    <xsl:template name="BoxUpWrdsInAllLinesInLineGroup">
        <xsl:param name="originalContext"/>
        <xsl:variable name="iPos" select="count(preceding-sibling::wrd) + 1"/>
        <xsl:if test="$bAutomaticallyWrapInterlinears='yes' and @XeLaTeXSpecial='pagebreakafter' and count(ancestor::line[preceding-sibling::*[name()='line']])=0">
            <!-- I'm not sure why, but putting a pagebreak here actually results in this and any other wrd items on the same line
                to occur on the current page.  The pagebreak comes after the end of the line.  -->
            <tex:cmd name="pagebreak" gr="0" nl2="0"/>
        </xsl:if>
        <tex:cmd name="hbox">
            <tex:parm>
                <!--       cannot use a tex:env because it inserts a newline which causes alignment issues
                    <tex:env name="tabular" nl1="0">-->
                <tex:spec cat="esc"/>
                <xsl:text>begin</xsl:text>
                <tex:spec cat="bg"/>
                <xsl:text>tabular</xsl:text>
                <tex:spec cat="eg"/>
                <tex:opt>t</tex:opt>
                <tex:parm>
                    <xsl:text>@</xsl:text>
                    <tex:spec cat="bg"/>
                    <tex:spec cat="eg"/>
                    <xsl:choose>
                        <xsl:when test="id(../../line/@lang)/@rtl='yes'">r</xsl:when>
                        <xsl:when test="id(langData[1]/@lang)/@rtl='yes'">r</xsl:when>
                        <xsl:when test="id(@lang)/@rtl='yes'">r</xsl:when>
                        <xsl:otherwise>l</xsl:otherwise>
                    </xsl:choose>
                    <xsl:text>@</xsl:text>
                    <tex:spec cat="bg"/>
                    <tex:spec cat="eg"/>
                </tex:parm>
                <xsl:for-each select="../preceding-sibling::line">
                    <xsl:for-each select="wrd[position()=$iPos]">
                        <xsl:call-template name="DoWrd">
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                        </xsl:call-template>
                    </xsl:for-each>
                    <tex:spec cat="esc"/>
                    <tex:spec cat="esc"/>
                </xsl:for-each>
                <xsl:call-template name="DoWrd">
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
                <tex:spec cat="esc"/>
                <tex:spec cat="esc"/>
                <xsl:for-each select="../following-sibling::line">
                    <xsl:for-each select="wrd[position()=$iPos]">
                        <xsl:call-template name="DoWrd">
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                        </xsl:call-template>
                    </xsl:for-each>
                    <tex:spec cat="esc"/>
                    <tex:spec cat="esc"/>
                </xsl:for-each>
                <tex:spec cat="lsb"/>
                <xsl:call-template name="GetSpaceBetweenGroups"/>
                <tex:spec cat="rsb"/>
                <tex:spec cat="esc"/>
                <xsl:text>end</xsl:text>
                <tex:spec cat="bg"/>
                <xsl:text>tabular</xsl:text>
                <tex:spec cat="eg"/>
                <!--                            </tex:env>-->
            </tex:parm>
        </tex:cmd>
        <xsl:if test="not($originalContext)">
            <xsl:for-each select="../preceding-sibling::line/wrd[position()=$iPos]">
                <xsl:call-template name="DoFootnoteTextWithinWrappableWrd">
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
            </xsl:for-each>
            <xsl:call-template name="DoFootnoteTextWithinWrappableWrd">
                <xsl:with-param name="originalContext" select="$originalContext"/>
            </xsl:call-template>
            <xsl:for-each select="../following-sibling::line/wrd[position()=$iPos]">
                <xsl:call-template name="DoFootnoteTextWithinWrappableWrd">
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
            </xsl:for-each>
        </xsl:if>
        <xsl:if test="position()!=last()">
            <xsl:choose>
                <xsl:when test="count(../../line) &gt; 1">
                    <tex:cmd name="XLingPaperintspace"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>&#x20;</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--  
        CalculateAvailableTableWidth
    -->
    <xsl:template name="CalculateAvailableTableWidth">
        <tex:cmd name="setlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPaperavailabletablewidth" gr="0"/>
            </tex:parm>
            <tex:parm>
                <xsl:choose>
                    <xsl:when test="ancestor::example">
                        <xsl:choose>
                            <xsl:when test="ancestor::landscape">
                                <xsl:value-of select="number($iPageHeight - $iPageTopMargin - $iPageBottomMargin - $iHeaderMargin - $iFooterMargin)"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="$iExampleWidth"/>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:text>pt</xsl:text>
                        <!--<xsl:call-template name="GetUnitOfMeasure">
                            <xsl:with-param name="sValue" select="$sPageWidth"/>
                        </xsl:call-template>-->
                        <xsl:text> - </xsl:text>
                        <xsl:value-of select="$sExampleIndentBefore"/>
                        <xsl:text> - </xsl:text>
                        <xsl:value-of select="$sExampleIndentAfter"/>
                        <xsl:text> - </xsl:text>
                        <xsl:value-of select="$iNumberWidth"/>
                        <xsl:text>em</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:choose>
                            <xsl:when test="ancestor::landscape">
                                <xsl:value-of select="number($iPageHeight - $iPageTopMargin - $iPageBottomMargin - $iHeaderMargin - $iFooterMargin)"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="number($iPageWidth - $iPageOutsideMargin - $iPageInsideMargin)"/>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:text>pt</xsl:text>
                        <!--<xsl:call-template name="GetUnitOfMeasure">
                            <xsl:with-param name="sValue" select="$sPageWidth"/>
                        </xsl:call-template>-->
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:if test="ancestor::framedUnit">
                    <xsl:variable name="framedtype" select="key('FramedTypeID',ancestor::framedUnit/@framedtype)"/>
                    <xsl:text> - </xsl:text>
                    <xsl:call-template name="SetFramedTypeItem">
                        <xsl:with-param name="sAttributeValue" select="normalize-space(exsl:node-set($framedtype)/@indent-before)"/>
                        <xsl:with-param name="sDefaultValue">.125in</xsl:with-param>
                    </xsl:call-template>
                    <xsl:text> - </xsl:text>
                    <xsl:call-template name="SetFramedTypeItem">
                        <xsl:with-param name="sAttributeValue" select="normalize-space(exsl:node-set($framedtype)/@indent-after)"/>
                        <xsl:with-param name="sDefaultValue">.125in</xsl:with-param>
                    </xsl:call-template>
                    <xsl:text> - </xsl:text>
                    <xsl:call-template name="SetFramedTypeItem">
                        <xsl:with-param name="sAttributeValue" select="normalize-space(exsl:node-set($framedtype)/@innerleftmargin)"/>
                        <xsl:with-param name="sDefaultValue">.125in</xsl:with-param>
                    </xsl:call-template>
                    <xsl:text> - </xsl:text>
                    <xsl:call-template name="SetFramedTypeItem">
                        <xsl:with-param name="sAttributeValue" select="normalize-space(exsl:node-set($framedtype)/@innerrightmargin)"/>
                        <xsl:with-param name="sDefaultValue">.125in</xsl:with-param>
                    </xsl:call-template>
                </xsl:if>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        CalculateColumnsInInterlinearLine
    -->
    <xsl:template name="CalculateColumnsInInterlinearLine">
        <xsl:param name="sList"/>
        <xsl:variable name="sNewList" select="concat(normalize-space($sList),' ')"/>
        <xsl:variable name="sFirst" select="substring-before($sNewList,' ')"/>
        <xsl:variable name="sRest" select="substring-after($sNewList,' ')"/>
        <xsl:text>x</xsl:text>
        <xsl:if test="$sRest">
            <xsl:call-template name="CalculateColumnsInInterlinearLine">
                <xsl:with-param name="sList" select="$sRest"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--  
        CalculateColumnWidths
    -->
    <xsl:template name="CalculateColumnWidths">
        <xsl:for-each select="tr[1]">
            <xsl:for-each select="td | th">
                <xsl:variable name="sColumnLetter">
                    <xsl:call-template name="GetColumnLetter"/>
                </xsl:variable>
                <tex:cmd name="XLingPapersetcolumnwidth" nl1="1">
                    <tex:parm>
                        <tex:cmd name="XLingPapercol{$sColumnLetter}width" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <tex:cmd name="XLingPapermincol{$sColumnLetter}" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <tex:cmd name="XLingPapermaxcol{$sColumnLetter}" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <!-- This is not necessarily exactly correct, but it's the best I've seen -->
                        <xsl:choose>
                            <xsl:when test="position()=1">
                                <xsl:text>-0</xsl:text>
                                <tex:cmd name="tabcolsep" gr="0"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>-2</xsl:text>
                                <tex:cmd name="tabcolsep" gr="0"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </tex:parm>
                </tex:cmd>
            </xsl:for-each>
        </xsl:for-each>
    </xsl:template>
    <!--  
        CalculateExampleAndExampleHeadingHeights
    -->
    <xsl:template name="CalculateExampleAndExampleHeadingHeights">
        <xsl:param name="bListsShareSameCode"/>
        <tex:cmd name="setbox0" gr="0"/>
        <xsl:text>=</xsl:text>
        <tex:cmd name="vbox">
            <tex:parm>
                <xsl:call-template name="DoExampleNumber">
                    <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                </xsl:call-template>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="XLingPaperexamplenumberheight" gr="0"/>
        <xsl:text>=</xsl:text>
        <tex:spec cat="esc"/>
        <xsl:text>ht0 </xsl:text>
        <tex:cmd name="advance" gr="0"/>
        <tex:cmd name="XLingPaperexamplenumberheight" gr="0"/>
        <xsl:text> by </xsl:text>
        <tex:cmd name="dp0" gr="0" nl2="1"/>
        <tex:cmd name="setbox0" gr="0"/>
        <xsl:text>=</xsl:text>
        <tex:cmd name="vbox">
            <tex:parm>
                <xsl:apply-templates select="descendant::exampleHeading[1]">
                    <xsl:with-param name="bCalculateHeight" select="'Y'"/>
                </xsl:apply-templates>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="XLingPaperexampleheadingheight" gr="0"/>
        <xsl:text>=</xsl:text>
        <tex:spec cat="esc"/>
        <xsl:text>ht0 </xsl:text>
        <tex:cmd name="advance" gr="0"/>
        <tex:cmd name="XLingPaperexampleheadingheight" gr="0"/>
        <xsl:text> by </xsl:text>
        <tex:cmd name="dp0" gr="0" nl2="1"/>
    </xsl:template>
    <!--  
        CalculateFootnoteNumber
    -->
    <xsl:template name="CalculateFootnoteNumber">
        <xsl:param name="originalContext"/>
        <xsl:param name="bInTableNumbered"/>
        <xsl:variable name="sFootnoteNumber">
            <xsl:call-template name="GetFootnoteNumber">
                <xsl:with-param name="originalContext" select="$originalContext"/>
                <xsl:with-param name="iAdjust" select="0"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="iFootnoteNumber">
            <xsl:choose>
                <xsl:when test="string-length($sFootnoteNumber)=0">0</xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$sFootnoteNumber"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="iTableCaptionEndnotes">
            <xsl:choose>
                <xsl:when test="$bInTableNumbered='N'">0</xsl:when>
                <xsl:otherwise>
                    <xsl:variable name="bCaptionIsBeforeTablenumbered">
                        <xsl:call-template name="CaptionIsBeforeTablenumbered"/>
                    </xsl:variable>
                    <xsl:choose>
                        <xsl:when test="name()='caption' and $bCaptionIsBeforeTablenumbered='N'">
                            <xsl:value-of select="count(ancestor::tablenumbered/table/descendant::*[name()!='caption']/descendant::endnote)"/>
                        </xsl:when>
                        <xsl:when test="name()='table' and $bCaptionIsBeforeTablenumbered='Y'">
                            <xsl:value-of select="count(ancestor::tablenumbered/table/caption/descendant::endnote)"/>
                        </xsl:when>
                        <xsl:otherwise>0</xsl:otherwise>
                    </xsl:choose>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:value-of select="$iFootnoteNumber + $iTableCaptionEndnotes"/>
    </xsl:template>
    <!--  
        CalculateMaxTableWidth
    -->
    <xsl:template name="CalculateMaxTableWidth">
        <tex:cmd name="setlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapertablemaxwidth" gr="0"/>
            </tex:parm>
            <tex:parm>
                <xsl:for-each select="tr[1]">
                    <xsl:for-each select="td | th">
                        <xsl:variable name="sColumnLetter">
                            <xsl:call-template name="GetColumnLetter"/>
                        </xsl:variable>
                        <tex:cmd name="XLingPapermaxcol{$sColumnLetter}" gr="0"/>
                        <xsl:if test="position() != last()">
                            <xsl:text>+</xsl:text>
                        </xsl:if>
                    </xsl:for-each>
                </xsl:for-each>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        CalculateMinTableWidth
    -->
    <xsl:template name="CalculateMinTableWidth">
        <tex:cmd name="setlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapertableminwidth" gr="0"/>
            </tex:parm>
            <tex:parm>
                <xsl:for-each select="tr[1]">
                    <xsl:for-each select="td | th">
                        <xsl:variable name="sColumnLetter">
                            <xsl:call-template name="GetColumnLetter"/>
                        </xsl:variable>
                        <tex:cmd name="XLingPapermincol{$sColumnLetter}" gr="0"/>
                        <xsl:if test="position() != last()">
                            <xsl:text>+</xsl:text>
                        </xsl:if>
                    </xsl:for-each>
                </xsl:for-each>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        CalculateMinMaxColumnWidths
    -->
    <xsl:template name="CalculateMinMaxColumnWidths">
        <xsl:for-each select="tr">
            <xsl:for-each select="td | th">
                <xsl:variable name="sColumnLetter">
                    <xsl:call-template name="GetColumnLetter"/>
                </xsl:variable>
                <xsl:variable name="sCellMaximumString">
                    <xsl:choose>
                        <xsl:when test="counter">
                            <xsl:apply-templates/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="GetLongestWordInCell"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <tex:cmd name="XLingPaperminmaxcellincolumn" nl1="1">
                    <tex:parm>
                        <xsl:value-of select="$sCellMaximumString"/>
                    </tex:parm>
                    <tex:parm>
                        <tex:cmd name="XLingPapermincol{$sColumnLetter}" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <xsl:choose>
                            <xsl:when test="name()='th'">
                                <xsl:call-template name="FormatTHContent">
                                    <xsl:with-param name="fIncludeEndnotes" select="'N'"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="FormatTDContent">
                                    <xsl:with-param name="bInARowSpan" select="'N'"/>
                                    <xsl:with-param name="fIncludeEndnotes" select="'N'"/>
                                </xsl:call-template>
                            </xsl:otherwise>
                        </xsl:choose>
                        <!--
                        <xsl:apply-templates select="."/>-->
                    </tex:parm>
                    <tex:parm>
                        <tex:cmd name="XLingPapermaxcol{$sColumnLetter}" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <xsl:choose>
                            <xsl:when test="position()=1">
                                <xsl:text>+0</xsl:text>
                                <tex:cmd name="tabcolsep" gr="0"/>
                            </xsl:when>
                            <xsl:when test="position()=last()">
                                <xsl:text>+0</xsl:text>
                                <tex:cmd name="tabcolsep" gr="0"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>+0</xsl:text>
                                <tex:cmd name="tabcolsep" gr="0"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </tex:parm>
                </tex:cmd>
            </xsl:for-each>
        </xsl:for-each>
    </xsl:template>
    <!--  
        CalculateSectionNumberIndent
    -->
    <xsl:template name="CalculateSectionNumberIndent">
        <xsl:param name="contentsLayout" select="exsl:node-set($frontMatterLayoutInfo)/contentsLayout"/>
        <xsl:for-each select="ancestor::*[contains(name(),'section') or name()='appendix' or name()='chapter' or name()='chapterBeforePart' or name()='chapterInCollection']">
            <xsl:call-template name="OutputSectionNumber">
                <xsl:with-param name="sContentsPeriod">
                    <xsl:choose>
                        <xsl:when test="starts-with(name(),'chapter')">
                            <xsl:if test="exsl:node-set($contentsLayout)/@useperiodafterchapternumber='yes'">
                                <xsl:text>.</xsl:text>
                            </xsl:if>
                        </xsl:when>
                        <xsl:when test="name()='appendix'">
                            <xsl:if test="exsl:node-set($contentsLayout)/@useperiodafterappendixletter='yes'">
                                <xsl:text>.</xsl:text>
                            </xsl:if>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:if test="exsl:node-set($contentsLayout)/@useperiodaftersectionnumber='yes'">
                                <xsl:text>.</xsl:text>
                            </xsl:if>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:with-param>
            </xsl:call-template>
            <tex:spec cat="esc"/>
            <xsl:text>&#x20;</xsl:text>
        </xsl:for-each>
    </xsl:template>
    <!--  
        CalculateSectionNumberWidth
    -->
    <xsl:template name="CalculateSectionNumberWidth">
        <xsl:call-template name="OutputSectionNumber">
            <xsl:with-param name="sContentsPeriod">
                <xsl:if test="exsl:node-set($frontMatterLayoutInfo)/contentsLayout/@useperiodaftersectionnumber='yes'">
                    <xsl:text>.</xsl:text>
                </xsl:if>
            </xsl:with-param>
        </xsl:call-template>
        <tex:spec cat="esc"/>
        <xsl:text>thinspace</xsl:text>
        <tex:spec cat="esc"/>
        <xsl:text>thinspace</xsl:text>
    </xsl:template>
    <!--  
        CalculateTableCellWidths
    -->
    <xsl:template name="CalculateTableCellWidths">
        <xsl:if
            test="not(ancestor::table) and not(descendant::*[string-length(@width)&gt;0]) and not(descendant::table) and not(descendant::*[string-length(@colspan)&gt;0]) and not(descendant::*[string-length(@rowspan)&gt;0]) and not(count(tr[1]/td | tr[1]/th)&gt; 26)">
            <xsl:if test="ancestor::endnote and preceding-sibling::*[name()='p' or name()='pc']">
                <!--  we need to do an overt \par here; otherwise the content of the paragraph wmay stretch across the line incorrectly -->
                <tex:cmd name="par"/>
            </xsl:if>
            <xsl:call-template name="CalculateMinMaxColumnWidths"/>
            <xsl:call-template name="CalculateAvailableTableWidth"/>
            <xsl:call-template name="CalculateMinTableWidth"/>
            <xsl:call-template name="CalculateMaxTableWidth"/>
            <xsl:call-template name="CalculateTableWidthRatio"/>
            <xsl:call-template name="CalculateColumnWidths"/>
            <xsl:if test="ancestor::framedUnit and ancestor::example">
                <!-- when we have a table in an example in a framedUnit, we have to force material out (via \par) and then adjust for the vertical space it uses. -->
                <tex:cmd name="par" gr="0"/>
                <tex:cmd name="vspace*">
                    <tex:parm>
                        <xsl:text>-</xsl:text>
                        <tex:cmd name="baselineskip" gr="0"/>
                    </tex:parm>
                </tex:cmd>
            </xsl:if>
            <xsl:if test="descendant-or-self::endnote and not(ancestor::table) or descendant-or-self::endnoteRef and not(ancestor::table)">
                <!-- longtable allows \footnote, but if the column spec has a 'p' for the column a footnote is in, 
                    then one cannot overtly say what the footnote number should be. 
                    Therefore, we must set the footnote counter here.
                -->
                <xsl:call-template name="SetLaTeXFootnoteCounter">
                    <xsl:with-param name="bInTableNumbered">
                        <xsl:choose>
                            <xsl:when test="ancestor::tablenumbered">
                                <xsl:text>Y</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>N</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        CalculateTableWidthRatio
    -->
    <xsl:template name="CalculateTableWidthRatio">
        <tex:cmd name="XLingPapercalculatetablewidthratio" nl1="1"/>
    </xsl:template>
    <!--  
        CaptionIsBeforeTablenumbered
    -->
    <xsl:template name="CaptionIsBeforeTablenumbered">
        <xsl:choose>
            <xsl:when test="/xlingpaper">
                <!-- style sheet takes precedence -->
                <xsl:choose>
                    <xsl:when test="exsl:node-set($documentLayoutInfo)/tablenumberedLayout/@captionLocation='before'">
                        <xsl:text>Y</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>N</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="exsl:node-set($lingPaper)/@tablenumberedLabelAndCaptionLocation='before'">
                        <xsl:text>Y</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>N</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        ConvertHexToDecimal
    -->
    <xsl:template name="ConvertHexToDecimal">
        <xsl:param name="sValue"/>
        <xsl:variable name="sLowerCase" select="translate($sValue,'ABCDEF','abcdef')"/>
        <xsl:choose>
            <xsl:when test="$sLowerCase='a'">10</xsl:when>
            <xsl:when test="$sLowerCase='b'">11</xsl:when>
            <xsl:when test="$sLowerCase='c'">12</xsl:when>
            <xsl:when test="$sLowerCase='d'">13</xsl:when>
            <xsl:when test="$sLowerCase='e'">14</xsl:when>
            <xsl:when test="$sLowerCase='f'">15</xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sValue"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        ConvertPercent20ToSpace
    -->
    <xsl:template name="ConvertPercent20ToSpace">
        <xsl:param name="sImageFile"/>
        <xsl:choose>
            <xsl:when test="contains($sImageFile,$sPercent20)">
                <xsl:value-of select="substring-before($sImageFile,'%20')"/>
                <xsl:text>&#x20;</xsl:text>
                <xsl:call-template name="ConvertPercent20ToSpace">
                    <xsl:with-param name="sImageFile" select="substring-after($sImageFile,$sPercent20)"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sImageFile"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        ConvertUnitOfMeasureToPoints
    -->
    <xsl:template name="ConvertUnitOfMeasureToPoints">
        <xsl:param name="sUnitOfMeasure"/>
        <xsl:variable name="sUnit" select="substring($sUnitOfMeasure,string-length($sUnitOfMeasure)-1,2)"/>
        <xsl:variable name="amount" select="substring-before($sUnitOfMeasure,$sUnit)"/>
        <xsl:choose>
            <xsl:when test="$sUnit='in'">
                <xsl:value-of select="number($amount) * 72.27"/>
            </xsl:when>
            <xsl:when test="$sUnit='cm'">
                <xsl:value-of select="number($amount) * 28.45275"/>
            </xsl:when>
            <xsl:when test="$sUnit='mm'">
                <xsl:value-of select="number($amount) * 2.845275"/>
            </xsl:when>
            <xsl:when test="$sUnit='em'">
                <!-- value is from https://www.convertunits.com/from/em/to/point+[TeX] on 2021.11.30 10:34am -->
                <xsl:value-of select="number($amount) * 12"/>
            </xsl:when>
            <xsl:otherwise>
                <!-- we assume the default is points -->
                <xsl:value-of select="$amount"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- 
        CountPreviousRowspansInMyRow
    -->
    <xsl:template name="CountPreviousRowspansInMyRow">
        <xsl:param name="previousCellsWithRowspansSpanningMyRow"/>
        <xsl:param name="iPosition"/>
        <xsl:param name="iMyInSituColumnNumber"/>
        <xsl:variable name="sOneYForEachColumn">
            <xsl:for-each select="$previousCellsWithRowspansSpanningMyRow">
                <!-- sorting is crucial here; we need the previous ones to go from left to right -->
                <xsl:sort select="count(preceding-sibling::td) +count(preceding-sibling::th)"/>
                <xsl:if test="position() = $iPosition">
                    <xsl:variable name="iRowNumberOfMyCell" select="count(../preceding-sibling::tr) + 1"/>
                    <xsl:variable name="iRealColumnNumberOfCell">
                        <xsl:call-template name="GetRealColumnNumberOfCell">
                            <xsl:with-param name="iRowNumberOfMyCell" select="$iRowNumberOfMyCell"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:if test="$iRealColumnNumberOfCell &lt;= ($iMyInSituColumnNumber + $iPosition)">
                        <!-- the real column is before or at the adjusted cell's column number -->
                        <xsl:choose>
                            <xsl:when test="@colspan &gt; 1">
                                <xsl:value-of select="substring($sYs,1,@colspan)"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>Y</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:if>
                </xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:value-of select="$sOneYForEachColumn"/>
        <xsl:if test="$iPosition &lt; count($previousCellsWithRowspansSpanningMyRow)">
            <xsl:call-template name="CountPreviousRowspansInMyRow">
                <xsl:with-param name="previousCellsWithRowspansSpanningMyRow" select="$previousCellsWithRowspansSpanningMyRow"/>
                <xsl:with-param name="iPosition" select="$iPosition + 1"/>
                <xsl:with-param name="iMyInSituColumnNumber" select="$iMyInSituColumnNumber + string-length($sOneYForEachColumn)"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--
        CreateAddToContents
    -->
    <xsl:template name="CreateAddToContents">
        <xsl:param name="id"/>
        <xsl:if test="$bHasContents='Y'">
            <tex:cmd name="XLingPaperaddtocontents">
                <tex:parm>
                    <xsl:value-of select="translate($id,$sIDcharsToMap, $sIDcharsMapped)"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
    </xsl:template>
    <!--
        CreateAddToIndex
    -->
    <xsl:template name="CreateAddToIndex">
        <xsl:param name="id"/>
        <xsl:if test="$bHasIndex='Y'">
            <tex:cmd name="XLingPaperaddtoindex">
                <tex:parm>
                    <xsl:value-of select="$id"/>
                </tex:parm>
            </tex:cmd>
            <xsl:call-template name="DoInternalTargetBegin">
                <xsl:with-param name="sName" select="$id"/>
            </xsl:call-template>
            <xsl:call-template name="DoInternalTargetEnd"/>
        </xsl:if>
    </xsl:template>
    <!--
        CreateAdjustedImageFile
    -->
    <xsl:template name="CreateAdjustedImageFile">
        <xsl:param name="sImgFile"/>
        <xsl:variable name="sImageFileLocationAdjustment">
            <xsl:choose>
                <xsl:when test="not(contains($sImgFile, ':'))">
                    <!-- .tex file is in temp directory so need to go up one level -->
                    <xsl:text>../</xsl:text>
                    <xsl:value-of select="$sImgFile"/>
                </xsl:when>
                <xsl:otherwise>
                    <!-- is an absolute path -->
                    <xsl:value-of select="$sImgFile"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:call-template name="ConvertPercent20ToSpace">
            <xsl:with-param name="sImageFile" select="$sImageFileLocationAdjustment"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        CreateAllNumberingLevelIndentAndWidthCommands
    -->
    <xsl:template name="CreateAllNumberingLevelIndentAndWidthCommands">
        <xsl:call-template name="CreateNumberingLevelIndentAndWidthCommands">
            <xsl:with-param name="sLevel" select="'levelone'"/>
        </xsl:call-template>
        <xsl:call-template name="CreateNumberingLevelIndentAndWidthCommands">
            <xsl:with-param name="sLevel" select="'leveltwo'"/>
        </xsl:call-template>
        <xsl:call-template name="CreateNumberingLevelIndentAndWidthCommands">
            <xsl:with-param name="sLevel" select="'levelthree'"/>
        </xsl:call-template>
        <xsl:call-template name="CreateNumberingLevelIndentAndWidthCommands">
            <xsl:with-param name="sLevel" select="'levelfour'"/>
        </xsl:call-template>
        <xsl:call-template name="CreateNumberingLevelIndentAndWidthCommands">
            <xsl:with-param name="sLevel" select="'levelfive'"/>
        </xsl:call-template>
        <xsl:call-template name="CreateNumberingLevelIndentAndWidthCommands">
            <xsl:with-param name="sLevel" select="'levelsix'"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        CreateBreakAfter
    -->
    <xsl:template name="CreateBreakAfter">
        <xsl:param name="example"/>
        <xsl:param name="originalContext"/>
        <xsl:param name="sSpaceBeforeFree"/>
        <tex:spec cat="esc"/>
        <tex:spec cat="esc"/>
        <!-- when we're showing ISO codes in an example/interlinearRef and the depth of the example number and ISO code is more than what's in the lineGroup,
            then we need to move any following material up
        -->
        <xsl:choose>
            <xsl:when
                test="exsl:node-set($lingPaper)/@showiso639-3codeininterlinear='yes' and  $bAutomaticallyWrapInterlinears!='yes' and $originalContext and parent::interlinear and ancestor::interlinear-text and count(preceding-sibling::*)=0">
                <xsl:call-template name="HandleISO639-3CodesInBreakAfter">
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when
                test="ancestor-or-self::example/@showiso639-3codes='yes' and  $bAutomaticallyWrapInterlinears!='yes' and $originalContext and parent::interlinear and ancestor::interlinear-text and count(preceding-sibling::*)=0">
                <xsl:call-template name="HandleISO639-3CodesInBreakAfter">
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>*
</xsl:text>
                <xsl:if test="string-length($sSpaceBeforeFree) &gt; 0">
                    <tex:spec cat="lsb"/>
                    <xsl:value-of select="$sSpaceBeforeFree"/>
                    <tex:spec cat="rsb"/>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <xsl:template name="AdjustForLongerISOCodeInInterlinearRef">
        <xsl:param name="iAdjust"/>
        <xsl:text>*</xsl:text>
        <tex:spec cat="lsb"/>
        <xsl:text>-</xsl:text>
        <xsl:value-of select="$iAdjust"/>
        <tex:cmd name="baselineskip" gr="0"/>
        <tex:spec cat="rsb" nl2="1"/>
    </xsl:template>
    <!--
        CreateColumnSpec
    -->
    <xsl:template name="CreateColumnSpec">
        <xsl:param name="iColspan" select="0"/>
        <xsl:param name="iBorder" select="0"/>
        <xsl:param name="sAlignDefault" select="'l'"/>
        <xsl:param name="bUseWidth" select="'Y'"/>
        <xsl:param name="sWidth" select="normalize-space(@width)"/>
        <xsl:call-template name="CreateVerticalLine">
            <xsl:with-param name="iBorder" select="$iBorder"/>
        </xsl:call-template>
        <xsl:call-template name="CreateColumnSpecBackgroundColor"/>
        <xsl:choose>
            <xsl:when test="string-length($sWidth) &gt; 0 and $bUseWidth='Y' and not(descendant::*[name()='endnote']/descendant::example)">
                <!-- We also have to look for endnotes with examples in them.  If we allow such, we get a TeX capacity exceeded error. 
                    This is also the case whenever we use a p{} so at least on Windows, this error occurs.
                -->
                <!--   
                    not needed, but still here so I can remember this way of setting it
                    <xsl:choose>
                    <xsl:when test="@align!='justify'">
                        <tex:spec cat="gt"/>
                        <tex:spec cat="bg"/>
                        <tex:spec cat="esc"/>
                        <xsl:choose>
                            <xsl:when test="@align='right'">
                                <xsl:text>raggedleft</xsl:text>
                            </xsl:when>
                            <xsl:when test="@align='center'">
                                <xsl:text>centering</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>raggedright</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                        <tex:spec cat="esc"/>
                        <xsl:text>arraybackslash</xsl:text>
                        <tex:spec cat="eg"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-\- justify is the default, so there's nothing to do here -\->
                    </xsl:otherwise>
                </xsl:choose>
-->
                <xsl:text>p</xsl:text>
                <tex:spec cat="bg"/>
                <xsl:choose>
                    <xsl:when test="contains($sWidth,'%')">
                        <xsl:call-template name="GetColumnWidthBasedOnPercentage">
                            <xsl:with-param name="iPercentage" select="substring-before(normalize-space($sWidth),'%')"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$sWidth"/>
                    </xsl:otherwise>
                </xsl:choose>
                <tex:spec cat="eg"/>
            </xsl:when>
            <xsl:when
                test="count(ancestor::table)=1 and not(ancestor::table/descendant::*[string-length(@width)&gt;0]) and not(ancestor::table/descendant::table) and not(ancestor::table/descendant::*[string-length(@colspan)&gt;0]) and not(ancestor::table/descendant::*[string-length(@rowspan)&gt;0]) and not(count(ancestor::table/tr[1]/td | ancestor::table/tr[1]/th)&gt; 26) and not(name()='caption' or name()='endCaption') and not(descendant::*[name()='endnote']/descendant::example)">
                <!-- In addition to the usual exceptions here, we also have to look for endnotes with examples in them.  If we allow such, we get a TeX capacity exceeded error. 
                        This is also the case whenever we use a p{} so at least on Windows, this error occurs.
                -->
                <xsl:choose>
                    <xsl:when test="@align='center'">
                        <tex:spec cat="gt"/>
                        <tex:group>
                            <tex:cmd name="centering" gr="0"/>
                        </tex:group>
                    </xsl:when>
                    <xsl:when test="@align='right'">
                        <tex:spec cat="gt"/>
                        <tex:group>
                            <tex:cmd name="raggedleft" gr="0"/>
                        </tex:group>
                    </xsl:when>
                    <xsl:when test="@align='justify'">
                        <!-- do nothing; it defaults to justify -->
                    </xsl:when>
                    <xsl:otherwise>
                        <tex:spec cat="gt"/>
                        <tex:group>
                            <tex:cmd name="raggedright" gr="0"/>
                        </tex:group>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:text>p</xsl:text>
                <tex:spec cat="bg"/>
                <xsl:variable name="sColumnLetter">
                    <xsl:call-template name="GetColumnLetter">
                        <xsl:with-param name="iPos" select="count(preceding-sibling::*)+1"/>
                    </xsl:call-template>
                </xsl:variable>
                <tex:cmd name="XLingPapercol{$sColumnLetter}width" gr="0"/>
                <tex:spec cat="eg"/>
            </xsl:when>
            <xsl:when test="@align='left'">l</xsl:when>
            <xsl:when test="@align='center'">c</xsl:when>
            <xsl:when test="@align='right'">r</xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sAlignDefault"/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="$iColspan &gt; 0">
            <xsl:call-template name="CreateColumnSpec">
                <xsl:with-param name="iColspan" select="$iColspan - 1"/>
                <xsl:with-param name="iBorder" select="$iBorder"/>
                <xsl:with-param name="bUseWidth" select="$bUseWidth"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--
        CreateColumnSpecBackgroundColor
    -->
    <xsl:template name="CreateColumnSpecBackgroundColor">
        <xsl:choose>
            <xsl:when test="string-length(@backgroundcolor) &gt; 0">
                <!-- use backgroundcolor attribute first -->
                <xsl:call-template name="OutputBackgroundColor"/>
            </xsl:when>
            <xsl:when test="string-length(key('TypeID', @type)/@backgroundcolor) &gt; 0">
                <!-- then try the type -->
                <xsl:for-each select="key('TypeID', @type)">
                    <xsl:call-template name="OutputBackgroundColor"/>
                </xsl:for-each>
            </xsl:when>
            <xsl:when test="string-length(../@backgroundcolor) &gt; 0 or string-length(key('TypeID', ../@type)/@backgroundcolor) &gt; 0">
                <!-- next use the row's background color -->
                <xsl:for-each select="..">
                    <xsl:call-template name="DoRowBackgroundColor">
                        <xsl:with-param name="bMarkAsRow" select="'N'"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <!-- finally, try the table -->
                <xsl:for-each select="../..">
                    <xsl:call-template name="DoRowBackgroundColor">
                        <xsl:with-param name="bMarkAsRow" select="'N'"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        CreateColumnSpecDefaultAtExpression
    -->
    <xsl:template name="CreateColumnSpecDefaultAtExpression">
        <xsl:text>@</xsl:text>
        <tex:spec cat="bg"/>
        <tex:spec cat="eg"/>
    </xsl:template>
    <!--
        CreateHorizontalLine
    -->
    <xsl:template name="CreateHorizontalLine">
        <xsl:param name="iBorder"/>
        <xsl:param name="bIsLast" select="'N'"/>
        <xsl:variable name="iCountAncestorEndnotes" select="count(ancestor::endnote)"/>
        <xsl:choose>
            <xsl:when test="$iBorder=1">
                <xsl:choose>
                    <xsl:when test="$bUseBookTabs='Y'">
                        <xsl:choose>
                            <xsl:when test="name()='tr' and count(preceding-sibling::tr)=0">
                                <xsl:call-template name="CreateTopRule">
                                    <xsl:with-param name="iCountAncestorEndnotes" select="$iCountAncestorEndnotes"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name()='table' and tr[1]/th">
                                <xsl:call-template name="CreateTopRule">
                                    <xsl:with-param name="iCountAncestorEndnotes" select="$iCountAncestorEndnotes"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="$bIsLast='Y' and ancestor-or-self::table[1][@border &gt; 0]">
                                <xsl:if test="count(ancestor::table[@border &gt; 0][count(ancestor::endnote)=$iCountAncestorEndnotes])=1">
                                    <tex:cmd name="bottomrule" gr="0"/>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="not(th) and preceding-sibling::tr[1][th[not(@rowspan &gt; 1)]]">
                                <tex:cmd name="midrule" gr="0"/>
                                <xsl:if
                                    test="not(ancestor::example) and not(../ancestor::table) and count(ancestor::table[@border &gt; 0])=1 and not(ancestor::framedUnit) and not(preceding-sibling::tr[1][th[following-sibling::td]])">
                                    <tex:cmd name="endhead" gr="0" sp="1" nl2="0"/>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="th[following-sibling::td] and preceding-sibling::tr[1][th[not(following-sibling::td)]]">
                                <tex:cmd name="midrule" gr="0"/>
                                <xsl:if
                                    test="not(ancestor::example) and not(../ancestor::table) and not(preceding-sibling::tr[position() &gt; 1][th[following-sibling::td]]) and not(ancestor::framedUnit)">
                                    <tex:cmd name="endhead" gr="0" sp="1" nl2="0"/>
                                </xsl:if>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:otherwise>
                        <tex:cmd name="hline" gr="0"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="$iBorder=2">
                <tex:cmd name="hline" gr="0"/>
                <tex:cmd name="hline" gr="0"/>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--
        CreateIndexID
    -->
    <xsl:template name="CreateIndexID">
        <xsl:text>rXLingPapIndex.</xsl:text>
        <xsl:value-of select="generate-id()"/>
    </xsl:template>
    <!--
        CreateIndexedItemID
    -->
    <xsl:template name="CreateIndexedItemID">
        <xsl:param name="sTermId"/>
        <xsl:text>rXLingPapIndexedItem.</xsl:text>
        <xsl:value-of select="$sTermId"/>
        <xsl:text>.</xsl:text>
        <xsl:value-of select="generate-id()"/>
    </xsl:template>
    <!--
        CreateIndexTermID
    -->
    <xsl:template name="CreateIndexTermID">
        <xsl:param name="sTermId"/>
        <xsl:text>rXLingPapIndexTerm.</xsl:text>
        <xsl:value-of select="$sTermId"/>
    </xsl:template>
    <!--
        CreateNumberingLevelIndentAndWidthCommands
    -->
    <xsl:template name="CreateNumberingLevelIndentAndWidthCommands">
        <xsl:param name="sLevel"/>
        <tex:cmd name="newlength" nl2="1">
            <tex:parm>
                <tex:cmd name="{$sLevel}indent" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl2="1">
            <tex:parm>
                <tex:cmd name="{$sLevel}width" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--
        CreatePrefaceID
    -->
    <xsl:template name="CreatePrefaceID">
        <xsl:value-of select="$sPrefaceID"/>
        <xsl:text>.</xsl:text>
        <xsl:value-of select="count(preceding-sibling::preface)+1"/>
    </xsl:template>
    <!--
        CreateTopRule
    -->
    <xsl:template name="CreateTopRule">
        <xsl:param name="iCountAncestorEndnotes"/>
        <xsl:if test="ancestor-or-self::table[1][@border &gt; 0] and count(ancestor-or-self::table[@border &gt; 0][count(ancestor::endnote)=$iCountAncestorEndnotes])=1">
            <xsl:choose>
                <xsl:when test="ancestor::example and not(ancestor-or-self::table[caption]) and ancestor-or-self::table[count(tr)&gt;1]">
                    <tex:cmd name="specialrule">
                        <tex:parm>
                            <tex:cmd name="heavyrulewidth" gr="0" nl2="0"/>
                        </tex:parm>
                        <tex:parm>
                            <xsl:text>-4</xsl:text>
                            <tex:cmd name="aboverulesep" gr="0" nl2="0"/>
                        </tex:parm>
                        <tex:parm>
                            <tex:cmd name="belowrulesep" gr="0" nl2="0"/>
                        </tex:parm>
                    </tex:cmd>
                </xsl:when>
                <xsl:when test="ancestor::li">
                    <tex:cmd name="specialrule">
                        <tex:parm>
                            <tex:cmd name="heavyrulewidth" gr="0" nl2="0"/>
                        </tex:parm>
                        <tex:parm>
                            <xsl:text>4</xsl:text>
                            <tex:cmd name="aboverulesep" gr="0" nl2="0"/>
                        </tex:parm>
                        <tex:parm>
                            <tex:cmd name="belowrulesep" gr="0" nl2="0"/>
                        </tex:parm>
                    </tex:cmd>
                </xsl:when>
                <xsl:otherwise>
                    <tex:cmd name="toprule" gr="0"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--
        CreateVerticalLine
    -->
    <xsl:template name="CreateVerticalLine">
        <xsl:param name="iBorder"/>
        <xsl:param name="bDisallowVerticalLines" select="$bUseBookTabs"/>
        <xsl:if test="$bDisallowVerticalLines!='Y'">
            <xsl:choose>
                <xsl:when test="$iBorder=1">
                    <tex:spec cat="vert"/>
                </xsl:when>
                <xsl:when test="$iBorder=2">
                    <tex:spec cat="vert"/>
                    <tex:spec cat="vert"/>
                </xsl:when>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--  
        DefineAFont
    -->
    <xsl:template name="DefineAFont">
        <xsl:param name="sFontName"/>
        <xsl:param name="sBaseFontName"/>
        <xsl:param name="sPointSize"/>
        <xsl:param name="bIsBold" select="'N'"/>
        <xsl:param name="bIsItalic" select="'N'"/>
        <xsl:param name="sColor" select="'default'"/>
        <tex:spec cat="esc"/>font<tex:spec cat="esc"/>
        <xsl:value-of select="$sFontName"/>
        <xsl:text>="</xsl:text>
        <xsl:value-of select="$sBaseFontName"/>
        <xsl:if test="$bIsBold='Y'">/B</xsl:if>
        <xsl:if test="$bIsItalic='Y'">/I</xsl:if>
        <xsl:if test="$sColor!='default'">
            <xsl:text>:color=</xsl:text>
            <xsl:call-template name="GetColorHexCode">
                <xsl:with-param name="sColor" select="$sColor"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:text>" at </xsl:text>
        <xsl:value-of select="$sPointSize"/>
        <xsl:text>pt
</xsl:text>
    </xsl:template>
    <!--  
        DefineAFontFamily
    -->
    <xsl:template name="DefineAFontFamily">
        <xsl:param name="sFontFamilyName"/>
        <xsl:param name="sBaseFontName"/>
        <tex:cmd name="newfontfamily" nl2="1">
            <tex:parm>
                <tex:spec cat="esc"/>
                <xsl:value-of select="$sFontFamilyName"/>
            </tex:parm>
            <xsl:variable name="bIsGraphite">
                <xsl:choose>
                    <xsl:when test="contains(@XeLaTeXSpecial, $sGraphite)">Y</xsl:when>
                    <xsl:when test="contains(../@XeLaTeXSpecial, $sGraphite)">Y</xsl:when>
                    <xsl:otherwise>N</xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:variable name="sFontFeatureList">
                <xsl:choose>
                    <xsl:when test="contains(@XeLaTeXSpecial, $sFontFeature)">
                        <xsl:value-of select="@XeLaTeXSpecial"/>
                    </xsl:when>
                    <xsl:when test="contains(../@XeLaTeXSpecial, $sFontFeature)">
                        <xsl:value-of select="../@XeLaTeXSpecial"/>
                    </xsl:when>
                </xsl:choose>
            </xsl:variable>
            <xsl:if
                test="$bIsGraphite='Y' or string-length($sFontFeatureList) &gt; 0 or contains(@XeLaTeXSpecial, $sFontScript) or contains(../@XeLaTeXSpecial, $sFontScript) or contains(@XeLaTeXSpecial, $sFontScriptLower) or contains(../@XeLaTeXSpecial, $sFontScriptLower)">
                <tex:opt>
                    <xsl:if test="$bIsGraphite='Y' or string-length($sFontFeatureList) &gt; 0">
                        <xsl:choose>
                            <xsl:when test="$bIsGraphite='Y'">
                                <xsl:value-of select="$sRendererIsGraphite"/>
                                <xsl:call-template name="HandleXeLaTeXSpecialFontFeature">
                                    <xsl:with-param name="sList" select="$sFontFeatureList"/>
                                    <xsl:with-param name="bIsFirstOpt" select="'N'"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="HandleXeLaTeXSpecialFontFeature">
                                    <xsl:with-param name="sList" select="$sFontFeatureList"/>
                                    <xsl:with-param name="bIsFirstOpt" select="'Y'"/>
                                </xsl:call-template>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:if>
                    <!-- some open type fonts also need a special script; handle them here -->
                    <xsl:choose>
                        <xsl:when test="contains(@XeLaTeXSpecial, $sFontScript) or contains(@XeLaTeXSpecial, $sFontScriptLower)">
                            <xsl:call-template name="HandleFontScriptOrLanguageXeLaTeXSpecial">
                                <xsl:with-param name="sFontSpecial" select="$sFontScript"/>
                                <xsl:with-param name="sDefault" select="'arab'"/>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:when test="contains(../@XeLaTeXSpecial, $sFontScript) or contains(../@XeLaTeXSpecial, $sFontScriptLower)">
                            <xsl:for-each select="..">
                                <xsl:call-template name="HandleFontScriptOrLanguageXeLaTeXSpecial">
                                    <xsl:with-param name="sFontSpecial" select="$sFontScript"/>
                                    <xsl:with-param name="sDefault" select="'arab'"/>
                                </xsl:call-template>
                            </xsl:for-each>
                        </xsl:when>
                    </xsl:choose>
                </tex:opt>
            </xsl:if>
            <tex:parm>
                <xsl:choose>
                    <!-- try to map some "default" fonts to potential real fonts -->
                    <xsl:when test="$sBaseFontName='Monospaced'">Courier New</xsl:when>
                    <xsl:when test="$sBaseFontName='SansSerif'">Arial</xsl:when>
                    <xsl:when test="$sBaseFontName='Serif'">Times New Roman</xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$sBaseFontName"/>
                    </xsl:otherwise>
                </xsl:choose>
                <!-- some open type fonts also need a special language; handle them here -->
                <xsl:choose>
                    <xsl:when test="contains(@XeLaTeXSpecial, $sFontLanguage)">
                        <xsl:call-template name="HandleFontScriptOrLanguageXeLaTeXSpecial">
                            <xsl:with-param name="sFontSpecial" select="$sFontLanguage"/>
                            <xsl:with-param name="sDefault" select="'ARA'"/>
                            <xsl:with-param name="sPunctuation" select="':'"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:when test="contains(../@XeLaTeXSpecial, $sFontLanguage)">
                        <xsl:for-each select="..">
                            <xsl:call-template name="HandleFontScriptOrLanguageXeLaTeXSpecial">
                                <xsl:with-param name="sFontSpecial" select="$sFontLanguage"/>
                                <xsl:with-param name="sDefault" select="'ARA'"/>
                                <xsl:with-param name="sPunctuation" select="':'"/>
                            </xsl:call-template>
                        </xsl:for-each>
                    </xsl:when>
                </xsl:choose>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        DefineBlockQuoteWithIndent
    -->
    <xsl:template name="DefineBlockQuoteWithIndent">
        <tex:cmd name="renewenvironment">
            <tex:parm>quotation</tex:parm>
            <tex:parm>
                <tex:cmd name="list">
                    <tex:parm/>
                    <tex:parm>
                        <tex:cmd name="leftmargin" gr="0"/>
                        <xsl:text>=</xsl:text>
                        <xsl:value-of select="$sBlockQuoteIndent"/>
                        <tex:cmd name="rightmargin" gr="0"/>
                        <xsl:text>=</xsl:text>
                        <xsl:value-of select="$sBlockQuoteIndent"/>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="item">
                    <tex:opt/>
                </tex:cmd>
            </tex:parm>
            <tex:parm>
                <tex:cmd name="endlist" gr="0"/>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        DetermineIfInARowSpan
        (Returns a string of 'Y's, one for each column covered by a previous rowspan)
    -->
    <xsl:template name="DetermineIfInARowSpan">
        <xsl:variable name="myCell" select="."/>
        <xsl:variable name="iRowNumberOfMyCell" select="count(../preceding-sibling::tr) + 1"/>
        <xsl:variable name="previousCellsWithRowspansSpanningMyRow"
            select="../preceding-sibling::tr/th[@rowspan][($iRowNumberOfMyCell - (count(../preceding-sibling::tr) + 1)) + 1 &lt;= @rowspan] | ../preceding-sibling::tr/td[@rowspan][($iRowNumberOfMyCell - (count(../preceding-sibling::tr) + 1)) + 1 &lt;= @rowspan]"/>
        <xsl:if test="count($previousCellsWithRowspansSpanningMyRow) &gt; 0">
            <!-- We now know that the current cell is in a row that is included by some previous cell's rowspan. -->
            <xsl:for-each select="$previousCellsWithRowspansSpanningMyRow">
                <!-- sorting is crucial here; we need the previous ones to go from left to right -->
                <xsl:sort select="count(preceding-sibling::td) +count(preceding-sibling::th)"/>
                <!-- Figure out if the current cell is just after such a rowspan (or sequence of contiguous rowspans) by
                    getting the real (absolute) column number of  the preceding cell and comparing it to the adjusted 
                    in situ column number of the current cell. 
                -->
                <xsl:variable name="iRealColumnNumberOfCell">
                    <xsl:call-template name="GetRealColumnNumberOfCell">
                        <xsl:with-param name="iRowNumberOfCell" select="count(../preceding-sibling::tr) + 1"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:variable name="myPrecedingSiblings" select="exsl:node-set($myCell)/preceding-sibling::td | exsl:node-set($myCell)/preceding-sibling::th"/>
                <xsl:variable name="iMyInSituColumnNumber" select="count(exsl:node-set($myPrecedingSiblings)[not(number(@colspan) &gt; 0)]) + sum(exsl:node-set($myPrecedingSiblings)[number(@colspan) &gt; 0]/@colspan)"/>
                <xsl:if test="$iRealColumnNumberOfCell = ($iMyInSituColumnNumber + position()) - 1">
                    <xsl:choose>
                        <xsl:when test="@colspan &gt; 1">
                            <!-- if this previous cell has a colspan, we need to account for it -->
                            <xsl:value-of select="substring($sYs,1,@colspan)"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>Y</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:if>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <!--
        DoAnyInterlinearWrappedWithSourceAfterFirstLine
    -->
    <xsl:template name="DoAnyInterlinearWrappedWithSourceAfterFirstLine">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:choose>
            <xsl:when test="interlinearSource">
                <xsl:call-template name="DoInterlinearWrappedWithSourceAfterFirstLine">
                    <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="string-length(normalize-space(@textref)) &gt; 0">
                <xsl:call-template name="DoInterlinearWrappedWithSourceAfterFirstLine">
                    <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="name()='listInterlinear'">
                        <xsl:apply-templates>
                            <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                        </xsl:apply-templates>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="OutputInterlinear"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        DoAuthorFootnoteNumber
    -->
    <xsl:template name="DoAuthorFootnoteNumber">
        <xsl:variable name="iTitleEndnote">
            <xsl:call-template name="GetCountOfEndnoteInTitleUsingSymbol"/>
        </xsl:variable>
        <xsl:variable name="iAuthorPosition" select="count(parent::author/preceding-sibling::author[endnote]) + $iTitleEndnote + 1"/>
        <xsl:choose>
            <xsl:when test="$iAuthorPosition &lt; 10">
                <xsl:value-of select="$iAuthorPosition"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="floor($iAuthorPosition div 9)"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        DoBreakBeforeLink
    -->
    <xsl:template name="DoBreakBeforeLink">
        <xsl:if test="contains(@XeLaTeXSpecial,'break-before')">
            <!-- since \\ will fail in some table cells, only do in paragraphs for now -->
            <xsl:if test=" ancestor::p or ancestor::pc">
                <tex:spec cat="esc"/>
                <tex:spec cat="esc"/>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--
        DoCellAttributes
    -->
    <xsl:template name="DoCellAttributes">
        <xsl:param name="iBorder" select="0"/>
        <xsl:param name="bInARowSpan"/>
        <xsl:variable name="valignFixup">
            <xsl:call-template name="HandleXeLaTeXSpecialCommand">
                <xsl:with-param name="sPattern" select="'valign-fixup='"/>
                <xsl:with-param name="default" select="'0pt'"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="number(@rowspan) &gt; 0 and number(@colspan) &gt; 0 or $valignFixup!='0pt' and number(@colspan) &gt; 0">
                <xsl:call-template name="HandleMulticolumnInCell">
                    <xsl:with-param name="bInARowSpan" select="$bInARowSpan"/>
                    <xsl:with-param name="iBorder" select="$iBorder"/>
                    <xsl:with-param name="iColSpan" select="@colspan"/>
                </xsl:call-template>
                <xsl:call-template name="HandleMultirowInCell">
                    <xsl:with-param name="valignFixup" select="$valignFixup"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="number(@colspan) &gt; 0">
                <xsl:call-template name="HandleMulticolumnInCell">
                    <xsl:with-param name="bInARowSpan" select="$bInARowSpan"/>
                    <xsl:with-param name="iBorder" select="$iBorder"/>
                    <xsl:with-param name="iColSpan" select="@colspan"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="number(@rowspan) &gt; 0 or $valignFixup!='0pt'">
                <xsl:call-template name="HandleMulticolumnInCell">
                    <xsl:with-param name="bInARowSpan" select="$bInARowSpan"/>
                    <xsl:with-param name="iBorder" select="$iBorder"/>
                    <xsl:with-param name="iColSpan" select="'1'"/>
                </xsl:call-template>
                <xsl:call-template name="HandleMultirowInCell">
                    <xsl:with-param name="valignFixup" select="$valignFixup"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="@align">
                <xsl:variable name="parentTablesFirstRow" select="ancestor::table[1]/tr[1]"/>
                <xsl:variable name="colSpansInTable" select="exsl:node-set($parentTablesFirstRow)/td[@colspan] | exsl:node-set($parentTablesFirstRow)/th[@colspan]"/>
                <xsl:variable name="rowSpansInTable" select="exsl:node-set($parentTablesFirstRow)/td[@rowspan] | exsl:node-set($parentTablesFirstRow)/th[@rowspan]"/>
                <xsl:variable name="widthsInFirstRowOfTable" select="exsl:node-set($parentTablesFirstRow)/td[@width] | exsl:node-set($parentTablesFirstRow)/th[@width]"/>
                <xsl:choose>
                    <xsl:when test="count($colSpansInTable) &gt; 0 or count($rowSpansInTable) &gt; 0 or count($widthsInFirstRowOfTable) = 0">
                        <!-- there are no widths set or there are some column spans somewhere in this table so figuring out widths is too complicated; punt -->
                        <xsl:call-template name="HandleMulticolumnInCell">
                            <xsl:with-param name="bInARowSpan" select="$bInARowSpan"/>
                            <xsl:with-param name="iBorder" select="$iBorder"/>
                            <xsl:with-param name="iColSpan" select="'1'"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- table has widths in first row and is simple enough to set widths of all columns -->
                        <xsl:call-template name="HandleMulticolumnInCell">
                            <xsl:with-param name="bInARowSpan" select="$bInARowSpan"/>
                            <xsl:with-param name="iBorder" select="$iBorder"/>
                            <xsl:with-param name="iColSpan" select="'1'"/>
                            <xsl:with-param name="sWidth">
                                <xsl:choose>
                                    <xsl:when test="@width">
                                        <xsl:value-of select="@width"/>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:variable name="iPosition" select="count(preceding-sibling::td) + count(preceding-sibling::th) + 1"/>
                                        <xsl:variable name="widthForThisCell" select="exsl:node-set($parentTablesFirstRow)/*[position()=$iPosition]/@width"/>
                                        <xsl:choose>
                                            <xsl:when test="string-length(normalize-space($widthForThisCell)) &gt; 0">
                                                <xsl:value-of select="$widthForThisCell"/>
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <!-- do nothing; its missing; use default -->
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
        </xsl:choose>
        <!--  later
            <xsl:if test="@valign">
            <xsl:attribute name="display-align">
            <xsl:choose>
            <xsl:when test="@valign='top'">before</xsl:when>
            <xsl:when test="@valign='middle'">center</xsl:when>
            <xsl:when test="@valign='bottom'">after</xsl:when>
            - I'm not sure what we should do with this one... -
            <xsl:when test="@valign='baseline'">center</xsl:when>
            <xsl:otherwise>auto</xsl:otherwise>
            </xsl:choose>
            </xsl:attribute>
            </xsl:if>
            <xsl:if test="@width">
            <xsl:attribute name="width">
            <xsl:value-of select="@width"/>
            </xsl:attribute>
            </xsl:if>
        -->
    </xsl:template>
    <!--
        DoCellAttributesEnd
    -->
    <xsl:template name="DoCellAttributesEnd">
        <xsl:variable name="valignFixup">
            <xsl:call-template name="HandleXeLaTeXSpecialCommand">
                <xsl:with-param name="sPattern" select="'valign-fixup='"/>
                <xsl:with-param name="default" select="'0pt'"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="number(@rowspan) &gt; 0 and number(@colspan) &gt; 0">
                <tex:spec cat="eg"/>
                <tex:spec cat="eg"/>
            </xsl:when>
            <xsl:when test="number(@colspan) &gt; 0">
                <tex:spec cat="eg"/>
            </xsl:when>
            <xsl:when test="number(@rowspan) &gt; 0 or $valignFixup!='0pt'">
                <tex:spec cat="eg"/>
                <tex:spec cat="eg"/>
            </xsl:when>
            <xsl:when test="@align">
                <tex:spec cat="eg"/>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--
        DoColor
    -->
    <xsl:template name="DoColor">
        <xsl:param name="sFontColor"/>
        <tex:cmd name="textcolor">
            <tex:opt>rgb</tex:opt>
            <tex:parm>
                <xsl:call-template name="GetColorCodeToUse">
                    <xsl:with-param name="sFontColor" select="$sFontColor"/>
                </xsl:call-template>
            </tex:parm>
        </tex:cmd>
        <tex:spec cat="bg"/>
        <!-- 
            <tex:cmd name="addfontfeature">
            <tex:parm>
            <xsl:text>Color=</xsl:text>
            <xsl:call-template name="GetColorHexCode">
            <xsl:with-param name="sColor" select="$sFontColor"/>
            </xsl:call-template>
            </tex:parm>
            </tex:cmd>
        -->
    </xsl:template>
    <!--
        DoEmbeddedBrBegin
    -->
    <xsl:template name="DoEmbeddedBrBegin">
        <xsl:param name="iCountBr"/>
        <xsl:if test="$iCountBr!=0">
            <!--<tex:spec cat="esc"/>
                <xsl:text>raise</xsl:text>
                <xsl:choose>
                <xsl:when test="$iCountBr=1">.5</xsl:when>
                <xsl:when test="$iCountBr=2">1</xsl:when>
                <xsl:when test="$iCountBr=3">1.5</xsl:when>
                <xsl:when test="$iCountBr=4">2</xsl:when>
                <xsl:when test="$iCountBr=5">2.5</xsl:when>
                <xsl:otherwise>0</xsl:otherwise>
                </xsl:choose>-->
            <!--            <tex:spec cat="esc"/>
                <xsl:text>multiply1by</xsl:text>
                <xsl:value-of select="$iCountBr"/> -->
            <!--            <tex:cmd name="baselineskip" gr="0"/>-->
            <tex:spec cat="esc"/>
            <xsl:choose>
                <xsl:when test="ancestor-or-self::listWord and ancestor-or-self::gloss">
                    <!-- need to align the resulting box at the top -->
                    <xsl:text>vtop</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>vbox</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            <tex:spec cat="bg"/>
            <tex:spec cat="esc"/>
            <xsl:text>hbox</xsl:text>
            <tex:spec cat="bg"/>
            <tex:cmd name="strut"/>
        </xsl:if>
    </xsl:template>
    <!--
        DoEmbeddedBrEnd
    -->
    <xsl:template name="DoEmbeddedBrEnd">
        <xsl:param name="iCountBr"/>
        <xsl:if test="$iCountBr!=0">
            <tex:spec cat="eg"/>
            <tex:spec cat="eg"/>
        </xsl:if>
    </xsl:template>
    <!--
        DoExampleHeadingWhenWrappable
    -->
    <xsl:template name="DoExampleHeadingWhenWrappable">
        <xsl:param name="bCalculateHeight" select="'N'"/>
        <tex:cmd name="parbox">
            <tex:opt>t</tex:opt>
            <tex:parm>
                <xsl:call-template name="GetWidthForExampleContent"/>
            </tex:parm>
        </tex:cmd>
        <tex:spec cat="bg"/>
        <xsl:apply-templates/>
        <tex:spec cat="eg"/>
        <xsl:if test="descendant-or-self::endnote">
            <xsl:for-each select="descendant-or-self::endnote">
                <xsl:apply-templates select=".">
                    <xsl:with-param name="sTeXFootnoteKind" select="'footnotetext'"/>
                </xsl:apply-templates>
            </xsl:for-each>
        </xsl:if>
        <xsl:choose>
            <xsl:when test="following-sibling::*[1][name()='interlinear' or name()='interlinearRef']">
                <!-- I'm not sure why exactly, but using \\ to end the heading causes the following interlinear to come out one pile per row.
                    Perhaps there is some side effect of LaTeX's \\ that causes this.
                    The following works, even though I'm not sure why.
                -->
                <xsl:variable name="sIsoCode">
                    <xsl:for-each select="following-sibling::*[1]">
                        <xsl:call-template name="GetISOCode"/>
                    </xsl:for-each>
                </xsl:variable>
                <!-- 2011.11.17               <xsl:variable name="sAdjustmentValue" select=".8"/>-->
                <xsl:choose>
                    <xsl:when test="string-length($sIsoCode) &gt; 0 ">
                        <xsl:if test="$bCalculateHeight='N'">
                            <xsl:if test="parent::example">
                                <tex:cmd name="XLingPaperAdjustHeaderInListInterlinearWithISOCodes">
                                    <tex:parm>
                                        <tex:cmd name="XLingPaperexampleheadingheight" gr="0"/>
                                    </tex:parm>
                                    <tex:parm>
                                        <tex:cmd name="XLingPaperexamplenumberheight" gr="0"/>
                                    </tex:parm>
                                </tex:cmd>
                                <!--                            <tex:cmd name="vspace*">
                                    <tex:parm>
                                    <xsl:text>-.8</xsl:text>
                                    <tex:cmd name="baselineskip" gr="0"/>
                                    </tex:parm>
                                    </tex:cmd>
                                -->
                            </xsl:if>
                            <tex:cmd name="newline" gr="0" nl2="1"/>
                        </xsl:if>
                    </xsl:when>
                    <xsl:otherwise>
                        <tex:cmd name="newline" gr="0" nl2="1"/>
                    </xsl:otherwise>
                </xsl:choose>
                <!-- 2011.11.17                   <tex:cmd name="vspace*">
                    <tex:parm>
                    <xsl:text>-</xsl:text>
                    <xsl:value-of select="$sAdjustmentValue"/>
                    <tex:cmd name="baselineskip" gr="0"/>
                    </tex:parm>
                    </tex:cmd>
                -->
                <!--  2011.11.17         <xsl:if test="string-length($sIsoCode) &gt; 0 ">
                    <tex:cmd name="vspace*">
                    <tex:parm>
                    <xsl:value-of select="$sAdjustmentValue"/>
                    <tex:cmd name="baselineskip" gr="0"/>
                    </tex:parm>
                    </tex:cmd>
                    </xsl:if>
                -->
            </xsl:when>
            <xsl:when test="parent::interlinear[parent::example][count(preceding-sibling::*)=0]">
                <xsl:if test="$bCalculateHeight='N'">
                    <xsl:variable name="sIsoCode">
                        <xsl:for-each select="following-sibling::*[1]">
                            <xsl:call-template name="GetISOCode"/>
                        </xsl:for-each>
                    </xsl:variable>
                    <xsl:if test="string-length($sIsoCode) &gt; 0">
                        <tex:cmd name="XLingPaperAdjustHeaderInListInterlinearWithISOCodes">
                            <tex:parm>
                                <tex:cmd name="XLingPaperexampleheadingheight" gr="0"/>
                            </tex:parm>
                            <tex:parm>
                                <tex:cmd name="XLingPaperexamplenumberheight" gr="0"/>
                            </tex:parm>
                        </tex:cmd>
                    </xsl:if>
                    <tex:cmd name="newline"/>
                </xsl:if>
            </xsl:when>
            <xsl:when test="parent::example">
                <!-- do nothing -->
            </xsl:when>
            <xsl:otherwise>
                <tex:cmd name="newline"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        DoExternalHyperRefBegin
    -->
    <xsl:template name="DoExternalHyperRefBegin">
        <xsl:param name="sName"/>
        <tex:spec cat="esc"/>
        <xsl:text>href</xsl:text>
        <tex:spec cat="bg"/>
        <xsl:value-of select="$sName"/>
        <tex:spec cat="eg"/>
        <tex:spec cat="bg"/>
    </xsl:template>
    <!--  
        DoExternalHyperRefEnd
    -->
    <xsl:template name="DoExternalHyperRefEnd">
        <tex:spec cat="eg"/>
    </xsl:template>
    <!--  
        DoImageFile
    -->
    <xsl:template name="DoImageFile">
        <xsl:param name="sXeTeXGraphicFile"/>
        <xsl:param name="sImgFile"/>
        <xsl:variable name="sAdjustedImageFile">
            <xsl:call-template name="CreateAdjustedImageFile">
                <xsl:with-param name="sImgFile" select="$sImgFile"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="sPatternVA" select="'vertical-adjustment='"/>
        <xsl:choose>
            <xsl:when test="ancestor::example">
                <!-- apparently we normally need to adjust the vertical position of the image when in an example -->
                <tex:cmd name="vspace*">
                    <tex:parm>
                        <xsl:variable name="default">
                            <xsl:text>-</xsl:text>
                            <tex:cmd name="baselineskip" gr="0" nl2="0"/>
                        </xsl:variable>
                        <xsl:call-template name="HandleXeLaTeXSpecialCommand">
                            <xsl:with-param name="sPattern" select="$sPatternVA"/>
                            <xsl:with-param name="default" select="$default"/>
                        </xsl:call-template>
                    </tex:parm>
                </tex:cmd>
            </xsl:when>
            <xsl:otherwise>
                <tex:cmd name="vspace*">
                    <tex:parm>
                        <xsl:call-template name="HandleXeLaTeXSpecialCommand">
                            <xsl:with-param name="sPattern" select="$sPatternVA"/>
                            <xsl:with-param name="default" select="'0pt'"/>
                        </xsl:call-template>
                    </tex:parm>
                </tex:cmd>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="contains(@XeLaTeXSpecial,$sPatternVA) and exsl:node-set($contentLayoutInfo)/figureLayout/@captionLocation='after'">
            <tex:cmd name="leavevmode"/>
        </xsl:if>
        <tex:spec cat="bg"/>
        <tex:cmd name="{$sXeTeXGraphicFile}" gr="0" nl2="0">
            <xsl:text> "</xsl:text>
            <xsl:value-of select="$sAdjustedImageFile"/>
            <xsl:text>" </xsl:text>
        </tex:cmd>
        <xsl:choose>
            <xsl:when test="contains($sXeLaTeXVersion,'2020') or exsl:node-set($lingPaper)/@useImageWidthSetToWidthOfExampleFigureOrChart='yes'">
                <xsl:choose>
                    <xsl:when test="contains(@XeLaTeXSpecial,'width=')">
                        <xsl:text>width </xsl:text>
                        <xsl:call-template name="HandleXeLaTeXSpecialCommand">
                            <xsl:with-param name="sPattern" select="'width='"/>
                            <xsl:with-param name="default" select="'4in'"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:when test="ancestor::p or ancestor::pc or ancestor::table">
                        <!-- do nothing; user will need to adjust -->
                    </xsl:when>
                    <xsl:when test="ancestor::example">
                        <xsl:text>width </xsl:text>
                        <tex:cmd name="XLingPaperImgInExampleWidth" gr="0" nl2="0"/>
                    </xsl:when>
                    <xsl:when test="ancestor::figure or ancestor::chart">
                        <xsl:text>width </xsl:text>
                        <tex:cmd name="XLingPaperImgInFigureWidth" gr="0" nl2="0"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>width </xsl:text>
                        <tex:cmd name="textwidth" gr="0" nl2="0"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <!-- I'm not sure why, but it sure appears that all graphics need to be scaled down by 75% or so;  allow the user to fine tune this-->
                <xsl:text>scaled </xsl:text>
                <xsl:variable name="default" select="750"/>
                <xsl:variable name="sPattern" select="'scaled='"/>
                <xsl:call-template name="HandleXeLaTeXSpecialCommand">
                    <xsl:with-param name="sPattern" select="$sPattern"/>
                    <xsl:with-param name="default" select="$default"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
        <tex:spec cat="eg"/>
    </xsl:template>
    <!--  
        DoInterlinearFree
    -->
    <xsl:template name="DoInterlinearFree">
        <xsl:param name="mode"/>
        <xsl:param name="bListsShareSameCode"/>
        <xsl:param name="originalContext"/>
        <xsl:if test="$bAutomaticallyWrapInterlinears!='yes' or $mode='NoTextRef'">
            <xsl:if test="preceding-sibling::*[1][name()='free' or name()='literal']">
                <tex:spec cat="esc"/>
                <tex:spec cat="esc"/>
                <xsl:text>*</xsl:text>
            </xsl:if>
        </xsl:if>
        <!-- add extra indent for when have an embedded interlinear; 
            be sure to allow for the case of when a listInterlinear begins with an interlinear -->
        <xsl:variable name="parent" select=".."/>
        <xsl:variable name="iParentPosition">
            <xsl:for-each select="../../*">
                <xsl:if test=".=$parent">
                    <xsl:value-of select="position()"/>
                </xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:variable name="sCurrentLanguage" select="@lang"/>
        <xsl:if test="contains(@XeLaTeXSpecial,'clearpage') and $bAutomaticallyWrapInterlinears='yes'">
            <tex:cmd name="clearpage" gr="0" nl2="0"/>
        </xsl:if>
        <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak') and $bAutomaticallyWrapInterlinears='yes'">
            <tex:cmd name="pagebreak" gr="0" nl2="0"/>
        </xsl:if>
        <xsl:choose>
            <xsl:when test="name()='literal'">
                <xsl:if
                    test="preceding-sibling::*[1][name()='literal'][@lang=$sCurrentLanguage] or preceding-sibling::*[1][name()='literal'][not(@lang)] or name(../..)='interlinear' or name(../..)='listInterlinear' and name(..)='interlinear' and $iParentPosition!=1">
                    <xsl:call-template name="DoInterlinearFreeIndent"/>
                </xsl:if>
                <xsl:call-template name="DoInterlinearFreeContent">
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                    <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                    <xsl:with-param name="mode" select="$mode"/>
                    <xsl:with-param name="freeLayout" select="exsl:node-set($contentLayoutInfo)/literalLayout/literalContentLayout"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if
                    test="preceding-sibling::*[1][name()='free'][@lang=$sCurrentLanguage] or preceding-sibling::*[1][name()='free'][not(@lang)] or name(../..)='interlinear' or name(../..)='listInterlinear' and name(..)='interlinear' and $iParentPosition!=1">
                    <xsl:call-template name="DoInterlinearFreeIndent"/>
                </xsl:if>
                <xsl:call-template name="DoInterlinearFreeContent">
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                    <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                    <xsl:with-param name="mode" select="$mode"/>
                    <xsl:with-param name="freeLayout" select="exsl:node-set($contentLayoutInfo)/freeLayout"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoInterlinearFreeContent
    -->
    <xsl:template name="DoInterlinearFreeContent">
        <xsl:param name="originalContext"/>
        <xsl:param name="bListsShareSameCode"/>
        <xsl:param name="mode"/>
        <xsl:param name="freeLayout"/>
        <xsl:variable name="fIsListInterlinearButNotInTable">
            <xsl:choose>
                <xsl:when test="ancestor::listInterlinear and not(ancestor::table)">
                    <xsl:choose>
                        <xsl:when test="$bAutomaticallyWrapInterlinears='yes' and following-sibling::*[1][name()='interlinearSource'] and $sInterlinearSourceStyle='AfterFree'">
                            <xsl:text>N</xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>Y</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="$originalContext and exsl:node-set($originalContext)/ancestor::listInterlinear and not(exsl:node-set($originalContext)/ancestor::table) and $sInterlinearSourceStyle='AfterFirstLine'">
                    <xsl:text>Y</xsl:text>
                </xsl:when>
                <xsl:when
                    test="$bAutomaticallyWrapInterlinears='yes' and $originalContext and exsl:node-set($originalContext)/ancestor-or-self::interlinearRef and not(exsl:node-set($originalContext)/ancestor::table) and $sInterlinearSourceStyle='AfterFirstLine'">
                    <xsl:text>Y</xsl:text>
                </xsl:when>
                <xsl:when
                    test="$bAutomaticallyWrapInterlinears='yes' and not($originalContext) and ancestor::interlinear[string-length(normalize-space(@textref)) &gt; 0 and string-length(normalize-space(@text))=0] and not(ancestor::table) and $sInterlinearSourceStyle='AfterFirstLine'">
                    <xsl:text>Y</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>N</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:if test="$fIsListInterlinearButNotInTable='Y'">
            <xsl:if test="ancestor::listInterlinear and not(ancestor::table)">
                <!-- need to compensate for the extra space after the letter -->
                <tex:cmd name="hspace*">
                    <tex:parm>
                        <tex:cmd name="XLingPaperspacewidth" gr="0" nl2="0"/>
                    </tex:parm>
                </tex:cmd>
                <xsl:if test="$bAutomaticallyWrapInterlinears='yes' and count(ancestor::interlinear) &gt; 0">
                    <xsl:choose>
                        <xsl:when test="ancestor::listInterlinear[child::*[1][name()='interlinear']]">
                            <!-- do nothing; since this interlinear is the first child, there's no need for extra indent-->
                        </xsl:when>
                        <xsl:when test="name(ancestor::*[name()='endnote' or name()='listInterlinear'][1])='endnote'">
                            <!-- is in an interlinear within an endnote (and this endnote is in a listInterlinear); do nothing -->
                        </xsl:when>
                        <xsl:otherwise>
                            <tex:cmd name="hspace*">
                                <tex:parm>
                                    <xsl:text>1em</xsl:text>
                                </tex:parm>
                            </tex:cmd>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:if>
                <xsl:call-template name="AdjustFreePositionForISOCodeInListInterlinear">
                    <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                </xsl:call-template>
                <tex:cmd name="hspace*">
                    <tex:parm>
                        <tex:cmd name="XLingPaperexamplefreeindent" gr="0"/>
                        <!--                    <xsl:text>-.3 em+</xsl:text>
                            <xsl:value-of select="$sExampleIndentBefore"/>
                            <xsl:text>-</xsl:text>
                            <xsl:value-of select="$sBlockQuoteIndent"/>
                        -->
                    </tex:parm>
                </tex:cmd>
            </xsl:if>
            <tex:cmd name="parbox">
                <tex:opt>t</tex:opt>
                <tex:parm>
                    <tex:cmd name="textwidth" gr="0" nl2="0"/>
                    <xsl:text> - </xsl:text>
                    <xsl:value-of select="$sExampleIndentBefore"/>
                    <xsl:text> - </xsl:text>
                    <xsl:value-of select="$sExampleIndentAfter"/>
                    <xsl:text> - </xsl:text>
                    <xsl:value-of select="$iNumberWidth"/>
                    <xsl:text>em - </xsl:text>
                    <xsl:call-template name="GetLetterWidth">
                        <xsl:with-param name="iLetterCount" select="count(ancestor::listInterlinear[1])"/>
                    </xsl:call-template>
                    <xsl:text>em</xsl:text>
                    <!-- not needed: <xsl:text>em - </xsl:text>
                    <tex:cmd name="XLingPaperspacewidth" gr="0" nl2="0"/>-->
                    <xsl:if test="contains($bListsShareSameCode,'N')">
                        <xsl:text> - </xsl:text>
                        <tex:cmd name="XLingPaperspacewidth" gr="0" nl2="0"/>
                        <xsl:text> - </xsl:text>
                        <tex:cmd name="XLingPaperisocodewidth" gr="0" nl2="0"/>
                    </xsl:if>
                </tex:parm>
            </tex:cmd>
            <tex:spec cat="bg"/>
        </xsl:if>
        <xsl:if test="$bAutomaticallyWrapInterlinears='yes'">
            <xsl:if test="$originalContext or $fIsListInterlinearButNotInTable='N'">
                <xsl:call-template name="AdjustFreePositionForISOCodeInListInterlinear">
                    <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                </xsl:call-template>
            </xsl:if>
            <xsl:if test="following-sibling::*[1][name()='lineGroup']">
                <tex:spec cat="bg"/>
            </xsl:if>
            <xsl:variable name="sSpaceBeforeFree" select="normalize-space(exsl:node-set($freeLayout)/@spacebefore)"/>
            <xsl:if test="string-length($sSpaceBeforeFree) &gt; 0">
                <tex:cmd name="vspace*">
                    <tex:parm>
                        <xsl:value-of select="$sSpaceBeforeFree"/>
                    </tex:parm>
                </tex:cmd>
            </xsl:if>
            <xsl:if test="$mode!='NoTextRef'">
                <!-- Need to override the XLingPaperraggedright stuff so free comes out correctly -->
                <xsl:if test="not(ancestor::listInterlinear)">
                    <tex:spec cat="bg"/>
                </xsl:if>
                <tex:cmd name="rightskip" gr="0"/>
                <xsl:text>=0pt</xsl:text>
                <tex:cmd name="pretolerance" gr="0"/>
                <xsl:text>=100</xsl:text>
            </xsl:if>
            <xsl:variable name="sHangingIndent">
                <xsl:choose>
                    <xsl:when test="string-length($sInitialGroupIndent) &gt; 0">
                        <xsl:value-of select="$sInitialGroupIndent"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:choose>
                            <xsl:when test="$mode='NoTextRef'">
                                <xsl:text>2</xsl:text>
                            </xsl:when>
                            <xsl:when test="contains($bListsShareSameCode,'N')">
                                <!-- want 1 plus 2.75 -->
                                <xsl:text>3.75</xsl:text>
                            </xsl:when>
                            <xsl:when test="ancestor::endnote and count(ancestor::interlinear[not(descendant::endnote)]) &gt; 1">
                                <xsl:text>2</xsl:text>
                            </xsl:when>
                            <xsl:when test="not(ancestor::endnote) and count(ancestor::interlinear) &gt; 1">
                                <xsl:text>2</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>1</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:text>em</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:choose>
                <xsl:when test="string-length($sAdjustIndentOfNonInitialFreeLineBy) &gt; 0">
                    <tex:cmd name="setlength">
                        <tex:parm>
                            <tex:cmd name="XLingPaperlongfreewrapindent" gr="0"/>
                        </tex:parm>
                        <tex:parm>
                            <xsl:value-of select="$sHangingIndent"/>
                            <xsl:text>-</xsl:text>
                            <tex:spec cat="esc"/>
                            <xsl:text>XLingPaperlongfreewrapindentadjust</xsl:text>
                        </tex:parm>
                    </tex:cmd>
                    <tex:spec cat="esc"/>
                    <xsl:text>hangindent</xsl:text>
                    <tex:spec cat="esc"/>
                    <xsl:text>XLingPaperlongfreewrapindent</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <tex:spec cat="esc"/>
                    <xsl:text>hangindent</xsl:text>
                    <xsl:value-of select="$sHangingIndent"/>
                </xsl:otherwise>
            </xsl:choose>
            <tex:cmd name="relax" gr="0" nl2="1"/>
            <tex:spec cat="esc"/>
            <xsl:text>hangafter1</xsl:text>
            <tex:cmd name="relax" gr="0" nl2="1"/>
            <xsl:choose>
                <xsl:when test="$mode='NoTextRef'">
                    <tex:cmd name="hspace*">
                        <tex:parm>
                            <xsl:choose>
                                <xsl:when test="string-length($sInitialGroupIndent) &gt; 0">
                                    <xsl:value-of select="$sInitialGroupIndent"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:variable name="sThisName" select="name()"/>
                                    <xsl:choose>
                                        <xsl:when test="../preceding-sibling::*[1][name()=$sThisName] or count(ancestor::interlinear) &gt; 1">
                                            <xsl:text>1.65</xsl:text>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <xsl:text>1</xsl:text>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                    <xsl:text>em</xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </tex:parm>
                    </tex:cmd>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:if test="not(ancestor::endnote) and count(ancestor::interlinear) &gt; 1 or ancestor::endnote and count(ancestor::interlinear[not(descendant::endnote)]) &gt; 1">
                        <tex:cmd name="hspace*">
                            <tex:parm>1em</tex:parm>
                        </tex:cmd>
                    </xsl:if>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:call-template name="DoLiteralLabel"/>
        <xsl:choose>
            <xsl:when test="@lang">
                <xsl:call-template name="HandleFreeLanguageFontInfo">
                    <xsl:with-param name="freeLayout" select="$freeLayout"/>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <!--                <tex:cmd name="raggedright" gr="0" nl2="0"/>-->
                <tex:group>
                    <xsl:call-template name="HandleFreeNoLanguageFontInfo">
                        <xsl:with-param name="originalContext" select="$originalContext"/>
                        <xsl:with-param name="freeLayout" select="$freeLayout"/>
                    </xsl:call-template>
                </tex:group>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="$mode!='NoTextRef'">
            <xsl:if
                test="$sInterlinearSourceStyle='AfterFree' and not(following-sibling::free or following-sibling::literal) and not(following-sibling::interlinear[descendant::free or descendant::literal])">
                <xsl:if test="ancestor::example  or ancestor::listInterlinear or ancestor::interlinear[@textref]">
                    <xsl:call-template name="OutputInterlinearTextReference">
                        <xsl:with-param name="sRef" select="ancestor::interlinear[@textref]/@textref"/>
                        <xsl:with-param name="sSource" select="../interlinearSource"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:if>
        </xsl:if>
        <xsl:if test="$sInterlinearSourceStyle='UnderFree' and not(following-sibling::free or following-sibling::literal)">
            <xsl:choose>
                <xsl:when test="../interlinearSource">
                    <xsl:if test="ancestor::example or ancestor::listInterlinear">
                        <tex:spec cat="esc"/>
                        <tex:spec cat="esc" nl2="1"/>
                        <tex:group>
                            <xsl:call-template name="OutputInterlinearTextReference">
                                <xsl:with-param name="sRef" select="../@textref"/>
                                <xsl:with-param name="sSource" select="../interlinearSource"/>
                            </xsl:call-template>
                        </tex:group>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="$mode!='NoTextRef' and ancestor::interlinear-text">
                    <tex:spec cat="esc"/>
                    <tex:spec cat="esc" nl2="1"/>
                    <tex:group>
                        <xsl:call-template name="OutputInterlinearTextReference">
                            <xsl:with-param name="sRef" select="../@textref"/>
                        </xsl:call-template>
                    </tex:group>
                </xsl:when>
            </xsl:choose>
        </xsl:if>
        <xsl:if test="$fIsListInterlinearButNotInTable='Y'">
            <tex:spec cat="eg"/>
        </xsl:if>
        <xsl:if test="$bAutomaticallyWrapInterlinears='yes' and $mode!='NoTextRef' and not(ancestor::td)">
            <xsl:if test="count(following-sibling::*) =0 and not(../following-sibling::interlinear and ancestor::example) or following-sibling::*[1][name()!='interlinear' and name()!='lineGroup']">
                <!--                <tex:cmd name="par"/> \par makes the hanging indent work, but causes bad page breaks and does not work in tables, etc.-->
                <xsl:choose>
                    <xsl:when test="following-sibling::*[1][name()='free' or name()='literal']">
                        <xsl:if test="$mode!='NoTextRef' and not(ancestor::listInterlinear) and $sInterlinearSourceStyle='AfterFirstLine'">
                            <!-- finish overriding XLingPaperraggedright stuff -->
                            <tex:spec cat="eg"/>
                        </xsl:if>
                        <!-- we want to keep this free with the following free or literal; using this will still wrap a long line -->
                        <tex:spec cat="esc"/>
                        <tex:spec cat="esc"/>
                        <xsl:text>*</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:if test="not(endnote) or not(contains(@XeLaTeXSpecial,'fix-free-literal-footnote-placement'))">
                            <!-- endnotes get put on next page if we try and use \vskip and it is near the bottom of the page -->
                            <!-- any vertical operation will cause the hanging indent to work: it ends the paragraph: TeX Book, p. 86 -->
                            <tex:cmd name="vskip" gr="0"/>
                            <xsl:text>0pt</xsl:text>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:if>
        </xsl:if>
        <xsl:if test="$bAutomaticallyWrapInterlinears='yes' and following-sibling::*[1][name()='lineGroup']">
            <tex:spec cat="eg"/>
        </xsl:if>
        <xsl:call-template name="DoFootnoteTextAfterFree">
            <xsl:with-param name="originalContext" select="$originalContext"/>
        </xsl:call-template>
        <!-- If we had to do a parbox, we need to now handle any footnotes in any interlinearSource -->
        <xsl:if test="$fIsListInterlinearButNotInTable='Y'">
            <xsl:if test="$mode!='NoTextRef'">
                <xsl:if
                    test="$sInterlinearSourceStyle='AfterFree' and not(following-sibling::free or following-sibling::literal) and not(following-sibling::interlinear[descendant::free or descendant::literal])">
                    <xsl:if test="ancestor::example  or ancestor::listInterlinear or ancestor::interlinear[@textref]">
                        <xsl:for-each select="../interlinearSource">
                            <xsl:call-template name="DoFootnoteTextAfterFree">
                                <!--                                <xsl:with-param name="originalContext" select="."/>-->
                            </xsl:call-template>
                        </xsl:for-each>
                    </xsl:if>
                </xsl:if>
            </xsl:if>
            <xsl:if test="$sInterlinearSourceStyle='UnderFree' and not(following-sibling::free or following-sibling::literal) and ../interlinearSource">
                <xsl:if test="ancestor::example or ancestor::listInterlinear">
                    <xsl:for-each select="../interlinearSource">
                        <xsl:call-template name="DoFootnoteTextAfterFree">
                            <xsl:with-param name="originalContext" select="."/>
                        </xsl:call-template>
                    </xsl:for-each>
                </xsl:if>
            </xsl:if>
        </xsl:if>
        <xsl:if test="$bAutomaticallyWrapInterlinears='yes'">
            <xsl:if test="$mode!='NoTextRef' and not(ancestor::listInterlinear)">
                <xsl:choose>
                    <xsl:when test="not(ancestor::td) and count(following-sibling::*) =0 and not(../following-sibling::interlinear and ancestor::example) or following-sibling::*[1][name()!='interlinear' and name()!='lineGroup']">
                        <xsl:choose>
                            <xsl:when test="following-sibling::*[1][name()='free' or name()='literal'] and $sInterlinearSourceStyle='AfterFirstLine'">
                                <!-- do nothing because already done above -->
                            </xsl:when>
                            <xsl:otherwise>
                                <!-- finish overriding XLingPaperraggedright stuff -->
                                <tex:spec cat="eg"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- finish overriding XLingPaperraggedright stuff -->
                        <tex:spec cat="eg"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:if>
            <xsl:choose>
                <xsl:when test="following-sibling::*[1][name()='interlinear'] ">
                    <xsl:call-template name="DoInterlinearFreeEndOfParagraph">
                        <xsl:with-param name="mode" select="$mode"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:when test="following-sibling::*[1][name()='lineGroup']">
                    <tex:cmd name="vspace">
                        <tex:parm>
                            <tex:cmd name="baselineskip"/>
                        </tex:parm>
                    </tex:cmd>
                    <tex:cmd name="newline"/>
                </xsl:when>
                <xsl:when test="../following-sibling::*[1][name()='interlinear']">
                    <xsl:choose>
                        <xsl:when test="count(ancestor::interlinear) &gt; 1">
                            <xsl:call-template name="DoInterlinearFreeEndOfParagraph">
                                <xsl:with-param name="mode" select="$mode"/>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:when test="ancestor::listInterlinear and count(ancestor::interlinear) &gt; 0">
                            <xsl:call-template name="DoInterlinearFreeEndOfParagraph">
                                <xsl:with-param name="mode" select="$mode"/>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise/>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="ancestor::td">
                    <tex:spec cat="esc"/>
                    <tex:spec cat="esc"/>
                    <tex:spec cat="lsb"/>
                    <xsl:call-template name="GetCurrentPointSize"/>
                    <tex:spec cat="rsb"/>
                </xsl:when>
                <xsl:otherwise/>
            </xsl:choose>
        </xsl:if>
        <xsl:variable name="sSpaceAfterFree" select="normalize-space(exsl:node-set($freeLayout)/@spaceafter)"/>
        <xsl:if test="string-length($sSpaceAfterFree) &gt; 0">
            <tex:cmd name="vspace">
                <tex:parm>
                    <xsl:value-of select="$sSpaceAfterFree"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
    </xsl:template>
    <!--  
        DoInterlinearFreeIndent
    -->
    <xsl:template name="DoInterlinearFreeIndent">
        <xsl:choose>
            <xsl:when test="$bAutomaticallyWrapInterlinears='yes' and ../preceding-sibling::*[1][name()='free' or name()='literal']">
                <!-- do nothing -->
            </xsl:when>
            <xsl:when test="$bAutomaticallyWrapInterlinears='yes' and count(ancestor::interlinear) &gt; 1">
                <!-- do nothing -->
            </xsl:when>
            <xsl:when test="$bAutomaticallyWrapInterlinears='yes' and ancestor::listInterlinear and count(ancestor::interlinear) &gt; 0">
                <!-- do nothing -->
            </xsl:when>
            <xsl:otherwise>
                <tex:cmd name="hspace*">
                    <tex:parm>
                        <xsl:text>0.1in</xsl:text>
                    </tex:parm>
                </tex:cmd>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        AdjustFreePositionForISOCodeInListInterlinear
    -->
    <xsl:template name="AdjustFreePositionForISOCodeInListInterlinear">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:if test="contains($bListsShareSameCode,'N')">
            <!-- need to compensate for the extra space of the ISO code -->
            <xsl:variable name="sIsoCode">
                <xsl:choose>
                    <xsl:when test="parent::listInterlinear">
                        <xsl:for-each select="parent::listInterlinear">
                            <xsl:call-template name="GetISOCode"/>
                        </xsl:for-each>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- assume is from an interlinearRef -->
                        <xsl:for-each select="parent::interlinear">
                            <xsl:call-template name="GetISOCode"/>
                        </xsl:for-each>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:choose>
                <xsl:when test="string-length($sIsoCode) &gt; 3">
                    <tex:cmd name="setlength">
                        <tex:parm>
                            <tex:cmd name="XLingPaperisocodewidth" gr="0"/>
                        </tex:parm>
                        <tex:parm>
                            <xsl:text>2.75em</xsl:text>
                        </tex:parm>
                    </tex:cmd>
                </xsl:when>
                <xsl:otherwise>
                    <tex:cmd name="settowidth">
                        <tex:parm>
                            <tex:cmd name="XLingPaperisocodewidth" gr="0"/>
                        </tex:parm>
                        <tex:parm>
                            <xsl:call-template name="OutputISOCodeInExample">
                                <xsl:with-param name="bOutputBreak" select="'N'"/>
                                <xsl:with-param name="sIsoCode" select="$sIsoCode"/>
                            </xsl:call-template>
                        </tex:parm>
                    </tex:cmd>
                </xsl:otherwise>
            </xsl:choose>
            <tex:cmd name="hspace*">
                <tex:parm>
                    <tex:cmd name="XLingPaperisocodewidth" gr="0" nl2="0"/>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="hspace*">
                <tex:parm>
                    <tex:cmd name="XLingPaperspacewidth" gr="0" nl2="0"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
    </xsl:template>
    <!--  
        DoInterlinearFreeEndOfParagraph
    -->
    <xsl:template name="DoInterlinearFreeEndOfParagraph">
        <xsl:param name="mode"/>
        <xsl:choose>
            <xsl:when test="$mode='NoTextRef'">
                <tex:spec cat="esc"/>
                <tex:spec cat="esc"/>
            </xsl:when>
            <xsl:otherwise>
                <tex:cmd name="vspace">
                    <tex:parm>
                        <tex:cmd name="baselineskip"/>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="newline" gr="0"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoInterlinearLine
    -->
    <xsl:template name="DoInterlinearLine">
        <xsl:param name="mode"/>
        <xsl:param name="bListsShareSameCode"/>
        <xsl:param name="originalContext"/>
        <xsl:if test="contains($bListsShareSameCode,'N') and count(preceding-sibling::line) &gt; 0">
            <tex:spec cat="align"/>
        </xsl:if>
        <xsl:choose>
            <xsl:when test="wrd">
                <xsl:for-each select="wrd">
                    <xsl:if test="position() &gt; 1">
                        <tex:spec cat="align"/>
                    </xsl:if>
                    <xsl:call-template name="DoWrd">
                        <xsl:with-param name="originalContext" select="$originalContext"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="bFlip">
                    <xsl:choose>
                        <xsl:when test="id(parent::lineGroup/line[1]/langData[1]/@lang)/@rtl='yes'">Y</xsl:when>
                        <xsl:otherwise>N</xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <!--<xsl:if test="$bFlip='Y'">
                    <xsl:attribute name="text-align">right</xsl:attribute>
                </xsl:if>-->
                <xsl:variable name="lang">
                    <xsl:call-template name="GetLangInNonWrdLine"/>
                </xsl:variable>
                <xsl:variable name="sOrientedContents">
                    <xsl:call-template name="GetOrientedContents">
                        <xsl:with-param name="bFlip" select="$bFlip"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:call-template name="OutputInterlinearLineAsTableCells">
                    <xsl:with-param name="sList" select="$sOrientedContents"/>
                    <xsl:with-param name="lang" select="$lang"/>
                    <xsl:with-param name="sAlign">
                        <xsl:choose>
                            <xsl:when test="$bFlip='Y'">right</xsl:when>
                            <xsl:otherwise>start</xsl:otherwise>
                        </xsl:choose>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="$mode!='NoTextRef'">
            <xsl:if test="count(preceding-sibling::line) = 0">
                <xsl:if test="$sInterlinearSourceStyle='AfterFirstLine'">
                    <xsl:if test="string-length(normalize-space(../../@textref)) &gt; 0 or ../../interlinearSource">
                        <tex:spec cat="align"/>
                        <xsl:call-template name="DoDebugExamples"/>
                        <xsl:call-template name="OutputInterlinearTextReference">
                            <xsl:with-param name="sRef" select="../../@textref"/>
                            <xsl:with-param name="sSource" select="../../interlinearSource"/>
                        </xsl:call-template>
                    </xsl:if>
                </xsl:if>
            </xsl:if>
        </xsl:if>
        <tex:spec cat="esc"/>
        <tex:spec cat="esc"/>
        <xsl:text>*
</xsl:text>
    </xsl:template>
    <!--  
        DoInterlinearLineGroup
    -->
    <xsl:template name="DoInterlinearLineGroup">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:param name="mode"/>
        <xsl:param name="originalContext"/>
        <xsl:choose>
            <xsl:when test="parent::interlinear[preceding-sibling::*]">
                <xsl:variable name="previous" select="parent::interlinear/preceding-sibling::*[1]"/>
                <xsl:choose>
                    <xsl:when test="$previous=exampleHeading">
                        <!--                    <tex:cmd name="par" gr="0" nl2="1"/>-->
                        <tex:spec cat="esc"/>
                        <tex:spec cat="esc"/>
                        <xsl:text>*
</xsl:text>
                    </xsl:when>
                    <xsl:when
                        test="name($previous)='free' or name($previous)='literal' or name($previous)='lineGroup' or name($previous)='interlinear' and exsl:node-set($previous)[parent::interlinear or parent::listInterlinear]">
                        <tex:spec cat="esc"/>
                        <tex:spec cat="esc"/>
                        <xsl:if test="count(../../lineGroup[last()]/line) &gt; 1 or count(line) &gt; 1">
                            <tex:spec cat="lsb"/>
                            <!--                        <xsl:text>3pt</xsl:text>-->
                            <xsl:choose>
                                <xsl:when test="string-length($sSpaceBetweenGroups) &gt; 0">
                                    <xsl:value-of select="$sSpaceBetweenGroups"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <tex:cmd name="baselineskip"/>
                                </xsl:otherwise>
                            </xsl:choose>
                            <tex:spec cat="rsb"/>
                        </xsl:if>
                        <tex:cmd name="hspace*" nl1="1">
                            <tex:parm>
                                <xsl:choose>
                                    <xsl:when test="string-length($sIndentOfNonInitialGroup) &gt; 0">
                                        <xsl:value-of select="$sIndentOfNonInitialGroup"/>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:text>.1in</xsl:text>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </tex:parm>
                        </tex:cmd>
                    </xsl:when>
                    <xsl:when test="preceding-sibling::*[1][name()='lineGroup' or name()='free' or name()='literal']">
                        <xsl:call-template name="HandleImmediatelyPrecedingLineGroupOrFree"/>
                    </xsl:when>
                    <xsl:otherwise> </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="preceding-sibling::*[1][name()='lineGroup' or name()='free' or name()='literal']">
                <xsl:call-template name="HandleImmediatelyPrecedingLineGroupOrFree"/>
            </xsl:when>
            <xsl:otherwise/>
        </xsl:choose>
        <tex:env name="tabular" nlb1="0" nlb2="0">
            <tex:opt>t</tex:opt>
            <tex:parm>
                <xsl:call-template name="DoInterlinearTabularMainPattern">
                    <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                </xsl:call-template>
            </tex:parm>
            <xsl:if test="contains($bListsShareSameCode,'N')">
                <xsl:variable name="sListIsoCode">
                    <xsl:call-template name="GetISOCode">
                        <xsl:with-param name="originalContext" select="$originalContext"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:if test="string-length($sListIsoCode) &gt; 3">
                    <xsl:variable name="iRowCount" select="count(line)"/>
                    <tex:cmd name="multirow">
                        <tex:parm>
                            <!-- 2011.11.16 was just output $iRowCount -->
                            <xsl:choose>
                                <xsl:when test="parent::listInterlinear">
                                    <xsl:text>2</xsl:text>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:value-of select="$iRowCount"/>
                                </xsl:otherwise>
                            </xsl:choose>
                        </tex:parm>
                        <tex:parm>
                            <xsl:text>2.75em</xsl:text>
                        </tex:parm>
                        <tex:opt>
                            <xsl:text>.88</xsl:text>
                            <tex:cmd name="baselineskip" gr="0"/>
                        </tex:opt>
                    </tex:cmd>
                    <tex:spec cat="bg"/>
                </xsl:if>
                <xsl:call-template name="OutputListLevelISOCode">
                    <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                    <xsl:with-param name="sIsoCode" select="$sListIsoCode"/>
                    <xsl:with-param name="bCloseOffMultirow" select="'Y'"/>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
                <xsl:if test="string-length($sListIsoCode) &gt; 3">
                    <tex:cat spec="eg"/>
                </xsl:if>
            </xsl:if>
            <xsl:call-template name="ApplyTemplatesPerTextRefMode">
                <xsl:with-param name="mode" select="$mode"/>
                <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                <xsl:with-param name="originalContext" select="$originalContext"/>
            </xsl:call-template>
        </tex:env>
        <xsl:choose>
            <!--            <xsl:when test="ancestor::table">
                <!-\- do nothing because the \\* causes LaTeX to give an error message "Missing \endgroup inserted" at the end of the table -\->
                </xsl:when>
            -->
            <xsl:when test="following-sibling::*[1][name()='lineGroup']">
                <!-- do nothing; otherwise we get an error -->
            </xsl:when>
            <xsl:when test="following-sibling::*[1][name()='free' or name()='literal'] or parent::interlinear/following-sibling::*[1][name()='free' or name()='literal']">
                <xsl:choose>
                    <xsl:when test="following-sibling::*[1][name()='free']">
                        <xsl:call-template name="CreateBreakAfter">
                            <xsl:with-param name="example" select="ancestor::example[1]"/>
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                            <xsl:with-param name="sSpaceBeforeFree">
                                <xsl:variable name="sSpaceBeforeFree" select="normalize-space(exsl:node-set($contentLayoutInfo)/freeLayout/@spacebefore)"/>
                                <xsl:if test="string-length($sSpaceBeforeFree) &gt; 0">
                                    <xsl:value-of select="$sSpaceBeforeFree"/>
                                </xsl:if>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="CreateBreakAfter">
                            <xsl:with-param name="example" select="ancestor::example[1]"/>
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                            <xsl:with-param name="sSpaceBeforeFree">
                                <xsl:variable name="sSpaceBeforeFree" select="normalize-space(exsl:node-set($contentLayoutInfo)/literalLayout/@spacebefore)"/>
                                <xsl:if test="string-length($sSpaceBeforeFree) &gt; 0">
                                    <xsl:value-of select="$sSpaceBeforeFree"/>
                                </xsl:if>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <!--                <tex:cmd name="par" gr="0" nl2="1"/>-->
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="DoFootnoteTextAtEndOfInLineGroup">
            <xsl:with-param name="originalContext" select="$originalContext"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        DoInterlinearTabularMainPattern
    -->
    <xsl:template name="DoInterlinearTabularMainPattern">
        <xsl:param name="bListsShareSameCode"/>
        <!-- 2011.11.16        <xsl:if test="contains($bListsShareSameCode,'N')">
            <xsl:variable name="sIsoCode">
                <xsl:for-each select="parent::listInterlinear">
                    <xsl:call-template name="GetISOCode"/>
                </xsl:for-each>
            </xsl:variable>
            <xsl:if test="string-length($sIsoCode) &gt; 3">
                <xsl:text>p</xsl:text>
                <tex:spec cat="bg"/>
                <xsl:text>2.75em</xsl:text>
                <tex:spec cat="eg"/>
            </xsl:if>
        </xsl:if>
-->
        <xsl:text>*</xsl:text>
        <tex:spec cat="bg"/>
        <xsl:variable name="iColCount">
            <xsl:call-template name="GetMaxColumnCountForLineGroup">
                <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$sInterlinearSourceStyle='AfterFirstLine'">
                <xsl:choose>
                    <xsl:when test="string-length(normalize-space(ancestor-or-self::*/@textref)) &gt; 0 or following-sibling::interlinearSource">
                        <!-- we have an extra column so include it -->
                        <xsl:value-of select="$iColCount + 1"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$iColCount"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$iColCount"/>
            </xsl:otherwise>
        </xsl:choose>
        <tex:spec cat="eg"/>
        <tex:spec cat="bg"/>
        <xsl:call-template name="CreateColumnSpecDefaultAtExpression"/>
        <xsl:choose>
            <xsl:when test="id(line[1]/@lang)/@rtl='yes'">r</xsl:when>
            <xsl:when test="id(line[1]/wrd[1]/@lang)/@rtl='yes'">r</xsl:when>
            <xsl:when test="id(line[1]/wrd/langData[1]/@lang)/@rtl='yes'">r</xsl:when>
            <xsl:otherwise>l</xsl:otherwise>
        </xsl:choose>
        <xsl:text>@</xsl:text>
        <tex:spec cat="bg"/>
        <tex:spec cat="esc"/>
        <tex:spec cat="space"/>
        <tex:spec cat="eg"/>
        <tex:spec cat="eg"/>
        <xsl:text>l</xsl:text>
    </xsl:template>
    <!--
        DoInterlinearTextReferenceLinkBegin
    -->
    <xsl:template name="DoInterlinearTextReferenceLinkBegin">
        <xsl:param name="sRef" select="@textref"/>
        <xsl:variable name="referencedInterlinear" select="key('InterlinearReferenceID',$sRef)"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($referencedInterlinear)[ancestor::referencedInterlinearTexts]">
                <xsl:call-template name="DoExternalHyperRefBegin">
                    <xsl:with-param name="sName">
                        <xsl:value-of select="exsl:node-set($referencedInterlinear)/ancestor::referencedInterlinearText/@url"/>
                        <xsl:text>.pdf#</xsl:text>
                        <xsl:value-of select="$sRef"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="DoInternalHyperlinkBegin">
                    <xsl:with-param name="sName" select="$sRef"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        DoInterlinearWrappedWithSourceAfterFirstLine
    -->
    <xsl:template name="DoInterlinearWrappedWithSourceAfterFirstLine">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:param name="bHasExampleHeading"/>
        <xsl:param name="originalContext"/>
        <tex:cmd name="settowidth">
            <tex:parm>
                <tex:spec cat="esc"/>
                <xsl:value-of select="$sTeXInterlinearSourceWidth"/>
            </tex:parm>
            <tex:parm>
                <xsl:call-template name="OutputInterlinearTextReferenceContent">
                    <xsl:with-param name="sSource" select="interlinearSource"/>
                    <xsl:with-param name="sRef" select="normalize-space(@textref)"/>
                    <xsl:with-param name="bContentOnly" select="'Y'"/>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="parbox">
            <tex:opt>
                <xsl:text>t</xsl:text>
            </tex:opt>
            <tex:parm>
                <xsl:call-template name="GetWidthForExampleContent">
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
                <xsl:text>-</xsl:text>
                <tex:spec cat="esc"/>
                <xsl:value-of select="$sTeXInterlinearSourceWidth"/>
                <xsl:text>-</xsl:text>
                <tex:spec cat="esc"/>
                <xsl:value-of select="$sTeXInterlinearSourceGapWidth"/>
            </tex:parm>
            <tex:parm>
                <tex:spec cat="esc"/>
                <xsl:text>&#x20;</xsl:text>
                <tex:cmd name="hspace">
                    <tex:parm>
                        <xsl:text>-</xsl:text>
                        <tex:cmd name="XLingPaperspacewidth"/>
                    </tex:parm>
                </tex:cmd>
                <xsl:choose>
                    <xsl:when test="name()='listInterlinear'">
                        <xsl:apply-templates select="*[name()!='interlinearSource']">
                            <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                        </xsl:apply-templates>
                    </xsl:when>
                    <xsl:when test="ancestor::interlinear-text">
                        <xsl:apply-templates>
                            <xsl:with-param name="bHasExampleHeading" select="$bHasExampleHeading"/>
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                        </xsl:apply-templates>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="OutputInterlinear">
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="OutputInterlinearTextReference">
            <xsl:with-param name="sRef" select="@textref"/>
            <xsl:with-param name="sSource" select="interlinearSource"/>
        </xsl:call-template>
        <xsl:call-template name="DoFootnoteTextWithinWrappableWrd"/>
    </xsl:template>
    <!--
        DoInternalHyperlinkBegin
    -->
    <xsl:template name="DoInternalHyperlinkBegin">
        <xsl:param name="sName"/>
        <tex:spec cat="esc"/>
        <xsl:text>hyperlink</xsl:text>
        <tex:spec cat="bg"/>
        <xsl:value-of select="translate($sName,$sIDcharsToMap, $sIDcharsMapped)"/>
        <tex:spec cat="eg"/>
        <tex:spec cat="bg"/>
    </xsl:template>
    <!--  
        DoInternalHyperlinkEnd
    -->
    <xsl:template name="DoInternalHyperlinkEnd">
        <tex:spec cat="eg"/>
    </xsl:template>
    <!--
        DoInternalTargetBegin
    -->
    <xsl:template name="DoInternalTargetBegin">
        <xsl:param name="sName"/>
        <xsl:param name="fDoRaisebox" select="'Y'"/>
        <xsl:if test="$fDoRaisebox='Y'">
            <tex:spec cat="esc"/>
            <xsl:text>raisebox</xsl:text>
            <tex:spec cat="bg"/>
            <tex:spec cat="esc"/>
            <xsl:text>baselineskip</xsl:text>
            <tex:spec cat="eg"/>
            <tex:spec cat="lsb"/>
            <xsl:text>0pt</xsl:text>
            <tex:spec cat="rsb"/>
            <tex:spec cat="bg"/>
        </xsl:if>
        <!-- in some contexts, \hypertarget needs to be \protected; we do it always since it is not easy to determine such contexts-->
        <tex:cmd name="protect" gr="0"/>
        <tex:spec cat="esc"/>
        <xsl:text>hypertarget</xsl:text>
        <tex:spec cat="bg"/>
        <xsl:value-of select="translate($sName,$sIDcharsToMap, $sIDcharsMapped)"/>
        <tex:spec cat="eg"/>
        <tex:spec cat="bg"/>
        <tex:spec cat="eg"/>
        <xsl:if test="$fDoRaisebox='Y'">
            <tex:spec cat="eg"/>
        </xsl:if>
    </xsl:template>
    <!--  
        DoInternalTargetEnd
    -->
    <xsl:template name="DoInternalTargetEnd">
        <!--        <tex:spec cat="eg"/>-->
    </xsl:template>
    <!--  
        DoIthCellInNonWrdInterlinearLineAsWrappable
    -->
    <xsl:template name="DoIthCellInNonWrdInterlinearLineAsWrappable">
        <xsl:param name="sList"/>
        <xsl:param name="lang"/>
        <xsl:param name="iPositionToUse"/>
        <xsl:param name="iCurrentPosition"/>
        <xsl:param name="iMaxColumns"/>
        <xsl:variable name="sNewList" select="concat(normalize-space($sList),' ')"/>
        <xsl:variable name="sFirst" select="substring-before($sNewList,' ')"/>
        <xsl:choose>
            <xsl:when test="$iCurrentPosition = $iPositionToUse">
                <xsl:call-template name="OutputInterlinearLineTableCellContent">
                    <xsl:with-param name="lang" select="$lang"/>
                    <xsl:with-param name="sFirst" select="$sFirst"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="sRest" select="substring-after($sNewList,' ')"/>
                <xsl:if test="$sRest or $iCurrentPosition &lt; $iMaxColumns">
                    <xsl:call-template name="DoIthCellInNonWrdInterlinearLineAsWrappable">
                        <xsl:with-param name="sList" select="$sRest"/>
                        <xsl:with-param name="lang" select="$lang"/>
                        <xsl:with-param name="iPositionToUse" select="$iPositionToUse"/>
                        <xsl:with-param name="iCurrentPosition" select="$iCurrentPosition + 1"/>
                        <xsl:with-param name="iMaxColumns" select="$iMaxColumns"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoListInterlinearEmbeddedTabular
    -->
    <xsl:template name="DoListInterlinearEmbeddedTabular">
        <tex:spec cat="bg"/>
        <xsl:apply-templates select="child::node()[name()!='interlinearSource']"/>
        <tex:spec cat="eg"/>
    </xsl:template>
    <!--  
        DoListLetter
    -->
    <xsl:template name="DoListLetter">
        <xsl:param name="sLetterWidth"/>
        <xsl:call-template name="OutputLetter"/>
    </xsl:template>
    <!--  
        DoNestedTypes
    -->
    <xsl:template name="DoNestedTypes">
        <xsl:param name="sList"/>
        <xsl:param name="originalContext"/>
        <xsl:variable name="sNewList" select="concat(normalize-space($sList),' ')"/>
        <xsl:variable name="sFirst" select="substring-before($sNewList,' ')"/>
        <xsl:variable name="sRest" select="substring-after($sNewList,' ')"/>
        <xsl:if test="string-length($sFirst) &gt; 0">
            <xsl:call-template name="DoType">
                <xsl:with-param name="type" select="$sFirst"/>
                <xsl:with-param name="bDoingNestedTypes" select="'y'"/>
                <xsl:with-param name="originalContext" select="$originalContext"/>
            </xsl:call-template>
            <xsl:if test="$sRest">
                <xsl:call-template name="DoNestedTypes">
                    <xsl:with-param name="sList" select="$sRest"/>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        DoNestedTypesBracketsOnly
    -->
    <xsl:template name="DoNestedTypesBracketsOnly">
        <xsl:param name="sList"/>
        <xsl:variable name="sNewList" select="concat(normalize-space($sList),' ')"/>
        <xsl:variable name="sFirst" select="substring-before($sNewList,' ')"/>
        <xsl:variable name="sRest" select="substring-after($sNewList,' ')"/>
        <xsl:if test="string-length($sFirst) &gt; 0">
            <xsl:call-template name="DoTypeBracketsOnly">
                <xsl:with-param name="type" select="$sFirst"/>
            </xsl:call-template>
            <xsl:if test="$sRest">
                <xsl:call-template name="DoNestedTypesBracketsOnly">
                    <xsl:with-param name="sList" select="$sRest"/>
                </xsl:call-template>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        DoNestedTypesEnd
    -->
    <xsl:template name="DoNestedTypesEnd">
        <xsl:param name="sList"/>
        <xsl:param name="originalContext"/>
        <xsl:variable name="sNewList" select="concat(normalize-space($sList),' ')"/>
        <xsl:variable name="sFirst" select="substring-before($sNewList,' ')"/>
        <xsl:variable name="sRest" select="substring-after($sNewList,' ')"/>
        <xsl:if test="string-length($sFirst) &gt; 0">
            <xsl:call-template name="DoTypeEnd">
                <xsl:with-param name="type" select="$sFirst"/>
                <xsl:with-param name="originalContext" select="$originalContext"/>
            </xsl:call-template>
            <xsl:if test="$sRest">
                <xsl:call-template name="DoNestedTypesEnd">
                    <xsl:with-param name="sList" select="$sRest"/>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        DoNonWrdInterlinearLineAsWrappable
    -->
    <xsl:template name="DoNonWrdInterlinearLineAsWrappable">
        <xsl:param name="sList"/>
        <xsl:param name="lang"/>
        <xsl:param name="bFlip"/>
        <xsl:param name="iPosition"/>
        <xsl:param name="iMaxColumns"/>
        <xsl:variable name="sNewList" select="concat(normalize-space($sList),' ')"/>
        <xsl:variable name="sFirst" select="substring-before($sNewList,' ')"/>
        <xsl:variable name="sRest" select="substring-after($sNewList,' ')"/>
        <xsl:variable name="iLineCountInLineGroup" select="count(../line)"/>
        <tex:cmd name="hbox">
            <tex:parm>
                <!--       cannot use an environment because it inserts a newline which causes alignment issues
                    <tex:env name="tabular" nl1="0">-->
                <tex:spec cat="esc"/>
                <xsl:text>begin</xsl:text>
                <tex:spec cat="bg"/>
                <xsl:text>tabular</xsl:text>
                <tex:spec cat="eg"/>
                <tex:opt>t</tex:opt>
                <tex:parm>
                    <xsl:text>@</xsl:text>
                    <tex:spec cat="bg"/>
                    <tex:spec cat="eg"/>
                    <xsl:text>l@</xsl:text>
                    <tex:spec cat="bg"/>
                    <tex:spec cat="eg"/>
                </tex:parm>
                <xsl:call-template name="OutputInterlinearLineTableCellContent">
                    <xsl:with-param name="lang" select="$lang"/>
                    <xsl:with-param name="sFirst" select="$sFirst"/>
                </xsl:call-template>
                <tex:spec cat="esc"/>
                <tex:spec cat="esc"/>
                <xsl:for-each select="following-sibling::line">
                    <xsl:variable name="langOfNewLine">
                        <xsl:call-template name="GetLangInNonWrdLine"/>
                    </xsl:variable>
                    <xsl:variable name="sOrientedContents">
                        <xsl:call-template name="GetOrientedContents">
                            <xsl:with-param name="bFlip" select="$bFlip"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:call-template name="DoIthCellInNonWrdInterlinearLineAsWrappable">
                        <xsl:with-param name="sList" select="$sOrientedContents"/>
                        <xsl:with-param name="lang" select="$langOfNewLine"/>
                        <xsl:with-param name="iPositionToUse" select="$iPosition"/>
                        <xsl:with-param name="iCurrentPosition" select="1"/>
                        <xsl:with-param name="iMaxColumns" select="$iMaxColumns"/>
                    </xsl:call-template>
                    <tex:spec cat="esc"/>
                    <tex:spec cat="esc"/>
                </xsl:for-each>
                <xsl:if test="$iLineCountInLineGroup &gt; 1 or not($sRest or $iPosition &lt; $iMaxColumns)">
                    <!-- need extra space between aligned units when there are two or more lines or if it's the last one -->
                    <tex:spec cat="lsb"/>
                    <xsl:call-template name="GetCurrentPointSize"/>
                    <tex:spec cat="rsb"/>
                </xsl:if>
                <tex:spec cat="esc"/>
                <xsl:text>end</xsl:text>
                <tex:spec cat="bg"/>
                <xsl:text>tabular</xsl:text>
                <tex:spec cat="eg"/>
                <!--                            </tex:env>-->
            </tex:parm>
        </tex:cmd>
        <xsl:if test="$sRest or $iPosition &lt; $iMaxColumns">
            <xsl:choose>
                <xsl:when test="$iLineCountInLineGroup &gt; 1">
                    <tex:cmd name="XLingPaperintspace"/>
                </xsl:when>
                <xsl:otherwise>
                    <!--  if there is only one line we might as well just use spaces -->
                    <xsl:text>&#x20;</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="DoNonWrdInterlinearLineAsWrappable">
                <xsl:with-param name="sList" select="$sRest"/>
                <xsl:with-param name="lang" select="$lang"/>
                <xsl:with-param name="bFlip" select="$bFlip"/>
                <xsl:with-param name="iPosition" select="$iPosition + 1"/>
                <xsl:with-param name="iMaxColumns" select="$iMaxColumns"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--  
        DoNotBreakHere
    -->
    <xsl:template name="DoNotBreakHere">
        <tex:spec cat="esc"/>
        <xsl:text>penalty10000</xsl:text>
    </xsl:template>
    <!--  
        DoRowBackgroundColor
    -->
    <xsl:template name="DoRowBackgroundColor">
        <xsl:param name="bMarkAsRow" select="'Y'"/>
        <xsl:call-template name="OutputBackgroundColor">
            <xsl:with-param name="bIsARow" select="$bMarkAsRow"/>
        </xsl:call-template>
        <xsl:for-each select="key('TypeID',@type)">
            <!-- note: this does not handle nested types -->
            <xsl:call-template name="OutputBackgroundColor">
                <xsl:with-param name="bIsARow" select="$bMarkAsRow"/>
            </xsl:call-template>
        </xsl:for-each>
    </xsl:template>
    <!--  
        DoRowSpanAdjust
    -->
    <xsl:template name="DoRowSpanAdjust">
        <xsl:param name="sList"/>
        <xsl:variable name="sRest" select="substring-after($sList,'Y')"/>
        <tex:spec cat="align"/>
        <xsl:if test="contains($sRest ,'Y')">
            <xsl:call-template name="DoRowSpanAdjust">
                <xsl:with-param name="sList" select="$sRest"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--  
        DoType
    -->
    <xsl:template name="DoType">
        <xsl:param name="type" select="@type"/>
        <xsl:param name="bDoingNestedTypes" select="'n'"/>
        <xsl:param name="originalContext"/>
        <xsl:for-each select="key('TypeID',$type)">
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="."/>
                <xsl:with-param name="originalContext" select="$originalContext"/>
            </xsl:call-template>
            <xsl:call-template name="DoNestedTypes">
                <xsl:with-param name="sList" select="@types"/>
                <xsl:with-param name="originalContext" select="$originalContext"/>
            </xsl:call-template>
            <xsl:if test="$bDoingNestedTypes!='y'">
                <xsl:value-of select="."/>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>
    <!--  
        DoTypeBracketsOnly
    -->
    <xsl:template name="DoTypeBracketsOnly">
        <xsl:param name="type" select="@type"/>
        <xsl:for-each select="key('TypeID',$type)">
            <xsl:call-template name="OutputFontAttributesBracketsOnly">
                <xsl:with-param name="language" select="."/>
            </xsl:call-template>
            <xsl:call-template name="DoNestedTypesBracketsOnly">
                <xsl:with-param name="sList" select="@types"/>
            </xsl:call-template>
        </xsl:for-each>
    </xsl:template>
    <!--  
        DoTypeEnd
    -->
    <xsl:template name="DoTypeEnd">
        <xsl:param name="type" select="@type"/>
        <xsl:param name="originalContext"/>
        <xsl:for-each select="key('TypeID',$type)">
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="."/>
                <xsl:with-param name="originalContext" select="$originalContext"/>
            </xsl:call-template>
            <xsl:call-template name="DoNestedTypesEnd">
                <xsl:with-param name="sList" select="@types"/>
                <xsl:with-param name="originalContext" select="$originalContext"/>
            </xsl:call-template>
        </xsl:for-each>
    </xsl:template>
    <!--  
        DoWrapableInterlinearLineGroup
    -->
    <xsl:template name="DoWrapableInterlinearLineGroup">
        <xsl:param name="mode"/>
        <xsl:param name="bHasExampleHeading"/>
        <xsl:param name="bListsShareSameCode"/>
        <xsl:param name="originalContext"/>
        <xsl:if test="(count(ancestor::interlinear) + count(ancestor::listInterlinear)) &gt; 1">
            <xsl:if test="$mode='NoTextRef' or  ../preceding-sibling::*[1][name()!='free' and name()!='literal']">
                <tex:cmd name="vspace">
                    <tex:parm>
                        <tex:cmd name="baselineskip"/>
                    </tex:parm>
                </tex:cmd>
            </xsl:if>
        </xsl:if>
        <xsl:variable name="sLeftIndent">
            <xsl:choose>
                <xsl:when test="string-length($sInitialGroupIndent) &gt; 0">
                    <xsl:value-of select="$sInitialGroupIndent"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:choose>
                        <xsl:when test="../preceding-sibling::*[1][name()='free' or name()='literal'] or count(ancestor::interlinear) &gt; 1">
                            <xsl:text>1.65</xsl:text>
                        </xsl:when>
                        <xsl:when test="preceding-sibling::*[1][name()='lineGroup']">
                            <xsl:text>2</xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>1</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                    <xsl:text>em</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:if test="$mode='NoTextRef'">
            <tex:cmd name="raggedright" gr="0" nl2="0"/>
            <tex:cmd name="leavevmode" gr="0" nl2="0"/>
            <tex:cmd name="hspace*" nl2="0">
                <tex:parm>
                    <xsl:value-of select="$sLeftIndent"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:if test="id(line[1]/@lang)/@rtl='yes' or id(line[1]/wrd/langData[1]/@lang)/@rtl='yes' or id(line[1]/wrd[1]/@lang)/@rtl='yes'">
            <tex:cmd name="beginR" gr="0"/>
        </xsl:if>
        <tex:cmd name="XLingPaperraggedright" gr="0"/>
        <xsl:if test="preceding-sibling::lineGroup or following-sibling::*[1][name()='lineGroup']">
            <tex:spec cat="bg"/>
        </xsl:if>
        <xsl:choose>
            <xsl:when test="string-length($sIndentOfNonInitialGroup) &gt; 0">
                <!-- \setlength{\XLingPapertempdim}{1em+0pt} -->
                <tex:cmd name="setlength">
                    <tex:parm>
                        <tex:spec cat="esc"/>
                        <xsl:text>XLingPapertempdim</xsl:text>
                    </tex:parm>
                    <tex:parm>
                        <xsl:if test="ancestor::interlinear-text">
                            <xsl:value-of select="$sLeftIndent"/>
                            <xsl:text>+</xsl:text>
                        </xsl:if>
                        <xsl:value-of select="$sIndentOfNonInitialGroup"/>
                    </tex:parm>
                </tex:cmd>
                <tex:spec cat="esc"/>
                <xsl:text>hangindent</xsl:text>
                <tex:spec cat="esc"/>
                <xsl:text>XLingPapertempdim</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <tex:spec cat="esc"/>
                <xsl:text>hangindent</xsl:text>
                <xsl:choose>
                    <xsl:when test="$mode='NoTextRef' and preceding-sibling::*[1][name()='lineGroup']">
                        <xsl:text>0</xsl:text>
                    </xsl:when>
                    <xsl:when test="$mode='NoTextRef'">
                        <xsl:text>2</xsl:text>
                    </xsl:when>
                    <xsl:when test="contains($bListsShareSameCode,'N')">
                        <!-- want 1 plus 2.75 -->
                        <xsl:text>3.75</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>1</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:text>em</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <tex:cmd name="relax" gr="0" nl2="1"/>
        <tex:spec cat="esc"/>
        <xsl:text>hangafter</xsl:text>
        <xsl:choose>
            <xsl:when
                test="name(..)='listInterlinear' and ../preceding-sibling::*[1][name()='exampleHeading'] and exsl:node-set($lingPaper)/@showiso639-3codeininterlinear='yes' and contains($bListsShareSameCode,'N')">
                <!-- if we use 2, then longer interlinears are aligned incorrectly -->
                <xsl:text>1</xsl:text>
            </xsl:when>
            <xsl:when
                test="name(..)='listInterlinear' and ../preceding-sibling::*[1][name()='exampleHeading'] and ancestor-or-self::example/@showiso639-3codes='yes' and contains($bListsShareSameCode,'N')">
                <!-- if we use 2, then longer interlinears are aligned incorrectly -->
                <xsl:text>1</xsl:text>
            </xsl:when>
            <xsl:when
                test="name(..)='listInterlinear' and ../preceding-sibling::*[1][name()='exampleHeading'] and $originalContext and exsl:node-set($originalContext)/ancestor-or-self::example/@showiso639-3codes='yes' and contains($bListsShareSameCode,'N')">
                <!-- if we use 2, then longer interlinears are aligned incorrectly -->
                <xsl:text>1</xsl:text>
            </xsl:when>
            <xsl:when test="../preceding-sibling::*[1][name()='exampleHeading'] or preceding-sibling::*[1][name()='exampleHeading'] or $bHasExampleHeading='Y'">
                <xsl:text>2</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>1</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <tex:cmd name="relax" gr="0" nl2="1"/>
        <xsl:if
            test="exsl:node-set($lingPaper)/@showiso639-3codeininterlinear='yes' and contains($bListsShareSameCode,'N') or ancestor-or-self::example/@showiso639-3codes='yes' and contains($bListsShareSameCode,'N') or $originalContext and exsl:node-set($originalContext)/ancestor-or-self::example/@showiso639-3codes='yes' and contains($bListsShareSameCode,'N')">
            <xsl:variable name="sListIsoCode">
                <xsl:call-template name="GetISOCode">
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:if test="$sListIsoCode!=''">
                <xsl:choose>
                    <xsl:when test="string-length($sListIsoCode) &gt; 3">
                        <tex:cmd name="parbox">
                            <tex:opt>
                                <xsl:text>t</xsl:text>
                            </tex:opt>
                            <tex:parm>
                                <xsl:text>2.75em</xsl:text>
                            </tex:parm>
                            <tex:parm>
                                <tex:cmd name="small">
                                    <tex:parm>
                                        <xsl:text>[</xsl:text>
                                        <xsl:value-of select="$sListIsoCode"/>
                                        <xsl:text>]</xsl:text>
                                    </tex:parm>
                                </tex:cmd>
                            </tex:parm>
                        </tex:cmd>
                    </xsl:when>
                    <xsl:otherwise>
                        <tex:cmd name="hbox">
                            <tex:parm>
                                <tex:cmd name="small">
                                    <tex:parm>
                                        <xsl:text>[</xsl:text>
                                        <xsl:value-of select="$sListIsoCode"/>
                                        <xsl:text>]</xsl:text>
                                    </tex:parm>
                                </tex:cmd>
                            </tex:parm>
                        </tex:cmd>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:if>
            <xsl:text>&#x20;</xsl:text>
        </xsl:if>
        <xsl:variable name="iColCount">
            <xsl:call-template name="GetMaxColumnCountForLineGroup">
                <xsl:with-param name="bListsShareSameCode" select="'Y'"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:if test="$sInterlinearSourceStyle='AfterFirstLine'">
            <xsl:if test="parent::interlinear[string-length(@textref) &gt; 0] or following-sibling::interlinearSource">
                <xsl:variable name="nearestRelevantElement" select="ancestor::*[name()='endnote' or name()='td'][1]"/>
                <xsl:if test="not($bAutomaticallyWrapInterlinears='yes') or not(name($nearestRelevantElement)='td')">
                    <!-- When a reference comes after the first line, without this a wrapped line will get justified and will be right-aligned. -->
                    <tex:cmd name="raggedright" gr="0" nl2="1"/>
                </xsl:if>
            </xsl:if>
        </xsl:if>
        <xsl:choose>
            <xsl:when test="line/wrd">
                <xsl:variable name="bRtl">
                    <xsl:choose>
                        <xsl:when test="id(line[1]/wrd/langData[1]/@lang)/@rtl='yes'">Y</xsl:when>
                        <xsl:otherwise>N</xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:choose>
                    <xsl:when test="$bRtl='Y'">
                        <xsl:for-each select="line[1]/wrd">
                            <xsl:sort select="position()" data-type="number" order="descending"/>
                            <xsl:call-template name="BoxUpWrdsInAllLinesInLineGroup">
                                <xsl:with-param name="originalContext" select="$originalContext"/>
                            </xsl:call-template>
                        </xsl:for-each>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:for-each select="line[count(wrd)=$iColCount][1]/wrd">
                            <xsl:call-template name="BoxUpWrdsInAllLinesInLineGroup">
                                <xsl:with-param name="originalContext" select="$originalContext"/>
                            </xsl:call-template>
                        </xsl:for-each>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:if test="$originalContext">
                    <xsl:for-each select="line">
                        <xsl:call-template name="DoFootnoteTextWithinWrappableWrd">
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                        </xsl:call-template>
                    </xsl:for-each>
                </xsl:if>
            </xsl:when>
            <xsl:otherwise>
                <!-- uses langData or gloss with #PCDATA -->
                <xsl:variable name="bFlip">
                    <xsl:choose>
                        <xsl:when test="id(line[1]/langData[1]/@lang)/@rtl='yes'">Y</xsl:when>
                        <xsl:otherwise>N</xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <!--                <xsl:if test="$bFlip='Y'">
                    <xsl:attribute name="text-align">right</xsl:attribute>
                    </xsl:if>
                -->
                <xsl:for-each select="line[1]">
                    <xsl:variable name="lang">
                        <xsl:call-template name="GetLangInNonWrdLine"/>
                    </xsl:variable>
                    <xsl:variable name="sOrientedContents">
                        <xsl:call-template name="GetOrientedContents">
                            <xsl:with-param name="bFlip" select="$bFlip"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:call-template name="DoNonWrdInterlinearLineAsWrappable">
                        <xsl:with-param name="sList" select="$sOrientedContents"/>
                        <xsl:with-param name="lang" select="$lang"/>
                        <xsl:with-param name="bFlip" select="$bFlip"/>
                        <xsl:with-param name="iPosition" select="1"/>
                        <xsl:with-param name="iMaxColumns" select="$iColCount"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:choose>
            <xsl:when test="$mode!='NoTextRef' and following-sibling::*[1][name()='interlinear' or name()='lineGroup']">
                <xsl:if test="preceding-sibling::lineGroup or following-sibling::*[1][name()='lineGroup']">
                    <tex:spec cat="eg"/>
                </xsl:if>
                <tex:cmd name="newline" nl2="1"/>
            </xsl:when>
            <xsl:when test="ancestor::endnote and ancestor::td">
                <xsl:variable name="iEndnotePosition" select="count(ancestor::*[name()!='endnote' and ancestor::endnote])"/>
                <xsl:variable name="iTdPosition" select="count(ancestor::*[name()!='td' and ancestor::td])"/>
                <xsl:choose>
                    <xsl:when test="$iEndnotePosition &lt; $iTdPosition">
                        <tex:spec cat="esc"/>
                        <tex:spec cat="esc"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <tex:spec cat="esc"/>
                        <tex:spec cat="esc"/>
                        <tex:spec cat="lsb"/>
                        <xsl:text>-</xsl:text>
                        <!--                        <xsl:call-template name="GetCurrentPointSize"/>-->
                        <xsl:call-template name="GetSpaceBetweenGroups"/>
                        <tex:spec cat="rsb"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="ancestor::endnote">
                <tex:spec cat="esc"/>
                <tex:spec cat="esc"/>
            </xsl:when>
            <xsl:when test="ancestor::td">
                <tex:spec cat="esc"/>
                <tex:spec cat="esc"/>
                <tex:spec cat="lsb"/>
                <xsl:text>-</xsl:text>
                <!--                <xsl:call-template name="GetCurrentPointSize"/>-->
                <xsl:call-template name="GetSpaceBetweenGroups"/>
                <tex:spec cat="rsb"/>
            </xsl:when>
            <xsl:when test="../preceding-sibling::lineGroup and ../following-sibling::*[1][name()='interlinear'] and ../preceding-sibling::*[1][name()='interlinear' or name()='lineGroup']">
                <xsl:if test="preceding-sibling::lineGroup or following-sibling::*[1][name()='lineGroup']">
                    <tex:spec cat="eg"/>
                </xsl:if>
                <tex:cmd name="newline" nl2="1"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="preceding-sibling::lineGroup or following-sibling::*[1][name()='lineGroup']">
                    <tex:spec cat="eg"/>
                </xsl:if>
                <xsl:if test="id(line[1]/@lang)/@rtl='yes' or id(line[1]/wrd/langData[1]/@lang)/@rtl='yes' or id(line[1]/wrd[1]/@lang)/@rtl='yes'">
                    <tex:cmd name="endR" gr="0"/>
                </xsl:if>
                <tex:cmd name="par" nl2="1"/>
            </xsl:otherwise>
        </xsl:choose>
        <!--<tex:cmd name="par" nl2="1"/>-->
        <xsl:if test="not(ancestor::listInterlinear and preceding-sibling::*[1][name()='lineGroup'] and following-sibling::*[1][name()='free' or name()='literal'])">
            <!-- Not sure why, but when have the above scenario, get the free translation on top of the last line of the lineGroup -->
            <xsl:choose>
                <xsl:when test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespaceexamples!='yes' and not(parent::td)">
                    <!-- do nothing -->
                </xsl:when>
                <xsl:when test="following-sibling::*[1][name()='lineGroup'] and $mode='NoTextRef'">
                    <!-- do nothing; we want the normal spacing -->
                </xsl:when>
                <xsl:when
                    test="ancestor::interlinear and preceding-sibling::*[1][name()='lineGroup'] and not($mode) and not($originalContext) and following-sibling::*[1][name()='free'] and $bHasExampleHeading!='Y'">
                    <!-- do nothing -->
                </xsl:when>
                <xsl:otherwise>
                    <tex:cmd name="vspace*">
                        <tex:parm>
                            <xsl:text>-</xsl:text>
                            <!--                            <xsl:call-template name="GetCurrentPointSize"/>-->
                            <xsl:call-template name="GetSpaceBetweenGroups"/>
                        </tex:parm>
                    </tex:cmd>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <!-- not sure why following is needed, but Lachixo example xPronombres.12a needs it -->
        <xsl:if
            test="ancestor::listInterlinear and count(../following-sibling::*)=0 and count(../preceding-sibling::interlinear) &gt; 0 and following-sibling::*[1][name()='free' or name()='literal']">
            <tex:cmd name="vspace*">
                <tex:parm>
                    <xsl:text>-</xsl:text>
                    <tex:cmd name="baselineskip"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
    </xsl:template>
    <!--  
        DoWrd
    -->
    <xsl:template name="DoWrd">
        <xsl:param name="originalContext"/>
        <xsl:choose>
            <xsl:when test="@lang">
                <!-- using cmd and parm outputs an unwanted space when there is an initial object - SIGH - does not do any better.... need to try spec nil -->
                <xsl:call-template name="OutputFontAttributes">
                    <xsl:with-param name="language" select="key('LanguageID',@lang)"/>
                    <xsl:with-param name="originalContext" select="."/>
                </xsl:call-template>
                <xsl:apply-templates>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:apply-templates>
                <xsl:call-template name="OutputFontAttributesEnd">
                    <xsl:with-param name="language" select="key('LanguageID',@lang)"/>
                    <xsl:with-param name="originalContext" select="."/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:apply-templates>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        ForceItalicsInContentsTitle
    -->
    <xsl:template name="ForceItalicsInContentsTitle">
        <tex:spec cat="esc"/>
        <xsl:text>textit</xsl:text>
        <tex:spec cat="bg"/>
        <xsl:value-of select="."/>
        <tex:spec cat="eg"/>
    </xsl:template>
    <!--  
        FormatTDContent
    -->
    <xsl:template name="FormatTDContent">
        <xsl:param name="bInARowSpan"/>
        <xsl:param name="fIncludeEndnotes" select="'Y'"/>
        <xsl:for-each select="..">
            <!-- have to do the row's type processing here -->
            <xsl:call-template name="DoType"/>
        </xsl:for-each>
        <xsl:call-template name="DoType"/>
        <!--      <xsl:call-template name="OutputBackgroundColor"/>-->
        <xsl:variable name="iCountBr" select="count(child::br)"/>
        <xsl:call-template name="DoEmbeddedBrBegin">
            <xsl:with-param name="iCountBr" select="$iCountBr"/>
        </xsl:call-template>
        <xsl:choose>
            <xsl:when test="$fIncludeEndnotes='N'">
                <xsl:apply-templates select="text() | child::node()[name()!='endnote']">
                    <xsl:with-param name="fIgnoreMediaObjectInsertion" select="'Y'"/>
                </xsl:apply-templates>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="DoEmbeddedBrEnd">
            <xsl:with-param name="iCountBr" select="$iCountBr"/>
        </xsl:call-template>
        <xsl:if test="not(contains($bInARowSpan,'Y'))">
            <xsl:call-template name="HandleFootnotesInTableHeader"/>
        </xsl:if>
        <xsl:call-template name="DoTypeEnd"/>
        <xsl:for-each select="..">
            <!-- have to do the row's type processing here -->
            <xsl:call-template name="DoTypeEnd"/>
        </xsl:for-each>
    </xsl:template>
    <!--  
        FormatTHContent
    -->
    <xsl:template name="FormatTHContent">
        <xsl:param name="fIncludeEndnotes" select="'Y'"/>
        <!-- default formatting is bold -->
        <tex:spec cat="esc"/>
        <xsl:text>textbf</xsl:text>
        <tex:spec cat="bg"/>
        <xsl:for-each select="..">
            <!-- have to do the row's type processing here -->
            <xsl:call-template name="DoType"/>
        </xsl:for-each>
        <xsl:call-template name="DoType"/>
        <!--      <xsl:call-template name="OutputBackgroundColor"/>-->
        <xsl:variable name="iCountBr" select="count(child::br)"/>
        <xsl:call-template name="DoEmbeddedBrBegin">
            <xsl:with-param name="iCountBr" select="$iCountBr"/>
        </xsl:call-template>
        <xsl:choose>
            <xsl:when test="$fIncludeEndnotes='N'">
                <xsl:apply-templates select="text() | *[name()!='endnote']"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates/>
            </xsl:otherwise>
        </xsl:choose>
        <!--        <xsl:if test="following-sibling::th | following-sibling::td | following-sibling::col">
            <xsl:text>&#xa0;</xsl:text>  Not sure why we have this 2010.07.10; it's not there for td's
            </xsl:if>
        -->
        <xsl:call-template name="DoEmbeddedBrEnd">
            <xsl:with-param name="iCountBr" select="$iCountBr"/>
        </xsl:call-template>
        <xsl:call-template name="DoTypeEnd"/>
        <xsl:for-each select="..">
            <!-- have to do the row's type processing here -->
            <xsl:call-template name="DoTypeEnd"/>
        </xsl:for-each>
        <tex:spec cat="eg"/>
    </xsl:template>
    <!--  
        GetColorCodeToUse
    -->
    <xsl:template name="GetColorCodeToUse">
        <xsl:param name="sFontColor"/>
        <xsl:choose>
            <xsl:when test="string-length($sFontColor) &gt; 2">
                <xsl:call-template name="GetColorDecimalCodesFromHexCode">
                    <xsl:with-param name="sColorHexCode">
                        <xsl:call-template name="GetColorHexCode">
                            <xsl:with-param name="sColor" select="$sFontColor"/>
                        </xsl:call-template>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <!-- use black -->
                <xsl:text>0,0,0</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
      GetColorDecimalCodeFromHexCode
   -->
    <xsl:template name="GetColorDecimalCodeFromHexCode">
        <xsl:param name="sColorHexCode"/>
        <xsl:variable name="s16" select="substring($sColorHexCode,1,1)"/>
        <xsl:variable name="s1" select="substring($sColorHexCode,2,1)"/>
        <xsl:variable name="i16">
            <xsl:call-template name="ConvertHexToDecimal">
                <xsl:with-param name="sValue" select="$s16"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="i1">
            <xsl:call-template name="ConvertHexToDecimal">
                <xsl:with-param name="sValue" select="$s1"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:value-of select="($i16 * 16 + $i1) div 255"/>
    </xsl:template>
    <!--  
      GetColorDecimalCodesFromHexCode
   -->
    <xsl:template name="GetColorDecimalCodesFromHexCode">
        <xsl:param name="sColorHexCode"/>
        <!-- the color package wants the RGB values in a decimal triplet, each value is to be between 0 and 1 -->
        <xsl:call-template name="GetColorDecimalCodeFromHexCode">
            <xsl:with-param name="sColorHexCode" select="substring($sColorHexCode,1,2)"/>
        </xsl:call-template>
        <xsl:text>,</xsl:text>
        <xsl:call-template name="GetColorDecimalCodeFromHexCode">
            <xsl:with-param name="sColorHexCode" select="substring($sColorHexCode,3,2)"/>
        </xsl:call-template>
        <xsl:text>,</xsl:text>
        <xsl:call-template name="GetColorDecimalCodeFromHexCode">
            <xsl:with-param name="sColorHexCode" select="substring($sColorHexCode,5,2)"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
      GetColorHexCode
   -->
    <xsl:template name="GetColorHexCode">
        <xsl:param name="sColor"/>
        <xsl:choose>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='aliceblue'">F0F8FF</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='antiquewhite'">FAEBD7</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='aqua'">00FFFF</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='aquamarine'">7FFFD4</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='azure'">F0FFFF</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='beige'">F5F5DC</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='bisque'">FFE4C4</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='black'">000000</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='blanchedalmond'">FFEBCD</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='blue'">0000FF</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='blueviolet'">8A2BE2</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='brown'">A52A2A</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='burlywood'">DEB887</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='cadetblue'">5F9EA0</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='chartreuse'">7FFF00</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='chocolate'">D2691E</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='coral'">FF7F50</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='cornflowerblue'">6495ED</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='cornsilk'">FFF8DC</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='crimson'">DC143C</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='cyan'">00FFFF</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='darkblue'">00008B</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='darkcyan'">008B8B</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='darkgoldenrod'">B8860B</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='darkgray'">A9A9A9</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='darkgreen'">006400</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='darkkhaki'">BDB76B</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='darkmagenta'">8B008B</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='darkolivegreen'">556B2F</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='darkorange'">FF8C00</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='darkorchid'">9932CC</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='darkred'">8B0000</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='darksalmon'">E9967A</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='darkseagreen'">8FBC8F</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='darkslateblue'">483D8B</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='darkslategray'">2F4F4F</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='darkturquoise'">00CED1</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='darkviolet'">9400D3</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='deeppink'">FF1493</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='deepskyblue'">00BFFF</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='dimgray'">696969</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='dodgerblue'">1E90FF</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='firebrick'">B22222</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='floralwhite'">FFFAF0</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='forestgreen'">228B22</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='fuchsia'">FF00FF</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='gainsboro'">DCDCDC</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='ghostwhite'">F8F8FF</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='gold'">FFD700</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='goldenrod'">DAA520</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='gray'">808080</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='green'">008000</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='greenyellow'">ADFF2F</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='honeydew'">F0FFF0</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='hotpink'">FF69B4</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='indianred '">CD5C5C</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='indigo '">4B0082</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='ivory'">FFFFF0</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='khaki'">F0E68C</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='lavender'">E6E6FA</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='lavenderblush'">FFF0F5</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='lawngreen'">7CFC00</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='lemonchiffon'">FFFACD</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='lightblue'">ADD8E6</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='lightcoral'">F08080</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='lightcyan'">E0FFFF</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='lightgoldenrodyellow'">FAFAD2</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='lightgrey'">D3D3D3</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='lightgreen'">90EE90</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='lightpink'">FFB6C1</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='lightsalmon'">FFA07A</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='lightseagreen'">20B2AA</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='lightskyblue'">87CEFA</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='lightslategray'">778899</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='lightsteelblue'">B0C4DE</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='lightyellow'">FFFFE0</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='lime'">00FF00</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='limegreen'">32CD32</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='linen'">FAF0E6</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='magenta'">FF00FF</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='maroon'">800000</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='mediumaquamarine'">66CDAA</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='mediumblue'">0000CD</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='mediumorchid'">BA55D3</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='mediumpurple'">9370D8</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='mediumseagreen'">3CB371</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='mediumslateblue'">7B68EE</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='mediumspringgreen'">00FA9A</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='mediumturquoise'">48D1CC</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='mediumvioletred'">C71585</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='midnightblue'">191970</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='mintcream'">F5FFFA</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='mistyrose'">FFE4E1</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='moccasin'">FFE4B5</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='navajowhite'">FFDEAD</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='navy'">000080</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='oldlace'">FDF5E6</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='olive'">808000</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='olivedrab'">6B8E23</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='orange'">FFA500</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='orangered'">FF4500</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='orchid'">DA70D6</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='palegoldenrod'">EEE8AA</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='palegreen'">98FB98</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='paleturquoise'">AFEEEE</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='palevioletred'">D87093</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='papayawhip'">FFEFD5</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='peachpuff'">FFDAB9</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='peru'">CD853F</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='pink'">FFC0CB</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='plum'">DDA0DD</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='powderblue'">B0E0E6</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='purple'">800080</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='red'">FF0000</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='rosybrown'">BC8F8F</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='royalblue'">4169E1</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='saddlebrown'">8B4513</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='salmon'">FA8072</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='sandybrown'">F4A460</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='seagreen'">2E8B57</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='seashell'">FFF5EE</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='sienna'">A0522D</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='silver'">C0C0C0</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='skyblue'">87CEEB</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='slateblue'">6A5ACD</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='slategray'">708090</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='snow'">FFFAFA</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='springgreen'">00FF7F</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='steelblue'">4682B4</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='tan'">D2B48C</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='teal'">008080</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='thistle'">D8BFD8</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='tomato'">FF6347</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='turquoise'">40E0D0</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='violet'">EE82EE</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='wheat'">F5DEB3</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='white'">FFFFFF</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='whitesmoke'">F5F5F5</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='yellow'">FFFF00</xsl:when>
            <xsl:when test="translate($sColor,$sUppercaseAtoZ, $sLowercaseAtoZ)='yellowgreen'">9ACD32</xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="string-length($sColor) = 7">
                        <!-- skip the initial # -->
                        <xsl:value-of select="substring(translate($sColor,'abcdef','ABCDEF'), 2)"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- somehow it came through as an invalid number; use black -->
                        <xsl:text>000000</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetColumnLetter
    -->
    <xsl:template name="GetColumnLetter">
        <xsl:param name="iPos" select="position()"/>
        <xsl:choose>
            <xsl:when test="$iPos=1">a</xsl:when>
            <xsl:when test="$iPos=2">b</xsl:when>
            <xsl:when test="$iPos=3">c</xsl:when>
            <xsl:when test="$iPos=4">d</xsl:when>
            <xsl:when test="$iPos=5">e</xsl:when>
            <xsl:when test="$iPos=6">f</xsl:when>
            <xsl:when test="$iPos=7">g</xsl:when>
            <xsl:when test="$iPos=8">h</xsl:when>
            <xsl:when test="$iPos=9">i</xsl:when>
            <xsl:when test="$iPos=10">j</xsl:when>
            <xsl:when test="$iPos=11">k</xsl:when>
            <xsl:when test="$iPos=12">l</xsl:when>
            <xsl:when test="$iPos=13">m</xsl:when>
            <xsl:when test="$iPos=14">n</xsl:when>
            <xsl:when test="$iPos=15">o</xsl:when>
            <xsl:when test="$iPos=16">p</xsl:when>
            <xsl:when test="$iPos=17">q</xsl:when>
            <xsl:when test="$iPos=18">r</xsl:when>
            <xsl:when test="$iPos=19">s</xsl:when>
            <xsl:when test="$iPos=20">t</xsl:when>
            <xsl:when test="$iPos=21">u</xsl:when>
            <xsl:when test="$iPos=22">v</xsl:when>
            <xsl:when test="$iPos=23">w</xsl:when>
            <xsl:when test="$iPos=24">x</xsl:when>
            <xsl:when test="$iPos=25">y</xsl:when>
            <xsl:when test="$iPos=26">z</xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetColumnWidthBasedOnPercentage
    -->
    <xsl:template name="GetColumnWidthBasedOnPercentage">
        <xsl:param name="iPercentage"/>
        <xsl:variable name="iTableWidth">
            <xsl:choose>
                <xsl:when test="$iPercentage&gt;=100">
                    <!-- do nothing; leave it -->
                </xsl:when>
                <xsl:otherwise>
                    <xsl:choose>
                        <xsl:when test="ancestor::example and ancestor::landscape">
                            <xsl:value-of select="($iTableExampleInLandscapeWidth*$iPercentage) div 100"/>
                        </xsl:when>
                        <xsl:when test="ancestor::example">
                            <xsl:value-of select="($iTableExampleWidth*$iPercentage) div 100"/>
                        </xsl:when>
                        <xsl:when test="ancestor::landscape">
                            <xsl:value-of select="($iTableInLandscapeWidth*$iPercentage) div 100"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="($iTableInPortraitWidth*$iPercentage) div 100"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:value-of select="$iTableWidth"/>
        <xsl:text>pt</xsl:text>
        <!--<xsl:call-template name="GetUnitOfMeasure">
            <xsl:with-param name="sValue" select="$sPageWidth"/>
        </xsl:call-template>-->
    </xsl:template>
    <!--  
        GetCurrentPointSize
    -->
    <xsl:template name="GetCurrentPointSize">
        <xsl:param name="bAddGlue" select="'N'"/>
        <xsl:choose>
            <xsl:when test="ancestor::endnote">
                <xsl:value-of select="$sFootnotePointSize"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sBasicPointSize"/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:text>pt</xsl:text>
        <xsl:if test="$bAddGlue='Y'">
            <xsl:text> plus 2pt minus 1pt</xsl:text>
        </xsl:if>
    </xsl:template>
    <!--  
        GetDynamicListItemName
    -->
    <xsl:template name="GetDynamicListItemName">
        <xsl:text>XLingPaperdynamiclistitem</xsl:text>
        <xsl:choose>
            <xsl:when test="count(ancestor::ol)=0">
                <xsl:text>one</xsl:text>
            </xsl:when>
            <xsl:when test="count(ancestor::ol)=1">
                <xsl:text>two</xsl:text>
            </xsl:when>
            <xsl:when test="count(ancestor::ol)=2">
                <xsl:text>three</xsl:text>
            </xsl:when>
            <xsl:when test="count(ancestor::ol)=3">
                <xsl:text>four</xsl:text>
            </xsl:when>
            <xsl:when test="count(ancestor::ol)=4">
                <xsl:text>five</xsl:text>
            </xsl:when>
            <xsl:when test="count(ancestor::ol)=5">
                <xsl:text>six</xsl:text>
            </xsl:when>
            <xsl:when test="count(ancestor::ol)=6">
                <xsl:text>seven</xsl:text>
            </xsl:when>
            <xsl:when test="count(ancestor::ol)=7">
                <xsl:text>eight</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>nine</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:text>width</xsl:text>
    </xsl:template>
    <!--  
        GetFramedTypeBackgroundColorName
    -->
    <xsl:template name="GetFramedTypeBackgroundColorName">
        <xsl:param name="sId"/>
        <xsl:variable name="sPosition" select="count(key('FramedTypeID',$sId)/preceding-sibling::*)"/>
        <xsl:text>FTColor</xsl:text>
        <xsl:value-of select="translate($sPosition,'0123456789','ABCDEFGHIJ')"/>
    </xsl:template>
    <!--  
        GetHyphenationLanguage
    -->
    <xsl:template name="GetHyphenationLanguage">
        <xsl:choose>
            <xsl:when test="$documentLang='am'">amharic</xsl:when>
            <xsl:when test="$documentLang='amh'">amharic</xsl:when>
            <xsl:when test="$documentLang='ar'">arabic</xsl:when>
            <xsl:when test="$documentLang='ara'">arabic</xsl:when>
            <xsl:when test="$documentLang='ast'">asturian</xsl:when>
            <xsl:when test="$documentLang='ben'">bengali</xsl:when>
            <xsl:when test="$documentLang='bg'">bulgarian</xsl:when>
            <xsl:when test="$documentLang='bn'">bengali</xsl:when>
            <xsl:when test="$documentLang='br'">breton</xsl:when>
            <xsl:when test="$documentLang='bre'">breton</xsl:when>
            <xsl:when test="$documentLang='bul'">bulgarian</xsl:when>
            <xsl:when test="$documentLang='ca'">catalan</xsl:when>
            <xsl:when test="$documentLang='cat'">catalan</xsl:when>
            <xsl:when test="$documentLang='ces'">czech</xsl:when>
            <xsl:when test="$documentLang='cop'">coptic</xsl:when>
            <xsl:when test="$documentLang='cs'">czech</xsl:when>
            <xsl:when test="$documentLang='cy'">welsh</xsl:when>
            <xsl:when test="$documentLang='cym'">welsh</xsl:when>
            <xsl:when test="$documentLang='da'">danish</xsl:when>
            <xsl:when test="$documentLang='dan'">danish</xsl:when>
            <xsl:when test="$documentLang='de'">german</xsl:when>
            <xsl:when test="$documentLang='deu'">german</xsl:when>
            <xsl:when test="$documentLang='dsb'">lsorbian</xsl:when>
            <xsl:when test="$documentLang='el'">greek</xsl:when>
            <xsl:when test="$documentLang='ell'">greek</xsl:when>
            <xsl:when test="$documentLang='en'">english</xsl:when>
            <xsl:when test="$documentLang='eng'">english</xsl:when>
            <xsl:when test="$documentLang='eo'">esperanto</xsl:when>
            <xsl:when test="$documentLang='epo'">esperanto</xsl:when>
            <xsl:when test="$documentLang='es'">spanish</xsl:when>
            <xsl:when test="$documentLang='est'">estonian</xsl:when>
            <xsl:when test="$documentLang='et'">estonian</xsl:when>
            <xsl:when test="$documentLang='eu'">basque</xsl:when>
            <xsl:when test="$documentLang='eus'">basque</xsl:when>
            <xsl:when test="$documentLang='fa'">farsi</xsl:when>
            <xsl:when test="$documentLang='fas'">farsi</xsl:when>
            <xsl:when test="$documentLang='fi'">finnish</xsl:when>
            <xsl:when test="$documentLang='fin'">finnish</xsl:when>
            <xsl:when test="$documentLang='fr'">french</xsl:when>
            <xsl:when test="$documentLang='fra'">french</xsl:when>
            <xsl:when test="$documentLang='ga'">irish</xsl:when>
            <xsl:when test="$documentLang='gd'">scottish</xsl:when>
            <xsl:when test="$documentLang='gl'">galician</xsl:when>
            <xsl:when test="$documentLang='gla'">scottish</xsl:when>
            <xsl:when test="$documentLang='gle'">irish</xsl:when>
            <xsl:when test="$documentLang='glg'">galician</xsl:when>
            <xsl:when test="$documentLang='he'">hebrew</xsl:when>
            <xsl:when test="$documentLang='heb'">hebrew</xsl:when>
            <xsl:when test="$documentLang='hi'">hindi</xsl:when>
            <xsl:when test="$documentLang='hin'">hindi</xsl:when>
            <xsl:when test="$documentLang='hr'">croatian</xsl:when>
            <xsl:when test="$documentLang='hrv'">croatian</xsl:when>
            <xsl:when test="$documentLang='hsb'">usorbian</xsl:when>
            <xsl:when test="$documentLang='hu'">hungarian</xsl:when>
            <xsl:when test="$documentLang='hun'">hungarian</xsl:when>
            <xsl:when test="$documentLang='hy'">armenian</xsl:when>
            <xsl:when test="$documentLang='hye'">armenian</xsl:when>
            <xsl:when test="$documentLang='ia'">interlingua</xsl:when>
            <xsl:when test="$documentLang='id'">indonesian</xsl:when>
            <xsl:when test="$documentLang='ina'">interlingua</xsl:when>
            <xsl:when test="$documentLang='ind'">indonesian</xsl:when>
            <xsl:when test="$documentLang='is'">icelandic</xsl:when>
            <xsl:when test="$documentLang='isl'">icelandic</xsl:when>
            <xsl:when test="$documentLang='it'">italian</xsl:when>
            <xsl:when test="$documentLang='ita'">italian</xsl:when>
            <xsl:when test="$documentLang='la'">latin</xsl:when>
            <xsl:when test="$documentLang='lao'">lao</xsl:when>
            <xsl:when test="$documentLang='lat'">latin</xsl:when>
            <xsl:when test="$documentLang='lav'">latvian</xsl:when>
            <xsl:when test="$documentLang='lit'">lithuanian</xsl:when>
            <xsl:when test="$documentLang='lo'">lao</xsl:when>
            <xsl:when test="$documentLang='lt'">lithuanian</xsl:when>
            <xsl:when test="$documentLang='lv'">latvian</xsl:when>
            <xsl:when test="$documentLang='mal'">malayalam</xsl:when>
            <xsl:when test="$documentLang='mar'">marathi</xsl:when>
            <xsl:when test="$documentLang='ml'">malayalam</xsl:when>
            <xsl:when test="$documentLang='mr'">marathi</xsl:when>
            <xsl:when test="$documentLang='ms'">malay</xsl:when>
            <xsl:when test="$documentLang='msa'">malay</xsl:when>
            <xsl:when test="$documentLang='nl'">dutch</xsl:when>
            <xsl:when test="$documentLang='nld'">dutch</xsl:when>
            <xsl:when test="$documentLang='nn'">nynorsk</xsl:when>
            <xsl:when test="$documentLang='nno'">nynorsk</xsl:when>
            <xsl:when test="$documentLang='oc'">occitan</xsl:when>
            <xsl:when test="$documentLang='oci'">occitan</xsl:when>
            <xsl:when test="$documentLang='pl'">polish</xsl:when>
            <xsl:when test="$documentLang='pol'">polish</xsl:when>
            <xsl:when test="$documentLang='por'">portuges</xsl:when>
            <xsl:when test="$documentLang='pt'">portuges</xsl:when>
            <xsl:when test="$documentLang='ro'">romanian</xsl:when>
            <xsl:when test="$documentLang='ron'">romanian</xsl:when>
            <xsl:when test="$documentLang='ru'">russian</xsl:when>
            <xsl:when test="$documentLang='rus'">russian</xsl:when>
            <xsl:when test="$documentLang='sa'">sanskrit</xsl:when>
            <xsl:when test="$documentLang='san'">sanskrit</xsl:when>
            <xsl:when test="$documentLang='sk'">slovak</xsl:when>
            <xsl:when test="$documentLang='sl'">slovenian</xsl:when>
            <xsl:when test="$documentLang='slk'">slovak</xsl:when>
            <xsl:when test="$documentLang='slv'">slovenian</xsl:when>
            <xsl:when test="$documentLang='spa'">spanish</xsl:when>
            <xsl:when test="$documentLang='sq'">albanian</xsl:when>
            <xsl:when test="$documentLang='sqi'">albanian</xsl:when>
            <xsl:when test="$documentLang='sr'">serbian</xsl:when>
            <xsl:when test="$documentLang='srp'">serbian</xsl:when>
            <xsl:when test="$documentLang='sv'">swedish</xsl:when>
            <xsl:when test="$documentLang='swe'">swedish</xsl:when>
            <xsl:when test="$documentLang='syr'">syriac</xsl:when>
            <xsl:when test="$documentLang='ta'">tamil</xsl:when>
            <xsl:when test="$documentLang='tam'">tamil</xsl:when>
            <xsl:when test="$documentLang='te'">telugu</xsl:when>
            <xsl:when test="$documentLang='tel'">telugu</xsl:when>
            <xsl:when test="$documentLang='th'">thai</xsl:when>
            <xsl:when test="$documentLang='tha'">thai</xsl:when>
            <xsl:when test="$documentLang='tk'">turkmen</xsl:when>
            <xsl:when test="$documentLang='tr'">turkish</xsl:when>
            <xsl:when test="$documentLang='tuk'">turkmen</xsl:when>
            <xsl:when test="$documentLang='tur'">turkish</xsl:when>
            <xsl:when test="$documentLang='uk'">ukrainian</xsl:when>
            <xsl:when test="$documentLang='ukr'">ukrainian</xsl:when>
            <xsl:when test="$documentLang='ur'">urdu</xsl:when>
            <xsl:when test="$documentLang='urd'">urdu</xsl:when>
            <xsl:when test="$documentLang='vi'">vietnamese</xsl:when>
            <xsl:when test="$documentLang='vie'">vietnamese</xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetItemWidth
    -->
    <xsl:template name="GetItemWidth">
        <xsl:choose>
            <xsl:when test="name()='ol'">
                <xsl:call-template name="GetNumberedItemWidth"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>XLingPaperbulletlistitemwidth</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetLangInNonWrdLine
    -->
    <xsl:template name="GetLangInNonWrdLine">
        <xsl:choose>
            <xsl:when test="langData">
                <xsl:value-of select="langData/@lang"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="gloss/@lang"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetLetterWidth
    -->
    <xsl:template name="GetLetterWidth">
        <xsl:param name="iLetterCount"/>
        <xsl:choose>
            <xsl:when test="$iLetterCount &lt; 27">1.5</xsl:when>
            <xsl:when test="$iLetterCount &lt; 53">2.5</xsl:when>
            <xsl:otherwise>3</xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetLongestWordInCell
    -->
    <xsl:template name="GetListItemWidthPattern">
        <xsl:param name="sNumberFormat"/>
        <xsl:variable name="iSize" select="count(li)"/>
        <xsl:choose>
            <xsl:when test="$sNumberFormat='1'">
                <xsl:choose>
                    <xsl:when test="$iSize &lt; 10">
                        <xsl:text>8</xsl:text>
                    </xsl:when>
                    <xsl:when test="$iSize &lt; 100">
                        <xsl:text>88</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>888</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="$sNumberFormat='A'">
                <xsl:choose>
                    <xsl:when test="$iSize &lt; 28">
                        <xsl:text>M</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>MM</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="$sNumberFormat='a'">
                <xsl:choose>
                    <xsl:when test="$iSize &lt; 28">
                        <xsl:text>m</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>mm</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="$sNumberFormat='I'">
                <xsl:choose>
                    <xsl:when test="$iSize &lt; 8">
                        <xsl:text>VII</xsl:text>
                    </xsl:when>
                    <xsl:when test="$iSize &lt; 17">
                        <xsl:text>VIII</xsl:text>
                    </xsl:when>
                    <xsl:when test="$iSize &lt; 19">
                        <xsl:text>XVIII</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- hope for the best...  -->
                        <xsl:text>MMM</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="$sNumberFormat='i'">
                <xsl:choose>
                    <xsl:when test="$iSize &lt; 8">
                        <xsl:text>vii</xsl:text>
                    </xsl:when>
                    <xsl:when test="$iSize &lt; 17">
                        <xsl:text>viii</xsl:text>
                    </xsl:when>
                    <xsl:when test="$iSize &lt; 19">
                        <xsl:text>xviii</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- hope for the best...  -->
                        <xsl:text>mmm</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="translate($sNumberFormat,'1aA','8mM')"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetLongestWordInCell
    -->
    <xsl:template name="GetLongestWordInCell">
        <!-- We need to find the longest word in a table cell.
            We put XML into a variable, with a root of <words> and each line as <word>.
            Each word contains one word in the cell.  We then sort these and get the longest one.
            Note that with XSLT version 1.0, we have to use something like the Saxon extension function node-set().
        -->
        <xsl:variable name="words">
            <words>
                <xsl:call-template name="GetWordsInCell">
                    <xsl:with-param name="sList" select="."/>
                </xsl:call-template>
            </words>
        </xsl:variable>
        <xsl:for-each select="saxon:node-set($words)/descendant::text()">
            <xsl:sort select="string-length(.)" order="descending"/>
            <xsl:if test="position()=1">
                <xsl:value-of select="."/>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>
    <!--  
        GetMaxColumnCountForLineGroup
    -->
    <xsl:template name="GetMaxColumnCountForLineGroup">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:variable name="iTempCount">
            <xsl:for-each select="line | ../listWord">
                <xsl:sort select="count(wrd) + count(langData) + count(gloss)" order="descending" data-type="number"/>
                <xsl:if test="position()=1">
                    <xsl:value-of select="count(wrd) + count(langData) + count(gloss)"/>
                </xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test=" name()!='listWord' and $iTempCount=1 or name()!='listWord' and count(descendant::wrd)=0">
                <!-- have space-delimited langData and/or gloss line(s) -->
                <xsl:variable name="sMaxColCount">
                    <xsl:call-template name="GetMaxColumnCountForPCDATALines"/>
                </xsl:variable>
                <xsl:variable name="sIsoCode">
                    <xsl:for-each select="parent::listInterlinear">
                        <xsl:call-template name="GetISOCode"/>
                    </xsl:for-each>
                </xsl:variable>
                <!--  2011.11.16              <xsl:choose>
                    <xsl:when test="string-length($sIsoCode) = 3">-->
                <xsl:choose>
                    <xsl:when test="contains($bListsShareSameCode,'N')">
                        <xsl:value-of select="string-length($sMaxColCount)+1"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="string-length($sMaxColCount)"/>
                    </xsl:otherwise>
                </xsl:choose>
                <!-- 2011.11.16                   </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="string-length($sMaxColCount)"/>
                    </xsl:otherwise>
                </xsl:choose>
-->
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="sIsoCode">
                    <xsl:for-each select="parent::listInterlinear">
                        <xsl:call-template name="GetISOCode"/>
                    </xsl:for-each>
                </xsl:variable>
                <xsl:choose>
                    <xsl:when test="contains($bListsShareSameCode,'N')">
                        <xsl:value-of select="number($iTempCount + 1)"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$iTempCount"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetMaxColumnCountForPCDATALines
    -->
    <xsl:template name="GetMaxColumnCountForPCDATALines">
        <!-- We need to figure out the maximum number of items in the line elements.
            The maximum could be in any line since the user just keys data in them.
            We use a bit of a trick.  We put XML into a variable, with a root of <lines> and each line as <line>.
            Each line contains one x for each item in the line.  We then sort these and get the longest one.
            We use the longest one to figure out how many columns we will need.
            Note that with XSLT version 1.0, we have to use something like the Saxon extension function node-set().
        -->
        <xsl:variable name="lines">
            <lines>
                <xsl:for-each select="line | ../listWord">
                    <line>
                        <xsl:call-template name="CalculateColumnsInInterlinearLine">
                            <xsl:with-param name="sList" select="langData | gloss"/>
                        </xsl:call-template>
                    </line>
                </xsl:for-each>
            </lines>
        </xsl:variable>
        <xsl:for-each select="saxon:node-set($lines)/descendant::*">
            <xsl:for-each select="line">
                <xsl:sort select="." order="descending"/>
                <xsl:if test="position()=1">
                    <xsl:value-of select="."/>
                </xsl:if>
            </xsl:for-each>
        </xsl:for-each>
    </xsl:template>
    <!--  
        GetMeasure
    -->
    <xsl:template name="GetMeasure">
        <xsl:param name="sValue"/>
        <xsl:value-of select="number(substring($sValue,1,string-length($sValue) - 2))"/>
    </xsl:template>
    <!--  
        GetMediaObjectSymbolCode
    -->
    <xsl:template name="GetMediaObjectSymbolCode">
        <tex:cmd name="symbol">
            <tex:parm>
                <xsl:call-template name="GetMediaObjectIconCode"/>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        GetNumberedItemWidth
    -->
    <xsl:template name="GetNumberedItemWidth">
        <xsl:variable name="iSize" select="count(li)"/>
        <xsl:variable name="sNumberFormat" select="@numberFormat"/>
        <xsl:choose>
            <xsl:when test="string-length($sNumberFormat) &gt; 0">
                <xsl:call-template name="GetDynamicListItemName"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="NestingLevel">
                    <xsl:choose>
                        <xsl:when test="ancestor::endnote">
                            <xsl:value-of select="count(ancestor::ol[not(descendant::endnote)])"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="count(ancestor-or-self::ol)"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:choose>
                    <xsl:when test="($NestingLevel mod 3)=1">
                        <xsl:choose>
                            <xsl:when test="$iSize &lt; 10">
                                <xsl:text>XLingPapersingledigitlistitemwidth</xsl:text>
                            </xsl:when>
                            <xsl:when test="$iSize &lt; 100">
                                <xsl:text>XLingPaperdoubledigitlistitemwidth</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>XLingPapertripledigitlistitemwidth</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:when test="($NestingLevel mod 3)=2">
                        <xsl:choose>
                            <xsl:when test="$iSize &lt; 27">
                                <xsl:text>XLingPapersingleletterlistitemwidth</xsl:text>
                            </xsl:when>
                            <xsl:when test="$iSize &lt; 53">
                                <xsl:text>XLingPaperdoubleletterlistitemwidth</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>XLingPapertripleletterlistitemwidth</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:when test="($NestingLevel mod 3)=0">
                        <xsl:choose>
                            <xsl:when test="$iSize &lt; 8">
                                <xsl:text>XLingPaperromanviilistitemwidth</xsl:text>
                            </xsl:when>
                            <xsl:when test="$iSize &lt; 17">
                                <xsl:text>XLingPaperromanviiilistitemwidth</xsl:text>
                            </xsl:when>
                            <xsl:when test="$iSize &lt; 19">
                                <xsl:text>XLingPaperromanxviiilistitemwidth</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <!-- hope for the best...  -->
                                <xsl:text>XLingPaperdoubleletterlistitemwidth</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- 
        GetOrientedContents
    -->
    <xsl:template name="GetOrientedContents">
        <xsl:param name="bFlip"/>
        <xsl:variable name="sContents">
            <!--               <xsl:apply-templates/>  Why do we want to include all the parameters, etc. when what we really want is the text? -->
            <!--                    <xsl:value-of select="."/>-->
            <xsl:value-of select="self::*[not(descendant-or-self::endnote)]"/>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$bFlip='Y'">
                <!-- flip order, left to right -->
                <xsl:call-template name="ReverseContents">
                    <xsl:with-param name="sList" select="$sContents"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="langData and id(langData/@lang)/@rtl='yes'">
                <!-- flip order, left to right -->
                <xsl:call-template name="ReverseContents">
                    <xsl:with-param name="sList" select="$sContents"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sContents"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- 
        GetRealColumnNumberOfCell
    -->
    <xsl:template name="GetRealColumnNumberOfCell">
        <xsl:param name="iRowNumberOfCell"/>
        <xsl:variable name="precedingSiblingsOfPreviousCellWithRowspan" select="preceding-sibling::td | preceding-sibling::th"/>
        <xsl:variable name="iInSituColumnNumberOfPreviousCellWithRowspan"
            select="count(exsl:node-set($precedingSiblingsOfPreviousCellWithRowspan)[not(number(@colspan) &gt; 0)]) + sum(exsl:node-set($precedingSiblingsOfPreviousCellWithRowspan)[number(@colspan) &gt; 0]/@colspan)"/>
        <xsl:variable name="iPreviousRowspansInRowOfCell">
            <xsl:variable name="sOneYForEachColumn">
                <xsl:call-template name="CountPreviousRowspansInMyRow">
                    <xsl:with-param name="previousCellsWithRowspansSpanningMyRow"
                        select="../preceding-sibling::tr/th[@rowspan][($iRowNumberOfCell - (count(../preceding-sibling::tr) + 1)) + 1 &lt;= @rowspan] | ../preceding-sibling::tr/td[@rowspan][($iRowNumberOfCell - (count(../preceding-sibling::tr) + 1)) + 1 &lt;= @rowspan]"/>
                    <xsl:with-param name="iPosition">1</xsl:with-param>
                    <xsl:with-param name="iMyInSituColumnNumber" select="$iInSituColumnNumberOfPreviousCellWithRowspan"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:value-of select="string-length($sOneYForEachColumn)"/>
        </xsl:variable>
        <xsl:value-of select="$iInSituColumnNumberOfPreviousCellWithRowspan + $iPreviousRowspansInRowOfCell"/>
    </xsl:template>
    <!--  
        GetSpaceBetweenGroups
    -->
    <xsl:template name="GetSpaceBetweenGroups">
        <xsl:choose>
            <xsl:when test="string-length($sSpaceBetweenGroups) &gt; 0">
                <xsl:value-of select="$sSpaceBetweenGroups"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="GetCurrentPointSize"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetWidthForExampleContent
    -->
    <xsl:template name="GetWidthForExampleContent">
        <xsl:param name="originalContext"/>
        <tex:cmd name="textwidth" gr="0" nl2="0"/>
        <xsl:text> - </xsl:text>
        <xsl:value-of select="$sExampleIndentBefore"/>
        <xsl:text> - </xsl:text>
        <xsl:value-of select="$sExampleIndentAfter"/>
        <xsl:text> - </xsl:text>
        <xsl:value-of select="$iNumberWidth"/>
        <xsl:text>em - </xsl:text>
        <tex:cmd name="XLingPaperspacewidth" gr="0" nl2="0"/>
        <xsl:if test="parent::listInterlinear or self::listInterlinear or $originalContext and exsl:node-set($originalContext)[parent::*[name()='listInterlinear']]">
            <xsl:variable name="iLetterCount">
                <xsl:choose>
                    <xsl:when test="parent::listInterlinear">
                        <xsl:for-each select="parent::listInterlinear">
                            <xsl:value-of select="count(listInterlinear)"/>
                        </xsl:for-each>
                    </xsl:when>
                    <xsl:when test="self::listInterlinear">
                        <xsl:value-of select="count(listInterlinear)"/>
                    </xsl:when>
                    <xsl:when test="$originalContext and exsl:node-set($originalContext)[parent::*[name()='listInterlinear']]">
                        <xsl:for-each select="exsl:node-set($originalContext)[parent::*[name()='listInterlinear']]">
                            <xsl:value-of select="count(listInterlinear)"/>
                        </xsl:for-each>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$iNumberWidth"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:text>-</xsl:text>
            <xsl:call-template name="GetLetterWidth">
                <xsl:with-param name="iLetterCount" select="$iLetterCount"/>
            </xsl:call-template>
            <xsl:text>em</xsl:text>
        </xsl:if>
    </xsl:template>
    <!--  
        GetWordsInCell
    -->
    <xsl:template name="GetWordsInCell">
        <xsl:param name="sList"/>
        <xsl:variable name="sNewList" select="concat(normalize-space($sList),' ')"/>
        <xsl:variable name="sFirst" select="substring-before($sNewList,' ')"/>
        <xsl:variable name="sRest" select="substring-after($sNewList,' ')"/>
        <word>
            <xsl:value-of select="$sFirst"/>
        </word>
        <xsl:if test="$sRest">
            <xsl:call-template name="GetWordsInCell">
                <xsl:with-param name="sList" select="$sRest"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--  
        GetXeLaTeXSpecialCommand
    -->
    <xsl:template name="GetXeLaTeXSpecialCommand">
        <xsl:param name="sAttr"/>
        <xsl:param name="sDefaultValue"/>
        <xsl:variable name="sCommandBeginning" select="substring-after(@XeLaTeXSpecial, $sAttr)"/>
        <xsl:variable name="sCommand" select="substring-before(substring($sCommandBeginning,2),$sSingleQuote)"/>
        <xsl:choose>
            <xsl:when test="string-length(normalize-space($sCommand)) &gt; 0">
                <xsl:value-of select="$sCommand"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:copy-of select="$sDefaultValue"/>
                <!--            <xsl:value-of select="$sDefaultValue"/>-->
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        HandleEndnotesInCaptionOfFigure
    -->
    <xsl:template name="HandleEndnotesInCaptionOfFigure">
        <xsl:if test="not(exsl:node-set($backMatterLayoutInfo)/useEndNotesLayout)">
            <xsl:for-each select="caption">
                <xsl:for-each select="descendant-or-self::endnote">
                    <xsl:apply-templates select=".">
                        <xsl:with-param name="sTeXFootnoteKind" select="'footnotetext'"/>
                    </xsl:apply-templates>
                </xsl:for-each>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleEndnoteTextInExampleInTable
    -->
    <xsl:template name="HandleEndnotesTextInCaptionAfterTablenumbered">
        <xsl:if test="not(exsl:node-set($backMatterLayoutInfo)/useEndNotesLayout)">
            <xsl:variable name="iEndnotesInTable" select="count(table/tr/descendant-or-self::endnote)"/>
            <xsl:for-each select="table/caption">
                <xsl:for-each select="descendant-or-self::endnote">
                    <xsl:variable name="sFootnoteNumberOffOne">
                        <xsl:call-template name="CalculateFootnoteNumber">
                            <xsl:with-param name="bInTableNumbered" select="'Y'"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:apply-templates select=".">
                        <xsl:with-param name="sTeXFootnoteKind" select="'footnotetext'"/>
                        <xsl:with-param name="sPrecalculatedNumber" select="$sFootnoteNumberOffOne + $iEndnotesInTable"/>
                    </xsl:apply-templates>
                </xsl:for-each>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleEndnoteTextInExampleInTable
    -->
    <xsl:template name="HandleEndnoteTextInExampleInTable">
        <xsl:if test="ancestor::table and descendant::endnote">
            <!-- when have a table with embedded examples and those examples have endnotes in them, 
                we need to put footnotetext here after the example.-->
            <xsl:for-each select="descendant-or-self::endnote">
                <xsl:apply-templates select=".">
                    <xsl:with-param name="sTeXFootnoteKind" select="'footnotetext'"/>
                </xsl:apply-templates>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleFontScriptOrLanguageXeLaTeXSpecial
    -->
    <xsl:template name="HandleFontScriptOrLanguageXeLaTeXSpecial">
        <xsl:param name="sFontSpecial"/>
        <xsl:param name="sDefault"/>
        <xsl:param name="sPunctuation" select="','"/>
        <xsl:value-of select="$sPunctuation"/>
        <xsl:value-of select="$sFontSpecial"/>
        <xsl:call-template name="HandleXeLaTeXSpecialCommand">
            <xsl:with-param name="sPattern" select="$sFontSpecial"/>
            <xsl:with-param name="default" select="$sDefault"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        HandleFontSize
    -->
    <xsl:template name="HandleFontSize">
        <xsl:param name="sSize"/>
        <xsl:param name="sFontFamily"/>
        <xsl:param name="language"/>
        <xsl:choose>
            <!-- percentage -->
            <xsl:when test="contains($sSize, '%')">
                <xsl:choose>
                    <xsl:when test="starts-with($sSize, '100')">
                        <!-- do nothing; leave it -->
                    </xsl:when>
                    <xsl:otherwise>
                        <tex:cmd name="fontspec">
                            <tex:opt>
                                <xsl:call-template name="HandleXeLaTeXSpecialGraphiteOrFontFeature">
                                    <xsl:with-param name="language" select="$language"/>
                                    <xsl:with-param name="bMoreOptionsWillFollow" select="'Y'"/>
                                </xsl:call-template>
                                <xsl:text>Scale=</xsl:text>
                                <xsl:value-of select="number(substring-before($sSize,'%')) div 100"/>
                                <!-- some open type fonts also need a special script; handle them here -->
                                <xsl:if test="$language and contains(exsl:node-set($language)/@XeLaTeXSpecial, $sFontScript) or $language and contains(exsl:node-set($language)/@XeLaTeXSpecial, $sFontScriptLower)">
                                    <xsl:for-each select="$language">
                                        <xsl:call-template name="HandleFontScriptOrLanguageXeLaTeXSpecial">
                                            <xsl:with-param name="sFontSpecial" select="$sFontScript"/>
                                            <xsl:with-param name="sDefault" select="'Arabic'"/>
                                        </xsl:call-template>
                                    </xsl:for-each>
                                </xsl:if>
                            </tex:opt>
                            <tex:parm>
                                <xsl:variable name="sNormFontFamily" select="normalize-space($sFontFamily)"/>
                                <xsl:choose>
                                    <xsl:when test="string-length($sNormFontFamily) &gt; 0">
                                        <xsl:value-of select="$sFontFamily"/>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:value-of select="$sDefaultFontFamily"/>
                                    </xsl:otherwise>
                                </xsl:choose>
                                <!-- some open type fonts also need a special language; handle them here -->
                                <xsl:if test="$language and contains(exsl:node-set($language)/@XeLaTeXSpecial, $sFontLanguage)">
                                    <xsl:for-each select="$language">
                                        <xsl:call-template name="HandleFontScriptOrLanguageXeLaTeXSpecial">
                                            <xsl:with-param name="sFontSpecial" select="$sFontLanguage"/>
                                            <xsl:with-param name="sDefault" select="'ARA'"/>
                                            <xsl:with-param name="sPunctuation" select="':'"/>
                                        </xsl:call-template>
                                    </xsl:for-each>
                                </xsl:if>
                            </tex:parm>
                        </tex:cmd>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <!-- relative sizes -->
            <xsl:when test="$sSize='smaller'">
                <tex:cmd name="small" gr="1"/>
            </xsl:when>
            <xsl:when test="$sSize='larger'">
                <tex:cmd name="large" gr="1"/>
            </xsl:when>
            <!-- key term absolute values -->
            <xsl:when test="$sSize='large'">
                <tex:cmd name="large" gr="1"/>
            </xsl:when>
            <xsl:when test="$sSize='medium'">
                <tex:cmd name="normalsize" gr="1"/>
            </xsl:when>
            <xsl:when test="$sSize='small'">
                <tex:cmd name="small" gr="1"/>
            </xsl:when>
            <xsl:when test="$sSize='x-large'">
                <tex:cmd name="Large" gr="1"/>
            </xsl:when>
            <xsl:when test="$sSize='xx-large'">
                <tex:cmd name="LARGE" gr="1"/>
            </xsl:when>
            <xsl:when test="$sSize='x-small'">
                <tex:cmd name="footnotesize" gr="1"/>
            </xsl:when>
            <xsl:when test="$sSize='xx-small'">
                <tex:cmd name="scriptsize" gr="1"/>
            </xsl:when>
            <!-- assume is a number and probably in points -->
            <xsl:otherwise>
                <xsl:variable name="sSizeOnly" select="substring-before($sSize, 'pt')"/>
                <tex:cmd name="fontsize">
                    <tex:parm>
                        <xsl:value-of select="$sSizeOnly"/>
                    </tex:parm>
                    <tex:parm>
                        <xsl:value-of select="number($sSizeOnly) * 1.2"/>
                    </tex:parm>
                </tex:cmd>
                <xsl:choose>
                    <xsl:when test="name()='endnote' and parent::langData">
                        <!-- need {} after selectfont or following text gets jammed up to footnote number -->
                        <tex:cmd name="selectfont"/>
                    </xsl:when>
                    <xsl:when test="name()='endnote' and parent::gloss">
                        <!-- need {} after selectfont or following text gets jammed up to footnote number -->
                        <tex:cmd name="selectfont"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <tex:cmd name="selectfont" gr="0" sp="1"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        HandleFootnotesInTableHeader
    -->
    <xsl:template name="HandleFootnotesInTableHeader">
        <xsl:if test="position()=1 or preceding-sibling::*[1][name()='th']">
            <xsl:variable name="headerRows" select="../preceding-sibling::tr[1][th[count(following-sibling::td)=0]]"/>
            <xsl:for-each select="exsl:node-set($headerRows)/th[descendant-or-self::endnote]">
                <xsl:for-each select="descendant-or-self::endnote">
                    <xsl:apply-templates select=".">
                        <xsl:with-param name="sTeXFootnoteKind" select="'footnotetext'"/>
                    </xsl:apply-templates>
                </xsl:for-each>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleFootnoteTextInLineGroup
    -->
    <xsl:template name="HandleFootnoteTextInLineGroup">
        <xsl:param name="originalContext"/>
        <xsl:for-each select="descendant-or-self::endnote">
            <xsl:apply-templates select=".">
                <xsl:with-param name="sTeXFootnoteKind" select="'footnotetext'"/>
                <xsl:with-param name="originalContext" select="$originalContext"/>
            </xsl:apply-templates>
        </xsl:for-each>
    </xsl:template>
    <!--  
        HandleHyphenationExceptionsFile
    -->
    <xsl:template name="HandleHyphenationExceptionsFile">
        <xsl:for-each select="//language[@id=$documentLang]">
            <xsl:variable name="sHyphenationExceptionsFile" select="normalize-space(@hyphenationExceptionsFile)"/>
            <xsl:if test="string-length($sHyphenationExceptionsFile) &gt; 0">
                <xsl:variable name="sPathToExceptionsFile" select="concat($sMainSourcePath, $sDirectorySlash, $sHyphenationExceptionsFile)"/>
                <xsl:for-each select="document($sPathToExceptionsFile)/exceptions/wordformingcharacter">
                    <tex:spec cat="esc"/>
                    <xsl:text>lccode`</xsl:text>
                    <xsl:value-of select="."/>
                    <xsl:text>=47
</xsl:text>
                </xsl:for-each>
                <tex:cmd name="hyphenation" nl2="1">
                    <tex:parm>
                        <xsl:for-each select="document($sPathToExceptionsFile)/exceptions/word">
                            <xsl:value-of select="."/>
                            <xsl:if test="position()!=last()">
                                <xsl:text>&#x20;</xsl:text>
                            </xsl:if>
                        </xsl:for-each>
                    </tex:parm>
                </tex:cmd>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>
    <!--  
        HandleGlossaryTermsInTableColumnSpecColumns
    -->
    <xsl:template name="HandleGlossaryTermsInTableColumnSpecColumns">
        <xsl:call-template name="HandleColumnWidth">
            <xsl:with-param name="sWidth" select="normalize-space(@glossaryTermWidth)"/>
            <xsl:with-param name="sDefaultSpec" select="'l'"/>
        </xsl:call-template>
        <xsl:if test="not(exsl:node-set($contentLayoutInfo)/glossaryTermsInTableLayout/@useEqualSignsColumn) or exsl:node-set($contentLayoutInfo)/glossaryTermsInTableLayout/@useEqualSignsColumn!='no'">
            <xsl:call-template name="HandleColumnWidth">
                <xsl:with-param name="sWidth" select="normalize-space(@equalsWidth)"/>
                <xsl:with-param name="sDefaultSpec" select="'c'"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="HandleColumnWidth">
            <xsl:with-param name="sWidth" select="normalize-space(@definitionWidth)"/>
            <xsl:with-param name="sDefaultSpec" select="'l'"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        HandleImmediatelyPrecedingLineGroupOrFree
    -->
    <xsl:template name="HandleImmediatelyPrecedingLineGroupOrFree">
        <tex:spec cat="esc"/>
        <tex:spec cat="esc"/>
        <tex:spec cat="lsb"/>
        <xsl:text>3pt</xsl:text>
        <tex:spec cat="rsb"/>
        <xsl:text>&#x0a;</xsl:text>
    </xsl:template>
    <!--  
        HandleImg
    -->
    <xsl:template name="HandleImg">
        <xsl:variable name="sImgFile" select="normalize-space(translate(@src,'\','/'))"/>
        <xsl:variable name="sExtension" select="substring($sImgFile,string-length($sImgFile)-3,4)"/>
        <xsl:choose>
            <xsl:when test="translate($sExtension,'GIF','gif')='.gif'">
                <xsl:if test="not(ancestor::example)">
                    <tex:cmd name="par"/>
                </xsl:if>
                <xsl:call-template name="ReportTeXCannotHandleThisMessage">
                    <xsl:with-param name="sMessage">
                        <xsl:text>We're sorry, but the graphic file </xsl:text>
                        <xsl:value-of select="$sImgFile"/>
                        <xsl:text> is in GIF format and this processor cannot handle GIF format.  You will need to convert the file to a different format.  We suggest using PNG format or JPG format.  Also see section 11.17.1.1 in the XLingPaper user documentation.</xsl:text>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$sExtension='.svg'">
                <xsl:variable name="sPDFFile" select="concat(substring-before($sImgFile,$sExtension),'.pdf')"/>
                <xsl:call-template name="HandlePDFImageFile">
                    <xsl:with-param name="sImgFile" select="$sPDFFile"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$sExtension='.mml'">
                <xsl:variable name="sPDFFile" select="concat(substring-before($sImgFile,$sExtension),'.pdf')"/>
                <xsl:call-template name="HandlePDFImageFile">
                    <xsl:with-param name="sImgFile" select="$sPDFFile"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$sExtension='.pdf'">
                <xsl:call-template name="HandlePDFImageFile">
                    <xsl:with-param name="sImgFile" select="$sImgFile"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="ancestor::example">
                        <tex:cmd name="parbox">
                            <tex:opt>t</tex:opt>
                            <tex:parm>
                                <tex:cmd name="textwidth" gr="0" nl2="0"/>
                                <xsl:text> - </xsl:text>
                                <xsl:value-of select="$sExampleIndentBefore"/>
                                <xsl:text> - </xsl:text>
                                <xsl:value-of select="$sExampleIndentAfter"/>
                            </tex:parm>
                            <tex:parm>
                                <xsl:call-template name="DoImageFile">
                                    <xsl:with-param name="sXeTeXGraphicFile" select="'XeTeXpicfile'"/>
                                    <xsl:with-param name="sImgFile" select="$sImgFile"/>
                                </xsl:call-template>
                            </tex:parm>
                        </tex:cmd>
                    </xsl:when>
                    <xsl:when test="parent::chart and not(ancestor::figure)">
                        <tex:cmd name="hbox">
                            <tex:parm>
                                <xsl:call-template name="DoImageFile">
                                    <xsl:with-param name="sXeTeXGraphicFile" select="'XeTeXpicfile'"/>
                                    <xsl:with-param name="sImgFile" select="$sImgFile"/>
                                </xsl:call-template>
                            </tex:parm>
                        </tex:cmd>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="DoImageFile">
                            <xsl:with-param name="sXeTeXGraphicFile" select="'XeTeXpicfile'"/>
                            <xsl:with-param name="sImgFile" select="$sImgFile"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        HandleISO639-3CodesInTableColumnSpecColumns
    -->
    <xsl:template name="HandleISO639-3CodesInTableColumnSpecColumns">
        <xsl:call-template name="HandleColumnWidth">
            <xsl:with-param name="sWidth" select="normalize-space(@codeWidth)"/>
            <xsl:with-param name="sDefaultSpec" select="'l'"/>
        </xsl:call-template>
        <xsl:if test="not(exsl:node-set($contentLayoutInfo)/iso639-3CodesInTableLayout/@useEqualSignsColumn) or exsl:node-set($contentLayoutInfo)/iso639-3CodesInTableLayout/@useEqualSignsColumn!='no'">
            <xsl:call-template name="HandleColumnWidth">
                <xsl:with-param name="sWidth" select="normalize-space(@equalsWidth)"/>
                <xsl:with-param name="sDefaultSpec" select="'c'"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="HandleColumnWidth">
            <xsl:with-param name="sWidth" select="normalize-space(@languageNameWidth)"/>
            <xsl:with-param name="sDefaultSpec" select="'l'"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        HandleISO639-HandleISOCodesInBreakAfter
    -->
    <xsl:template name="HandleISO639-3CodesInBreakAfter">
        <xsl:param name="originalContext"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($originalContext)[parent::example]">
                <xsl:variable name="iLineCount" select="count(line)"/>
                <xsl:variable name="sIsoCode">
                    <xsl:call-template name="GetISOCode"/>
                </xsl:variable>
                <xsl:choose>
                    <xsl:when test="string-length($sIsoCode) &gt; 3">
                        <!-- the ISO code takes two extra lines -->
                        <xsl:choose>
                            <xsl:when test="$iLineCount &lt; 3">
                                <xsl:choose>
                                    <xsl:when test="$iLineCount=1">
                                        <xsl:call-template name="AdjustForLongerISOCodeInInterlinearRef">
                                            <xsl:with-param name="iAdjust" select="'1.65'"/>
                                        </xsl:call-template>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:call-template name="AdjustForLongerISOCodeInInterlinearRef">
                                            <xsl:with-param name="iAdjust" select="'.65'"/>
                                        </xsl:call-template>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>*
</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- the ISO code takes one extra line -->
                        <xsl:choose>
                            <xsl:when test="$iLineCount=1">
                                <xsl:call-template name="AdjustForLongerISOCodeInInterlinearRef">
                                    <xsl:with-param name="iAdjust" select="'.65'"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>*
</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>*
</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        HandleLangDataGlossInWordOrListWord
    -->
    <xsl:template name="HandleLangDataGlossInWordOrListWord">
        <xsl:for-each select="langData | gloss">
            <xsl:apply-templates select="self::*"/>
            <xsl:if test="position()!=last()">
                <tex:spec cat="align"/>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>
    <!--  
        HandleLanguageContent
    -->
    <xsl:template name="HandleLanguageContent">
        <xsl:param name="language"/>
        <xsl:param name="bReversing"/>
        <xsl:param name="originalContext"/>
        <xsl:param name="bInMarker" select="'N'"/>
        <xsl:param name="fInContents" select="'N'"/>
        <xsl:variable name="bReverseWrdContent">
            <xsl:choose>
                <xsl:when test="ancestor-or-self::wrd">
                    <xsl:choose>
                        <xsl:when test="exsl:node-set($language)/@rtl='yes' and $bReversing='N'">
                            <!-- only need to reverse if the wrd contains a space (but that space is not in an endnote) -->
                            <xsl:choose>
                                <xsl:when test="descendant::endnote">
                                    <xsl:variable name="sNonEndnote" select="node()[name()!='endnote']"/>
                                    <xsl:choose>
                                        <xsl:when test="contains($sNonEndnote,' ')">
                                            <xsl:text>Y</xsl:text>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <xsl:text>N</xsl:text>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:choose>
                                        <xsl:when test="contains(.,' ')">
                                            <xsl:text>Y</xsl:text>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <xsl:text>N</xsl:text>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>N</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Not in a wrd but make this be 'Y' so choose below works properly -->
                    <xsl:text>Y</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="exsl:node-set($language)/@rtl='yes' and $bReversing='N' and $bReverseWrdContent='Y'">
                <xsl:call-template name="ReverseContentsInNodes">
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$bReversing = 'Y'">
                <xsl:apply-templates select="node()" mode="reverse">
                    <xsl:sort select="position()" order="descending"/>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:apply-templates>
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="$fInContents='Y'">
                        <xsl:apply-templates mode="contents">
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                            <xsl:with-param name="bInMarker" select="$bInMarker"/>
                        </xsl:apply-templates>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:apply-templates>
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                            <xsl:with-param name="bInMarker" select="$bInMarker"/>
                        </xsl:apply-templates>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        HandleMulticolumnInCell
    -->
    <xsl:template name="HandleMulticolumnInCell">
        <xsl:param name="bInARowSpan"/>
        <xsl:param name="iBorder"/>
        <xsl:param name="iColSpan" select="'1'"/>
        <xsl:param name="sWidth" select="normalize-space(@width)"/>
        <tex:cmd name="multicolumn">
            <tex:parm>
                <xsl:value-of select="$iColSpan"/>
            </tex:parm>
            <tex:parm>
                <xsl:if test="count(preceding-sibling::*) = 0 and not(contains($bInARowSpan,'Y'))">
                    <!--                     <xsl:if test="count(preceding-sibling::*) = 0">-->
                    <xsl:call-template name="CreateColumnSpecDefaultAtExpression"/>
                </xsl:if>
                <xsl:if test="$iBorder=0 and contains(@XeLaTeXSpecial,'border-left=') or contains(key('TypeID',@type)/@XeLaTeXSpecial,'border-left=')">
                    <xsl:variable name="sValue">
                        <xsl:choose>
                            <xsl:when test="contains(key('TypeID',@type)/@XeLaTeXSpecial,'border-left=')">
                                <xsl:for-each select="key('TypeID',@type)">
                                    <xsl:call-template name="HandleXeLaTeXSpecialCommand">
                                        <xsl:with-param name="sPattern" select="'border-left='"/>
                                        <xsl:with-param name="default" select="'0'"/>
                                    </xsl:call-template>
                                </xsl:for-each>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="HandleXeLaTeXSpecialCommand">
                                    <xsl:with-param name="sPattern" select="'border-left='"/>
                                    <xsl:with-param name="default" select="'0'"/>
                                </xsl:call-template>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:variable>
                    <xsl:call-template name="CreateVerticalLine">
                        <xsl:with-param name="iBorder" select="number($sValue)"/>
                        <xsl:with-param name="bDisallowVerticalLines" select="'N'"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:call-template name="CreateColumnSpec">
                    <xsl:with-param name="iBorder" select="$iBorder"/>
                    <xsl:with-param name="sWidth" select="$sWidth"/>
                </xsl:call-template>
                <xsl:if test="$iBorder=0 and contains(@XeLaTeXSpecial,'border-right=') or contains(key('TypeID',@type)/@XeLaTeXSpecial,'border-right=')">
                    <xsl:variable name="sValue">
                        <xsl:choose>
                            <xsl:when test="contains(key('TypeID',@type)/@XeLaTeXSpecial,'border-right=')">
                                <xsl:for-each select="key('TypeID',@type)">
                                    <xsl:call-template name="HandleXeLaTeXSpecialCommand">
                                        <xsl:with-param name="sPattern" select="'border-right='"/>
                                        <xsl:with-param name="default" select="'0'"/>
                                    </xsl:call-template>
                                </xsl:for-each>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="HandleXeLaTeXSpecialCommand">
                                    <xsl:with-param name="sPattern" select="'border-right='"/>
                                    <xsl:with-param name="default" select="'0'"/>
                                </xsl:call-template>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:variable>
                    <xsl:call-template name="CreateVerticalLine">
                        <xsl:with-param name="iBorder" select="number($sValue)"/>
                        <xsl:with-param name="bDisallowVerticalLines" select="'N'"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="count(following-sibling::*) = 0">
                    <xsl:call-template name="CreateVerticalLine">
                        <xsl:with-param name="iBorder" select="$iBorder"/>
                    </xsl:call-template>
                    <xsl:call-template name="CreateColumnSpecDefaultAtExpression"/>
                </xsl:if>
            </tex:parm>
        </tex:cmd>
        <tex:spec cat="bg"/>
    </xsl:template>
    <!--  
        HandleMultirowInCell
    -->
    <xsl:template name="HandleMultirowInCell">
        <xsl:param name="valignFixup"/>
        <tex:cmd name="multirow">
            <tex:parm>
                <xsl:variable name="sRowSpan" select="normalize-space(@rowspan)"/>
                <xsl:choose>
                    <xsl:when test="string-length($sRowSpan) &gt; 0">
                        <xsl:value-of select="$sRowSpan"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>1</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </tex:parm>
            <tex:parm>
                <xsl:choose>
                    <xsl:when test="string-length(normalize-space(@width)) &gt; 0">
                        <xsl:value-of select="@width"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>*</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </tex:parm>
            <xsl:if test="@valign">
                <xsl:choose>
                    <xsl:when test="$valignFixup!='0pt'">
                        <tex:opt>
                            <xsl:value-of select="$valignFixup"/>
                        </tex:opt>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:variable name="iAdjustFactor" select="(@rowspan - 1) * 1.25"/>
                        <xsl:choose>
                            <xsl:when test="@valign='top'">
                                <tex:opt>
                                    <xsl:value-of select="$iAdjustFactor"/>
                                    <xsl:text>ex</xsl:text>
                                </tex:opt>
                            </xsl:when>
                            <xsl:when test="@valign='bottom'">
                                <tex:opt>
                                    <xsl:text>-</xsl:text>
                                    <xsl:value-of select="$iAdjustFactor"/>
                                    <xsl:text>ex</xsl:text>
                                </tex:opt>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:if>
        </tex:cmd>
        <tex:spec cat="bg"/>
    </xsl:template>
    <!--  
        HandlePDFImageFile
    -->
    <xsl:template name="HandlePDFImageFile">
        <xsl:param name="sImgFile"/>
        <xsl:choose>
            <xsl:when test="ancestor::example">
                <tex:cmd name="parbox">
                    <tex:opt>t</tex:opt>
                    <tex:parm>
                        <tex:cmd name="textwidth" gr="0" nl2="0"/>
                        <!--<xsl:text> - </xsl:text>
                        <xsl:value-of select="$sBlockQuoteIndent"/>
                        <xsl:text> - </xsl:text>
                        <xsl:value-of select="$iExampleWidth"/>
                        <xsl:text>em</xsl:text>-->
                        <xsl:text> - </xsl:text>
                        <xsl:value-of select="$sExampleIndentBefore"/>
                        <xsl:text> - </xsl:text>
                        <xsl:value-of select="$sExampleIndentAfter"/>
                    </tex:parm>
                    <tex:parm>
                        <xsl:call-template name="DoImageFile">
                            <xsl:with-param name="sXeTeXGraphicFile" select="'XeTeXpdffile'"/>
                            <xsl:with-param name="sImgFile" select="$sImgFile"/>
                        </xsl:call-template>
                    </tex:parm>
                </tex:cmd>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="DoImageFile">
                    <xsl:with-param name="sXeTeXGraphicFile" select="'XeTeXpdffile'"/>
                    <xsl:with-param name="sImgFile" select="$sImgFile"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        HandlePreviousPInEndnote
    -->
    <xsl:template name="HandlePreviousPInEndnote">
        <xsl:choose>
            <xsl:when test="ancestor::table">
                <xsl:text>&#xa;</xsl:text>
            </xsl:when>
            <xsl:when test="ancestor::secTitle or ancestor::title">
                <tex:spec cat="esc"/>
                <tex:spec cat="esc"/>
            </xsl:when>
            <xsl:otherwise>
                <tex:cmd name="par"/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:choose>
            <xsl:when test="name()='pc'">
                <tex:cmd name="noindent" gr="0" nl2="0" sp="1"/>
            </xsl:when>
            <xsl:otherwise>
                <tex:cmd name="indent" gr="0" nl2="0" sp="1"/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:apply-templates/>
    </xsl:template>
    <!--  
        HandleSmallCapsBegin
    -->
    <xsl:template name="HandleSmallCapsBegin">
        <!-- HACK: "real" typesetting systems require a custom small caps font -->
        <!-- Use font-size:smaller and do a text-transform to uppercase -->
        <!--      <tex:cmd name="small" gr="0"/>-->
        <tex:spec cat="bg"/>
        <tex:cmd name="MakeUppercase" gr="0"/>
        <tex:spec cat="bg"/>
    </xsl:template>
    <!--  
        HandleSmallCapsBracketsOnly
    -->
    <xsl:template name="HandleSmallCapsBracketsOnly">
        <tex:spec cat="bg"/>
        <tex:spec cat="bg"/>
        <!--        <xsl:call-template name="HandleSmallCapsEndDoNestedTypes">
            <xsl:with-param name="sList" select="@types"/>
            </xsl:call-template>
        -->
    </xsl:template>
    <!--  
        HandleSmallCapsEnd
    -->
    <xsl:template name="HandleSmallCapsEnd">
        <!-- may need to protect \\ so we always do it -->
        <tex:cmd name="protect" gr="0"/>
        <tex:spec cat="eg"/>
        <tex:spec cat="eg"/>
        <!--        <xsl:call-template name="HandleSmallCapsEndDoNestedTypes">
            <xsl:with-param name="sList" select="@types"/>
        </xsl:call-template>
-->
    </xsl:template>
    <!--  
        HandleSmallCapsEndDoNestedTypes
    -->
    <xsl:template name="HandleSmallCapsEndDoNestedTypes">
        <xsl:param name="sList"/>
        <xsl:variable name="sNewList" select="concat(normalize-space($sList),' ')"/>
        <xsl:variable name="sFirst" select="substring-before($sNewList,' ')"/>
        <xsl:variable name="sRest" select="substring-after($sNewList,' ')"/>
        <xsl:if test="string-length($sFirst) &gt; 0">
            <xsl:for-each select="key('TypeID',$sFirst)">
                <xsl:call-template name="HandleSmallCapsEnd"/>
            </xsl:for-each>
            <xsl:if test="$sRest">
                <xsl:call-template name="HandleSmallCapsEndDoNestedTypes">
                    <xsl:with-param name="sList" select="$sRest"/>
                </xsl:call-template>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--
        HandleXeLaTeXSpecialCommand
    -->
    <xsl:template name="HandleVerticalSpacingWhenExampleHeadingWithISOCode">
        <xsl:variable name="sIsoCode">
            <xsl:call-template name="GetISOCode"/>
        </xsl:variable>
        <xsl:if test="string-length($sIsoCode) &gt; 0 and preceding-sibling::exampleHeading">
            <tex:cmd name="vspace*" nl2="1">
                <tex:parm>
                    <xsl:text>-.8</xsl:text>
                    <tex:cmd name="baselineskip" gr="0" nl2="0"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
    </xsl:template>
    <!--
        HandleXeLaTeXSpecialCommand
    -->
    <xsl:template name="HandleXeLaTeXSpecialCommand">
        <xsl:param name="sPattern"/>
        <xsl:param name="default"/>
        <xsl:choose>
            <xsl:when test="contains(@XeLaTeXSpecial,$sPattern)">
                <xsl:variable name="sValue">
                    <xsl:call-template name="GetXeLaTeXSpecialCommand">
                        <xsl:with-param name="sAttr" select="$sPattern"/>
                        <xsl:with-param name="sDefaultValue" select="$default"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:copy-of select="$sValue"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:copy-of select="$default"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        HandleXeLaTeXSpecialFontFeature
    -->
    <xsl:template name="HandleXeLaTeXSpecialFontFeature">
        <xsl:param name="sList"/>
        <xsl:param name="bIsFirstOpt" select="'Y'"/>
        <xsl:variable name="sCommandBeginning" select="substring-after($sList, $sFontFeature)"/>
        <xsl:variable name="sCommand" select="substring-before(substring($sCommandBeginning,2),$sSingleQuote)"/>
        <xsl:variable name="sRest" select="substring-after($sCommandBeginning,' ')"/>
        <xsl:if test="string-length($sCommandBeginning) &gt; 0">
            <xsl:if test="$bIsFirstOpt='N'">
                <xsl:text>,</xsl:text>
            </xsl:if>
            <xsl:text>RawFeature=</xsl:text>
            <tex:spec cat="bg"/>
            <xsl:value-of select="$sCommand"/>
            <tex:spec cat="eg"/>
            <xsl:if test="$sRest">
                <xsl:call-template name="HandleXeLaTeXSpecialFontFeature">
                    <xsl:with-param name="sList" select="$sRest"/>
                    <xsl:with-param name="bIsFirstOpt" select="'N'"/>
                </xsl:call-template>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--
        HandleXeLaTeXSpecialFontFeatureForFontName
    -->
    <xsl:template name="HandleXeLaTeXSpecialFontFeatureForFontName">
        <xsl:param name="sList"/>
        <xsl:variable name="sCommandBeginning" select="substring-after($sList, $sFontFeature)"/>
        <xsl:variable name="sCommand" select="substring-before(substring($sCommandBeginning,2),$sSingleQuote)"/>
        <xsl:variable name="sRest" select="substring-after($sCommandBeginning,' ')"/>
        <xsl:if test="string-length($sCommandBeginning) &gt; 0">
            <xsl:value-of select="translate(translate($sCommand,' =','XY'),$sDigits, $sLetters)"/>
            <xsl:if test="$sRest">
                <xsl:call-template name="HandleXeLaTeXSpecialFontFeatureForFontName">
                    <xsl:with-param name="sList" select="$sRest"/>
                </xsl:call-template>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--
        HandleXeLaTeXSpecialGraphiteOrFontFeature
    -->
    <xsl:template name="HandleXeLaTeXSpecialGraphiteOrFontFeature">
        <xsl:param name="language"/>
        <xsl:param name="bMoreOptionsWillFollow" select="'N'"/>
        <xsl:choose>
            <xsl:when test="$language and contains(exsl:node-set($language)/@XeLaTeXSpecial,$sGraphite)">
                <xsl:value-of select="$sRendererIsGraphite"/>
                <xsl:call-template name="HandleXeLaTeXSpecialFontFeature">
                    <xsl:with-param name="sList" select="exsl:node-set($language)/@XeLaTeXSpecial"/>
                    <xsl:with-param name="bIsFirstOpt" select="'N'"/>
                </xsl:call-template>
                <xsl:if test="$bMoreOptionsWillFollow='Y'">
                    <xsl:text>,</xsl:text>
                </xsl:if>
            </xsl:when>
            <xsl:when test="$language and contains(exsl:node-set($language)/@XeLaTeXSpecial,$sFontFeature)">
                <xsl:call-template name="HandleXeLaTeXSpecialFontFeature">
                    <xsl:with-param name="sList" select="exsl:node-set($language)/@XeLaTeXSpecial"/>
                    <xsl:with-param name="bIsFirstOpt" select="'Y'"/>
                </xsl:call-template>
                <xsl:if test="$bMoreOptionsWillFollow='Y'">
                    <xsl:text>,</xsl:text>
                </xsl:if>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--
        InsertCommaBetweenConsecutiveEndnotesUsingSuperscript
    -->
    <xsl:template name="InsertCommaBetweenConsecutiveEndnotesUsingSuperscript">
        <xsl:if test="preceding-sibling::node()[1][name()='endnote' or name()='endnoteRef']">
            <tex:spec cat="esc"/>
            <xsl:text>textsuperscript</xsl:text>
            <tex:spec cat="bg"/>
            <xsl:call-template name="InsertCommaBetweenConsecutiveEndnotes"/>
            <tex:spec cat="eg"/>
        </xsl:if>
    </xsl:template>
    <!--
        InsertFontSizeIfNeeded
    -->
    <xsl:template name="InsertFontSizeIfNeeded">
        <xsl:if test="number($sBasicPointSize)&gt;12 or number($sBasicPointSize)&lt;10">
            <xsl:call-template name="HandleFontSize">
                <xsl:with-param name="sSize" select="concat($sBasicPointSize,'pt')"/>
            </xsl:call-template>
            <xsl:text>&#x20;</xsl:text>
        </xsl:if>
    </xsl:template>
    <!--
        OKToBreakHere
    -->
    <xsl:template name="OKToBreakHere">
        <tex:cmd name="XLingPaperneedspace" nl2="1">
            <tex:parm>
                <xsl:text>5</xsl:text>
                <tex:spec cat="esc"/>
                <xsl:text>baselineskip</xsl:text>
            </tex:parm>
        </tex:cmd>
        <tex:spec cat="esc" nl1="1" nl2="0"/>
        <xsl:text>penalty-3000</xsl:text>
    </xsl:template>
    <!--
        OutputAbbreviationsInCommaSeparatedList
    -->
    <xsl:template name="OutputAbbreviationInCommaSeparatedList">
        <xsl:call-template name="DoInternalTargetBegin">
            <xsl:with-param name="sName" select="@id"/>
        </xsl:call-template>
        <xsl:call-template name="OutputAbbrTerm">
            <xsl:with-param name="abbr" select="."/>
        </xsl:call-template>
        <xsl:call-template name="DoAnyEqualsSignBetweenAbbrAndDefinition"/>
        <xsl:call-template name="OutputAbbrDefinition">
            <xsl:with-param name="abbr" select="."/>
        </xsl:call-template>
        <xsl:call-template name="DoInternalTargetEnd"/>
        <xsl:choose>
            <xsl:when test="position() = last()">
                <xsl:text>.</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>, </xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        OutputAbbreviationInTable
    -->
    <xsl:template name="OutputAbbreviationInTable">
        <xsl:param name="abbrsShownHere"/>
        <xsl:param name="abbrInSecondColumn"/>
        <!--  we do not use abbrsShownHere in this instance of OutputAbbreviationInTable  -->
        <xsl:call-template name="OutputAbbreviationItemInTable"/>
        <xsl:if test="exsl:node-set($contentLayoutInfo)/abbreviationsInTableLayout/@useDoubleColumns='yes'">
            <tex:spec cat="align"/>
            <xsl:for-each select="$abbrInSecondColumn">
                <xsl:call-template name="OutputAbbreviationItemInTable"/>
            </xsl:for-each>
        </xsl:if>
        <tex:spec cat="esc"/>
        <tex:spec cat="esc" nl2="1"/>
    </xsl:template>
    <!--
        OutputAbbreviationItemInTable
    -->
    <xsl:template name="OutputAbbreviationItemInTable">
        <tex:cmd name="setlength">
            <tex:parm>
                <tex:spec cat="esc"/>
                <xsl:text>baselineskip</xsl:text>
            </tex:parm>
            <tex:parm>
                <tex:spec cat="esc"/>
                <xsl:value-of select="$sTeXAbbrBaselineskip"/>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="DoInternalTargetBegin">
            <xsl:with-param name="sName" select="@id"/>
        </xsl:call-template>
        <xsl:call-template name="OutputAbbrTerm">
            <xsl:with-param name="abbr" select="."/>
        </xsl:call-template>
        <xsl:call-template name="DoInternalTargetEnd"/>
        <tex:spec cat="align"/>
        <xsl:if test="not(exsl:node-set($contentLayoutInfo)/abbreviationsInTableLayout/@useEqualSignsColumn) or exsl:node-set($contentLayoutInfo)/abbreviationsInTableLayout/@useEqualSignsColumn!='no'">
            <xsl:text> = </xsl:text>
            <tex:spec cat="align"/>
        </xsl:if>
        <xsl:call-template name="OutputAbbrDefinition">
            <xsl:with-param name="abbr" select="."/>
        </xsl:call-template>
    </xsl:template>
    <!--
        OutputAbbreviationsInTable
    -->
    <xsl:template name="OutputAbbreviationsInTable">
        <xsl:param name="abbrsUsed"
            select="//abbreviation[not(ancestor::chapterInCollection/backMatter/abbreviations)][//abbrRef[not(ancestor::chapterInCollection/backMatter/abbreviations) and not(ancestor::comment)]/@abbr=@id]"/>
        <xsl:if test="count($abbrsUsed) &gt; 0">
            <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacetables='yes' and exsl:node-set($contentLayoutInfo)/abbreviationsInTableLayout/@useSingleSpacing!='no'">
                <tex:spec cat="bg"/>
                <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
            </xsl:if>
            <tex:spec cat="bg"/>
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/abbreviationsInTableLayout"/>
            </xsl:call-template>
            <tex:cmd name="setlength">
                <tex:parm>
                    <tex:spec cat="esc"/>
                    <xsl:value-of select="$sTeXAbbrBaselineskip"/>
                </tex:parm>
                <tex:parm>
                    <tex:spec cat="esc"/>
                    <xsl:text>baselineskip</xsl:text>
                </tex:parm>
            </tex:cmd>
            <tex:env name="longtable">
                <tex:opt>l</tex:opt>
                <tex:parm>
                    <xsl:text>@</xsl:text>
                    <tex:group>
                        <tex:cmd name="hspace*">
                            <tex:parm>
                                <xsl:variable name="sStartIndent" select="normalize-space(exsl:node-set($contentLayoutInfo)/abbreviationsInTableLayout/@start-indent)"/>
                                <xsl:choose>
                                    <xsl:when test="string-length($sStartIndent)&gt;0">
                                        <xsl:value-of select="$sStartIndent"/>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <tex:cmd name="parindent" gr="0" nl2="0"/>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </tex:parm>
                        </tex:cmd>
                    </tex:group>
                    <xsl:call-template name="HandleAbbreviationsInTableColumnSpecColumns"/>
                    <xsl:if test="exsl:node-set($contentLayoutInfo)/abbreviationsInTableLayout/@useDoubleColumns='yes'">
                        <xsl:text>@</xsl:text>
                        <tex:group>
                            <tex:cmd name="hspace*">
                                <tex:parm>
                                    <xsl:variable name="sSep" select="normalize-space(exsl:node-set($contentLayoutInfo)/abbreviationsInTableLayout/@doubleColumnSeparation)"/>
                                    <xsl:choose>
                                        <xsl:when test="string-length($sSep)&gt;0">
                                            <xsl:value-of select="$sSep"/>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <tex:cmd name="parindent" gr="0" nl2="0"/>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </tex:parm>
                            </tex:cmd>
                        </tex:group>
                        <xsl:call-template name="HandleAbbreviationsInTableColumnSpecColumns"/>
                    </xsl:if>
                </tex:parm>
                <!--  I'm not happy with how this poor man's attempt at getting double column works when there are long definitions.
                The table column widths may be long and short; if a cell in the second row needs to lap over a line, then the
                corresponding cell in the other column may skip a row (as far as what one would expect).
                So I'm going with just a single table here.
                <xsl:variable name="iHalfwayPoint" select="ceiling(count($abbrsUsed) div 2)"/>
                <xsl:for-each select="exsl:node-set($abbrsUsed)[position() &lt;= $iHalfwayPoint]">
            -->
                <xsl:call-template name="SortAbbreviationsInTable">
                    <xsl:with-param name="abbrsUsed" select="$abbrsUsed"/>
                </xsl:call-template>
            </tex:env>
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/abbreviationsInTableLayout"/>
            </xsl:call-template>
            <tex:spec cat="eg"/>
            <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacetables='yes' and exsl:node-set($contentLayoutInfo)/abbreviationsInTableLayout/@useSingleSpacing!='no'">
                <tex:spec cat="eg"/>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--
        OutputAbbrDefinition
    -->
    <!--    <xsl:template name="OutputAbbrDefinition">
        <xsl:param name="abbr"/>
        <xsl:choose>
            <xsl:when test="string-length($abbrLang) &gt; 0">
                <xsl:choose>
                    <xsl:when test="string-length(exsl:node-set($abbr)//abbrInLang[@lang=$abbrLang]/abbrTerm) &gt; 0">
                        <xsl:apply-templates select="exsl:node-set($abbr)/abbrInLang[@lang=$abbrLang]/abbrDefinition/text() | exsl:node-set($abbr)/abbrInLang[@lang=$abbrLang]/abbrDefinition/*" mode="Use"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-\- a language is specified, but this abbreviation does not have anything; try using the default;
                            this assumes that something is better than nothing -\->
                        <xsl:apply-templates select="exsl:node-set($abbr)/abbrInLang[1]/abbrDefinition/text() | exsl:node-set($abbr)/abbrInLang[1]/abbrDefinition/*" mode="Use"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <!-\-  no language specified; just use the first one -\->
                <xsl:apply-templates select="exsl:node-set($abbr)/abbrInLang[1]/abbrDefinition/text() | exsl:node-set($abbr)/abbrInLang[1]/abbrDefinition/*"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>-->
    <!--
        OutputAbbrTerm
    -->
    <xsl:template name="OutputAbbrTerm">
        <xsl:param name="abbr"/>
        <tex:group>
            <xsl:if test="exsl:node-set($abbreviations)/@usesmallcaps='yes' and not(exsl:node-set($abbreviations)/@font-variant='small-caps')">
                <tex:cmd name="fontspec">
                    <tex:opt>Scale=0.65</tex:opt>
                    <tex:parm>
                        <xsl:variable name="closestGlossOrObjectWithAFontFamily">
                            <xsl:for-each select="ancestor::object">
                                <xsl:sort order="descending"/>
                                <xsl:for-each select="key('TypeID',@type)">
                                    <xsl:if test="string-length(@font-family) &gt; 0">
                                        <xsl:value-of select="@font-family"/>
                                        <xsl:text>|</xsl:text>
                                    </xsl:if>
                                </xsl:for-each>
                            </xsl:for-each>
                            <xsl:for-each select="ancestor::gloss">
                                <xsl:sort order="descending"/>
                                <xsl:for-each select="key('LanguageID',@lang)">
                                    <xsl:if test="string-length(@font-family) &gt; 0">
                                        <xsl:value-of select="@font-family"/>
                                        <xsl:text>|</xsl:text>
                                    </xsl:if>
                                </xsl:for-each>
                            </xsl:for-each>
                        </xsl:variable>
                        <xsl:choose>
                            <xsl:when test="string-length($closestGlossOrObjectWithAFontFamily) &gt; 0">
                                <xsl:value-of select="substring-before($closestGlossOrObjectWithAFontFamily,'|')"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="$sDefaultFontFamily"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </tex:parm>
                </tex:cmd>
                <xsl:call-template name="HandleSmallCapsBegin"/>
            </xsl:if>
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="$abbreviations"/>
                <xsl:with-param name="ignoreFontFamily">
                    <xsl:choose>
                        <xsl:when test="exsl:node-set($abbr)/@ignoreabbreviationsfontfamily='yes'">
                            <xsl:text>Y</xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>N</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:with-param>
            </xsl:call-template>
            <xsl:choose>
                <xsl:when test="string-length($abbrLang) &gt; 0">
                    <xsl:choose>
                        <xsl:when test="string-length(exsl:node-set($abbr)//abbrInLang[@lang=$abbrLang]/abbrTerm) &gt; 0">
                            <xsl:apply-templates select="exsl:node-set($abbr)/abbrInLang[@lang=$abbrLang]/abbrTerm" mode="Use"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <!-- a language is specified, but this abbreviation does not have anything; try using the default;
                                this assumes that something is better than nothing -->
                            <xsl:apply-templates select="exsl:node-set($abbr)/abbrInLang[1]/abbrTerm" mode="Use"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                    <!--  no language specified; just use the first one -->
                    <xsl:apply-templates select="exsl:node-set($abbr)/abbrInLang[1]/abbrTerm" mode="Use"/>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="$abbreviations"/>
                <xsl:with-param name="ignoreFontFamily">
                    <xsl:choose>
                        <xsl:when test="exsl:node-set($abbr)/@ignoreabbreviationsfontfamily='yes'">
                            <xsl:text>Y</xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>N</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:with-param>
            </xsl:call-template>
            <xsl:if test="exsl:node-set($abbreviations)/@usesmallcaps='yes' and not(exsl:node-set($abbreviations)/@font-variant='small-caps')">
                <xsl:call-template name="HandleSmallCapsEnd"/>
            </xsl:if>
        </tex:group>
    </xsl:template>
    <!--
        OutputBackgroundColor
    -->
    <xsl:template name="OutputBackgroundColor">
        <xsl:param name="bIsARow" select="'N'"/>
        <xsl:if test="string-length(@backgroundcolor) &gt; 0">
            <xsl:variable name="sKind">
                <xsl:choose>
                    <xsl:when test="$bIsARow='Y'">
                        <xsl:text>rowcolor</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>columncolor</xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:if test="$bIsARow='N'">
                <tex:spec cat="gt"/>
                <tex:spec cat="bg"/>
            </xsl:if>
            <tex:cmd name="{$sKind}">
                <tex:opt>rgb</tex:opt>
                <tex:parm>
                    <xsl:call-template name="GetColorDecimalCodesFromHexCode">
                        <xsl:with-param name="sColorHexCode">
                            <xsl:call-template name="GetColorHexCode">
                                <xsl:with-param name="sColor" select="@backgroundcolor"/>
                            </xsl:call-template>
                        </xsl:with-param>
                    </xsl:call-template>
                </tex:parm>
            </tex:cmd>
            <xsl:if test="$bIsARow='N'">
                <tex:spec cat="eg"/>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        OutputComment
    -->
    <xsl:template name="OutputComment">
        <tex:spec cat="bg"/>
        <tex:cmd name="colorbox">
            <tex:opt>rgb</tex:opt>
            <tex:parm>
                <xsl:call-template name="GetColorDecimalCodesFromHexCode">
                    <xsl:with-param name="sColorHexCode">
                        <xsl:call-template name="GetColorHexCode">
                            <xsl:with-param name="sColor" select="'yellow'"/>
                        </xsl:call-template>
                    </xsl:with-param>
                </xsl:call-template>
            </tex:parm>
            <tex:spec cat="bg"/>
        </tex:cmd>
        <xsl:text>[[</xsl:text>
        <tex:spec cat="eg"/>
        <xsl:apply-templates/>
        <tex:cmd name="colorbox">
            <tex:opt>rgb</tex:opt>
            <tex:parm>
                <xsl:call-template name="GetColorDecimalCodesFromHexCode">
                    <xsl:with-param name="sColorHexCode">
                        <xsl:call-template name="GetColorHexCode">
                            <xsl:with-param name="sColor" select="'yellow'"/>
                        </xsl:call-template>
                    </xsl:with-param>
                </xsl:call-template>
            </tex:parm>
            <tex:spec cat="bg"/>
        </tex:cmd>
        <!--        <xsl:apply-templates/>-->
        <xsl:text>]]</xsl:text>
        <tex:spec cat="eg"/>
        <tex:spec cat="eg"/>
    </xsl:template>
    <!--  
        OutputFontAttributes
    -->
    <xsl:template name="OutputFontAttributes">
        <xsl:param name="language"/>
        <xsl:param name="originalContext"/>
        <xsl:param name="bIsOverride" select="'N'"/>
        <xsl:param name="ignoreFontFamily" select="'N'"/>
        <!-- unsuccessful attempt at dealing with "normal" to override inherited values 
            <xsl:param name="bCloseOffParent" select="'Y'"/>
            <xsl:if test="$bCloseOffParent='Y'">
            <xsl:variable name="myParent" select="parent::langData"/>
            <xsl:if test="$myParent">
            <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="key('LanguageID',exsl:node-set($myParent)/@lang)"/>
            <xsl:with-param name="bStartParent" select="'N'"/>
            </xsl:call-template>
            </xsl:if>
            </xsl:if>
        -->
        <xsl:variable name="sFontFamily" select="normalize-space(exsl:node-set($language)/@font-family)"/>
        <xsl:if test="string-length($sFontFamily) &gt; 0 and $ignoreFontFamily='N'">
            <xsl:if test="ancestor::definition or ancestor::example and ancestor::endnote or ancestor::interlinear-text and ancestor::endnote">
                <tex:spec cat="bg"/>
            </xsl:if>
            <xsl:call-template name="HandleFontFamily">
                <xsl:with-param name="language" select="$language"/>
                <xsl:with-param name="sFontFamily" select="$sFontFamily"/>
                <xsl:with-param name="bIsOverride" select="$bIsOverride"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:variable name="sFontSize" select="normalize-space(exsl:node-set($language)/@font-size)"/>
        <xsl:if test="string-length($sFontSize) &gt; 0">
            <tex:spec cat="bg"/>
            <xsl:call-template name="HandleFontSize">
                <xsl:with-param name="sSize" select="$sFontSize"/>
                <xsl:with-param name="sFontFamily" select="exsl:node-set($language)/@font-family"/>
                <xsl:with-param name="language" select="$language"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:variable name="sFontStyle" select="normalize-space(exsl:node-set($language)/@font-style)"/>
        <xsl:if test="string-length($sFontStyle) &gt; 0">
            <xsl:choose>
                <xsl:when test="$sFontStyle='italic'">
                    <tex:spec cat="esc"/>
                    <xsl:text>textit</xsl:text>
                    <tex:spec cat="bg"/>
                </xsl:when>
                <xsl:when test="$sFontStyle='oblique'">
                    <tex:spec cat="esc"/>
                    <xsl:text>textsl</xsl:text>
                    <tex:spec cat="bg"/>
                </xsl:when>
                <xsl:when test="$sFontStyle='normal'">
                    <tex:spec cat="esc"/>
                    <xsl:text>textup</xsl:text>
                    <tex:spec cat="bg"/>
                </xsl:when>
                <xsl:otherwise>
                    <!-- use italic as default -->
                    <tex:spec cat="esc"/>
                    <xsl:text>textit</xsl:text>
                    <tex:spec cat="bg"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:variable name="sFontVariant" select="normalize-space(exsl:node-set($language)/@font-variant)"/>
        <xsl:if test="string-length($sFontVariant) &gt; 0">
            <xsl:choose>
                <xsl:when test="$sFontVariant='small-caps'">
                    <xsl:if test="not($originalContext and exsl:node-set($originalContext)[descendant::abbrRef])">
                        <xsl:if test="string-length($sFontSize)=0">
                            <xsl:call-template name="HandleFontSize">
                                <xsl:with-param name="sSize" select="'65%'"/>
                                <xsl:with-param name="sFontFamily" select="$sFontFamily"/>
                                <xsl:with-param name="language" select="$language"/>
                            </xsl:call-template>
                        </xsl:if>
                        <xsl:call-template name="HandleSmallCapsBegin"/>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="$sFontStyle='italic'">
                    <!-- do nothing; we do not want to turn off the italic by using a normal -->
                </xsl:when>
                <xsl:when test="$sFontStyle='normal'">
                    <tex:spec cat="esc"/>
                    <xsl:text>textup</xsl:text>
                    <tex:spec cat="bg"/>
                </xsl:when>
                <xsl:otherwise>
                    <!-- only allow small caps -->
                    <!-- following does more than use normal - it also uses the main font
                        <tex:spec cat="esc"/>
                        <xsl:text>textnormal</xsl:text>
                        <tex:spec cat="bg"/> -->
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:variable name="sFontWeight" select="normalize-space(exsl:node-set($language)/@font-weight)"/>
        <xsl:if test="string-length($sFontWeight) &gt; 0">
            <xsl:choose>
                <xsl:when test="$sFontWeight='bold'">
                    <tex:spec cat="esc"/>
                    <xsl:text>textbf</xsl:text>
                    <tex:spec cat="bg"/>
                </xsl:when>
                <xsl:when test="$sFontStyle='italic'">
                    <!-- do nothing - we do *not* want to do a 'normal' or we'll cancel the italic -->
                </xsl:when>
                <xsl:when test="$sFontWeight='normal'">
                    <tex:spec cat="esc"/>
                    <xsl:text>textmd</xsl:text>
                    <tex:spec cat="bg"/>
                </xsl:when>
                <xsl:otherwise>
                    <!-- use bold as default -->
                    <tex:spec cat="esc"/>
                    <xsl:text>textbf</xsl:text>
                    <tex:spec cat="bg"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:variable name="sFontColor" select="normalize-space(exsl:node-set($language)/@color)"/>
        <xsl:if test="string-length($sFontColor) &gt; 0">
            <xsl:call-template name="DoColor">
                <xsl:with-param name="sFontColor" select="$sFontColor"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:variable name="sBackgroundColor" select="normalize-space(exsl:node-set($language)/@backgroundcolor)"/>
        <!-- we do not allow background color for titles; PDF fails to be produced -->
        <xsl:if test="not(name()='type') and  string-length($sBackgroundColor) &gt; 0 and not(exsl:node-set($language)/@usetitleinheader)">
            <xsl:for-each select="$language">
                <tex:spec cat="bg"/>
                <tex:cmd name="colorbox">
                    <tex:opt>rgb</tex:opt>
                    <tex:parm>
                        <xsl:call-template name="GetColorDecimalCodesFromHexCode">
                            <xsl:with-param name="sColorHexCode">
                                <xsl:call-template name="GetColorHexCode">
                                    <xsl:with-param name="sColor" select="@backgroundcolor"/>
                                </xsl:call-template>
                            </xsl:with-param>
                        </xsl:call-template>
                    </tex:parm>
                    <tex:spec cat="bg"/>
                </tex:cmd>
            </xsl:for-each>
        </xsl:if>
        <xsl:call-template name="OutputTextTransform">
            <xsl:with-param name="sTextTransform" select="normalize-space(exsl:node-set($language)/@text-transform)"/>
            <xsl:with-param name="originalContext" select="$originalContext"/>
        </xsl:call-template>
        <xsl:call-template name="OutputTypeAttributes">
            <xsl:with-param name="sList" select="exsl:node-set($language)/@XeLaTeXSpecial"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        OutputFontAttributesBracketsOnly
    -->
    <xsl:template name="OutputFontAttributesBracketsOnly">
        <xsl:param name="language"/>
        <xsl:call-template name="OutputTypeAttributesEnd">
            <xsl:with-param name="sList" select="exsl:node-set($language)/@XeLaTeXSpecial"/>
        </xsl:call-template>
        <xsl:variable name="sFontFamily" select="normalize-space(exsl:node-set($language)/@font-family)"/>
        <xsl:if test="string-length($sFontFamily) &gt; 0">
            <tex:spec cat="bg"/>
        </xsl:if>
        <xsl:variable name="sFontStyle" select="normalize-space(exsl:node-set($language)/@font-style)"/>
        <xsl:if test="string-length($sFontStyle) &gt; 0">
            <xsl:if test="$sFontStyle='italic' or $sFontStyle='normal'">
                <tex:spec cat="bg"/>
            </xsl:if>
        </xsl:if>
        <xsl:variable name="sFontVariant" select="normalize-space(exsl:node-set($language)/@font-variant)"/>
        <xsl:if test="string-length($sFontVariant) &gt; 0">
            <xsl:choose>
                <xsl:when test="$sFontVariant='small-caps'">
                    <xsl:call-template name="HandleSmallCapsBracketsOnly"/>
                </xsl:when>
                <xsl:when test="$sFontStyle='italic'">
                    <!-- do nothing; we do not want to turn off the italic by using a normal -->
                </xsl:when>
                <xsl:when test="$sFontStyle='normal'">
                    <tex:spec cat="bg"/>
                </xsl:when>
                <xsl:otherwise>
                    <!-- doing nothing currenlty -->
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:variable name="sFontWeight" select="normalize-space(exsl:node-set($language)/@font-weight)"/>
        <xsl:if test="string-length($sFontWeight) &gt; 0">
            <xsl:choose>
                <xsl:when test="$sFontStyle='italic' and $sFontWeight!='bold'">
                    <!-- do nothing - we do *not* want to do a 'normal' or we'll cancel the italic -->
                </xsl:when>
                <xsl:when test="$sFontWeight='normal'">
                    <tex:spec cat="bg"/>
                </xsl:when>
                <xsl:otherwise>
                    <tex:spec cat="bg"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:variable name="sFontColor" select="normalize-space(exsl:node-set($language)/@color)"/>
        <xsl:if test="string-length($sFontColor) &gt; 0">
            <tex:spec cat="bg"/>
        </xsl:if>
    </xsl:template>
    <!--  
        OutputFontAttributesEnd
    -->
    <xsl:template name="OutputFontAttributesEnd">
        <xsl:param name="language"/>
        <xsl:param name="originalContext"/>
        <xsl:param name="ignoreFontFamily" select="'N'"/>
        <!-- unsuccessful attempt at dealing with "normal" to override inherited values 
            <xsl:param name="bStartParent" select="'Y'"/>
        -->
        <xsl:call-template name="OutputTypeAttributesEnd">
            <xsl:with-param name="sList" select="exsl:node-set($language)/@XeLaTeXSpecial"/>
        </xsl:call-template>
        <xsl:call-template name="OutputTextTransformEnd">
            <xsl:with-param name="sTextTransform" select="normalize-space(exsl:node-set($language)/@text-transform)"/>
            <xsl:with-param name="originalContext" select="$originalContext"/>
        </xsl:call-template>
        <xsl:variable name="sBackgroundColor" select="normalize-space(exsl:node-set($language)/@backgroundcolor)"/>
        <!-- we do not allow background color for titles; PDF fails to be produced -->
        <xsl:if test="not(name()='type') and  string-length($sBackgroundColor) &gt; 0 and not(exsl:node-set($language)/@usetitleinheader)">
            <tex:spec cat="eg"/>
            <tex:spec cat="eg"/>
        </xsl:if>
        <xsl:variable name="sFontFamily" select="normalize-space(exsl:node-set($language)/@font-family)"/>
        <xsl:if test="string-length($sFontFamily) &gt; 0 and $ignoreFontFamily='N'">
            <tex:spec cat="eg"/>
            <xsl:if test="ancestor::definition or ancestor::example and ancestor::endnote or ancestor::interlinear-text and ancestor::endnote">
                <tex:spec cat="eg"/>
            </xsl:if>
        </xsl:if>
        <xsl:variable name="sFontSize" select="normalize-space(exsl:node-set($language)/@font-size)"/>
        <xsl:if test="string-length($sFontSize) &gt; 0">
            <tex:spec cat="eg"/>
        </xsl:if>
        <xsl:variable name="sFontStyle" select="normalize-space(exsl:node-set($language)/@font-style)"/>
        <xsl:if test="string-length($sFontStyle) &gt; 0">
            <tex:spec cat="eg"/>
        </xsl:if>
        <xsl:variable name="sFontVariant" select="normalize-space(exsl:node-set($language)/@font-variant)"/>
        <xsl:if test="string-length($sFontVariant) &gt; 0">
            <xsl:choose>
                <xsl:when test="$sFontVariant='small-caps'">
                    <xsl:if test="not($originalContext  and exsl:node-set($originalContext)[descendant::abbrRef])">
                        <xsl:call-template name="HandleSmallCapsEnd"/>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="$sFontStyle='italic'">
                    <!-- do nothing; we do not want to turn off the italic by using a normal -->
                </xsl:when>
                <xsl:when test="$sFontStyle='normal'">
                    <tex:spec cat="eg"/>
                </xsl:when>
                <xsl:otherwise>
                    <!-- doing nothing currenlty -->
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:variable name="sFontWeight" select="normalize-space(exsl:node-set($language)/@font-weight)"/>
        <xsl:if test="string-length($sFontWeight) &gt; 0">
            <xsl:choose>
                <xsl:when test="$sFontStyle='italic' and $sFontWeight!='bold'">
                    <!-- do nothing - we do *not* want to do a 'normal' or we'll cancel the italic -->
                </xsl:when>
                <xsl:when test="$sFontWeight='normal'">
                    <tex:spec cat="eg"/>
                </xsl:when>
                <xsl:otherwise>
                    <tex:spec cat="eg"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:variable name="sFontColor" select="normalize-space(exsl:node-set($language)/@color)"/>
        <xsl:if test="string-length($sFontColor) &gt; 0">
            <tex:spec cat="eg"/>
        </xsl:if>
        <!-- unsuccessful attempt at dealing with "normal" to override inherited values 
            <xsl:if test="$bStartParent='Y'">
            <xsl:variable name="myParent" select="parent::langData"/>
            <xsl:if test="$myParent">
            <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="key('LanguageID',exsl:node-set($myParent)/@lang)"/>
            <xsl:with-param name="bCloseOffParent" select="'N'"/>
            </xsl:call-template>
            </xsl:if>
            </xsl:if>
        -->
    </xsl:template>
    <!--
        OutputGlossaryTerm
    -->
    <xsl:template name="OutputGlossaryTerm">
        <xsl:param name="glossaryTerm"/>
        <xsl:param name="bIsRef" select="'Y'"/>
        <xsl:param name="glossaryTermRef"/>
        <xsl:param name="kind" select="'Table'"/>
        <xsl:variable name="fontInfoToUse">
            <xsl:choose>
                <xsl:when test="$kind='DefinitionList'">
                    <xsl:variable name="stylesheetInfo" select="exsl:node-set($contentLayoutInfo)/glossaryTermsInDefinitionListLayout/glossaryTermTermInDefinitionListLayout"/>
                    <xsl:choose>
                        <xsl:when test="$stylesheetInfo">
                            <xsl:copy-of select="$stylesheetInfo"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:copy-of select="$glossaryTerms"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:copy-of select="$glossaryTerms"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <tex:group>
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="exsl:node-set($fontInfoToUse)/*"/>
                <xsl:with-param name="ignoreFontFamily">
                    <xsl:choose>
                        <xsl:when test="exsl:node-set($glossaryTerm)/@ignoreglossarytermsfontfamily='yes'">
                            <xsl:text>Y</xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>N</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:with-param>
            </xsl:call-template>
            <xsl:call-template name="OutputGlossaryTermContentInContext">
                <xsl:with-param name="glossaryTerm" select="$glossaryTerm"/>
                <xsl:with-param name="bIsRef" select="$bIsRef"/>
                <xsl:with-param name="glossaryTermRef" select="$glossaryTermRef"/>
            </xsl:call-template>
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="exsl:node-set($fontInfoToUse)/*"/>
            </xsl:call-template>
        </tex:group>
    </xsl:template>
    <!--
        OutputGlossaryTermInDefinitionList
    -->
    <xsl:template name="OutputGlossaryTermInDefinitionList">
        <xsl:param name="glossaryTermsShownHere"/>
        <xsl:variable name="defnListLayout" select="exsl:node-set($contentLayoutInfo)/glossaryTermsInDefinitionListLayout"/>
        <xsl:variable name="sThisHangingIndent" select="normalize-space(exsl:node-set($defnListLayout)/@hangingIndentNormalIndent)"/>
        <xsl:variable name="sThisInitialIndent" select="normalize-space(exsl:node-set($defnListLayout)/@hangingIndentInitialIndent)"/>
        <xsl:if test="contains(@XeLaTeXSpecial,'clearpage')">
            <tex:cmd name="clearpage" gr="0" nl2="0"/>
        </xsl:if>
        <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak')">
            <tex:cmd name="pagebreak" gr="0" nl2="0"/>
        </xsl:if>
        <tex:spec cat="bg"/>
        <tex:cmd name="hangafter" gr="0"/>
        <xsl:text>1</xsl:text>
        <tex:cmd name="relax" gr="0" nl2="1"/>
        <tex:cmd name="hangindent" gr="0"/>
        <xsl:choose>
            <xsl:when test="string-length($sThisHangingIndent) &gt; 0">
                <xsl:value-of select="$sThisHangingIndent"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sParagraphIndent"/>
            </xsl:otherwise>
        </xsl:choose>
        <tex:cmd name="relax" gr="0" nl2="1"/>
        <xsl:choose>
            <xsl:when test="string-length($sThisInitialIndent) &gt; 0">
                <tex:cmd name="parindent" gr="0"/>
                <xsl:value-of select="$sThisInitialIndent"/>
                <tex:cmd name="indent"/>
            </xsl:when>
            <xsl:otherwise>
                <tex:cmd name="noindent"/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="OutputGlossaryTermItemAsDefinitionList">
            <xsl:with-param name="glossaryTermsShownHere" select="$glossaryTermsShownHere"/>
        </xsl:call-template>
        <tex:cmd name="par" nl2="1"/>
        <xsl:variable name="sSpaceBetween" select="normalize-space(exsl:node-set($defnListLayout)/@spaceBetweenParagraphs)"/>
        <xsl:if test="string-length($sSpaceBetween) &gt; 0">
            <tex:cmd name="vspace">
                <tex:parm>
                    <xsl:value-of select="$sSpaceBetween"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <tex:spec cat="eg"/>
    </xsl:template>
    <!--
        OutputGlossaryTermInTable
    -->
    <xsl:template name="OutputGlossaryTermInTable">
        <xsl:param name="glossaryTermsShownHere"/>
        <xsl:param name="glossaryTermInSecondColumn"/>

        <xsl:call-template name="OutputGlossaryTermItemInTable">
            <xsl:with-param name="glossaryTermsShownHere" select="$glossaryTermsShownHere"/>
        </xsl:call-template>
        <xsl:if test="exsl:node-set($contentLayoutInfo)/glossaryTermsInTableLayout/@useDoubleColumns='yes'">
            <tex:spec cat="align"/>
            <xsl:for-each select="$glossaryTermInSecondColumn">
                <xsl:call-template name="OutputGlossaryTermItemInTable">
                    <xsl:with-param name="glossaryTermsShownHere" select="$glossaryTermsShownHere"/>
                </xsl:call-template>
            </xsl:for-each>
        </xsl:if>
        <tex:spec cat="esc"/>
        <tex:spec cat="esc" nl2="1"/>
    </xsl:template>
    <!--
        OutputGlossaryTermItemInTable
    -->
    <xsl:template name="OutputGlossaryTermItemAsDefinitionList">
        <xsl:param name="glossaryTermsShownHere"/>
        <xsl:variable name="defnListLayout" select="exsl:node-set($contentLayoutInfo)/glossaryTermsInDefinitionListLayout"/>
        <xsl:call-template name="DoInternalTargetBegin">
            <xsl:with-param name="sName" select="@id"/>
        </xsl:call-template>
        <xsl:variable name="sBefore" select="exsl:node-set($defnListLayout)/glossaryTermTermInDefinitionListLayout/@textbefore"/>
        <xsl:if test="string-length($sBefore) &gt; 0">
            <xsl:value-of select="$sBefore"/>
        </xsl:if>
        <xsl:call-template name="OutputGlossaryTerm">
            <xsl:with-param name="glossaryTerm" select="."/>
            <xsl:with-param name="bIsRef" select="'N'"/>
            <xsl:with-param name="kind" select="'DefinitionList'"/>
        </xsl:call-template>
        <xsl:call-template name="DoInternalTargetEnd"/>
        <xsl:variable name="sAfter" select="exsl:node-set($defnListLayout)/glossaryTermTermInDefinitionListLayout/@textafter"/>
        <xsl:choose>
            <xsl:when test="string-length($sAfter) &gt; 0">
                <xsl:value-of select="$sAfter"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>: </xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:variable name="sDefnColor" select="normalize-space(exsl:node-set($defnListLayout)/glossaryTermDefinitionInDefinitionListLayout/@color)"/>
        <xsl:if test="string-length($sDefnColor) &gt; 0">
            <tex:cmd name="definecolor">
                <tex:parm>defnColor</tex:parm>
                <tex:parm>rgb</tex:parm>
                <tex:parm>
                    <xsl:call-template name="GetColorDecimalCodesFromHexCode">
                        <xsl:with-param name="sColorHexCode">
                            <xsl:call-template name="GetColorHexCode">
                                <xsl:with-param name="sColor" select="$sDefnColor"/>
                            </xsl:call-template>
                        </xsl:with-param>
                    </xsl:call-template>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="hypersetup">
                <tex:parm>linkcolor=defnColor</tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="exsl:node-set($defnListLayout)/glossaryTermDefinitionInDefinitionListLayout"/>
        </xsl:call-template>
        <xsl:variable name="sBeforeDefn" select="exsl:node-set($defnListLayout)/glossaryTermDefinitionInDefinitionListLayout/@textbefore"/>
        <xsl:if test="string-length($sBeforeDefn) &gt; 0">
            <xsl:value-of select="$sBeforeDefn"/>
        </xsl:if>
        <xsl:call-template name="OutputGlossaryTermDefinition">
            <xsl:with-param name="glossaryTerm" select="."/>
        </xsl:call-template>
        <xsl:variable name="sAfterDefn" select="exsl:node-set($defnListLayout)/glossaryTermDefinitionInDefinitionListLayout/@textafter"/>
        <xsl:if test="string-length($sAfterDefn) &gt; 0">
            <xsl:value-of select="$sAfterDefn"/>
        </xsl:if>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="exsl:node-set($defnListLayout)/glossaryTermDefinitionInDefinitionListLayout"/>
        </xsl:call-template>
        <xsl:if test="string-length($sDefnColor) &gt; 0">
            <tex:cmd name="hypersetup">
                <tex:parm>linkcolor=black</tex:parm>
            </tex:cmd>
        </xsl:if>
    </xsl:template>
    <!--
        OutputGlossaryTermItemInTable
    -->
    <xsl:template name="OutputGlossaryTermItemInTable">
        <xsl:param name="glossaryTermsShownHere"/>
        <xsl:call-template name="DoInternalTargetBegin">
            <xsl:with-param name="sName" select="@id"/>
        </xsl:call-template>
        <xsl:call-template name="OutputGlossaryTerm">
            <xsl:with-param name="glossaryTerm" select="."/>
            <xsl:with-param name="bIsRef" select="'N'"/>
        </xsl:call-template>
        <xsl:call-template name="DoInternalTargetEnd"/>
        <tex:spec cat="align"/>
        <xsl:if test="not(exsl:node-set($contentLayoutInfo)/glossaryTermsInTableLayout/@useEqualSignsColumn) or exsl:node-set($contentLayoutInfo)/glossaryTermsInTableLayout/@useEqualSignsColumn!='no'">
            <xsl:text> = </xsl:text>
            <tex:spec cat="align"/>
        </xsl:if>
        <xsl:call-template name="OutputGlossaryTermDefinition">
            <xsl:with-param name="glossaryTerm" select="."/>
        </xsl:call-template>
    </xsl:template>
    <!--
        OutputGlossaryTermsAsDefinitionList
    -->
    <xsl:template name="OutputGlossaryTermsAsDefinitionList">
        <xsl:param name="glossaryTermsUsed"
            select="//glossaryTerm[not(ancestor::chapterInCollection/backMatter/glossaryTerms)][//glossaryTermRef[not(ancestor::chapterInCollection/backMatter/glossaryTerms)]/@glossaryTerm=@id]"/>
        <xsl:if test="count($glossaryTermsUsed) &gt; 0">
            <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacetables='yes' and exsl:node-set($contentLayoutInfo)/glossaryTermsInDefinitionListLayout/@useSingleSpacing!='no'">
                <tex:spec cat="bg"/>
                <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
            </xsl:if>
            <tex:spec cat="bg"/>
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/glossaryTermsInDefinitionListLayout"/>
            </xsl:call-template>
            <xsl:call-template name="SortGlossaryTermsAsDefinitionList">
                <xsl:with-param name="glossaryTermsUsed" select="$glossaryTermsUsed"/>
            </xsl:call-template>
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/glossaryTermsInDefinitionListLayout"/>
            </xsl:call-template>
            <tex:spec cat="eg"/>
            <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacetables='yes' and exsl:node-set($contentLayoutInfo)/glossaryTermsInDefinitionListLayout/@useSingleSpacing!='no'">
                <tex:spec cat="eg"/>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--
        OutputGlossaryTermsInTable
    -->
    <xsl:template name="OutputGlossaryTermsInTable">
        <xsl:param name="glossaryTermsUsed"
            select="//glossaryTerm[not(ancestor::chapterInCollection/backMatter/glossaryTerms)][//glossaryTermRef[not(ancestor::chapterInCollection/backMatter/glossaryTerms)]/@glossaryTerm=@id]"/>
        <xsl:if test="count($glossaryTermsUsed) &gt; 0">
            <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacetables='yes' and exsl:node-set($contentLayoutInfo)/glossaryTermsInTableLayout/@useSingleSpacing!='no'">
                <tex:spec cat="bg"/>
                <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
            </xsl:if>
            <tex:spec cat="bg"/>
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/glossaryTermsInTableLayout"/>
            </xsl:call-template>
            <tex:env name="longtable">
                <tex:opt>l</tex:opt>
                <tex:parm>
                    <xsl:text>@</xsl:text>
                    <tex:group>
                        <tex:cmd name="hspace*">
                            <tex:parm>
                                <xsl:variable name="sStartIndent" select="normalize-space(exsl:node-set($contentLayoutInfo)/glossaryTermsInTableLayout/@start-indent)"/>
                                <xsl:choose>
                                    <xsl:when test="string-length($sStartIndent)&gt;0">
                                        <xsl:value-of select="$sStartIndent"/>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <tex:cmd name="parindent" gr="0" nl2="0"/>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </tex:parm>
                        </tex:cmd>
                    </tex:group>
                    <xsl:call-template name="HandleGlossaryTermsInTableColumnSpecColumns"/>
                    <xsl:if test="exsl:node-set($contentLayoutInfo)/glossaryTermsInTableLayout/@useDoubleColumns='yes'">
                        <xsl:text>@</xsl:text>
                        <tex:group>
                            <tex:cmd name="hspace*">
                                <tex:parm>
                                    <xsl:variable name="sSep" select="normalize-space(exsl:node-set($contentLayoutInfo)/glossaryTermsInTableLayout/@doubleColumnSeparation)"/>
                                    <xsl:choose>
                                        <xsl:when test="string-length($sSep)&gt;0">
                                            <xsl:value-of select="$sSep"/>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <tex:cmd name="parindent" gr="0" nl2="0"/>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </tex:parm>
                            </tex:cmd>
                        </tex:group>
                        <xsl:call-template name="HandleGlossaryTermsInTableColumnSpecColumns"/>
                    </xsl:if>
                </tex:parm>
                <!--  I'm not happy with how this poor man's attempt at getting double column works when there are long definitions.
                    The table column widths may be long and short; if a cell in the second row needs to lap over a line, then the
                    corresponding cell in the other column may skip a row (as far as what one would expect).
                    So I'm going with just a single table here.
                    <xsl:variable name="iHalfwayPoint" select="ceiling(count($abbrsUsed) div 2)"/>
                    <xsl:for-each select="exsl:node-set($abbrsUsed)[position() &lt;= $iHalfwayPoint]">
                -->
                <xsl:call-template name="SortGlossaryTermsInTable">
                    <xsl:with-param name="glossaryTermsUsed" select="$glossaryTermsUsed"/>
                </xsl:call-template>
            </tex:env>
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/glossaryTermsInTableLayout"/>
            </xsl:call-template>
            <tex:spec cat="eg"/>
            <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacetables='yes' and exsl:node-set($contentLayoutInfo)/glossaryTermsInTableLayout/@useSingleSpacing!='no'">
                <tex:spec cat="eg"/>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--
        OutputIndexedItemsRange
    -->
    <xsl:template name="OutputIndexedItemsRange">
        <xsl:param name="sIndexedItemID"/>
        <xsl:variable name="sPage" select="document($sIndexFile)/idx/indexitem[@ref=$sIndexedItemID]/@page"/>
        <xsl:call-template name="OutputIndexedItemsPageNumber">
            <xsl:with-param name="sIndexedItemID" select="$sIndexedItemID"/>
            <xsl:with-param name="sPage" select="$sPage"/>
        </xsl:call-template>
        <xsl:if test="beginId">
            <xsl:variable name="sBeginId" select="beginId"/>
            <xsl:for-each select="exsl:node-set($lingPaper)//indexedRangeEnd[@begin=$sBeginId][not(ancestor::comment)][1]">
                <!-- only use first one because that's all there should be -->
                <xsl:variable name="sIndexedRangeEndID">
                    <xsl:call-template name="CreateIndexedItemID">
                        <xsl:with-param name="sTermId" select="@begin"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:variable name="sEndPage" select="document($sIndexFile)/idx/indexitem[@ref=$sIndexedRangeEndID]/@page"/>
                <xsl:if test="$sPage != $sEndPage">
                    <xsl:text>-</xsl:text>
                    <xsl:call-template name="OutputIndexedItemsPageNumber">
                        <xsl:with-param name="sIndexedItemID" select="$sIndexedRangeEndID"/>
                        <xsl:with-param name="sPage" select="$sEndPage"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <!--  
        OutputIndexTerms
    -->
    <xsl:template name="OutputIndexTerms">
        <xsl:param name="sIndexKind"/>
        <xsl:param name="lang"/>
        <xsl:param name="terms"/>
        <xsl:variable name="indexTermsToShow" select="exsl:node-set($terms)/indexTerm[@kind=$sIndexKind or @kind='subject' and $sIndexKind='common' or count(//index)=1]"/>
        <xsl:if test="$indexTermsToShow">
            <xsl:variable name="iIndent" select="count(exsl:node-set($terms)/ancestor::*[name()='indexTerm']) * .125"/>
            <xsl:for-each select="$indexTermsToShow">
                <!--                <xsl:sort select="term[1]"/>-->
                <xsl:sort lang="{$lang}" select="term[@lang=$lang or position()=1 and not (following-sibling::term[@lang=$lang])]"/>
                <xsl:variable name="sTermId" select="@id"/>
                <!-- if a nested index term is cited, we need to be sure to show its parents, even if they are not cited -->
                <xsl:variable name="bHasCitedDescendant">
                    <xsl:for-each select="descendant::indexTerm">
                        <xsl:variable name="sDescendantTermId" select="@id"/>
                        <xsl:if test="//indexedItem[@term=$sDescendantTermId][not(ancestor::comment)] or //indexedRangeBegin[@term=$sDescendantTermId][not(ancestor::comment)]">
                            <xsl:text>Y</xsl:text>
                        </xsl:if>
                        <xsl:if test="@see">
                            <xsl:call-template name="CheckSeeTargetIsCitedOrItsDescendantIsCited"/>
                        </xsl:if>
                    </xsl:for-each>
                </xsl:variable>
                <xsl:variable name="indexedItems" select="//indexedItem[@term=$sTermId][not(ancestor::comment)] | //indexedRangeBegin[@term=$sTermId][not(ancestor::comment)]"/>
                <xsl:variable name="bHasSeeAttribute">
                    <xsl:if test="string-length(@see) &gt; 0">
                        <xsl:text>Y</xsl:text>
                    </xsl:if>
                </xsl:variable>
                <xsl:variable name="bSeeTargetIsCitedOrItsDescendantIsCited">
                    <xsl:if test="$bHasSeeAttribute='Y'">
                        <xsl:call-template name="CheckSeeTargetIsCitedOrItsDescendantIsCited"/>
                    </xsl:if>
                </xsl:variable>
                <xsl:choose>
                    <xsl:when test="$indexedItems or contains($bHasCitedDescendant,'Y')">
                        <tex:cmd name="XLingPaperindexitem" nl2="1">
                            <tex:parm>
                                <xsl:value-of select="$iIndent"/>
                                <xsl:text>in</xsl:text>
                            </tex:parm>
                            <tex:parm>
                                <!-- this term or one its descendants is cited; show it -->
                                <xsl:call-template name="DoInternalTargetBegin">
                                    <xsl:with-param name="sName">
                                        <xsl:call-template name="CreateIndexTermID">
                                            <xsl:with-param name="sTermId" select="$sTermId"/>
                                        </xsl:call-template>
                                    </xsl:with-param>
                                </xsl:call-template>
                                <xsl:call-template name="DoInternalTargetEnd"/>
                                <xsl:call-template name="OutputIndexTermsTerm">
                                    <xsl:with-param name="lang" select="$lang"/>
                                    <xsl:with-param name="indexTerm" select="."/>
                                </xsl:call-template>
                                <xsl:if test="$indexedItems or $bHasSeeAttribute='Y' and contains($bSeeTargetIsCitedOrItsDescendantIsCited, 'Y')">
                                    <xsl:call-template name="OutputTextAfterIndexTerm"/>
                                </xsl:if>
                                <xsl:text>&#x20;&#x20;</xsl:text>
                                <!-- When a given item is on the same page more than once, we want to show only one occurrence.
                                     In addition, if one of the items on the same page is the main item, then we want to show
                                     that main item only and not the other items on that page.
                                     To do this, we create a data structure first and then run through it.
                                -->
                                <xsl:variable name="items">
                                    <xsl:for-each select="$indexedItems">
                                        <item>
                                            <xsl:variable name="sIndexedItemID">
                                                <xsl:call-template name="CreateIndexedItemID">
                                                    <xsl:with-param name="sTermId" select="$sTermId"/>
                                                </xsl:call-template>
                                            </xsl:variable>
                                            <id>
                                                <xsl:value-of select="$sIndexedItemID"/>
                                            </id>
                                            <xsl:if test="name()='indexedRangeBegin'">
                                                <beginId>
                                                    <xsl:value-of select="@id"/>
                                                </beginId>
                                            </xsl:if>
                                            <xsl:if test="@main='yes'">
                                                <main/>
                                            </xsl:if>
                                            <page>
                                                <xsl:value-of select="document($sIndexFile)/idx/indexitem[@ref=$sIndexedItemID]/@page"/>
                                            </page>
                                        </item>
                                    </xsl:for-each>
                                </xsl:variable>
                                <xsl:variable name="iTotalItems" select="count($indexedItems)"/>
                                <xsl:for-each select="saxon:node-set($items)/item">
                                    <!-- show each reference -->
                                    <xsl:variable name="sThisPage" select="string(page)"/>
                                    <xsl:variable name="itemsBeforeOnThisPage" select="preceding-sibling::item[string(page)=$sThisPage]"/>
                                    <xsl:variable name="itemsAfterOnThisPageMain" select="following-sibling::item[string(page)=$sThisPage and main]"/>
                                    <xsl:choose>
                                        <xsl:when test="$itemsBeforeOnThisPage">
                                            <!-- do nothing; already handled -->
                                        </xsl:when>
                                        <xsl:when test="$itemsAfterOnThisPageMain">
                                            <!-- there are other items on this page, but this is the main one; use it -->
                                            <xsl:if test="position()!=1">
                                                <xsl:text>, </xsl:text>
                                            </xsl:if>
                                            <xsl:variable name="iOnThisPage" select="count($itemsAfterOnThisPageMain)+1"/>
                                            <xsl:choose>
                                                <xsl:when test="$iOnThisPage &lt; $iTotalItems">
                                                    <tex:cmd name="textbf">
                                                        <tex:parm>
                                                            <xsl:call-template name="OutputIndexedItemsRange">
                                                                <xsl:with-param name="sIndexedItemID" select="exsl:node-set($itemsAfterOnThisPageMain)/id"/>
                                                            </xsl:call-template>
                                                        </tex:parm>
                                                    </tex:cmd>
                                                </xsl:when>
                                                <xsl:otherwise>
                                                    <xsl:call-template name="OutputIndexedItemsRange">
                                                        <xsl:with-param name="sIndexedItemID" select="exsl:node-set($itemsAfterOnThisPageMain)/id"/>
                                                    </xsl:call-template>
                                                </xsl:otherwise>
                                            </xsl:choose>
                                        </xsl:when>
                                        <xsl:when test="main and $iTotalItems &gt; 1">
                                            <!-- there is only this item on this page and it is main (and there are other items to show) -->
                                            <xsl:if test="position()!=1">
                                                <xsl:text>, </xsl:text>
                                            </xsl:if>
                                            <tex:cmd name="textbf">
                                                <tex:parm>
                                                    <xsl:call-template name="OutputIndexedItemsRange">
                                                        <xsl:with-param name="sIndexedItemID" select="id"/>
                                                    </xsl:call-template>
                                                </tex:parm>
                                            </tex:cmd>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <xsl:if test="position()!=1">
                                                <xsl:text>, </xsl:text>
                                            </xsl:if>
                                            <xsl:call-template name="OutputIndexedItemsRange">
                                                <xsl:with-param name="sIndexedItemID" select="id"/>
                                            </xsl:call-template>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </xsl:for-each>
                                <xsl:if test="$bHasSeeAttribute='Y' and contains($bSeeTargetIsCitedOrItsDescendantIsCited, 'Y')">
                                    <!-- this term also has a @see attribute which refers to a term that is cited or whose descendant is cited -->
                                    <tex:spec cat="esc"/>
                                    <xsl:text>textit</xsl:text>
                                    <tex:spec cat="bg"/>
                                    <xsl:call-template name="OutputIndexTermSeeBefore">
                                        <xsl:with-param name="indexedItems" select="$indexedItems"/>
                                    </xsl:call-template>
                                    <tex:spec cat="eg"/>
                                    <xsl:call-template name="DoInternalHyperlinkBegin">
                                        <xsl:with-param name="sName">
                                            <xsl:call-template name="CreateIndexTermID">
                                                <xsl:with-param name="sTermId" select="@see"/>
                                            </xsl:call-template>
                                        </xsl:with-param>
                                    </xsl:call-template>
                                    <xsl:call-template name="LinkAttributesBegin">
                                        <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/indexLinkLayout"/>
                                    </xsl:call-template>
                                    <!--<!-\-     Why this? -\->                               <xsl:apply-templates select="key('IndexTermID',@see)/term[@lang=$lang or position()=1 and not (following-sibling::term[@lang=$lang])]" mode="InIndex"/>-->
                                    <xsl:call-template name="OutputIndexTermsTermFullPath">
                                        <xsl:with-param name="lang" select="$lang"/>
                                        <xsl:with-param name="indexTerm" select="key('IndexTermID',@see)"/>
                                    </xsl:call-template>
                                    <xsl:call-template name="LinkAttributesEnd">
                                        <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/indexLinkLayout"/>
                                    </xsl:call-template>
                                    <xsl:call-template name="DoInternalHyperlinkEnd"/>
                                    <xsl:call-template name="OutputIndexTermSeeAfter">
                                        <xsl:with-param name="indexedItems" select="$indexedItems"/>
                                    </xsl:call-template>
                                </xsl:if>
                                <!--                        <tex:cmd name="par" nl2="1"/>-->
                                <xsl:call-template name="OutputIndexTerms">
                                    <xsl:with-param name="sIndexKind" select="$sIndexKind"/>
                                    <xsl:with-param name="lang" select="$lang"/>
                                    <xsl:with-param name="terms" select="indexTerms"/>
                                </xsl:call-template>
                            </tex:parm>
                        </tex:cmd>
                    </xsl:when>
                    <xsl:when test="$bHasSeeAttribute='Y' and contains($bSeeTargetIsCitedOrItsDescendantIsCited, 'Y')">
                        <!-- neither this term nor its decendants are cited, but it has a @see attribute which refers to a term that is cited or for which one of its descendants is cited -->
                        <tex:cmd name="XLingPaperindexitem" nl2="1">
                            <tex:parm>
                                <xsl:value-of select="$iIndent"/>
                                <xsl:text>in</xsl:text>
                            </tex:parm>
                            <tex:parm>
                                <!--<xsl:apply-templates select="term[1]" mode="InIndex"/>
                                    <xsl:text>&#x20;&#x20;See </xsl:text>-->
                                <xsl:apply-templates select="term[@lang=$lang or position()=1 and not (following-sibling::term[@lang=$lang])]" mode="InIndex"/>
                                <xsl:text>,</xsl:text>
                                <tex:spec cat="esc"/>
                                <xsl:text>textit</xsl:text>
                                <tex:spec cat="bg"/>
                                <xsl:call-template name="OutputIndexTermSeeAloneBefore"/>
                                <tex:spec cat="eg"/>
                                <xsl:call-template name="DoInternalHyperlinkBegin">
                                    <xsl:with-param name="sName">
                                        <xsl:call-template name="CreateIndexTermID">
                                            <xsl:with-param name="sTermId" select="@see"/>
                                        </xsl:call-template>
                                    </xsl:with-param>
                                </xsl:call-template>
                                <xsl:call-template name="LinkAttributesBegin">
                                    <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/indexLinkLayout"/>
                                </xsl:call-template>
                                <xsl:call-template name="OutputIndexTermsTermFullPath">
                                    <xsl:with-param name="lang" select="$lang"/>
                                    <xsl:with-param name="indexTerm" select="key('IndexTermID',@see)"/>
                                </xsl:call-template>
                                <xsl:call-template name="LinkAttributesEnd">
                                    <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/indexLinkLayout"/>
                                </xsl:call-template>
                                <xsl:call-template name="DoInternalHyperlinkEnd"/>
                                <xsl:text>.</xsl:text>
                            </tex:parm>
                        </tex:cmd>
                    </xsl:when>
                </xsl:choose>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <!--  
        OutputInterlinear
    -->
    <xsl:template name="OutputInterlinear">
        <xsl:param name="mode"/>
        <xsl:param name="originalContext"/>
        <xsl:choose>
            <xsl:when test="lineSet">
                <xsl:for-each select="lineSet | conflation">
                    <xsl:call-template name="ApplyTemplatesPerTextRefMode">
                        <xsl:with-param name="mode" select="$mode"/>
                        <xsl:with-param name="originalContext" select="$originalContext"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="ApplyTemplatesPerTextRefMode">
                    <xsl:with-param name="mode" select="$mode"/>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        OutputInterlinearTextReference
    -->
    <xsl:template name="OutputInterlinearTextReference">
        <xsl:param name="sRef"/>
        <xsl:param name="sSource"/>
        <xsl:if test="string-length(normalize-space($sRef)) &gt; 0 or $sSource">
            <xsl:choose>
                <xsl:when test="$sInterlinearSourceStyle='AfterFree'">
                    <tex:group>
                        <xsl:text disable-output-escaping="yes">&#xa0;&#xa0;</xsl:text>
                        <xsl:call-template name="OutputInterlinearTextReferenceContent">
                            <xsl:with-param name="sSource" select="$sSource"/>
                            <xsl:with-param name="sRef" select="$sRef"/>
                        </xsl:call-template>
                    </tex:group>
                </xsl:when>
                <xsl:otherwise>
                    <tex:cmd name="hfil" gr="0" nl2="0"/>
                    <xsl:text disable-output-escaping="yes">&#xa0;&#xa0;</xsl:text>
                    <xsl:call-template name="OutputInterlinearTextReferenceContent">
                        <xsl:with-param name="sSource" select="$sSource"/>
                        <xsl:with-param name="sRef" select="$sRef"/>
                    </xsl:call-template>
                    <xsl:if test="$sInterlinearSourceStyle='UnderFree' and $bAutomaticallyWrapInterlinears='yes'">
                        <!-- adjust for any right indent to example interlnear (not list interlinear; we handle that elsewhere -->
                        <xsl:variable name="sIndentAfter" select="normalize-space(exsl:node-set($documentLayoutInfo)/exampleLayout/@indent-after)"/>
                        <xsl:if test="not(ancestor::listInterlinear) and string-length($sIndentAfter) &gt; 0">
                            <tex:cmd name="hspace*">
                                <tex:parm>
                                    <xsl:value-of select="$sIndentAfter"/>
                                </tex:parm>
                            </tex:cmd>
                        </xsl:if>
                    </xsl:if>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--
        OutputISO639-3CodeInCommaSeparatedList
    -->
    <xsl:template name="OutputISO639-3CodeInCommaSeparatedList">
        <xsl:call-template name="DoInternalTargetBegin">
            <xsl:with-param name="sName" select="@id"/>
        </xsl:call-template>
        <xsl:value-of select="@ISO639-3Code"/>
        <xsl:text> = </xsl:text>
        <xsl:call-template name="OutputISO639-3CodeLanguageName">
            <xsl:with-param name="language" select="."/>
        </xsl:call-template>
        <xsl:call-template name="DoInternalTargetEnd"/>
        <xsl:choose>
            <xsl:when test="position() = last()">
                <xsl:text>.</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>, </xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        OutputISO639-3CodeInTable
    -->
    <xsl:template name="OutputISO639-3CodeInTable">
        <xsl:param name="codesShownHere"/>
        <xsl:param name="codeInSecondColumn"/>

        <!--  we do not use abbrsShownHere in this instance of OutputAbbreviationInTable  -->
        <xsl:call-template name="OutputISO639-3CodeItemInTable"/>
        <xsl:if test="exsl:node-set($contentLayoutInfo)/iso639-3CodesInTableLayout/@useDoubleColumns='yes'">
            <tex:spec cat="align"/>
            <xsl:for-each select="$codeInSecondColumn">
                <xsl:call-template name="OutputISO639-3CodeItemInTable"/>
            </xsl:for-each>
        </xsl:if>
        <tex:spec cat="esc"/>
        <tex:spec cat="esc" nl2="1"/>
    </xsl:template>
    <!--
        OutputISO639-3CodeItemInTable
    -->
    <xsl:template name="OutputISO639-3CodeItemInTable">
        <xsl:param name="codesShownHere"/>

        <xsl:call-template name="DoInternalTargetBegin">
            <xsl:with-param name="sName" select="@id"/>
        </xsl:call-template>
        <xsl:value-of select="@ISO639-3Code"/>
        <xsl:call-template name="DoInternalTargetEnd"/>
        <tex:spec cat="align"/>
        <xsl:if test="not(exsl:node-set($contentLayoutInfo)/iso639-3CodesInTableLayout/@useEqualSignsColumn) or exsl:node-set($contentLayoutInfo)/iso639-3CodesInTableLayout/@useEqualSignsColumn!='no'">
            <xsl:text> = </xsl:text>
            <tex:spec cat="align"/>
        </xsl:if>
        <xsl:call-template name="OutputISO639-3CodeLanguageName">
            <xsl:with-param name="language" select="."/>
        </xsl:call-template>
    </xsl:template>
    <!--
        OutputISO639-3CodesInTable
    -->
    <xsl:template name="OutputISO639-3CodesInTable">
        <xsl:param name="codesUsed"
            select="//language[//iso639-3codeRef[not(ancestor::chapterInCollection)]/@lang=@id or //lineGroup/line[1]/descendant::langData[1][not(ancestor::chapterInCollection)]/@lang=@id or //word/langData[1][not(ancestor::chapterInCollection)]/@lang=@id or //listWord/langData[1][not(ancestor::chapterInCollection)]/@lang=@id]"/>
        <xsl:if test="count($codesUsed) &gt; 0">
            <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacetables='yes' and exsl:node-set($contentLayoutInfo)/iso639-3CodesInTableLayout/@useSingleSpacing!='no'">
                <tex:spec cat="bg"/>
                <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
            </xsl:if>
            <tex:spec cat="bg"/>
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/iso639-3CodesInTableLayout"/>
            </xsl:call-template>
            <tex:env name="longtable">
                <tex:opt>l</tex:opt>
                <tex:parm>
                    <xsl:text>@</xsl:text>
                    <tex:group>
                        <tex:cmd name="hspace*">
                            <tex:parm>
                                <xsl:variable name="sStartIndent" select="normalize-space(exsl:node-set($contentLayoutInfo)/iso639-3CodesInTableLayout/@start-indent)"/>
                                <xsl:choose>
                                    <xsl:when test="string-length($sStartIndent)&gt;0">
                                        <xsl:value-of select="$sStartIndent"/>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <tex:cmd name="parindent" gr="0" nl2="0"/>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </tex:parm>
                        </tex:cmd>
                    </tex:group>
                    <xsl:call-template name="HandleISO639-3CodesInTableColumnSpecColumns"/>
                    <xsl:if test="exsl:node-set($contentLayoutInfo)/iso63-3CodesInTableLayout/@useDoubleColumns='yes'">
                        <xsl:text>@</xsl:text>
                        <tex:group>
                            <tex:cmd name="hspace*">
                                <tex:parm>
                                    <xsl:variable name="sSep" select="normalize-space(exsl:node-set($contentLayoutInfo)/iso639-3CodesInTableLayout/@doubleColumnSeparation)"/>
                                    <xsl:choose>
                                        <xsl:when test="string-length($sSep)&gt;0">
                                            <xsl:value-of select="$sSep"/>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <tex:cmd name="parindent" gr="0" nl2="0"/>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </tex:parm>
                            </tex:cmd>
                        </tex:group>
                        <xsl:call-template name="HandleISO639-3CodesInTableColumnSpecColumns"/>
                    </xsl:if>
                </tex:parm>
                <!--  I'm not happy with how this poor man's attempt at getting double column works when there are long definitions.
                    The table column widths may be long and short; if a cell in the second row needs to lap over a line, then the
                    corresponding cell in the other column may skip a row (as far as what one would expect).
                    So I'm going with just a single table here.
                    <xsl:variable name="iHalfwayPoint" select="ceiling(count($abbrsUsed) div 2)"/>
                    <xsl:for-each select="exsl:node-set($abbrsUsed)[position() &lt;= $iHalfwayPoint]">
                -->
                <xsl:call-template name="SortISO639-3CodesInTable">
                    <xsl:with-param name="codesUsed" select="$codesUsed"/>
                </xsl:call-template>
            </tex:env>
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/iso639-3CodesInTableLayout"/>
            </xsl:call-template>
            <tex:spec cat="eg"/>
            <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacetables='yes' and exsl:node-set($contentLayoutInfo)/iso39-3CodesInTableLayout/@useSingleSpacing!='no'">
                <tex:spec cat="eg"/>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        OutputISOCodeInExample
    -->
    <xsl:template name="OutputISOCodeInExample">
        <xsl:param name="sIsoCode"/>
        <xsl:param name="bOutputBreak" select="'Y'"/>
        <xsl:if test="$bOutputBreak='Y'">
            <tex:spec cat="esc"/>
            <tex:spec cat="esc"/>
        </xsl:if>
        <tex:cmd name="small">
            <tex:parm>
                <xsl:text>[</xsl:text>
                <xsl:choose>
                    <xsl:when test="$bShowISO639-3Codes='Y'">
                        <xsl:call-template name="DoInternalHyperlinkBegin">
                            <xsl:with-param name="sName" select="exsl:node-set($languages)[@ISO639-3Code=$sIsoCode][1]/@id"/>
                        </xsl:call-template>
                        <xsl:call-template name="LinkAttributesBegin">
                            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/iso639-3CodesLinkLayout"/>
                        </xsl:call-template>
                        <xsl:value-of select="$sIsoCode"/>
                        <xsl:call-template name="LinkAttributesEnd">
                            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/iso639-3CodesLinkLayout"/>
                        </xsl:call-template>
                        <xsl:call-template name="DoInternalHyperlinkEnd"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$sIsoCode"/>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:text>]</xsl:text>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        OutputLetter
    -->
    <xsl:template name="OutputLetter">
        <xsl:call-template name="DoInternalTargetBegin">
            <xsl:with-param name="sName" select="@letter"/>
        </xsl:call-template>
        <xsl:apply-templates select="." mode="letter"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($contentLayoutInfo)/exampleLayout/@listItemsHaveParenInsteadOfPeriod='yes'">
                <xsl:text>)</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>.</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="DoInternalTargetEnd"/>
    </xsl:template>
    <!--  
        OutputList
    -->
    <xsl:template name="OutputList">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:variable name="sLetterWidth">
            <xsl:call-template name="GetLetterWidth">
                <xsl:with-param name="iLetterCount" select="count(parent::example/listWord | parent::example/listSingle | parent::example/listInterlinear)"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="sIsoCode">
            <xsl:call-template name="GetISOCode"/>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="name()='listInterlinear'">
                <xsl:variable name="toDoList" select=". | following-sibling::listInterlinear"/>
                <xsl:for-each select=". | following-sibling::listInterlinear">
                    <xsl:if test="position() = 1">
                        <xsl:choose>
                            <xsl:when test="not(preceding-sibling::exampleHeading)">
                                <xsl:if test="not(parent::example[parent::td])">
                                    <tex:cmd name="vspace*" nl2="1">
                                        <tex:parm>
                                            <xsl:text>-</xsl:text>
                                            <xsl:if test="string-length($sIsoCode) &gt; 0 and not(contains($bListsShareSameCode,'N'))">
                                                <xsl:choose>
                                                    <xsl:when test="contains($sIsoCode,'-')">
                                                        <xsl:text>2.75</xsl:text>
                                                    </xsl:when>
                                                    <xsl:otherwise>
                                                        <xsl:text>1.9</xsl:text>
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                            </xsl:if>
                                            <!-- if there is no ISO code, we just use a factor of 1 so we do not need to output anything -->
                                            <tex:cmd name="baselineskip" gr="0" nl2="0"/>
                                        </tex:parm>
                                    </tex:cmd>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="preceding-sibling::exampleHeading and string-length($sIsoCode) &gt; 0 and not(contains($bListsShareSameCode,'N'))">
                                <xsl:if test="not(parent::example[parent::td])">
                                    <tex:cmd name="XLingPaperAdjustHeaderInListInterlinearWithISOCodes">
                                        <tex:parm>
                                            <tex:cmd name="XLingPaperexampleheadingheight" gr="0"/>
                                        </tex:parm>
                                        <tex:parm>
                                            <tex:cmd name="XLingPaperexamplenumberheight" gr="0"/>
                                        </tex:parm>
                                    </tex:cmd>
                                </xsl:if>
                            </xsl:when>
                            <xsl:otherwise>
                                <!-- do nothing; it comes out fine -->
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:if>
                    <xsl:variable name="sXLingPaperListInterlinear">
                        <xsl:choose>
                            <xsl:when test="parent::example[parent::td]">
                                <xsl:text>XLingPaperlistinterlinearintable</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>XLingPaperlistinterlinear</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:variable>
                    <xsl:choose>
                        <xsl:when test="contains(@XeLaTeXSpecial,'clearpage')">
                            <tex:cmd name="clearpage" gr="0" nl2="0"/>
                        </xsl:when>
                        <xsl:when test="contains(@XeLaTeXSpecial,'pagebreak')">
                            <tex:cmd name="pagebreak" gr="0" nl2="0"/>
                        </xsl:when>
                    </xsl:choose>
                    <tex:cmd name="{$sXLingPaperListInterlinear}" nl1="0" nl2="1">
                        <tex:parm>
                            <xsl:value-of select="$sExampleIndentBefore"/>
                        </tex:parm>
                        <tex:parm>
                            <xsl:value-of select="$iNumberWidth"/>
                            <xsl:text>em</xsl:text>
                        </tex:parm>
                        <tex:parm>
                            <xsl:call-template name="GetLetterWidth">
                                <xsl:with-param name="iLetterCount" select="count(listInterlinear)"/>
                            </xsl:call-template>
                            <xsl:text>em</xsl:text>
                        </tex:parm>
                        <tex:parm>
                            <xsl:call-template name="OutputLetter"/>
                        </tex:parm>
                        <tex:parm>
                            <xsl:call-template name="HandleAnyInterlinearAlignedWordSkipOverride"/>
                            <xsl:choose>
                                <xsl:when test="$bAutomaticallyWrapInterlinears='yes' and $sInterlinearSourceStyle='AfterFirstLine'">
                                    <xsl:choose>
                                        <xsl:when test="parent::example">
                                            <xsl:call-template name="DoAnyInterlinearWrappedWithSourceAfterFirstLine">
                                                <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                                            </xsl:call-template>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <xsl:apply-templates>
                                                <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                                            </xsl:apply-templates>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:apply-templates>
                                        <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                                    </xsl:apply-templates>
                                </xsl:otherwise>
                            </xsl:choose>
                        </tex:parm>
                    </tex:cmd>
                    <xsl:if test="position() != last()">
                        <xsl:choose>
                            <xsl:when test="parent::example[parent::td]">
                                <tex:spec cat="esc"/>
                                <tex:spec cat="esc"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <tex:cmd name="vspace">
                                    <tex:parm>
                                        <tex:cmd name="baselineskip" gr="0"/>
                                    </tex:parm>
                                </tex:cmd>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:if>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <tex:group nl2="1">
                    <xsl:variable name="sTableType">
                        <xsl:choose>
                            <xsl:when test="parent::example[parent::td]">tabular</xsl:when>
                            <xsl:when test="parent::example[parent::endnote[parent::td]]">tabular</xsl:when>
                            <xsl:when test="name()='listDefinition' and parent::example[parent::endnote[ancestor::listWord or ancestor::listDefinition or ancestor::listSingle]]">tabular</xsl:when>
                            <xsl:when test="name()='listSingle' and parent::example[parent::endnote[ancestor::listWord or ancestor::listDefinition or ancestor::listSingle]]">tabular</xsl:when>
                            <xsl:when test="name()='listWord' and parent::example[parent::endnote[ancestor::listWord or ancestor::listDefinition or ancestor::listSingle]]">tabular</xsl:when>
                            <xsl:otherwise>longtable</xsl:otherwise>
                        </xsl:choose>
                    </xsl:variable>
                    <xsl:if test="$sTableType='longtable'">
                        <xsl:call-template name="PrepareListForLongtable">
                            <xsl:with-param name="sIsoCode" select="$sIsoCode"/>
                            <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                        </xsl:call-template>
                    </xsl:if>
                    <tex:env name="{$sTableType}" nl1="1">
                        <xsl:if test="$sTableType='tabular'">
                            <tex:opt>t</tex:opt>
                        </xsl:if>
                        <tex:parm>
                            <xsl:text>p</xsl:text>
                            <tex:spec cat="bg"/>
                            <xsl:value-of select="$sLetterWidth"/>
                            <xsl:text>em</xsl:text>
                            <tex:spec cat="eg"/>
                            <xsl:choose>
                                <xsl:when test="name()='listDefinition' or name()='listSingle'">
                                    <xsl:if test="contains($bListsShareSameCode,'N')">
                                        <xsl:text>@</xsl:text>
                                        <tex:spec cat="bg"/>
                                        <tex:spec cat="eg"/>
                                        <xsl:text>l</xsl:text>
                                        <xsl:text>@</xsl:text>
                                        <tex:spec cat="bg"/>
                                        <tex:spec cmd="esc"/>
                                        <xsl:text>&#x20;</xsl:text>
                                        <tex:spec cat="eg"/>
                                    </xsl:if>
                                    <xsl:text>@</xsl:text>
                                    <tex:spec cat="bg"/>
                                    <tex:spec cat="eg"/>
                                    <xsl:text>p</xsl:text>
                                    <tex:spec cat="bg"/>
                                    <xsl:value-of select="$sExampleWidth"/>
                                    <xsl:text>-</xsl:text>
                                    <xsl:value-of select="$sExampleIndentBefore"/>
                                    <xsl:text>-</xsl:text>
                                    <xsl:value-of select="$sExampleIndentAfter"/>
                                    <xsl:text>-</xsl:text>
                                    <xsl:value-of select="$sLetterWidth"/>
                                    <xsl:text>em</xsl:text>
                                    <xsl:text>-</xsl:text>
                                    <xsl:value-of select="$iNumberWidth"/>
                                    <xsl:text>em</xsl:text>
                                    <tex:spec cat="eg"/>
                                    <xsl:text>l</xsl:text>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:call-template name="DoInterlinearTabularMainPattern">
                                        <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                                    </xsl:call-template>
                                </xsl:otherwise>
                            </xsl:choose>
                        </tex:parm>
                        <xsl:call-template name="DoListLetter">
                            <xsl:with-param name="sLetterWidth" select="$sLetterWidth"/>
                        </xsl:call-template>
                        <tex:spec cat="align"/>
                        <xsl:call-template name="OutputListLevelISOCode">
                            <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                            <xsl:with-param name="sIsoCode" select="$sIsoCode"/>
                        </xsl:call-template>
                        <!-- not sure if the following is the best or even needed...
                            <tex:cmd name="hspace*">
                            <tex:parm>-2.5pt</tex:parm>
                            </tex:cmd>  -->
                        <xsl:call-template name="OutputWordOrSingle"/>
                        <xsl:if test="name()='listWord'">
                            <xsl:apply-templates select="word">
                                <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                            </xsl:apply-templates>
                        </xsl:if>
                        <!-- remaining rows -->
                        <xsl:for-each select="following-sibling::listWord | following-sibling::listSingle | following-sibling::listDefinition">
                            <tex:spec cat="esc"/>
                            <tex:spec cat="esc" nl2="1"/>
                            <xsl:if test="contains(@XeLaTeXSpecial,'clearpage')">
                                <tex:cmd name="clearpage" gr="0" nl2="0"/>
                            </xsl:if>
                            <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak')">
                                <tex:cmd name="pagebreak" gr="0" nl2="0"/>
                            </xsl:if>
                            <xsl:call-template name="DoListLetter">
                                <xsl:with-param name="sLetterWidth" select="$sLetterWidth"/>
                            </xsl:call-template>
                            <tex:spec cat="align"/>
                            <xsl:variable name="sListIsoCode">
                                <xsl:call-template name="GetISOCode"/>
                            </xsl:variable>
                            <xsl:call-template name="OutputListLevelISOCode">
                                <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                                <xsl:with-param name="sIsoCode" select="$sListIsoCode"/>
                            </xsl:call-template>
                            <xsl:call-template name="OutputWordOrSingle"/>
                            <xsl:if test="name()='listWord'">
                                <xsl:apply-templates select="word">
                                    <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                                </xsl:apply-templates>
                            </xsl:if>
                        </xsl:for-each>
                    </tex:env>
                </tex:group>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        OutputListLevelISOCode
    -->
    <xsl:template name="OutputListLevelISOCode">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:param name="sIsoCode"/>
        <xsl:param name="bCloseOffMultirow" select="'N'"/>
        <xsl:param name="originalContext"/>
        <xsl:if
            test="exsl:node-set($lingPaper)/@showiso639-3codeininterlinear='yes' or ancestor-or-self::example/@showiso639-3codes='yes' or $originalContext and exsl:node-set($originalContext)/ancestor-or-self::example/@showiso639-3codes='yes'">
            <xsl:if test="contains($bListsShareSameCode,'N')">
                <xsl:variable name="sISOCodeTeXOutput">
                    <xsl:call-template name="OutputISOCodeInExample">
                        <xsl:with-param name="bOutputBreak" select="'N'"/>
                        <xsl:with-param name="sIsoCode" select="$sIsoCode"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:choose>
                    <xsl:when test=" name()='lineGroup' and count(preceding-sibling::*)!=0 and preceding-sibling::*[1][name()!='exampleHeading']">
                        <tex:cmd name="settowidth">
                            <tex:parm>
                                <tex:cmd name="XLingPaperisocodewidth" gr="0"/>
                            </tex:parm>
                            <tex:parm>
                                <xsl:copy-of select="saxon:node-set($sISOCodeTeXOutput)"/>
                            </tex:parm>
                        </tex:cmd>
                        <tex:cmd name="hspace*">
                            <tex:parm>
                                <tex:cmd name="XLingPaperisocodewidth" gr="0" nl2="0"/>
                            </tex:parm>
                        </tex:cmd>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:copy-of select="saxon:node-set($sISOCodeTeXOutput)"/>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:if test="$bCloseOffMultirow='Y'">
                    <xsl:if test="string-length($sIsoCode) &gt; 3">
                        <!-- following closes off the content of the multirow command -->
                        <tex:spec cat="eg"/>
                    </xsl:if>
                </xsl:if>
                <tex:spec cat="align"/>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        OutputPlainTOCLine
    -->
    <xsl:template name="OutputPlainTOCLine">
        <xsl:param name="sLabel"/>
        <xsl:param name="sSpaceBefore" select="'0'"/>
        <xsl:param name="sIndent" select="'0pt'"/>
        <xsl:param name="sNumWidth" select="'0pt'"/>
        <xsl:if test="number($sSpaceBefore)>0">
            <tex:cmd name="vspace">
                <tex:parm>
                    <!--    <xsl:value-of select="$sBasicPointSize"/>
                        <xsl:text>pt</xsl:text>-->
                    <xsl:call-template name="GetCurrentPointSize">
                        <xsl:with-param name="bAddGlue" select="'Y'"/>
                    </xsl:call-template>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <tex:cmd name="XLingPaperplaintocline" nl2="1">
            <tex:parm>
                <xsl:copy-of select="$sIndent"/>
            </tex:parm>
            <tex:parm>
                <xsl:copy-of select="$sNumWidth"/>
            </tex:parm>
            <tex:parm>
                <xsl:copy-of select="$sLabel"/>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        OutputTable
    -->
    <xsl:template name="OutputTable">
        <xsl:variable name="iBorder" select="ancestor-or-self::table/@border"/>
        <xsl:variable name="firstRowColumns" select="tr[1]/th | tr[1]/td"/>
        <!--        <xsl:variable name="iNumCols" select="count(exsl:node-set($firstRowColumns)[not(number(@colspan) &gt; 0)]) + sum(exsl:node-set($firstRowColumns)[number(@colspan) &gt; 0]/@colspan)"/>-->
        <!-- attempt to calculate the number of columns, but we need to also set up colspans, so this won't always work... sigh.
    
    <xsl:variable name="rows">
            <rows>
                <xsl:for-each select="tr">
                    <rowcount>
                        <xsl:value-of select="count(*[not(number(@colspan) &gt; 0)]) + sum(*[number(@colspan) &gt; 0]/@colspan)"/>
                    </rowcount>
                </xsl:for-each>
            </rows>
        </xsl:variable>
        <xsl:variable name="iNumCols">
            <xsl:for-each select="saxon:node-set($rows)/descendant::*">
                <xsl:for-each select="row">
                    <xsl:sort select="." order="descending" data-type="number"/>
                    <xsl:if test="position()=1">
                        <xsl:value-of select="."/>
                    </xsl:if>
                </xsl:for-each>
            </xsl:for-each>
        </xsl:variable>
        -->
        <!-- trying to be a bit smarter with the column counting... -->
        <xsl:variable name="rowsall">
            <rows>
                <xsl:for-each select="tr">
                    <rowcount>
                        <xsl:value-of select="count(*[not(number(@colspan) &gt; 0)]) + sum(*[number(@colspan) &gt; 0]/@colspan)"/>
                    </rowcount>
                </xsl:for-each>
            </rows>
        </xsl:variable>
        <xsl:variable name="elementsWithColspan" select="descendant::*[@colspan]"/>
        <xsl:variable name="iNumCols">
            <xsl:choose>
                <xsl:when test="count($elementsWithColspan) &gt; 0">
                    <xsl:value-of select="count(exsl:node-set($firstRowColumns)[not(number(@colspan) &gt; 0)]) + sum(exsl:node-set($firstRowColumns)[number(@colspan) &gt; 0]/@colspan)"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:for-each select="saxon:node-set($rowsall)/descendant::*">
                        <xsl:for-each select="rowcount">
                            <xsl:sort select="." order="descending" data-type="number"/>
                            <xsl:if test="position()=1">
                                <xsl:value-of select="."/>
                            </xsl:if>
                        </xsl:for-each>
                    </xsl:for-each>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="iRowWithMaxColumns">
            <xsl:choose>
                <xsl:when test="count($elementsWithColspan) &gt; 0">
                    <xsl:text>1</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:variable name="rowHasMaxCount" select="saxon:node-set($rowsall)/rows/rowcount[number(.)=number($iNumCols)]"/>
                    <xsl:for-each select="$rowHasMaxCount">
                        <xsl:if test="position()=1">
                            <xsl:value-of select="count(preceding-sibling::rowcount) + 1"/>
                        </xsl:if>
                    </xsl:for-each>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="sEnvName">
            <xsl:choose>
                <xsl:when test="ancestor::td or ancestor::th or ancestor::framedUnit">
                    <!--                    <xsl:when test="parent::example or parent::td">-->
                    <xsl:text>tabular</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>longtable</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="parent::example">
                <xsl:variable name="sIsoCode">
                    <xsl:call-template name="GetISOCode"/>
                </xsl:variable>
                <xsl:if test="string-length($sIsoCode) &gt;0">
                    <tex:cmd name="vspace*">
                        <tex:parm>
                            <xsl:call-template name="AdjustForISOCodeInExampleNumber">
                                <xsl:with-param name="sIsoCode" select="$sIsoCode"/>
                            </xsl:call-template>
                        </tex:parm>
                    </tex:cmd>
                </xsl:if>
                <xsl:call-template name="SetTeXCommand">
                    <xsl:with-param name="sTeXCommand" select="'setlength'"/>
                    <xsl:with-param name="sCommandToSet" select="'LTpre'"/>
                    <xsl:with-param name="sValue">
                        <xsl:choose>
                            <xsl:when test="preceding-sibling::exampleHeading">
                                <xsl:choose>
                                    <xsl:when test="caption">.25</xsl:when>
                                    <xsl:when test="$iBorder &gt;= 1">1</xsl:when>
                                    <xsl:otherwise>.25</xsl:otherwise>
                                </xsl:choose>
                            </xsl:when>
                            <xsl:when test="caption">-.9</xsl:when>
                            <xsl:when test="$iBorder &gt;= 1">-.5</xsl:when>
                            <xsl:otherwise>-.9</xsl:otherwise>
                        </xsl:choose>
                        <tex:cmd name="baselineskip" gr="0" nl2="0"/>
                    </xsl:with-param>
                </xsl:call-template>
                <xsl:call-template name="SetTeXCommand">
                    <xsl:with-param name="sTeXCommand" select="'setlength'"/>
                    <xsl:with-param name="sCommandToSet" select="'LTleft'"/>
                    <xsl:with-param name="sValue">
                        <xsl:value-of select="$sExampleIndentBefore"/>
                        <xsl:text> + </xsl:text>
                        <xsl:value-of select="$iNumberWidth"/>
                        <xsl:text>em</xsl:text>
                    </xsl:with-param>
                </xsl:call-template>
                <xsl:call-template name="SetTeXCommand">
                    <xsl:with-param name="sTeXCommand" select="'setlength'"/>
                    <xsl:with-param name="sCommandToSet" select="'LTpost'"/>
                    <xsl:with-param name="sValue">
                        <xsl:text>0pt</xsl:text>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="not(ancestor::endnote)">
                <xsl:choose>
                    <xsl:when test="ancestor::tablenumbered and not(ancestor::table) and $sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacetables='yes'">
                        <tex:cmd name="{$sSingleSpacingCommand}" gr="0"/>
                        <tex:cmd name="vspace*">
                            <tex:parm>
                                <xsl:text>-</xsl:text>
                                <xsl:choose>
                                    <xsl:when
                                        test="exsl:node-set($contentLayoutInfo)/tablenumberedLayout/@captionLocation='before' or not(exsl:node-set($contentLayoutInfo)/tablenumberedLayout) and exsl:node-set($lingPaper)/@tablenumberedLabelAndCaptionLocation='before'">
                                        <xsl:choose>
                                            <xsl:when test="$sLineSpacing='double'">
                                                <xsl:text>3</xsl:text>
                                            </xsl:when>
                                            <xsl:when test="$sLineSpacing='spaceAndAHalf'">
                                                <xsl:text>3</xsl:text>
                                            </xsl:when>
                                        </xsl:choose>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:choose>
                                            <xsl:when test="$sLineSpacing='double'">
                                                <xsl:text>2</xsl:text>
                                            </xsl:when>
                                            <xsl:when test="$sLineSpacing='spaceAndAHalf'">
                                                <xsl:text>2.5</xsl:text>
                                            </xsl:when>
                                        </xsl:choose>
                                    </xsl:otherwise>
                                </xsl:choose>
                                <tex:cmd name="baselineskip" gr="0"/>
                            </tex:parm>
                        </tex:cmd>
                    </xsl:when>
                    <xsl:when test="ancestor::framedUnit">
                        <tex:cmd name="noindent" gr="0"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <tex:cmd name="vspace*">
                            <tex:parm>
                                <xsl:text>-</xsl:text>
                                <tex:cmd name="baselineskip" gr="0"/>
                            </tex:parm>
                        </tex:cmd>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <!--            <xsl:otherwise> </xsl:otherwise>-->
        </xsl:choose>
        <tex:env name="{$sEnvName}" nl1="0">
            <tex:opt>
                <xsl:choose>
                    <xsl:when test="parent::example or ancestor::table">t</xsl:when>
                    <xsl:otherwise>
                        <xsl:variable name="sAlign" select="normalize-space(@align)"/>
                        <xsl:choose>
                            <xsl:when test="string-length($sAlign) &gt; 0">
                                <xsl:choose>
                                    <xsl:when test="$sAlign='center'">c</xsl:when>
                                    <xsl:when test="$sAlign='right'">r</xsl:when>
                                    <xsl:otherwise>l</xsl:otherwise>
                                </xsl:choose>
                            </xsl:when>
                            <xsl:otherwise>l</xsl:otherwise>
                        </xsl:choose>
                    </xsl:otherwise>
                </xsl:choose>
            </tex:opt>
            <tex:parm>
                <xsl:choose>
                    <xsl:when test="contains(@XeLaTeXSpecial,'column-formatting=')">
                        <xsl:call-template name="HandleXeLaTeXSpecialCommand">
                            <xsl:with-param name="sPattern" select="'column-formatting='"/>
                            <xsl:with-param name="default" select="'@{}l@{}'"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="CreateColumnSpecDefaultAtExpression"/>
                        <!--                        <xsl:variable name="columns" select="tr[1]/td | tr[1]/th"/>-->
                        <xsl:variable name="columns" select="tr[position()=$iRowWithMaxColumns]/td | tr[position()=$iRowWithMaxColumns]/th"/>
                        <xsl:for-each select="$columns">
                            <xsl:choose>
                                <xsl:when test="number(@colspan) &gt; 0">
                                    <xsl:call-template name="CreateColumnSpec">
                                        <xsl:with-param name="iColspan" select="@colspan - 1"/>
                                        <xsl:with-param name="iBorder" select="$iBorder"/>
                                        <xsl:with-param name="bUseWidth" select="'N'"/>
                                    </xsl:call-template>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:call-template name="CreateColumnSpec">
                                        <xsl:with-param name="iBorder" select="$iBorder"/>
                                    </xsl:call-template>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:for-each>
                        <xsl:if test="not($columns)">
                            <!-- the table is empty!  We still need something, though or TeX will complain. -->
                            <xsl:text>l</xsl:text>
                        </xsl:if>
                        <xsl:call-template name="CreateVerticalLine">
                            <xsl:with-param name="iBorder" select="$iBorder"/>
                        </xsl:call-template>
                        <xsl:call-template name="CreateColumnSpecDefaultAtExpression"/>
                    </xsl:otherwise>
                </xsl:choose>
            </tex:parm>
            <xsl:apply-templates select="caption">
                <xsl:with-param name="iNumCols" select="$iNumCols"/>
            </xsl:apply-templates>
            <xsl:if test="tr/th | headerRow">
                <xsl:call-template name="CreateHorizontalLine">
                    <xsl:with-param name="iBorder" select="$iBorder"/>
                </xsl:call-template>
                <xsl:variable name="headerRows" select="tr[th[count(following-sibling::td)=0]]"/>
                <xsl:choose>
                    <xsl:when test="count($headerRows) != 1">
                        <xsl:for-each select="$headerRows">
                            <xsl:apply-templates select="th[count(following-sibling::td)=0] | headerRow">
                                <!--                        <xsl:with-param name="iBorder" select="$iBorder"/>-->
                            </xsl:apply-templates>
                            <tex:spec cat="esc"/>
                            <tex:spec cat="esc"/>
                        </xsl:for-each>
                    </xsl:when>
                    <xsl:otherwise>
                        <!--                  <xsl:call-template name="OutputBackgroundColor"/>-->
                        <xsl:apply-templates select="tr[th[count(following-sibling::td)=0]] | headerRow">
                            <!--                     <xsl:with-param name="iBorder" select="$iBorder"/>-->
                        </xsl:apply-templates>
                        <!--                  <xsl:apply-templates select="tr/th[count(following-sibling::td)=0] | headerRow"/>-->
                        <!--                  <tex:spec cat="esc"/>-->
                        <!--                  <tex:spec cat="esc"/>-->
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:if>
            <xsl:variable name="rows" select="tr[not(th) or th[count(following-sibling::td)!=0]]"/>
            <xsl:choose>
                <xsl:when test="$rows">
                    <xsl:apply-templates select="$rows">
                        <xsl:with-param name="iBorder" select="$iBorder"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>(This table does not have any contents!)</xsl:text>
                    <tex:spec cat="esc"/>
                    <tex:spec cat="esc"/>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:apply-templates select="endCaption">
                <xsl:with-param name="iNumCols" select="$iNumCols"/>
            </xsl:apply-templates>
        </tex:env>
        <xsl:variable name="iTableCount" select="count(ancestor-or-self::table)"/>
        <xsl:if test="$iTableCount  = 2 and descendant-or-self::endnote">
            <!-- When have a table within a table - longtable (the outermost table) can handle footnotes; tabular (the inner tables) cannot.
                   We handle it by putting the text of all footnotes here at the end of the first embedded table 
                   (doing it for each embedded table does not work - the text of the embedded footnote does not come out). -->
            <xsl:for-each select="descendant-or-self::endnote">
                <xsl:apply-templates select=".">
                    <xsl:with-param name="sTeXFootnoteKind" select="'footnotetext'"/>
                </xsl:apply-templates>
            </xsl:for-each>
        </xsl:if>
        <xsl:if test="ancestor::framedUnit">
            <tex:cmd name="par"/>
            <tex:cmd name="vspace">
                <tex:parm>
                    <tex:cmd name="baselineskip"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
    </xsl:template>
    <!--  
        OutputTextTransform
    -->
    <xsl:template name="OutputTextTransform">
        <xsl:param name="sTextTransform"/>
        <xsl:param name="originalContext"/>
        <xsl:if test="string-length($sTextTransform) &gt; 0">
            <!--  and $originalContext and name(exsl:node-set($originalContext)/*)='' -->
            <xsl:if test="not($originalContext) or name(exsl:node-set($originalContext)/*)=''">
                <xsl:choose>
                    <xsl:when test="$sTextTransform='uppercase'">
                        <tex:spec cat="bg"/>
                        <tex:cmd name="MakeUppercase" gr="0"/>
                        <tex:spec cat="bg"/>
                    </xsl:when>
                    <xsl:when test="$sTextTransform='lowercase'">
                        <tex:spec cat="bg"/>
                        <tex:cmd name="MakeLowercase" gr="0"/>
                        <tex:spec cat="bg"/>
                    </xsl:when>
                    <!-- we ignore 'captialize' and 'none' -->
                </xsl:choose>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        OutputTextTransformEnd
    -->
    <xsl:template name="OutputTextTransformEnd">
        <xsl:param name="sTextTransform"/>
        <xsl:param name="originalContext"/>
        <xsl:if test="string-length($sTextTransform) &gt; 0">
            <!--  and $originalContext and name(exsl:node-set($originalContext)/*)='' -->
            <xsl:if test="not($originalContext) or name(exsl:node-set($originalContext)/*)=''">
                <xsl:choose>
                    <xsl:when test="$sTextTransform='uppercase'">
                        <tex:spec cat="eg"/>
                        <tex:spec cat="eg"/>
                    </xsl:when>
                    <xsl:when test="$sTextTransform='lowercase'">
                        <tex:spec cat="eg"/>
                        <tex:spec cat="eg"/>
                    </xsl:when>
                    <!-- we ignore 'captialize' and 'none' -->
                </xsl:choose>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        OutputTypeAttributes
    -->
    <xsl:template name="OutputTypeAttributes">
        <xsl:param name="sList"/>
        <xsl:variable name="sNewList" select="concat(normalize-space($sList),' ')"/>
        <xsl:variable name="sFirst" select="substring-before($sNewList,' ')"/>
        <xsl:variable name="sRest" select="substring-after($sNewList,' ')"/>
        <xsl:if test="string-length($sFirst) &gt; 0">
            <xsl:choose>
                <xsl:when test="$sFirst='superscript'">
                    <tex:spec cat="esc"/>
                    <xsl:text>textsuperscript</xsl:text>
                    <tex:spec cat="bg"/>
                </xsl:when>
                <xsl:when test="$sFirst='subscript'">
                    <tex:spec cat="esc"/>
                    <xsl:text>textsubscript</xsl:text>
                    <tex:spec cat="bg"/>
                </xsl:when>
                <xsl:when test="$sFirst='underline'">
                    <tex:spec cat="esc"/>
                    <xsl:text>uline</xsl:text>
                    <tex:spec cat="bg"/>
                </xsl:when>
                <xsl:when test="$sFirst='line-through'">
                    <tex:spec cat="esc"/>
                    <xsl:text>sout</xsl:text>
                    <tex:spec cat="bg"/>
                </xsl:when>
            </xsl:choose>
            <xsl:if test="$sRest">
                <xsl:call-template name="OutputTypeAttributes">
                    <xsl:with-param name="sList" select="$sRest"/>
                </xsl:call-template>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        OutputTypeAttributesEnd
    -->
    <xsl:template name="OutputTypeAttributesEnd">
        <xsl:param name="sList"/>
        <xsl:variable name="sNewList" select="concat(normalize-space($sList),' ')"/>
        <xsl:variable name="sFirst" select="substring-before($sNewList,' ')"/>
        <xsl:variable name="sRest" select="substring-after($sNewList,' ')"/>
        <xsl:if test="string-length($sFirst) &gt; 0">
            <xsl:choose>
                <xsl:when test="$sFirst='superscript'">
                    <tex:spec cat="eg"/>
                </xsl:when>
                <xsl:when test="$sFirst='subscript'">
                    <tex:spec cat="eg"/>
                </xsl:when>
                <xsl:when test="$sFirst='underline'">
                    <tex:spec cat="eg"/>
                </xsl:when>
                <xsl:when test="$sFirst='line-through'">
                    <tex:spec cat="eg"/>
                </xsl:when>
            </xsl:choose>
            <xsl:if test="$sRest">
                <xsl:call-template name="OutputTypeAttributesEnd">
                    <xsl:with-param name="sList" select="$sRest"/>
                </xsl:call-template>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--
        OutputWordOrSingle
    -->
    <xsl:template name="OutputWordOrSingle">
        <xsl:choose>
            <xsl:when test="name()='listWord'">
                <xsl:call-template name="HandleLangDataGlossInWordOrListWord"/>
            </xsl:when>
            <xsl:when test="name()='word' and descendant::word or name()='word' and ancestor::word">
                <xsl:call-template name="HandleLangDataGlossInWordOrListWord"/>
            </xsl:when>
            <xsl:when test="name()='word' and descendant::word or name()='word' and ancestor::listWord">
                <xsl:call-template name="HandleLangDataGlossInWordOrListWord"/>
            </xsl:when>
            <xsl:when test="name()='listDefinition'">
                <xsl:for-each select="definition">
                    <xsl:apply-templates select="self::*"/>
                    <xsl:if test="position()!=last()">
                        <tex:spec cat="align"/>
                    </xsl:if>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="HandleVerticalSpacingWhenExampleHeadingWithISOCode"/>
                <xsl:for-each select="langData | gloss | interlinearSource">
                    <xsl:apply-templates select="self::*"/>
                    <tex:spec cat="esc"/>
                    <xsl:text>&#x20;</xsl:text>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        PrepareListForLongtable
    -->
    <xsl:template name="PrepareListForLongtable">
        <xsl:param name="sIsoCode"/>
        <xsl:param name="bListsShareSameCode"/>
        <xsl:if test="../descendant-or-self::endnote">
            <!-- longtable allows \footnote, but if the column spec has a 'p' for the column a footnote is in, 
                then one cannot overtly say what the footnote number should be. 
                Therefore, we must set the footnote counter here.
            -->
            <xsl:call-template name="SetLaTeXFootnoteCounter"/>
        </xsl:if>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'setlength'"/>
            <xsl:with-param name="sCommandToSet" select="'LTpre'"/>
            <xsl:with-param name="sValue">
                <xsl:choose>
                    <xsl:when test="string-length($sIsoCode) &gt; 0 and not(contains($bListsShareSameCode,'N'))">
                        <xsl:choose>
                            <xsl:when test="preceding-sibling::exampleHeading">
                                <xsl:text>-.8</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>-1.725</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:when test="preceding-sibling::exampleHeading">
                        <xsl:text>.1</xsl:text>
                    </xsl:when>
                    <xsl:when test="exsl:node-set($contentLayoutInfo)/exampleLayout/@numberProperUseParens='no'">
                        <xsl:text>-.7</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>-.875</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
                <tex:cmd name="baselineskip" gr="0" nl2="0"/>
            </xsl:with-param>
        </xsl:call-template>
        <!--                    </xsl:if>-->
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'setlength'"/>
            <xsl:with-param name="sCommandToSet" select="'LTleft'"/>
            <xsl:with-param name="sValue">
                <xsl:value-of select="$sExampleIndentBefore"/>
                <xsl:text> + </xsl:text>
                <xsl:choose>
                    <xsl:when test="name()='word'">
                        <xsl:value-of select="$iNumberWidth"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$iNumberWidth - .5"/>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:text>em</xsl:text>
            </xsl:with-param>
        </xsl:call-template>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'setlength'"/>
            <xsl:with-param name="sCommandToSet" select="'LTpost'"/>
            <xsl:with-param name="sValue">
                <xsl:text>0pt</xsl:text>
            </xsl:with-param>
        </xsl:call-template>

    </xsl:template>
    <!--  
        ReportTeXCannotHandleThisMessage
    -->
    <xsl:template name="ReportTeXCannotHandleThisMessage">
        <xsl:param name="sMessage"/>
        <xsl:if test="name()!='img'">
            <tex:spec cat="esc"/>
            <tex:spec cat="esc"/>
        </xsl:if>
        <tex:cmd name="colorbox">
            <tex:parm>yellow</tex:parm>
            <tex:parm>
                <tex:cmd name="parbox">
                    <tex:opt>t</tex:opt>
                    <tex:parm>
                        <tex:cmd name="textwidth" gr="0" nl2="0"/>
                        <xsl:text>-5em</xsl:text>
                    </tex:parm>
                    <tex:parm>
                        <tex:spec cat="esc"/>
                        <xsl:text>raggedright </xsl:text>
                        <xsl:copy-of select="$sMessage"/>
                    </tex:parm>
                </tex:cmd>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        ReverseContents
    -->
    <xsl:template name="ReverseContents">
        <xsl:param name="sList"/>
        <xsl:param name="bInsertSpaceAfterLast" select="'Y'"/>
        <xsl:param name="bIsTopLevel" select="'Y'"/>
        <xsl:variable name="sNewList" select="concat(normalize-space($sList),' ')"/>
        <xsl:variable name="sFirst" select="substring-before($sNewList,' ')"/>
        <xsl:variable name="sRest" select="substring-after($sNewList,' ')"/>
        <xsl:if test="$sRest">
            <xsl:call-template name="ReverseContents">
                <xsl:with-param name="sList" select="$sRest"/>
                <xsl:with-param name="bIsTopLevel" select="'N'"/>
                <xsl:with-param name="bInsertSpaceAfterLast" select="$bInsertSpaceAfterLast"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:value-of select="$sFirst"/>
        <xsl:if test="$bIsTopLevel='N' or $bInsertSpaceAfterLast='Y'">
            <xsl:text>&#x20;</xsl:text>
        </xsl:if>
    </xsl:template>
    <!--  
        ReverseContentsInNodes
    -->
    <xsl:template name="ReverseContentsInNodes">
        <xsl:param name="originalContext"/>
        <xsl:apply-templates select="node()" mode="reverse">
            <xsl:sort select="position()" order="descending"/>
            <xsl:with-param name="originalContext" select="$originalContext"/>
        </xsl:apply-templates>
    </xsl:template>
    <xsl:template match="text()" mode="reverse">
        <xsl:variable name="sTrimmed" select="normalize-space(.)"/>
        <xsl:value-of select="substring-after(.,$sTrimmed)"/>
        <xsl:call-template name="ReverseContents">
            <xsl:with-param name="sList" select="."/>
            <xsl:with-param name="bInsertSpaceAfterLast" select="'N'"/>
        </xsl:call-template>
        <xsl:value-of select="substring-before(.,$sTrimmed)"/>
    </xsl:template>
    <!-- reverse -->
    <xsl:template match="object" mode="reverse">
        <xsl:param name="originalContext"/>
        <xsl:apply-templates select=".">
            <xsl:with-param name="originalContext" select="$originalContext"/>
            <xsl:with-param name="bReversing" select="'Y'"/>
        </xsl:apply-templates>
    </xsl:template>
    <xsl:template match="langData" mode="reverse">
        <xsl:param name="originalContext"/>
        <xsl:apply-templates select=".">
            <xsl:with-param name="originalContext" select="$originalContext"/>
            <xsl:with-param name="bReversing" select="'Y'"/>
        </xsl:apply-templates>
    </xsl:template>
    <xsl:template match="gloss" mode="reverse">
        <xsl:param name="originalContext"/>
        <xsl:apply-templates select=".">
            <xsl:with-param name="originalContext" select="$originalContext"/>
            <xsl:with-param name="bReversing" select="'Y'"/>
        </xsl:apply-templates>
    </xsl:template>
    <xsl:template match="endnote | endnoteRef" mode="reverse">
        <xsl:param name="originalContext"/>
        <xsl:apply-templates select=".">
            <xsl:with-param name="originalContext" select="$originalContext"/>
        </xsl:apply-templates>
    </xsl:template>
    <xsl:template
        match="exampleRef | sectionRef | appendixRef | citation | br | figureRef | tablenumberedRef | q | img | genericRef | genericTarget | link | 
        indexedItem | indexedRangeBegin | indexedRangeEnd | interlinearRefCitation | mediaObject"
        mode="reverse">
        <xsl:apply-templates select="."/>
    </xsl:template>
    <!--  
        SetDefaultXLingPaperInterWordSkip
    -->
    <xsl:template name="SetDefaultXLingPaperInterWordSkip">
        <xsl:variable name="sDefaultGlue" select="'6.66666pt plus 3.33333pt minus 2.22222pt'"/>
        <tex:cmd name="XLingPaperinterwordskip" gr="0" nl1="1"/>
        <xsl:text>=</xsl:text>
        <xsl:choose>
            <xsl:when test="exsl:node-set($documentLayoutInfo)/interlinearAlignedWordSpacing/@XeLaTeXSpecial[contains(.,'interlinear-aligned-word-skip')]">
                <xsl:for-each select="exsl:node-set($documentLayoutInfo)/interlinearAlignedWordSpacing">
                    <xsl:call-template name="GetXeLaTeXSpecialCommand">
                        <xsl:with-param name="sAttr" select="'interlinear-aligned-word-skip='"/>
                        <xsl:with-param name="sDefaultValue" select="$sDefaultGlue"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sDefaultGlue"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        SetExampleKeepWithNext
    -->
    <xsl:template name="SetExampleKeepWithNext">
        <!-- we need to make sure the example number stays on the same page as the table or list -->
        <xsl:choose>
            <xsl:when test="listWord or listSingle or listDefinition">
                <tex:cmd name="XLingPaperneedspace">
                    <tex:parm>
                        <xsl:variable name="iLines" select="count(listWord | listSingle | listDefinition)"/>
                        <xsl:choose>
                            <xsl:when test="$iLines &gt; 3">
                                <!-- try to guarantee at least 2 lines on this page -->
                                <xsl:choose>
                                    <xsl:when test="exampleHeading">
                                        <xsl:text>4</xsl:text>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:text>3</xsl:text>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:when>
                            <xsl:otherwise>
                                <!-- try to keep it all on same page -->
                                <xsl:value-of select="$iLines + 1"/>
                            </xsl:otherwise>
                        </xsl:choose>
                        <tex:spec cat="esc"/>baselineskip</tex:parm>
                </tex:cmd>
            </xsl:when>
            <xsl:when test="table">
                <tex:cmd name="XLingPaperneedspace">
                    <tex:parm>
                        <xsl:choose>
                            <xsl:when test="contains(@XeLaTeXSpecial,'needspace')">
                                <xsl:call-template name="HandleXeLaTeXSpecialCommand">
                                    <xsl:with-param name="sPattern" select="'needspace='"/>
                                    <xsl:with-param name="default" select="'1'"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:variable name="iMinRows" select="count(table/descendant-or-self::tr) + count(table/caption)  + count(exampleHeading)"/>
                                <xsl:variable name="iLines">
                                    <xsl:choose>
                                        <xsl:when test="table/@border=1">
                                            <xsl:choose>
                                                <xsl:when test="table/descendant::th">2</xsl:when>
                                                <xsl:otherwise>1</xsl:otherwise>
                                            </xsl:choose>
                                        </xsl:when>
                                        <xsl:otherwise>0</xsl:otherwise>
                                    </xsl:choose>
                                </xsl:variable>
                                <xsl:variable name="iInterlinearLines" select="count(table/descendant-or-self::tr/td[1]/descendant::line)"/>
                                <xsl:variable name="iInterlinearFrees"
                                    select="count(table/descendant-or-self::tr/td[1]/descendant::free) + count(table/descendant-or-self::tr/td[1]/descendant::literal)"/>
                                <xsl:variable name="iMinLines" select="$iMinRows + $iLines + $iInterlinearLines + $iInterlinearFrees"/>
                                <xsl:choose>
                                    <!-- assume if it is greater than 10, then we will get a page break somewhere within the example -->
                                    <xsl:when test="$iMinLines &gt; 10">10</xsl:when>
                                    <xsl:otherwise>
                                        <xsl:value-of select="$iMinLines"/>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:otherwise>
                        </xsl:choose>
                        <tex:spec cat="esc"/>
                        <xsl:text>baselineskip</xsl:text>
                    </tex:parm>
                </tex:cmd>
            </xsl:when>
            <xsl:when test="chart/ul or chart/ol">
                <tex:cmd name="XLingPaperneedspace">
                    <tex:parm>
                        <xsl:variable name="iLines" select="count(descendant::li)"/>
                        <xsl:choose>
                            <xsl:when test="$iLines &gt; 3">
                                <!-- try to guarantee at least 2 lines on this page -->
                                <xsl:text>3</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <!-- try to keep it all on same page -->
                                <xsl:value-of select="$iLines + 1"/>
                            </xsl:otherwise>
                        </xsl:choose>
                        <tex:spec cat="esc"/>baselineskip</tex:parm>
                </tex:cmd>
            </xsl:when>
            <xsl:when test="word/word">
                <tex:cmd name="XLingPaperneedspace">
                    <tex:parm>
                        <xsl:variable name="iLines" select="count(descendant::word)"/>
                        <xsl:choose>
                            <xsl:when test="$iLines &gt; 3">
                                <!-- try to guarantee at least 2 lines on this page -->
                                <xsl:text>3</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <!-- try to keep it all on same page -->
                                <xsl:value-of select="$iLines + 1"/>
                            </xsl:otherwise>
                        </xsl:choose>
                        <tex:spec cat="esc"/>baselineskip</tex:parm>
                </tex:cmd>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  
        SetFootnoteCounterIfNeeded
    -->
    <xsl:template name="SetFootnoteCounterIfNeeded">
        <xsl:param name="bInTableNumbered" select="'N'"/>
        <xsl:if test="descendant::endnote">
            <xsl:call-template name="SetLaTeXFootnoteCounter">
                <xsl:with-param name="bInTableNumbered" select="$bInTableNumbered"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--  
        SetFootnoteLayout
    -->
    <xsl:template name="SetFootnoteLayout">
        <!--\renewcommand{\footnotelayout}{\doublespacing}
        \newlength{\myfootnotesep}
        \setlength{\myfootnotesep}{\baselineskip}
        \addtolength{\myfootnotesep}{-\footnotesep}
        \setlength{\footnotesep}{\myfootnotesep} % set spacing between footnotes-->
        <tex:cmd name="renewcommand" nl1="1">
            <tex:parm>
                <tex:cmd name="footnotelayout" gr="0"/>
            </tex:parm>
            <tex:parm>
                <xsl:choose>
                    <xsl:when test="$sLineSpacing='double'">
                        <tex:cmd name="doublespacing" gr="0"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <tex:cmd name="onehalfspacing" gr="0"/>
                    </xsl:otherwise>
                </xsl:choose>
                <tex:cmd name="footnotesize" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPaperfootnotesep" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="setlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPaperfootnotesep" gr="0"/>
            </tex:parm>
            <tex:parm>
                <tex:cmd name="baselineskip" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="addtolength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPaperfootnotesep" gr="0"/>
            </tex:parm>
            <tex:parm>
                <xsl:text>-</xsl:text>
                <tex:cmd name="footnotesep" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="setlength" nl1="1">
            <tex:parm>
                <tex:cmd name="footnotesep" gr="0"/>
            </tex:parm>
            <tex:parm>
                <tex:cmd name="XLingPaperfootnotesep" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:spec cat="comment"/>
        <xsl:text> set spacing between footnotes
</xsl:text>
    </xsl:template>
    <!--  
        SetFramedTypeItem
    -->
    <xsl:template name="SetFramedTypeItem">
        <xsl:param name="sAttributeValue"/>
        <xsl:param name="sDefaultValue"/>
        <xsl:param name="bUseBaselineskipAsDefault" select="'N'"/>
        <xsl:choose>
            <xsl:when test="string-length($sAttributeValue) &gt; 0">
                <xsl:value-of select="$sAttributeValue"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="$bUseBaselineskipAsDefault='Y'">
                        <tex:cmd name="baselineskip" gr="0"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$sDefaultValue"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        SetFramedTypes
    -->
    <xsl:template name="SetFramedTypes">
        <xsl:for-each select="//framedType">
            <xsl:variable name="sColor" select="normalize-space(@backgroundcolor)"/>
            <xsl:if test="string-length($sColor) &gt; 0">
                <tex:cmd name="definecolor" nl2="1">
                    <tex:parm>
                        <xsl:call-template name="GetFramedTypeBackgroundColorName">
                            <xsl:with-param name="sId" select="@id"/>
                        </xsl:call-template>
                    </tex:parm>
                    <tex:parm>HTML</tex:parm>
                    <tex:parm>
                        <xsl:call-template name="GetColorHexCode">
                            <xsl:with-param name="sColor" select="$sColor"/>
                        </xsl:call-template>
                    </tex:parm>
                </tex:cmd>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>
    <!--  
        SetHeaderFooterRuleWidth
    -->
    <xsl:template name="SetHeaderFooterRuleWidth">
        <xsl:param name="rulepattern"/>
        <xsl:param name="rulewidth"/>
        <tex:parm>
            <xsl:choose>
                <xsl:when test="not($rulepattern)">
                    <xsl:text>0pt</xsl:text>
                </xsl:when>
                <xsl:when test="$rulepattern='rule' or $rulepattern='dots'">
                    <xsl:choose>
                        <xsl:when test="string-length($rulewidth) &gt; 0">
                            <xsl:value-of select="$rulewidth"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>0pt</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>0pt</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </tex:parm>
    </xsl:template>
    <!--  
        SetHeaderFooterRuleDots
    -->
    <xsl:template name="SetHeaderFooterRuleDots">
        <xsl:param name="rulepattern"/>
        <xsl:param name="rule"/>
        <xsl:param name="fDoDots" select="'Y'"/>
        <xsl:choose>
            <xsl:when test="$rulepattern='dots'">
                <xsl:call-template name="SetHeaderFooterRuleDotsProper">
                    <xsl:with-param name="rule" select="$rule"/>
                    <xsl:with-param name="fDoDots" select="$fDoDots"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$fFooterUsesDots and $rule='footrule'">
                <xsl:call-template name="SetHeaderFooterRuleDotsProper">
                    <xsl:with-param name="rule" select="$rule"/>
                    <xsl:with-param name="fDoDots" select="'N'"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$fHeaderUsesDots and $rule='headrule'">
                <xsl:call-template name="SetHeaderFooterRuleDotsProper">
                    <xsl:with-param name="rule" select="$rule"/>
                    <xsl:with-param name="fDoDots" select="'N'"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  
        SetHeaderFooterRuleDotsProper
    -->
    <xsl:template name="SetHeaderFooterRuleDotsProper">
        <xsl:param name="rule"/>
        <xsl:param name="fDoDots"/>
        <tex:cmd name="renewcommand" nl2="1">
            <tex:parm>
                <tex:cmd name="{$rule}" gr="0"/>
            </tex:parm>
            <tex:parm>
                <tex:cmd name="vbox" gr="0"/>
                <xsl:text> to 0pt</xsl:text>
                <tex:parm>
                    <tex:cmd name="hbox" gr="0"/>
                    <xsl:text> to</xsl:text>
                    <tex:cmd name="headwidth" gr="0"/>
                    <tex:parm>
                        <xsl:choose>
                            <xsl:when test="$fDoDots='Y'">
                                <tex:cmd name="dotfill" gr="0"/>
                            </xsl:when>
                        </xsl:choose>
                    </tex:parm>
                    <tex:cmd name="vss" gr="0"/>
                </tex:parm>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetHeaderFooterRuleWidths
    -->
    <xsl:template name="SetHeaderFooterRuleWidths">
        <xsl:param name="layoutInfo"/>
        <xsl:choose>
            <xsl:when test="$layoutInfo">
                <xsl:variable name="headrulepattern" select="exsl:node-set($layoutInfo)/descendant::header[1]/@rulebelowpattern"/>
                <xsl:variable name="footrulepattern" select="exsl:node-set($layoutInfo)/descendant::footer[1]/@ruleabovepattern"/>
                <tex:cmd name="renewcommand" nl2="1">
                    <tex:parm>
                        <tex:cmd name="headrulewidth" gr="0"/>
                    </tex:parm>
                    <xsl:variable name="rulewidth" select="exsl:node-set($layoutInfo)/descendant::header[1]/@rulebelowwidth"/>
                    <xsl:call-template name="SetHeaderFooterRuleWidth">
                        <xsl:with-param name="rulepattern" select="$headrulepattern"/>
                        <xsl:with-param name="rulewidth" select="$rulewidth"/>
                    </xsl:call-template>
                </tex:cmd>
                <xsl:call-template name="SetHeaderFooterRuleDots">
                    <xsl:with-param name="rulepattern" select="$headrulepattern"/>
                    <xsl:with-param name="rule" select="'headrule'"/>
                </xsl:call-template>
                <tex:cmd name="renewcommand" nl2="1">
                    <tex:parm>
                        <tex:cmd name="footrulewidth" gr="0"/>
                    </tex:parm>
                    <xsl:variable name="rulewidth" select="exsl:node-set($layoutInfo)/descendant::footer[1]/@ruleabovewidth"/>
                    <xsl:call-template name="SetHeaderFooterRuleWidth">
                        <xsl:with-param name="rulepattern" select="$footrulepattern"/>
                        <xsl:with-param name="rulewidth" select="$rulewidth"/>
                    </xsl:call-template>
                </tex:cmd>
                <xsl:call-template name="SetHeaderFooterRuleDots">
                    <xsl:with-param name="rulepattern" select="$footrulepattern"/>
                    <xsl:with-param name="rule" select="'footrule'"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <tex:cmd name="renewcommand" nl2="1">
                    <tex:parm>
                        <tex:cmd name="headrulewidth" gr="0"/>
                    </tex:parm>
                    <tex:parm>0pt</tex:parm>
                </tex:cmd>
                <tex:cmd name="renewcommand" nl2="1">
                    <tex:parm>
                        <tex:cmd name="footrulewidth" gr="0"/>
                    </tex:parm>
                    <tex:parm>0pt</tex:parm>
                </tex:cmd>
            </xsl:otherwise>
        </xsl:choose>       
    </xsl:template>
    <!--  
        SetImgWidths
    -->
    <xsl:template name="SetImgWidths">
        <!-- img elements are handled differently -->
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPaperImgInExampleWidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPaperImgInFigureWidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="setlength">
            <tex:parm>
                <tex:cmd name="XLingPaperImgInExampleWidth" gr="0"/>
            </tex:parm>
            <tex:parm>
                <tex:cmd name="textwidth" gr="0" nl2="0"/>
                <xsl:text> - </xsl:text>
                <xsl:value-of select="$sExampleIndentBefore"/>
                <xsl:text> - </xsl:text>
                <xsl:value-of select="$sExampleIndentAfter"/>
                <xsl:text> - </xsl:text>
                <xsl:value-of select="$iNumberWidth"/>
                <xsl:text>em</xsl:text>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="setlength">
            <tex:parm>
                <tex:cmd name="XLingPaperImgInFigureWidth" gr="0"/>
            </tex:parm>
            <tex:parm>
                <tex:cmd name="textwidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetInterlinearSourceLength
    -->
    <xsl:template name="SetInterlinearSourceLength">
        <xsl:if test="$bAutomaticallyWrapInterlinears='yes' and $sInterlinearSourceStyle='AfterFirstLine'">
            <tex:cmd name="newlength" nl1="1">
                <tex:parm>
                    <tex:cmd name="{$sTeXInterlinearSourceWidth}" gr="0" nl2="0"/>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="newlength" nl1="1">
                <tex:parm>
                    <tex:cmd name="{$sTeXInterlinearSourceGapWidth}" gr="0" nl2="0"/>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="settowidth" nl1="1">
                <tex:parm>
                    <tex:cmd name="{$sTeXInterlinearSourceGapWidth}" gr="0" nl2="0"/>
                </tex:parm>
                <tex:parm>
                    <xsl:text disable-output-escaping="yes">&#xa0;&#xa0;</xsl:text>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
    </xsl:template>
    <!--  
        SetListLengths
    -->
    <xsl:template name="SetListLengths">
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'setlength'"/>
            <xsl:with-param name="sCommandToSet" select="'topsep'"/>
            <xsl:with-param name="sValue" select="'0pt'"/>
        </xsl:call-template>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'setlength'"/>
            <xsl:with-param name="sCommandToSet" select="'partopsep'"/>
            <xsl:with-param name="sValue" select="'0pt'"/>
        </xsl:call-template>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'setlength'"/>
            <xsl:with-param name="sCommandToSet" select="'itemsep'"/>
            <xsl:with-param name="sValue" select="'0pt'"/>
        </xsl:call-template>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'setlength'"/>
            <xsl:with-param name="sCommandToSet" select="'parsep'"/>
            <xsl:with-param name="sValue" select="'0pt'"/>
        </xsl:call-template>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'setlength'"/>
            <xsl:with-param name="sCommandToSet" select="'parskip'"/>
            <xsl:with-param name="sValue" select="'0pt'"/>
        </xsl:call-template>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'setlength'"/>
            <xsl:with-param name="sCommandToSet" select="'leftmargini'"/>
            <xsl:with-param name="sValue" select="'1em'"/>
        </xsl:call-template>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'setlength'"/>
            <xsl:with-param name="sCommandToSet" select="'leftmarginii'"/>
            <xsl:with-param name="sValue" select="'1em'"/>
        </xsl:call-template>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'setlength'"/>
            <xsl:with-param name="sCommandToSet" select="'leftmarginiii'"/>
            <xsl:with-param name="sValue" select="'1em'"/>
        </xsl:call-template>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'setlength'"/>
            <xsl:with-param name="sCommandToSet" select="'leftmarginiv'"/>
            <xsl:with-param name="sValue" select="'1em'"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        SetListLengthWidths
    -->
    <xsl:template name="SetListLengthWidths">
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPaperlistinexampleindent" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPaperisocodewidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'setlength'"/>
            <xsl:with-param name="sCommandToSet" select="'XLingPaperlistinexampleindent'"/>
            <xsl:with-param name="sValue">
                <xsl:choose>
                    <xsl:when test="string-length($sExampleIndentBefore) &gt; 0">
                        <xsl:value-of select="$sExampleIndentBefore"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>.125in</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:text>+ 2.75em</xsl:text>
            </xsl:with-param>
        </xsl:call-template>
        <xsl:if test="//example/annotationRef">
            <tex:cmd name="newlength" nl1="1">
                <tex:parm>
                    <tex:cmd name="XLingPaperannoinexampleindent" gr="0" nl2="0"/>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="setlength" nl1="1">
                <tex:parm>
                    <tex:cmd name="XLingPaperannoinexampleindent" gr="0" nl2="0"/>
                </tex:parm>
                <tex:parm>
                    <tex:cmd name="XLingPaperlistinexampleindent" gr="0" nl2="0"/>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="addtolength" nl1="1">
                <tex:parm>
                    <tex:cmd name="XLingPaperannoinexampleindent" gr="0" nl2="0"/>
                </tex:parm>
                <tex:parm>
                    <xsl:variable name="sStartIndent" select="normalize-space(exsl:node-set($annotationLayoutInfo)/@start-indent)"/>
                    <xsl:choose>
                        <xsl:when test="string-length($sStartIndent) &gt; 0">
                            <xsl:value-of select="$sStartIndent"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>.25in</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPaperlistitemindent" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPaperbulletlistitemwidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
            <xsl:with-param name="sCommandToSet" select="'XLingPaperbulletlistitemwidth'"/>
            <xsl:with-param name="sValue">
                <xsl:value-of select="$sBulletPoint"/>
                <tex:spec cat="esc"/>
                <xsl:text>&#x20;</xsl:text>
            </xsl:with-param>
        </xsl:call-template>
        <tex:cmd name="newlength" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPapersingledigitlistitemwidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
            <xsl:with-param name="sCommandToSet" select="'XLingPapersingledigitlistitemwidth'"/>
            <xsl:with-param name="sValue">
                <xsl:call-template name="InsertFontSizeIfNeeded"/>
                <xsl:text>8.</xsl:text>
                <tex:spec cat="esc"/>
                <xsl:text>&#x20;</xsl:text>
            </xsl:with-param>
        </xsl:call-template>
        <tex:cmd name="newlength" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPaperdoubledigitlistitemwidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
            <xsl:with-param name="sCommandToSet" select="'XLingPaperdoubledigitlistitemwidth'"/>
            <xsl:with-param name="sValue">
                <xsl:call-template name="InsertFontSizeIfNeeded"/>
                <xsl:text>88.</xsl:text>
                <tex:spec cat="esc"/>
                <xsl:text>&#x20;</xsl:text>
            </xsl:with-param>
        </xsl:call-template>
        <tex:cmd name="newlength" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPapertripledigitlistitemwidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
            <xsl:with-param name="sCommandToSet" select="'XLingPapertripledigitlistitemwidth'"/>
            <xsl:with-param name="sValue">
                <xsl:call-template name="InsertFontSizeIfNeeded"/>
                <xsl:text>888.</xsl:text>
                <tex:spec cat="esc"/>
                <xsl:text>&#x20;</xsl:text>
            </xsl:with-param>
        </xsl:call-template>
        <tex:cmd name="newlength" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPapersingleletterlistitemwidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
            <xsl:with-param name="sCommandToSet" select="'XLingPapersingleletterlistitemwidth'"/>
            <xsl:with-param name="sValue">
                <xsl:call-template name="InsertFontSizeIfNeeded"/>
                <xsl:text>m.</xsl:text>
                <tex:spec cat="esc"/>
                <xsl:text>&#x20;</xsl:text>
            </xsl:with-param>
        </xsl:call-template>
        <tex:cmd name="newlength" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPaperdoubleletterlistitemwidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
            <xsl:with-param name="sCommandToSet" select="'XLingPaperdoubleletterlistitemwidth'"/>
            <xsl:with-param name="sValue">
                <xsl:call-template name="InsertFontSizeIfNeeded"/>
                <xsl:text>mm.</xsl:text>
                <tex:spec cat="esc"/>
                <xsl:text>&#x20;</xsl:text>
            </xsl:with-param>
        </xsl:call-template>
        <tex:cmd name="newlength" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPapertripleletterlistitemwidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
            <xsl:with-param name="sCommandToSet" select="'XLingPapertripleletterlistitemwidth'"/>
            <xsl:with-param name="sValue">
                <xsl:call-template name="InsertFontSizeIfNeeded"/>
                <xsl:text>mmm.</xsl:text>
                <tex:spec cat="esc"/>
                <xsl:text>&#x20;</xsl:text>
            </xsl:with-param>
        </xsl:call-template>
        <tex:cmd name="newlength" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPaperromanviilistitemwidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
            <xsl:with-param name="sCommandToSet" select="'XLingPaperromanviilistitemwidth'"/>
            <xsl:with-param name="sValue">
                <xsl:call-template name="InsertFontSizeIfNeeded"/>
                <xsl:text>vii.</xsl:text>
                <tex:spec cat="esc"/>
                <xsl:text>&#x20;</xsl:text>
            </xsl:with-param>
        </xsl:call-template>
        <tex:cmd name="newlength" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPaperromanviiilistitemwidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
            <xsl:with-param name="sCommandToSet" select="'XLingPaperromanviiilistitemwidth'"/>
            <xsl:with-param name="sValue">
                <xsl:call-template name="InsertFontSizeIfNeeded"/>
                <xsl:text>viii.</xsl:text>
                <tex:spec cat="esc"/>
                <xsl:text>&#x20;</xsl:text>
            </xsl:with-param>
        </xsl:call-template>
        <tex:cmd name="newlength" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPaperromanxviiilistitemwidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
            <xsl:with-param name="sCommandToSet" select="'XLingPaperromanxviiilistitemwidth'"/>
            <xsl:with-param name="sValue">
                <xsl:call-template name="InsertFontSizeIfNeeded"/>
                <xsl:text>xviii.</xsl:text>
                <tex:spec cat="esc"/>
                <xsl:text>&#x20;</xsl:text>
            </xsl:with-param>
        </xsl:call-template>
        <tex:cmd name="newlength" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPaperspacewidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
            <xsl:with-param name="sCommandToSet" select="'XLingPaperspacewidth'"/>
            <xsl:with-param name="sValue">
                <tex:spec cat="esc"/>
                <xsl:text>&#x20;</xsl:text>
            </xsl:with-param>
        </xsl:call-template>
        <xsl:if test="//ol[string-length(@numberFormat)&gt;0]">
            <tex:cmd name="newlength" nl2="1">
                <tex:parm>
                    <tex:cmd name="XLingPaperdynamiclistitemonewidth" gr="0" nl2="0"/>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="newlength" nl2="1">
                <tex:parm>
                    <tex:cmd name="XLingPaperdynamiclistitemtwowidth" gr="0" nl2="0"/>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="newlength" nl2="1">
                <tex:parm>
                    <tex:cmd name="XLingPaperdynamiclistitemthreewidth" gr="0" nl2="0"/>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="newlength" nl2="1">
                <tex:parm>
                    <tex:cmd name="XLingPaperdynamiclistitemfourwidth" gr="0" nl2="0"/>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="newlength" nl2="1">
                <tex:parm>
                    <tex:cmd name="XLingPaperdynamiclistitemfivewidth" gr="0" nl2="0"/>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="newlength" nl2="1">
                <tex:parm>
                    <tex:cmd name="XLingPaperdynamiclistitemsixwidth" gr="0" nl2="0"/>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="newlength" nl2="1">
                <tex:parm>
                    <tex:cmd name="XLingPaperdynamiclistitemsevenwidth" gr="0" nl2="0"/>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="newlength" nl2="1">
                <tex:parm>
                    <tex:cmd name="XLingPaperdynamiclistitemeightwidth" gr="0" nl2="0"/>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="newlength" nl2="1">
                <tex:parm>
                    <tex:cmd name="XLingPaperdynamiclistitemninewidth" gr="0" nl2="0"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
    </xsl:template>

    <!--  
        SetMetadata
    -->
    <xsl:template name="SetMetadata">
        <xsl:text>pdfauthor=</xsl:text>
        <tex:parm>
            <xsl:call-template name="SetMetadataAuthor"/>
        </tex:parm>
        <xsl:text>, pdfcreator=</xsl:text>
        <tex:parm>
            <xsl:call-template name="SetMetadataCreator"/>
        </tex:parm>
        <xsl:if test="exsl:node-set($lingPaper)/frontMatter/title != ''">
            <xsl:text>, pdftitle=</xsl:text>
            <tex:parm>
                <xsl:call-template name="SetMetadataTitle"/>
            </tex:parm>
        </xsl:if>
        <xsl:if test="string-length(exsl:node-set($lingPaper)/publishingInfo/keywords) &gt; 0">
            <xsl:text>, pdfkeywords=</xsl:text>
            <tex:parm>
                <xsl:call-template name="SetMetadataKeywords"/>
            </tex:parm>
        </xsl:if>
    </xsl:template>
    <!--  
        SetPageLayoutParameters
    -->
    <xsl:template name="SetPageLayoutParameters">
        <tex:cmd name="setlength" nl2="1">
            <tex:parm>
                <tex:cmd name="paperheight" gr="0"/>
            </tex:parm>
            <tex:parm>
                <xsl:call-template name="AdjustLayoutParameterUnitName">
                    <xsl:with-param name="sLayoutParam" select="$sPageHeight"/>
                </xsl:call-template>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="setlength" nl2="1">
            <tex:parm>
                <tex:cmd name="paperwidth" gr="0"/>
            </tex:parm>
            <tex:parm>
                <xsl:call-template name="AdjustLayoutParameterUnitName">
                    <xsl:with-param name="sLayoutParam" select="$sPageWidth"/>
                </xsl:call-template>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="setlength" nl2="1">
            <tex:parm>
                <tex:cmd name="topmargin" gr="0"/>
            </tex:parm>
            <tex:parm>0pt</tex:parm>
        </tex:cmd>
        <tex:cmd name="setlength" nl2="1">
            <tex:parm>
                <tex:cmd name="voffset" gr="0"/>
            </tex:parm>
            <tex:parm>
                <xsl:variable name="sPageTopMarginToAdjust">
                    <!--<xsl:variable name="iPageTopMargin">
                        <xsl:call-template name="GetMeasure">
                            <xsl:with-param name="sValue" select="$sPageTopMargin"/>
                        </xsl:call-template>
                    </xsl:variable>-->
                    <xsl:call-template name="SubtractOneInch">
                        <xsl:with-param name="sValue" select="'pt'"/>
                        <!-- the .15in makes it match what we got with FO - I'm not sure why, though -->
                        <xsl:with-param name="iValue" select="$iPageTopMargin"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:call-template name="AdjustLayoutParameterUnitName">
                    <xsl:with-param name="sLayoutParam" select="$sPageTopMarginToAdjust"/>
                </xsl:call-template>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="setlength" nl2="1">
            <tex:parm>
                <tex:cmd name="evensidemargin" gr="0"/>
            </tex:parm>
            <tex:parm>
                <xsl:variable name="sEvenSideMarginToAdjust">
                    <xsl:choose>
                        <xsl:when test="exsl:node-set($pageLayoutInfo)/useThesisSubmissionStyle/@singlesided='yes'">
                            <xsl:call-template name="SubtractOneInch">
                                <xsl:with-param name="sValue" select="'pt'"/>
                                <xsl:with-param name="iValue" select="$iPageInsideMargin"/>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="SubtractOneInch">
                                <xsl:with-param name="sValue" select="'pt'"/>
                                <xsl:with-param name="iValue" select="$iPageOutsideMargin"/>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:call-template name="AdjustLayoutParameterUnitName">
                    <xsl:with-param name="sLayoutParam" select="$sEvenSideMarginToAdjust"/>
                </xsl:call-template>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="setlength" nl2="1">
            <tex:parm>
                <tex:cmd name="oddsidemargin" gr="0"/>
            </tex:parm>
            <tex:parm>
                <xsl:variable name="sOddSideMarginToAdjust">
                    <xsl:call-template name="SubtractOneInch">
                        <xsl:with-param name="sValue" select="'pt'"/>
                        <xsl:with-param name="iValue" select="$iPageInsideMargin"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:call-template name="AdjustLayoutParameterUnitName">
                    <xsl:with-param name="sLayoutParam" select="$sOddSideMarginToAdjust"/>
                </xsl:call-template>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="setlength" nl2="1">
            <tex:parm>
                <tex:cmd name="textwidth" gr="0"/>
            </tex:parm>
            <tex:parm>
                <xsl:variable name="sTextWidthToAdjust">
                    <xsl:value-of select="number($iPageWidth - $iPageInsideMargin - $iPageOutsideMargin)"/>
                    <xsl:text>pt</xsl:text>
                    <!--<xsl:call-template name="GetUnitOfMeasure">
                        <xsl:with-param name="sValue" select="$sPageWidth"/>
                    </xsl:call-template>-->
                </xsl:variable>
                <xsl:call-template name="AdjustLayoutParameterUnitName">
                    <xsl:with-param name="sLayoutParam" select="$sTextWidthToAdjust"/>
                </xsl:call-template>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="setlength" nl2="1">
            <tex:parm>
                <tex:cmd name="textheight" gr="0"/>
            </tex:parm>
            <tex:parm>
                <xsl:variable name="sTextHeightToAdjust">
                    <xsl:value-of select="number($iPageHeight - $iPageTopMargin - $iPageBottomMargin - $iHeaderMargin - $iFooterMargin)"/>
                    <xsl:text>pt</xsl:text>
                    <!--<xsl:call-template name="GetUnitOfMeasure">
                        <xsl:with-param name="sValue" select="$sPageHeight"/>
                    </xsl:call-template>-->
                </xsl:variable>
                <xsl:call-template name="AdjustLayoutParameterUnitName">
                    <xsl:with-param name="sLayoutParam" select="$sTextHeightToAdjust"/>
                </xsl:call-template>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="setlength" nl2="1">
            <tex:parm>
                <tex:cmd name="headheight" gr="0"/>
            </tex:parm>
            <tex:parm>
                <!-- head height needs to be about 2 points larger -->
                <!--                <xsl:variable name="iDefault" select="$sBasicPointSize + 2.5"/>
                <xsl:choose>
                    <xsl:when test="$iDefault &gt;= 13.59999">
                        <xsl:value-of select="$iDefault"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>13.59999</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
-->
                <!-- head height needs to be about 2 points larger -->
                <xsl:value-of select="$sBasicPointSize + 2.5"/>
                <xsl:text>pt</xsl:text>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="setlength" nl2="1">
            <tex:parm>
                <tex:cmd name="headsep" gr="0"/>
            </tex:parm>
            <tex:parm>
                <xsl:variable name="iHeaderMarginAsPoints">
                    <xsl:call-template name="ConvertToPoints">
                        <xsl:with-param name="sValue" select="'pt'"/>
                        <xsl:with-param name="iValue" select="$iHeaderMargin"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:value-of select="number($iHeaderMarginAsPoints - $sBasicPointSize - 2)"/>
                <xsl:text>pt</xsl:text>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="setlength" nl2="1">
            <tex:parm>
                <tex:cmd name="footskip" gr="0"/>
            </tex:parm>
            <tex:parm>
                <xsl:call-template name="AdjustLayoutParameterUnitName">
                    <xsl:with-param name="sLayoutParam" select="$sFooterMargin"/>
                </xsl:call-template>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="SetStartingPageNumber"/>
        <xsl:variable name="sFootnoteIndent" select="normalize-space(exsl:node-set($pageLayoutInfo)/footnoteIndent)"/>
        <xsl:if test="string-length($sFootnoteIndent)&gt;0">
            <tex:cmd name="makeatletter" gr="0" nl2="1"/>
            <tex:cmd name="renewcommand" gr="0"/>
            <tex:cmd name="@makefntext">
                <tex:opt>1</tex:opt>
                <tex:parm>
                    <tex:cmd name="hskip" gr="0"/>
                    <xsl:value-of select="$sFootnoteIndent"/>
                    <tex:cmd name="@makefnmark" gr="0"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>1</xsl:text>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="makeatother" gr="0" nl1="1" nl2="1"/>
        </xsl:if>
        <xsl:if test="contains(@XeLaTeXSpecial,'overfullhbox')">
            <xsl:variable name="sValue">
                <xsl:call-template name="GetXeLaTeXSpecialCommand">
                    <xsl:with-param name="sAttr" select="'overfullhbox='"/>
                    <xsl:with-param name="sDefaultValue" select="'5pt'"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:if test="string-length($sValue) &gt; 0">
                <tex:cmd name="setlength" nl2="1">
                    <tex:parm>
                        <tex:cmd name="overfullrule" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <xsl:value-of select="$sValue"/>
                    </tex:parm>
                </tex:cmd>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        SetSpecialTextSymbols
    -->
    <xsl:template name="SetSpecialTextSymbols">
        <tex:cmd name="DeclareTextSymbol" nl2="1">
            <tex:parm>
                <tex:cmd name="textsquarebracketleft" gr="0"/>
            </tex:parm>
            <tex:parm>EU1</tex:parm>
            <tex:parm>91</tex:parm>
        </tex:cmd>
        <tex:cmd name="DeclareTextSymbol" nl2="1">
            <tex:parm>
                <tex:cmd name="textsquarebracketright" gr="0"/>
            </tex:parm>
            <tex:parm>EU1</tex:parm>
            <tex:parm>93</tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetAbbrInTableBaselineskip
    -->
    <xsl:template name="SetAbbrInTableBaselineskip">
        <xsl:if test="descendant::abbreviationsShownHere[not(ancestor::p)]">
            <tex:cmd name="newlength">
                <tex:parm>
                    <tex:spec cat="esc"/>
                    <xsl:value-of select="$sTeXAbbrBaselineskip"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
    </xsl:template>
    <!--  
        SetClubWidowPenalties
    -->
    <xsl:template name="SetClubWidowPenalties">
        <xsl:param name="iPenalty" select="'10000'"/>
        <tex:cmd name="clubpenalty" gr="0" nl1="1"/>
        <xsl:text>=</xsl:text>
        <xsl:value-of select="$iPenalty"/>
        <xsl:text>&#xa;</xsl:text>
        <tex:cmd name="widowpenalty" gr="0"/>
        <xsl:text>=</xsl:text>
        <xsl:value-of select="$iPenalty"/>
    </xsl:template>
    <!--  
        SetStartingPageNumber
    -->
    <xsl:template name="SetStartingPageNumber">
        <xsl:param name="startingPageNumber" select="exsl:node-set($lingPaper)/publishingInfo/@startingPageNumber"/>
        <xsl:variable name="sStartingPageNumber" select="normalize-space($startingPageNumber)"/>
        <xsl:if test="string-length($sStartingPageNumber) &gt; 0">
            <tex:cmd name="setcounter">
                <tex:parm>
                    <xsl:text>page</xsl:text>
                </tex:parm>
                <tex:parm>
                    <xsl:value-of select="$sStartingPageNumber"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
    </xsl:template>
    <!--  
        SetStartingPageNumberInBook
    -->
    <xsl:template name="SetStartingPageNumberInBook">
        <xsl:variable name="sStartingPageNumberInBook" select="normalize-space(exsl:node-set($lingPaper)/publishingInfo/@startingPageNumberInBook)"/>
        <xsl:if test="string-length($sStartingPageNumberInBook) &gt; 0">
            <tex:cmd name="setcounter">
                <tex:parm>
                    <xsl:text>page</xsl:text>
                </tex:parm>
                <tex:parm>
                    <xsl:value-of select="$sStartingPageNumberInBook"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
    </xsl:template>
    <!--  
        SetTableLengthWidths
    -->
    <xsl:template name="SetTableLengthWidths">
        <tex:cmd name="newsavebox" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapertempbox" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapertemplen" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPaperavailabletablewidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapertableminwidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapertablemaxwidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapertablewidthminustableminwidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapertablemaxwidthminusminwidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapertablewidthratio" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincola" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcola" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercolawidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincolb" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcolb" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercolbwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincolc" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcolc" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercolcwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincold" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcold" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercoldwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincole" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcole" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercolewidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincolf" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcolf" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercolfwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincolg" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcolg" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercolgwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincolh" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcolh" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercolhwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincoli" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcoli" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercoliwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincolj" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcolj" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercoljwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincolk" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcolk" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercolkwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincoll" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcoll" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercollwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincolm" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcolm" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercolmwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincoln" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcoln" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercolnwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincolo" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcolo" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercolowidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincolp" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcolp" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercolpwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincolq" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcolq" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercolqwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincolr" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcolr" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercolrwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincols" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcols" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercolswidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincolt" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcolt" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercoltwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincolu" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcolu" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercoluwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincolv" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcolv" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercolvwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincolw" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcolw" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercolwwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincolx" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcolx" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercolxwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincoly" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcoly" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercolywidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapermincolz" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapermaxcolz" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength">
            <tex:parm>
                <tex:cmd name="XLingPapercolzwidth" gr="0"/>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetTeXCommand
    -->
    <xsl:template name="SetTeXCommand">
        <xsl:param name="sTeXCommand"/>
        <xsl:param name="sCommandToSet"/>
        <xsl:param name="sValue"/>
        <tex:cmd name="{$sTeXCommand}">
            <tex:parm>
                <tex:cmd name="{$sCommandToSet}" gr="0" nl2="0"/>
            </tex:parm>
            <tex:parm>
                <xsl:copy-of select="$sValue"/>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetTOClengths
    -->
    <xsl:template name="SetTOClengths">
        <tex:cmd name="newlength" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPaperpnumwidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newlength" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPapertocrmarg" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <xsl:variable name="sMaxPageNumberLengthInContents">
            <xsl:for-each select="document($sTableOfContentsFile)/toc/tocline">
                <xsl:sort data-type="number" order="descending" select="string-length(@page)"/>
                <xsl:if test="position()=1">
                    <xsl:value-of select="string-length(@page)"/>
                </xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'setlength'"/>
            <xsl:with-param name="sCommandToSet" select="'XLingPaperpnumwidth'"/>
            <xsl:with-param name="sValue">
                <xsl:choose>
                    <xsl:when test="$sMaxPageNumberLengthInContents &gt; 0">
                        <xsl:choose>
                            <xsl:when test="$sMaxPageNumberLengthInContents = 1">1.05em</xsl:when>
                            <xsl:when test="$sMaxPageNumberLengthInContents = 2">1.55em</xsl:when>
                            <xsl:when test="$sMaxPageNumberLengthInContents = 3">2.05em</xsl:when>
                            <xsl:otherwise>2.55em</xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:otherwise>1.55em</xsl:otherwise>
                </xsl:choose>
            </xsl:with-param>
        </xsl:call-template>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'setlength'"/>
            <xsl:with-param name="sCommandToSet" select="'XLingPapertocrmarg'"/>
            <xsl:with-param name="sValue">
                <tex:cmd name="XLingPaperpnumwidth" gr="0" nl2="0"/>
                <xsl:text>+1em</xsl:text>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--  
        SetUsePackages
    -->
    <xsl:template name="SetUsePackages">
        <xsl:variable name="sHyphenationLanguage">
            <xsl:call-template name="GetHyphenationLanguage"/>
        </xsl:variable>
        <xsl:if test="string-length($sHyphenationLanguage) &gt; 0">
            <tex:cmd name="usepackage" nl2="1">
                <tex:parm>polyglossia</tex:parm>
            </tex:cmd>
            <tex:cmd name="setmainlanguage">
                <tex:parm>
                    <xsl:value-of select="$sHyphenationLanguage"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:if test="//framedUnit | //framedType">
            <tex:cmd name="usepackage" nl2="1">
                <tex:opt>framemethod=TikZ</tex:opt>
                <tex:parm>mdframed</tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:if test="//mediaObject">
            <tex:cmd name="usepackage" nl2="1">
                <tex:parm>attachfile2</tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:if test="exsl:node-set($pageLayoutInfo)/@showLineNumbers='yes'">
            <tex:cmd name="usepackage" nl2="1">
                <tex:parm>lineno</tex:parm>
            </tex:cmd>
        </xsl:if>
        <!-- Doing this ourselves: using Needspace without the initial \par
            <tex:cmd name="usepackage" nl2="1">
            <tex:parm>needspace</tex:parm>
        </tex:cmd>-->
        <tex:cmd name="usepackage" nl2="1">
            <tex:parm>xltxtra</tex:parm>
        </tex:cmd>
        <tex:cmd name="usepackage" nl2="1">
            <tex:parm>setspace</tex:parm>
        </tex:cmd>
        <xsl:choose>
            <xsl:when test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespaceendnotes!='yes' and not(exsl:node-set($backMatterLayoutInfo)/useEndNotesLayout)">
                <tex:cmd name="usepackage" nl2="1">
                    <xsl:if test="exsl:node-set($pageLayoutInfo)/footnoteLine/@forcefootnotestobottomofpage='yes'">
                        <tex:opt>bottom</tex:opt>
                    </xsl:if>
                    <tex:parm>footmisc</tex:parm>
                </tex:cmd>
                <xsl:variable name="sFootnoteIndent" select="normalize-space(exsl:node-set($pageLayoutInfo)/footnoteIndent)"/>
                <xsl:if test="string-length($sFootnoteIndent)&gt;0">
                    <tex:cmd name="footnotemargin" gr="0"/>
                    <xsl:value-of select="$sFootnoteIndent"/>
                    <xsl:text>&#xa;</xsl:text>
                </xsl:if>
            </xsl:when>
            <xsl:when test="exsl:node-set($pageLayoutInfo)/footnoteLine/@forcefootnotestobottomofpage='yes'">
                <tex:cmd name="usepackage" nl2="1">
                    <tex:opt>bottom</tex:opt>
                    <tex:parm>footmisc</tex:parm>
                </tex:cmd>
                <xsl:variable name="sFootnoteIndent" select="normalize-space(exsl:node-set($pageLayoutInfo)/footnoteIndent)"/>
                <xsl:if test="string-length($sFootnoteIndent)&gt;0">
                    <tex:cmd name="footnotemargin" gr="0"/>
                    <xsl:value-of select="$sFootnoteIndent"/>
                    <xsl:text>&#xa;</xsl:text>
                </xsl:if>
            </xsl:when>
        </xsl:choose>
        <tex:cmd name="usepackage" nl2="1">
            <tex:opt>normalem</tex:opt>
            <tex:parm>ulem</tex:parm>
        </tex:cmd>
        <tex:cmd name="usepackage" nl2="1">
            <tex:parm>color</tex:parm>
        </tex:cmd>
        <tex:cmd name="usepackage" nl2="1">
            <tex:parm>colortbl</tex:parm>
        </tex:cmd>
        <tex:cmd name="usepackage" nl2="1">
            <tex:parm>tabularx</tex:parm>
        </tex:cmd>
        <tex:cmd name="usepackage" nl2="1">
            <tex:parm>longtable</tex:parm>
        </tex:cmd>
        <xsl:if test="exsl:node-set($publisherStyleSheet)/@XeLaTeXSpecial[contains(.,'longtable-patch')]">
            <!-- Following fixes a bug between longtable and fancyhdr.  It is from https://tex.stackexchange.com/questions/54671/longtable-changes-the-page-heading -->
            <xsl:if test="not($bIsBook)">
                <tex:cmd name="usepackage" nl2="1">
                    <tex:parm>etoolbox</tex:parm>
                </tex:cmd>
            </xsl:if>
            <tex:cmd name="makeatletter" gr="0" nl2="1"/>
            <tex:cmd name="patchcmd" nl2="1">
                <tex:parm>
                    <tex:cmd name="LT@output" gr="0"/>
                </tex:parm>
                <tex:parm>
                    <tex:cmd name="@colht" gr="0"/>
                    <xsl:text>&#x20;</xsl:text>
                    <tex:cmd name="vbox" gr="0"/>
                </tex:parm>
                <tex:parm>
                    <tex:cmd name="@colht" gr="0"/>
                </tex:parm>
                <tex:parm/>
                <tex:parm/>
            </tex:cmd>
            <tex:cmd name="makeatother" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:if test="//landscape or //*[@showinlandscapemode='yes']">
            <tex:cmd name="usepackage" nl2="1">
                <tex:parm>lscape</tex:parm>
            </tex:cmd>
        </xsl:if>
        <tex:cmd name="usepackage" nl2="1">
            <tex:parm>multirow</tex:parm>
        </tex:cmd>
        <tex:cmd name="usepackage" nl2="1">
            <tex:parm>booktabs</tex:parm>
        </tex:cmd>
        <tex:cmd name="usepackage" nl2="1">
            <tex:parm>calc</tex:parm>
        </tex:cmd>
        <tex:cmd name="usepackage" nl2="1">
            <tex:parm>fancyhdr</tex:parm>
        </tex:cmd>
        <tex:cmd name="usepackage" nl2="1">
            <tex:parm>fontspec</tex:parm>
        </tex:cmd>
        <tex:cmd name="usepackage" nl2="1">
            <tex:parm>hyperref</tex:parm>
        </tex:cmd>
        <xsl:if test="//language[@rtl='yes'] and exsl:node-set($lingPaper)/@automaticallywrapinterlinears='yes'">
            <tex:cmd name="TeXXeTstate=1" gr="0" nl2="1"/>
        </xsl:if>
        <tex:cmd name="hypersetup" nl2="1">
            <tex:parm>
                <xsl:text>colorlinks=true, citecolor=black, filecolor=black, linkcolor=black, urlcolor=blue, bookmarksopen=true, </xsl:text>
                <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespaceendnotes!='yes' and not(exsl:node-set($backMatterLayoutInfo)/useEndNotesLayout)">
                    <xsl:text>hyperfootnotes=false, </xsl:text>
                </xsl:if>
                <xsl:call-template name="SetMetadata"/>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SubtractOneInch
    -->
    <xsl:template name="SubtractOneInch">
        <xsl:param name="sValue"/>
        <xsl:param name="iValue"/>
        <xsl:variable name="sUnit">
            <xsl:call-template name="GetUnitOfMeasure">
                <xsl:with-param name="sValue" select="$sValue"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$sUnit='in'">
                <xsl:value-of select="number($iValue - 1)"/>
                <xsl:text>in</xsl:text>
            </xsl:when>
            <xsl:when test="$sUnit='mm'">
                <xsl:value-of select="number($iValue - 25.4)"/>
                <xsl:text>mm</xsl:text>
            </xsl:when>
            <xsl:when test="$sUnit='cm'">
                <xsl:value-of select="number($iValue - 2.54)"/>
                <xsl:text>cm</xsl:text>
            </xsl:when>
            <xsl:when test="$sUnit='pt'">
                <xsl:value-of select="number($iValue - 72.27)"/>
                <xsl:text>pt</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$iValue"/>
                <xsl:value-of select="$sUnit"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- 
====================================
What might go in a TeX package file
====================================
-->
    <!--  
        SetTOCMacros
    -->
    <xsl:template name="SetTOCMacros">
        <xsl:call-template name="SetXLingPaperTableOfContentsMacro"/>
        <xsl:call-template name="SetXLingPaperAddToContentsMacro"/>
        <xsl:call-template name="SetXLingPaperEndTableOfContentsMacro"/>
        <xsl:call-template name="SetXLingPaperDotFillMacro"/>
        <xsl:call-template name="SetXLingPaperDottedTOCLineMacro"/>
    </xsl:template>
    <!--  
        SetXLingPaperFreeMacro
    -->
    <xsl:template name="SetXLingPaperFreeMacro">
        <!--  
            #1 is the indent
            #2 is the content of the free
        -->
        <tex:cmd name="newcommand" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPaperfree" gr="0" nl2="0"/>
            </tex:parm>
            <tex:opt>2</tex:opt>
            <tex:parm>
                <tex:cmd name="vskip" gr="0" nl2="0"/>
                <xsl:text>0pt plus .2pt</xsl:text>
                <tex:group>
                    <tex:cmd name="leftskip" gr="0" nl1="1" nl2="0"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>1</xsl:text>
                    <tex:cmd name="relax" gr="0" nl2="0"/>
                    <tex:spec cat="comment"/>
                    <xsl:text> left glue for indent</xsl:text>
                    <tex:cmd name="parindent" gr="0" nl1="1" nl2="0"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>1</xsl:text>
                    <tex:cmd name="relax" gr="0" nl2="0"/>
                    <tex:cmd name="interlinepenalty10000" gr="0" nl1="1" nl2="0"/>
                    <tex:cmd name="leavevmode" gr="0" nl1="1" nl2="0"/>
                    <tex:spec cat="bg"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>2</xsl:text>
                    <tex:spec cat="eg"/>
                    <tex:cmd name="nobreak" gr="0" nl2="1"/>
                    <tex:cmd name="par" gr="0"/>
                </tex:group>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetXLingPaperExampleFreeIndent
    -->
    <xsl:template name="SetXLingPaperExampleFreeIndent">
        <tex:cmd name="newlength" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPaperexamplefreeindent" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'setlength'"/>
            <xsl:with-param name="sCommandToSet" select="'XLingPaperexamplefreeindent'"/>
            <xsl:with-param name="sValue">
                <xsl:text>-.3 em</xsl:text>
                <!-- 2010.03.31  I think all this was a work-around for a bug I had where I used  $sBlockQuoteIndent instead of  $sExampleIndentBefore in examples.
    <xsl:text>-.3 em+</xsl:text>
                <xsl:variable name="iBlockQuoteIndent" select="substring($sBlockQuoteIndent,1,string-length($sBlockQuoteIndent)-2)"/>
                <xsl:variable name="iExampleIndentBefore" select="substring($sExampleIndentBefore,1,string-length($sExampleIndentBefore)-2)"/>
                <xsl:choose>
                    <xsl:when test="number($iBlockQuoteIndent) &gt; number($iExampleIndentBefore)">
                        <xsl:value-of select="$sBlockQuoteIndent"/>
                        <xsl:text>-</xsl:text>
                        <xsl:value-of select="$sExampleIndentBefore"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$sExampleIndentBefore"/>
                        <xsl:text>-</xsl:text>
                        <xsl:value-of select="$sBlockQuoteIndent"/>
                    </xsl:otherwise>
                </xsl:choose>
-->
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--  
        SetXLingPaperExampleMacro
    -->
    <xsl:template name="SetXLingPaperExampleMacro">
        <!-- based on the borrowed set toc macro from LaTeX's latex.ltx file 
            #1 is the left indent
            #2 is the right indent
            #3 is the width of the example number
            #4 is the example number
            #5 is the content of the list item
        -->
        <tex:cmd name="newcommand" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPaperexample" gr="0" nl2="0"/>
            </tex:parm>
            <tex:opt>5</tex:opt>
            <tex:parm>
                <tex:cmd name="newdimen" gr="0" nl1="1" nl2="0"/>
                <tex:cmd name="XLingPapertempdim" gr="0" nl2="1"/>
                <tex:cmd name="vskip" gr="0" nl2="0"/>
                <xsl:text>0pt plus .2pt</xsl:text>
                <tex:group>
                    <tex:cmd name="leftskip" gr="0" nl1="1" nl2="0"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>1</xsl:text>
                    <tex:cmd name="relax" gr="0" nl2="0"/>
                    <tex:spec cat="comment"/>
                    <xsl:text> left glue for indent</xsl:text>
                    <tex:cmd name="hspace*" nl1="1" nl2="0">
                        <tex:parm>
                            <tex:spec cat="parm"/>
                            <xsl:text>1</xsl:text>
                        </tex:parm>
                    </tex:cmd>
                    <tex:cmd name="relax" gr="0" nl2="0"/>
                    <tex:cmd name="rightskip" gr="0" nl1="1" nl2="0"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>2</xsl:text>
                    <tex:cmd name="relax" gr="0" nl2="0"/>
                    <tex:spec cat="comment"/>
                    <xsl:text> right glue for indent</xsl:text>
                    <tex:cmd name="interlinepenalty10000" gr="0" nl1="1" nl2="0"/>
                    <tex:cmd name="leavevmode" gr="0" nl1="1" nl2="0"/>
                    <tex:cmd name="XLingPapertempdim" gr="0" nl1="1" nl2="0"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>3</xsl:text>
                    <tex:cmd name="relax" gr="0" nl2="0"/>
                    <tex:spec cat="comment"/>
                    <xsl:text> example number width</xsl:text>
                    <tex:cmd name="advance" gr="0" nl1="1" nl2="0"/>
                    <tex:cmd name="leftskip" gr="0" nl2="0"/>
                    <tex:cmd name="XLingPapertempdim" gr="0" nl2="0"/>
                    <tex:cmd name="null" gr="0" nl2="0"/>
                    <tex:cmd name="nobreak" gr="0" nl2="0"/>
                    <tex:cmd name="hskip" gr="0" nl2="0"/>
                    <xsl:text>-</xsl:text>
                    <tex:cmd name="leftskip" gr="0" nl2="0"/>
                    <tex:cmd name="hbox to" gr="0" nl2="0"/>
                    <tex:cmd name="XLingPapertempdim" gr="0" nl2="0">
                        <tex:parm>
                            <tex:cmd name="normalfont" gr="0" nl2="0"/>
                            <tex:cmd name="normalcolor" gr="0" nl2="0"/>
                            <tex:spec cat="parm"/>
                            <xsl:text>4</xsl:text>
                            <tex:cmd name="hfil" gr="0" nl2="0"/>
                        </tex:parm>
                    </tex:cmd>
                    <tex:spec cat="bg"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>5</xsl:text>
                    <tex:spec cat="eg"/>
                    <tex:cmd name="nobreak" gr="0" nl2="1"/>
                    <tex:cmd name="par" gr="0"/>
                </tex:group>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!-- 
        \newcommand{\XLingPaperexampleintable}[5]{
        \newdimen\XLingPapertempdim
        %%%\vskip0pt plus .2pt{
        \leftskip#1\relax% left glue for indent
        \hspace*{#1}\relax
        \rightskip#2\relax% right glue for indent
        \interlinepenalty10000
        \leavevmode
        \XLingPapertempdim#3\relax% example number width
        %%%\advance\leftskip\XLingPapertempdim\null\nobreak\hskip-\leftskip
        \hbox to\XLingPapertempdim{\normalfont\normalcolor#4\hfil}{#5}\nobreak
        %%%\par}
        }
    -->
    <!--  
        SetXLingPaperExampleInTableMacro
    -->
    <xsl:template name="SetXLingPaperExampleInTableMacro">
        <!-- based on the borrowed set toc macro from LaTeX's latex.ltx file 
            #1 is the left indent
            #2 is the right indent
            #3 is the width of the example number
            #4 is the example number
            #5 is the content of the list item
        -->
        <tex:cmd name="newcommand" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPaperexampleintable" gr="0" nl2="0"/>
            </tex:parm>
            <tex:opt>5</tex:opt>
            <tex:parm>
                <tex:cmd name="newdimen" gr="0" nl1="1" nl2="0"/>
                <tex:cmd name="XLingPapertempdim" gr="0" nl2="0"/>
                <tex:cmd name="leftskip" gr="0" nl1="1" nl2="0"/>
                <tex:spec cat="parm"/>
                <xsl:text>1</xsl:text>
                <tex:cmd name="relax" gr="0" nl2="0"/>
                <tex:spec cat="comment"/>
                <xsl:text> left glue for indent</xsl:text>
                <tex:cmd name="hspace*" nl1="1" nl2="0">
                    <tex:parm>
                        <tex:spec cat="parm"/>
                        <xsl:text>1</xsl:text>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="relax" gr="0" nl2="0"/>
                <tex:cmd name="rightskip" gr="0" nl1="1" nl2="0"/>
                <tex:spec cat="parm"/>
                <xsl:text>2</xsl:text>
                <tex:cmd name="relax" gr="0" nl2="0"/>
                <tex:spec cat="comment"/>
                <xsl:text> right glue for indent</xsl:text>
                <tex:cmd name="interlinepenalty10000" gr="0" nl1="1" nl2="0"/>
                <tex:cmd name="leavevmode" gr="0" nl1="1" nl2="0"/>
                <tex:cmd name="XLingPapertempdim" gr="0" nl1="1" nl2="0"/>
                <tex:spec cat="parm"/>
                <xsl:text>3</xsl:text>
                <tex:cmd name="relax" gr="0" nl2="0"/>
                <tex:spec cat="comment"/>
                <xsl:text> example number width</xsl:text>
                <tex:cmd name="hbox to" gr="0" nl1="1"/>
                <tex:cmd name="XLingPapertempdim" gr="0" nl2="0">
                    <tex:parm>
                        <tex:cmd name="normalfont" gr="0" nl2="0"/>
                        <tex:cmd name="normalcolor" gr="0" nl2="0"/>
                        <tex:spec cat="parm"/>
                        <xsl:text>4</xsl:text>
                        <tex:cmd name="hfil" gr="0" nl2="0"/>
                    </tex:parm>
                </tex:cmd>
                <tex:spec cat="bg"/>
                <tex:env name="tabular">
                    <tex:opt>t</tex:opt>
                    <tex:parm>
                        <xsl:text>@</xsl:text>
                        <tex:spec cat="bg"/>
                        <tex:spec cat="eg"/>
                        <xsl:text>l@</xsl:text>
                        <tex:spec cat="bg"/>
                        <tex:spec cat="eg"/>
                    </tex:parm>
                    <tex:spec cat="parm"/>
                    <xsl:text>5</xsl:text>
                </tex:env>
                <tex:spec cat="eg"/>
                <tex:cmd name="nobreak" gr="0" nl2="1"/>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetXLingPaperIndexMacro
    -->
    <xsl:template name="SetXLingPaperIndexMacro">
        <tex:cmd name="newcommand" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPaperindex" gr="0" nl2="0"/>
            </tex:parm>
            <tex:parm>
                <tex:cmd name="immediate" gr="0" nl2="0"/>
                <tex:cmd name="openout7" gr="0" nl2="0"/>
                <xsl:text> = </xsl:text>
                <tex:cmd name="jobname.idx" gr="0" nl2="0"/>
                <tex:cmd name="relax" gr="0" nl2="1"/>
                <tex:cmd name="immediate" gr="0" nl2="0"/>
                <tex:cmd name="write7">
                    <tex:parm>
                        <tex:spec cat="lt"/>
                        <xsl:text>idx</xsl:text>
                        <tex:spec cat="gt"/>
                    </tex:parm>
                </tex:cmd>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetXLingPaperIndexItemMacro
    -->
    <xsl:template name="SetXLingPaperIndexItemMacro">
        <!-- based on the borrowed set toc macro from LaTeX's latex.ltx file 
            #1 is the indent
            #4 is the content of the index item
        -->
        <tex:cmd name="newcommand" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPaperindexitem" gr="0" nl2="0"/>
            </tex:parm>
            <tex:opt>2</tex:opt>
            <tex:parm>
                <tex:cmd name="vskip" gr="0" nl2="0"/>
                <xsl:text>0pt plus .2pt</xsl:text>
                <tex:group>
                    <tex:cmd name="leftskip" gr="0" nl1="1" nl2="0"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>1</xsl:text>
                    <tex:cmd name="relax" gr="0" nl2="0"/>
                    <tex:spec cat="comment"/>
                    <xsl:text> left glue for indent</xsl:text>
                    <tex:cmd name="parindent" gr="0" nl1="1" nl2="0"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>1</xsl:text>
                    <tex:cmd name="relax" gr="0" nl2="0"/>
                    <tex:cmd name="interlinepenalty10000" gr="0" nl1="1" nl2="0"/>
                    <tex:cmd name="leavevmode" gr="0" nl1="1" nl2="0"/>
                    <tex:cmd name="advance" gr="0" nl1="1" nl2="0"/>
                    <tex:cmd name="leftskip" gr="0" nl2="0"/>
                    <xsl:text>.25in</xsl:text>
                    <tex:cmd name="null" gr="0" nl2="0"/>
                    <tex:cmd name="nobreak" gr="0" nl2="0"/>
                    <tex:cmd name="hskip" gr="0" nl2="0"/>
                    <xsl:text>-</xsl:text>
                    <tex:cmd name="leftskip" gr="0" nl2="0"/>
                    <tex:spec cat="bg"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>2</xsl:text>
                    <tex:spec cat="eg"/>
                    <tex:cmd name="nobreak" gr="0" nl2="1"/>
                    <tex:cmd name="par" gr="0"/>
                </tex:group>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetXLingPaperListItemMacro
    -->
    <xsl:template name="SetXLingPaperListItemMacro">
        <!-- based on the borrowed set toc macro from LaTeX's latex.ltx file 
            #1 is the indent
            #2 is the width of the label
            #3 is the label
            #4 is the content of the list item
        -->
        <tex:cmd name="newcommand" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPaperlistitem" gr="0" nl2="0"/>
            </tex:parm>
            <tex:opt>4</tex:opt>
            <tex:parm>
                <tex:cmd name="newdimen" gr="0" nl1="1" nl2="0"/>
                <tex:cmd name="XLingPapertempdim" gr="0" nl2="1"/>
                <tex:cmd name="vskip" gr="0" nl2="0"/>
                <xsl:text>0pt plus .2pt</xsl:text>
                <tex:group>
                    <tex:cmd name="leftskip" gr="0" nl1="1" nl2="0"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>1</xsl:text>
                    <tex:cmd name="relax" gr="0" nl2="0"/>
                    <tex:spec cat="comment"/>
                    <xsl:text> left glue for indent</xsl:text>
                    <tex:cmd name="parindent" gr="0" nl1="1" nl2="0"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>1</xsl:text>
                    <tex:cmd name="relax" gr="0" nl2="0"/>
                    <tex:cmd name="interlinepenalty10000" gr="0" nl1="1" nl2="0"/>
                    <tex:cmd name="leavevmode" gr="0" nl1="1" nl2="0"/>
                    <tex:cmd name="XLingPapertempdim" gr="0" nl1="1" nl2="0"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>2</xsl:text>
                    <tex:cmd name="relax" gr="0" nl2="0"/>
                    <tex:spec cat="comment"/>
                    <xsl:text> label width</xsl:text>
                    <tex:cmd name="advance" gr="0" nl1="1" nl2="0"/>
                    <tex:cmd name="leftskip" gr="0" nl2="0"/>
                    <tex:cmd name="XLingPapertempdim" gr="0" nl2="0"/>
                    <tex:cmd name="null" gr="0" nl2="0"/>
                    <tex:cmd name="nobreak" gr="0" nl2="0"/>
                    <tex:cmd name="hskip" gr="0" nl2="0"/>
                    <xsl:text>-</xsl:text>
                    <tex:cmd name="leftskip" gr="0" nl2="0"/>
                    <tex:cmd name="hbox to" gr="0" nl2="0"/>
                    <tex:cmd name="XLingPapertempdim" gr="0" nl2="0">
                        <tex:parm>
                            <tex:cmd name="hfil" gr="0" nl2="0"/>
                            <tex:cmd name="normalfont" gr="0" nl2="0"/>
                            <tex:cmd name="normalcolor" gr="0" nl2="0"/>
                            <tex:spec cat="parm"/>
                            <xsl:text>3</xsl:text>
                            <tex:spec cat="esc"/>
                            <xsl:text>&#x20;</xsl:text>
                        </tex:parm>
                    </tex:cmd>
                    <tex:spec cat="bg"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>4</xsl:text>
                    <tex:spec cat="eg"/>
                    <tex:cmd name="nobreak" gr="0" nl2="1"/>
                    <tex:cmd name="par" gr="0"/>
                </tex:group>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetXLingPaperListInterlinearMacro
    -->
    <xsl:template name="SetXLingPaperListInterlinearMacro">
        <!-- based on the borrowed set toc macro from LaTeX's latex.ltx file 
            #1 is the indent
            #2 is the width of the example number
            #3 is the width of the letter
            #4 is the letter
            #5 is the content 
        -->
        <tex:cmd name="newcommand" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPaperlistinterlinear" gr="0" nl2="0"/>
            </tex:parm>
            <tex:opt>5</tex:opt>
            <tex:parm>
                <!--                <tex:cmd name="newdimen" gr="0" nl1="1" nl2="0"/>
                <tex:cmd name="XLingPapertempdimletter" gr="0" nl2="1"/>
-->
                <tex:cmd name="vskip" gr="0" nl2="0"/>
                <xsl:text>0pt plus .2pt</xsl:text>
                <tex:group>
                    <tex:cmd name="hspace*">
                        <tex:parm>
                            <tex:spec cat="parm"/>
                            <xsl:text>1</xsl:text>
                        </tex:parm>
                    </tex:cmd>
                    <tex:cmd name="hspace*">
                        <tex:parm>
                            <tex:spec cat="parm"/>
                            <xsl:text>2</xsl:text>
                        </tex:parm>
                    </tex:cmd>
                    <tex:cmd name="XLingPapertempdimletter" gr="0" nl1="1" nl2="0"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>3</xsl:text>
                    <tex:cmd name="relax" gr="0" nl2="0"/>
                    <tex:spec cat="comment"/>
                    <xsl:text> letter width</xsl:text>
                    <tex:cmd name="advance" gr="0" nl1="1" nl2="0"/>
                    <tex:cmd name="leftskip" gr="0" nl2="0"/>
                    <tex:cmd name="XLingPapertempdimletter" gr="0" nl2="0"/>
                    <tex:cmd name="null" gr="0" nl2="0"/>
                    <tex:cmd name="nobreak" gr="0" nl2="0"/>
                    <tex:cmd name="hskip" gr="0" nl2="0"/>
                    <xsl:text>-</xsl:text>
                    <tex:cmd name="leftskip" gr="0" nl2="0"/>
                    <tex:cmd name="hspace*" nl2="0">
                        <tex:parm>-.3em</tex:parm>
                    </tex:cmd>
                    <tex:cmd name="hbox to" gr="0" nl2="0"/>
                    <tex:cmd name="XLingPapertempdimletter" gr="0" nl2="0">
                        <tex:parm>
                            <tex:cmd name="normalfont" gr="0" nl2="0"/>
                            <tex:cmd name="normalcolor" gr="0" nl2="0"/>
                            <tex:spec cat="parm"/>
                            <xsl:text>4</xsl:text>
                            <tex:spec cat="esc"/>
                            <xsl:text>&#x20;</xsl:text>
                            <tex:cmd name="hfil" gr="0" nl2="0"/>
                        </tex:parm>
                    </tex:cmd>
                    <tex:spec cat="bg"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>5</xsl:text>
                    <tex:spec cat="eg"/>
                    <tex:cmd name="nobreak" gr="0" nl2="1"/>
                    <tex:cmd name="par" gr="0"/>
                </tex:group>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetXLingPaperListInterlinearInTableMacro
    -->
    <xsl:template name="SetXLingPaperListInterlinearInTableMacro">
        <!-- based on the borrowed set toc macro from LaTeX's latex.ltx file 
            #1 is the indent
            #2 is the width of the example number
            #3 is the width of the letter
            #4 is the letter
            #5 is the content 
        -->
        <tex:cmd name="newcommand" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPaperlistinterlinearintable" gr="0" nl2="0"/>
            </tex:parm>
            <tex:opt>5</tex:opt>
            <tex:parm>
                <!--     following is too much
    <tex:cmd name="hspace*">
                    <tex:parm>
                        <tex:spec cat="parm"/>
                        <xsl:text>1</xsl:text>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="hspace*">
                    <tex:parm>
                        <tex:spec cat="parm"/>
                        <xsl:text>2</xsl:text>
                    </tex:parm>
                </tex:cmd>
-->
                <tex:cmd name="XLingPapertempdimletter" gr="0" nl1="1" nl2="0"/>
                <tex:spec cat="parm"/>
                <xsl:text>3</xsl:text>
                <tex:cmd name="relax" gr="0" nl2="0"/>
                <tex:spec cat="comment"/>
                <xsl:text> letter width</xsl:text>
                <tex:cmd name="hspace*" nl1="1">
                    <tex:parm>-.3em</tex:parm>
                </tex:cmd>
                <tex:cmd name="hbox to" gr="0" nl2="0"/>
                <tex:cmd name="XLingPapertempdimletter" gr="0" nl2="0">
                    <tex:parm>
                        <tex:cmd name="normalfont" gr="0" nl2="0"/>
                        <tex:cmd name="normalcolor" gr="0" nl2="0"/>
                        <tex:spec cat="parm"/>
                        <xsl:text>4</xsl:text>
                        <tex:spec cat="esc"/>
                        <xsl:text>&#x20;</xsl:text>
                        <tex:cmd name="hfil" gr="0" nl2="0"/>
                    </tex:parm>
                </tex:cmd>
                <tex:spec cat="bg"/>
                <tex:env name="tabular">
                    <tex:opt>t</tex:opt>
                    <tex:parm>
                        <xsl:text>@</xsl:text>
                        <tex:spec cat="bg"/>
                        <tex:spec cat="eg"/>
                        <xsl:text>l@</xsl:text>
                        <tex:spec cat="bg"/>
                        <tex:spec cat="eg"/>
                    </tex:parm>
                    <tex:spec cat="parm"/>
                    <xsl:text>5</xsl:text>
                </tex:env>
                <tex:spec cat="eg"/>
                <tex:cmd name="nobreak" gr="0" nl2="1"/>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetXLingPaperDottedTOCLineMacro
    -->
    <xsl:template name="SetXLingPaperDottedTOCLineMacro">
        <!-- borrowed with slight changes (and gratitude) from LaTeX's latex.ltx file -->
        <tex:cmd name="newcommand" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPaperdottedtocline" gr="0" nl2="0"/>
            </tex:parm>
            <tex:opt>4</tex:opt>
            <tex:parm>
                <xsl:if test="contains($sXeLaTeXVersion,'2020')">
                    <!-- following vspace* command needed for TeX Live 2020 hyperlink command; not sure why  -->
                    <tex:cmd name="vspace*">
                        <tex:parm>
                            <xsl:text>-</xsl:text>
                            <tex:cmd name="baselineskip" gr="0" nl1="1" nl2="0"/>
                        </tex:parm>
                    </tex:cmd>
                </xsl:if>
                <tex:cmd name="newdimen" gr="0" nl1="1" nl2="0"/>
                <tex:cmd name="XLingPapertempdim" gr="0" nl2="1"/>
                <tex:cmd name="vskip" gr="0" nl2="0"/>
                <xsl:text>0pt plus .2pt</xsl:text>
                <tex:group>
                    <tex:cmd name="leftskip" gr="0" nl1="1" nl2="0"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>1</xsl:text>
                    <tex:cmd name="relax" gr="0" nl2="0"/>
                    <tex:spec cat="comment"/>
                    <xsl:text> left glue for indent</xsl:text>
                    <tex:cmd name="rightskip" gr="0" nl1="1" nl2="0"/>
                    <tex:cmd name="XLingPapertocrmarg" gr="0" nl2="0"/>
                    <tex:spec cat="comment"/>
                    <xsl:text> right glue for for right margin</xsl:text>
                    <tex:cmd name="parfillskip" gr="0" nl1="1" nl2="0"/>
                    <xsl:text>-</xsl:text>
                    <tex:cmd name="rightskip" gr="0" nl2="0"/>
                    <tex:spec cat="comment"/>
                    <xsl:text> so can go into margin if need be???</xsl:text>
                    <tex:cmd name="parindent" gr="0" nl1="1" nl2="0"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>1</xsl:text>
                    <tex:cmd name="relax" gr="0" nl2="0"/>
                    <tex:cmd name="interlinepenalty10000" gr="0" nl1="1" nl2="0"/>
                    <tex:cmd name="leavevmode" gr="0" nl1="1" nl2="0"/>
                    <tex:cmd name="XLingPapertempdim" gr="0" nl1="1" nl2="0"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>2</xsl:text>
                    <tex:cmd name="relax" gr="0" nl2="0"/>
                    <tex:spec cat="comment"/>
                    <xsl:text> numwidth</xsl:text>
                    <tex:cmd name="advance" gr="0" nl1="1" nl2="0"/>
                    <tex:cmd name="leftskip" gr="0" nl2="0"/>
                    <tex:cmd name="XLingPapertempdim" gr="0" nl2="0"/>
                    <tex:cmd name="null" gr="0" nl2="0"/>
                    <tex:cmd name="nobreak" gr="0" nl2="0"/>
                    <tex:cmd name="hskip" gr="0" nl2="0"/>
                    <xsl:text>-</xsl:text>
                    <tex:cmd name="leftskip" gr="0" nl2="0"/>
                    <tex:spec cat="bg"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>3</xsl:text>
                    <tex:spec cat="eg"/>
                    <tex:cmd name="nobreak" gr="0" nl2="1"/>
                    <tex:cmd name="XLingPaperdotfill" gr="0" nl2="0"/>
                    <tex:cmd name="nobreak" gr="0" nl2="1"/>
                    <tex:cmd name="hbox to" gr="0" nl2="0"/>
                    <tex:cmd name="XLingPaperpnumwidth" gr="0" nl2="0">
                        <tex:parm>
                            <tex:cmd name="hfil" gr="0" nl2="0"/>
                            <tex:cmd name="normalfont" gr="0" nl2="0"/>
                            <tex:cmd name="normalcolor" gr="0" nl2="0"/>
                            <tex:spec cat="parm"/>
                            <xsl:text>4</xsl:text>
                        </tex:parm>
                    </tex:cmd>
                    <tex:cmd name="par" gr="0" nl1="1"/>
                </tex:group>
            </tex:parm>
        </tex:cmd>
        <xsl:if test="//chapterInCollection or $parts and //contentsLayout[@partCentered='no' and @partShowPageNumber!='yes']">
            <tex:cmd name="newcommand" nl2="1">
                <tex:parm>
                    <tex:cmd name="XLingPaperplaintocline" gr="0" nl2="0"/>
                </tex:parm>
                <tex:opt>3</tex:opt>
                <tex:parm>
                    <tex:cmd name="newdimen" gr="0" nl1="1" nl2="0"/>
                    <tex:cmd name="XLingPapertempdim" gr="0" nl2="1"/>
                    <tex:cmd name="vskip" gr="0" nl2="0"/>
                    <xsl:text>0pt plus .2pt</xsl:text>
                    <tex:group>
                        <tex:cmd name="leftskip" gr="0" nl1="1" nl2="0"/>
                        <tex:spec cat="parm"/>
                        <xsl:text>1</xsl:text>
                        <tex:cmd name="relax" gr="0" nl2="0"/>
                        <tex:spec cat="comment"/>
                        <xsl:text> left glue for indent</xsl:text>
                        <tex:cmd name="rightskip" gr="0" nl1="1" nl2="0"/>
                        <tex:cmd name="XLingPapertocrmarg" gr="0" nl2="0"/>
                        <tex:spec cat="comment"/>
                        <xsl:text> right glue for for right margin</xsl:text>
                        <tex:cmd name="parfillskip" gr="0" nl1="1" nl2="0"/>
                        <xsl:text>-</xsl:text>
                        <tex:cmd name="rightskip" gr="0" nl2="0"/>
                        <tex:spec cat="comment"/>
                        <xsl:text> so can go into margin if need be???</xsl:text>
                        <tex:cmd name="parindent" gr="0" nl1="1" nl2="0"/>
                        <tex:spec cat="parm"/>
                        <xsl:text>1</xsl:text>
                        <tex:cmd name="relax" gr="0" nl2="0"/>
                        <tex:cmd name="interlinepenalty10000" gr="0" nl1="1" nl2="0"/>
                        <tex:cmd name="leavevmode" gr="0" nl1="1" nl2="0"/>
                        <tex:cmd name="XLingPapertempdim" gr="0" nl1="1" nl2="0"/>
                        <tex:spec cat="parm"/>
                        <xsl:text>2</xsl:text>
                        <tex:cmd name="relax" gr="0" nl2="0"/>
                        <tex:spec cat="comment"/>
                        <xsl:text> numwidth</xsl:text>
                        <tex:cmd name="advance" gr="0" nl1="1" nl2="0"/>
                        <tex:cmd name="leftskip" gr="0" nl2="0"/>
                        <tex:cmd name="XLingPapertempdim" gr="0" nl2="0"/>
                        <tex:cmd name="null" gr="0" nl2="0"/>
                        <tex:cmd name="nobreak" gr="0" nl2="0"/>
                        <tex:cmd name="hskip" gr="0" nl2="0"/>
                        <xsl:text>-</xsl:text>
                        <tex:cmd name="leftskip" gr="0" nl2="0"/>
                        <tex:spec cat="bg"/>
                        <tex:spec cat="parm"/>
                        <xsl:text>3</xsl:text>
                        <tex:spec cat="eg"/>
                        <tex:cmd name="nobreak" gr="0" nl2="1"/>
                        <tex:cmd name="hfill" gr="0" nl2="0"/>
                        <tex:cmd name="nobreak" gr="0" nl2="1"/>
                        <tex:cmd name="hbox to" gr="0" nl2="0"/>
                        <tex:cmd name="XLingPaperpnumwidth" gr="0" nl2="0">
                            <tex:parm>
                                <tex:cmd name="hfil" gr="0" nl2="0"/>
                                <tex:cmd name="normalfont" gr="0" nl2="0"/>
                                <tex:cmd name="normalcolor" gr="0" nl2="0"/>
                            </tex:parm>
                        </tex:cmd>
                        <tex:cmd name="par" gr="0" nl1="1"/>
                    </tex:group>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
    </xsl:template>
    <!--  
        SetXLingPaperAdjustHeaderInListInterlinearWithISOCodes
    -->
    <xsl:template name="SetXLingPaperAdjustHeaderInListInterlinearWithISOCodes">
        <xsl:if test="exsl:node-set($lingPaper)/@showiso639-3codeininterlinear='yes' or //example/@showiso639-3codes='yes'">
            <xsl:if
                test="//example/exampleHeading[following-sibling::listInterlinear or following-sibling::interlinear] or //example/child::*[1][name()='interlinear' and child::*[1][name()='exampleHeading']]">
                <tex:cmd name="newdimen" gr="0"/>
                <tex:cmd name="XLingPaperexamplenumberheight" gr="0" nl2="1"/>
                <tex:cmd name="newdimen" gr="0"/>
                <tex:cmd name="XLingPaperexampleheadingheight" gr="0" nl2="1"/>
                <tex:cmd name="newlength" nl1="1" nl2="1">
                    <tex:parm>
                        <tex:cmd name="XLingPaperAdjust" gr="0"/>
                    </tex:parm>
                </tex:cmd>
                <!--  
                #1 is the height of the example heading
                #2 is the height of the example number/ISO code complex
            -->
                <tex:cmd name="newcommand" nl2="1">
                    <tex:parm>
                        <tex:cmd name="XLingPaperAdjustHeaderInListInterlinearWithISOCodes" gr="0" nl2="0"/>
                    </tex:parm>
                    <tex:opt>2</tex:opt>
                    <tex:parm>
                        <!-- \newcommand{\XLingPaperAdjustHeaderInListInterlinearWithISOCodes}[2]{
                    \ifnum#1<#2
                    \newlength{\XLingPaperAdjust}
                    \XLingPaperAdjust=\XlingPaperexampleheadingheight
                    \advance\XLingPaperAdjust by-\XlingPaperexamplenumberheight
                    \advance\XLingPaperAdjust by-.3\baselineskip
                    \vspace*{\XLingPaperAdjust}
                    \fi
                    }
-->
                        <tex:cmd name="ifnum" gr="0" nl1="1" sp="1"/>
                        <tex:spec cat="parm"/>
                        <xsl:text>1</xsl:text>
                        <tex:spec cat="lt"/>
                        <tex:spec cat="parm"/>
                        <xsl:text>2</xsl:text>
                        <tex:spec cat="esc"/>
                        <xsl:text>XLingPaperAdjust=</xsl:text>
                        <tex:spec cat="parm"/>
                        <xsl:text>1</xsl:text>
                        <tex:cmd name="advance" gr="0" nl1="1"/>
                        <tex:spec cat="esc"/>
                        <xsl:text>XLingPaperAdjust by -</xsl:text>
                        <tex:spec cat="parm"/>
                        <xsl:text>2</xsl:text>
                        <!--                    <tex:cmd name="advance" gr="0" nl1="1"/>
                    <tex:spec cat="esc"/>
                    <xsl:text>XLingPaperAdjust by -.2</xsl:text>
                    <tex:cmd name="baselineskip" gr="0"/>
                    <tex:spec cat="comment"/>
                    <xsl:text> wish I knew why this was needed, but it seems to be... maybe 5pt will also work</xsl:text>
-->
                        <tex:cmd name="vspace*" nl1="1">
                            <tex:parm>
                                <tex:cmd name="XLingPaperAdjust" gr="0"/>
                            </tex:parm>
                        </tex:cmd>
                        <tex:cmd name="fi" gr="0" nl1="1"/>
                    </tex:parm>
                </tex:cmd>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        SetXLingPaperAlignedWordSpacing
    -->
    <xsl:template name="SetXLingPaperAlignedWordSpacing">
        <tex:cmd name="newskip" gr="0"/>
        <tex:cmd name="XLingPaperinterwordskip" gr="0"/>
        <xsl:call-template name="SetDefaultXLingPaperInterWordSkip"/>
        <tex:cmd name="def" gr="0" nl1="1"/>
        <tex:cmd name="XLingPaperintspace" nl2="1">
            <tex:parm>
                <tex:cmd name="hskip" gr="0"/>
                <tex:cmd name="XLingPaperinterwordskip" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <!-- Also do special ragged right with pretolerance to avoid long lines -->
        <tex:cmd name="def" gr="0"/>
        <tex:cmd name="XLingPaperraggedright">
            <tex:parm>
                <!-- See TeX book, page101 -->
                <tex:cmd name="rightskip" gr="0"/>
                <xsl:text>=0pt plus1fil</xsl:text>
                <!-- See TeX book, page 96 -->
                <tex:cmd name="pretolerance" gr="0"/>
                <xsl:text>=10000</xsl:text>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetXLingPaperBlockQuoteMacro
    -->
    <xsl:template name="SetXLingPaperBlockQuoteMacro">
        <!-- based on the borrowed set toc macro from LaTeX's latex.ltx file 
            #1 is the blockquote left indent
            #2 is the blockquote right indent
            #3 is the content of the block quote
        -->
        <xsl:if test="//blockquote">
            <xsl:if test="//blockquote[parent::li]">
                <tex:cmd name="newlength">
                    <tex:parm>
                        <tex:cmd name="XLingPaperbqtemp" gr="0"/>
                    </tex:parm>
                </tex:cmd>
            </xsl:if>
            <tex:cmd name="newcommand" nl2="1">
                <tex:parm>
                    <tex:cmd name="XLingPaperblockquote" gr="0" nl2="0"/>
                </tex:parm>
                <tex:opt>5</tex:opt>
                <tex:parm>
                    <tex:cmd name="vskip" gr="0" nl2="0"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>4</xsl:text>
                    <tex:group>
                        <tex:cmd name="leftskip" gr="0" nl1="1" nl2="0"/>
                        <tex:spec cat="parm"/>
                        <xsl:text>1</xsl:text>
                        <tex:cmd name="relax" gr="0" nl2="0"/>
                        <tex:spec cat="comment"/>
                        <xsl:text> left glue for indent</xsl:text>
                        <tex:cmd name="relax" gr="0" nl2="0"/>
                        <tex:cmd name="rightskip" gr="0" nl1="1" nl2="0"/>
                        <tex:spec cat="parm"/>
                        <xsl:text>2</xsl:text>
                        <tex:cmd name="relax" gr="0" nl2="0"/>
                        <tex:spec cat="comment"/>
                        <xsl:text> right glue for indent</xsl:text>
                        <tex:cmd name="interlinepenalty10000" gr="0" nl1="1" nl2="0"/>
                        <tex:cmd name="leavevmode" gr="0" nl1="1" nl2="0"/>
                        <tex:cmd name="hskip" gr="0" nl2="0"/>
                        <xsl:text>-</xsl:text>
                        <tex:cmd name="parindent" gr="0" nl2="0"/>
                        <tex:spec cat="bg"/>
                        <tex:spec cat="parm"/>
                        <xsl:text>3</xsl:text>
                        <tex:spec cat="eg"/>
                        <tex:cmd name="nobreak" gr="0" nl2="1"/>
                    </tex:group>
                    <tex:cmd name="vskip" gr="0" nl2="0"/>
                    <tex:spec cat="parm"/>
                    <xsl:text>5</xsl:text>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
    </xsl:template>
    <!--  
        SetXLingPaperDotFillMacro
    -->
    <xsl:template name="SetXLingPaperDotFillMacro">
        <tex:cmd name="newcommand" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPaperdotfill" gr="0" nl2="0"/>
            </tex:parm>
            <xsl:choose>
                <xsl:when test="exsl:node-set($frontMatterLayoutInfo)/contentsLayout/@betweentitleandnumber='space'">
                    <tex:parm>
                        <tex:cmd name="hfill" gr="0" nl2="0"/>
                    </tex:parm>
                </xsl:when>
                <xsl:when test="exsl:node-set($frontMatterLayoutInfo)/contentsLayout/@betweentitleandnumber='rule'">
                    <tex:parm>
                        <xsl:text> </xsl:text>
                        <tex:cmd name="leaders" gr="0" nl2="0"/>
                        <tex:cmd name="hbox">
                            <tex:parm>
                                <xsl:text>_</xsl:text>
                            </tex:parm>
                        </tex:cmd>
                        <tex:cmd name="hfill" gr="0" nl2="0"/>
                    </tex:parm>
                </xsl:when>
                <xsl:otherwise>
                    <tex:parm>
                        <tex:cmd name="leaders" gr="0" nl2="0"/>
                        <tex:cmd name="hbox">
                            <tex:parm>
                                <tex:spec cat="mshift"/>
                                <tex:cmd name="mathsurround" gr="0" nl2="0"/>
                                <xsl:text> 0pt</xsl:text>
                                <tex:cmd name="mkern" gr="0" nl2="0"/>
                                <xsl:text> 4.5 mu</xsl:text>
                                <tex:cmd name="hbox">
                                    <tex:parm>.</tex:parm>
                                </tex:cmd>
                                <tex:cmd name="mkern" gr="0" nl2="0"/>
                                <xsl:text> 4.5 mu</xsl:text>
                                <tex:spec cat="mshift"/>
                            </tex:parm>
                        </tex:cmd>
                        <tex:cmd name="hfill" gr="0" nl2="0"/>
                    </tex:parm>
                </xsl:otherwise>
            </xsl:choose>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetXLingPaperEndTableOfContentsMacro
    -->
    <xsl:template name="SetXLingPaperEndTableOfContentsMacro">
        <tex:cmd name="newcommand" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPaperendtableofcontents" gr="0" nl2="0"/>
            </tex:parm>
            <tex:parm>
                <tex:cmd name="immediate" gr="0"/>
                <tex:cmd name="write8">
                    <tex:parm>
                        <tex:spec cat="lt"/>
                        <xsl:text>/toc</xsl:text>
                        <tex:spec cat="gt"/>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="closeout8" gr="0" nl2="0"/>
                <tex:cmd name="relax" gr="0" nl2="1"/>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetXLingPaperEndIndexMacro
    -->
    <xsl:template name="SetXLingPaperEndIndexMacro">
        <tex:cmd name="newcommand" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPaperendindex" gr="0" nl2="0"/>
            </tex:parm>
            <tex:parm>
                <tex:cmd name="immediate" gr="0" nl2="0"/>
                <tex:cmd name="write7">
                    <tex:parm>
                        <tex:spec cat="lt"/>
                        <xsl:text>/idx</xsl:text>
                        <tex:spec cat="gt"/>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="closeout7" gr="0" nl2="0"/>
                <tex:cmd name="relax" gr="0" nl2="1"/>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetXLingPaperAddToContentsMacro
    -->
    <xsl:template name="SetXLingPaperAddToContentsMacro">
        <xsl:call-template name="SetXLingPaperAddElementToTocFile">
            <xsl:with-param name="sCommandName" select="'XLingPaperaddtocontents'"/>
            <xsl:with-param name="sElementName" select="'tocline'"/>
            <xsl:with-param name="sWriteNumber" select="'write8'"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        SetXLingPaperAddToIndexMacro
    -->
    <xsl:template name="SetXLingPaperAddToIndexMacro">
        <xsl:call-template name="SetXLingPaperAddElementToTocFile">
            <xsl:with-param name="sCommandName" select="'XLingPaperaddtoindex'"/>
            <xsl:with-param name="sElementName" select="'indexitem'"/>
            <xsl:with-param name="sWriteNumber" select="'write7'"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        SetLaTeXFootnoteCounter
    -->
    <xsl:template name="SetLaTeXFootnoteCounter">
        <xsl:param name="originalContext"/>
        <xsl:param name="bInTableNumbered" select="'N'"/>
        <tex:cmd name="setcounter">
            <tex:parm>footnote</tex:parm>
            <tex:parm>
                <xsl:call-template name="CalculateFootnoteNumber">
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                    <xsl:with-param name="bInTableNumbered" select="$bInTableNumbered"/>
                </xsl:call-template>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetXLingPaperAddElementToTocFile
    -->
    <xsl:template name="SetXLingPaperAddElementToTocFile">
        <xsl:param name="sElementName"/>
        <xsl:param name="sCommandName"/>
        <xsl:param name="sWriteNumber"/>
        <tex:cmd name="newcommand" nl2="1">
            <tex:parm>
                <tex:cmd name="{$sCommandName}" gr="0" nl2="0"/>
            </tex:parm>
            <tex:opt>1</tex:opt>
            <tex:parm>
                <!--   No: outputs too soon             <tex:cmd name="immediate" gr="0" nl2="0"/>-->
                <tex:cmd name="{$sWriteNumber}">
                    <tex:parm>
                        <tex:spec cat="lt"/>
                        <xsl:value-of select="$sElementName"/>
                        <xsl:text> ref="</xsl:text>
                        <tex:spec cat="parm"/>
                        <xsl:text>1" page="</xsl:text>
                        <tex:cmd name="thepage" gr="0" nl2="0"/>
                        <xsl:text>"/</xsl:text>
                        <tex:spec cat="gt"/>
                    </tex:parm>
                </tex:cmd>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetXLingPaperAdjustIndentOfNonInitialFreeLine
    -->
    <xsl:template name="SetXLingPaperAdjustIndentOfNonInitialFreeLine">
        <xsl:if test="string-length($sAdjustIndentOfNonInitialFreeLineBy) &gt; 0">
            <tex:cmd name="newlength">
                <tex:parm>
                    <tex:cmd name="XLingPaperlongfreewrapindent" gr="0"/>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="newlength">
                <tex:parm>
                    <tex:cmd name="XLingPaperlongfreewrapindentadjust" gr="0"/>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="setlength">
                <tex:parm>
                    <tex:cmd name="XLingPaperlongfreewrapindentadjust" gr="0"/>
                </tex:parm>
                <tex:parm>
                    <xsl:value-of select="$sAdjustIndentOfNonInitialFreeLineBy"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
    </xsl:template>
    <!--  
        SetXLingPaperNeedSpaceMacro
    -->
    <xsl:template name="SetXLingPaperNeedSpaceMacro">
        <!-- based on the Needspace macro from the needspace package 
            #1 is the vertical space needed
        -->
        <tex:cmd name="newcommand" nl2="1" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPaperneedspace" gr="0" nl2="0"/>
            </tex:parm>
            <tex:opt>1</tex:opt>
            <tex:parm>
                <tex:cmd name="penalty" gr="0"/>
                <xsl:text>-100</xsl:text>
                <tex:cmd name="begingroup" gr="0" nl2="1"/>
                <tex:cmd name="newdimen" gr="0" nl2="0">
                    <tex:parm>
                        <tex:cmd name="XLingPaperspaceneeded" gr="0" nl2="0"/>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="newdimen" gr="0" nl1="1" nl2="1">
                    <tex:parm>
                        <tex:cmd name="XLingPaperspaceavailable" gr="0" nl2="0"/>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="setlength" gr="0" nl1="0" nl2="0">
                    <tex:parm>
                        <tex:cmd name="XLingPaperspaceneeded" gr="0" nl2="0"/>
                    </tex:parm>
                    <tex:parm>
                        <tex:spec cat="parm"/>
                        <xsl:text>1</xsl:text>
                    </tex:parm>
                </tex:cmd>
                <tex:spec cat="comment"/>
                <tex:cmd name="XLingPaperspaceavailable" gr="0" nl1="1"/>
                <tex:cmd name="pagegoal" gr="0"/>
                <xsl:text>&#x20;</xsl:text>
                <tex:cmd name="advance" gr="0"/>
                <tex:cmd name="XLingPaperspaceavailable" gr="0"/>
                <xsl:text>-</xsl:text>
                <tex:cmd name="pagetotal" gr="0" nl2="1"/>
                <tex:cmd name="ifdim" gr="0"/>
                <xsl:text>&#x20;</xsl:text>
                <tex:cmd name="XLingPaperspaceneeded" gr="0" nl2="0"/>
                <tex:spec cat="gt"/>
                <tex:cmd name="XLingPaperspaceavailable" gr="0" nl2="1"/>
                <tex:cmd name="ifdim" gr="0"/>
                <xsl:text>&#x20;</xsl:text>
                <tex:cmd name="XLingPaperspaceavailable" gr="0" nl2="0"/>
                <tex:spec cat="gt"/>
                <xsl:text>0pt&#xa;</xsl:text>
                <tex:cmd name="vfil" gr="0" nl2="1"/>
                <tex:cmd name="fi" gr="0" nl2="1"/>
                <tex:cmd name="break" gr="0" nl2="1"/>
                <tex:cmd name="fi" gr="0"/>
                <tex:cmd name="endgroup" gr="0"/>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetXLingPaperTableOfContentsMacro
    -->
    <xsl:template name="SetXLingPaperTableOfContentsMacro">
        <tex:cmd name="newcommand" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPapertableofcontents" gr="0" nl2="0"/>
            </tex:parm>
            <tex:parm>
                <tex:cmd name="immediate" gr="0" nl2="0"/>
                <tex:cmd name="openout8" gr="0" nl2="0"/>
                <xsl:text> = </xsl:text>
                <tex:cmd name="jobname.toc" gr="0" nl2="0"/>
                <tex:cmd name="relax" gr="0" nl2="1"/>
                <tex:cmd name="immediate" gr="0" nl2="0"/>
                <tex:cmd name="write8">
                    <tex:parm>
                        <tex:spec cat="lt"/>
                        <xsl:text>toc</xsl:text>
                        <tex:spec cat="gt"/>
                    </tex:parm>
                </tex:cmd>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetXLingPaperListItemMacro
    -->
    <xsl:template name="SetXLingPaperTableWidthMacros">
        <tex:cmd name="newcommand" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPaperlongestcell" gr="0" nl2="0"/>
            </tex:parm>
            <tex:opt>2</tex:opt>
            <tex:parm>
                <tex:cmd name="ifdim" gr="0" nl1="1"/>
                <tex:spec cat="parm"/>
                <xsl:text>1</xsl:text>
                <tex:spec cat="gt"/>
                <tex:spec cat="parm"/>
                <xsl:text>2
</xsl:text>
                <tex:spec cat="parm"/>
                <xsl:text>2=</xsl:text>
                <tex:spec cat="parm"/>
                <xsl:text>1</xsl:text>
                <tex:cmd name="fi" gr="0" nl1="1" nl2="1"/>
            </tex:parm>
        </tex:cmd>
        <!-- 
        #1 is text to use for calculating minimum width of the cell
        #2 is the column (maximum) minimum width
        #3 is the material to use for calculating  maximum width of the cell
        #4 is the column maximum width
        #5 is an adjustment amount
        -->
        <tex:cmd name="newcommand" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPaperminmaxcellincolumn" gr="0" nl2="0"/>
            </tex:parm>
            <tex:opt>5</tex:opt>
            <tex:parm>
                <tex:cmd name="savebox" nl1="1">
                    <tex:parm>
                        <tex:cmd name="XLingPapertempbox" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <tex:spec cat="parm"/>
                        <xsl:text>3</xsl:text>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="settowidth" nl1="1">
                    <tex:parm>
                        <tex:cmd name="XLingPapertemplen" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <tex:cmd name="usebox">
                            <tex:parm>
                                <tex:cmd name="XLingPapertempbox" gr="0"/>
                            </tex:parm>
                        </tex:cmd>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="addtolength" nl1="1">
                    <tex:parm>
                        <tex:cmd name="XLingPapertemplen" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <tex:spec cat="parm"/>
                        <xsl:text>5</xsl:text>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="XLingPaperlongestcell" nl1="1">
                    <tex:parm>
                        <tex:cmd name="XLingPapertemplen" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <tex:spec cat="parm"/>
                        <xsl:text>4</xsl:text>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="setlength" nl1="1">
                    <tex:parm>
                        <tex:cmd name="XLingPapertemplen" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <tex:cmd name="widthof">
                            <tex:parm>
                                <tex:spec cat="parm"/>
                                <xsl:text>1</xsl:text>
                            </tex:parm>
                        </tex:cmd>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="addtolength" nl1="1">
                    <tex:parm>
                        <tex:cmd name="XLingPapertemplen" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <tex:spec cat="parm"/>
                        <xsl:text>5</xsl:text>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="ifdim" gr="0" nl1="1"/>
                <tex:cmd name="XLingPapertemplen" gr="0" nl2="0"/>
                <tex:spec cat="gt"/>
                <tex:spec cat="parm"/>
                <xsl:text>4</xsl:text>
                <!--                <tex:spec cat="parm" nl1="1"/>-->
                <tex:cmd name="XLingPapertemplen" gr="0" nl1="1"/>
                <xsl:text>=</xsl:text>
                <tex:spec cat="parm"/>
                <xsl:text>4</xsl:text>
                <tex:cmd name="fi" gr="0" nl1="1"/>
                <tex:cmd name="XLingPaperlongestcell" nl1="1">
                    <tex:parm>
                        <tex:cmd name="XLingPapertemplen" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <tex:spec cat="parm"/>
                        <xsl:text>2</xsl:text>
                    </tex:parm>
                </tex:cmd>
            </tex:parm>
        </tex:cmd>
        <!-- 
    #1 is the column width (output)
    #2 is the min width
    #3 is the max width
    #4 is an adjustment amount for column separation
-->
        <tex:cmd name="newcommand" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapersetcolumnwidth" gr="0" nl2="0"/>
            </tex:parm>
            <tex:opt>4</tex:opt>
            <tex:parm>
                <tex:cmd name="ifdim" gr="0" nl1="1"/>
                <tex:cmd name="XLingPapertableminwidth" gr="0" nl2="0"/>
                <tex:spec cat="gt"/>
                <tex:cmd name="XLingPaperavailabletablewidth" gr="0" nl2="0"/>
                <tex:spec cat="parm" nl1="1"/>
                <xsl:text>1=</xsl:text>
                <tex:spec cat="parm"/>
                <xsl:text>2</xsl:text>
                <tex:cmd name="else" gr="0" nl1="1"/>
                <tex:cmd name="ifdim" gr="0" nl1="1"/>
                <tex:cmd name="XLingPapertableminwidth" gr="0" nl2="0"/>
                <xsl:text>=</xsl:text>
                <tex:cmd name="XLingPaperavailabletablewidth" gr="0" nl2="0"/>
                <tex:spec cat="parm" nl1="1"/>
                <xsl:text>1=</xsl:text>
                <tex:spec cat="parm"/>
                <xsl:text>2</xsl:text>
                <tex:cmd name="else" gr="0" nl1="1"/>
                <tex:cmd name="ifdim" gr="0" nl1="1"/>
                <tex:cmd name="XLingPapertablemaxwidth" gr="0" nl2="0"/>
                <tex:spec cat="lt"/>
                <tex:cmd name="XLingPaperavailabletablewidth" gr="0" nl2="0"/>
                <tex:spec cat="parm" nl1="1"/>
                <xsl:text>1=</xsl:text>
                <tex:spec cat="parm"/>
                <xsl:text>3</xsl:text>
                <tex:cmd name="else" gr="0" nl1="1"/>
                <tex:cmd name="setlength" nl1="1">
                    <tex:parm>
                        <tex:cmd name="XLingPapertemplen" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <tex:spec cat="parm"/>
                        <xsl:text>3-</xsl:text>
                        <tex:spec cat="parm"/>
                        <xsl:text>2</xsl:text>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="divide" gr="0" nl1="1">
                    <tex:cmd name="XLingPapertemplen" gr="0"/>
                    <xsl:text> by 100</xsl:text>
                </tex:cmd>
                <tex:cmd name="multiply" gr="0" nl1="1">
                    <tex:cmd name="XLingPapertemplen" gr="0"/>
                    <xsl:text> by </xsl:text>
                    <tex:cmd name="XLingPapertablewidthratio" gr="0"/>
                </tex:cmd>
                <tex:spec cat="parm" nl1="1"/>
                <xsl:text>1=</xsl:text>
                <tex:spec cat="parm"/>
                <xsl:text>2</xsl:text>
                <tex:cmd name="addtolength" nl1="1">
                    <tex:parm>
                        <tex:spec cat="parm"/>
                        <xsl:text>1</xsl:text>
                    </tex:parm>
                    <tex:parm>
                        <tex:cmd name="XLingPapertemplen" gr="0"/>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="addtolength" nl1="1">
                    <tex:parm>
                        <tex:spec cat="parm"/>
                        <xsl:text>1</xsl:text>
                    </tex:parm>
                    <tex:parm>
                        <tex:spec cat="parm"/>
                        <xsl:text>4</xsl:text>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="fi" gr="0" nl1="1"/>
                <tex:cmd name="fi" gr="0" nl1="1"/>
                <tex:cmd name="fi" gr="0" nl1="1" nl2="1"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="newcommand" nl1="1">
            <tex:parm>
                <tex:cmd name="XLingPapercalculatetablewidthratio" gr="0" nl2="0"/>
            </tex:parm>
            <tex:parm>
                <tex:cmd name="setlength" nl1="1">
                    <tex:parm>
                        <tex:cmd name="XLingPapertablewidthminustableminwidth" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <tex:cmd name="XLingPaperavailabletablewidth" gr="0"/>
                        <xsl:text>-</xsl:text>
                        <tex:cmd name="XLingPapertableminwidth" gr="0"/>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="setlength" nl1="1">
                    <tex:parm>
                        <tex:cmd name="XLingPapertablemaxwidthminusminwidth" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <tex:cmd name="XLingPapertablemaxwidth" gr="0"/>
                        <xsl:text>-</xsl:text>
                        <tex:cmd name="XLingPapertableminwidth" gr="0"/>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="ifdim" gr="0" nl1="1"/>
                <tex:cmd name="XLingPapertablemaxwidthminusminwidth" gr="0" nl2="0"/>
                <xsl:text>=0sp</xsl:text>
                <tex:cmd name="XLingPapertablemaxwidthminusminwidth" gr="0" nl1="1"/>
                <xsl:text>=10000sp</xsl:text>
                <tex:cmd name="fi" gr="0" nl1="1"/>
                <tex:cmd name="setlength" nl1="1">
                    <tex:parm>
                        <tex:cmd name="XLingPapertablewidthratio" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <tex:cmd name="XLingPapertablewidthminustableminwidth" gr="0"/>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="divide" nl1="1" gr="0">
                    <tex:cmd name="XLingPapertablemaxwidthminusminwidth" gr="0"/>
                    <xsl:text> by 100</xsl:text>
                </tex:cmd>
                <tex:cmd name="divide" nl1="1" gr="0">
                    <tex:cmd name="XLingPapertablewidthratio" gr="0"/>
                    <xsl:text> by </xsl:text>
                    <tex:cmd name="XLingPapertablemaxwidthminusminwidth" gr="0"/>
                </tex:cmd>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetZeroWidthSpaceHandling
    -->
    <xsl:template name="SetZeroWidthSpaceHandling">
        <tex:spec cat="esc"/>
        <xsl:text>catcode`</xsl:text>
        <tex:spec cat="sup"/>
        <tex:spec cat="sup"/>
        <tex:spec cat="sup"/>
        <tex:spec cat="sup"/>
        <xsl:text>200b=</xsl:text>
        <tex:spec cat="esc"/>
        <xsl:text>active
</xsl:text>
        <tex:spec cat="esc"/>
        <xsl:text>def</xsl:text>
        <tex:spec cat="sup"/>
        <tex:spec cat="sup"/>
        <tex:spec cat="sup"/>
        <tex:spec cat="sup"/>
        <xsl:text>200b</xsl:text>
        <tex:spec cat="bg"/>
        <tex:spec cat="esc"/>
        <xsl:text>hskip0pt</xsl:text>
        <tex:spec cat="eg"/>
    </xsl:template>
    <!--  
        UseFootnoteSymbols
    -->
    <xsl:template name="UseFootnoteSymbols">
        <tex:cmd name="renewcommand">
            <tex:parm>
                <tex:cmd name="thefootnote" gr="0"/>
            </tex:parm>
            <tex:parm>
                <tex:cmd name="fnsymbol">
                    <tex:parm>
                        <xsl:text>footnote</xsl:text>
                    </tex:parm>
                </tex:cmd>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
</xsl:stylesheet>
