<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:tex="http://getfo.sourceforge.net/texml/ns1" xmlns:saxon="http://icl.com/saxon"
xmlns:exsl="http://exslt.org/common">
    <xsl:output method="xml" version="1.0" encoding="utf-8"/>
    <!-- ===========================================================
      Parameters
      =========================================================== -->
    <xsl:param name="sSection1PointSize" select="'12'"/>
    <xsl:param name="sSection2PointSize" select="'10'"/>
    <xsl:param name="sSection3PointSize" select="'10'"/>
    <xsl:param name="sSection4PointSize" select="'10'"/>
    <xsl:param name="sSection5PointSize" select="'10'"/>
    <xsl:param name="sSection6PointSize" select="'10'"/>
    <xsl:param name="sBackMatterItemTitlePointSize" select="'12'"/>
    <xsl:param name="sBlockQuoteIndent" select="'.125in'"/>
    <xsl:param name="sDefaultFontFamily" select="'Times New Roman'"/>
    <!--        <xsl:param name="sDefaultFontFamily" select="'Charis SIL'"/> -->
    <xsl:param name="sFooterMargin" select="'.25in'"/>
    <xsl:param name="sFootnotePointSize" select="'8'"/>
    <xsl:param name="sHeaderMargin" select="'.25in'"/>
    <xsl:param name="sPageWidth" select="'6in'"/>
    <xsl:param name="sPageHeight" select="'9in'"/>
    <xsl:param name="sPageTopMargin" select="'.7in'"/>
    <xsl:param name="sPageBottomMargin" select="'.675in'"/>
    <xsl:param name="sPageInsideMargin" select="'1in'"/>
    <xsl:param name="sPageOutsideMargin" select="'.5in'"/>
    <xsl:param name="sParagraphIndent" select="'1em'"/>
    <xsl:param name="sLinkColor"/>
    <xsl:param name="sLinkTextDecoration"/>
    <!-- the following is actually  the main source file path and name without extension -->
    <xsl:param name="sMainSourcePath" select="'C:/Users/Andy%20Black/Documents/XLingPap/HabPlay'"/>
    <xsl:param name="sMainSourceFile" select="'TestTeXPaperTeXML'"/>
    <xsl:param name="sDirectorySlash" select="'/'"/>
    <xsl:param name="sTableOfContentsFile" select="concat($sMainSourcePath, $sDirectorySlash, 'XLingPaperPDFTemp', $sDirectorySlash, $sMainSourceFile,'.toc')"/>
    <xsl:param name="sIndexFile" select="concat($sMainSourcePath, $sDirectorySlash, 'XLingPaperPDFTemp', $sDirectorySlash, $sMainSourceFile,'.idx')"/>
    <xsl:param name="sFOProcessor">XEP</xsl:param>
    <xsl:param name="sXeLaTeXVersion">2010</xsl:param>
    <xsl:param name="bUseBookTabs" select="'Y'"/>
    <xsl:param name="bDoDebug" select="'n'"/>
    <!-- need a better solution for the following -->
    <xsl:param name="sVernacularFontFamily" select="'Arial Unicode MS'"/>
    <!--
        sInterlinearSourceStyle:
        The default is AfterFirstLine (immediately after the last item in the first line)
        The other possibilities are AfterFree (immediately after the free translation, on the same line)
        and UnderFree (on the line immediately after the free translation)
    -->
    <!--       <xsl:param name="sInterlinearSourceStyle">AfterFirstLine</xsl:param>-->
    <xsl:param name="sInterlinearSourceStyle">AfterFree</xsl:param>
    <xsl:variable name="sLaTeXBasicPointSize" select="$sBasicPointSize"/>
    <xsl:variable name="sExampleIndentBefore" select="$sBlockQuoteIndent"/>
    <xsl:variable name="sExampleIndentAfter" select="'0pt'"/>
    <xsl:variable name="lineSpacing" select="/nothere"/>
    <xsl:variable name="sLineSpacing" select="exsl:node-set($lineSpacing)/@linespacing"/>
    <xsl:variable name="sXLingPaperAbbreviation" select="'XLingPaperAbbreviation'"/>
    <xsl:variable name="sXLingPaperGlossaryTerm" select="'XLingPaperGlossaryTerm'"/>
    <xsl:variable name="iMagnificationFactor">1</xsl:variable>
    <xsl:variable name="sListInitialHorizontalOffset">0pt</xsl:variable>
    <!--    <xsl:variable name="frontMatterLayoutInfo" select="exsl:node-set($publisherStyleSheet)/frontMatterLayout"/>-->
    <xsl:variable name="chapterBeforePart" select="//chapterBeforePart"/>
    <xsl:variable name="annotationLayoutInfo" select="annotationLayout"/>
    <xsl:variable name="iExampleNumberWidthInPoints">
        <xsl:call-template name="ConvertUnitOfMeasureToPoints">
            <xsl:with-param name="sUnitOfMeasure">
                <xsl:value-of select="concat($iNumberWidth,'em')"/>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="iExampleIndentBeforeInPoints">
        <xsl:call-template name="ConvertUnitOfMeasureToPoints">
            <xsl:with-param name="sUnitOfMeasure">
                <xsl:value-of select="$sExampleIndentBefore"/>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="iExampleIndentAfterInPoints">
        <xsl:call-template name="ConvertUnitOfMeasureToPoints">
            <xsl:with-param name="sUnitOfMeasure">
                <xsl:value-of select="$sExampleIndentAfter"/>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="iTableExampleAdjustment">
        <xsl:value-of select="number($iExampleIndentBeforeInPoints + $iExampleNumberWidthInPoints + $iExampleIndentAfterInPoints)"/>
    </xsl:variable>
    <xsl:variable name="iTableExampleInLandscapeWidth">
        <xsl:value-of select="number($iTableInLandscapeWidth - $iTableExampleAdjustment)"/>
    </xsl:variable>
    <xsl:variable name="iTableExampleWidth">
        <xsl:value-of select="number($iTableInPortraitWidth - $iTableExampleAdjustment)"/>
    </xsl:variable>
    <!-- ===========================================================
        MAIN BODY
        =========================================================== -->
    <xsl:template match="/lingPaper">
        <tex:TeXML>
            <xsl:comment> generated by XLingPapXeLaTeX1.xsl Version <xsl:value-of select="$sVersion"/>&#x20;</xsl:comment>
            <tex:cmd name="documentclass" nl2="1">
                <!--            <tex:opt>a4paper</tex:opt>-->
                <tex:opt>
                    <xsl:choose>
                        <xsl:when test="$sBasicPointSize='10'">10</xsl:when>
                        <xsl:when test="$sBasicPointSize='11'">11</xsl:when>
                        <xsl:when test="$sBasicPointSize='12'">12</xsl:when>
                        <xsl:when test="$chapters">10</xsl:when>
                        <xsl:otherwise>12</xsl:otherwise>
                    </xsl:choose>
                    <xsl:text>pt</xsl:text>
                    <xsl:if test="$bHasChapter!='Y'">
                        <xsl:text>,twoside</xsl:text>
                    </xsl:if>
                </tex:opt>
                <tex:parm>
                    <!--                    <xsl:text>article</xsl:text>-->
                    <xsl:choose>
                        <!-- book limits PDF bookmarks to two levels, but we need book for starting on odd pages -->
                        <xsl:when test="$bHasChapter='Y'">
                            <xsl:text>book</xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>article</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </tex:parm>
            </tex:cmd>
            <xsl:call-template name="SetPageLayoutParameters"/>
            <xsl:call-template name="SetSpecialTextSymbols"/>
            <xsl:call-template name="SetUsePackages"/>
            <xsl:call-template name="SetHeaderFooter"/>
            <xsl:call-template name="SetFonts"/>
            <xsl:call-template name="SetFramedTypes"/>
            <tex:cmd name="setlength" nl2="1">
                <tex:parm>
                    <tex:cmd name="parindent" gr="0"/>
                </tex:parm>
                <tex:parm>
                    <xsl:value-of select="$sParagraphIndent"/>
                </tex:parm>
            </tex:cmd>
            <xsl:call-template name="SetZeroWidthSpaceHandling"/>
            <xsl:call-template name="DefineBlockQuoteWithIndent"/>
            <xsl:call-template name="SetClubWidowPenalties"/>
            <xsl:call-template name="SetAbbrInTableBaselineskip"/>
            <tex:env name="document">
                <!-- add some glue to baselineskip -->
                <tex:cmd name="baselineskip" gr="0"/>
                <xsl:text>=</xsl:text>
                <tex:cmd name="glueexpr" gr="0"/>
                <tex:cmd name="baselineskip" gr="0"/>
                <xsl:text> + 0pt plus 2pt minus 1pt</xsl:text>
                <tex:cmd name="relax" gr="0" nl2="1"/>
                <xsl:call-template name="CreateAllNumberingLevelIndentAndWidthCommands"/>
                <tex:spec cat="esc"/>
                <xsl:text>newdimen</xsl:text>
                <tex:spec cat="esc"/>
                <xsl:text>XLingPapertempdim
</xsl:text>
                <tex:spec cat="esc"/>
                <xsl:text>newdimen</xsl:text>
                <tex:spec cat="esc"/>
                <xsl:text>XLingPapertempdimletter
</xsl:text>
                <xsl:call-template name="SetTOCMacros"/>
                <xsl:call-template name="SetTOClengths"/>
                <xsl:if test="$bHasIndex='Y'">
                    <xsl:call-template name="SetXLingPaperIndexMacro"/>
                    <xsl:call-template name="SetXLingPaperAddToIndexMacro"/>
                    <xsl:call-template name="SetXLingPaperIndexItemMacro"/>
                    <xsl:call-template name="SetXLingPaperEndIndexMacro"/>
                    <tex:cmd name="XLingPaperindex" gr="0" nl2="0"/>
                </xsl:if>
                <xsl:call-template name="SetInterlinearSourceLength"/>
                <xsl:if test="contains($fTablesCanWrap,'Y')">
                    <xsl:call-template name="SetTableLengthWidths"/>
                    <xsl:call-template name="SetXLingPaperTableWidthMacros"/>
                </xsl:if>
                <xsl:call-template name="SetXLingPaperNeedSpaceMacro"/>
                <xsl:call-template name="SetListLengthWidths"/>
                <xsl:call-template name="SetXLingPaperListItemMacro"/>
                <xsl:call-template name="SetXLingPaperBlockQuoteMacro"/>
                <xsl:call-template name="SetXLingPaperExampleMacro"/>
                <xsl:call-template name="SetXLingPaperExampleInTableMacro"/>
                <xsl:call-template name="SetXLingPaperFreeMacro"/>
                <xsl:call-template name="SetXLingPaperListInterlinearMacro"/>
                <xsl:call-template name="SetXLingPaperListInterlinearInTableMacro"/>
                <xsl:call-template name="SetXLingPaperExampleFreeIndent"/>
                <xsl:call-template name="SetXLingPaperAdjustHeaderInListInterlinearWithISOCodes"/>
                <xsl:if test="exsl:node-set($lingPaper)/@automaticallywrapinterlinears='yes'">
                    <xsl:call-template name="SetXLingPaperAlignedWordSpacing"/>
                </xsl:if>
                <xsl:call-template name="HandleHyphenationExceptionsFile"/>
                <tex:cmd name="raggedbottom" gr="0" nl2="1"/>
                <tex:env name="MainFont">
                    <xsl:if test="contains($sXeLaTeXVersion,'2020') or exsl:node-set($lingPaper)/@useImageWidthSetToWidthOfExampleFigureOrChart='yes'">
                        <xsl:call-template name="SetImgWidths"/>
                    </xsl:if>
                    <xsl:choose>
                        <xsl:when test="$chapters">
                            <xsl:apply-templates/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:apply-templates select="frontMatter"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </tex:env>
                <xsl:if test="$bHasContents='Y' or $bHasIndex='Y'">
                    <tex:cmd name="clearpage" gr="0"/>
                </xsl:if>
                <xsl:if test="$bHasContents='Y'">
                    <tex:cmd name="XLingPaperendtableofcontents" gr="0" nl2="1"/>
                </xsl:if>
                <xsl:if test="$bHasIndex='Y'">
                    <tex:cmd name="XLingPaperendindex" gr="0" nl2="1"/>
                </xsl:if>
            </tex:env>
        </tex:TeXML>
    </xsl:template>
    <!-- ===========================================================
      FRONTMATTER
      =========================================================== -->
    <xsl:template match="frontMatter">
        <xsl:choose>
            <xsl:when test="$chapters">
                <xsl:if test="not(ancestor::chapterInCollection)">
                    <tex:cmd name="pagestyle" nl2="1">
                        <tex:parm>empty</tex:parm>
                    </tex:cmd>
                    <tex:cmd name="pagenumbering">
                        <tex:parm>roman</tex:parm>
                    </tex:cmd>
                </xsl:if>
                <xsl:choose>
                    <xsl:when test="ancestor::chapterInCollection">
                        <xsl:apply-templates select="author | affiliation | emailAddress | presentedAt | date | version | ../publishingInfo/publishingBlurb"/>
                        <xsl:apply-templates select="contents | acknowledgements | abstract | keywordsShownHere | preface"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:apply-templates select="title | subtitle | author | affiliation | emailAddress | presentedAt | date | version | ../publishingInfo/publishingBlurb"/>
                        <tex:cmd name="pagestyle" nl2="1">
                            <tex:parm>empty</tex:parm>
                        </tex:cmd>
                        <xsl:apply-templates select="contents | acknowledgements | abstract | keywordsShownHere | preface" mode="book"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="title | subtitle | author | affiliation | emailAddress | presentedAt | date | version | ../publishingInfo/publishingBlurb"/>
                <xsl:apply-templates select="contents | acknowledgements | abstract | keywordsShownHere | preface"/>
                <xsl:apply-templates select="//section1[not(parent::appendix)]"/>
                <xsl:apply-templates select="//backMatter"/>
                <!--                <xsl:apply-templates select="//index" mode="Index"/> -->
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
      title
      -->
    <xsl:template match="title[not(ancestor::chapterInCollection)]">
        <xsl:if test="$chapters">
            <tex:cmd name="pagestyle" nl2="1">
                <tex:parm>empty</tex:parm>
            </tex:cmd>
            <tex:cmd name="vspace*" nl2="1">
                <tex:parm>1.25in</tex:parm>
            </tex:cmd>
            <!-- adjust for center environment -->
            <!--            <tex:cmd name="vspace*">
                <tex:parm>
                    <xsl:text>-2</xsl:text>
                    <tex:cmd name="topsep" gr="0"/>
                </tex:parm>
            </tex:cmd>
-->
            <tex:group>
                <tex:cmd name="centering">
                    <tex:parm>
                        <tex:cmd name="TitleFontFamily">
                            <tex:parm>
                                <tex:cmd name="huge">
                                    <tex:parm>
                                        <tex:cmd name="textbf">
                                            <tex:parm>
                                                <xsl:apply-templates/>
                                                <xsl:variable name="contentForThisElement">
                                                    <xsl:apply-templates/>
                                                </xsl:variable>
                                                <xsl:if test="string-length($contentForThisElement) &gt; 0">
                                                    <tex:spec cat="esc"/>
                                                    <tex:spec cat="esc"/>
                                                </xsl:if>
                                            </tex:parm>
                                        </tex:cmd>
                                    </tex:parm>
                                </tex:cmd>
                            </tex:parm>
                        </tex:cmd>
                    </tex:parm>
                </tex:cmd>
            </tex:group>
            <!-- adjust for center environment -->
            <!--<tex:cmd name="vspace*">
                <tex:parm>
                    <xsl:text>-</xsl:text>
                    <tex:cmd name="parsep" gr="0"/>
                </tex:parm>
            </tex:cmd>-->
            <xsl:apply-templates select="following-sibling::subtitle"/>
            <tex:cmd name="cleardoublepage"/>
        </xsl:if>
        <tex:cmd name="vspace*" nl2="1">
            <tex:parm>1in</tex:parm>
        </tex:cmd>
        <!-- adjust for center environment -->
        <!--        <tex:cmd name="vspace*">
            <tex:parm>
                <xsl:text>-2</xsl:text>
                <tex:cmd name="topsep" gr="0"/>
            </tex:parm>
        </tex:cmd>
-->
        <tex:group>
            <tex:cmd name="centering" nl2="1">
                <tex:parm>
                    <tex:cmd name="TitleFontFamily">
                        <tex:parm>
                            <tex:cmd name="LARGE">
                                <tex:parm>
                                    <tex:cmd name="textbf">
                                        <tex:parm>
                                            <xsl:apply-templates/>
                                            <xsl:variable name="contentForThisElement">
                                                <xsl:apply-templates/>
                                            </xsl:variable>
                                            <xsl:if test="string-length($contentForThisElement) &gt; 0">
                                                <tex:spec cat="esc"/>
                                                <tex:spec cat="esc"/>
                                            </xsl:if>
                                        </tex:parm>
                                    </tex:cmd>
                                </tex:parm>
                            </tex:cmd>
                        </tex:parm>
                    </tex:cmd>
                </tex:parm>
            </tex:cmd>
        </tex:group>
        <!-- adjust for center environment -->
        <!--        <tex:cmd name="vspace*">
            <tex:parm>
                <xsl:text>-</xsl:text>
                <tex:cmd name="parsep" gr="0"/>
            </tex:parm>
        </tex:cmd>
-->
        <xsl:if test="not($chapters)">
            <tex:cmd name="thispagestyle" nl2="1">
                <tex:parm>plain</tex:parm>
            </tex:cmd>
        </xsl:if>
        <tex:cmd name="markboth" nl2="1">
            <tex:parm>
                <xsl:choose>
                    <xsl:when test="string-length(../shortTitle) &gt; 0">
                        <xsl:apply-templates select="../shortTitle" mode="InMarker"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <!--                        <xsl:apply-templates select="child::node()[name()!='endnote']"/>-->
                        <xsl:apply-templates mode="InMarker"/>
                    </xsl:otherwise>
                </xsl:choose>
            </tex:parm>
            <tex:parm/>
        </tex:cmd>
    </xsl:template>
    <!--
      subtitle
      -->
    <xsl:template match="subtitle">
        <tex:cmd name="vspace*">
            <tex:parm>.25in</tex:parm>
        </tex:cmd>
        <!-- adjust for center environment -->
        <!--        <tex:cmd name="vspace*">
            <tex:parm>
                <xsl:text>-2</xsl:text>
                <tex:cmd name="topsep" gr="0"/>
            </tex:parm>
        </tex:cmd>
-->
        <tex:group>
            <tex:cmd name="centering" nl1="1">
                <tex:parm>
                    <tex:cmd name="SubtitleFontFamily">
                        <tex:parm>
                            <tex:cmd name="Large">
                                <tex:parm>
                                    <tex:cmd name="textbf">
                                        <tex:parm>
                                            <xsl:apply-templates/>
                                            <xsl:variable name="contentForThisElement">
                                                <xsl:apply-templates/>
                                            </xsl:variable>
                                            <xsl:if test="string-length($contentForThisElement) &gt; 0">
                                                <tex:spec cat="esc"/>
                                                <tex:spec cat="esc"/>
                                            </xsl:if>
                                        </tex:parm>
                                    </tex:cmd>
                                </tex:parm>
                            </tex:cmd>
                        </tex:parm>
                    </tex:cmd>
                </tex:parm>
            </tex:cmd>
        </tex:group>
        <!-- adjust for center environment -->
        <!--        <tex:cmd name="vspace*">
            <tex:parm>
                <xsl:text>-</xsl:text>
                <tex:cmd name="parsep" gr="0"/>
                </tex:parm>
                </tex:cmd>
        -->
    </xsl:template>
    <!--
        author
    -->
    <xsl:template match="author">
        <!-- adjust for center environment -->
        <!--        <tex:cmd name="vspace*">
            <tex:parm>
            <xsl:text>-2</xsl:text>
            <tex:cmd name="topsep" gr="0"/>
            </tex:parm>
            </tex:cmd>
        -->
        <tex:group>
            <xsl:if test="descendant::endnote">
                <xsl:call-template name="UseFootnoteSymbols"/>
            </xsl:if>
            <tex:cmd name="centering">
                <tex:parm>
                    <tex:cmd name="AuthorFontFamily">
                        <tex:parm>
                            <tex:cmd name="textit">
                                <tex:parm>
                                    <xsl:apply-templates/>
                                    <xsl:variable name="contentForThisElement">
                                        <xsl:apply-templates/>
                                    </xsl:variable>
                                    <xsl:if test="string-length($contentForThisElement) &gt; 0">
                                        <tex:spec cat="esc"/>
                                        <tex:spec cat="esc"/>
                                    </xsl:if>
                                </tex:parm>
                            </tex:cmd>
                        </tex:parm>
                    </tex:cmd>
                </tex:parm>
            </tex:cmd>
        </tex:group>
        <!-- adjust for center environment -->
        <!--        <tex:cmd name="vspace*">
            <tex:parm>
                <xsl:text>-</xsl:text>
                <tex:cmd name="parsep" gr="0"/>
            </tex:parm>
        </tex:cmd>
-->
    </xsl:template>
    <!--
      affiliation
      -->
    <xsl:template match="affiliation">
        <tex:group>
            <tex:cmd name="centering" nl1="1">
                <tex:parm>
                    <tex:cmd name="AffiliationFontFamily">
                        <tex:parm>
                            <tex:cmd name="textit">
                                <tex:parm>
                                    <xsl:apply-templates/>
                                    <xsl:variable name="contentForThisElement">
                                        <xsl:apply-templates/>
                                    </xsl:variable>
                                    <xsl:if test="string-length($contentForThisElement) &gt; 0">
                                        <tex:spec cat="esc"/>
                                        <tex:spec cat="esc"/>
                                    </xsl:if>
                                </tex:parm>
                            </tex:cmd>
                        </tex:parm>
                    </tex:cmd>
                </tex:parm>
            </tex:cmd>
        </tex:group>
    </xsl:template>
    <!--
        emailAddress
    -->
    <xsl:template match="emailAddress">
        <tex:group>
            <tex:cmd name="centering" nl1="1">
                <tex:parm>
                    <tex:cmd name="EmailAddressFontFamily">
                        <tex:parm>
                            <tex:cmd name="textit">
                                <tex:parm>
                                    <xsl:apply-templates/>
                                    <xsl:variable name="contentForThisElement">
                                        <xsl:apply-templates/>
                                    </xsl:variable>
                                    <xsl:if test="string-length($contentForThisElement) &gt; 0">
                                        <tex:spec cat="esc"/>
                                        <tex:spec cat="esc"/>
                                    </xsl:if>
                                </tex:parm>
                            </tex:cmd>
                        </tex:parm>
                    </tex:cmd>
                </tex:parm>
            </tex:cmd>
        </tex:group>
    </xsl:template>
    <!--
      date or presentedAt
      -->
    <xsl:template match="date | presentedAt">
        <!-- adjust for center environment -->
        <!--        <tex:cmd name="vspace*">
            <tex:parm>
                <xsl:text>-2</xsl:text>
                <tex:cmd name="topsep" gr="0"/>
            </tex:parm>
        </tex:cmd>
-->
        <tex:group>
            <tex:cmd name="centering" nl1="1">
                <tex:parm>
                    <tex:cmd name="DateFontFamily">
                        <tex:parm>
                            <xsl:apply-templates/>
                            <xsl:variable name="contentForThisElement">
                                <xsl:apply-templates/>
                            </xsl:variable>
                            <xsl:if test="string-length($contentForThisElement) &gt; 0">
                                <xsl:if test="child::*[position()=last()][name()='br'][not(following-sibling::text())]">
                                    <!-- cannot have two \\ in a row, so need to insert something; we'll use a non-breaking space -->
                                    <xsl:text>&#xa0;</xsl:text>
                                </xsl:if>
                                <tex:spec cat="esc"/>
                                <tex:spec cat="esc"/>
                            </xsl:if>
                        </tex:parm>
                    </tex:cmd>
                </tex:parm>
            </tex:cmd>
        </tex:group>
        <!-- adjust for center environment -->
        <!--        <tex:cmd name="vspace*">
            <tex:parm>
                <xsl:text>-</xsl:text>
                <tex:cmd name="parsep" gr="0"/>
            </tex:parm>
        </tex:cmd>
