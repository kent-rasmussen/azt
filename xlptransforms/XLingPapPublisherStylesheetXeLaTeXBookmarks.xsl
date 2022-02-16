<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:tex="http://getfo.sourceforge.net/texml/ns1" xmlns:saxon="http://icl.com/saxon"
xmlns:exsl="http://exslt.org/common">
    <!--
        abstract  (bookmarks)
    -->
    <xsl:template match="abstract" mode="bookmarks">
        <xsl:call-template name="OutputBookmark">
            <xsl:with-param name="sLink">
                <xsl:call-template name="GetIdToUse">
                    <xsl:with-param name="sBaseId" select="concat($sAbstractID,count(preceding-sibling::abstract))"/>
                </xsl:call-template>
            </xsl:with-param>
            <xsl:with-param name="sLabel">
                <xsl:call-template name="OutputAbstractLabel">
                    <xsl:with-param name="fUseShortTitleIfExists" select="'Y'"/>
                </xsl:call-template>
            </xsl:with-param>
            <xsl:with-param name="sNestingLevel">
                <xsl:choose>
                    <xsl:when test="ancestor::chapterInCollection">
                        <xsl:text>2</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>1</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--
        acknowledgements (bookmarks)
    -->
    <xsl:template match="acknowledgements" mode="bookmarks">
        <xsl:call-template name="OutputBookmark">
            <xsl:with-param name="sLink">
                <xsl:call-template name="GetIdToUse">
                    <xsl:with-param name="sBaseId" select="$sAcknowledgementsID"/>
                </xsl:call-template>
            </xsl:with-param>
            <xsl:with-param name="sLabel">
                <xsl:call-template name="OutputAcknowledgementsLabel"/>
            </xsl:with-param>
            <xsl:with-param name="sNestingLevel">
                <xsl:choose>
                    <xsl:when test="ancestor::chapterInCollection">
                        <xsl:text>2</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>1</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--
        appendix (bookmarks)
    -->
    <xsl:template match="appendix" mode="bookmarks">
        <tex:cmd name="raisebox">
            <tex:parm>
                <tex:cmd name="baselineskip" gr="0"/>
            </tex:parm>
            <tex:opt>0pt</tex:opt>
            <tex:parm>
                <tex:cmd name="pdfbookmark" nl2="0">
                    <xsl:choose>
                        <xsl:when test="ancestor::chapterInCollection">
                            <tex:opt>2</tex:opt>
                        </xsl:when>
                        <xsl:otherwise>
                            <tex:opt>1</tex:opt>
                        </xsl:otherwise>
                    </xsl:choose>
                    <tex:parm>
                        <xsl:call-template name="OutputChapterNumber">
                            <xsl:with-param name="fDoTextAfterLetter" select="'N'"/>
                        </xsl:call-template>
                        <xsl:apply-templates select="secTitle/text() | secTitle/*[name()!='comment']" mode="bookmarks"/>
                        <!--                <xsl:value-of select="secTitle"/>-->
                    </tex:parm>
                    <tex:parm>
                        <xsl:value-of select="translate(@id,$sIDcharsToMap, $sIDcharsMapped)"/>
                    </tex:parm>
                </tex:cmd>
            </tex:parm>
        </tex:cmd>
        <!--        <xsl:apply-templates select="section1 | section2" mode="bookmarks"/>-->
    </xsl:template>
    <!-- 
        chapter (bookmarks) 
    -->
    <xsl:template match="chapter | chapterBeforePart | chapterInCollection" mode="bookmarks">
        <xsl:call-template name="OutputBookmark">
            <xsl:with-param name="sLink" select="@id"/>
            <xsl:with-param name="sLabel">
                <xsl:call-template name="OutputChapterNumber"/>
                <xsl:text>&#xa0;</xsl:text>
                <xsl:apply-templates select="secTitle/text() | secTitle/*[name()!='comment'] | frontMatter/title" mode="bookmarks"/>
            </xsl:with-param>
        </xsl:call-template>
        <!--        <xsl:apply-templates select="section1 | section2" mode="bookmarks"/>-->
    </xsl:template>
    <!--
      contents (bookmarks)
   -->
    <xsl:template match="contents" mode="bookmarks">
        <xsl:param name="id"/>
        <xsl:param name="sTitle"/>
        <xsl:choose>
            <xsl:when test="string-length($id) &gt; 0">
                <xsl:call-template name="OutputBookmark">
                    <xsl:with-param name="sLink" select="$id"/>
                    <xsl:with-param name="sLabel" select="$sTitle"/>
                    <xsl:with-param name="sNestingLevel">
                        <xsl:choose>
                            <xsl:when test="ancestor::chapterInCollection">
                                <xsl:text>2</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>1</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="OutputBookmark">
                    <xsl:with-param name="sLink" select="'rXLingPapContents'"/>
                    <xsl:with-param name="sLabel">
                        <xsl:call-template name="OutputContentsLabel"/>
                    </xsl:with-param>
                    <xsl:with-param name="sNestingLevel">
                        <xsl:choose>
                            <xsl:when test="ancestor::chapterInCollection">
                                <xsl:text>2</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>1</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
      endnote (bookmarks)
   -->
    <xsl:template match="endnote" mode="bookmarks"/>
    <!--
      endnotes (bookmarks)
   -->
    <xsl:template match="endnotes" mode="bookmarks">
        <xsl:call-template name="OutputBookmark">
            <xsl:with-param name="sLink" select="$sEndnotesID"/>
            <xsl:with-param name="sLabel">
                <xsl:call-template name="OutputEndnotesLabel"/>
            </xsl:with-param>
            <xsl:with-param name="sNestingLevel">
                <xsl:choose>
                    <xsl:when test="ancestor::chapterInCollection">
                        <xsl:text>2</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>1</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--
        glossary (bookmarks)
    -->
    <xsl:template match="glossary" mode="bookmarks">
        <xsl:variable name="iPos" select="count(preceding-sibling::glossary) + 1"/>
        <xsl:call-template name="OutputBookmark">
            <xsl:with-param name="sLink" select="concat($sGlossaryID,$iPos)"/>
            <xsl:with-param name="sLabel">
                <xsl:call-template name="OutputGlossaryLabel"/>
            </xsl:with-param>
            <xsl:with-param name="sNestingLevel">
                <xsl:choose>
                    <xsl:when test="ancestor::chapterInCollection">
                        <xsl:text>2</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>1</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--
        index  (bookmarks)
    -->
    <xsl:template match="index" mode="bookmarks">
        <xsl:call-template name="OutputBookmark">
            <xsl:with-param name="sLink">
                <xsl:call-template name="CreateIndexID"/>
            </xsl:with-param>
            <xsl:with-param name="sLabel">
                <xsl:call-template name="OutputIndexLabel"/>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--
        keywords (bookmarks)
    -->
    <xsl:template match="keywordsShownHere[@showincontents='yes']" mode="bookmarks">
        <xsl:call-template name="OutputBookmark">
            <xsl:with-param name="sLink">
                <xsl:call-template name="GetIdToUse">
                    <xsl:with-param name="sBaseId">
                        <xsl:choose>
                            <xsl:when test="parent::frontMatter">
                                <xsl:value-of select="$sKeywordsInFrontMatterID"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="$sKeywordsInBackMatterID"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:with-param>
            <xsl:with-param name="sLabel">
                <xsl:call-template name="OutputKeywordsLabel"/>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>    <!-- 
        part (bookmarks) 
    -->
    <xsl:template match="part" mode="bookmarks">
        <!--        <xsl:param name="nLevel"/>-->
        <!--        <xsl:if test="position()=1">
            <xsl:for-each select="preceding-sibling::*[name()='chapterBeforePart']">
                <xsl:apply-templates select=".">
                    <!-\-                    <xsl:with-param name="nLevel" select="$nLevel"/>-\->
                </xsl:apply-templates>
            </xsl:for-each>
        </xsl:if>