-->
    </xsl:template>
    <!--
      version
      -->
    <xsl:template match="version">
        <tex:group>
            <tex:cmd name="centering" nl1="1">
                <tex:parm>
                    <xsl:text>Version: </xsl:text>
                    <xsl:apply-templates/>
                    <tex:spec cat="esc"/>
                    <tex:spec cat="esc"/>
                </tex:parm>
            </tex:cmd>
        </tex:group>
    </xsl:template>
    <xsl:template match="keywordsShownHere" mode="book">
        <xsl:apply-templates select="self::*"/>
    </xsl:template>
    <xsl:template match="keywordsShownHere">
        <xsl:choose>
            <xsl:when test="$chapters and parent::backMatter">
                <xsl:call-template name="OutputFrontOrBackMatterTitle">
                    <xsl:with-param name="id">
                        <xsl:call-template name="GetKeywordsID"/>
                    </xsl:with-param>
                    <xsl:with-param name="sTitle">
                        <xsl:call-template name="OutputKeywordsLabel"/>
                    </xsl:with-param>
                    <xsl:with-param name="bIsBook" select="'Y'"/>
                    <xsl:with-param name="bForcePageBreak">
                        <xsl:choose>
                            <xsl:when test="$bIsBook!='Y' or ancestor::chapterInCollection">
                                <xsl:text>N</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>Y</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:with-param>
                </xsl:call-template>
                <xsl:call-template name="OutputKeywordsShownHere"/>
                <tex:cmd name="par" nl2="1"/>
            </xsl:when>
            <xsl:when test="not($chapters) and parent::backMatter">
                <xsl:call-template name="OutputFrontOrBackMatterTitle">
                    <xsl:with-param name="id">
                        <xsl:call-template name="GetKeywordsID"/>
                    </xsl:with-param>
                    <xsl:with-param name="sTitle">
                        <xsl:call-template name="OutputKeywordsLabel"/>
                    </xsl:with-param>
                    <xsl:with-param name="bIsBook" select="'N'"/>
                </xsl:call-template>
                <xsl:call-template name="OutputKeywordsShownHere"/>
                <tex:cmd name="par" nl2="1"/>
            </xsl:when>
            <xsl:otherwise>
                <tex:env name="center">
                    <xsl:call-template name="DoInternalTargetBegin">
                        <xsl:with-param name="sName" select="$sKeywordsInFrontMatterID"/>
                    </xsl:call-template>
                    <tex:cmd name="MainFont">
                        <tex:parm>
                            <xsl:call-template name="OutputKeywordsLabel"/>
                            <xsl:call-template name="OutputKeywordsShownHere"/>
                        </tex:parm>
                    </tex:cmd>
                    <xsl:call-template name="DoInternalTargetEnd"/>
                    <xsl:call-template name="CreateAddToContents">
                        <xsl:with-param name="id" select="$sKeywordsInFrontMatterID"/>
                    </xsl:call-template>
                </tex:env>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        publishingBlurb
    -->
    <xsl:template match="publishingInfo/publishingBlurb">
        <tex:env name="flushleft">
            <tex:env name="footnotesize">
                <xsl:apply-templates/>
            </tex:env>
        </tex:env>
    </xsl:template>
    <!--
        contents (for book)
    -->
    <xsl:template match="contents" mode="book">
        <xsl:call-template name="SetBookNonTitlePageStyle"/>
        <xsl:call-template name="DoContents">
            <xsl:with-param name="bIsBook" select="'Y'"/>
        </xsl:call-template>
    </xsl:template>
    <xsl:template name="SetBookNonTitlePageStyle">
        <!-- this is a book and what comes before is the title; it needs to have empty headers and footers; we get this by
            setting the pagestyle to empty before clearing the page.
        -->
        <tex:cmd name="cleardoublepage" nl1="1" nl2="2"/>
        <tex:cmd name="pagestyle">
            <tex:parm>fancy</tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--
      contents (for paper)
      -->
    <xsl:template match="contents">
        <xsl:call-template name="DoContents">
            <xsl:with-param name="bIsBook" select="'N'"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        contents (for chapter in a collection
    -->
    <xsl:template match="contents[ancestor::chapterInCollection]">
        <xsl:call-template name="DoContentsInChapterInCollection"/>
    </xsl:template>
    <!--
      abstract, preface and acknowledgements (for book)
      -->
    <xsl:template match="abstract | acknowledgements | preface" mode="book">
        <!-- need to get (second) title page to use empty page style -->
        <xsl:if test="not(ancestor::chapterInCollection)">
            <xsl:choose>
                <xsl:when test="preceding-sibling::contents">
                    <!-- already done -->
                </xsl:when>
                <xsl:when test="name()='acknowledgements' and not(preceding-sibling::contents)">
                    <xsl:call-template name="SetBookNonTitlePageStyle"/>
                </xsl:when>
                <xsl:when test="name()='abstract' and not(preceding-sibling::contents) and not(preceding-sibling::acknowledgements)">
                    <xsl:call-template name="SetBookNonTitlePageStyle"/>
                </xsl:when>
                <xsl:when test="name()='preface' and not(preceding-sibling::contents) and not(preceding-sibling::acknowledgements) and not(preceding-sibling::preface)">
                    <xsl:call-template name="SetBookNonTitlePageStyle"/>
                </xsl:when>
            </xsl:choose>
        </xsl:if>
        <xsl:call-template name="DoAbstractAcknowledgementsOrPreface">
            <xsl:with-param name="bIsBook" select="'Y'"/>
        </xsl:call-template>
    </xsl:template>
    <!--
      abstract, preface and acknowledgements (paper)
      -->
    <xsl:template match="abstract | acknowledgements | preface">
        <xsl:call-template name="DoAbstractAcknowledgementsOrPreface">
            <xsl:with-param name="bIsBook" select="'N'"/>
        </xsl:call-template>
        <xsl:if test="ancestor::chapterInCollection">
            <!-- need some vertical space because we do not do a page break here -->
            <tex:cmd name="vspace">
                <tex:parm>
                    <tex:cmd name="baselineskip" gr="0"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
    </xsl:template>
    <xsl:template match="abstract" mode="contents">
        <xsl:variable name="sId">
            <xsl:call-template name="GetIdToUse">
                <xsl:with-param name="sBaseId" select="concat($sAbstractID,count(preceding-sibling::abstract))"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:call-template name="OutputTOCLine">
            <xsl:with-param name="sLink" select="$sId"/>
            <xsl:with-param name="sLabel">
                <xsl:call-template name="OutputAbstractLabel"/>
            </xsl:with-param>
            <xsl:with-param name="sIndent">
                <tex:cmd name="leveloneindent" gr="0" nl2="0"/>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <xsl:template match="acknowledgements" mode="contents">
        <xsl:variable name="sId">
            <xsl:call-template name="GetIdToUse">
                <xsl:with-param name="sBaseId" select="$sAcknowledgementsID"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:call-template name="OutputTOCLine">
            <xsl:with-param name="sLink" select="$sId"/>
            <xsl:with-param name="sLabel">
                <xsl:call-template name="OutputAcknowledgementsLabel"/>
            </xsl:with-param>
            <xsl:with-param name="sIndent">
                <tex:cmd name="leveloneindent" gr="0" nl2="0"/>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <xsl:template match="preface" mode="contents">
        <xsl:variable name="sId">
            <xsl:call-template name="GetIdToUse">
                <xsl:with-param name="sBaseId" select="concat($sPrefaceID,'.',count(preceding-sibling::preface)+1)"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:call-template name="OutputTOCLine">
            <xsl:with-param name="sLink" select="$sId"/>
            <xsl:with-param name="sLabel">
                <xsl:call-template name="OutputPrefaceLabel"/>
            </xsl:with-param>
            <xsl:with-param name="sIndent">
                <tex:cmd name="leveloneindent" gr="0" nl2="0"/>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!-- ===========================================================
      PARTS, CHAPTERS, SECTIONS, and APPENDICES
      =========================================================== -->
    <!--
      Part
      -->
    <xsl:template match="part">
        <tex:cmd name="cleardoublepage"/>
        <xsl:if test="not(preceding-sibling::part) and not(//chapterBeforePart)">
            <!-- start using arabic page numbers -->
            <tex:cmd name="pagenumbering">
                <tex:parm>arabic</tex:parm>
            </tex:cmd>
        </xsl:if>
        <tex:cmd name="thispagestyle">
            <tex:parm>empty</tex:parm>
        </tex:cmd>
        <xsl:call-template name="SetStartingPageNumber">
            <xsl:with-param name="startingPageNumber" select="@startingPageNumber"/>
        </xsl:call-template>
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <tex:cmd name="vspace*" nl1="1" nl2="1">
            <tex:parm>144pt</tex:parm>
        </tex:cmd>
        <tex:group nl1="1" nl2="1">
            <!-- adjust for center environment -->
            <!--            <tex:cmd name="vspace*">
                <tex:parm>
                    <xsl:text>-2</xsl:text>
                    <tex:cmd name="topsep" gr="0"/>
                </tex:parm>
            </tex:cmd>
-->
            <tex:group>
                <tex:cmd name="centering" nl2="1">
                    <tex:parm>
                        <xsl:call-template name="DoInternalTargetBegin">
                            <xsl:with-param name="sName" select="@id"/>
                        </xsl:call-template>
                        <tex:cmd name="ChapterFontFamily">
                            <tex:parm>
                                <tex:cmd name="Large">
                                    <tex:parm>
                                        <tex:spec cat="esc"/>
                                        <xsl:text>textbf</xsl:text>
                                        <tex:spec cat="bg"/>
                                        <xsl:call-template name="OutputPartLabel"/>
                                        <xsl:text>&#x20;</xsl:text>
                                        <xsl:apply-templates select="." mode="numberPart"/>
                                        <tex:spec cat="eg"/>
                                    </tex:parm>
                                </tex:cmd>
                            </tex:parm>
                        </tex:cmd>
                        <xsl:call-template name="DoInternalTargetEnd"/>
                        <tex:cmd name="par"/>
                    </tex:parm>
                </tex:cmd>
            </tex:group>
            <!-- adjust for center environment -->
            <!--            <tex:cmd name="vspace*">
                <tex:parm>
                    <xsl:text>-</xsl:text>
                    <tex:cmd name="parsep" gr="0"/>
                </tex:parm>
            </tex:cmd>
-->
            <tex:cmd name="vspace" nl1="1" nl2="1">
                <tex:parm>10.8pt</tex:parm>
            </tex:cmd>
            <!-- adjust for center environment -->
            <!--            <tex:cmd name="vspace*">
                <tex:parm>
                    <xsl:text>-2</xsl:text>
                    <tex:cmd name="topsep" gr="0"/>
                </tex:parm>
            </tex:cmd>
-->
            <tex:group>
                <tex:cmd name="centering" nl2="1">
                    <tex:parm>
                        <tex:cmd name="ChapterFontFamily">
                            <tex:parm>
                                <tex:cmd name="LARGE">
                                    <tex:parm>
                                        <tex:cmd name="raisebox">
                                            <tex:parm>
                                                <tex:cmd name="baselineskip" gr="0"/>
                                            </tex:parm>
                                            <tex:opt>0pt</tex:opt>
                                            <tex:parm>
                                                <tex:cmd name="pdfbookmark" nl2="0">
                                                    <tex:opt>
                                                        <xsl:text>1</xsl:text>
                                                    </tex:opt>
                                                    <tex:parm>
                                                        <xsl:call-template name="OutputSectionNumberAndTitle">
                                                            <xsl:with-param name="bIsBookmark" select="'Y'"/>
                                                        </xsl:call-template>
                                                    </tex:parm>
                                                    <tex:parm>
                                                        <xsl:value-of select="translate(@id,$sIDcharsToMap, $sIDcharsMapped)"/>
                                                    </tex:parm>
                                                </tex:cmd>
                                            </tex:parm>
                                        </tex:cmd>
                                        <tex:spec cat="esc"/>
                                        <xsl:text>textbf</xsl:text>
                                        <tex:spec cat="bg"/>
                                        <xsl:apply-templates select="secTitle"/>
                                        <tex:spec cat="eg"/>
                                    </tex:parm>
                                </tex:cmd>
                            </tex:parm>
                        </tex:cmd>
                        <tex:cmd name="par"/>
                    </tex:parm>
                </tex:cmd>
            </tex:group>
            <!-- adjust for center environment -->
            <!--            <tex:cmd name="vspace*">
                <tex:parm>
                    <xsl:text>-</xsl:text>
                    <tex:cmd name="parsep" gr="0"/>
                </tex:parm>
            </tex:cmd>
-->
            <tex:cmd name="markright" nl2="1">
                <tex:parm>
                    <xsl:call-template name="DoSecTitleRunningHeader"/>
                </tex:parm>
            </tex:cmd>
            <xsl:call-template name="CreateAddToContents">
                <xsl:with-param name="id" select="@id"/>
            </xsl:call-template>
        </tex:group>
        <tex:cmd name="par"/>
        <xsl:call-template name="DoNotBreakHere"/>
        <tex:cmd name="vspace" nl1="1" nl2="1">
            <tex:parm>21.6pt</tex:parm>
        </tex:cmd>
        <xsl:apply-templates select="child::node()[name()!='secTitle' and name()!='chapter' and name()!='chapterInCollection']"/>
        <xsl:apply-templates select="child::node()[name()='chapter' or name()='chapterInCollection']"/>
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="endlandscape" gr="0" nl2="1"/>
        </xsl:if>
    </xsl:template>
    <!--
      Chapter or appendix (in book with chapters)
      -->
    <xsl:template match="chapter | appendix[//chapter]  | chapterBeforePart | chapterInCollection | appendix[//chapterInCollection]">
        <xsl:text>&#x0a;</xsl:text>
        <xsl:if test="not(ancestor::chapterInCollection)">
            <tex:cmd name="cleardoublepage"/>
            <xsl:variable name="bFirstChapterInBook">
                <xsl:choose>
                    <xsl:when test="name()='chapterBeforePart'">Y</xsl:when>
                    <xsl:when test="name()='chapter' and not(preceding-sibling::chapter) and not($parts)">Y</xsl:when>
                    <xsl:when test="name()='chapterInCollection' and not(preceding-sibling::chapterInCollection) and not($parts)">Y</xsl:when>
                    <xsl:when test="name()='chapter' and not(preceding-sibling::chapter) and parent::part and not(parent::part[preceding-sibling::part]) and not($chapterBeforePart)">Y</xsl:when>
                    <xsl:when
                        test="name()='chapterInCollection' and not(preceding-sibling::chapterInCollection)  and parent::part and not(parent::part[preceding-sibling::part]) and not($chapterBeforePart)"
                        >Y</xsl:when>
                </xsl:choose>
            </xsl:variable>
            <!--        <xsl:if test="name()='chapterBeforePart' or name()='chapter' and not(preceding-sibling::chapter) and not(//part) or name()='chapterInCollection' and not(preceding-sibling::chapterInCollection) and not(//part) or name()='chapter' and parent::part and not(parent::part[preceding-sibling::part]) and not //chapterBeforePart or name()='chapterInCollection' and parent::part and not(parent::part[preceding-sibling::part]) and not //chapterBeforePart">-->
            <xsl:if test="contains($bFirstChapterInBook,'Y')">
                <!-- start using arabic page numbers -->
                <tex:cmd name="pagenumbering">
                    <tex:parm>arabic</tex:parm>
                </tex:cmd>
                <xsl:call-template name="SetStartingPageNumberInBook"/>
            </xsl:if>
            <tex:cmd name="thispagestyle">
                <tex:parm>plain</tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:call-template name="SetStartingPageNumber">
            <xsl:with-param name="startingPageNumber" select="@startingPageNumber"/>
        </xsl:call-template>
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <tex:cmd name="vspace*" nl1="1" nl2="1">
            <xsl:choose>
                <xsl:when test="ancestor::chapterInCollection">
                    <tex:parm>24pt</tex:parm>
                </xsl:when>
                <xsl:otherwise>
                    <tex:parm>144pt</tex:parm>
                </xsl:otherwise>
            </xsl:choose>
        </tex:cmd>
        <tex:group nl1="1" nl2="1">
            <tex:cmd name="centerline" nl2="1">
                <tex:parm>
                    <xsl:call-template name="DoInternalTargetBegin">
                        <xsl:with-param name="sName" select="@id"/>
                    </xsl:call-template>
                    <tex:cmd name="ChapterFontFamily">
                        <tex:parm>
                            <tex:cmd name="Large">
                                <tex:parm>
                                    <tex:spec cat="esc"/>
                                    <xsl:text>textbf</xsl:text>
                                    <tex:spec cat="bg"/>
                                    <xsl:call-template name="OutputChapterNumber"/>
                                    <tex:spec cat="eg"/>
                                </tex:parm>
                            </tex:cmd>
                        </tex:parm>
                    </tex:cmd>
                    <xsl:call-template name="DoInternalTargetEnd"/>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="vspace" nl1="1" nl2="1">
                <tex:parm>10.8pt</tex:parm>
            </tex:cmd>
            <!-- adjust for center environment -->
            <!--            <tex:cmd name="vspace*">
                <tex:parm>
                    <xsl:text>-2</xsl:text>
                    <tex:cmd name="topsep" gr="0"/>
                </tex:parm>
            </tex:cmd>
-->
            <tex:group>
                <tex:cmd name="centering" nl2="1">
                    <tex:parm>
                        <tex:cmd name="ChapterFontFamily">
                            <tex:parm>
                                <tex:cmd name="LARGE">
                                    <tex:parm>
                                        <tex:cmd name="raisebox">
                                            <tex:parm>
                                                <tex:cmd name="baselineskip" gr="0"/>
                                            </tex:parm>
                                            <tex:opt>0pt</tex:opt>
                                            <tex:parm>
                                                <tex:cmd name="pdfbookmark" nl2="0">
                                                    <tex:opt>
                                                        <xsl:choose>
                                                            <xsl:when test="name()='appendix' and ancestor::chapterInCollection">
                                                                <xsl:text>2</xsl:text>
                                                            </xsl:when>
                                                            <xsl:otherwise>
                                                                <xsl:text>1</xsl:text>
                                                            </xsl:otherwise>
                                                        </xsl:choose>
                                                    </tex:opt>
                                                    <tex:parm>
                                                        <xsl:call-template name="OutputSectionNumberAndTitle">
                                                            <xsl:with-param name="bIsBookmark" select="'Y'"/>
                                                        </xsl:call-template>
                                                    </tex:parm>
                                                    <tex:parm>
                                                        <xsl:value-of select="translate(@id,$sIDcharsToMap, $sIDcharsMapped)"/>
                                                    </tex:parm>
                                                </tex:cmd>
                                            </tex:parm>
                                        </tex:cmd>
                                        <xsl:call-template name="CreateAddToContents">
                                            <xsl:with-param name="id" select="@id"/>
                                        </xsl:call-template>
                                        <tex:spec cat="esc"/>
                                        <xsl:text>textbf</xsl:text>
                                        <tex:spec cat="bg"/>
                                        <!--                                    <xsl:call-template name="OutputChapTitle">-->
                                        <!--                                        <xsl:with-param name="sTitle">-->
                                        <xsl:apply-templates select="secTitle | frontMatter/title"/>
                                        <!--                                        </xsl:with-param>-->
                                        <!--                                    </xsl:call-template>-->
                                        <xsl:variable name="contentForThisElement">
                                            <xsl:apply-templates select="secTitle | frontMatter/title"/>
                                        </xsl:variable>
                                        <xsl:if test="string-length($contentForThisElement) &gt; 0">
                                            <tex:spec cat="esc"/>
                                            <tex:spec cat="esc"/>
                                        </xsl:if>
                                        <tex:spec cat="eg"/>
                                    </tex:parm>
                                </tex:cmd>
                            </tex:parm>
                        </tex:cmd>
                    </tex:parm>
                </tex:cmd>
            </tex:group>
            <!-- adjust for center environment -->
            <!--            <tex:cmd name="vspace*">
                <tex:parm>
                    <xsl:text>-</xsl:text>
                    <tex:cmd name="parsep" gr="0"/>
                </tex:parm>
            </tex:cmd>
-->
            <tex:cmd name="markboth" nl2="1">
                <tex:parm>
                    <xsl:call-template name="DoSecTitleRunningHeader"/>
                </tex:parm>
                <tex:parm>
                    <xsl:call-template name="DoSecTitleRunningHeader"/>
                </tex:parm>
            </tex:cmd>
        </tex:group>
        <tex:cmd name="par"/>
        <xsl:call-template name="DoNotBreakHere"/>
        <tex:cmd name="vspace" nl1="1" nl2="1">
            <tex:parm>21.6pt</tex:parm>
        </tex:cmd>
        <xsl:apply-templates select="child::node()[name()!='secTitle']"/>
        <xsl:if test="@showinlandscapemode='yes'">
            <xsl:if test="contains(@XeLaTeXSpecial,'fix-final-landscape')">
                <tex:cmd name="XLingPaperendtableofcontents" gr="0"/>
            </xsl:if>
            <tex:cmd name="endlandscape" gr="0" nl2="1"/>
        </xsl:if>
    </xsl:template>
    <!--
      Sections
      -->
    <xsl:template match="section1">
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:call-template name="DoSectionLevelTitle">
            <xsl:with-param name="bIsCentered" select="'Y'"/>
            <xsl:with-param name="sFontFamily" select="'SectionLevelOneFontFamily'"/>
            <xsl:with-param name="sFontSize">large</xsl:with-param>
            <xsl:with-param name="sBold">textbf</xsl:with-param>
        </xsl:call-template>
        <xsl:apply-templates select="child::node()[name()!='secTitle']"/>
        <xsl:if test="@showinlandscapemode='yes'">
            <xsl:if test="contains(@XeLaTeXSpecial,'fix-final-landscape')">
                <tex:cmd name="XLingPaperendtableofcontents" gr="0"/>
            </xsl:if>
            <tex:cmd name="endlandscape" gr="0" nl2="1"/>
        </xsl:if>
    </xsl:template>
    <xsl:template match="section2">
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:call-template name="DoSectionLevelTitle">
            <xsl:with-param name="sFontFamily" select="'SectionLevelTwoFontFamily'"/>
            <xsl:with-param name="sBold">textbf</xsl:with-param>
        </xsl:call-template>
        <xsl:apply-templates select="child::node()[name()!='secTitle']"/>
        <xsl:if test="@showinlandscapemode='yes'">
            <xsl:if test="contains(@XeLaTeXSpecial,'fix-final-landscape')">
                <tex:cmd name="XLingPaperendtableofcontents" gr="0"/>
            </xsl:if>
            <tex:cmd name="endlandscape" gr="0" nl2="1"/>
        </xsl:if>
    </xsl:template>
    <xsl:template match="section3">
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:call-template name="DoSectionLevelTitle">
            <xsl:with-param name="sFontFamily" select="'SectionLevelThreeFontFamily'"/>
            <xsl:with-param name="sItalic">textit</xsl:with-param>
        </xsl:call-template>
        <xsl:apply-templates select="child::node()[name()!='secTitle']"/>
        <xsl:if test="@showinlandscapemode='yes'">
            <xsl:if test="contains(@XeLaTeXSpecial,'fix-final-landscape')">
                <tex:cmd name="XLingPaperendtableofcontents" gr="0"/>
            </xsl:if>
            <tex:cmd name="endlandscape" gr="0" nl2="1"/>
        </xsl:if>
    </xsl:template>
    <xsl:template match="section4 | section5 | section6">
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:call-template name="DoSectionLevelTitle">
            <xsl:with-param name="sFontFamily">
                <xsl:choose>
                    <xsl:when test="name()='section4'">
                        <xsl:text>SectionLevelFourFontFamily</xsl:text>
                    </xsl:when>
                    <xsl:when test="name()='section5'">
                        <xsl:text>SectionLevelFiveFontFamily</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>SectionLevelSixFontFamily</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:with-param>
            <xsl:with-param name="sItalic">textit</xsl:with-param>
        </xsl:call-template>
        <xsl:apply-templates select="child::node()[name()!='secTitle']"/>
        <xsl:if test="@showinlandscapemode='yes'">
            <xsl:if test="contains(@XeLaTeXSpecial,'fix-final-landscape')">
                <tex:cmd name="XLingPaperendtableofcontents" gr="0"/>
            </xsl:if>
            <tex:cmd name="endlandscape" gr="0" nl2="1"/>
        </xsl:if>
    </xsl:template>
    <!--
      Appendix
      -->
    <xsl:template match="appendix[not(//chapter) and not(//chapterInCollection)]">
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:call-template name="OutputFrontOrBackMatterTitle">
            <xsl:with-param name="id" select="@id"/>
            <xsl:with-param name="sTitle">
                <xsl:apply-templates select="." mode="numberAppendix"/>
                <xsl:text disable-output-escaping="yes">.&#x20;</xsl:text>
            </xsl:with-param>
            <xsl:with-param name="titlePart2" select="secTitle"/>
            <xsl:with-param name="bIsBook" select="'N'"/>
            <xsl:with-param name="bForcePageBreak" select="'N'"/>
        </xsl:call-template>
        <xsl:apply-templates select="child::node()[name()!='secTitle']"/>
        <xsl:if test="@showinlandscapemode='yes'">
            <xsl:if test="contains(@XeLaTeXSpecial,'fix-final-landscape')">
                <tex:cmd name="XLingPaperendtableofcontents" gr="0"/>
            </xsl:if>
            <tex:cmd name="endlandscape" gr="0" nl2="1"/>
        </xsl:if>
    </xsl:template>
    <!--
      sectionRef
      -->
    <xsl:template match="sectionRef">
        <xsl:param name="fDoHyperlink" select="'Y'"/>
        <xsl:call-template name="OutputAnyTextBeforeSectionRef"/>
        <xsl:call-template name="DoReferenceShowTitleBefore">
            <xsl:with-param name="showTitle" select="@showTitle"/>
        </xsl:call-template>
        <xsl:if test="$fDoHyperlink='Y'">
            <xsl:call-template name="DoInternalHyperlinkBegin">
                <xsl:with-param name="sName" select="@sec"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="DoSectionRef"/>
        <xsl:if test="$fDoHyperlink='Y'">
            <xsl:call-template name="DoInternalHyperlinkEnd"/>
        </xsl:if>
        <xsl:call-template name="DoReferenceShowTitleAfter">
            <xsl:with-param name="showTitle" select="@showTitle"/>
        </xsl:call-template>
    </xsl:template>
    <!--
      appendixRef
      -->
    <xsl:template match="appendixRef">
        <xsl:param name="fDoHyperlink" select="'Y'"/>
        <xsl:call-template name="OutputAnyTextBeforeAppendixRef"/>
        <xsl:call-template name="DoReferenceShowTitleBefore">
            <xsl:with-param name="showTitle" select="@showTitle"/>
        </xsl:call-template>
        <xsl:if test="$fDoHyperlink='Y'">
            <xsl:call-template name="DoInternalHyperlinkBegin">
                <xsl:with-param name="sName" select="@app"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="DoAppendixRef"/>
        <xsl:if test="$fDoHyperlink='Y'">
            <xsl:call-template name="DoInternalHyperlinkEnd"/>
        </xsl:if>
        <xsl:call-template name="DoReferenceShowTitleAfter">
            <xsl:with-param name="showTitle" select="@showTitle"/>
        </xsl:call-template>
    </xsl:template>
    <!--
      genericRef
      -->
    <xsl:template match="genericRef">
        <xsl:call-template name="AddAnyLinkAttributes"/>
        <xsl:call-template name="DoInternalHyperlinkBegin">
            <xsl:with-param name="sName" select="@gref"/>
        </xsl:call-template>
        <xsl:call-template name="OutputGenericRef"/>
        <xsl:call-template name="DoInternalHyperlinkEnd"/>
    </xsl:template>
    <!--
        link
    -->
    <xsl:template match="link">
        <xsl:call-template name="DoBreakBeforeLink"/>
        <xsl:call-template name="DoExternalHyperRefBegin">
            <xsl:with-param name="sName" select="@href"/>
        </xsl:call-template>
        <xsl:apply-templates/>
        <xsl:call-template name="DoExternalHyperRefEnd"/>
    </xsl:template>
    <!-- ===========================================================
      PARAGRAPH
      =========================================================== -->
    <xsl:template match="p | pc">
        <xsl:choose>
            <xsl:when test="string-length(.)=0 and count(*)=0">
                <!-- this paragraph is empty; do nothing -->
            </xsl:when>
            <xsl:when test="count(child::node())=1 and name(child::node())='comment' and exsl:node-set($lingPaper)/@showcommentinoutput!='yes'">
                <!-- this paragraph is effectively empty since all it has is a comment; do nothing -->
            </xsl:when>
            <xsl:when test="parent::endnote and name()='p' and not(preceding-sibling::p)">
                <!--  and position()='1'" -->
                <xsl:call-template name="OutputTypeAttributes">
                    <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
                </xsl:call-template>
                <xsl:if test="parent::blockquote">
                    <xsl:call-template name="DoType">
                        <xsl:with-param name="type" select="parent::blockquote/@type"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:apply-templates/>
                <xsl:if test="parent::blockquote">
                    <xsl:call-template name="DoTypeEnd">
                        <xsl:with-param name="type" select="parent::blockquote/@type"/>
                    </xsl:call-template>
                </xsl:if>
                <!-- I do not understand why this should make any differemce, but it does.  See Larry Lyman's ZapPron paper, footnote 4 -->
                <xsl:if test="following-sibling::table and ancestor::table">
                    <tex:spec cat="esc"/>
                    <tex:spec cat="esc"/>
                    <!--                    <tex:cmd name="par" nl2="1"/> this causes TeX to halt for the XLingPaper user doc-->
                </xsl:if>
                <xsl:if test="ancestor::li">
                    <!-- we're in a list, so we need to be sure we have a \par to force the preceding material to use the \leftskip and \parindent of a p in a footnote -->
                    <xsl:choose>
                        <xsl:when test="ancestor::table">
                            <!-- cannot use \par here; have to use \\ -->
                            <tex:spec cat="esc"/>
                            <tex:spec cat="esc"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <!--  Turns out that when there are multiple endnotes in a list, that using \par creates extra vertical space between the footnotes.
                                <tex:cmd name="par"/>-->
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:if>
                <xsl:if test="following-sibling::*[1][name()='blockquote']">
                    <xsl:if test="not(ancestor::td)">
                        <!-- we need to be sure we have a \par to force the preceding material to use the \leftskip and \parindent of a p in a footnote -->
                        <tex:cmd name="par"/>
                    </xsl:if>
                </xsl:if>
            </xsl:when>
            <xsl:when test="parent::endnote and name()='p' and preceding-sibling::table[1]">
                <tex:cmd name="par"/>
                <xsl:apply-templates/>
            </xsl:when>
            <xsl:when test="parent::endnote and name()='p' and preceding-sibling::*[name()='p' or name()='pc']">
                <xsl:call-template name="HandlePreviousPInEndnote"/>
            </xsl:when>
            <xsl:when test="parent::endnote and name()='pc' and preceding-sibling::*[name()='p' or name()='pc']">
                <xsl:call-template name="HandlePreviousPInEndnote"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="parent::li and count(preceding-sibling::p) = 0 and count(preceding-sibling::text()) &gt; 0">
                    <tex:cmd name="par"/>
                </xsl:if>
                <xsl:if test="parent::li and name()='p'">
                    <xsl:if test="count(preceding-sibling::p) = 0 or count(preceding-sibling::p) = 1 or count(preceding-sibling::p) = 0 and count(preceding-sibling::text()) &gt; 0">
                        <!-- because we are still within the \XLingPaperlistitem command, we need to force the paragraph indent value back -->
                        <tex:cmd name="setlength">
                            <tex:parm>
                                <tex:cmd name="parindent" gr="0"/>
                            </tex:parm>
                            <tex:parm>
                                <xsl:value-of select="$sParagraphIndent"/>
                            </tex:parm>
                        </tex:cmd>
                    </xsl:if>
                </xsl:if>
                <xsl:choose>
                    <xsl:when test="name()='pc'">
                        <xsl:if test="contains(@XeLaTeXSpecial,'clearpage')">
                            <tex:cmd name="clearpage" gr="0" nl2="0"/>
                        </xsl:if>
                        <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak')">
                            <tex:cmd name="pagebreak" gr="0" nl2="0"/>
                        </xsl:if>
                        <tex:cmd name="noindent" gr="0" nl2="0" sp="1"/>
                    </xsl:when>
                    <xsl:when test="parent::blockquote and count(preceding-sibling::node())=0">
                        <xsl:if test="contains(@XeLaTeXSpecial,'clearpage')">
                            <tex:cmd name="clearpage" gr="0" nl2="0"/>
                        </xsl:if>
                        <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak')">
                            <tex:cmd name="pagebreak" gr="0" nl2="0"/>
                        </xsl:if>
                        <tex:cmd name="noindent" gr="0" nl2="0" sp="1"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:if test="preceding-sibling::*[1][name()='example' or name()='blockquote']">
                            <!-- lose paragraph indent unless we do this when an example precedes; adding \par to the example macro does not work -->
                            <tex:cmd name="par" gr="0" nl2="0"/>
                        </xsl:if>
                        <xsl:if test="contains(@XeLaTeXSpecial,'clearpage')">
                            <tex:cmd name="clearpage" gr="0" nl2="0"/>
                        </xsl:if>
                        <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak')">
                            <tex:cmd name="pagebreak" gr="0" nl2="0"/>
                        </xsl:if>
                        <tex:cmd name="indent" gr="0" nl2="0" sp="1"/>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:if test="parent::blockquote">
                    <!-- want to do this in blockquote, but type kinds of things cannot cross paragraph boundaries, so have to do here -->
                    <xsl:call-template name="DoType">
                        <xsl:with-param name="type" select="parent::blockquote/@type"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="parent::prose-text">
                    <xsl:call-template name="OutputFontAttributes">
                        <xsl:with-param name="language" select="key('LanguageID',parent::prose-text/@lang)"/>
                    </xsl:call-template>
                    <!-- want to do this in prose-text, but type kinds of things cannot cross paragraph boundaries, so have to do here -->
                    <xsl:call-template name="DoType">
                        <xsl:with-param name="type" select="parent::prose-text/@type"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:apply-templates/>
                <xsl:if test="parent::prose-text">
                    <xsl:call-template name="DoTypeEnd">
                        <xsl:with-param name="type" select="parent::prose-text/@type"/>
                    </xsl:call-template>
                    <xsl:call-template name="OutputFontAttributesEnd">
                        <xsl:with-param name="language" select="key('LanguageID',parent::prose-text/@lang)"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="parent::blockquote">
                    <xsl:call-template name="DoTypeEnd">
                        <xsl:with-param name="type" select="parent::blockquote/@type"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:choose>
                    <xsl:when test="ancestor::td">
                        <xsl:text>&#xa;</xsl:text>
                    </xsl:when>
                    <xsl:when test="parent::li and count(preceding-sibling::*)=0 and following-sibling::*[1][name()='p' or name()='pc']">
                        <tex:cmd name="par"/>
                    </xsl:when>
                    <xsl:when test="parent::li and count(preceding-sibling::*)=0">
                        <!-- do nothing -->
                    </xsl:when>
                    <xsl:when test="parent::endnote and count(following-sibling::*)=0">
                        <!-- do nothing -->
                    </xsl:when>
                    <xsl:otherwise>
                        <tex:cmd name="par"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- ===========================================================
        Annotation reference (part of an annotated bibliography)
        =========================================================== -->
    <xsl:template match="annotationRef">
        <xsl:if test="contains(@XeLaTeXSpecial,'clearpage')">
            <tex:cmd name="clearpage" gr="0" nl2="0"/>
        </xsl:if>
        <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak')">
            <tex:cmd name="pagebreak" gr="0" nl2="0"/>
        </xsl:if>
        <xsl:if test="not(parent::example)">
            <tex:spec cat="esc"/>
            <xsl:text>leftskip0in</xsl:text>
            <tex:cmd name="relax" gr="0" nl2="1"/>
        </xsl:if>
        <tex:spec cat="bg"/>
        <tex:spec cat="esc"/>
        <xsl:text>hangindent.25in</xsl:text>
        <tex:cmd name="relax" gr="0" nl2="1"/>
        <tex:spec cat="esc"/>
        <xsl:text>hangafter1</xsl:text>
        <tex:cmd name="relax" gr="0" nl2="1"/>
        <tex:cmd name="noindent"/>
        <xsl:for-each select="key('RefWorkID',@citation)">
            <xsl:call-template name="DoRefWork">
                <xsl:with-param name="works" select="."/>
                <xsl:with-param name="bDoTarget" select="'N'"/>
            </xsl:call-template>
        </xsl:for-each>
        <tex:spec cat="esc"/>
        <xsl:text>leftskip</xsl:text>
        <xsl:choose>
            <xsl:when test="parent::example">
                <tex:cmd name="XLingPaperannoinexampleindent" gr="0" nl2="0"/>
            </xsl:when>
            <xsl:otherwise>.25in</xsl:otherwise>
        </xsl:choose>
        <tex:cmd name="relax" gr="0" nl2="1"/>
        <tex:spec cat="eg"/>
        <xsl:call-template name="DoNestedAnnotations">
            <xsl:with-param name="sList" select="@annotation"/>
        </xsl:call-template>
    </xsl:template>
    <!-- ===========================================================
      QUOTES
      =========================================================== -->
    <!--    <xsl:template match="q">
        <xsl:value-of select="$sLdquo"/>
        <xsl:call-template name="DoType"/>
        <xsl:apply-templates/>
        <xsl:call-template name="DoTypeEnd"/>
        <xsl:value-of select="$sRdquo"/>
    </xsl:template>
    <xsl:template match="blockquote">
        <tex:env name="quotation">
            <xsl:apply-templates/>
        </tex:env>
    </xsl:template>
-->
    <!-- ===========================================================
      EXAMPLES
      =========================================================== -->
    <xsl:template match="example">
        <xsl:variable name="myEndnote" select="ancestor::endnote"/>
        <xsl:variable name="myAncestorLists" select="ancestor::ol | ancestor::ul"/>
        <xsl:if test="parent::li">
            <!-- we need to close the li group and force a paragraph end to maintain the proper indent of this li -->
            <xsl:call-template name="DoTypeForLI">
                <xsl:with-param name="myAncestorLists" select="$myAncestorLists"/>
                <xsl:with-param name="myEndnote" select="$myEndnote"/>
                <xsl:with-param name="bIsEnd" select="'Y'"/>
            </xsl:call-template>
            <tex:spec cat="eg"/>
            <tex:cmd name="par"/>
        </xsl:if>
        <tex:group>
            <xsl:variable name="precedingSibling" select="preceding-sibling::*[1]"/>
            <xsl:if
                test="name($precedingSibling)='p' or name($precedingSibling)='pc' or name($precedingSibling)='example' or name($precedingSibling)='table' or name($precedingSibling)='chart' or name($precedingSibling)='tree' or name($precedingSibling)='interlinear-text' or parent::blockquote and not($precedingSibling)">
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
            <xsl:if test="parent::li and name($precedingSibling)!='example' and name($precedingSibling)!='p' and name($precedingSibling)!='pc' ">
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
            <xsl:variable name="bListsShareSameCode">
                <xsl:call-template name="DetermineIfListsShareSameISOCode"/>
            </xsl:variable>
            <xsl:call-template name="HandleAnyExampleHeadingAdjustWithISOCode">
                <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
            </xsl:call-template>
            <xsl:variable name="sXLingPaperExample">
                <xsl:choose>
                    <xsl:when test="parent::td">
                        <xsl:text>XLingPaperexampleintable</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>XLingPaperexample</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:if test="$sXLingPaperExample='XLingPaperexample'">
                <xsl:if test="contains(@XeLaTeXSpecial,'needspace')">
                    <!-- the needspace seems to be needed to get page breaking right in some cases -->
                    <tex:cmd name="XLingPaperneedspace">
                        <tex:parm>
                            <xsl:call-template name="HandleXeLaTeXSpecialCommand">
                                <xsl:with-param name="sPattern" select="'needspace='"/>
                                <xsl:with-param name="default" select="'1'"/>
                            </xsl:call-template>
                            <tex:cmd name="baselineskip"/>
                        </tex:parm>
                    </tex:cmd>
                </xsl:if>
                <tex:cmd name="raggedright"/>
                <xsl:call-template name="SetExampleKeepWithNext"/>
            </xsl:if>
            <xsl:if test="contains(@XeLaTeXSpecial,'clearpage')">
                <tex:cmd name="clearpage" gr="0" nl2="0"/>
            </xsl:if>
            <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak')">
                <tex:cmd name="pagebreak" gr="0" nl2="0"/>
            </xsl:if>
            <tex:cmd name="{$sXLingPaperExample}" nl1="0" nl2="1">
                <tex:parm>
                    <xsl:value-of select="$sExampleIndentBefore"/>
                </tex:parm>
                <tex:parm>
                    <xsl:value-of select="$sExampleIndentAfter"/>
                </tex:parm>
                <tex:parm>
                    <xsl:value-of select="$iNumberWidth"/>
                    <xsl:text>em</xsl:text>
                </tex:parm>
                <tex:parm>
                    <xsl:call-template name="DoExampleNumber">
                        <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                    </xsl:call-template>
                </tex:parm>
                <tex:parm>
                    <!--               <xsl:choose>
                        <xsl:when test="$bAutomaticallyWrapInterlinears='yes' and interlinear">
                            <tex:cmd name="parbox">
                                <tex:opt>t</tex:opt>
                                <tex:parm>
                                    <tex:cmd name="textwidth" gr="0" nl2="0"/>
                                    <xsl:text> - </xsl:text>
                                    <xsl:value-of select="$sExampleIndentBefore"/>
                                    <xsl:text> - </xsl:text>
                                    <xsl:value-of select="$iNumberWidth"/>
                                    <xsl:text>em - </xsl:text>
                            <!-\-        <xsl:call-template name="GetLetterWidth">
                                        <xsl:with-param name="iLetterCount" select="count(ancestor::listInterlinear[1])"/>
                                    </xsl:call-template>
                                    <xsl:text>em - </xsl:text>
                            -\->        <tex:cmd name="XLingPaperspacewidth" gr="0" nl2="0"/>
<!-\-                                    <xsl:if test="contains($bListsShareSameCode,'N')">
                                        <xsl:text> - </xsl:text>
                                        <tex:cmd name="XLingPaperspacewidth" gr="0" nl2="0"/>
                                        <xsl:text> - </xsl:text>
                                        <tex:cmd name="XLingPaperisocodewidth" gr="0" nl2="0"/>
                                    </xsl:if>
-\->                                </tex:parm>
                            </tex:cmd>
                            <tex:spec cat="bg"/>
                            <xsl:apply-templates>
                                <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                            </xsl:apply-templates>
                            <tex:spec cat="eg"/>
                        </xsl:when>
                        <xsl:otherwise>
                    -->
                    <xsl:call-template name="HandleAnyInterlinearAlignedWordSkipOverride"/>
                    <xsl:apply-templates>
                        <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                    </xsl:apply-templates>
                    <!--                            
                        </xsl:otherwise>
                    </xsl:choose>
-->
                </tex:parm>
            </tex:cmd>
            <!-- 
                </xsl:otherwise>
            </xsl:choose>
            -->
            <!--        </tex:env>-->
            <xsl:variable name="followingSibling" select="following-sibling::*[1]"/>
            <xsl:if test="interlinear and $bAutomaticallyWrapInterlinears='yes' and exsl:node-set($followingSibling)[name()='example' and child::interlinear]">
                <!-- When there are many example/interlinears in a row, we need to tell TeX it's OK to break between them.
                    Otherwise, we get awful page breaking. -->
                <tex:cmd name="smallbreak" gr="0"/>
            </xsl:if>
            <xsl:if
                test="name($followingSibling)='p' or name($followingSibling)='pc' or name($followingSibling)='table' or name($followingSibling)='chart' or name($followingSibling)='tree' or name($followingSibling)='interlinear-text' or parent::li and not(name($followingSibling)='example')">
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
        </tex:group>
        <xsl:if test="parent::li">
            <!-- need to reopen the li group we closed above before this example -->
            <xsl:call-template name="DoTypeForLI">
                <xsl:with-param name="myAncestorLists" select="$myAncestorLists"/>
                <xsl:with-param name="myEndnote" select="$myEndnote"/>
                <xsl:with-param name="bBracketsOnly" select="'Y'"/>
            </xsl:call-template>
            <tex:spec cat="bg"/>
        </xsl:if>
        <xsl:call-template name="HandleEndnoteTextInExampleInTable"/>
    </xsl:template>
    <!--  
        DoEdPlural
    -->
    <xsl:template name="DoEdPlural">
        <xsl:param name="editor"/>
        <xsl:apply-templates select="$editor"/>
        <xsl:text>, ed</xsl:text>
        <xsl:if test="exsl:node-set($editor)/@plural='yes'">
            <xsl:text>s</xsl:text>
        </xsl:if>
        <xsl:text>.</xsl:text>
    </xsl:template>
    <!--
        DoEndnote
    -->
    <xsl:template name="DoEndnote">
        <xsl:param name="sTeXFootnoteKind"/>
        <xsl:param name="originalContext"/>
        <xsl:param name="sPrecalculatedNumber" select="''"/>
        <xsl:variable name="sFootnoteNumber">
            <xsl:choose>
                <xsl:when test="string-length($sPrecalculatedNumber) &gt; 0">
                    <xsl:value-of select="$sPrecalculatedNumber"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="GetFootnoteNumber">
                        <xsl:with-param name="originalContext" select="$originalContext"/>
                        <xsl:with-param name="iAdjust" select="0"/>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:if test="$sTeXFootnoteKind!='footnotetext'">
            <xsl:call-template name="InsertCommaBetweenConsecutiveEndnotesUsingSuperscript"/>
        </xsl:if>
        <xsl:choose>
            <xsl:when test="$originalContext and ancestor::interlinear-text">
                <!-- do nothing for an interlinearRef containing an endnote -->
            </xsl:when>
            <xsl:when test="ancestor::td[@rowspan &gt; 0] and $sTeXFootnoteKind!='footnotetext'">
                <tex:cmd name="footnotemark">
                    <xsl:if test="not(ancestor::interlinear-text)">
                        <tex:opt>
                            <xsl:value-of select="$sFootnoteNumber"/>
                        </tex:opt>
                    </xsl:if>
                </tex:cmd>
            </xsl:when>
            <xsl:when test="count(ancestor::table) &gt; 1 and $sTeXFootnoteKind!='footnotetext' ">
                <tex:cmd name="footnotemark" gr="0"/>
            </xsl:when>
            <xsl:when test="ancestor::example[ancestor::table] and $sTeXFootnoteKind!='footnotetext' ">
                <tex:cmd name="footnotemark" gr="0"/>
            </xsl:when>
            <xsl:when test="ancestor::caption and $sTeXFootnoteKind!='footnotetext' ">
                <tex:cmd name="footnotemark"/>
            </xsl:when>
            <xsl:when test="ancestor::lineGroup and $sTeXFootnoteKind!='footnotetext'">
                <xsl:if test="$originalContext">
                    <xsl:call-template name="AdjustFootnoteNumberPerInterlinearRefs">
                        <xsl:with-param name="originalContext" select="$originalContext"/>
                    </xsl:call-template>
                </xsl:if>
                <tex:cmd name="footnotemark">
                    <xsl:if test="not(ancestor::interlinear-text)">
                        <tex:opt>
                            <xsl:value-of select="$sFootnoteNumber"/>
                        </tex:opt>
                    </xsl:if>
                </tex:cmd>
            </xsl:when>
            <xsl:when test="ancestor::free and $sTeXFootnoteKind!='footnotetext' or ancestor::literal and $sTeXFootnoteKind!='footnotetext'">
                <xsl:if test="$originalContext">
                    <xsl:call-template name="AdjustFootnoteNumberPerInterlinearRefs">
                        <xsl:with-param name="originalContext" select="$originalContext"/>
                    </xsl:call-template>
                </xsl:if>
                <tex:cmd name="footnotemark">
                    <xsl:if test="not(ancestor::interlinear-text)">
                        <tex:opt>
                            <xsl:value-of select="$sFootnoteNumber"/>
                        </tex:opt>
                    </xsl:if>
                </tex:cmd>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="$originalContext and $sTeXFootnoteKind!='footnotetext'">
                    <xsl:call-template name="AdjustFootnoteNumberPerInterlinearRefs">
                        <xsl:with-param name="originalContext" select="$originalContext"/>
                    </xsl:call-template>
                </xsl:if>
                <!-- in some contexts, \footnote needs to be \protected; we do it always since it is not easy to determine such contexts-->
                <tex:cmd name="protect" gr="0"/>
                <tex:cmd name="{$sTeXFootnoteKind}">
                    <xsl:if test="$sTeXFootnoteKind='footnotetext' or not(ancestor::table)">
                        <!-- longtable will not handle the forced footnote number if the column has a 'p' columns spec, so we punt and just use plain \footnote -->
                        <xsl:if test="not(ancestor::interlinear-text) and not(ancestor::listDefinition) and not(ancestor::listSingle)">
                            <tex:opt>
                                <xsl:value-of select="$sFootnoteNumber"/>
                            </tex:opt>
                        </xsl:if>
                        <xsl:if test="ancestor::interlinear-text and following-sibling::endnote">
                            <xsl:if test="ancestor::free or ancestor::literal">
                                <tex:opt>
                                    <xsl:value-of select="$sFootnoteNumber"/>
                                </tex:opt>
                            </xsl:if>
                        </xsl:if>
                    </xsl:if>
                    <tex:parm>
                        <tex:group>
                            <tex:spec cat="esc"/>
                            <xsl:text>leftskip0pt</xsl:text>
                            <tex:spec cat="esc"/>
                            <xsl:text>parindent1em</xsl:text>
                            <xsl:call-template name="DoInternalTargetBegin">
                                <xsl:with-param name="sName" select="@id"/>
                            </xsl:call-template>
                            <xsl:call-template name="DoInternalTargetEnd"/>
                            <xsl:apply-templates/>
                        </tex:group>
                    </tex:parm>
                </tex:cmd>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="parent::blockquote and count(following-sibling::text())=0 and not(following-sibling::endnote)">
            <!-- an endnote ends the initial text in a blockquote; need to insert a \par -->
            <tex:cmd name="par"/>
        </xsl:if>
    </xsl:template>
    <!--  
        DoEndnoteRefCannedText
    -->
    <xsl:template name="DoEndnoteRefCannedText">
        <xsl:text>See footnote </xsl:text>
        <xsl:call-template name="DoEndnoteRefNumber"/>
        <xsl:choose>
            <xsl:when test="$chapters">
                <xsl:text> in chapter </xsl:text>
                <xsl:variable name="sNoteId" select="@note"/>
                <xsl:for-each select="exsl:node-set($chapters)[descendant::endnote[@id=$sNoteId]]">
                    <xsl:number level="any" count="chapter | chapterInCollection" format="1"/>
                </xsl:for-each>
                <xsl:text>.</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>.</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoEndnoteRefNumber
    -->
    <xsl:template name="DoEndnoteRefNumber">
        <xsl:call-template name="DoInternalHyperlinkBegin">
            <xsl:with-param name="sName" select="@note"/>
        </xsl:call-template>
        <xsl:call-template name="AddAnyLinkAttributes"/>
        <xsl:for-each select="key('EndnoteID',@note)">
            <xsl:call-template name="GetFootnoteNumber">
                <xsl:with-param name="iAdjust" select="0"/>
            </xsl:call-template>
        </xsl:for-each>
        <xsl:call-template name="DoInternalHyperlinkEnd"/>
    </xsl:template>
    <!--
        DoExampleNumber
    -->
    <xsl:template name="DoExampleNumber">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:variable name="sIsoCode">
            <xsl:if test="not(listDefinition) and not(definition)">
                <xsl:call-template name="GetISOCode"/>
            </xsl:if>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="string-length($sIsoCode) &gt; 0 and not(contains($bListsShareSameCode,'N'))">
                <tex:cmd name="raisebox">
                    <tex:parm>
                        <xsl:call-template name="AdjustForISOCodeInExampleNumber">
                            <xsl:with-param name="sIsoCode" select="$sIsoCode"/>
                        </xsl:call-template>
                    </tex:parm>
                    <tex:parm>
                        <tex:cmd name="parbox">
                            <tex:opt>b</tex:opt>
                            <tex:parm>
                                <xsl:value-of select="$iNumberWidth"/>
                                <xsl:text>em</xsl:text>
                            </tex:parm>
                            <tex:parm>
                                <xsl:call-template name="DoInternalTargetBegin">
                                    <xsl:with-param name="sName" select="@num"/>
                                </xsl:call-template>
                                <xsl:text>(</xsl:text>
                                <xsl:call-template name="GetExampleNumber">
                                    <xsl:with-param name="example" select="."/>
                                </xsl:call-template>
                                <xsl:text>)</xsl:text>
                                <xsl:call-template name="DoInternalTargetEnd"/>
                                <xsl:call-template name="OutputExampleLevelISOCode">
                                    <xsl:with-param name="sIsoCode" select="$sIsoCode"/>
                                    <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                                </xsl:call-template>
                            </tex:parm>
                        </tex:cmd>
                    </tex:parm>
                </tex:cmd>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="DoInternalTargetBegin">
                    <xsl:with-param name="sName" select="@num"/>
                </xsl:call-template>
                <xsl:text>(</xsl:text>
                <xsl:call-template name="GetExampleNumber">
                    <xsl:with-param name="example" select="."/>
                </xsl:call-template>
                <xsl:text>)</xsl:text>
                <xsl:call-template name="DoInternalTargetEnd"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        exampleRef
    -->
    <xsl:template match="exampleRef">
        <xsl:param name="fDoHyperlink" select="'Y'"/>
        <xsl:if test="$fDoHyperlink='Y'">
            <xsl:call-template name="DoInternalHyperlinkBegin">
                <xsl:with-param name="sName">
                    <xsl:choose>
                        <xsl:when test="@letter and name(id(@letter))!='example'">
                            <xsl:value-of select="@letter"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:if test="@num">
                                <xsl:value-of select="@num"/>
                            </xsl:if>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:with-param>
            </xsl:call-template>
            <xsl:call-template name="AddAnyLinkAttributes"/>
        </xsl:if>
        <xsl:call-template name="DoExampleRefContent"/>
        <xsl:if test="$fDoHyperlink='Y'">
            <xsl:call-template name="DoExternalHyperRefEnd"/>
        </xsl:if>
    </xsl:template>
    <!--
        iso639-3codeRef
    -->
    <xsl:template match="iso639-3codeRef">
        <xsl:param name="fDoHyperlink" select="'Y'"/>
        <xsl:if test="$fDoHyperlink='Y'">
            <xsl:call-template name="DoInternalHyperlinkBegin">
                <xsl:with-param name="sName" select="@lang"/>
            </xsl:call-template>
            <xsl:call-template name="AddAnyLinkAttributes"/>
        </xsl:if>
        <xsl:call-template name="DoISO639-3codeRefContent"/>
        <xsl:if test="$fDoHyperlink='Y'">
            <xsl:call-template name="DoExternalHyperRefEnd"/>
        </xsl:if>
    </xsl:template>
    <!--
        figure
    -->
    <xsl:template match="figure">
        <xsl:choose>
            <xsl:when test="descendant::endnote or @location='here'">
                <!--  cannot have endnotes in floats...
                    If the user says, Put it here, don't treat it like a float                
                -->
                <tex:cmd name="vspace">
                    <tex:parm>
                        <!--    <xsl:value-of select="$sBasicPointSize"/>
                        <xsl:text>pt</xsl:text>-->
                        <xsl:call-template name="GetCurrentPointSize">
                            <xsl:with-param name="bAddGlue" select="'Y'"/>
                        </xsl:call-template>
                    </tex:parm>
                </tex:cmd>
                <xsl:call-template name="DoFigure"/>
                <xsl:if test="not(caption and descendant::img) or caption and descendant::img and not(following-sibling::*[1][name()='figure'])">
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
            </xsl:when>
            <xsl:otherwise>
                <tex:spec cat="esc" nl1="1"/>
                <xsl:text>begin</xsl:text>
                <tex:spec cat="bg"/>
                <xsl:text>figure</xsl:text>
                <tex:spec cat="eg"/>
                <tex:spec cat="lsb"/>
                <xsl:choose>
                    <!-- 2011.04.15: no longer using float for the 'here' but actually putting it here -->
                    <xsl:when test="@location='here'">htbp</xsl:when>
                    <xsl:when test="@location='bottomOfPage'">b</xsl:when>
                    <xsl:when test="@location='topOfPage'">t</xsl:when>
                </xsl:choose>
                <tex:spec cat="rsb" nl2="1"/>
                <xsl:call-template name="DoFigure"/>
                <tex:spec cat="esc" nl1="1"/>
                <xsl:text>end</xsl:text>
                <tex:spec cat="bg"/>
                <xsl:text>figure</xsl:text>
                <tex:spec cat="eg" nl2="1"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        figureRef
    -->
    <xsl:template match="figureRef">
        <xsl:call-template name="OutputAnyTextBeforeFigureRef"/>
        <xsl:call-template name="DoReferenceShowTitleBefore">
            <xsl:with-param name="showTitle" select="@showCaption"/>
        </xsl:call-template>
        <xsl:call-template name="AddAnyLinkAttributes"/>
        <xsl:call-template name="DoInternalHyperlinkBegin">
            <xsl:with-param name="sName" select="@figure"/>
        </xsl:call-template>
        <xsl:call-template name="DoFigureRef"/>
        <xsl:call-template name="DoInternalHyperlinkEnd"/>
        <xsl:call-template name="DoReferenceShowTitleAfter">
            <xsl:with-param name="showTitle" select="@showCaption"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        listOfFiguresShownHere
    -->
    <xsl:template match="listOfFiguresShownHere">
        <xsl:for-each select="//figure[not(ancestor::endnote or ancestor::framedUnit)]">
            <xsl:call-template name="OutputTOCLine">
                <xsl:with-param name="sLink" select="@id"/>
                <xsl:with-param name="sLabel">
                    <xsl:call-template name="OutputFigureLabelAndCaption">
                        <xsl:with-param name="bDoBold" select="'N'"/>
                        <xsl:with-param name="bDoStyles" select="'N'"/>
                    </xsl:call-template>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:for-each>
    </xsl:template>
    <!--
        tablenumbered
    -->
    <xsl:template match="tablenumbered">
        <xsl:choose>
            <xsl:when test="descendant::endnote or @location='here' or ancestor::framedUnit">
                <!--  cannot have endnotes in floats... 
                    If the user says, Put it here, don't treat it like a float                
                -->
                <tex:cmd name="vspace">
                    <tex:parm>
                        <!--    <xsl:value-of select="$sBasicPointSize"/>
                        <xsl:text>pt</xsl:text>-->
                        <xsl:call-template name="GetCurrentPointSize">
                            <xsl:with-param name="bAddGlue" select="'Y'"/>
                        </xsl:call-template>
                    </tex:parm>
                </tex:cmd>
                <xsl:call-template name="DoTableNumbered"/>
                <xsl:if test="exsl:node-set($lingPaper)/@tablenumberedLabelAndCaptionLocation='after'">
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
            </xsl:when>
            <xsl:otherwise>
                <tex:spec cat="esc" nl1="1"/>
                <xsl:text>begin</xsl:text>
                <tex:spec cat="bg"/>
                <xsl:text>table</xsl:text>
                <tex:spec cat="eg"/>
                <tex:spec cat="lsb"/>
                <xsl:choose>
                    <!-- 2011.04.15: no longer using float for the 'here' but actually putting it here -->
                    <xsl:when test="@location='here'">htbp</xsl:when>
                    <xsl:when test="@location='bottomOfPage'">bhp</xsl:when>
                    <xsl:when test="@location='topOfPage'">thp</xsl:when>
                </xsl:choose>
                <tex:spec cat="rsb" nl2="1"/>
                <xsl:call-template name="DoTableNumbered"/>
                <tex:spec cat="esc" nl1="1"/>
                <xsl:text>end</xsl:text>
                <tex:spec cat="bg"/>
                <xsl:text>table</xsl:text>
                <tex:spec cat="eg" nl2="1"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        tablenumberedRef
    -->
    <xsl:template match="tablenumberedRef">
        <xsl:call-template name="OutputAnyTextBeforeTablenumberedRef"/>
        <xsl:call-template name="DoReferenceShowTitleBefore">
            <xsl:with-param name="showTitle" select="@showCaption"/>
        </xsl:call-template>
        <xsl:call-template name="AddAnyLinkAttributes"/>
        <xsl:call-template name="DoInternalHyperlinkBegin">
            <xsl:with-param name="sName" select="@table"/>
        </xsl:call-template>
        <xsl:call-template name="DoTablenumberedRef"/>
        <xsl:call-template name="DoInternalHyperlinkEnd"/>
        <xsl:call-template name="DoReferenceShowTitleAfter">
            <xsl:with-param name="showTitle" select="@showCaption"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        listOfTablesShownHere
    -->
    <xsl:template match="listOfTablesShownHere">
        <xsl:for-each select="//tablenumbered[not(ancestor::endnote or ancestor::framedUnit)]">
            <xsl:call-template name="OutputTOCLine">
                <xsl:with-param name="sLink" select="@id"/>
                <xsl:with-param name="sLabel">
                    <xsl:call-template name="OutputTableNumberedLabelAndCaption">
                        <xsl:with-param name="bDoBold" select="'N'"/>
                        <xsl:with-param name="bDoStyles" select="'N'"/>
                    </xsl:call-template>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:for-each>
    </xsl:template>
    <!-- ===========================================================
        GLOSS
        =========================================================== -->
    <xsl:template match="gloss">
        <xsl:param name="originalContext"/>
        <xsl:param name="bReversing" select="'N'"/>
        <xsl:param name="bInMarker" select="'N'"/>
        <xsl:variable name="language" select="key('LanguageID',@lang)"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($language)/@rtl='yes'">
                <tex:spec cat="bg"/>
            </xsl:when>
            <xsl:when test="not(ancestor::example) and not(ancestor::interlinear-text)">
                <!-- 2012.03.05 I'm not sure why using this is a problem... -->
                <tex:spec cat="bg"/>
            </xsl:when>
        </xsl:choose>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="$language"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:variable name="iCountBr" select="count(child::br)"/>
        <xsl:call-template name="DoEmbeddedBrBegin">
            <xsl:with-param name="iCountBr" select="$iCountBr"/>
        </xsl:call-template>
        <xsl:call-template name="HandleLanguageContent">
            <xsl:with-param name="language" select="$language"/>
            <xsl:with-param name="bReversing" select="$bReversing"/>
            <xsl:with-param name="originalContext" select="$originalContext"/>
            <xsl:with-param name="bInMarker" select="$bInMarker"/>
        </xsl:call-template>
        <xsl:call-template name="DoEmbeddedBrEnd">
            <xsl:with-param name="iCountBr" select="$iCountBr"/>
        </xsl:call-template>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="$language"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:choose>
            <xsl:when test="exsl:node-set($language)/@rtl='yes'">
                <tex:spec cat="eg"/>
            </xsl:when>
            <xsl:when test="not(ancestor::example) and not(ancestor::interlinear-text)">
                <!-- 2012.03.05 I'm not sure why using this is a problem... -->
                <tex:spec cat="eg"/>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!-- ===========================================================
        glossaryTerms
        =========================================================== -->
    <xsl:template match="glossaryTermRef">
        <xsl:choose>
            <xsl:when test="ancestor::genericRef">
                <xsl:call-template name="OutputGlossaryTerm">
                    <xsl:with-param name="glossaryTerm" select="id(@glossaryTerm)"/>
                    <xsl:with-param name="glossaryTermRef" select="."/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <tex:group>
                    <xsl:call-template name="DoInternalHyperlinkBegin">
                        <xsl:with-param name="sName" select="@glossaryTerm"/>
                    </xsl:call-template>
                    <xsl:call-template name="AddAnyLinkAttributes"/>
                    <xsl:call-template name="OutputGlossaryTerm">
                        <xsl:with-param name="glossaryTerm" select="id(@glossaryTerm)"/>
                        <xsl:with-param name="glossaryTermRef" select="."/>
                    </xsl:call-template>
                    <xsl:call-template name="DoInternalHyperlinkEnd"/>
                </tex:group>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- ===========================================================
        LANGDATA
        =========================================================== -->
    <xsl:template match="langData" mode="InMarker">
        <xsl:apply-templates select="self::*"/>
    </xsl:template>
    <xsl:template match="langData">
        <xsl:param name="originalContext"/>
        <xsl:param name="bReversing" select="'N'"/>
        <!-- if we are using \mbox{} to deal with unwanted hyphenation, and the langData begins with a space, we need to insert a space here -->
        <xsl:if test="substring(.,1,1)=' ' and string-length(normalize-space(//lingPaper/@xml:lang))&gt;0">
            <xsl:if test="ancestor::p or ancestor::pc or ancestor::hangingIndent">
                <xsl:text>&#x20;</xsl:text>
            </xsl:if>
        </xsl:if>
        <tex:spec cat="bg"/>
        <xsl:variable name="language" select="key('LanguageID',@lang)"/>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="$language"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:variable name="iCountBr" select="count(child::br)"/>
        <xsl:call-template name="DoEmbeddedBrBegin">
            <xsl:with-param name="iCountBr" select="$iCountBr"/>
        </xsl:call-template>
        <xsl:call-template name="HandleLanguageContent">
            <xsl:with-param name="language" select="$language"/>
            <xsl:with-param name="bReversing" select="$bReversing"/>
            <xsl:with-param name="originalContext" select="$originalContext"/>
        </xsl:call-template>
        <xsl:call-template name="DoEmbeddedBrEnd">
            <xsl:with-param name="iCountBr" select="$iCountBr"/>
        </xsl:call-template>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="$language"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <tex:spec cat="eg"/>
    </xsl:template>
    <!-- ===========================================================
        ENDNOTES and ENDNOTEREFS
        =========================================================== -->
    <!--
        endnotes
    -->
    <!--
        endnote (bookmarks)
    -->
    <xsl:template match="endnote" mode="bookmarks"/>
    <!--
        endnote in flow of text
    -->
    <xsl:template match="endnote">
        <xsl:param name="originalContext"/>
        <xsl:param name="sTeXFootnoteKind" select="'footnote'"/>
        <xsl:param name="sPrecalculatedNumber" select="''"/>
        <xsl:call-template name="DoEndnote">
            <xsl:with-param name="sTeXFootnoteKind" select="$sTeXFootnoteKind"/>
            <xsl:with-param name="originalContext" select="$originalContext"/>
            <xsl:with-param name="sPrecalculatedNumber" select="$sPrecalculatedNumber"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        endnote in langData or gloss
    -->
    <xsl:template match="endnote[parent::langData or parent::gloss]">
        <xsl:param name="sTeXFootnoteKind" select="'footnote'"/>
        <xsl:param name="originalContext"/>
        <!-- need to end any font attributes in effect, do the endnote, and then re-start any font attributes-->
        <xsl:variable name="language" select="key('LanguageID',../@lang)"/>
        <xsl:if test="$sTeXFootnoteKind='footnote'">
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="$language"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="DoEndnote">
            <xsl:with-param name="sTeXFootnoteKind" select="$sTeXFootnoteKind"/>
            <xsl:with-param name="originalContext" select="$originalContext"/>
        </xsl:call-template>
        <xsl:if test="$sTeXFootnoteKind='footnote'">
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="$language"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--
        endnoteRef
    -->
    <xsl:template match="endnoteRef">
        <xsl:choose>
            <xsl:when test="ancestor::endnote">
                <xsl:choose>
                    <xsl:when test="@showNumberOnly!='yes'">
                        <xsl:call-template name="DoEndnoteRefCannedText"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="DoEndnoteRefNumber"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="@showNumberOnly='yes'">
                <xsl:call-template name="DoEndnoteRefNumber"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="sFootnoteNumber">
                    <xsl:call-template name="GetFootnoteNumber">
                        <xsl:with-param name="iAdjust" select="0"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:call-template name="InsertCommaBetweenConsecutiveEndnotesUsingSuperscript"/>
                <tex:cmd name="footnote">
                    <xsl:if test="not(ancestor::table)">
                        <!-- longtable will not handle the forced footnote number if the column has a 'p' columns spec, so we punt and just use plain \footnote -->
                        <tex:opt>
                            <xsl:value-of select="$sFootnoteNumber"/>
                        </tex:opt>
                    </xsl:if>
                    <tex:parm>
                        <xsl:call-template name="DoEndnoteRefCannedText"/>
                        <xsl:apply-templates/>
                    </tex:parm>
                </tex:cmd>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ===========================================================
      CITATIONS, Glossary, Indexes and REFERENCES 
      =========================================================== -->
    <!--
      citation
      -->
    <xsl:template match="//citation[not(parent::selectedBibliography)]">
        <xsl:variable name="refer" select="id(@ref)"/>
        <xsl:call-template name="DoInternalHyperlinkBegin">
            <xsl:with-param name="sName" select="@ref"/>
        </xsl:call-template>
        <xsl:call-template name="AddAnyLinkAttributes"/>
        <xsl:call-template name="DoOutputCitationContents">
            <xsl:with-param name="refer" select="$refer"/>
        </xsl:call-template>
        <xsl:call-template name="DoInternalHyperlinkEnd"/>
        <xsl:if test="parent::blockquote and count(following-sibling::text())=0 and not(following-sibling::endnote)">
            <!-- a citation ends the initial text in a blockquote; need to insert a \par -->
            <tex:cmd name="par"/>
        </xsl:if>
    </xsl:template>
    <!--
      glossary
      -->
    <xsl:template match="glossary">
        <xsl:choose>
            <xsl:when test="$chapters">
                <xsl:call-template name="DoGlossary">
                    <xsl:with-param name="bIsBook" select="'Y'"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="DoGlossary"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
      index
      -->
    <xsl:template match="index">
        <xsl:call-template name="DoIndex"/>
    </xsl:template>
    <!--
        authorContactInfo
    -->
    <xsl:template match="authorContactInfo">
        <xsl:choose>
            <xsl:when test="preceding-sibling::authorContactInfo">
                <tex:cmd name="hfill"/>
            </xsl:when>
            <xsl:otherwise>
                <tex:cmd name="vspace">
                    <tex:parm>24pt</tex:parm>
                </tex:cmd>
                <tex:cmd name="noindent"/>
            </xsl:otherwise>
        </xsl:choose>
        <tex:cmd name="hbox">
            <tex:parm>
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
                    <xsl:variable name="authorInfo" select="key('AuthorContactID',@author)"/>
                    <xsl:apply-templates select="exsl:node-set($authorInfo)/contactName"/>
                    <tex:spec cat="esc"/>
                    <tex:spec cat="esc"/>
                    <xsl:for-each select="exsl:node-set($authorInfo)/contactAffiliation">
                        <xsl:apply-templates select="."/>
                        <tex:spec cat="esc"/>
                        <tex:spec cat="esc"/>
                    </xsl:for-each>
                    <xsl:for-each select="exsl:node-set($authorInfo)/contactAddress">
                        <xsl:apply-templates select="."/>
                        <tex:spec cat="esc"/>
                        <tex:spec cat="esc"/>
                    </xsl:for-each>
                    <xsl:for-each select="exsl:node-set($authorInfo)/contactEmail">
                        <xsl:apply-templates select="."/>
                        <tex:spec cat="esc"/>
                        <tex:spec cat="esc"/>
                    </xsl:for-each>
                    <xsl:for-each select="exsl:node-set($authorInfo)/contactElectronic[@show='yes']">
                        <xsl:apply-templates select="."/>
                        <tex:spec cat="esc"/>
                        <tex:spec cat="esc"/>
                    </xsl:for-each>
                </tex:env>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--
        interlinearRefCitation
    -->
    <xsl:template match="interlinearRefCitation[@showTitleOnly='short' or @showTitleOnly='full']">
        <!-- we do not show any brackets when these options are set -->
        <xsl:call-template name="DoReferenceShowTitleBefore">
            <xsl:with-param name="showTitle" select="@showTitleOnly"/>
        </xsl:call-template>
        <xsl:call-template name="AddAnyLinkAttributes"/>
        <xsl:call-template name="DoInterlinearTextReferenceLinkBegin"/>
        <xsl:call-template name="DoInterlinearRefCitationShowTitleOnly"/>
        <xsl:call-template name="DoInternalHyperlinkEnd"/>
        <xsl:call-template name="DoReferenceShowTitleAfter">
            <xsl:with-param name="showTitle" select="@showTitleOnly"/>
        </xsl:call-template>
    </xsl:template>
    <xsl:template match="interlinearRefCitation">
        <xsl:if test="not(@bracket) or @bracket='both' or @bracket='initial'">
            <xsl:text>[</xsl:text>
        </xsl:if>
        <xsl:variable name="interlinear" select="key('InterlinearReferenceID',@textref)"/>
        <xsl:choose>
            <xsl:when test="name($interlinear)='interlinear-text'">
                <xsl:call-template name="AddAnyLinkAttributes"/>
                <xsl:call-template name="DoInterlinearTextReferenceLinkBegin"/>
                <xsl:choose>
                    <xsl:when test="exsl:node-set($interlinear)/textInfo/shortTitle and string-length(exsl:node-set($interlinear)/textInfo/shortTitle) &gt; 0">
                        <xsl:apply-templates select="exsl:node-set($interlinear)/textInfo/shortTitle/child::node()[name()!='endnote']"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:apply-templates select="exsl:node-set($interlinear)/textInfo/textTitle/child::node()[name()!='endnote']"/>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:call-template name="DoInternalHyperlinkEnd"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="DoInterlinearRefCitation">
                    <xsl:with-param name="sRef" select="@textref"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="not(@bracket) or @bracket='both' or @bracket='final'">
            <xsl:text>]</xsl:text>
        </xsl:if>
    </xsl:template>
    <!--
      references
      -->
    <xsl:template match="references">
        <xsl:choose>
            <xsl:when test="$chapters">
                <xsl:call-template name="DoReferences">
                    <xsl:with-param name="bIsBook" select="'Y'"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="DoReferences"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
      refTitle
      -->
    <xsl:template match="refTitle">
        <xsl:variable name="sTitle" select="normalize-space(.)"/>
        <xsl:if test="string-length($sTitle) &gt; 0">
            <xsl:apply-templates/>
        </xsl:if>
    </xsl:template>
    <!-- ===========================================================
      ABBREVIATION
      =========================================================== -->
    <xsl:template match="abbrRef">
        <xsl:param name="bInMarker" select="'N'"/>
        <xsl:choose>
            <xsl:when test="ancestor::genericRef">
                <xsl:call-template name="OutputAbbrTerm">
                    <xsl:with-param name="abbr" select="id(@abbr)"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <tex:group>
                    <xsl:if test="$bInMarker!='Y'">
                        <xsl:call-template name="DoInternalHyperlinkBegin">
                            <xsl:with-param name="sName" select="@abbr"/>
                        </xsl:call-template>
                        <xsl:call-template name="AddAnyLinkAttributes"/>
                    </xsl:if>
                    <xsl:for-each select="ancestor::gloss">
                        <xsl:sort order="descending"/>
                        <xsl:call-template name="OutputFontAttributes">
                            <xsl:with-param name="language" select="key('LanguageID',@lang)"/>
                        </xsl:call-template>
                    </xsl:for-each>
                    <xsl:for-each select="ancestor::object">
                        <xsl:sort order="descending"/>
                        <xsl:call-template name="DoType">
                            <xsl:with-param name="type" select="@type"/>
                        </xsl:call-template>
                    </xsl:for-each>
                    <xsl:call-template name="OutputAbbrTerm">
                        <xsl:with-param name="abbr" select="id(@abbr)"/>
                    </xsl:call-template>
                    <xsl:for-each select="ancestor::object">
                        <xsl:sort order="descending"/>
                        <xsl:call-template name="DoTypeEnd">
                            <xsl:with-param name="type" select="@type"/>
                        </xsl:call-template>
                    </xsl:for-each>
                    <xsl:for-each select="ancestor::gloss">
                        <xsl:sort order="descending"/>
                        <xsl:call-template name="OutputFontAttributesEnd">
                            <xsl:with-param name="language" select="key('LanguageID',@lang)"/>
                        </xsl:call-template>
                    </xsl:for-each>
                    <xsl:if test="$bInMarker!='Y'">
                        <xsl:call-template name="DoInternalHyperlinkEnd"/>
                    </xsl:if>
                </tex:group>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- ===========================================================
      NUMBERING PROCESSING 
      =========================================================== -->
    <!--  
                  sections
-->
    <xsl:template mode="number" match="*">
        <xsl:choose>
            <xsl:when test="ancestor-or-self::chapter">
                <xsl:apply-templates select="." mode="numberChapter"/>
                <xsl:if test="ancestor::chapter">
                    <xsl:text>.</xsl:text>
                </xsl:if>
            </xsl:when>
            <xsl:when test="ancestor-or-self::chapterInCollection">
                <xsl:apply-templates select="." mode="numberChapter"/>
                <xsl:if test="ancestor::chapterInCollection">
                    <xsl:text>.</xsl:text>
                </xsl:if>
            </xsl:when>
            <xsl:when test="ancestor-or-self::chapterBeforePart">
                <xsl:text>0</xsl:text>
                <xsl:if test="ancestor::chapterBeforePart">
                    <xsl:text>.</xsl:text>
                </xsl:if>
            </xsl:when>
        </xsl:choose>
        <!--
        <xsl:if test="$chapters">
            <xsl:apply-templates select="." mode="numberChapter"/>.</xsl:if>
            -->
        <xsl:choose>
            <xsl:when test="count($chapters)=0 and count(//section1)=1 and count(//section1/section2)=0">
                <!-- if there are no chapters and there is but one section1 (with no subsections), there's no need to have a number so don't  -->
            </xsl:when>
            <xsl:otherwise>
                <xsl:number level="multiple" count="section1 | section2 | section3 | section4 | section5 | section6" format="1.1"/>
            </xsl:otherwise>
        </xsl:choose>
        <!--      <xsl:variable name="numAt1">
         <xsl:number level="multiple" count="section1 | section2 | section3 | section4 | section5 | section6" format="1.1"/>
      </xsl:variable>
-->
        <!--  adjust section1 number down by one to start with 0 -->
        <!--      <xsl:variable name="num1" select="substring-before($numAt1,'.')"/>
      <xsl:variable name="numRest" select="substring-after($numAt1,'.')"/>
      <xsl:variable name="num1At0">
         <xsl:choose>
            <xsl:when test="$num1">
               <xsl:value-of select="number($num1)-1"/>
               <xsl:text>.</xsl:text>
            </xsl:when>
            <xsl:otherwise>
               <xsl:value-of select="number($numAt1)-1"/>
            </xsl:otherwise>
         </xsl:choose>
      </xsl:variable>
      <xsl:value-of select="$num1At0"/>
      <xsl:value-of select="$numRest"/>
-->
    </xsl:template>
    <!--  
                  endnote
-->
    <xsl:template mode="endnote" match="endnote[parent::author]">
        <xsl:variable name="iAuthorPosition" select="count(ancestor::author/preceding-sibling::author[endnote]) + 1"/>
        <xsl:value-of select="$iAuthorPosition"/>
    </xsl:template>
    <!--  
        figure
    -->
    <xsl:template mode="figure" match="*" priority="10">
        <xsl:choose>
            <xsl:when test="$chapters">
                <xsl:for-each select="ancestor::chapter | ancestor::appendix | ancestor::chapterBeforePart | ancestor::chapterInCollection">
                    <xsl:call-template name="OutputChapterNumber">
                        <xsl:with-param name="fIgnoreTextAfterLetter" select="'Y'"/>
                    </xsl:call-template>
                </xsl:for-each>
                <xsl:text>.</xsl:text>
                <xsl:number level="any" count="figure[not(ancestor::endnote or ancestor::framedUnit)]" from="chapter | appendix | chapterBeforePart | chapterInCollection" format="1"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:number level="any" count="figure[not(ancestor::endnote or ancestor::framedUnit)]" format="1"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        tablenumbered
    -->
    <xsl:template mode="tablenumbered" match="*" priority="10">
        <xsl:choose>
            <xsl:when test="$chapters">
                <xsl:for-each select="ancestor::chapter | ancestor::appendix | ancestor::chapterBeforePart | ancestor::chapterInCollection">
                    <xsl:call-template name="OutputChapterNumber">
                        <xsl:with-param name="fIgnoreTextAfterLetter" select="'Y'"/>
                    </xsl:call-template>
                </xsl:for-each>
                <xsl:text>.</xsl:text>
                <xsl:number level="any" count="tablenumbered[not(ancestor::endnote or ancestor::framedUnit)]" from="chapter | appendix | chapterBeforePart | chapterInCollection" format="1"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:number level="any" count="tablenumbered[not(ancestor::endnote or ancestor::framedUnit)]" format="1"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
                  letter
-->
    <xsl:template mode="letter" match="*">
        <xsl:number level="single" count="listWord | listSingle | listInterlinear | listDefinition | lineSet" format="a"/>
    </xsl:template>
    <xsl:template match="shortTitle"/>
    <xsl:template match="shortTitle" mode="InMarker">
        <xsl:apply-templates/>
    </xsl:template>
    <!-- ===========================================================
      NAMED TEMPLATES
      =========================================================== -->
    <!--
                  AddAnyLinkAttributes
                                    -->
    <xsl:template name="AddAnyLinkAttributes">
        <xsl:if test="$sLinkColor">
            <xsl:attribute name="color">
                <xsl:value-of select="$sLinkColor"/>
            </xsl:attribute>
        </xsl:if>
        <xsl:if test="$sLinkTextDecoration">
            <xsl:attribute name="text-decoration">
                <xsl:value-of select="$sLinkTextDecoration"/>
            </xsl:attribute>
        </xsl:if>
    </xsl:template>
    <!--
      CalculateColumnPosition
   -->
    <xsl:template name="CalculateColumnPosition">
        <xsl:param name="iColspan" select="0"/>
        <xsl:param name="iBorder" select="0"/>
        <xsl:param name="sAlignDefault" select="'l'"/>
        <xsl:call-template name="CreateVerticalLine">
            <xsl:with-param name="iBorder" select="$iBorder"/>
        </xsl:call-template>
        <xsl:choose>
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
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--
                  CheckSeeTargetIsCitedOrItsDescendantIsCited
                                    -->
    <xsl:template name="CheckSeeTargetIsCitedOrItsDescendantIsCited">
        <xsl:variable name="sSee" select="@see"/>
        <xsl:choose>
            <xsl:when test="//indexedItem[@term=$sSee][not(ancestor::comment)] | //indexedRangeBegin[@term=$sSee][not(ancestor::comment)]">
                <xsl:text>Y</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:for-each select="key('IndexTermID',@see)/descendant::indexTerm">
                    <xsl:variable name="sDescendantTermId" select="@id"/>
                    <xsl:if test="//indexedItem[@term=$sDescendantTermId][not(ancestor::comment)] or //indexedRangeBegin[@term=$sDescendantTermId][not(ancestor::comment)]">
                        <xsl:text>Y</xsl:text>
                    </xsl:if>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
      CreateGlossaryID
   -->
    <xsl:template name="CreateGlossaryID">
        <xsl:call-template name="GetIdToUse">
            <xsl:with-param name="sBaseId">
                <xsl:value-of select="$sGlossaryID"/>
                <xsl:text>.</xsl:text>
                <xsl:value-of select="count(preceding-sibling::glossary)+1"/>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--
        DefineLangaugeAndTypeFonts
    -->
    <xsl:template name="DefineLangaugeAndTypeFonts">
        <xsl:for-each select="//language | //type[string-length(normalize-space(@font-family)) &gt; 0] | //keyTerm[string-length(normalize-space(@font-family)) &gt; 0]">
            <xsl:call-template name="DefineAFontFamily">
                <xsl:with-param name="sFontFamilyName">
                    <xsl:call-template name="FontFamilyNameToUse">
                        <xsl:with-param name="language" select="."/>
                        <xsl:with-param name="id" select="@id"/>
                    </xsl:call-template>
                </xsl:with-param>
                <xsl:with-param name="sBaseFontName">
                    <xsl:variable name="sFontFamily" select="normalize-space(@font-family)"/>
                    <xsl:choose>
                        <xsl:when test="string-length($sFontFamily) &gt; 0">
                            <xsl:value-of select="$sFontFamily"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$sDefaultFontFamily"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:for-each>
    </xsl:template>
    <!--  
      DoAbbreviations
   -->
    <xsl:template name="DoAbbreviations">
        <xsl:call-template name="OutputFrontOrBackMatterTitle">
            <xsl:with-param name="id" select="'rXLingPapAbbreviations'"/>
            <xsl:with-param name="sTitle">
                <xsl:call-template name="OutputAbbreviationsLabel"/>
            </xsl:with-param>
            <xsl:with-param name="bIsBook" select="'N'"/>
            <xsl:with-param name="bForcePageBreak" select="'N'"/>
        </xsl:call-template>
        <xsl:call-template name="OutputAbbreviationsInTable"/>
    </xsl:template>
    <!--
        DoAbstractAcknowledgementsOrPreface
    -->
    <xsl:template name="DoAbstractAcknowledgementsOrPreface">
        <xsl:param name="bIsBook" select="'Y'"/>
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:variable name="bForcePageBreak">
            <xsl:choose>
                <xsl:when test="ancestor::chapterInCollection">
                    <xsl:text>N</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$bIsBook"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="name(.)='abstract'">
                <xsl:call-template name="OutputFrontOrBackMatterTitle">
                    <xsl:with-param name="id">
                        <xsl:call-template name="GetIdToUse">
                            <xsl:with-param name="sBaseId" select="concat($sAbstractID,count(preceding-sibling::abstract))"/>
                        </xsl:call-template>
                    </xsl:with-param>
                    <xsl:with-param name="sTitle">
                        <xsl:call-template name="OutputAbstractLabel"/>
                    </xsl:with-param>
                    <xsl:with-param name="bIsBook" select="$bIsBook"/>
                    <xsl:with-param name="bForcePageBreak" select="$bForcePageBreak"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="name(.)='acknowledgements'">
                <xsl:call-template name="OutputFrontOrBackMatterTitle">
                    <xsl:with-param name="id">
                        <xsl:call-template name="GetIdToUse">
                            <xsl:with-param name="sBaseId" select="$sAcknowledgementsID"/>
                        </xsl:call-template>
                    </xsl:with-param>
                    <xsl:with-param name="sTitle">
                        <xsl:call-template name="OutputAcknowledgementsLabel"/>
                    </xsl:with-param>
                    <xsl:with-param name="bIsBook" select="$bIsBook"/>
                    <xsl:with-param name="bForcePageBreak" select="$bForcePageBreak"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="OutputFrontOrBackMatterTitle">
                    <xsl:with-param name="id">
                        <xsl:call-template name="GetIdToUse">
                            <xsl:with-param name="sBaseId">
                                <xsl:call-template name="CreatePrefaceID"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:with-param>
                    <xsl:with-param name="sTitle">
                        <xsl:call-template name="OutputPrefaceLabel"/>
                    </xsl:with-param>
                    <xsl:with-param name="bIsBook" select="$bIsBook"/>
                    <xsl:with-param name="bForcePageBreak" select="$bForcePageBreak"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:apply-templates/>
        <xsl:if test="@showinlandscapemode='yes'">
            <xsl:if test="contains(@XeLaTeXSpecial,'fix-final-landscape')">
                <tex:cmd name="XLingPaperendtableofcontents" gr="0"/>
            </xsl:if>
            <tex:cmd name="endlandscape" gr="0" nl2="1"/>
        </xsl:if>
    </xsl:template>
    <!--
        DoAnnotation
    -->
    <xsl:template name="DoAnnotation">
        <xsl:param name="sAnnotation"/>
        <tex:cmd name="vspace">
            <tex:parm>
                <xsl:text>3pt</xsl:text>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="noindent"/>
        <xsl:apply-templates select="key('AnnotationID',$sAnnotation)"/>
        <tex:cmd name="par"/>
        <tex:cmd name="vspace">
            <tex:parm>
                <xsl:text>3pt</xsl:text>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--
        DoBook
    -->
    <xsl:template name="DoBook">
        <xsl:param name="book"/>
        <xsl:param name="pages"/>
        <xsl:for-each select="$book">
            <xsl:variable name="sTitle" select="normalize-space(../refTitle)"/>
            <xsl:if test="string-length($sTitle) &gt; 0">
                <tex:cmd name="textit">
                    <tex:parm>
                        <xsl:apply-templates select="../refTitle"/>
                    </tex:parm>
                </tex:cmd>
                <xsl:text>.  </xsl:text>
            </xsl:if>
            <xsl:if test="../../@showAuthorName='no'">
                <xsl:for-each select="..">
                    <xsl:call-template name="DoDate">
                        <xsl:with-param name="works" select="exsl:node-set($book)/.."/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:if>
            <xsl:if test="translatedBy">
                <xsl:text>Translated by </xsl:text>
                <xsl:apply-templates select="translatedBy"/>
                <xsl:call-template name="OutputPeriodIfNeeded">
                    <xsl:with-param name="sText" select="translatedBy"/>
                </xsl:call-template>
                <xsl:text>&#x20;</xsl:text>
            </xsl:if>
            <xsl:if test="editor">
                <xsl:apply-templates select="editor"/>
                <xsl:call-template name="OutputPeriodIfNeeded">
                    <xsl:with-param name="sText" select="editor"/>
                </xsl:call-template>
                <xsl:text>&#x20;</xsl:text>
            </xsl:if>
            <xsl:if test="edition">
                <xsl:apply-templates select="edition"/>
                <xsl:call-template name="OutputPeriodIfNeeded">
                    <xsl:with-param name="sText" select="edition"/>
                </xsl:call-template>
                <xsl:text>&#x20;</xsl:text>
            </xsl:if>
            <xsl:if test="seriesEd">
                <xsl:apply-templates select="seriesEd"/>
                <xsl:call-template name="OutputPeriodIfNeeded">
                    <xsl:with-param name="sText" select="seriesEd"/>
                </xsl:call-template>
                <xsl:text>&#x20;</xsl:text>
            </xsl:if>
            <xsl:if test="series">
                <tex:cmd name="textit">
                    <tex:parm>
                        <xsl:apply-templates select="series"/>
                    </tex:parm>
                </tex:cmd>
                <xsl:if test="not(bVol)">
                    <xsl:call-template name="OutputPeriodIfNeeded">
                        <xsl:with-param name="sText" select="series"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:text>&#x20;</xsl:text>
            </xsl:if>
            <xsl:variable name="sPages" select="normalize-space($pages)"/>
            <xsl:choose>
                <xsl:when test="bVol">
                    <xsl:value-of select="normalize-space(bVol)"/>
                    <xsl:if test="string-length($sPages) &gt; 0">
                        <xsl:text>:</xsl:text>
                        <xsl:value-of select="$pages"/>
                    </xsl:if>
                    <xsl:call-template name="OutputPeriodIfNeeded">
                        <xsl:with-param name="sText" select="bVol"/>
                    </xsl:call-template>
                    <xsl:text>&#x20;</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:if test="string-length($sPages) &gt; 0">
                        <xsl:value-of select="$sPages"/>
                        <xsl:text>. </xsl:text>
                    </xsl:if>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:if test="multivolumeWork">
                <tex:cmd name="textit">
                    <tex:parm>
                        <xsl:apply-templates select="multivolumeWork"/>
                    </tex:parm>
                </tex:cmd>
                <xsl:text>.&#x20;</xsl:text>
            </xsl:if>
            <xsl:choose>
                <xsl:when test="location and publisher">
                    <xsl:apply-templates select="location"/>
                    <xsl:text>: </xsl:text>
                    <xsl:apply-templates select="publisher"/>
                    <xsl:call-template name="OutputPeriodIfNeeded">
                        <xsl:with-param name="sText" select="publisher"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:when test="location">
                    <xsl:apply-templates select="location"/>
                    <xsl:call-template name="OutputPeriodIfNeeded">
                        <xsl:with-param name="sText" select="location"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:when test="publisher">
                    <xsl:apply-templates select="publisher"/>
                    <xsl:call-template name="OutputPeriodIfNeeded">
                        <xsl:with-param name="sText" select="publisher"/>
                    </xsl:call-template>
                </xsl:when>
            </xsl:choose>
            <xsl:call-template name="DoReprintInfo">
                <xsl:with-param name="reprintInfo" select="reprintInfo"/>
            </xsl:call-template>
            <xsl:call-template name="DoRefUrlEtc">
                <xsl:with-param name="path" select="."/>
            </xsl:call-template>
        </xsl:for-each>
    </xsl:template>
    <!--
        DoContents
    -->
    <xsl:template name="DoContents">
        <xsl:param name="bIsBook" select="'Y'"/>
        <xsl:if test="not(ancestor::chapterInCollection)">
            <tex:cmd name="XLingPapertableofcontents" gr="0" nl2="0"/>
        </xsl:if>
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:choose>
            <xsl:when test="$bIsBook='Y'">
                <xsl:call-template name="OutputFrontOrBackMatterTitle">
                    <xsl:with-param name="id" select="'rXLingPapContents'"/>
                    <xsl:with-param name="sTitle">
                        <xsl:call-template name="OutputContentsLabel"/>
                    </xsl:with-param>
                    <xsl:with-param name="bIsBook" select="'Y'"/>
                    <xsl:with-param name="bForcePageBreak">
                        <xsl:choose>
                            <xsl:when test="ancestor::chapterInCollection">
                                <xsl:text>N</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>Y</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="OutputFrontOrBackMatterTitle">
                    <xsl:with-param name="id" select="'rXLingPapContents'"/>
                    <xsl:with-param name="sTitle">
                        <xsl:call-template name="OutputContentsLabel"/>
                    </xsl:with-param>
                    <xsl:with-param name="bIsBook" select="'N'"/>
                    <xsl:with-param name="bForcePageBreak" select="'N'"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:variable name="nLevel">
            <xsl:value-of select="number(@showLevel)"/>
        </xsl:variable>
        <xsl:if test="//keywordsShownHere[@showincontents='yes' and parent::frontMatter][not(ancestor::chapterInCollection)]">
            <xsl:for-each select="//keywordsShownHere[@showincontents='yes' and parent::frontMatter][not(ancestor::chapterInCollection)]">
                <xsl:call-template name="OutputTOCLine">
                    <xsl:with-param name="sLink">
                        <xsl:value-of select="$sKeywordsInFrontMatterID"/>
                    </xsl:with-param>
                    <xsl:with-param name="sLabel">
                        <xsl:call-template name="OutputKeywordsLabel"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>
        </xsl:if>
        <!-- acknowledgements -->
        <xsl:if test="//frontMatter/acknowledgements[not(ancestor::chapterInCollection)]">
            <xsl:for-each select="//frontMatter/acknowledgements[not(ancestor::chapterInCollection)]">
                <xsl:call-template name="OutputTOCLine">
                    <xsl:with-param name="sLink">
                        <xsl:value-of select="$sAcknowledgementsID"/>
                    </xsl:with-param>
                    <xsl:with-param name="sLabel">
                        <xsl:call-template name="OutputAcknowledgementsLabel"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>
        </xsl:if>
        <!-- abstract -->
        <xsl:for-each select="//abstract[not(ancestor::chapterInCollection)]">
            <xsl:call-template name="OutputTOCLine">
                <xsl:with-param name="sLink" select="concat($sAbstractID,count(preceding-sibling::abstract))"/>
                <xsl:with-param name="sLabel">
                    <xsl:call-template name="OutputAbstractLabel"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:for-each>
        <!-- preface -->
        <xsl:for-each select="//preface[not(ancestor::chapterInCollection)]">
            <xsl:call-template name="OutputTOCLine">
                <xsl:with-param name="sLink">
                    <xsl:call-template name="CreatePrefaceID"/>
                </xsl:with-param>
                <xsl:with-param name="sLabel">
                    <xsl:call-template name="OutputPrefaceLabel"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:for-each>
        <!-- part -->
        <xsl:if test="$parts">
            <xsl:for-each select="$parts">
                <xsl:variable name="part" select="."/>
                <xsl:if test="position()=1">
                    <xsl:for-each select="preceding-sibling::*[name()='chapterBeforePart']">
                        <xsl:call-template name="OutputAllChapterTOC">
                            <xsl:with-param name="nLevel">
                                <xsl:value-of select="$nLevel"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:for-each>
                </xsl:if>
                <xsl:call-template name="OutputTOCLine">
                    <xsl:with-param name="sLink" select="@id"/>
                    <xsl:with-param name="sLabel">
                        <xsl:call-template name="OutputPartLabel"/>
                        <xsl:text>&#x20;</xsl:text>
                        <xsl:apply-templates select="." mode="numberPart"/>
                        <xsl:text>&#xa0;</xsl:text>
                        <xsl:apply-templates select="secTitle"/>
                    </xsl:with-param>
                </xsl:call-template>
                <xsl:for-each select="exsl:node-set($chapters)[ancestor::part[.=$part]]">
                    <xsl:call-template name="OutputAllChapterTOC">
                        <xsl:with-param name="nLevel">
                            <xsl:value-of select="$nLevel"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:for-each>
        </xsl:if>
        <!-- chapter, no parts -->
        <xsl:if test="not($parts) and $chapters">
            <xsl:for-each select="$chapters">
                <xsl:call-template name="OutputAllChapterTOC">
                    <xsl:with-param name="nLevel">
                        <xsl:value-of select="$nLevel"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>
        </xsl:if>
        <!-- section, no chapters -->
        <xsl:if test="not($parts) and not($chapters)">
            <xsl:call-template name="OutputAllSectionTOC">
                <xsl:with-param name="nLevel">
                    <xsl:value-of select="$nLevel"/>
                </xsl:with-param>
                <xsl:with-param name="nodesSection1" select="//section1[not(parent::appendix)]"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:for-each select="//appendix[not(ancestor::chapterInCollection)]">
            <xsl:call-template name="OutputAllChapterTOC">
                <xsl:with-param name="nLevel">
                    <xsl:value-of select="$nLevel"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:for-each>
        <xsl:for-each select="//glossary[not(ancestor::chapterInCollection)]">
            <xsl:call-template name="OutputTOCLine">
                <xsl:with-param name="sLink">
                    <xsl:call-template name="CreateGlossaryID"/>
                </xsl:with-param>
                <xsl:with-param name="sLabel">
                    <xsl:call-template name="OutputGlossaryLabel"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:for-each>
        <!-- acknowledgements -->
        <xsl:if test="//backMatter/acknowledgements[not(ancestor::chapterInCollection)]">
            <xsl:call-template name="OutputTOCLine">
                <xsl:with-param name="sLink">
                    <xsl:value-of select="$sAcknowledgementsID"/>
                </xsl:with-param>
                <xsl:with-param name="sLabel">
                    <xsl:call-template name="OutputAcknowledgementsLabel"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:if>
        <xsl:if test="//references[not(ancestor::chapterInCollection)] and //citation[not(ancestor::chapterInCollection/backMatter/references)]">
            <xsl:for-each select="exsl:node-set($lingPaper)/backMatter/references">
                <xsl:call-template name="OutputTOCLine">
                    <xsl:with-param name="sLink" select="$sReferencesID"/>
                    <xsl:with-param name="sLabel">
                        <xsl:for-each select="//references[not(ancestor::chapterInCollection)]">
                            <xsl:call-template name="OutputReferencesLabel"/>
                        </xsl:for-each>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>
        </xsl:if>
        <xsl:if test="//keywordsShownHere[@showincontents='yes' and parent::backMatter and not(ancestor::chapterInCollection)]">
            <xsl:for-each select="//keywordsShownHere[@showincontents='yes' and parent::backMatter and not(ancestor::chapterInCollection)]">
                <xsl:call-template name="OutputTOCLine">
                    <xsl:with-param name="sLink" select="$sKeywordsInBackMatterID"/>
                    <xsl:with-param name="sLabel">
                        <xsl:for-each select="//keywordsShownHere[parent::backMatter and not(ancestor::chapterInCollection)]">
                            <xsl:call-template name="OutputKeywordsLabel"/>
                        </xsl:for-each>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>
        </xsl:if>
        <xsl:for-each select="//index">
            <xsl:call-template name="OutputTOCLine">
                <xsl:with-param name="sLink">
                    <xsl:call-template name="CreateIndexID"/>
                </xsl:with-param>
                <xsl:with-param name="sLabel">
                    <xsl:call-template name="OutputIndexLabel"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:for-each>
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="endlandscape" gr="0" nl2="1"/>
        </xsl:if>
    </xsl:template>
    <!--
        DoContentsInChapterInCollection
    -->
    <xsl:template name="DoContentsInChapterInCollection">
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:call-template name="OutputFrontOrBackMatterTitle">
            <xsl:with-param name="id">
                <xsl:call-template name="GetIdToUse">
                    <xsl:with-param name="sBaseId" select="$sContentsID"/>
                </xsl:call-template>
            </xsl:with-param>
            <xsl:with-param name="sTitle">
                <xsl:call-template name="OutputContentsLabel"/>
            </xsl:with-param>
            <xsl:with-param name="bIsBook" select="'N'"/>
            <xsl:with-param name="bForcePageBreak" select="'N'"/>
        </xsl:call-template>
        <xsl:variable name="nLevel">
            <xsl:value-of select="number(@showLevel)"/>
        </xsl:variable>
        <xsl:for-each select="ancestor::chapterInCollection">
            <xsl:if test="frontMatter/abstract  or frontMatter/acknowledgements or frontMatter/preface">
                <tex:cmd name="settowidth">
                    <tex:parm>
                        <tex:cmd name="leveloneindent" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <xsl:text>1</xsl:text>
                        <tex:spec cat="esc"/>
                        <xsl:text>&#x20;</xsl:text>
                    </tex:parm>
                </tex:cmd>
                <xsl:apply-templates select="frontMatter/abstract | frontMatter/acknowledgements | frontMatter/preface" mode="contents"/>
            </xsl:if>
            <xsl:call-template name="OutputAllSectionTOC">
                <xsl:with-param name="nLevel">
                    <xsl:value-of select="$nLevel"/>
                </xsl:with-param>
                <xsl:with-param name="nodesSection1" select="section1[not(parent::appendix)]"/>
            </xsl:call-template>
            <xsl:call-template name="OutputChapterInCollectionBackMatterContents">
                <xsl:with-param name="nLevel" select="$nLevel"/>
            </xsl:call-template>
        </xsl:for-each>
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="endlandscape" gr="0" nl2="1"/>
        </xsl:if>
        <tex:cmd name="vspace">
            <tex:parm>
                <tex:cmd name="baselineskip" gr="0"/>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        DoDebugExamples
    -->
    <xsl:template name="DoDebugExamples">
        <xsl:if test="$bDoDebug='y'">
            <xsl:attribute name="border">solid 1pt gray</xsl:attribute>
            <xsl:attribute name="border-collapse">collapse</xsl:attribute>
        </xsl:if>
    </xsl:template>
    <!--  
        DoDebugFooter
    -->
    <xsl:template name="DoDebugFooter">
        <xsl:if test="$bDoDebug='y'">
            <xsl:attribute name="border">
                <xsl:text>thin solid blue</xsl:text>
            </xsl:attribute>
        </xsl:if>
    </xsl:template>
    <!--  
        DoDebugFrontMatterBody
    -->
    <xsl:template name="DoDebugFrontMatterBody">
        <xsl:if test="$bDoDebug='y'">
            <xsl:attribute name="border">
                <xsl:text>thick solid green</xsl:text>
            </xsl:attribute>
        </xsl:if>
    </xsl:template>
    <!--  
        DoDebugHeader
    -->
    <xsl:template name="DoDebugHeader">
        <xsl:if test="$bDoDebug='y'">
            <xsl:attribute name="border">
                <xsl:text>thin solid red</xsl:text>
            </xsl:attribute>
        </xsl:if>
    </xsl:template>
    <!--  
        DoFigure
    -->
    <xsl:template name="DoFigure">
        <xsl:if test="contains(@XeLaTeXSpecial,'clearpage')">
            <tex:cmd name="clearpage" gr="0" nl2="0"/>
        </xsl:if>
        <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak')">
            <tex:cmd name="pagebreak" gr="0" nl2="0"/>
        </xsl:if>
        <xsl:call-template name="DoInternalTargetBegin">
            <xsl:with-param name="sName" select="@id"/>
        </xsl:call-template>
        <xsl:call-template name="DoInternalTargetEnd"/>
        <xsl:call-template name="CreateAddToContents">
            <xsl:with-param name="id" select="@id"/>
        </xsl:call-template>
        <xsl:if test="caption and descendant::img">
            <tex:cmd name="setbox0" gr="0"/>
            <xsl:text>=</xsl:text>
            <tex:cmd name="vbox" gr="0"/>
            <!--            \setbox0=\vbox{-->
        </xsl:if>
        <tex:spec cat="bg"/>
        <tex:spec cat="esc"/>
        <xsl:text>protect</xsl:text>
        <xsl:choose>
            <xsl:when test="@align='center'">
                <tex:spec cat="esc"/>
                <xsl:text>centering </xsl:text>
            </xsl:when>
            <xsl:when test="@align='right'">
                <tex:spec cat="esc"/>
                <xsl:text>raggedleft</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <tex:spec cat="esc"/>
                <xsl:text>raggedright</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="DoType">
            <xsl:with-param name="type" select="@type"/>
        </xsl:call-template>
        <xsl:if test="exsl:node-set($lingPaper)/@figureLabelAndCaptionLocation='before'">
            <tex:cmd name="XLingPaperneedspace">
                <tex:parm>
                    <xsl:text>3</xsl:text>
                    <tex:cmd name="baselineskip" gr="0"/>
                </tex:parm>
            </tex:cmd>
            <xsl:call-template name="OutputFigureLabelAndCaption"/>
            <tex:spec cat="esc"/>
            <tex:spec cat="esc"/>
            <tex:spec cat="lsb"/>
            <xsl:text>.3em</xsl:text>
            <tex:spec cat="rsb"/>
            <xsl:call-template name="HandleEndnotesInCaptionOfFigure"/>
        </xsl:if>
        <tex:cmd name="leavevmode" gr="0" nl2="1"/>
        <xsl:apply-templates select="*[name()!='caption' and name()!='shortCaption']"/>
        <xsl:if test="exsl:node-set($lingPaper)/@figureLabelAndCaptionLocation='before'">
            <xsl:if test="chart/*[position()=last()][name()='img']">
                <tex:spec cat="esc"/>
                <tex:spec cat="esc"/>
            </xsl:if>
        </xsl:if>
        <xsl:call-template name="DoTypeEnd">
            <xsl:with-param name="type" select="@type"/>
        </xsl:call-template>
        <xsl:if test="exsl:node-set($lingPaper)/@figureLabelAndCaptionLocation='after'">
            <xsl:for-each select="chart/*">
                <xsl:if test="position()=last() and name()='img'">
                    <tex:spec cat="esc"/>
                    <tex:spec cat="esc"/>
                </xsl:if>
            </xsl:for-each>
            <tex:cmd name="vspace">
                <tex:parm>.3em</tex:parm>
            </tex:cmd>
            <xsl:call-template name="OutputFigureLabelAndCaption"/>
            <tex:spec cat="esc"/>
            <tex:spec cat="esc"/>
            <xsl:call-template name="HandleEndnotesInCaptionOfFigure"/>
        </xsl:if>
        <tex:spec cat="eg"/>
        <xsl:if test="caption and descendant::img">
            <tex:cmd name="box0" gr="0"/>
            <xsl:for-each select="caption/endnote">
                <xsl:call-template name="DoEndnote">
                    <xsl:with-param name="sTeXFootnoteKind" select="'footnotetext'"/>
                </xsl:call-template>
            </xsl:for-each>
            <tex:cmd name="par"/>
            <!-- \box0\par -->
        </xsl:if>
    </xsl:template>
    <!--  
        DoFootnoteTextAfterFree
    -->
    <xsl:template name="DoFootnoteTextAfterFree">
        <xsl:param name="originalContext"/>
        <xsl:for-each select="descendant-or-self::endnote">
            <xsl:apply-templates select=".">
                <xsl:with-param name="sTeXFootnoteKind" select="'footnotetext'"/>
                <xsl:with-param name="originalContext" select="$originalContext"/>
            </xsl:apply-templates>
        </xsl:for-each>
    </xsl:template>
    <!--  
        DoFootnoteTextAtEndOfInLineGroup
    -->
    <xsl:template name="DoFootnoteTextAtEndOfInLineGroup">
        <xsl:param name="originalContext"/>
        <xsl:call-template name="HandleFootnoteTextInLineGroup">
            <xsl:with-param name="originalContext" select="$originalContext"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        DoFootnoteTextWithinWrappableWrd
    -->
    <xsl:template name="DoFootnoteTextWithinWrappableWrd">
        <xsl:param name="originalContext"/>
        <xsl:for-each select="descendant-or-self::endnote">
            <xsl:apply-templates select=".">
                <xsl:with-param name="sTeXFootnoteKind" select="'footnotetext'"/>
                <xsl:with-param name="originalContext" select="$originalContext"/>
            </xsl:apply-templates>
        </xsl:for-each>
    </xsl:template>
    <!--  
        DoGlossary
    -->
    <xsl:template name="DoGlossary">
        <xsl:param name="bIsBook" select="'N'"/>
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:call-template name="OutputFrontOrBackMatterTitle">
            <xsl:with-param name="id">
                <xsl:call-template name="CreateGlossaryID"/>
            </xsl:with-param>
            <xsl:with-param name="sTitle">
                <xsl:call-template name="OutputGlossaryLabel"/>
            </xsl:with-param>
            <xsl:with-param name="bIsBook" select="$bIsBook"/>
            <xsl:with-param name="bForcePageBreak">
                <xsl:choose>
                    <xsl:when test="$bIsBook!='Y' or ancestor::chapterInCollection">
                        <xsl:text>N</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>Y</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:with-param>
        </xsl:call-template>
        <xsl:apply-templates/>
        <xsl:if test="@showinlandscapemode='yes'">
            <xsl:if test="contains(@XeLaTeXSpecial,'fix-final-landscape')">
                <tex:cmd name="XLingPaperendtableofcontents" gr="0"/>
            </xsl:if>
            <tex:cmd name="endlandscape" gr="0" nl2="1"/>
        </xsl:if>
    </xsl:template>
    <!--  
        DoIndex
    -->
    <xsl:template name="DoIndex">
        <xsl:call-template name="OutputFrontOrBackMatterTitle">
            <xsl:with-param name="id">
                <xsl:call-template name="CreateIndexID"/>
            </xsl:with-param>
            <xsl:with-param name="sTitle">
                <xsl:call-template name="OutputIndexLabel"/>
            </xsl:with-param>
            <xsl:with-param name="bIsBook">
                <xsl:choose>
                    <xsl:when test="$chapters">Y</xsl:when>
                    <xsl:otherwise>N</xsl:otherwise>
                </xsl:choose>
            </xsl:with-param>
            <xsl:with-param name="bForcePageBreak">
                <xsl:choose>
                    <xsl:when test="not($chapters) or ancestor::chapterInCollection">
                        <xsl:text>N</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>Y</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:with-param>
            <xsl:with-param name="bDoTwoColumns" select="'Y'"/>
        </xsl:call-template>
        <!-- process any paragraphs, etc. that may be at the beginning -->
        <xsl:apply-templates/>
        <xsl:text>&#x0a;</xsl:text>
        <xsl:if test="$chapters">
            <!-- close off all non-two column initial material; the \twocolumn[span stuff] command needs to end here -->
            <tex:spec cat="rsb"/>
        </xsl:if>
        <!-- now process the contents of this index -->
        <xsl:variable name="sIndexKind">
            <xsl:choose>
                <xsl:when test="@kind">
                    <xsl:value-of select="@kind"/>
                </xsl:when>
                <xsl:otherwise>common</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:call-template name="OutputIndexTerms">
            <xsl:with-param name="sIndexKind" select="$sIndexKind"/>
            <xsl:with-param name="lang" select="$indexLang"/>
            <xsl:with-param name="terms" select="//lingPaper/indexTerms"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        DoInterlinearRefCitation
    -->
    <xsl:template name="DoInterlinearRefCitation">
        <xsl:param name="sRef"/>
        <tex:group>
            <xsl:call-template name="DoInterlinearTextReferenceLinkBegin">
                <xsl:with-param name="sName" select="$sRef"/>
            </xsl:call-template>
            <!--            <xsl:call-template name="AddAnyLinkAttributes"/>-->
            <!--            <xsl:variable name="interlinear" select="key('InterlinearReferenceID',$sRef)"/>
                <xsl:if test="not(@lineNumberOnly) or @lineNumberOnly!='yes'">
                <xsl:value-of select="exsl:node-set($interlinear)/../textInfo/shortTitle"/>
                <xsl:text>:</xsl:text>
                </xsl:if>
                <xsl:value-of select="count(exsl:node-set($interlinear)/preceding-sibling::interlinear) + 1"/>
            -->
            <xsl:call-template name="DoInterlinearRefCitationContent">
                <xsl:with-param name="sRef" select="$sRef"/>
            </xsl:call-template>
            <xsl:call-template name="DoInternalHyperlinkEnd"/>
        </tex:group>
    </xsl:template>
    <!--  
        DoReferences
    -->
    <xsl:template name="DoReferences">
        <xsl:param name="bIsBook" select="'N'"/>
        <xsl:variable name="gtAuthors" select="//refAuthor[refWork/@id=//citation[ancestor::glossaryTerm[key('GlossaryTermRefs',@id)]]/@ref]"/>
        <xsl:variable name="otherAuthors" select="//refAuthor[refWork/@id=//citation[not(ancestor::comment) and not(ancestor::annotation) and not(ancestor::glossaryTerm)]/@ref]"/>
        <xsl:variable name="authors" select="$otherAuthors | $gtAuthors"/>
        <xsl:if test="$authors">
            <xsl:if test="@showinlandscapemode='yes'">
                <tex:cmd name="landscape" gr="0" nl2="1"/>
            </xsl:if>
            <xsl:call-template name="OutputFrontOrBackMatterTitle">
                <xsl:with-param name="id">
                    <xsl:call-template name="GetIdToUse">
                        <xsl:with-param name="sBaseId" select="$sReferencesID"/>
                    </xsl:call-template>
                </xsl:with-param>
                <xsl:with-param name="sTitle">
                    <xsl:call-template name="OutputReferencesLabel"/>
                </xsl:with-param>
                <xsl:with-param name="bIsBook" select="$bIsBook"/>
                <xsl:with-param name="bForcePageBreak">
                    <xsl:choose>
                        <xsl:when test="$bIsBook!='Y' or ancestor::chapterInCollection">
                            <xsl:text>N</xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>Y</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:with-param>
            </xsl:call-template>
            <!--<tex:env name="description" nlb1="0" nle1="1">
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
                </xsl:call-template>-->
            <tex:cmd name="raggedright" gr="0" nl2="1"/>
            <xsl:call-template name="HandleRefAuthors"/>
            <xsl:if test="@showinlandscapemode='yes'">
                <xsl:if test="contains(@XeLaTeXSpecial,'fix-final-landscape')">
                    <tex:cmd name="XLingPaperendtableofcontents" gr="0"/>
                </xsl:if>
                <tex:cmd name="endlandscape" gr="0" nl2="1"/>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        DoRefCitation
    -->
    <xsl:template name="DoRefCitation">
        <xsl:param name="citation"/>
        <xsl:for-each select="$citation">
            <xsl:variable name="refer" select="id(@refToBook)"/>
            <xsl:call-template name="DoInternalHyperlinkBegin">
                <xsl:with-param name="sName" select="@refToBook"/>
            </xsl:call-template>
            <xsl:value-of select="exsl:node-set($refer)/../@citename"/>
            <xsl:text>,&#x20;</xsl:text>
            <xsl:value-of select="exsl:node-set($refer)/authorRole"/>
            <xsl:text>, </xsl:text>
            <xsl:variable name="sPage" select="normalize-space(@page)"/>
            <xsl:if test="string-length($sPage) &gt; 0">
                <xsl:text>&#x20;</xsl:text>
                <xsl:value-of select="$sPage"/>
            </xsl:if>
            <xsl:text>.</xsl:text>
            <xsl:call-template name="DoExternalHyperRefEnd"/>
        </xsl:for-each>
    </xsl:template>
    <!--  
        DoRefUrlEtc
    -->
    <xsl:template name="DoRefUrlEtc">
        <xsl:param name="path"/>
        <xsl:if test="exsl:node-set($path)/url">
            <xsl:text> (</xsl:text>
            <xsl:call-template name="AddAnyLinkAttributes"/>
            <xsl:call-template name="DoExternalHyperRefBegin">
                <xsl:with-param name="sName" select="normalize-space(translate(exsl:node-set($path)/url,$sStripFromUrl,''))"/>
            </xsl:call-template>
            <xsl:value-of select="normalize-space(exsl:node-set($path)/url)"/>
            <xsl:call-template name="DoExternalHyperRefEnd"/>
            <xsl:text>)</xsl:text>
            <xsl:if test="exsl:node-set($path)/dateAccessed">
                <xsl:text>  (accessed </xsl:text>
                <xsl:value-of select="normalize-space(exsl:node-set($path)/dateAccessed)"/>
                <xsl:text>)</xsl:text>
            </xsl:if>
            <xsl:text>.</xsl:text>
        </xsl:if>
        <xsl:if test="exsl:node-set($lingPaper)/@showiso639-3codeininterlinear='yes' or ancestor-or-self::refWork/@showiso639-3codes='yes'">
            <xsl:for-each select="exsl:node-set($path)/iso639-3code">
                <xsl:sort/>
                <tex:cmd name="small">
                    <tex:parm>
                        <xsl:if test="position() = 1">
                            <xsl:text>  [</xsl:text>
                        </xsl:if>
                        <xsl:choose>
                            <xsl:when test="$bShowISO639-3Codes='Y'">
                                <xsl:variable name="sThisCode" select="."/>
                                <xsl:call-template name="DoInternalHyperlinkBegin">
                                    <xsl:with-param name="sName" select="exsl:node-set($languages)[@ISO639-3Code=$sThisCode]/@id"/>
                                </xsl:call-template>
                                <xsl:value-of select="."/>
                                <xsl:call-template name="DoInternalHyperlinkEnd"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="."/>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:if test="position() != last()">
                            <xsl:text>, </xsl:text>
                        </xsl:if>
                        <xsl:if test="position() = last()">
                            <xsl:text>]</xsl:text>
                        </xsl:if>
                    </tex:parm>
                </tex:cmd>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <!--  
        DoRefWork
    -->
    <xsl:template name="DoRefWork">
        <xsl:param name="works"/>
        <xsl:param name="sortedWorks"/>
        <xsl:param name="bDoTarget" select="'Y'"/>
        <xsl:if test="$bDoTarget='Y'">
            <xsl:call-template name="DoInternalTargetBegin">
                <xsl:with-param name="sName" select="@id"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:if test="../@showAuthorName!='no'">
            <xsl:variable name="author">
                <xsl:value-of select="normalize-space(../@name)"/>
            </xsl:variable>
            <xsl:value-of select="$author"/>
            <xsl:if test="substring($author,string-length($author),string-length($author))!='.'">.</xsl:if>
            <xsl:text>&#x20;  </xsl:text>
            <xsl:if test="authorRole">
                <xsl:value-of select="authorRole"/>
                <xsl:text>.  </xsl:text>
            </xsl:if>
            <xsl:call-template name="DoDate">
                <xsl:with-param name="works" select="$works"/>
                <xsl:with-param name="sortedWorks" select="$sortedWorks"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:if test="$bDoTarget='Y'">
            <xsl:call-template name="DoInternalTargetEnd"/>
        </xsl:if>
        <!--
            book
        -->
        <xsl:if test="book">
            <xsl:call-template name="DoBook">
                <xsl:with-param name="book" select="book"/>
            </xsl:call-template>
        </xsl:if>
        <!--
            collection
        -->
        <xsl:if test="collection">
            <xsl:variable name="sTitle" select="normalize-space(refTitle)"/>
            <xsl:if test="string-length($sTitle) &gt; 0">
                <xsl:apply-templates select="refTitle"/>
                <xsl:text>.</xsl:text>
            </xsl:if>
            <xsl:if test="../@showAuthorName='no'">
                <xsl:call-template name="DoDate">
                    <xsl:with-param name="works" select="$works"/>
                </xsl:call-template>
            </xsl:if>
            <xsl:text> In </xsl:text>
            <xsl:choose>
                <xsl:when test="collection/collCitation">
                    <xsl:variable name="citation" select="collection/collCitation"/>
                    <xsl:choose>
                        <xsl:when test="saxon:node-set($collOrProcVolumesToInclude)/refWork[@id=exsl:node-set($citation)/@refToBook]">
                            <xsl:call-template name="DoRefCitation">
                                <xsl:with-param name="citation" select="$citation"/>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="FleshOutRefCitation">
                                <xsl:with-param name="citation" select="$citation"/>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="DoEdPlural">
                        <xsl:with-param name="editor" select="collection/collEd"/>
                    </xsl:call-template>
                    <xsl:text>&#x20;</xsl:text>
                    <tex:cmd name="textit">
                        <tex:parm>
                            <xsl:apply-templates select="collection/collTitle"/>
                        </tex:parm>
                    </tex:cmd>
                    <xsl:text>.</xsl:text>
                    <xsl:call-template name="DoCollectionEdition"/>
                    <xsl:choose>
                        <xsl:when test="collection/collVol">
                            <xsl:text>&#x20;</xsl:text>
                            <xsl:value-of select="normalize-space(collection/collVol)"/>
                            <xsl:text>:</xsl:text>
                            <xsl:value-of select="normalize-space(collection/collPages)"/>
                            <xsl:text>. </xsl:text>
                        </xsl:when>
                        <xsl:when test="collection/collPages">
                            <xsl:if test="collection/collVol">
                                <xsl:text>,</xsl:text>
                            </xsl:if>
                            <xsl:text>&#x20;</xsl:text>
                            <xsl:value-of select="normalize-space(collection/collPages)"/>
                            <xsl:text>. </xsl:text>
                        </xsl:when>
                        <!--                                    <xsl:otherwise>
                            <xsl:text>.</xsl:text>
                            </xsl:otherwise>
                        -->
                    </xsl:choose>
                    <xsl:if test="collection/seriesEd">
                        <xsl:call-template name="DoEdPlural">
                            <xsl:with-param name="editor" select="collection/seriesEd"/>
                        </xsl:call-template>
                        <xsl:text>&#x20;</xsl:text>
                    </xsl:if>
                    <xsl:if test="collection/series">
                        <tex:cmd name="textit">
                            <tex:parm>
                                <xsl:apply-templates select="collection/series"/>
                            </tex:parm>
                        </tex:cmd>
                        <xsl:choose>
                            <xsl:when test="collection/bVol">
                                <xsl:text>&#x20;</xsl:text>
                                <xsl:apply-templates select="collection/bVol"/>
                                <xsl:text>. </xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="OutputPeriodIfNeeded">
                                    <xsl:with-param name="sText" select="collection/series"/>
                                </xsl:call-template>
                                <xsl:text>&#x20;</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:if>
                    <xsl:if test="collection/multivolumeWork">
                        <tex:cmd name="textit">
                            <tex:parm>
                                <xsl:apply-templates select="collection/multivolumeWork"/>
                            </tex:parm>
                        </tex:cmd>
                        <xsl:text>.&#x20;</xsl:text>
                    </xsl:if>
                    <xsl:choose>
                        <xsl:when test="collection/location">
                            <xsl:text>&#x20;</xsl:text>
                            <xsl:apply-templates select="collection/location"/>
                            <xsl:text>: </xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>&#x20;</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                    <xsl:if test="collection/publisher">
                        <xsl:apply-templates select="collection/publisher"/>
                        <xsl:call-template name="OutputPeriodIfNeeded">
                            <xsl:with-param name="sText" select="collection/publisher"/>
                        </xsl:call-template>
                    </xsl:if>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="DoReprintInfo">
                <xsl:with-param name="reprintInfo" select="collection/reprintInfo"/>
            </xsl:call-template>
            <xsl:call-template name="DoRefUrlEtc">
                <xsl:with-param name="path" select="collection"/>
            </xsl:call-template>
        </xsl:if>
        <!--
            dissertation
        -->
        <xsl:if test="dissertation">
            <xsl:variable name="sTitle" select="normalize-space(refTitle)"/>
            <xsl:if test="string-length($sTitle) &gt; 0">
                <tex:cmd name="textit">
                    <tex:parm>
                        <xsl:apply-templates select="refTitle"/>
                    </tex:parm>
                </tex:cmd>
                <xsl:text>.  </xsl:text>
            </xsl:if>
            <xsl:call-template name="OutputLabel">
                <xsl:with-param name="sDefault" select="$sPhDDissertationDefaultLabel"/>
                <xsl:with-param name="pLabel">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(dissertation/@labelDissertation)) &gt; 0">
                            <xsl:value-of select="dissertation/@labelDissertation"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="//references/@labelDissertation"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:with-param>
            </xsl:call-template>
            <xsl:text>. </xsl:text>
            <xsl:if test="../@showAuthorName='no'">
                <xsl:call-template name="DoDate">
                    <xsl:with-param name="works" select="$works"/>
                </xsl:call-template>
            </xsl:if>
            <xsl:if test="dissertation/location">
                <xsl:text> (</xsl:text>
                <xsl:apply-templates select="dissertation/location"/>
                <xsl:text>).  </xsl:text>
            </xsl:if>
            <xsl:apply-templates select="dissertation/institution"/>
            <xsl:text>.</xsl:text>
            <xsl:if test="dissertation/published">
                <xsl:text>  Published by </xsl:text>
                <xsl:apply-templates select="dissertation/published/location"/>
                <xsl:text>: </xsl:text>
                <xsl:apply-templates select="dissertation/published/publisher"/>
                <xsl:text>, </xsl:text>
                <xsl:value-of select="normalize-space(dissertation/published/pubDate)"/>
                <xsl:text>.</xsl:text>
                <xsl:call-template name="DoReprintInfo">
                    <xsl:with-param name="reprintInfo" select="dissertation/published/reprintInfo"/>
                </xsl:call-template>
            </xsl:if>
            <xsl:call-template name="DoRefUrlEtc">
                <xsl:with-param name="path" select="dissertation"/>
            </xsl:call-template>
        </xsl:if>
        <!--
            journal article
        -->
        <xsl:if test="article">
            <xsl:variable name="sTitle" select="normalize-space(refTitle)"/>
            <xsl:if test="string-length($sTitle) &gt; 0">
                <xsl:apply-templates select="refTitle"/>
                <xsl:text>.</xsl:text>
                <xsl:text>&#x20;</xsl:text>
            </xsl:if>
            <tex:cmd name="textit">
                <tex:parm>
                    <xsl:apply-templates select="article/jTitle"/>
                </tex:parm>
            </tex:cmd>
            <xsl:text>&#x20;</xsl:text>
            <xsl:if test="../@showAuthorName='no'">
                <xsl:call-template name="DoDate">
                    <xsl:with-param name="works" select="$works"/>
                </xsl:call-template>
            </xsl:if>
            <xsl:value-of select="normalize-space(article/jVol)"/>
            <xsl:if test="article/jIssueNumber">
                <xsl:text>(</xsl:text>
                <xsl:value-of select="article/jIssueNumber"/>
                <xsl:text>)</xsl:text>
            </xsl:if>
            <xsl:choose>
                <xsl:when test="article/jPages">
                    <xsl:text>:</xsl:text>
                    <xsl:value-of select="normalize-space(article/jPages)"/>
                </xsl:when>
                <xsl:when test="article/jArticleNumber">
                    <xsl:text>-</xsl:text>
                    <xsl:value-of select="normalize-space(article/jArticleNumber)"/>
                </xsl:when>
            </xsl:choose>
            <xsl:text>.</xsl:text>
            <xsl:call-template name="DoReprintInfo">
                <xsl:with-param name="reprintInfo" select="article/reprintInfo"/>
            </xsl:call-template>
            <xsl:call-template name="DoRefUrlEtc">
                <xsl:with-param name="path" select="article"/>
            </xsl:call-template>
        </xsl:if>
        <!--
            field notes
        -->
        <xsl:if test="fieldNotes">
            <xsl:variable name="sTitle" select="normalize-space(refTitle)"/>
            <xsl:if test="string-length($sTitle) &gt; 0">
                <xsl:apply-templates select="refTitle"/>
                <xsl:text>.</xsl:text>
                <xsl:text>&#x20;</xsl:text>
            </xsl:if>
            <xsl:if test="../@showAuthorName='no'">
                <xsl:call-template name="DoDate">
                    <xsl:with-param name="works" select="$works"/>
                </xsl:call-template>
            </xsl:if>
            <xsl:if test="fieldNotes/location">
                <xsl:text> (</xsl:text>
                <xsl:apply-templates select="fieldNotes/location"/>
                <xsl:text>).  </xsl:text>
            </xsl:if>
            <xsl:apply-templates select="fieldNotes/institution"/>
            <xsl:text>.</xsl:text>
            <xsl:call-template name="DoRefUrlEtc">
                <xsl:with-param name="path" select="fieldNotes"/>
            </xsl:call-template>
        </xsl:if>
        <!--
            ms (manuscript)
        -->
        <xsl:if test="ms">
            <xsl:variable name="sTitle" select="normalize-space(refTitle)"/>
            <xsl:if test="string-length($sTitle) &gt; 0">
                <xsl:apply-templates select="refTitle"/>
                <xsl:text>.</xsl:text>
                <xsl:text>&#x20;</xsl:text>
            </xsl:if>
            <xsl:if test="../@showAuthorName='no'">
                <xsl:call-template name="DoDate">
                    <xsl:with-param name="works" select="$works"/>
                </xsl:call-template>
            </xsl:if>
            <xsl:if test="ms/location">
                <xsl:text> (</xsl:text>
                <xsl:apply-templates select="ms/location"/>
                <xsl:text>).  </xsl:text>
            </xsl:if>
            <xsl:apply-templates select="ms/institution"/>
            <xsl:if test="ms/msVersion">
                <xsl:apply-templates select="ms/msVersion"/>
                <xsl:text>.  </xsl:text>
            </xsl:if>
            <xsl:choose>
                <xsl:when test="ms">
                    <xsl:text> Manuscript.</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>.</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="DoRefUrlEtc">
                <xsl:with-param name="path" select="ms"/>
            </xsl:call-template>
        </xsl:if>
        <!--
            paper
        -->
        <xsl:if test="paper">
            <xsl:variable name="sTitle" select="normalize-space(refTitle)"/>
            <xsl:if test="string-length($sTitle) &gt; 0">
                <xsl:apply-templates select="refTitle"/>
                <xsl:text>.</xsl:text>
            </xsl:if>
            <xsl:if test="../@showAuthorName='no'">
                <xsl:call-template name="DoDate">
                    <xsl:with-param name="works" select="$works"/>
                </xsl:call-template>
            </xsl:if>
            <xsl:call-template name="OutputPaperLabel"/>
            <xsl:value-of select="normalize-space(paper/conference)"/>
            <xsl:if test="paper/location">
                <xsl:text>, </xsl:text>
                <xsl:apply-templates select="paper/location"/>
            </xsl:if>
            <xsl:text>.</xsl:text>
            <xsl:call-template name="DoRefUrlEtc">
                <xsl:with-param name="path" select="paper"/>
            </xsl:call-template>
        </xsl:if>
        <!--
            proceedings
        -->
        <xsl:if test="proceedings">
            <xsl:variable name="sTitle" select="normalize-space(refTitle)"/>
            <xsl:if test="string-length($sTitle) &gt; 0">
                <xsl:apply-templates select="refTitle"/>
                <xsl:text>.</xsl:text>
            </xsl:if>
            <xsl:if test="../@showAuthorName='no'">
                <xsl:call-template name="DoDate">
                    <xsl:with-param name="works" select="$works"/>
                </xsl:call-template>
            </xsl:if>
            <xsl:choose>
                <xsl:when test="proceedings/procCitation">
                    <xsl:text>  In </xsl:text>
                    <xsl:variable name="citation" select="proceedings/procCitation"/>
                    <xsl:choose>
                        <xsl:when test="saxon:node-set($collOrProcVolumesToInclude)/refWork[@id=exsl:node-set($citation)/@refToBook]">
                            <xsl:call-template name="DoRefCitation">
                                <xsl:with-param name="citation" select="$citation"/>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="FleshOutRefCitation">
                                <xsl:with-param name="citation" select="$citation"/>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:choose>
                        <xsl:when test="proceedings/procEd">
                            <xsl:text>  In </xsl:text>
                            <xsl:call-template name="DoEdPlural">
                                <xsl:with-param name="editor" select="proceedings/procEd"/>
                            </xsl:call-template>
                            <xsl:text>&#x20;</xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>&#x20;</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                    <tex:cmd name="textit">
                        <tex:parm>
                            <xsl:value-of select="normalize-space(proceedings/procTitle)"/>
                        </tex:parm>
                    </tex:cmd>
                    <xsl:choose>
                        <xsl:when test="proceedings/procVol">
                            <xsl:text>&#x20;</xsl:text>
                            <xsl:value-of select="normalize-space(proceedings/procVol)"/>
                            <xsl:text>:</xsl:text>
                            <xsl:value-of select="normalize-space(proceedings/procPages)"/>
                            <xsl:text>. </xsl:text>
                        </xsl:when>
                        <xsl:when test="proceedings/procPages">
                            <xsl:text>, </xsl:text>
                            <xsl:value-of select="normalize-space(proceedings/procPages)"/>
                            <xsl:text>. </xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>. </xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                    <xsl:if test="collection/seriesEd">
                        <xsl:call-template name="DoEdPlural">
                            <xsl:with-param name="editor" select="proceedings/seriesEd"/>
                        </xsl:call-template>
                        <xsl:text>&#x20;</xsl:text>
                    </xsl:if>
                    <xsl:if test="proceedings/series">
                        <tex:cmd name="textit">
                            <tex:parm>
                                <xsl:apply-templates select="proceedings/series"/>
                            </tex:parm>
                        </tex:cmd>
                        <xsl:choose>
                            <xsl:when test="proceedings/bVol">
                                <xsl:text>&#x20;</xsl:text>
                                <xsl:apply-templates select="proceedings/bVol"/>
                                <xsl:text>. </xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="OutputPeriodIfNeeded">
                                    <xsl:with-param name="sText" select="proceedings/series"/>
                                </xsl:call-template>
                                <xsl:text>&#x20;</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:if>
                    <xsl:if test="proceedings/location or proceedings/publisher">
                        <xsl:apply-templates select="proceedings/location"/>
                        <xsl:if test="proceedings/publisher">
                            <xsl:text>: </xsl:text>
                            <xsl:apply-templates select="proceedings/publisher"/>
                        </xsl:if>
                        <xsl:text>.</xsl:text>
                    </xsl:if>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="DoReprintInfo">
                <xsl:with-param name="reprintInfo" select="proceedings/reprintInfo"/>
            </xsl:call-template>
            <xsl:call-template name="DoRefUrlEtc">
                <xsl:with-param name="path" select="proceedings"/>
            </xsl:call-template>
        </xsl:if>
        <!--
            thesis
        -->
        <xsl:if test="thesis">
            <xsl:variable name="sTitle" select="normalize-space(refTitle)"/>
            <xsl:if test="string-length($sTitle) &gt; 0">
                <tex:cmd name="textit">
                    <tex:parm>
                        <xsl:apply-templates select="refTitle"/>
                    </tex:parm>
                </tex:cmd>
                <xsl:text>.  </xsl:text>
            </xsl:if>
            <xsl:call-template name="OutputLabel">
                <xsl:with-param name="sDefault" select="$sMAThesisDefaultLabel"/>
                <xsl:with-param name="pLabel">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(thesis/@labelThesis)) &gt; 0">
                            <xsl:value-of select="thesis/@labelThesis"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="//references/@labelThesis"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:with-param>
            </xsl:call-template>
            <xsl:text>. </xsl:text>
            <xsl:if test="../@showAuthorName='no'">
                <xsl:call-template name="DoDate">
                    <xsl:with-param name="works" select="$works"/>
                </xsl:call-template>
            </xsl:if>
            <xsl:if test="thesis/location">
                <xsl:text> (</xsl:text>
                <xsl:apply-templates select="thesis/location"/>
                <xsl:text>).  </xsl:text>
            </xsl:if>
            <xsl:apply-templates select="thesis/institution"/>
            <xsl:text>.</xsl:text>
            <xsl:if test="thesis/published">
                <xsl:text>  Published by </xsl:text>
                <xsl:apply-templates select="thesis/published/location"/>
                <xsl:text>: </xsl:text>
                <xsl:apply-templates select="thesis/published/publisher"/>
                <xsl:text>, </xsl:text>
                <xsl:value-of select="normalize-space(thesis/published/pubDate)"/>
                <xsl:text>.</xsl:text>
                <xsl:call-template name="DoReprintInfo">
                    <xsl:with-param name="reprintInfo" select="thesis/published/reprintInfo"/>
                </xsl:call-template>
            </xsl:if>
            <xsl:call-template name="DoRefUrlEtc">
                <xsl:with-param name="path" select="thesis"/>
            </xsl:call-template>
        </xsl:if>
        <!--
            webPage
        -->
        <xsl:if test="webPage">
            <xsl:variable name="sTitle" select="normalize-space(refTitle)"/>
            <xsl:if test="string-length($sTitle) &gt; 0">
                <xsl:apply-templates select="refTitle"/>
                <xsl:text>.</xsl:text>
                <xsl:text>&#x20;</xsl:text>
            </xsl:if>
            <xsl:if test="../@showAuthorName='no'">
                <xsl:call-template name="DoDate">
                    <xsl:with-param name="works" select="$works"/>
                </xsl:call-template>
            </xsl:if>
            <xsl:if test="webPage/edition">
                <xsl:apply-templates select="webPage/edition"/>
                <xsl:call-template name="OutputPeriodIfNeeded">
                    <xsl:with-param name="sText" select="webPage/edition"/>
                </xsl:call-template>
                <xsl:text>&#x20;</xsl:text>
            </xsl:if>
            <xsl:if test="webPage/location">
                <xsl:apply-templates select="webPage/location"/>
                <xsl:text>: </xsl:text>
            </xsl:if>
            <xsl:if test="webPage/institution">
                <xsl:apply-templates select="webPage/institution"/>
                <xsl:text>. </xsl:text>
            </xsl:if>
            <xsl:if test="webPage/publisher">
                <xsl:apply-templates select="webPage/publisher"/>
            </xsl:if>
            <xsl:call-template name="DoReprintInfo">
                <xsl:with-param name="reprintInfo" select="webPage/reprintInfo"/>
            </xsl:call-template>
            <xsl:text> (</xsl:text>
            <xsl:call-template name="AddAnyLinkAttributes"/>
            <xsl:call-template name="DoExternalHyperRefBegin">
                <xsl:with-param name="sName" select="normalize-space(webPage/url)"/>
            </xsl:call-template>
            <xsl:value-of select="normalize-space(webPage/url)"/>
            <xsl:call-template name="DoExternalHyperRefEnd"/>
            <xsl:text>).</xsl:text>
            <xsl:if test="webPage/dateAccessed">
                <xsl:text>  (accessed </xsl:text>
                <xsl:value-of select="normalize-space(webPage/dateAccessed)"/>
                <xsl:text>).</xsl:text>
            </xsl:if>
        </xsl:if>
        <xsl:call-template name="DoRefUrlEtc">
            <xsl:with-param name="path" select="."/>
        </xsl:call-template>
        <xsl:variable name="sDOI" select="normalize-space(descendant::doi)"/>
        <xsl:if test="string-length($sDOI) &gt; 0">
            <xsl:text> doi:</xsl:text>
            <xsl:call-template name="AddAnyLinkAttributes"/>
            <xsl:call-template name="DoExternalHyperRefBegin">
                <xsl:with-param name="sName" select="concat('https://doi.org/',translate($sDOI,$sStripFromUrl,''))"/>
            </xsl:call-template>
            <xsl:value-of select="$sDOI"/>
            <xsl:call-template name="DoExternalHyperRefEnd"/>
            <xsl:text>.</xsl:text>
        </xsl:if>
        <xsl:apply-templates select="descendant-or-self::comment"/>
        <tex:cmd name="par" gr="0" nl2="1"/>
    </xsl:template>
    <!--  
        DoRefWorks
    -->
    <xsl:template name="DoRefWorkPrep">
<!--        <xsl:variable name="thisAuthor" select="."/>
        <xsl:variable name="works"
            select="refWork[@id=exsl:node-set($citations)[not(ancestor::comment) and not(ancestor::annotation)][not(ancestor::refWork) or ancestor::refWork[@id=exsl:node-set($citations)[not(ancestor::refWork)]/@ref]]/@ref] | exsl:node-set($refWorks)[@id=saxon:node-set($collOrProcVolumesToInclude)/refWork/@id][parent::refAuthor=$thisAuthor] | refWork[@id=exsl:node-set($citationsInAnnotationsReferredTo)[not(ancestor::comment)]/@ref]"/>
        <!-\-            <xsl:for-each select="$authors">
            <xsl:variable name="works" select="refWork[@id=//citation[not(ancestor::comment)]/@ref]"/>
        -\->
        <xsl:for-each select="$works">
--> 
        <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak')">
                <tex:cmd name="pagebreak" gr="0" nl2="0"/>
            </xsl:if>
            <tex:spec cat="esc"/>
            <xsl:text>hangindent.25in</xsl:text>
            <tex:cmd name="relax" gr="0" nl2="1"/>
            <tex:spec cat="esc"/>
            <xsl:text>hangafter1</xsl:text>
            <tex:cmd name="relax" gr="0" nl2="1"/>
            <tex:cmd name="fontsize">
                <tex:parm>10</tex:parm>
                <tex:parm>12</tex:parm>
            </tex:cmd>
            <tex:cmd name="selectfont" gr="0" nl2="1"/>
            <!--                        <tex:cmd name="item" gr="0" nl2="1"/>-->