-->
        <tex:cmd name="raisebox">
            <tex:parm>
                <tex:cmd name="baselineskip" gr="0"/>
            </tex:parm>
            <tex:opt>0pt</tex:opt>
            <tex:parm>
                <tex:cmd name="pdfbookmark" nl2="0">
                    <tex:opt>1</tex:opt>
                    <tex:parm>
                        <xsl:call-template name="OutputPartLabel"/>
                        <xsl:text>&#x20;</xsl:text>
                        <xsl:apply-templates select="." mode="numberPart"/>
                        <xsl:text>&#xa0;</xsl:text>
                        <xsl:apply-templates select="secTitle/text() | secTitle/*[name()!='comment']" mode="bookmarks"/>
                        <!--                <xsl:value-of select="secTitle"/>-->
                    </tex:parm>
                    <tex:parm>
                        <xsl:value-of select="translate(@id,$sIDcharsToMap, $sIDcharsMapped)"/>
                    </tex:parm>
                </tex:cmd>
            </tex:parm>
        </tex:cmd>
        <!--        <xsl:apply-templates mode="bookmarks">-->
        <!--                <xsl:with-param name="nLevel" select="$nLevel"/>-->
        <!--        </xsl:apply-templates>-->
    </xsl:template>
    <!--
        preface (bookmarks)
    -->
    <xsl:template match="preface" mode="bookmarks">
        <xsl:call-template name="OutputBookmark">
            <xsl:with-param name="sLink">
                <xsl:variable name="sPos" select="count(preceding-sibling::preface)+1"/>
                <xsl:call-template name="GetIdToUse">
                    <xsl:with-param name="sBaseId" select="concat($sPrefaceID,$sPos)"/>
                </xsl:call-template>
            </xsl:with-param>
            <xsl:with-param name="sLabel">
                <xsl:call-template name="OutputPrefaceLabel"/>
            </xsl:with-param>
            <xsl:with-param name="sNestingLevel">
                <xsl:choose>
                    <xsl:when test="ancestor::chapterInCollection">
                        <xsl:text>2</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>1</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--
        references (bookmarks)
    -->
    <xsl:template match="references" mode="bookmarks">
        <xsl:call-template name="OutputBookmark">
            <xsl:with-param name="sLink">
                <xsl:call-template name="GetIdToUse">
                    <xsl:with-param name="sBaseId" select="$sReferencesID"/>
                </xsl:call-template>
            </xsl:with-param>
            <xsl:with-param name="sLabel">
                <xsl:call-template name="OutputReferencesLabel"/>
            </xsl:with-param>
            <xsl:with-param name="sNestingLevel">
                <xsl:choose>
                    <xsl:when test="ancestor::chapterInCollection">
                        <xsl:text>2</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>1</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!-- 
        section1 (bookmarks) 
    -->
    <xsl:template match="section1" mode="bookmarks">
        <xsl:call-template name="OutputSectionBookmark"/>
        <xsl:if test="$nLevel>=2 and exsl:node-set($bodyLayoutInfo)/section2Layout/@ignore!='yes'">
            <!--                <xsl:apply-templates select="section2" mode="bookmarks"/>-->
        </xsl:if>
    </xsl:template>
    <!-- 
        section2 (bookmarks) 
    -->
    <xsl:template match="section2" mode="bookmarks">
        <xsl:call-template name="OutputSectionBookmark"/>
        <xsl:if test="$nLevel>=3 and exsl:node-set($bodyLayoutInfo)/section3Layout/@ignore!='yes'">
            <!--                <xsl:apply-templates select="section3" mode="bookmarks"/>-->
        </xsl:if>
    </xsl:template>
    <!-- 
        section3 (bookmarks) 
    -->
    <xsl:template match="section3" mode="bookmarks">
        <xsl:call-template name="OutputSectionBookmark"/>
        <xsl:if test="$nLevel>=4 and exsl:node-set($bodyLayoutInfo)/section4Layout/@ignore!='yes'">
            <!--                <xsl:apply-templates select="section4" mode="bookmarks"/>-->
        </xsl:if>
    </xsl:template>
    <!-- 
        section4 (bookmarks) 
    -->
    <xsl:template match="section4" mode="bookmarks">
        <xsl:call-template name="OutputSectionBookmark"/>
        <xsl:if test="$nLevel>=5 and exsl:node-set($bodyLayoutInfo)/section5Layout/@ignore!='yes'">
            <!--                <xsl:apply-templates select="section5" mode="bookmarks"/>-->
        </xsl:if>
    </xsl:template>
    <!-- 
        section5 (bookmarks) 
    -->
    <xsl:template match="section5" mode="bookmarks">
        <xsl:call-template name="OutputSectionBookmark"/>
        <xsl:if test="$nLevel>=6 and exsl:node-set($bodyLayoutInfo)/section6Layout/@ignore!='yes'">
            <!--                <xsl:apply-templates select="section6" mode="bookmarks"/>-->
        </xsl:if>
    </xsl:template>
    <!-- 
        section6 (bookmarks) 
    -->
    <xsl:template match="section6" mode="bookmarks">
        <xsl:call-template name="OutputSectionBookmark"/>
    </xsl:template>
    <!--  
      OutputBookmark
   -->
    <xsl:template name="OutputBookmark">
        <xsl:param name="sLink"/>
        <xsl:param name="sLabel"/>
        <xsl:param name="sNestingLevel" select="'1'"/>
        <tex:cmd name="raisebox">
            <tex:parm>
                <tex:cmd name="baselineskip" gr="0"/>
            </tex:parm>
            <tex:opt>0pt</tex:opt>
            <tex:parm>
                <tex:cmd name="pdfbookmark" nl2="0">
                    <tex:opt>
                        <xsl:value-of select="$sNestingLevel"/>
                    </tex:opt>
                    <tex:parm>
                        <xsl:value-of select="$sLabel"/>
                    </tex:parm>
                    <tex:parm>
                        <xsl:value-of select="translate($sLink,$sIDcharsToMap, $sIDcharsMapped)"/>
                    </tex:parm>
                </tex:cmd>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        OutputSectionBookmark
    -->
    <xsl:template name="OutputSectionBookmark">
        <tex:cmd name="raisebox">
            <tex:parm>
                <tex:cmd name="baselineskip" gr="0"/>
            </tex:parm>
            <tex:opt>0pt</tex:opt>
            <tex:parm>
                <tex:cmd name="pdfbookmark" nl2="0">
                    <xsl:variable name="iLevel" select="substring-after(name(),'section')"/>
                    <tex:opt>
                        <xsl:choose>
                            <xsl:when test="name()='section1' and ancestor::appendix and ancestor::chapterInCollection">3</xsl:when>
                            <xsl:when test="name()='section2' and ancestor::appendix and ancestor::section1">3</xsl:when>
                            <xsl:when test="ancestor::chapter or ancestor::chapterBeforePart or ancestor::chapterInCollection">
                                <xsl:value-of select="$iLevel + 1"/>
                            </xsl:when>
                            <xsl:when test="name()='section1' and ancestor::appendix">2</xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="$iLevel"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </tex:opt>
                    <tex:parm>
                        <xsl:call-template name="OutputSectionNumber">
                            <xsl:with-param name="bIsForBookmark" select="'Y'"/>
                            <xsl:with-param name="sContentsPeriod">
                                <xsl:choose>
                                    <xsl:when test="name()='section1'">
                                        <xsl:if test="not(exsl:node-set($bodyLayoutInfo)/section1Layout/numberLayoutInfo) and exsl:node-set($bodyLayoutInfo)/section1Layout/sectionTitleLayout/@useperiodafternumber='yes'">
                                            <xsl:text>.</xsl:text>
                                        </xsl:if>
                                    </xsl:when>
                                    <xsl:when test="name()='section2'">
                                        <xsl:if test="not(exsl:node-set($bodyLayoutInfo)/section2Layout/numberLayoutInfo) and exsl:node-set($bodyLayoutInfo)/section2Layout/sectionTitleLayout/@useperiodafternumber='yes'">
                                            <xsl:text>.</xsl:text>
                                        </xsl:if>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:if test="not(exsl:node-set($bodyLayoutInfo)/section3Layout/numberLayoutInfo) and exsl:node-set($bodyLayoutInfo)/section3Layout/sectionTitleLayout/@useperiodafternumber='yes'">
                                            <xsl:text>.</xsl:text>
                                        </xsl:if>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:with-param>
                        </xsl:call-template>
                        <xsl:if test="not(count(//section1)=1 and count(//section2)=0)">
                            <xsl:text>&#xa0;</xsl:text>
                        </xsl:if>
                        <xsl:apply-templates select="secTitle/text() | secTitle/*[name()!='comment']" mode="bookmarks"/>
                    </tex:parm>
                    <tex:parm>
                        <xsl:value-of select="translate(@id,$sIDcharsToMap, $sIDcharsMapped)"/>
                    </tex:parm>
                </tex:cmd>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
</xsl:stylesheet>