<!--            <xsl:call-template name="DoRefWork">
                <xsl:with-param name="works" select="$works"/>
            </xsl:call-template>
        </xsl:for-each>
-->    </xsl:template>
    <!--  
        DoDate
    -->
    <xsl:template name="DoDate">
        <xsl:param name="works"/>
        <xsl:param name="sortedWorks"/>
        <xsl:variable name="date">
            <xsl:value-of select="refDate"/>
        </xsl:variable>
        <xsl:for-each select="refDate">
            <xsl:call-template name="OutputRefDateValue">
                <xsl:with-param name="date" select="$date"/>
                <xsl:with-param name="works" select="$works"/>
                <xsl:with-param name="sortedWorks" select="$sortedWorks"/>
            </xsl:call-template>
        </xsl:for-each>
        <xsl:text>. </xsl:text>
    </xsl:template>
    <!--  
        DoSectionRefLabel
    -->
    <xsl:template name="DoSectionRefLabel">
        <xsl:param name="sLabel"/>
        <xsl:param name="sDefault"/>
        <xsl:choose>
            <xsl:when test="string-length($sLabel) &gt; 0">
                <xsl:value-of select="$sLabel"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sDefault"/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:text>&#xa0;</xsl:text>
    </xsl:template>
    <!--  
        DoSectionLevelTitle
    -->
    <xsl:template name="DoSectionLevelTitle">
        <xsl:param name="bIsCentered" select="'N'"/>
        <xsl:param name="sFontFamily"/>
        <xsl:param name="sFontSize" select="'normalsize'"/>
        <xsl:param name="sBold"/>
        <xsl:param name="sItalic"/>
        <xsl:param name="sVerticalSpaceBefore" select="$sBasicPointSize"/>
        <xsl:param name="sVerticalSpaceAfter" select="$sBasicPointSize"/>
        <tex:cmd name="vspace" nl1="1" nl2="1">
            <tex:parm><xsl:value-of select="$sVerticalSpaceBefore"/>pt</tex:parm>
        </tex:cmd>
        <xsl:if test="contains(key('TypeID',@type)/@XeLaTeXSpecial,'clearpage') or contains(@XeLaTeXSpecial,'clearpage')">
            <tex:cmd name="clearpage" gr="0" nl2="0"/>
        </xsl:if>
        <xsl:if test="contains(key('TypeID',@type)/@XeLaTeXSpecial,'pagebreak') or contains(@XeLaTeXSpecial,'pagebreak')">
            <tex:cmd name="pagebreak" gr="0" nl2="0"/>
        </xsl:if>
        <xsl:call-template name="OKToBreakHere"/>
        <tex:group nl1="1" nl2="1">
            <xsl:call-template name="DoType"/>
            <xsl:choose>
                <xsl:when test="$bIsCentered='Y'">
                    <!-- adjust for center environment -->
                    <!--                    <tex:cmd name="vspace*">
                        <tex:parm>
                            <xsl:text>-2</xsl:text>
                            <tex:cmd name="topsep" gr="0"/>
                        </tex:parm>
                    </tex:cmd>
-->
                    <tex:group>
                        <tex:cmd name="centering">
                            <xsl:call-template name="DoSectionLevelTitleCommon">
                                <xsl:with-param name="sFontFamily" select="$sFontFamily"/>
                                <xsl:with-param name="sFontSize" select="$sFontSize"/>
                                <xsl:with-param name="sBold" select="$sBold"/>
                                <xsl:with-param name="sItalic" select="$sItalic"/>
                            </xsl:call-template>
                            <xsl:variable name="contentForThisElement">
                                <xsl:call-template name="DoSectionLevelTitleCommon">
                                    <xsl:with-param name="sFontFamily" select="$sFontFamily"/>
                                    <xsl:with-param name="sFontSize" select="$sFontSize"/>
                                    <xsl:with-param name="sBold" select="$sBold"/>
                                    <xsl:with-param name="sItalic" select="$sItalic"/>
                                </xsl:call-template>
                            </xsl:variable>
                            <xsl:if test="string-length($contentForThisElement) &gt; 0">
                                <tex:spec cat="esc"/>
                                <tex:spec cat="esc"/>
                            </xsl:if>
                        </tex:cmd>
                    </tex:group>
                    <!-- adjust for center environment -->
                    <!--                    <tex:cmd name="vspace*">
                        <tex:parm>
                            <xsl:text>-</xsl:text>
                            <tex:cmd name="parsep" gr="0"/>
                        </tex:parm>
                    </tex:cmd>
-->
                </xsl:when>
                <xsl:otherwise>
                    <tex:cmd name="noindent" nl2="1">
                        <tex:parm>
                            <xsl:call-template name="DoSectionLevelTitleCommon">
                                <xsl:with-param name="sFontFamily" select="$sFontFamily"/>
                                <xsl:with-param name="sFontSize" select="$sFontSize"/>
                                <xsl:with-param name="sBold" select="$sBold"/>
                                <xsl:with-param name="sItalic" select="$sItalic"/>
                            </xsl:call-template>
                        </tex:parm>
                    </tex:cmd>
                    <!--                        <xsl:text>noindent</xsl:text>-->
                </xsl:otherwise>
            </xsl:choose>
            <tex:cmd name="markright" nl2="1">
                <tex:parm>
                    <xsl:call-template name="DoSecTitleRunningHeader"/>
                </tex:parm>
            </tex:cmd>
            <xsl:call-template name="CreateAddToContents">
                <xsl:with-param name="id" select="@id"/>
            </xsl:call-template>
            <xsl:call-template name="DoTypeEnd"/>
        </tex:group>
        <tex:cmd name="par"/>
        <xsl:call-template name="DoNotBreakHere"/>
        <tex:cmd name="vspace" nl1="1" nl2="1">
            <tex:parm><xsl:value-of select="$sVerticalSpaceAfter"/>pt</tex:parm>
        </tex:cmd>
    </xsl:template>
    <xsl:template name="DoSectionLevelTitleCommon">
        <xsl:param name="sFontFamily"/>
        <xsl:param name="sFontSize"/>
        <xsl:param name="sBold"/>
        <xsl:param name="sItalic"/>
        <xsl:call-template name="DoInternalTargetBegin">
            <xsl:with-param name="sName" select="@id"/>
        </xsl:call-template>
        <tex:cmd name="{$sFontFamily}">
            <tex:parm>
                <tex:cmd name="{$sFontSize}">
                    <tex:parm>
                        <tex:cmd name="raisebox">
                            <tex:parm>
                                <tex:cmd name="baselineskip" gr="0"/>
                            </tex:parm>
                            <tex:opt>0pt</tex:opt>
                            <tex:parm>
                                <tex:cmd name="pdfbookmark" nl2="0">
                                    <tex:opt>
                                        <xsl:variable name="iLevel" select="substring-after(name(),'section')"/>
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
                                        <xsl:call-template name="OutputSectionNumberAndTitle">
                                            <xsl:with-param name="bIsBookmark" select="'Y'"/>
                                        </xsl:call-template>
                                    </tex:parm>
                                    <tex:parm>
                                        <xsl:value-of select="translate(@id,$sIDcharsToMap, $sIDcharsMapped)"/>
                                    </tex:parm>
                                </tex:cmd>
                            </tex:parm>
                        </tex:cmd>
                        <!-- since we do not have a way to say 'normal' , we have to do the bold this way-->
                        <xsl:if test="$sBold='textbf'">
                            <tex:spec cat="esc"/>
                            <xsl:text>textbf</xsl:text>
                            <tex:spec cat="bg"/>
                        </xsl:if>
                        <xsl:choose>
                            <xsl:when test="$sItalic='textit'">
                                <tex:cmd name="{$sItalic}">
                                    <tex:parm>
                                        <xsl:call-template name="OutputSectionNumberAndTitle"/>
                                    </tex:parm>
                                </tex:cmd>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="OutputSectionNumberAndTitle"/>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:if test="$sBold='textbf'">
                            <tex:spec cat="eg"/>
                        </xsl:if>
                    </tex:parm>
                </tex:cmd>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="DoInternalTargetEnd"/>
    </xsl:template>
    <!--  
                  DoSecTitleRunningHeader
-->
    <xsl:template name="DoSecTitleRunningHeader">
        <xsl:choose>
            <xsl:when test="string-length(shortTitle) &gt; 0">
                <xsl:apply-templates select="shortTitle" mode="InMarker"/>
            </xsl:when>
            <xsl:when test="string-length(frontMatter/shortTitle) &gt; 0">
                <xsl:apply-templates select="frontMatter/shortTitle" mode="InMarker"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="secTitle | frontMatter/title" mode="InMarker"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoTableNumbered
    -->
    <xsl:template name="DoTableNumbered">
        <xsl:if test="preceding-sibling::*[1][name()!='p' and name()!='pc']">
            <!-- p and pc insert one of these already -->
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
        <xsl:if test="contains(@XeLaTeXSpecial,'clearpage')">
            <tex:cmd name="clearpage" gr="0" nl2="0"/>
        </xsl:if>
        <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak')">
            <tex:cmd name="pagebreak" gr="0" nl2="0"/>
        </xsl:if>
        <tex:cmd name="XLingPaperneedspace">
            <tex:parm>
                <xsl:text>3</xsl:text>
                <tex:cmd name="baselineskip" gr="0"/>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="DoInternalTargetBegin">
            <xsl:with-param name="sName" select="@id"/>
        </xsl:call-template>
        <xsl:call-template name="DoInternalTargetEnd"/>
        <xsl:call-template name="CreateAddToContents">
            <xsl:with-param name="id" select="@id"/>
        </xsl:call-template>
        <!--        <xsl:choose>
            <xsl:when test="@align='center'">
            <tex:spec cat="esc"/>
            <xsl:text>centering </xsl:text>
            </xsl:when>
            <xsl:when test="@align='right'">
            <tex:spec cat="esc"/>
            <xsl:text>raggedleft</xsl:text>
            </xsl:when>
            </xsl:choose>
        -->
        <xsl:call-template name="DoType">
            <xsl:with-param name="type" select="@type"/>
        </xsl:call-template>
        <xsl:if test="exsl:node-set($lingPaper)/@tablenumberedLabelAndCaptionLocation='before'">
            <xsl:call-template name="OutputTableNumberedLabelAndCaption"/>
            <tex:spec cat="esc"/>
            <tex:spec cat="esc"/>
            <!--            <tex:spec cat="lsb"/>
                <xsl:text>.3em</xsl:text>
                <tex:spec cat="rsb"/>
            -->
        </xsl:if>
        <!--        <tex:cmd name="leavevmode" gr="0" nl2="1"/>-->
        <xsl:apply-templates select="*[name()!='shortCaption']"/>
        <xsl:call-template name="DoTypeEnd">
            <xsl:with-param name="type" select="@type"/>
        </xsl:call-template>
        <xsl:if test="exsl:node-set($lingPaper)/@tablenumberedLabelAndCaptionLocation='after'">
            <tex:cmd name="vspace*">
                <tex:parm>
                    <xsl:text>-</xsl:text>
                    <tex:cmd name="baselineskip" gr="0"/>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="vspace">
                <tex:parm>.3em</tex:parm>
            </tex:cmd>
            <xsl:call-template name="OutputTableNumberedLabelAndCaption"/>
            <xsl:call-template name="HandleEndnotesTextInCaptionAfterTablenumbered"/>
            <tex:cmd name="par"/>
            <tex:cmd name="vspace">
                <tex:parm>.3em</tex:parm>
            </tex:cmd>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleFreeLanguageFontInfo
    -->
    <xsl:template name="HandleFreeLanguageFontInfo">
        <xsl:param name="originalContext"/>
        <xsl:variable name="language" select="key('LanguageID',@lang)"/>
        <tex:cmd name="Lang{translate(@lang,$sDigits, $sLetters)}FontFamily">
            <tex:parm>
                <!--                        <tex:cmd name="raggedright" gr="0" nl2="0"/>-->
                <tex:group>
                    <xsl:call-template name="OutputFontAttributes">
                        <xsl:with-param name="language" select="$language"/>
                    </xsl:call-template>
                    <xsl:call-template name="DoLiteralLabel"/>
                    <xsl:call-template name="HandleLanguageContent">
                        <xsl:with-param name="language" select="$language"/>
                        <xsl:with-param name="bReversing" select="'N'"/>
                        <xsl:with-param name="originalContext" select="$originalContext"/>
                    </xsl:call-template>
                    <xsl:call-template name="OutputFontAttributesEnd">
                        <xsl:with-param name="language" select="$language"/>
                    </xsl:call-template>
                </tex:group>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        HandleFreeNoLanguageFontInfo
    -->
    <xsl:template name="HandleFreeNoLanguageFontInfo">
        <xsl:param name="originalContext"/>
        <xsl:variable name="sFreeTextContent" select="normalize-space(.)"/>
        <xsl:choose>
            <xsl:when test="string-length($sFreeTextContent)=0 and following-sibling::free">
                <xsl:text>&#xa0;</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:apply-templates>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        FleshOutRefCitation
    -->
    <xsl:template name="FleshOutRefCitation">
        <xsl:param name="citation"/>
        <xsl:variable name="citedWork" select="key('RefWorkID',exsl:node-set($citation)/@refToBook)"/>
        <xsl:call-template name="ConvertLastNameFirstNameToFirstNameLastName">
            <xsl:with-param name="sCitedWorkAuthor" select="exsl:node-set($citedWork)/../@name"/>
        </xsl:call-template>
        <xsl:choose>
            <xsl:when test="exsl:node-set($citedWork)/authorRole">
                <xsl:text>, </xsl:text>
                <xsl:value-of select="exsl:node-set($citedWork)/authorRole"/>
                <xsl:call-template name="OutputPeriodIfNeeded">
                    <xsl:with-param name="sText" select="exsl:node-set($citedWork)/authorRole"/>
                </xsl:call-template>
                <xsl:text>&#x20;</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>.  </xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="DoBook">
            <xsl:with-param name="book" select="exsl:node-set($citedWork)/book"/>
            <xsl:with-param name="pages" select="exsl:node-set($citation)/@page"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        FontFamilyNameToUse
    -->
    <xsl:template name="FontFamilyNameToUse">
        <xsl:param name="language"/>
        <xsl:param name="id"/>
        <xsl:text>Lang</xsl:text>
        <xsl:choose>
            <xsl:when test="string-length($id) &gt; 0">
                <xsl:value-of select="translate($id,$sDigits, $sLetters)"/>
            </xsl:when>
            <xsl:when test="name($language)='keyTerm'">
                <xsl:text>KeyTerm</xsl:text>
                <xsl:value-of select="translate(generate-id($language),$sDigits, $sLetters)"/>
            </xsl:when>
            <xsl:otherwise/>
        </xsl:choose>
        <xsl:text>FontFamily</xsl:text>
    </xsl:template>
    <!--  
        HandleFontFamily
    -->
    <xsl:template name="HandleFontFamily">
        <xsl:param name="language"/>
        <tex:spec cat="esc"/>
        <xsl:call-template name="FontFamilyNameToUse">
            <xsl:with-param name="language" select="$language"/>
            <xsl:with-param name="id">
                <xsl:choose>
                    <xsl:when test="name($language)='abbreviations'">
                        <xsl:value-of select="$sXLingPaperAbbreviation"/>
                    </xsl:when>
                    <xsl:when test="name($language)='glossaryTerms'">
                        <xsl:value-of select="$sXLingPaperGlossaryTerm"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="exsl:node-set($language)/@id"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:with-param>
        </xsl:call-template>
        <tex:spec cat="bg"/>
    </xsl:template>
    <!--
        LinkAttributesBegin
    -->
    <xsl:template name="LinkAttributesBegin"/>
    <!--
        LinkAttributesEnd
    -->
    <xsl:template name="LinkAttributesEnd"/>
    <!--  
                  OutputChapterNumber
-->
    <xsl:template name="OutputChapterNumber">
        <xsl:choose>
            <xsl:when test="name()='chapter'">
                <xsl:apply-templates select="." mode="numberChapter"/>
            </xsl:when>
            <xsl:when test="name()='chapterBeforePart'">
                <xsl:text>0</xsl:text>
            </xsl:when>
            <xsl:when test="name()='chapterInCollection'">
                <xsl:apply-templates select="." mode="numberChapter"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="." mode="numberAppendix"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
                  OutputChapTitle
-->
    <xsl:template name="OutputChapTitle">
        <xsl:param name="sTitle"/>
        <xsl:apply-templates select="$sTitle"/>
    </xsl:template>
    <!--  
                  OutputExampleNumber
-->
    <xsl:template name="OutputExampleNumber">
        <xsl:element name="a">
            <xsl:attribute name="name">
                <xsl:value-of select="../../@num"/>
            </xsl:attribute>
            <xsl:text>(</xsl:text>
            <xsl:call-template name="GetExampleNumber">
                <xsl:with-param name="example" select="."/>
            </xsl:call-template>
            <xsl:text>)</xsl:text>
        </xsl:element>
    </xsl:template>
    <!--  
        OutputFigureLabelAndCaption
    -->
    <xsl:template name="OutputFigureLabelAndCaption">
        <xsl:param name="bDoBold" select="'Y'"/>
        <xsl:param name="bDoStyles" select="'Y'"/>
        <xsl:if test="$bDoBold='Y'">
            <tex:spec cat="bg"/>
            <tex:spec cat="esc"/>
            <xsl:text>textbf</xsl:text>
            <tex:spec cat="bg"/>
        </xsl:if>
        <xsl:call-template name="OutputFigureLabel"/>
        <!--        <xsl:apply-templates select="." mode="figure"/>-->
        <xsl:call-template name="GetFigureNumber">
            <xsl:with-param name="figure" select="."/>
        </xsl:call-template>
        <xsl:text>&#xa0;</xsl:text>
        <xsl:if test="$bDoBold='Y'">
            <tex:spec cat="eg"/>
            <tex:spec cat="eg"/>
        </xsl:if>
        <xsl:choose>
            <xsl:when test="$bDoStyles='Y'">
                <xsl:apply-templates select="caption" mode="show"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="caption" mode="contents"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <xsl:template match="caption | endCaption" mode="show">
        <xsl:param name="bDoBold" select="'Y'"/>
        <xsl:param name="bDoLineBreak" select="'N'"/>
        <xsl:if test="descendant-or-self::endnote">
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
        <xsl:if test="$bDoBold='Y'">
            <tex:spec cat="bg"/>
            <tex:spec cat="esc"/>
            <xsl:text>textbf</xsl:text>
            <tex:spec cat="bg"/>
        </xsl:if>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="."/>
        </xsl:call-template>
        <xsl:call-template name="DoType"/>
        <xsl:apply-templates/>
        <xsl:if test="$bDoLineBreak='Y'">
            <tex:spec cat="esc"/>
            <tex:spec cat="esc"/>
        </xsl:if>
        <xsl:call-template name="DoTypeEnd"/>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="."/>
        </xsl:call-template>
        <xsl:if test="$bDoBold='Y'">
            <tex:spec cat="eg"/>
            <tex:spec cat="eg"/>
        </xsl:if>
    </xsl:template>
    <xsl:template match="caption | endCaption" mode="contents">
        <xsl:choose>
            <xsl:when test="following-sibling::shortCaption">
                <xsl:apply-templates select="following-sibling::shortCaption"/>
            </xsl:when>
            <xsl:when test="ancestor::tablenumbered/shortCaption">
                <xsl:apply-templates select="ancestor::tablenumbered/shortCaption"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="text() | *[not(descendant-or-self::endnote or descendant-or-self::indexedItem)]"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
                  OutputFrontOrBackMatterTitle
-->
    <xsl:template name="OutputFrontOrBackMatterTitle">
        <xsl:param name="id"/>
        <xsl:param name="sTitle"/>
        <xsl:param name="titlePart2"/>
        <xsl:param name="bIsBook" select="'Y'"/>
        <xsl:param name="bForcePageBreak" select="'N'"/>
        <xsl:param name="bDoTwoColumns" select="'N'"/>
        <xsl:choose>
            <xsl:when test="$bIsBook='Y' and $bForcePageBreak='Y'">
                <tex:cmd name="cleardoublepage"/>
                <xsl:if test="$bDoTwoColumns = 'Y'">
                    <tex:cmd name="markboth" nl2="1">
                        <tex:parm>
                            <xsl:call-template name="GetHeaderTitleForFrontOrBackMatter">
                                <xsl:with-param name="sTitle" select="$sTitle"/>
                            </xsl:call-template>
                        </tex:parm>
                        <tex:parm>
                            <xsl:call-template name="GetHeaderTitleForFrontOrBackMatter">
                                <xsl:with-param name="sTitle" select="$sTitle"/>
                            </xsl:call-template>
                        </tex:parm>
                    </tex:cmd>
                    <tex:spec cat="esc" nl1="1"/>
                    <xsl:text>twocolumn</xsl:text>
                    <tex:spec cat="lsb"/>
                </xsl:if>
                <tex:cmd name="thispagestyle">
                    <tex:parm>plain</tex:parm>
                </tex:cmd>
                <tex:cmd name="vspace*" nl1="1" nl2="1">
                    <tex:parm>172.2pt</tex:parm>
                </tex:cmd>
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="$bForcePageBreak='Y'">
                        <tex:cmd name="pagebreak" gr="0" nl2="1"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <tex:cmd name="vspace" nl1="1" nl2="1">
                            <tex:parm>
                                <!--    <xsl:value-of select="$sBasicPointSize"/>
                                <xsl:text>pt</xsl:text>-->
                                <xsl:call-template name="GetCurrentPointSize">
                                    <xsl:with-param name="bAddGlue" select="'Y'"/>
                                </xsl:call-template>
                            </tex:parm>
                        </tex:cmd>
                        <xsl:call-template name="OKToBreakHere"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
        <tex:group nl1="1" nl2="1">
            <!-- adjust for center environment -->
            <!--            <tex:cmd name="vspace*">
                <tex:parm>
                    <xsl:text>-2</xsl:text>
                    <tex:cmd name="topsep" gr="0"/>
                </tex:parm>
            </tex:cmd>
-->
            <tex:group>
                <tex:cmd name="centering" nl2="1">
                    <tex:parm>
                        <xsl:call-template name="DoInternalTargetBegin">
                            <xsl:with-param name="sName" select="$id"/>
                        </xsl:call-template>
                        <tex:cmd>
                            <xsl:attribute name="name">
                                <xsl:choose>
                                    <xsl:when test="$chapters">LARGE</xsl:when>
                                    <xsl:otherwise>large</xsl:otherwise>
                                </xsl:choose>
                            </xsl:attribute>
                            <tex:parm>
                                <tex:cmd name="raisebox">
                                    <tex:parm>
                                        <tex:cmd name="baselineskip" gr="0"/>
                                    </tex:parm>
                                    <tex:opt>0pt</tex:opt>
                                    <tex:parm>
                                        <tex:cmd name="pdfbookmark" nl2="0">
                                            <tex:opt>
                                                <xsl:choose>
                                                    <xsl:when test="ancestor::chapterInCollection">
                                                        <xsl:text>2</xsl:text>
                                                    </xsl:when>
                                                    <xsl:otherwise>
                                                        <xsl:text>1</xsl:text>
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                            </tex:opt>
                                            <tex:parm>
                                                <xsl:value-of select="$sTitle"/>
                                                <xsl:if test="$titlePart2">
                                                    <xsl:value-of select="$titlePart2"/>
                                                </xsl:if>
                                            </tex:parm>
                                            <tex:parm>
                                                <xsl:value-of select="translate($id,$sIDcharsToMap, $sIDcharsMapped)"/>
                                            </tex:parm>
                                        </tex:cmd>
                                    </tex:parm>
                                </tex:cmd>
                                <tex:cmd name="textbf">
                                    <tex:parm>
                                        <xsl:call-template name="DoType">
                                            <xsl:with-param name="type" select="@type"/>
                                        </xsl:call-template>
                                        <xsl:value-of select="$sTitle"/>
                                        <xsl:if test="$titlePart2">
                                            <xsl:apply-templates select="$titlePart2"/>
                                        </xsl:if>
                                        <xsl:call-template name="DoTypeEnd"/>
                                        <xsl:variable name="contentForThisElement">
                                            <xsl:value-of select="$sTitle"/>
                                            <xsl:if test="$titlePart2">
                                                <xsl:apply-templates select="$titlePart2"/>
                                            </xsl:if>
                                        </xsl:variable>
                                        <xsl:if test="string-length($contentForThisElement) &gt; 0">
                                            <tex:spec cat="esc"/>
                                            <tex:spec cat="esc"/>
                                        </xsl:if>
                                    </tex:parm>
                                </tex:cmd>
                            </tex:parm>
                        </tex:cmd>
                        <xsl:call-template name="DoInternalTargetEnd"/>
                    </tex:parm>
                </tex:cmd>
            </tex:group>
            <!-- adjust for center environment -->
            <!--            <tex:cmd name="vspace*">
                <tex:parm>
                <xsl:text>-</xsl:text>
                <tex:cmd name="parsep" gr="0"/>
                </tex:parm>
                </tex:cmd>
            -->
            <xsl:choose>
                <xsl:when test="$bIsBook='Y' and $bDoTwoColumns='N'">
                    <tex:cmd name="markboth" nl2="1">
                        <tex:parm>
                            <xsl:call-template name="GetHeaderTitleForFrontOrBackMatter">
                                <xsl:with-param name="sTitle" select="$sTitle"/>
                            </xsl:call-template>
                        </tex:parm>
                        <tex:parm>
                            <xsl:call-template name="GetHeaderTitleForFrontOrBackMatter">
                                <xsl:with-param name="sTitle" select="$sTitle"/>
                            </xsl:call-template>
                        </tex:parm>
                    </tex:cmd>
                </xsl:when>
                <xsl:otherwise>
                    <tex:cmd name="markright" nl2="1">
                        <tex:parm>
                            <xsl:call-template name="GetHeaderTitleForFrontOrBackMatter">
                                <xsl:with-param name="sTitle" select="$sTitle"/>
                            </xsl:call-template>
                        </tex:parm>
                    </tex:cmd>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="CreateAddToContents">
                <xsl:with-param name="id" select="$id"/>
            </xsl:call-template>
        </tex:group>
        <tex:cmd name="par"/>
        <xsl:call-template name="DoNotBreakHere"/>
        <tex:cmd name="vspace" nl1="1" nl2="1">
            <tex:parm>
                <!--    <xsl:value-of select="$sBasicPointSize"/>
                <xsl:text>pt</xsl:text>-->
                <xsl:call-template name="GetCurrentPointSize">
                    <xsl:with-param name="bAddGlue" select="'Y'"/>
                </xsl:call-template>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <xsl:template name="GetHeaderTitleForFrontOrBackMatter">
        <xsl:param name="sTitle"/>
        <xsl:choose>
            <xsl:when test="ancestor-or-self::appendix">
                <xsl:call-template name="DoSecTitleRunningHeader"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sTitle"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
                   OutputIndexedItemsPageNumber
-->
    <xsl:template name="OutputIndexedItemsPageNumber">
        <xsl:param name="sIndexedItemID"/>
        <xsl:param name="sPage"/>
        <xsl:call-template name="AddAnyLinkAttributes"/>
        <xsl:call-template name="DoInternalHyperlinkBegin">
            <xsl:with-param name="sName" select="$sIndexedItemID"/>
        </xsl:call-template>
        <xsl:choose>
            <xsl:when test="$sPage">
                <xsl:value-of select="$sPage"/>
            </xsl:when>
            <xsl:otherwise>??</xsl:otherwise>
        </xsl:choose>
        <xsl:if test="ancestor::endnote">
            <xsl:text>n</xsl:text>
        </xsl:if>
        <xsl:call-template name="DoInternalHyperlinkEnd"/>
    </xsl:template>
    <!--  
        OutputInterlinearLineAsTableCells
    -->
    <xsl:template name="OutputInterlinearLineAsTableCells">
        <xsl:param name="sList"/>
        <xsl:param name="lang"/>
        <xsl:param name="sAlign"/>
        <xsl:variable name="sNewList" select="concat(normalize-space($sList),' ')"/>
        <xsl:variable name="sFirst" select="substring-before($sNewList,' ')"/>
        <xsl:variable name="sRest" select="substring-after($sNewList,' ')"/>
        <xsl:call-template name="DoDebugExamples"/>
        <xsl:call-template name="OutputInterlinearLineTableCellContent">
            <xsl:with-param name="lang" select="$lang"/>
            <xsl:with-param name="sFirst" select="$sFirst"/>
        </xsl:call-template>
        <tex:spec cat="align"/>
        <xsl:if test="$sRest">
            <xsl:call-template name="OutputInterlinearLineAsTableCells">
                <xsl:with-param name="sList" select="$sRest"/>
                <xsl:with-param name="lang" select="$lang"/>
                <xsl:with-param name="sAlign" select="$sAlign"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--  
        OutputInterlinearLineTableCellContent
    -->
    <xsl:template name="OutputInterlinearLineTableCellContent">
        <xsl:param name="lang"/>
        <xsl:param name="sFirst"/>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="key('LanguageID',$lang)"/>
            <xsl:with-param name="originalContext" select="$sFirst"/>
        </xsl:call-template>
        <xsl:value-of select="$sFirst"/>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="key('LanguageID',$lang)"/>
            <xsl:with-param name="originalContext" select="$sFirst"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        OutputInterlinearTextReferenceContent
    -->
    <xsl:template name="OutputInterlinearTextReferenceContent">
        <xsl:param name="sSource"/>
        <xsl:param name="sRef"/>
        <xsl:param name="bContentOnly" select="'N'"/>
        <xsl:param name="originalContext"/>
        <xsl:if test="$bContentOnly!='Y'">
            <tex:cmd name="hfill" nl2="0"/>
        </xsl:if>
        <xsl:text>[</xsl:text>
        <xsl:choose>
            <xsl:when test="$sSource">
                <xsl:apply-templates select="$sSource" mode="contents">
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:apply-templates>
            </xsl:when>
            <xsl:when test="string-length(normalize-space($sRef)) &gt; 0">
                <tex:group>
                    <xsl:call-template name="DoInterlinearTextReferenceLinkBegin">
                        <xsl:with-param name="sRef" select="$sRef"/>
                    </xsl:call-template>
                    <xsl:call-template name="AddAnyLinkAttributes"/>
                    <xsl:variable name="interlinear" select="key('InterlinearReferenceID',$sRef)"/>
                    <xsl:value-of select="exsl:node-set($interlinear)/../textInfo/shortTitle"/>
                    <xsl:choose>
                        <xsl:when test="string-length(exsl:node-set($contentLayoutInfo)/interlinearTextLayout/@textbeforeReferenceNumber) &gt; 0">
                            <!-- do nothing here; it is handled in DoInterlinearTextNumber -->
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>:</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                    <xsl:call-template name="DoInterlinearTextNumber">
                        <xsl:with-param name="interlinear" select="$interlinear"/>
                        <xsl:with-param name="sRef" select="$sRef"/>
                    </xsl:call-template>
                    <xsl:call-template name="DoInternalHyperlinkEnd"/>
                </tex:group>
            </xsl:when>
        </xsl:choose>
        <xsl:text>]</xsl:text>
    </xsl:template>
    <!--  
                  OutputSectionNumberAndTitle
-->
    <xsl:template name="OutputSectionNumberAndTitle">
        <xsl:param name="bIsBookmark" select="'N'"/>
        <xsl:param name="bIsContents" select="'N'"/>
        <xsl:call-template name="OutputSectionNumber"/>
        <xsl:text disable-output-escaping="yes">&#x20;</xsl:text>
        <xsl:choose>
            <xsl:when test="$bIsBookmark='Y'">
                <xsl:apply-templates select="secTitle/text() | secTitle/*[name()!='comment'] | frontMatter/title/text() | frontMatter/title/*[name()!='comment']" mode="bookmarks"/>
            </xsl:when>
            <xsl:when test="$bIsContents='Y'">
                <xsl:apply-templates select="secTitle | frontMatter/title" mode="contents"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="secTitle | frontMatter/title"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
      OutputSectionNumber
   -->
    <xsl:template name="OutputSectionNumber">
        <xsl:choose>
            <xsl:when test="ancestor-or-self::appendix">
                <xsl:apply-templates select="." mode="numberAppendix"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="." mode="number"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
                  OutputAllChapterTOC
-->
    <xsl:template name="OutputAllChapterTOC">
        <xsl:param name="nLevel" select="3"/>
        <xsl:choose>
            <xsl:when test="name()='appendix' and ancestor::chapterInCollection">
                <!-- figure out what the new value of the indent based on the section number itself -->
                <xsl:variable name="sSectionNumberIndentFormula">
                    <xsl:call-template name="CalculateSectionNumberIndent"/>
                </xsl:variable>
                <xsl:call-template name="SetTeXCommand">
                    <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
                    <xsl:with-param name="sCommandToSet" select="'leveloneindent'"/>
                    <xsl:with-param name="sValue" select="$sSectionNumberIndentFormula"/>
                </xsl:call-template>
                <!-- figure out what the new value of the number width based on the section number itself -->
                <xsl:variable name="sSectionNumberWidthFormula">
                    <xsl:call-template name="CalculateSectionNumberWidth"/>
                </xsl:variable>
                <xsl:call-template name="SetTeXCommand">
                    <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
                    <xsl:with-param name="sCommandToSet" select="'levelonewidth'"/>
                    <xsl:with-param name="sValue" select="$sSectionNumberWidthFormula"/>
                </xsl:call-template>
                <!-- output the toc line -->
                <xsl:call-template name="OutputTOCLine">
                    <xsl:with-param name="sLink" select="@id"/>
                    <xsl:with-param name="sLabel">
                        <xsl:call-template name="OutputChapterNumber"/>
                        <xsl:text>&#xa0;</xsl:text>
                        <xsl:apply-templates select="secTitle" mode="contents"/>
                    </xsl:with-param>
                    <xsl:with-param name="sIndent">
                        <tex:cmd name="leveloneindent" gr="0" nl2="0"/>
                    </xsl:with-param>
                    <xsl:with-param name="sNumWidth">
                        <tex:cmd name="levelonewidth" gr="0" nl2="0"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="OutputTOCLine">
                    <xsl:with-param name="sLink" select="@id"/>
                    <xsl:with-param name="sLabel">
                        <xsl:call-template name="OutputChapterNumber"/>
                        <xsl:text>&#xa0;</xsl:text>
                        <xsl:apply-templates select="secTitle | frontMatter/title" mode="contents"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
        <!-- following is for chapterInCollection -->
        <xsl:if test="name()='chapterInCollection'">
            <xsl:if test="frontMatter/author">
                <xsl:if test="count(preceding-sibling::chapterInCollection)=0">
                    <tex:cmd name="settowidth">
                        <tex:parm>
                            <tex:cmd name="leveloneindent" gr="0"/>
                        </tex:parm>
                        <tex:parm>
                            <xsl:text>1</xsl:text>
                            <tex:spec cat="esc"/>
                            <xsl:text>&#x20;</xsl:text>
                        </tex:parm>
                    </tex:cmd>
                </xsl:if>
                <!-- do author(s) -->
                <xsl:call-template name="OutputPlainTOCLine">
                    <xsl:with-param name="sIndent">
                        <tex:cmd name="leveloneindent" gr="0"/>
                    </xsl:with-param>
                    <xsl:with-param name="sLabel">
                        <tex:cmd name="textit">
                            <tex:parm>
                                <xsl:call-template name="GetAuthorsAsCommaSeparatedList"/>
                            </tex:parm>
                        </tex:cmd>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:if>
            <xsl:if test="frontMatter/abstract  or frontMatter/acknowledgements or frontMatter/preface">
                <tex:cmd name="settowidth">
                    <tex:parm>
                        <tex:cmd name="leveloneindent" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <xsl:text>1</xsl:text>
                        <tex:spec cat="esc"/>
                        <xsl:text>&#x20;</xsl:text>
                    </tex:parm>
                </tex:cmd>
                <xsl:apply-templates select="frontMatter/abstract | frontMatter/acknowledgements | frontMatter/preface" mode="contents"/>
            </xsl:if>
        </xsl:if>
        <xsl:choose>
            <xsl:when test="section1">
                <xsl:call-template name="OutputAllSectionTOC">
                    <xsl:with-param name="nLevel">
                        <xsl:value-of select="$nLevel"/>
                    </xsl:with-param>
                    <xsl:with-param name="nodesSection1" select="section1"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="section2">
                <!-- only for appendix -->
                <xsl:call-template name="OutputAllSectionTOC">
                    <xsl:with-param name="nLevel">
                        <xsl:value-of select="$nLevel"/>
                    </xsl:with-param>
                    <xsl:with-param name="nodesSection1" select="section2"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
        <xsl:call-template name="OutputChapterInCollectionBackMatterContents">
            <xsl:with-param name="nLevel" select="$nLevel"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
                  OutputAllSectionTOC
-->
    <xsl:template name="OutputAllSectionTOC">
        <xsl:param name="nLevel" select="3"/>
        <xsl:param name="nodesSection1"/>
        <xsl:if test="$nLevel!=0">
            <xsl:for-each select="$nodesSection1">
                <xsl:call-template name="OutputSectionTOC">
                    <xsl:with-param name="sLevel" select="'1'"/>
                </xsl:call-template>
                <xsl:if test="section2 and $nLevel>=2">
                    <xsl:for-each select="section2">
                        <xsl:call-template name="OutputSectionTOC">
                            <xsl:with-param name="sLevel" select="'2'"/>
                        </xsl:call-template>
                        <xsl:if test="section3 and $nLevel>=3">
                            <xsl:for-each select="section3">
                                <xsl:call-template name="OutputSectionTOC">
                                    <xsl:with-param name="sLevel" select="'3'"/>
                                </xsl:call-template>
                                <xsl:if test="section4 and $nLevel>=4">
                                    <xsl:for-each select="section4">
                                        <xsl:call-template name="OutputSectionTOC">
                                            <xsl:with-param name="sLevel" select="'4'"/>
                                        </xsl:call-template>
                                        <xsl:if test="section5 and $nLevel>=5">
                                            <xsl:for-each select="section5">
                                                <xsl:call-template name="OutputSectionTOC">
                                                    <xsl:with-param name="sLevel" select="'5'"/>
                                                </xsl:call-template>
                                                <xsl:if test="section6 and $nLevel>=6">
                                                    <xsl:for-each select="section6">
                                                        <xsl:call-template name="OutputSectionTOC">
                                                            <xsl:with-param name="sLevel" select="'6'"/>
                                                        </xsl:call-template>
                                                    </xsl:for-each>
                                                </xsl:if>
                                            </xsl:for-each>
                                        </xsl:if>
                                    </xsl:for-each>
                                </xsl:if>
                            </xsl:for-each>
                        </xsl:if>
                    </xsl:for-each>
                </xsl:if>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <!--  
        OutputAppendixTOC
    -->
    <xsl:template name="OutputAppendixTOC">
        <xsl:param name="nLevel"/>
        <xsl:call-template name="OutputAllChapterTOC">
            <xsl:with-param name="nLevel">
                <xsl:value-of select="$nLevel"/>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--  
        OutputChapterInCollectionBackMatterContents
    -->
    <xsl:template name="OutputChapterInCollectionBackMatterContents">
        <xsl:param name="nLevel"/>
        <xsl:variable name="sChapterInCollectionID" select="ancestor-or-self::chapterInCollection/@id"/>
        <xsl:for-each select="backMatter/acknowledgements">
            <xsl:call-template name="OutputTOCLine">
                <xsl:with-param name="sLink">
                    <xsl:value-of select="$sAcknowledgementsID"/>
                    <xsl:text>.</xsl:text>
                    <xsl:value-of select="$sChapterInCollectionID"/>
                </xsl:with-param>
                <xsl:with-param name="sLabel">
                    <xsl:call-template name="OutputAcknowledgementsLabel"/>
                </xsl:with-param>
                <xsl:with-param name="sIndent">
                    <tex:cmd name="leveloneindent" gr="0" nl2="0"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:for-each>
        <xsl:for-each select="backMatter/appendix">
            <xsl:call-template name="OutputAppendixTOC">
                <xsl:with-param name="nLevel" select="$nLevel"/>
            </xsl:call-template>
        </xsl:for-each>
        <xsl:for-each select="backMatter/glossary">
            <xsl:variable name="iPos" select="position()"/>
            <xsl:call-template name="OutputTOCLine">
                <xsl:with-param name="sLink">
                    <xsl:value-of select="$sGlossaryID"/>
                    <xsl:text>.</xsl:text>
                    <xsl:value-of select="$iPos"/>
                    <xsl:text>.</xsl:text>
                    <xsl:value-of select="$sChapterInCollectionID"/>
                </xsl:with-param>
                <xsl:with-param name="sLabel">
                    <xsl:call-template name="OutputGlossaryLabel"/>
                </xsl:with-param>
                <xsl:with-param name="sIndent">
                    <tex:cmd name="leveloneindent" gr="0" nl2="0"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:for-each>
        <!--        <xsl:for-each select="backMatter/endnotes">
            <xsl:call-template name="OutputTOCLine">
                <xsl:with-param name="sLink">
                    <xsl:value-of select="$sEndnotesID"/>
                    <xsl:text>.</xsl:text>
                    <xsl:value-of select="$sChapterInCollectionID"/>
                </xsl:with-param>
                <xsl:with-param name="sLabel">
                    <xsl:call-template name="OutputEndnotesLabel"/>
                </xsl:with-param>
                <xsl:with-param name="sIndent">
                <tex:cmd name="leveloneindent" gr="0" nl2="0"/>
                </xsl:with-param>
                </xsl:call-template>
        </xsl:for-each>-->
        <xsl:for-each select="backMatter/references">
            <xsl:call-template name="OutputTOCLine">
                <xsl:with-param name="sLink">
                    <xsl:value-of select="$sReferencesID"/>
                    <xsl:text>.</xsl:text>
                    <xsl:value-of select="$sChapterInCollectionID"/>
                </xsl:with-param>
                <xsl:with-param name="sLabel">
                    <xsl:call-template name="OutputReferencesLabel"/>
                </xsl:with-param>
                <xsl:with-param name="sIndent">
                    <tex:cmd name="leveloneindent" gr="0" nl2="0"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:for-each>
    </xsl:template>
    <!--  
                  OutputSectionTOC
-->
    <xsl:template name="OutputSectionTOC">
        <xsl:param name="sLevel"/>
        <!-- set level command name -->
        <xsl:variable name="sLevelName">
            <xsl:choose>
                <xsl:when test="$sLevel='1'">
                    <xsl:text>levelone</xsl:text>
                </xsl:when>
                <xsl:when test="$sLevel='2'">
                    <xsl:text>leveltwo</xsl:text>
                </xsl:when>
                <xsl:when test="$sLevel='3'">
                    <xsl:text>levelthree</xsl:text>
                </xsl:when>
                <xsl:when test="$sLevel='4'">
                    <xsl:text>levelfour</xsl:text>
                </xsl:when>
                <xsl:when test="$sLevel='5'">
                    <xsl:text>levelfive</xsl:text>
                </xsl:when>
                <xsl:when test="$sLevel='6'">
                    <xsl:text>levelsix</xsl:text>
                </xsl:when>
            </xsl:choose>
        </xsl:variable>
        <!-- figure out what the new value of the indent based on the section number itself -->
        <xsl:variable name="sSectionNumberIndentFormula">
            <xsl:call-template name="CalculateSectionNumberIndent"/>
        </xsl:variable>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
            <xsl:with-param name="sCommandToSet" select="concat($sLevelName,'indent')"/>
            <xsl:with-param name="sValue" select="$sSectionNumberIndentFormula"/>
        </xsl:call-template>
        <!-- figure out what the new value of the number width based on the section number itself -->
        <xsl:variable name="sSectionNumberWidthFormula">
            <xsl:call-template name="CalculateSectionNumberWidth"/>
        </xsl:variable>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
            <xsl:with-param name="sCommandToSet" select="concat($sLevelName,'width')"/>
            <xsl:with-param name="sValue" select="$sSectionNumberWidthFormula"/>
        </xsl:call-template>
        <!-- output the toc line -->
        <xsl:call-template name="OutputTOCLine">
            <xsl:with-param name="sLink" select="@id"/>
            <xsl:with-param name="sLabel">
                <xsl:call-template name="OutputSectionNumberAndTitle">
                    <xsl:with-param name="bIsContents" select="'Y'"/>
                    <!-- to avoid line breaks via br elements -->
                </xsl:call-template>
            </xsl:with-param>
            <xsl:with-param name="sIndent">
                <tex:cmd name="{$sLevelName}indent" gr="0" nl2="0"/>
            </xsl:with-param>
            <xsl:with-param name="sNumWidth">
                <tex:cmd name="{$sLevelName}width" gr="0" nl2="0"/>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--  
        OutputTableNumberedLabel
    -->
    <xsl:template name="OutputTableNumberedLabel">
        <xsl:variable name="label" select="exsl:node-set($lingPaper)/@tablenumberedLabel"/>
        <xsl:choose>
            <xsl:when test="string-length($label) &gt; 0">
                <xsl:value-of select="$label"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>Table </xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        OutputTableNumberedLabelAndCaption
    -->
    <xsl:template name="OutputTableNumberedLabelAndCaption">
        <xsl:param name="bDoBold" select="'Y'"/>
        <xsl:param name="bDoStyles" select="'Y'"/>
        <xsl:choose>
            <xsl:when test="table/@align='center'">
                <tex:spec cat="esc"/>
                <xsl:text>centering </xsl:text>
            </xsl:when>
            <xsl:when test="table/@align='right'">
                <tex:spec cat="esc"/>
                <xsl:text>raggedleft </xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <tex:spec cat="esc"/>
                <xsl:text>raggedright </xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="$bDoBold='Y'">
            <tex:spec cat="bg"/>
            <tex:spec cat="esc"/>
            <xsl:text>textbf</xsl:text>
            <tex:spec cat="bg"/>
        </xsl:if>
        <xsl:call-template name="OutputTableNumberedLabel"/>
        <!--        <xsl:apply-templates select="." mode="tablenumbered"/>-->
        <xsl:call-template name="GetTableNumberedNumber">
            <xsl:with-param name="tablenumbered" select="."/>
        </xsl:call-template>
        <xsl:text>&#xa0;</xsl:text>
        <xsl:if test="$bDoBold='Y'">
            <tex:spec cat="eg"/>
            <tex:spec cat="eg"/>
        </xsl:if>
        <xsl:choose>
            <xsl:when test="$bDoStyles='Y'">
                <xsl:apply-templates select="table/caption | table/endCaption | caption" mode="show">
                    <xsl:with-param name="bDoLineBreak" select="'N'"/>
                </xsl:apply-templates>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="table/caption | table/endCaption | caption" mode="contents"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        OutputTOCLine
    -->
    <xsl:template name="OutputTOCLine">
        <xsl:param name="sLink"/>
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
        <xsl:if test="contains(@XeLaTeXSpecial,'contentsbreak')">
            <tex:cmd name="pagebreak" nl2="0"/>
        </xsl:if>
        <xsl:call-template name="DoInternalHyperlinkBegin">
            <xsl:with-param name="sName" select="$sLink"/>
        </xsl:call-template>
        <tex:cmd name="XLingPaperdottedtocline" nl2="1">
            <tex:parm>
                <xsl:copy-of select="$sIndent"/>
            </tex:parm>
            <tex:parm>
                <xsl:copy-of select="$sNumWidth"/>
            </tex:parm>
            <tex:parm>
                <xsl:copy-of select="$sLabel"/>
            </tex:parm>
            <tex:parm>
                <xsl:variable name="sPage" select="document($sTableOfContentsFile)/toc/tocline[@ref=translate($sLink,$sIDcharsToMap,$sIDcharsMapped)]/@page"/>
                <xsl:choose>
                    <xsl:when test="$sPage">
                        <xsl:value-of select="$sPage"/>
                    </xsl:when>
                    <xsl:otherwise>??</xsl:otherwise>
                </xsl:choose>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="DoInternalHyperlinkEnd"/>
    </xsl:template>
    <!--  
      SetFonts
   -->
    <xsl:template name="SetFonts">
        <tex:cmd name="setmainfont" nl2="1">
            <tex:parm>
                <xsl:value-of select="$sDefaultFontFamily"/>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="DefineAFont">
            <xsl:with-param name="sFontName" select="'MainFont'"/>
            <xsl:with-param name="sBaseFontName" select="$sDefaultFontFamily"/>
            <xsl:with-param name="sPointSize" select="$sBasicPointSize"/>
        </xsl:call-template>
        <xsl:call-template name="DefineAFontFamily">
            <xsl:with-param name="sFontFamilyName" select="'HeaderFooterFontFamily'"/>
            <xsl:with-param name="sBaseFontName" select="$sDefaultFontFamily"/>
        </xsl:call-template>
        <xsl:call-template name="DefineAFontFamily">
            <xsl:with-param name="sFontFamilyName" select="'TitleFontFamily'"/>
            <xsl:with-param name="sBaseFontName" select="$sDefaultFontFamily"/>
        </xsl:call-template>
        <xsl:call-template name="DefineAFontFamily">
            <xsl:with-param name="sFontFamilyName" select="'SubtitleFontFamily'"/>
            <xsl:with-param name="sBaseFontName" select="$sDefaultFontFamily"/>
        </xsl:call-template>
        <xsl:call-template name="DefineAFontFamily">
            <xsl:with-param name="sFontFamilyName" select="'AuthorFontFamily'"/>
            <xsl:with-param name="sBaseFontName" select="$sDefaultFontFamily"/>
        </xsl:call-template>
        <xsl:call-template name="DefineAFontFamily">
            <xsl:with-param name="sFontFamilyName" select="'AffiliationFontFamily'"/>
            <xsl:with-param name="sBaseFontName" select="$sDefaultFontFamily"/>
        </xsl:call-template>
        <xsl:call-template name="DefineAFontFamily">
            <xsl:with-param name="sFontFamilyName" select="'EmailAddressFontFamily'"/>
            <xsl:with-param name="sBaseFontName" select="$sDefaultFontFamily"/>
        </xsl:call-template>
        <xsl:call-template name="DefineAFontFamily">
            <xsl:with-param name="sFontFamilyName" select="'DateFontFamily'"/>
            <xsl:with-param name="sBaseFontName" select="$sDefaultFontFamily"/>
        </xsl:call-template>
        <xsl:call-template name="DefineAFontFamily">
            <xsl:with-param name="sFontFamilyName" select="'ChapterFontFamily'"/>
            <xsl:with-param name="sBaseFontName" select="$sDefaultFontFamily"/>
        </xsl:call-template>
        <xsl:call-template name="DefineAFontFamily">
            <xsl:with-param name="sFontFamilyName" select="'SectionLevelOneFontFamily'"/>
            <xsl:with-param name="sBaseFontName" select="$sDefaultFontFamily"/>
        </xsl:call-template>
        <xsl:call-template name="DefineAFontFamily">
            <xsl:with-param name="sFontFamilyName" select="'SectionLevelTwoFontFamily'"/>
            <xsl:with-param name="sBaseFontName" select="$sDefaultFontFamily"/>
        </xsl:call-template>
        <xsl:call-template name="DefineAFontFamily">
            <xsl:with-param name="sFontFamilyName" select="'SectionLevelThreeFontFamily'"/>
            <xsl:with-param name="sBaseFontName" select="$sDefaultFontFamily"/>
        </xsl:call-template>
        <xsl:call-template name="DefineAFontFamily">
            <xsl:with-param name="sFontFamilyName" select="'SectionLevelFourFontFamily'"/>
            <xsl:with-param name="sBaseFontName" select="$sDefaultFontFamily"/>
        </xsl:call-template>
        <xsl:call-template name="DefineAFontFamily">
            <xsl:with-param name="sFontFamilyName" select="'SectionLevelFiveFontFamily'"/>
            <xsl:with-param name="sBaseFontName" select="$sDefaultFontFamily"/>
        </xsl:call-template>
        <xsl:call-template name="DefineAFontFamily">
            <xsl:with-param name="sFontFamilyName" select="'SectionLevelSixFontFamily'"/>
            <xsl:with-param name="sBaseFontName" select="$sDefaultFontFamily"/>
        </xsl:call-template>
        <xsl:if test="$abbreviations and string-length(exsl:node-set($abbreviations)/@font-family) &gt; 0">
            <xsl:call-template name="DefineAFontFamily">
                <xsl:with-param name="sFontFamilyName">
                    <xsl:text>Lang</xsl:text>
                    <xsl:value-of select="$sXLingPaperAbbreviation"/>
                    <xsl:text>FontFamily</xsl:text>
                </xsl:with-param>
                <xsl:with-param name="sBaseFontName" select="exsl:node-set($abbreviations)/@font-family"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:if test="$glossaryTerms and string-length(exsl:node-set($glossaryTerms)/@font-family) &gt; 0">
            <xsl:call-template name="DefineAFontFamily">
                <xsl:with-param name="sFontFamilyName">
                    <xsl:text>Lang</xsl:text>
                    <xsl:value-of select="$sXLingPaperGlossaryTerm"/>
                    <xsl:text>FontFamily</xsl:text>
                </xsl:with-param>
                <xsl:with-param name="sBaseFontName" select="exsl:node-set($glossaryTerms)/@font-family"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="DefineLangaugeAndTypeFonts"/>
    </xsl:template>
    <!--  
      SetHeaderFooter
   -->
    <xsl:template name="SetHeaderFooter">
        <tex:cmd name="pagestyle" nl2="1">
            <tex:parm>fancy</tex:parm>
        </tex:cmd>
        <tex:cmd name="fancyhf" nl2="1"/>
        <tex:cmd name="fancyhead" nl2="1">
            <tex:opt>RO,LE</tex:opt>
            <tex:parm>
                <tex:cmd name="HeaderFooterFontFamily">
                    <tex:parm>
                        <tex:cmd name="small">
                            <tex:parm>
                                <tex:cmd name="textit">
                                    <tex:parm>
                                        <tex:cmd name="thepage" gr="0"/>
                                    </tex:parm>
                                </tex:cmd>
                            </tex:parm>
                        </tex:cmd>
                    </tex:parm>
                </tex:cmd>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="fancyhead" nl2="1">
            <tex:opt>RE</tex:opt>
            <tex:parm>
                <tex:cmd name="HeaderFooterFontFamily">
                    <tex:parm>
                        <tex:cmd name="small">
                            <tex:parm>
                                <tex:cmd name="textit">
                                    <tex:parm>
                                        <tex:cmd name="leftmark" gr="0"/>
                                    </tex:parm>
                                </tex:cmd>
                            </tex:parm>
                        </tex:cmd>
                    </tex:parm>
                </tex:cmd>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="fancyhead" nl2="1">
            <tex:opt>LO</tex:opt>
            <tex:parm>
                <tex:cmd name="HeaderFooterFontFamily">
                    <tex:parm>
                        <tex:cmd name="small">
                            <tex:parm>
                                <tex:cmd name="textit">
                                    <tex:parm>
                                        <tex:cmd name="rightmark" gr="0"/>
                                    </tex:parm>
                                </tex:cmd>
                            </tex:parm>
                        </tex:cmd>
                    </tex:parm>
                </tex:cmd>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="SetHeaderFooterRuleWidths"/>
        <tex:cmd name="fancypagestyle" nl2="1">
            <tex:parm>plain</tex:parm>
            <tex:parm>
                <tex:cmd name="fancyhf" nl2="1"/>
                <tex:cmd name="fancyfoot" nl2="1">
                    <tex:opt>C</tex:opt>
                    <tex:parm>
                        <tex:cmd name="HeaderFooterFontFamily">
                            <tex:parm>
                                <tex:cmd name="small">
                                    <tex:parm>
                                        <tex:cmd name="textit">
                                            <tex:parm>
                                                <tex:cmd name="thepage" gr="0"/>
                                            </tex:parm>
                                        </tex:cmd>
                                    </tex:parm>
                                </tex:cmd>
                            </tex:parm>
                        </tex:cmd>
                    </tex:parm>
                </tex:cmd>
                <xsl:call-template name="SetHeaderFooterRuleWidths"/>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SingleSpaceAdjust
    -->
    <xsl:template name="SingleSpaceAdjust">
        <tex:cmd name="hspace*">
            <tex:parm>-.25em</tex:parm>
        </tex:cmd>
    </xsl:template>
    <xsl:template match="interlinearSource" mode="contents">
        <xsl:apply-templates/>
    </xsl:template>
    <!-- ===========================================================
        ELEMENTS TO IGNORE
        =========================================================== -->
    <xsl:template match="language"/>
    <xsl:template match="citation[parent::selectedBibliography]"/>
    <xsl:template match="authorContacts"/>
    <xsl:template match="interlinearSource"/>
    <xsl:template match="textInfo/shortTitle"/>
    <xsl:template match="styles"/>
    <xsl:template match="style"/>
    <xsl:template match="dd"/>
    <xsl:template match="referencedInterlinearTexts"/>
    <xsl:template match="term"/>
    <xsl:template match="type"/>
    <!-- ===========================================================
          TRANSFORMS TO INCLUDE
        =========================================================== -->
    <xsl:include href="XLingPapCommon.xsl"/>
    <xsl:include href="XLingPapCannedCommon.xsl"/>
    <xsl:include href="XLingPapXeLaTeXCommon.xsl"/>
</xsl:stylesheet>
