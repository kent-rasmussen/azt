<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.1" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:fo="http://www.w3.org/1999/XSL/Format" xmlns:tex="http://getfo.sourceforge.net/texml/ns1"
    xmlns:saxon="http://icl.com/saxon" xmlns:exsl="http://exslt.org/common">
    <xsl:output method="xml" version="1.0" encoding="utf-8" indent="no"/>
    <!-- ===========================================================
      Parameterized Variables
      =========================================================== -->
    <!-- the following is actually  the main source file path and name without extension -->
    <xsl:param name="sMainSourcePath" select="'C:/Documents and Settings/Andy Black/My Documents/XLingPap/XeTeX'"/>
    <xsl:param name="sMainSourceFile" select="'TestTeXPaperTeXML'"/>
    <xsl:param name="sDirectorySlash" select="'/'"/>
    <xsl:param name="sTableOfContentsFile" select="concat($sMainSourcePath, $sDirectorySlash, 'XLingPaperPDFTemp', $sDirectorySlash, $sMainSourceFile,'.toc')"/>
    <xsl:param name="sIndexFile" select="concat($sMainSourcePath, $sDirectorySlash, 'XLingPaperPDFTemp', $sDirectorySlash, $sMainSourceFile,'.idx')"/>
    <xsl:param name="sFOProcessor">XEP</xsl:param>
    <xsl:param name="sXeLaTeXVersion">2010</xsl:param>
    <xsl:param name="bUseBookTabs" select="'Y'"/>
    <xsl:variable name="sPageWidth" select="string(exsl:node-set($pageLayoutInfo)/pageWidth)"/>
    <xsl:variable name="sPageHeight" select="string(exsl:node-set($pageLayoutInfo)/pageHeight)"/>
    <xsl:variable name="sPageTopMargin" select="string(exsl:node-set($pageLayoutInfo)/pageTopMargin)"/>
    <xsl:variable name="sPageBottomMargin" select="string(exsl:node-set($pageLayoutInfo)/pageBottomMargin)"/>
    <xsl:variable name="sPageInsideMargin" select="string(exsl:node-set($pageLayoutInfo)/pageInsideMargin)"/>
    <xsl:variable name="sPageOutsideMargin" select="string(exsl:node-set($pageLayoutInfo)/pageOutsideMargin)"/>
    <xsl:variable name="sHeaderMargin" select="string(exsl:node-set($pageLayoutInfo)/headerMargin)"/>
    <xsl:variable name="sFooterMargin" select="string(exsl:node-set($pageLayoutInfo)/footerMargin)"/>
    <xsl:variable name="sParagraphIndent" select="string(exsl:node-set($pageLayoutInfo)/paragraphIndent)"/>
    <xsl:variable name="sBlockQuoteIndent" select="string(exsl:node-set($pageLayoutInfo)/blockQuoteIndent)"/>
    <xsl:variable name="sDefaultFontFamily" select="string(exsl:node-set($pageLayoutInfo)/defaultFontFamily)"/>
    <xsl:variable name="sDefaultFontFamilyXeLaTeXSpecial" select="string(exsl:node-set($pageLayoutInfo)/defaultFontFamily/@XeLaTeXSpecial)"/>
    <xsl:variable name="sLaTeXBasicPointSize">
        <xsl:choose>
            <xsl:when test="$sBasicPointSize='10'">10</xsl:when>
            <xsl:when test="$sBasicPointSize='11'">11</xsl:when>
            <xsl:when test="$sBasicPointSize='12'">12</xsl:when>
            <xsl:when test="$chapters">10</xsl:when>
            <xsl:otherwise>12</xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="sFootnotePointSize" select="string(exsl:node-set($pageLayoutInfo)/footnotePointSize)"/>
    <!--    <xsl:variable name="frontMatterLayoutInfo" select="exsl:node-set($publisherStyleSheet)/frontMatterLayout"/>-->
    <!--    <xsl:variable name="bodyLayoutInfo" select="exsl:node-set($publisherStyleSheet)/bodyLayout"/>-->
    <xsl:variable name="chapterTitleOnEvenPage" select="exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles/descendant::*[name()='chapterTitle' or name()='chapterNumber'][ancestor::headerFooterEvenPage]"/>
    <xsl:variable name="chapterTitleOnOddPage" select="exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles/descendant::*[name()='chapterTitle' or name()='chapterNumber'][ancestor::headerFooterOddPage]"/>
    <xsl:variable name="sectionTitleOnEvenPage" select="exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles/descendant::*[name()='sectionTitle' or name()='sectionNumber'][ancestor::headerFooterEvenPage]"/>
    <xsl:variable name="sectionTitleOnOddPage" select="exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles/descendant::*[name()='sectionTitle' or name()='sectionNumber'][ancestor::headerFooterOddPage]"/>
    <xsl:variable name="iAffiliationLayouts" select="count(exsl:node-set($frontMatterLayoutInfo)/affiliationLayout)"/>
    <xsl:variable name="iAuthorLayouts" select="count(exsl:node-set($frontMatterLayoutInfo)/authorLayout)"/>
    <xsl:variable name="iEmailAddressLayouts" select="count(exsl:node-set($frontMatterLayoutInfo)/emailAddressLayout)"/>
    <xsl:variable name="sExampleIndentBefore" select="string(exsl:node-set($contentLayoutInfo)/exampleLayout/@indent-before)"/>
    <xsl:variable name="sExampleIndentAfter" select="string(exsl:node-set($contentLayoutInfo)/exampleLayout/@indent-after)"/>
    <xsl:variable name="lineSpacing" select="exsl:node-set($pageLayoutInfo)/lineSpacing"/>
    <xsl:variable name="sLineSpacing" select="exsl:node-set($lineSpacing)/@linespacing"/>
    <xsl:variable name="sSection1PointSize" select="'12'"/>
    <xsl:variable name="sSection2PointSize" select="'10'"/>
    <xsl:variable name="sSection3PointSize" select="'10'"/>
    <xsl:variable name="sSection4PointSize" select="'10'"/>
    <xsl:variable name="sSection5PointSize" select="'10'"/>
    <xsl:variable name="sSection6PointSize" select="'10'"/>
    <xsl:variable name="sBackMatterItemTitlePointSize" select="'12'"/>
    <xsl:variable name="sLinkColor" select="exsl:node-set($pageLayoutInfo)/linkLayout/@color"/>
    <xsl:variable name="sLinkTextDecoration" select="exsl:node-set($pageLayoutInfo)/linkLayout/@decoration"/>
    <xsl:variable name="bDoDebug" select="'n'"/>
    <!-- need a better solution for the following -->
    <xsl:variable name="sVernacularFontFamily" select="'Arial Unicode MS'"/>
    <!--
        sInterlinearSourceStyle:
        The default is AfterFirstLine (immediately after the last item in the first line)
        The other possibilities are AfterFree (immediately after the free translation, on the same line)
        and UnderFree (on the line immediately after the free translation)
    -->
    <xsl:variable name="sInterlinearSourceStyle" select="exsl:node-set($contentLayoutInfo)/interlinearSourceStyle/@interlinearsourcestyle"/>
    <xsl:variable name="styleSheetFigureLabelLayout" select="exsl:node-set($contentLayoutInfo)/figureLayout/figureLabelLayout"/>
    <xsl:variable name="styleSheetFigureNumberLayout" select="exsl:node-set($contentLayoutInfo)/figureLayout/figureNumberLayout"/>
    <xsl:variable name="styleSheetFigureCaptionLayout" select="exsl:node-set($contentLayoutInfo)/figureLayout/figureCaptionLayout"/>
    <xsl:variable name="sSpaceBetweenFigureAndCaption" select="normalize-space(exsl:node-set($contentLayoutInfo)/figureLayout/@spaceBetweenFigureAndCaption)"/>
    <xsl:variable name="styleSheetTableNumberedLabelLayout" select="exsl:node-set($contentLayoutInfo)/tablenumberedLayout/tablenumberedLabelLayout"/>
    <xsl:variable name="styleSheetTableNumberedNumberLayout" select="exsl:node-set($contentLayoutInfo)/tablenumberedLayout/tablenumberedNumberLayout"/>
    <xsl:variable name="styleSheetTableNumberedCaptionLayout" select="exsl:node-set($contentLayoutInfo)/tablenumberedLayout/tablenumberedCaptionLayout"/>
    <xsl:variable name="sSpaceBetweenTableAndCaption" select="normalize-space(exsl:node-set($contentLayoutInfo)/tablenumberedLayout/@spaceBetweenTableAndCaption)"/>
    <xsl:variable name="iMagnificationFactor">
        <xsl:variable name="sAdjustedFactor" select="normalize-space(exsl:node-set($contentLayoutInfo)/magnificationFactor)"/>
        <xsl:choose>
            <xsl:when test="string-length($sAdjustedFactor) &gt; 0 and $sAdjustedFactor!='1' and number($sAdjustedFactor)!='NaN'">
                <xsl:value-of select="$sAdjustedFactor"/>
            </xsl:when>
            <xsl:otherwise>1</xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="sListInitialHorizontalOffset">
        <xsl:variable name="sIndentBefore" select="normalize-space(exsl:node-set($contentLayoutInfo)/listLayout/@indent-before)"/>
        <xsl:choose>
            <xsl:when test="string-length($sIndentBefore)&gt;0">
                <xsl:value-of select="$sIndentBefore"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>0pt</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="sGraphiteForFontName" select="'Graphite'"/>
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
                <xsl:value-of select="exsl:node-set($contentLayoutInfo)/exampleLayout/@indent-before"/>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="iExampleIndentAfterInPoints">
        <xsl:call-template name="ConvertUnitOfMeasureToPoints">
            <xsl:with-param name="sUnitOfMeasure">
                <xsl:value-of select="exsl:node-set($contentLayoutInfo)/exampleLayout/@indent-after"/>
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
      Variables
      =========================================================== -->
    <xsl:variable name="references" select="//references"/>
    <!-- ===========================================================
      MAIN BODY
      =========================================================== -->
    <xsl:template match="//lingPaper">
        <tex:TeXML>
            <xsl:comment> generated by XLingPapPublisherStylesheetXeLaTeX.xsl Version <xsl:value-of select="$sVersion"/>&#x20;</xsl:comment>
            <xsl:if test="$iMagnificationFactor!=1">
                <tex:spec cat="esc"/>
                <xsl:text>mag </xsl:text>
                <xsl:value-of select="$iMagnificationFactor * 1000"/>
                <xsl:text>&#x0a;</xsl:text>
            </xsl:if>
            <tex:cmd name="documentclass" nl2="1">
                <!--            <tex:opt>a4paper</tex:opt>-->
                <tex:opt>
                    <xsl:value-of select="$sLaTeXBasicPointSize"/>
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
            <xsl:call-template name="SetFootnoteRule"/>
            <tex:cmd name="setlength" nl2="1">
                <tex:parm>
                    <tex:cmd name="parindent" gr="0"/>
                </tex:parm>
                <tex:parm>
                    <xsl:value-of select="$sParagraphIndent"/>
                </tex:parm>
            </tex:cmd>
            <xsl:if test="$sLineSpacing and $sLineSpacing!='single'">
                <xsl:choose>
                    <xsl:when test="$sLineSpacing='double'">
                        <tex:cmd name="doublespacing" gr="0" nl2="1"/>
                    </xsl:when>
                    <xsl:when test="$sLineSpacing='spaceAndAHalf'">
                        <tex:cmd name="onehalfspacing" gr="0" nl2="1"/>
                    </xsl:when>
                </xsl:choose>
            </xsl:if>
            <xsl:call-template name="SetZeroWidthSpaceHandling"/>
            <xsl:call-template name="CreateClearEmptyDoublePageCommand"/>
            <xsl:call-template name="DefineBlockQuoteWithIndent"/>
            <xsl:call-template name="SetClubWidowPenalties"/>
            <xsl:call-template name="SetAbbrInTableBaselineskip"/>
            <xsl:if test="exsl:node-set($pageLayoutInfo)/@showLineNumbers='yes'">
                <tex:cmd name="def" gr="0"/>
                <tex:cmd name="linenumberfont" gr="0">
                    <tex:parm>
                        <tex:cmd name="MainFont" gr="0"/>
                        <tex:cmd name="tiny" gr="0"/>
                    </tex:parm>
                </tex:cmd>
            </xsl:if>
            <tex:env name="document">
                <xsl:if test="exsl:node-set($pageLayoutInfo)/@showLineNumbers='yes'">
                    <tex:cmd name="linenumbers" gr="0" nl2="1"/>
                </xsl:if>
                <!-- add some glue to baselineskip -->
                <tex:cmd name="baselineskip" gr="0"/>
                <xsl:text>=</xsl:text>
                <tex:cmd name="glueexpr" gr="0"/>
                <tex:cmd name="baselineskip" gr="0"/>
                <xsl:text> + 0pt plus 2pt minus 1pt</xsl:text>
                <tex:cmd name="relax" gr="0" nl2="1"/>
                <tex:cmd name="renewcommand" nl2="1">
                    <tex:parm>
                        <tex:spec cat="esc"/>
                        <xsl:text>footnotesize</xsl:text>
                    </tex:parm>
                    <tex:parm>
                        <xsl:call-template name="HandleFontSize">
                            <xsl:with-param name="sSize">
                                <xsl:value-of select="exsl:node-set($pageLayoutInfo)/footnotePointSize"/>
                                <xsl:text>pt</xsl:text>
                            </xsl:with-param>
                        </xsl:call-template>
                    </tex:parm>
                </tex:cmd>
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
                <xsl:call-template name="SetListLengthWidths"/>
                <xsl:if test="exsl:node-set($contentLayoutInfo)/figureLayout/@listOfFiguresUsesFigureAndPageHeaders='yes'">
                    <xsl:call-template name="SetListOfWidths"/>
                </xsl:if>
                <xsl:call-template name="SetXLingPaperNeedSpaceMacro"/>
                <xsl:call-template name="SetXLingPaperListItemMacro"/>
                <xsl:call-template name="SetXLingPaperBlockQuoteMacro"/>
                <xsl:call-template name="SetXLingPaperExampleMacro"/>
                <xsl:call-template name="SetXLingPaperExampleInTableMacro"/>
                <xsl:call-template name="SetXLingPaperFreeMacro"/>
                <xsl:call-template name="SetXLingPaperListInterlinearMacro"/>
                <xsl:call-template name="SetXLingPaperListInterlinearInTableMacro"/>
                <xsl:call-template name="SetXLingPaperExampleFreeIndent"/>
                <xsl:call-template name="SetXLingPaperAdjustHeaderInListInterlinearWithISOCodes"/>
                <xsl:if test="exsl:node-set($referencesLayoutInfo)/@useAuthorOverDateStyle='yes'">
                    <xsl:call-template name="SetXLingPaperEntrySpaceAuthorOverDateMacro"/>
                </xsl:if>
                <xsl:if test="exsl:node-set($lingPaper)/@automaticallywrapinterlinears='yes'">
                    <xsl:call-template name="SetXLingPaperAlignedWordSpacing"/>
                    <xsl:call-template name="SetXLingPaperAdjustIndentOfNonInitialFreeLine"/>
                </xsl:if>
                <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespaceendnotes!='yes' and not(exsl:node-set($backMatterLayoutInfo)/useEndNotesLayout)">
                    <xsl:call-template name="SetFootnoteLayout"/>
                </xsl:if>
                <xsl:if test="contains($sXeLaTeXVersion,'2020') or exsl:node-set($lingPaper)/@useImageWidthSetToWidthOfExampleFigureOrChart='yes'">
                    <xsl:call-template name="SetImgWidths"/>
                </xsl:if>
                <xsl:variable name="sSpaceBetweenTextAndLine" select="normalize-space(exsl:node-set($pageLayoutInfo)/footnoteLine/@spacebetweentextandline)"/>
                <xsl:if test="string-length($sSpaceBetweenTextAndLine) &gt; 0">
                    <tex:cmd name="setlength">
                        <tex:parm>
                            <tex:cmd name="skip" gr="0"/>
                            <tex:cmd name="footins" gr="0"/>
                        </tex:parm>
                        <tex:parm>
                            <xsl:value-of select="$sSpaceBetweenTextAndLine"/>
                            <xsl:text> plus 5pt minus 2pt</xsl:text>
                        </tex:parm>
                    </tex:cmd>
                </xsl:if>
                <tex:cmd name="raggedbottom" gr="0" nl2="1"/>
                <tex:cmd name="pagestyle">
                    <tex:parm>fancy</tex:parm>
                </tex:cmd>
                <xsl:call-template name="HandleHyphenationExceptionsFile"/>
                <xsl:if test="$sBasicPointSize!=$sLaTeXBasicPointSize and $sLineSpacing and $sLineSpacing!='single'">
                    <xsl:call-template name="SetXLingPaperSingleSpacingMacro"/>
                </xsl:if>
                <xsl:choose>
                    <xsl:when test="contains($sDefaultFontFamilyXeLaTeXSpecial,'graphite')">
                        <tex:spec cat="esc"/>
                        <xsl:text>XLingPaper</xsl:text>
                        <xsl:value-of select="translate($sDefaultFontFamily,$sDigits, $sLetters)"/>
                        <xsl:text>FontFamily</xsl:text>
                        <xsl:value-of select="$sGraphiteForFontName"/>
                        <xsl:call-template name="HandleXeLaTeXSpecialFontFeatureForFontName">
                            <xsl:with-param name="sList" select="$sDefaultFontFamilyXeLaTeXSpecial"/>
                        </xsl:call-template>
                        <xsl:call-template name="HandleFontSize">
                            <xsl:with-param name="sSize" select="concat($sBasicPointSize,'pt')"/>
                            <xsl:with-param name="sFontFamily" select="$sDefaultFontFamily"/>
                        </xsl:call-template>
                        <xsl:call-template name="ProcessDocument"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <tex:env name="MainFont">
                            <xsl:call-template name="ProcessDocument"/>
                        </tex:env>
                    </xsl:otherwise>
                </xsl:choose>
            </tex:env>
        </tex:TeXML>
    </xsl:template>
    <xsl:template name="CreateClearEmptyDoublePageCommand">
        <tex:cmd name="let" gr="0" nl1="1"/>
        <tex:cmd name="origdoublepage" gr="0"/>
        <tex:cmd name="cleardoublepage" gr="0" nl2="1"/>
        <tex:cmd name="newcommand">
            <tex:parm>
                <tex:cmd name="clearemptydoublepage" gr="0"/>
            </tex:parm>
            <tex:parm>
                <tex:cmd name="clearpage">
                    <tex:parm>
                        <tex:cmd name="pagestyle">
                            <tex:parm>empty</tex:parm>
                        </tex:cmd>
                        <tex:cmd name="origdoublepage" gr="0"/>
                    </tex:parm>
                </tex:cmd>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!-- ===========================================================
      FRONTMATTER
      =========================================================== -->
    <xsl:template match="frontMatter">
        <xsl:param name="frontMatterLayout" select="$frontMatterLayoutInfo"/>
        <xsl:variable name="frontMatter" select="."/>
        <xsl:choose>
            <xsl:when test="$bIsBook">
                <xsl:call-template name="DoBookFrontMatterFirstStuffPerLayout">
                    <xsl:with-param name="frontMatter" select="."/>
                    <xsl:with-param name="frontMatterLayout" select="$frontMatterLayout"/>
                </xsl:call-template>
                <xsl:if test="not(ancestor::chapterInCollection)">
                    <xsl:call-template name="DoBookFrontMatterPagedStuffPerLayout">
                        <xsl:with-param name="frontMatter" select="."/>
                        <xsl:with-param name="frontMatterLayout" select="$frontMatterLayout"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="exsl:node-set($frontMatterLayout)/headerFooterPageStyles">
                    <tex:cmd name="pagestyle">
                        <tex:parm>frontmatter</tex:parm>
                    </tex:cmd>
                </xsl:if>
                <xsl:call-template name="DoFrontMatterPerLayout">
                    <xsl:with-param name="frontMatter" select="."/>
                    <xsl:with-param name="frontMatterLayout" select="$frontMatterLayout"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="ancestor::chapterInCollection">
            <!-- need to set header/footer to use a blank for any section portion now that the section part may have been set to a front matter item -->
            <xsl:call-template name="DoRunningHeader">
                <xsl:with-param name="sHeader">
                    <xsl:text/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--
      title
      -->
    <xsl:template match="title">
        <xsl:if test="exsl:node-set($frontMatterLayoutInfo)/titleHeaderFooterPageStyles">
            <tex:cmd name="pagestyle">
                <tex:parm>frontmattertitle</tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:if test="$bIsBook">
            <tex:group>
                <xsl:call-template name="DoTitleFormatInfo">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/titleLayout"/>
                </xsl:call-template>
                <xsl:if test="descendant::endnote and exsl:node-set($frontMatterLayoutInfo)/titleLayout/@useFootnoteSymbols='yes'">
                    <xsl:call-template name="UseFootnoteSymbols"/>
                </xsl:if>
                <xsl:apply-templates select="child::node()[name()!='endnote']"/>
                <xsl:variable name="contentForThisElement">
                    <xsl:apply-templates/>
                </xsl:variable>
                <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/titleLayout"/>
                </xsl:call-template>
                <xsl:call-template name="DoTitleFormatInfoEnd">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/titleLayout"/>
                    <xsl:with-param name="contentOfThisElement" select="$contentForThisElement"/>
                </xsl:call-template>
            </tex:group>
            <tex:cmd name="par" nl2="1"/>
            <xsl:call-template name="DoSpaceAfter">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/titleLayout"/>
            </xsl:call-template>
            <xsl:apply-templates select="following-sibling::subtitle"/>
        </xsl:if>
        <tex:group>
            <xsl:call-template name="DoTitleFormatInfo">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/titleLayout"/>
                <xsl:with-param name="originalContext" select="."/>
            </xsl:call-template>
            <xsl:if test="descendant::endnote and exsl:node-set($frontMatterLayoutInfo)/titleLayout/@useFootnoteSymbols='yes'">
                <xsl:call-template name="UseFootnoteSymbols"/>
            </xsl:if>
            <xsl:apply-templates/>
            <xsl:variable name="contentForThisElement">
                <xsl:apply-templates/>
            </xsl:variable>
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/titleLayout"/>
            </xsl:call-template>
            <xsl:call-template name="DoTitleFormatInfoEnd">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/titleLayout"/>
                <xsl:with-param name="contentOfThisElement" select="$contentForThisElement"/>
                <xsl:with-param name="originalContext" select="."/>
            </xsl:call-template>
        </tex:group>
        <tex:cmd name="par" nl2="1"/>
        <xsl:call-template name="DoSpaceAfter">
            <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/titleLayout"/>
        </xsl:call-template>
    </xsl:template>
    <xsl:template match="title" mode="contentOnly">
        <xsl:apply-templates/>
    </xsl:template>
    <!--
      subtitle
      -->
    <xsl:template match="subtitle">
        <tex:group>
            <xsl:call-template name="DoTitleFormatInfo">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/subtitleLayout"/>
            </xsl:call-template>
            <xsl:apply-templates/>
            <xsl:variable name="contentForThisElement">
                <xsl:apply-templates/>
            </xsl:variable>
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/subtitleLayout"/>
            </xsl:call-template>
            <xsl:call-template name="DoTitleFormatInfoEnd">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/subtitleLayout"/>
                <xsl:with-param name="contentOfThisElement" select="$contentForThisElement"/>
            </xsl:call-template>
        </tex:group>
        <tex:cmd name="par" nl2="1"/>
    </xsl:template>
    <!--
      author
      -->
    <xsl:template match="author">
        <xsl:param name="authorLayoutToUse"/>
        <tex:group>
            <xsl:if test="descendant::endnote">
                <xsl:call-template name="UseFootnoteSymbols"/>
            </xsl:if>
            <xsl:call-template name="DoFrontMatterFormatInfoBegin">
                <xsl:with-param name="layoutInfo" select="$authorLayoutToUse"/>
            </xsl:call-template>
            <xsl:apply-templates/>
            <xsl:variable name="contentForThisElement">
                <xsl:apply-templates/>
            </xsl:variable>
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="$authorLayoutToUse"/>
            </xsl:call-template>
            <xsl:call-template name="DoFrontMatterFormatInfoEnd">
                <xsl:with-param name="layoutInfo" select="$authorLayoutToUse"/>
                <xsl:with-param name="contentOfThisElement" select="$contentForThisElement"/>
            </xsl:call-template>
        </tex:group>
        <tex:cmd name="par" nl2="1"/>
        <xsl:call-template name="DoSpaceAfter">
            <xsl:with-param name="layoutInfo" select="$authorLayoutToUse"/>
        </xsl:call-template>
    </xsl:template>
    <xsl:template match="author" mode="contentOnly">
        <xsl:choose>
            <xsl:when test="preceding-sibling::author and not(following-sibling::author)">
                <xsl:text> and </xsl:text>
            </xsl:when>
            <xsl:when test="preceding-sibling::author">
                <xsl:text>, </xsl:text>
            </xsl:when>
        </xsl:choose>
        <xsl:apply-templates/>
    </xsl:template>
    <!--
      affiliation
      -->
    <xsl:template match="affiliation">
        <xsl:param name="affiliationLayoutToUse"/>
        <tex:group>
            <xsl:call-template name="DoFrontMatterFormatInfoBegin">
                <xsl:with-param name="layoutInfo" select="$affiliationLayoutToUse"/>
            </xsl:call-template>
            <xsl:apply-templates/>
            <xsl:variable name="contentForThisElement">
                <xsl:apply-templates/>
            </xsl:variable>
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="$affiliationLayoutToUse"/>
            </xsl:call-template>
            <xsl:call-template name="DoFrontMatterFormatInfoEnd">
                <xsl:with-param name="layoutInfo" select="$affiliationLayoutToUse"/>
                <xsl:with-param name="contentOfThisElement" select="$contentForThisElement"/>
            </xsl:call-template>
        </tex:group>
        <tex:cmd name="par" nl2="1"/>
        <xsl:call-template name="DoSpaceAfter">
            <xsl:with-param name="layoutInfo" select="$affiliationLayoutToUse"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        emailAddress
    -->
    <xsl:template match="emailAddress">
        <xsl:param name="emailAddressLayoutToUse"/>
        <tex:group>
            <xsl:call-template name="DoFrontMatterFormatInfoBegin">
                <xsl:with-param name="layoutInfo" select="$emailAddressLayoutToUse"/>
            </xsl:call-template>
            <xsl:apply-templates/>
            <xsl:variable name="contentForThisElement">
                <xsl:apply-templates/>
            </xsl:variable>
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="$emailAddressLayoutToUse"/>
            </xsl:call-template>
            <xsl:call-template name="DoFrontMatterFormatInfoEnd">
                <xsl:with-param name="layoutInfo" select="$emailAddressLayoutToUse"/>
                <xsl:with-param name="contentOfThisElement" select="$contentForThisElement"/>
            </xsl:call-template>
        </tex:group>
        <tex:cmd name="par" nl2="1"/>
        <xsl:call-template name="DoSpaceAfter">
            <xsl:with-param name="layoutInfo" select="$emailAddressLayoutToUse"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        date
    -->
    <xsl:template match="date">
        <xsl:param name="frontMatterLayout" select="$frontMatterLayoutInfo"/>
        <tex:group>
            <xsl:call-template name="DoFrontMatterFormatInfoBegin">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayout)/dateLayout"/>
            </xsl:call-template>
            <xsl:apply-templates/>
            <xsl:variable name="contentForThisElement">
                <xsl:apply-templates/>
            </xsl:variable>
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayout)/dateLayout"/>
            </xsl:call-template>
            <xsl:call-template name="DoFrontMatterFormatInfoEnd">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayout)/dateLayout"/>
                <xsl:with-param name="contentOfThisElement" select="$contentForThisElement"/>
            </xsl:call-template>
        </tex:group>
        <tex:cmd name="par" nl2="1"/>
        <xsl:call-template name="DoSpaceAfter">
            <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayout)/dateLayout"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        presentedAt
    -->
    <xsl:template match="presentedAt">
        <tex:group>
            <xsl:call-template name="DoFrontMatterFormatInfoBegin">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/presentedAtLayout"/>
            </xsl:call-template>
            <xsl:apply-templates/>
            <xsl:variable name="contentForThisElement">
                <xsl:apply-templates/>
            </xsl:variable>
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/presentedAtLayout"/>
            </xsl:call-template>
            <xsl:call-template name="DoFrontMatterFormatInfoEnd">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/presentedAtLayout"/>
                <xsl:with-param name="contentOfThisElement" select="$contentForThisElement"/>
            </xsl:call-template>
        </tex:group>
        <tex:cmd name="par" nl2="1"/>
        <xsl:call-template name="DoSpaceAfter">
            <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/presentedAtLayout"/>
        </xsl:call-template>
    </xsl:template>
    <!--
      version
      -->
    <xsl:template match="version">
        <xsl:param name="frontMatterLayout" select="$frontMatterLayoutInfo"/>
        <tex:group>
            <xsl:call-template name="DoFrontMatterFormatInfoBegin">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayout)/versionLayout"/>
            </xsl:call-template>
            <xsl:apply-templates/>
            <xsl:variable name="contentForThisElement">
                <xsl:apply-templates/>
            </xsl:variable>
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayout)/versionLayout"/>
            </xsl:call-template>
            <xsl:call-template name="DoFrontMatterFormatInfoEnd">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayout)/versionLayout"/>
                <xsl:with-param name="contentOfThisElement" select="$contentForThisElement"/>
            </xsl:call-template>
        </tex:group>
        <tex:cmd name="par" nl2="1"/>
        <xsl:call-template name="DoSpaceAfter">
            <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayout)/versionLayout"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        volumeAuthorRef
    -->
    <xsl:template match="volumeAuthorRef" mode="header-footer">
        <xsl:call-template name="DoHeaderFooterItemFontInfo"/>
        <xsl:choose>
            <xsl:when test="string-length(//volumeAuthor) &gt;0">
                <xsl:apply-templates select="//volumeAuthor"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>Volume Author Will Show Here</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="DoHeaderFooterItemFontInfoEnd"/>
    </xsl:template>
    <!--
        volumeTitleRef
    -->
    <xsl:template match="volumeTitleRef" mode="header-footer">
        <xsl:call-template name="DoHeaderFooterItemFontInfo"/>
        <xsl:choose>
            <xsl:when test="string-length(//volumeAuthor) &gt;0">
                <xsl:apply-templates select="//volumeTitle"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>Volume Title Will Show Here</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="DoHeaderFooterItemFontInfoEnd"/>
    </xsl:template>
    <!--
        publishingBlurb
    -->
    <xsl:template match="publishingBlurb">
        <xsl:param name="bInHeader" select="'N'"/>
        <tex:group>
            <xsl:call-template name="DoFrontMatterFormatInfoBegin">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/publishingBlurbLayout"/>
            </xsl:call-template>
            <xsl:apply-templates/>
            <xsl:variable name="contentForThisElement">
                <xsl:apply-templates/>
            </xsl:variable>
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/publishingBlurbLayout"/>
            </xsl:call-template>
            <xsl:call-template name="DoFrontMatterFormatInfoEnd">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/publishingBlurbLayout"/>
                <xsl:with-param name="contentOfThisElement" select="$contentForThisElement"/>
            </xsl:call-template>
        </tex:group>
        <xsl:if test="$bInHeader='N'">
            <tex:cmd name="par" nl2="1"/>
            <xsl:call-template name="DoSpaceAfter">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/publishingBlurbLayout"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--
      contents (for book)
      -->
    <xsl:template match="contents" mode="book">
        <xsl:param name="frontMatterLayout" select="$frontMatterLayoutInfo"/>
        <xsl:param name="contentsLayoutToUse" select="exsl:node-set($frontMatterLayoutInfo)/contentsLayout"/>
        <xsl:call-template name="DoPageBreakFormatInfo">
            <xsl:with-param name="layoutInfo" select="$contentsLayoutToUse"/>
        </xsl:call-template>
        <xsl:call-template name="DoContents">
            <xsl:with-param name="bIsBook" select="'Y'"/>
            <xsl:with-param name="frontMatterLayout" select="$frontMatterLayout"/>
            <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
        </xsl:call-template>
    </xsl:template>
    <!--
      contents (for paper)
      -->
    <xsl:template match="contents" mode="paper">
        <xsl:param name="frontMatterLayout" select="$frontMatterLayoutInfo"/>
        <xsl:param name="contentsLayoutToUse" select="$contentsLayout"/>
        <xsl:call-template name="DoContents">
            <xsl:with-param name="bIsBook" select="'N'"/>
            <xsl:with-param name="frontMatterLayout" select="$frontMatterLayout"/>
            <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
        </xsl:call-template>
    </xsl:template>
    <!--
      aknowledgements (frontmatter - book)
   -->
    <xsl:template match="acknowledgements" mode="frontmatter-book">
        <xsl:call-template name="DoFrontMatterItemNewPage">
            <xsl:with-param name="id">
                <xsl:call-template name="GetIdToUse">
                    <xsl:with-param name="sBaseId" select="$sAcknowledgementsID"/>
                </xsl:call-template>
            </xsl:with-param>
            <xsl:with-param name="sTitle">
                <xsl:call-template name="OutputAcknowledgementsLabel"/>
            </xsl:with-param>
            <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/acknowledgementsLayout"/>
            <xsl:with-param name="sRunningHeader">
                <xsl:call-template name="OutputAcknowledgementsLabel">
                    <xsl:with-param name="fUseShortTitleIfExists" select="'Y'"/>
                </xsl:call-template>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--
      aknowledgements (backmatter-book)
   -->
    <xsl:template match="acknowledgements" mode="backmatter-book">
        <xsl:param name="backMatterLayout" select="$backMatterLayoutInfo"/>
        <xsl:call-template name="DoBackMatterItemNewPage">
            <xsl:with-param name="id">
                <xsl:call-template name="GetIdToUse">
                    <xsl:with-param name="sBaseId" select="$sAcknowledgementsID"/>
                </xsl:call-template>
            </xsl:with-param>
            <xsl:with-param name="sTitle">
                <xsl:call-template name="OutputAcknowledgementsLabel"/>
            </xsl:with-param>
            <xsl:with-param name="layoutInfo" select="exsl:node-set($backMatterLayout)/acknowledgementsLayout"/>
            <xsl:with-param name="sRunningHeader">
                <xsl:call-template name="OutputAcknowledgementsLabel">
                    <xsl:with-param name="fUseShortTitleIfExists" select="'Y'"/>
                </xsl:call-template>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--
        acknowledgements (paper)
    -->
    <xsl:template match="acknowledgements" mode="paper">
        <xsl:param name="frontMatterLayout" select="$frontMatterLayoutInfo"/>
        <xsl:param name="backMatterLayout" select="$backMatterLayoutInfo"/>
        <xsl:choose>
            <xsl:when test="ancestor::frontMatter and exsl:node-set($frontMatterLayout)/acknowledgementsLayout/@showAsFootnoteAtEndOfAbstract='yes'">
                <!-- do nothing; the content of the acknowledgements are to appear in a footnote at the end of the abstract -->
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="@showinlandscapemode='yes'">
                    <tex:cmd name="landscape" gr="0" nl2="1"/>
                </xsl:if>
                <xsl:choose>
                    <xsl:when test="ancestor::frontMatter">
                        <xsl:call-template name="OutputFrontOrBackMatterTitle">
                            <xsl:with-param name="id">
                                <xsl:call-template name="GetIdToUse">
                                    <xsl:with-param name="sBaseId" select="$sAcknowledgementsID"/>
                                </xsl:call-template>
                            </xsl:with-param>
                            <xsl:with-param name="sTitle">
                                <xsl:call-template name="OutputAcknowledgementsLabel"/>
                            </xsl:with-param>
                            <xsl:with-param name="bIsBook" select="'N'"/>
                            <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayout)/acknowledgementsLayout"/>
                            <xsl:with-param name="sRunningHeader">
                                <xsl:call-template name="OutputAcknowledgementsLabel">
                                    <xsl:with-param name="fUseShortTitleIfExists" select="'Y'"/>
                                </xsl:call-template>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="OutputFrontOrBackMatterTitle">
                            <xsl:with-param name="id">
                                <xsl:call-template name="GetIdToUse">
                                    <xsl:with-param name="sBaseId" select="$sAcknowledgementsID"/>
                                </xsl:call-template>
                            </xsl:with-param>
                            <xsl:with-param name="sTitle">
                                <xsl:call-template name="OutputAcknowledgementsLabel"/>
                            </xsl:with-param>
                            <xsl:with-param name="bIsBook" select="'N'"/>
                            <xsl:with-param name="layoutInfo" select="exsl:node-set($backMatterLayout)/acknowledgementsLayout"/>
                            <xsl:with-param name="sRunningHeader">
                                <xsl:call-template name="OutputAcknowledgementsLabel">
                                    <xsl:with-param name="fUseShortTitleIfExists" select="'Y'"/>
                                </xsl:call-template>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:apply-templates/>
                <xsl:if test="@showinlandscapemode='yes'">
                    <xsl:if test="contains(@XeLaTeXSpecial,'fix-final-landscape')">
                        <tex:cmd name="XLingPaperendtableofcontents" gr="0"/>
                    </xsl:if>
                    <xsl:if test="contains(@XeLaTeXSpecial,'fix-final-landscape')">
                        <tex:cmd name="XLingPaperendtableofcontents" gr="0"/>
                    </xsl:if>
                    <tex:cmd name="endlandscape" gr="0" nl2="1"/>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        keywordsShownHere
    -->
    <xsl:template match="keywordsShownHere" mode="paper">
        <xsl:param name="frontMatterLayout"/>
        <xsl:apply-templates select="self::*">
            <xsl:with-param name="frontMatterLayout" select="$frontMatterLayout"/>
        </xsl:apply-templates>
    </xsl:template>
    <xsl:template match="keywordsShownHere">
        <xsl:param name="frontMatterLayout"/>
        <xsl:choose>
            <xsl:when test="parent::frontMatter">
                <xsl:call-template name="OutputKeywordsTitleAndContent">
                    <xsl:with-param name="sKeywordsID" select="$sKeywordsInFrontMatterID"/>
                    <xsl:with-param name="layoutInfo" select="$frontMatterLayout"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="OutputKeywordsTitleAndContent">
                    <xsl:with-param name="sKeywordsID" select="$sKeywordsInBackMatterID"/>
                    <xsl:with-param name="layoutInfo" select="$frontMatterLayout"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!--
        preface (paper)
    -->
    <!--    <xsl:template match="preface" mode="paper">
        <xsl:param name="frontMatterLayout" select="$frontMatterLayoutInfo"/>
        <xsl:param name="iLayoutPosition" select="0"/>
        <xsl:variable name="iPos" select="count(preceding-sibling::preface) + 1"/>
        <xsl:if test="$iLayoutPosition = 0 or $iLayoutPosition = $iPos">
            <xsl:call-template name="DoPrefacePerPaperLayout">
                <xsl:with-param name="prefaceLayout" select="$prefaceLayout"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
-->
    <!-- ===========================================================
      PARTS, CHAPTERS, SECTIONS, and APPENDICES
      =========================================================== -->
    <!--
      Part
      -->
    <xsl:template match="part">
        <xsl:call-template name="DoPageBreakFormatInfo">
            <xsl:with-param name="layoutInfo">
                <xsl:choose>
                    <xsl:when test="name(exsl:node-set($bodyLayoutInfo)/partLayout/*[1])='partTitleLayout'">
                        <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/partLayout/partTitleLayout"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/partLayout/numberLayout"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:with-param>
        </xsl:call-template>
        <xsl:if test="not(preceding-sibling::part) and not(//chapterBeforePart)">
            <xsl:if test="exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles">
                <tex:cmd name="pagestyle">
                    <tex:parm>body</tex:parm>
                </tex:cmd>
            </xsl:if>
            <xsl:call-template name="SetPageNumberingForBody"/>
        </xsl:if>
        <xsl:call-template name="SetStartingPageNumber">
            <xsl:with-param name="startingPageNumber" select="@startingPageNumber"/>
        </xsl:call-template>
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <tex:group>
            <xsl:call-template name="DoTitleFormatInfo">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($bodyLayoutInfo)/partLayout/numberLayout"/>
            </xsl:call-template>
            <tex:cmd name="thispagestyle">
                <tex:parm>empty</tex:parm>
            </tex:cmd>
            <xsl:call-template name="DoBookMark"/>
            <xsl:call-template name="CreateAddToContents">
                <xsl:with-param name="id" select="@id"/>
            </xsl:call-template>
            <xsl:call-template name="DoInternalTargetBegin">
                <xsl:with-param name="sName" select="@id"/>
            </xsl:call-template>
            <xsl:call-template name="OutputChapTitle">
                <xsl:with-param name="sTitle">
                    <xsl:call-template name="OutputPartLabel"/>
                    <xsl:text>&#x20;</xsl:text>
                    <xsl:apply-templates select="." mode="numberPart"/>
                </xsl:with-param>
            </xsl:call-template>
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($bodyLayoutInfo)/partLayout/numberLayout"/>
            </xsl:call-template>
            <xsl:variable name="contentForThisElement">
                <xsl:call-template name="OutputChapTitle">
                    <xsl:with-param name="sTitle">
                        <xsl:call-template name="OutputPartLabel"/>
                        <xsl:text>&#x20;</xsl:text>
                        <xsl:apply-templates select="." mode="numberPart"/>
                    </xsl:with-param>
                </xsl:call-template>
                <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($bodyLayoutInfo)/partLayout/numberLayout"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:call-template name="DoTitleFormatInfoEnd">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($bodyLayoutInfo)/partLayout/numberLayout"/>
                <xsl:with-param name="contentOfThisElement" select="$contentForThisElement"/>
            </xsl:call-template>
            <xsl:call-template name="DoInternalTargetEnd"/>
        </tex:group>
        <tex:cmd name="par" nl2="1"/>
        <xsl:call-template name="DoSpaceAfter">
            <xsl:with-param name="layoutInfo" select="exsl:node-set($bodyLayoutInfo)/partLayout/numberLayout"/>
        </xsl:call-template>
        <tex:group>
            <xsl:call-template name="DoTitleFormatInfo">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($bodyLayoutInfo)/partLayout/partTitleLayout"/>
            </xsl:call-template>
            <xsl:apply-templates select="secTitle"/>
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($bodyLayoutInfo)/partLayout/partTitleLayout"/>
            </xsl:call-template>
            <xsl:variable name="contentForThisElement">
                <xsl:apply-templates select="secTitle"/>
                <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($bodyLayoutInfo)/partLayout/partTitleLayout"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:call-template name="DoTitleFormatInfoEnd">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($bodyLayoutInfo)/partLayout/partTitleLayout"/>
                <xsl:with-param name="contentOfThisElement" select="$contentForThisElement"/>
            </xsl:call-template>
        </tex:group>
        <tex:cmd name="par" nl2="1"/>
        <xsl:call-template name="DoSpaceAfter">
            <xsl:with-param name="layoutInfo" select="exsl:node-set($bodyLayoutInfo)/partLayout/partTitleLayout"/>
        </xsl:call-template>
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
        <xsl:call-template name="DoPageBreakFormatInfo">
            <xsl:with-param name="layoutInfo">
                <xsl:choose>
                    <xsl:when test="name()='appendix' and not(ancestor::chapterInCollection)">
                        <xsl:choose>
                            <xsl:when test="name(exsl:node-set($backMatterLayoutInfo)/appendixLayout/*[1])='appendixTitleLayout'">
                                <xsl:copy-of select="exsl:node-set($backMatterLayoutInfo)/appendixLayout/appendixTitleLayout"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:copy-of select="exsl:node-set($backMatterLayoutInfo)/appendixLayout/numberLayout"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:when test="name()='appendix' and ancestor::chapterInCollection">
                        <xsl:choose>
                            <xsl:when test="name(exsl:node-set($bodyLayoutInfo)/chapterInCollectionBackMatterLayout/appendixLayout/*[1])='appendixTitleLayout'">
                                <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/chapterInCollectionBackMatterLayout/appendixLayout/appendixTitleLayout"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/chapterInCollectionBackMatterLayout/appendixLayout/numberLayout"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:when test="name()='chapterInCollection' or name()='chapterBeforePart' and //chapterInCollection">
                        <xsl:choose>
                            <xsl:when test="name(exsl:node-set($bodyLayoutInfo)/chapterInCollectionLayout/*[1])='chapterTitleLayout'">
                                <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/chapterInCollectionLayout/chapterTitleLayout"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/chapterInCollectionLayout/numberLayout"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:choose>
                            <xsl:when test="name(exsl:node-set($bodyLayoutInfo)/chapterLayout/*[1])='chapterTitleLayout'">
                                <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/chapterLayout/chapterTitleLayout"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/chapterLayout/numberLayout"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:with-param>
            <xsl:with-param name="bUseClearEmptyDoublePage">
                <xsl:choose>
                    <xsl:when test="parent::part or name()='chapterBeforePart'">Y</xsl:when>
                    <xsl:otherwise>N</xsl:otherwise>
                </xsl:choose>
            </xsl:with-param>
        </xsl:call-template>
        <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak')">
            <tex:cmd name="pagebreak" nl2="0"/>
        </xsl:if>
        <xsl:if test="contains(name(),'chapter') and not(parent::part) and position()=1 or preceding-sibling::*[1][name(.)='frontMatter']">
            <xsl:if test="exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles">
                <tex:cmd name="pagestyle">
                    <tex:parm>body</tex:parm>
                </tex:cmd>
            </xsl:if>
            <xsl:call-template name="SetPageNumberingForBody"/>
        </xsl:if>
        <xsl:if test="exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles/headerFooterFirstPage">
            <xsl:choose>
                <xsl:when
                    test="contains(name(),'chapter') and not(exsl:node-set($bodyLayoutInfo)/chapterLayout/numberLayout) and exsl:node-set($bodyLayoutInfo)/chapterLayout/chapterTitleLayout/@pagebreakbefore!='yes' and name(preceding-sibling::*[1])!='frontMatter'">
                    <!-- do nothing -->
                </xsl:when>
                <xsl:when test="name()='appendix' and ancestor::chapterInCollection">
                    <!-- do nothing -->
                </xsl:when>
                <xsl:when test="name()='appendix' and exsl:node-set($backMatterLayoutInfo)/headerFooterPageStyles/headerFooterFirstPage">
                    <tex:cmd name="thispagestyle">
                        <tex:parm>backmatterfirstpage</tex:parm>
                    </tex:cmd>
                </xsl:when>
                <xsl:otherwise>
                    <tex:cmd name="thispagestyle">
                        <tex:parm>bodyfirstpage</tex:parm>
                    </tex:cmd>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:call-template name="SetStartingPageNumber">
            <xsl:with-param name="startingPageNumber" select="@startingPageNumber"/>
        </xsl:call-template>
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <!-- put title in marker so it can show up in running header -->
        <xsl:variable name="sRunningHeader">
            <xsl:choose>
                <xsl:when test="ancestor::chapterInCollection and name()='appendix'">
                    <!-- an appendix in a chapter in a collection is treated like a section, as far as the header is concerned -->
                    <xsl:call-template name="DoSecTitleRunningHeader">
                        <xsl:with-param name="number" select="$chapterNumberInHeaderLayout"/>
                        <xsl:with-param name="bNumberIsBeforeTitle" select="$bChapterNumberIsBeforeTitle"></xsl:with-param>
                    </xsl:call-template>
                </xsl:when>
                <xsl:when test="exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles/*[descendant::chapterTitle and descendant::sectionTitle]">
                    <!-- some header or a footer has both the chapter title and the section title; 
                        make the section be blank in case there is no section for a while (or at all) 
                        so that we do not get the chapter title repeated twice in the header/footer -->
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="DoSecTitleRunningHeader">
                        <xsl:with-param name="number" select="$chapterNumberInHeaderLayout"/>
                        <xsl:with-param name="bNumberIsBeforeTitle" select="$bChapterNumberIsBeforeTitle"></xsl:with-param>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:call-template name="DoRunningHeader">
            <xsl:with-param name="sHeader" select="$sRunningHeader"/>
        </xsl:call-template>
        <!-- <xsl:if
            test="exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles/descendant::header[descendant::chapterTitle and descendant::sectionTitle] or exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles/descendant::footer[descendant::chapterTitle and descendant::sectionTitle]">
            <!-\- either a header or a footer has both the chapter title and the section title; 
                make the section be blank in case there is no section for a while (or at all) 
                so that we do not get the chapter title repeated twice in the header/footer -\->
            <tex:cmd name="markright">
                <tex:param/>
            </tex:cmd>
        </xsl:if>-->
        <xsl:if test="name()='chapterInCollection'">
            <xsl:variable name="originalContext" select="."/>
            <xsl:for-each select="exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles/headerFooterPage/* | exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles/headerFooterFirstPage/*">
                <!-- uses the same layout for all pages -->
                <xsl:for-each select="*">
                    <!-- for each left, center, right item -->
                    <xsl:if test="*/chapterInCollectionAuthor">
                        <xsl:call-template name="DoHeaderFooterItem">
                            <xsl:with-param name="item" select="."/>
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                        </xsl:call-template>
                    </xsl:if>
                </xsl:for-each>
            </xsl:for-each>
            <xsl:for-each select="exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles/*[name()='headerFooterOddEvenPages']/*">
                <!-- uses odd/even page layout -->
                <xsl:for-each select="*">
                    <xsl:for-each select="*[descendant::chapterInCollectionAuthor]">
                        <!-- for each left, center, right item -->
                        <xsl:call-template name="DoHeaderFooterItem">
                            <xsl:with-param name="item" select="."/>
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                            <xsl:with-param name="sOddEven">
                                <xsl:choose>
                                    <xsl:when test="ancestor::headerFooterEvenPage">E</xsl:when>
                                    <xsl:otherwise>O</xsl:otherwise>
                                </xsl:choose>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:for-each>
        </xsl:if>
        <xsl:if test="contains(name(),'chapter') and not(parent::part) and position()=1 or preceding-sibling::*[1][name(.)='frontMatter']">
            <xsl:call-template name="SetStartingPageNumberInBook"/>
        </xsl:if>
        <xsl:call-template name="CreateAddToContents">
            <xsl:with-param name="id" select="@id"/>
        </xsl:call-template>
        <!--<xsl:call-template name="DoBookMark"/>-->
        <xsl:variable name="numberLayoutToUse">
            <xsl:choose>
                <xsl:when test="name()='appendix' and not(ancestor::chapterInCollection)">
                    <xsl:copy-of select="exsl:node-set($backMatterLayoutInfo)/appendixLayout/numberLayout"/>
                </xsl:when>
                <xsl:when test="name()='appendix' and ancestor::chapterInCollection">
                    <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/chapterInCollectionBackMatterLayout/appendixLayout/numberLayout"/>
                </xsl:when>
                <xsl:when test="name()='chapterInCollection' or name()='chapterBeforePart' and //chapterInCollection">
                    <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/chapterInCollectionLayout/numberLayout"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/chapterLayout/numberLayout"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="titleLayoutToUse">
            <xsl:choose>
                <xsl:when test="name()='appendix' and not(ancestor::chapterInCollection)">
                    <xsl:copy-of select="exsl:node-set($backMatterLayoutInfo)/appendixLayout/appendixTitleLayout"/>
                </xsl:when>
                <xsl:when test="name()='appendix' and ancestor::chapterInCollection">
                    <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/chapterInCollectionBackMatterLayout/appendixLayout/appendixTitleLayout"/>
                </xsl:when>
                <xsl:when test="name()='chapterInCollection' or name()='chapterBeforePart' and //chapterInCollection">
                    <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/chapterInCollectionLayout/chapterTitleLayout"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/chapterLayout/chapterTitleLayout"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="count(exsl:node-set($numberLayoutToUse)/*) &gt; 0">
                <!--<xsl:call-template name="DoInternalTargetBegin">
                    <xsl:with-param name="sName" select="@id"/>
                </xsl:call-template>-->
                <tex:group>
                    <xsl:call-template name="DoTitleFormatInfo">
                        <xsl:with-param name="layoutInfo" select="exsl:node-set($numberLayoutToUse)/descendant-or-self::*"/>
                        <!-- page break stuff has already been done; when we changed to use raisebox for hypertarget and made the
                               content of the hypertarget be empty, we suddenly got an extra page break here.
                        -->
                        <xsl:with-param name="fDoPageBreakFormatInfo" select="'N'"/>
                    </xsl:call-template>
                    <xsl:call-template name="DoInternalTargetBegin">
                        <xsl:with-param name="sName" select="@id"/>
                    </xsl:call-template>
                    <xsl:call-template name="DoBookMark"/>
                    <xsl:call-template name="OutputChapTitle">
                        <xsl:with-param name="sTitle">
                            <xsl:call-template name="OutputChapterNumber"/>
                        </xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                        <xsl:with-param name="layoutInfo" select="exsl:node-set($numberLayoutToUse)/descendant-or-self::*"/>
                    </xsl:call-template>
                    <xsl:variable name="contentForThisElement">
                        <xsl:call-template name="OutputChapTitle">
                            <xsl:with-param name="sTitle">
                                <xsl:call-template name="OutputChapterNumber"/>
                            </xsl:with-param>
                        </xsl:call-template>
                        <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                            <xsl:with-param name="layoutInfo" select="exsl:node-set($numberLayoutToUse)/descendant-or-self::*"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <!-- hack: cannot do this in DoTitleFormatInfoEnd -->
                    <xsl:if test="name()='appendix' and exsl:node-set($titleLayoutToUse)/appendixTitleLayout/@showletter='no'">
                        <tex:spec cat="esc"/>
                        <tex:spec cat="esc"/>
                    </xsl:if>
                    <xsl:call-template name="DoTitleFormatInfoEnd">
                        <xsl:with-param name="layoutInfo" select="exsl:node-set($numberLayoutToUse)/descendant-or-self::*"/>
                        <xsl:with-param name="contentOfThisElement" select="$contentForThisElement"/>
                    </xsl:call-template>
                </tex:group>
                <xsl:call-template name="DoInternalTargetEnd"/>
                <tex:cmd name="par" nl2="1"/>
                <xsl:call-template name="DoSpaceAfter">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($numberLayoutToUse)/descendant-or-self::*"/>
                </xsl:call-template>
                <tex:group>
                    <xsl:call-template name="DoTitleFormatInfo">
                        <xsl:with-param name="layoutInfo" select="exsl:node-set($titleLayoutToUse)/descendant-or-self::*"/>
                    </xsl:call-template>
                    <xsl:if test="frontMatter/title/child::node()[name()='endnote'] and exsl:node-set($titleLayoutToUse)/chapterTitleLayout/@useFootnoteSymbols='yes'">
                        <xsl:call-template name="UseFootnoteSymbols"/>
                    </xsl:if>
                    <xsl:apply-templates select="secTitle | frontMatter/title"/>
                    <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                        <xsl:with-param name="layoutInfo" select="exsl:node-set($titleLayoutToUse)/descendant-or-self::*"/>
                    </xsl:call-template>
                    <xsl:variable name="contentForThisElement2">
                        <xsl:apply-templates select="secTitle | frontMatter/title"/>
                        <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                            <xsl:with-param name="layoutInfo" select="exsl:node-set($titleLayoutToUse)/descendant-or-self::*"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:call-template name="DoTitleFormatInfoEnd">
                        <xsl:with-param name="layoutInfo" select="exsl:node-set($titleLayoutToUse)/descendant-or-self::*"/>
                        <xsl:with-param name="contentOfThisElement" select="$contentForThisElement2"/>
                    </xsl:call-template>
                </tex:group>
            </xsl:when>
            <xsl:otherwise>
                <tex:group>
                    <xsl:variable name="sTextTransform" select="exsl:node-set($titleLayoutToUse)/descendant-or-self::*/@text-transform"/>
                    <xsl:variable name="fNoNumberLayout">
                        <xsl:choose>
                            <xsl:when test="string-length(exsl:node-set($numberLayoutToUse)/@linebefore)=0">
                                <xsl:text>Y</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>N</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:variable>
                    <xsl:if test="$sTextTransform='uppercase' and $fNoNumberLayout='N' or $sTextTransform='lowercase' and $fNoNumberLayout='N'">
                        <xsl:call-template name="DoBookMark"/>
                        <xsl:call-template name="DoInternalTargetBegin">
                            <xsl:with-param name="sName" select="@id"/>
                        </xsl:call-template>
                    </xsl:if>
                    <xsl:call-template name="DoTitleFormatInfo">
                        <xsl:with-param name="layoutInfo" select="exsl:node-set($titleLayoutToUse)/descendant-or-self::*"/>
                        <!-- page break stuff has already been done; when we changed to use raisebox for hypertarget and made the
                            content of the hypertarget be empty, we suddenly got an extra page break here.
                        -->
                        <xsl:with-param name="fDoPageBreakFormatInfo" select="'N'"/>
                    </xsl:call-template>
                    <xsl:if test="string-length($sTextTransform)=0 or not($sTextTransform='uppercase' or $sTextTransform='lowercase') or $fNoNumberLayout='Y'">
                        <xsl:call-template name="DoInternalTargetBegin">
                            <xsl:with-param name="sName" select="@id"/>
                        </xsl:call-template>
                        <xsl:call-template name="DoBookMark"/>
                    </xsl:if>
                    <xsl:call-template name="OutputChapTitle">
                        <xsl:with-param name="sTitle">
                            <xsl:call-template name="OutputChapterNumber"/>
                        </xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DoInternalTargetEnd"/>
                    <xsl:apply-templates select="secTitle | frontMatter/title"/>
                    <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                        <xsl:with-param name="layoutInfo" select="exsl:node-set($titleLayoutToUse)/descendant-or-self::*"/>
                    </xsl:call-template>
                    <xsl:variable name="contentForThisElement2">
                        <xsl:apply-templates select="secTitle | frontMatter/title"/>
                        <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                            <xsl:with-param name="layoutInfo" select="exsl:node-set($titleLayoutToUse)/descendant-or-self::*"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:call-template name="DoTitleFormatInfoEnd">
                        <xsl:with-param name="layoutInfo" select="exsl:node-set($titleLayoutToUse)/descendant-or-self::*"/>
                        <xsl:with-param name="contentOfThisElement" select="$contentForThisElement2"/>
                    </xsl:call-template>
                    <xsl:if test="string-length($sTextTransform) &gt; 0 and $fNoNumberLayout='Y'">
                        <xsl:call-template name="DoInternalTargetBegin">
                            <xsl:with-param name="sName" select="@id"/>
                        </xsl:call-template>
                        <xsl:call-template name="DoInternalTargetEnd"/>
                    </xsl:if>
                </tex:group>
            </xsl:otherwise>
        </xsl:choose>
        <tex:cmd name="par" nl2="1"/>
        <xsl:call-template name="DoSpaceAfter">
            <xsl:with-param name="layoutInfo" select="exsl:node-set($titleLayoutToUse)/descendant-or-self::*"/>
        </xsl:call-template>
        <xsl:apply-templates select="child::node()[name()!='secTitle']">
            <xsl:with-param name="frontMatterLayout" select="exsl:node-set($bodyLayoutInfo)/chapterInCollectionFrontMatterLayout"/>
            <xsl:with-param name="backMatterLayout" select="exsl:node-set($bodyLayoutInfo)/chapterInCollectionBackMatterLayout"/>
        </xsl:apply-templates>
        <xsl:if test="@showinlandscapemode='yes'">
            <xsl:if test="contains(@XeLaTeXSpecial,'fix-final-landscape')">
                <tex:cmd name="XLingPaperendtableofcontents" gr="0"/>
            </xsl:if>
            <tex:cmd name="endlandscape" gr="0" nl2="1"/>
        </xsl:if>
    </xsl:template>
    <!--
        chapterInCollectionAuthor
    -->
    <xsl:template match="chapterInCollectionAuthor" mode="header-footer">
        <xsl:param name="originalContext"/>
        <xsl:if test="name($originalContext)='chapterInCollection'">
            <xsl:call-template name="DoHeaderFooterItemFontInfo"/>
            <xsl:choose>
                <xsl:when test="string-length(normalize-space(exsl:node-set($originalContext)/frontMatter/shortAuthor)) &gt; 0">
                    <xsl:apply-templates select="exsl:node-set($originalContext)/frontMatter/shortAuthor"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates select="exsl:node-set($originalContext)/frontMatter/author" mode="contentOnly"/>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="DoHeaderFooterItemFontInfoEnd"/>
        </xsl:if>
    </xsl:template>
    <!--
        chapterNumber
    -->
    <xsl:template match="chapterNumber[not(following-sibling::chapterTitle) and not(preceding-sibling::chapterTitle)]" mode="header-footer">
        <xsl:call-template name="DoHeaderFooterItemFontInfo"/>
        <xsl:call-template name="SetMarkPerOddEvenPage"/>
        <xsl:call-template name="DoHeaderFooterItemFontInfoEnd"/>
    </xsl:template>
    <xsl:template match="chapterNumber" mode="header-footer">
        <!-- there is also a chapterTitle so we do nothing here.  The formatting of the chapterNumber is handled in the first part of the \markboth command -->
    </xsl:template>
    <!--
        chapterTitle
    -->
    <xsl:template match="chapterTitle" mode="header-footer">
        <xsl:call-template name="DoHeaderFooterItemFontInfo"/>
        <xsl:call-template name="SetMarkPerOddEvenPage"/>
        <xsl:call-template name="DoHeaderFooterItemFontInfoEnd"/>
    </xsl:template>
    <!--
      Sections
      -->
    <xsl:template match="section1">
        <xsl:call-template name="DoSection">
            <xsl:with-param name="layoutInfo" select="exsl:node-set($bodyLayoutInfo)/section1Layout"/>
        </xsl:call-template>
    </xsl:template>
    <xsl:template match="section2">
        <xsl:call-template name="DoSection">
            <xsl:with-param name="layoutInfo" select="exsl:node-set($bodyLayoutInfo)/section2Layout"/>
        </xsl:call-template>
    </xsl:template>
    <xsl:template match="section3">
        <xsl:call-template name="DoSection">
            <xsl:with-param name="layoutInfo" select="exsl:node-set($bodyLayoutInfo)/section3Layout"/>
        </xsl:call-template>
    </xsl:template>
    <xsl:template match="section4">
        <xsl:call-template name="DoSection">
            <xsl:with-param name="layoutInfo" select="exsl:node-set($bodyLayoutInfo)/section4Layout"/>
        </xsl:call-template>
    </xsl:template>
    <xsl:template match="section5">
        <xsl:call-template name="DoSection">
            <xsl:with-param name="layoutInfo" select="exsl:node-set($bodyLayoutInfo)/section5Layout"/>
        </xsl:call-template>
    </xsl:template>
    <xsl:template match="section6">
        <xsl:call-template name="DoSection">
            <xsl:with-param name="layoutInfo" select="exsl:node-set($bodyLayoutInfo)/section6Layout"/>
        </xsl:call-template>
    </xsl:template>
    <!--
      Appendix
      -->
    <xsl:template match="appendix[not(//chapter | //chapterInCollection)]">
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:if test="contains(@XeLaTeXSpecial,'clearpage')">
            <tex:cmd name="clearpage" gr="0" nl2="0"/>
        </xsl:if>
        <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak')">
            <tex:cmd name="pagebreak" nl2="0"/>
        </xsl:if>
        <xsl:variable name="appLayout" select="exsl:node-set($backMatterLayoutInfo)/appendixLayout/appendixTitleLayout"/>
        <xsl:if test="exsl:node-set($lingPaper)/section1">
            <!-- Normal case for a paper. -->
            <!-- put title in marker so it can show up in running header -->
            <tex:cmd name="markboth" nl2="1">
                <tex:parm>
                    <xsl:call-template name="DoSecTitleRunningHeader">
                        <xsl:with-param name="number" select="$chapterNumberInHeaderLayout"/>
                        <xsl:with-param name="bNumberIsBeforeTitle" select="$bChapterNumberIsBeforeTitle"></xsl:with-param>
                    </xsl:call-template>
                </tex:parm>
                <tex:parm>
                    <xsl:call-template name="DoSecTitleRunningHeader">
                        <xsl:with-param name="number" select="$chapterNumberInHeaderLayout"/>
                        <xsl:with-param name="bNumberIsBeforeTitle" select="$bChapterNumberIsBeforeTitle"></xsl:with-param>
                    </xsl:call-template>
                </tex:parm>
            </tex:cmd>
            <xsl:call-template name="CreateAddToContents">
                <xsl:with-param name="id" select="@id"/>
            </xsl:call-template>
        </xsl:if>
        <tex:group>
            <xsl:variable name="sTextTransform" select="exsl:node-set($appLayout)/@text-transform"/>
            <xsl:if test="$sTextTransform='uppercase' or $sTextTransform='lowercase'">
                <xsl:call-template name="DoBookMark"/>
                <xsl:call-template name="DoInternalTargetBegin">
                    <xsl:with-param name="sName" select="@id"/>
                </xsl:call-template>
            </xsl:if>
            <!--            <xsl:call-template name="DoTitleNeedsSpace"/> Now do this in DoTitleFormatInfo-->
            <xsl:call-template name="DoType">
                <xsl:with-param name="type" select="@type"/>
            </xsl:call-template>
            <xsl:call-template name="DoTitleFormatInfo">
                <xsl:with-param name="layoutInfo" select="$appLayout"/>
                <xsl:with-param name="originalContext" select="secTitle"/>
            </xsl:call-template>
            <xsl:if test="not(exsl:node-set($lingPaper)/section1)">
                <!-- Special case for when there are no chapters and no sections, just appendices.
                     It is used by Mexico branch linguistics publications for a grammar in a dictionary;
                     it is a book format (including appendices starting on an odd page) but since there
                     are no chapters, it is treated as a paper. -->
                <!-- put title in marker so it can show up in running header -->
                <tex:cmd name="markboth" nl2="1">
                    <tex:parm>
                        <xsl:call-template name="DoSecTitleRunningHeader">
                            <xsl:with-param name="number" select="$chapterNumberInHeaderLayout"/>
                            <xsl:with-param name="bNumberIsBeforeTitle" select="$bChapterNumberIsBeforeTitle"></xsl:with-param>
                        </xsl:call-template>
                    </tex:parm>
                    <tex:parm>
                        <xsl:call-template name="DoSecTitleRunningHeader">
                            <xsl:with-param name="number" select="$chapterNumberInHeaderLayout"/>
                            <xsl:with-param name="bNumberIsBeforeTitle" select="$bChapterNumberIsBeforeTitle"></xsl:with-param>
                        </xsl:call-template>
                    </tex:parm>
                </tex:cmd>
                <xsl:call-template name="CreateAddToContents">
                    <xsl:with-param name="id" select="@id"/>
                </xsl:call-template>
            </xsl:if>
            <xsl:if test="string-length($sTextTransform)=0 or not($sTextTransform='uppercase' or $sTextTransform='lowercase')">
                <xsl:call-template name="DoBookMark"/>
                <xsl:call-template name="DoInternalTargetBegin">
                    <xsl:with-param name="sName" select="@id"/>
                </xsl:call-template>
            </xsl:if>
            <xsl:if test="exsl:node-set($appLayout)/@showletter!='no'">
                <xsl:apply-templates select="." mode="numberAppendix"/>
                <xsl:value-of select="exsl:node-set($appLayout)/@textafterletter"/>
            </xsl:if>
            <xsl:apply-templates select="secTitle"/>
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="$appLayout"/>
            </xsl:call-template>
            <xsl:variable name="contentForThisElement">
                <xsl:apply-templates select="secTitle"/>
                <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                    <xsl:with-param name="layoutInfo" select="$appLayout"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:call-template name="DoTitleFormatInfoEnd">
                <xsl:with-param name="layoutInfo" select="$appLayout"/>
                <xsl:with-param name="originalContext" select="secTitle"/>
                <xsl:with-param name="contentOfThisElement" select="$contentForThisElement"/>
            </xsl:call-template>
            <xsl:call-template name="DoTypeEnd">
                <xsl:with-param name="type" select="@type"/>
            </xsl:call-template>
            <xsl:call-template name="DoInternalTargetEnd"/>
        </tex:group>
        <tex:cmd name="par" nl2="1"/>
        <xsl:call-template name="DoSpaceAfter">
            <xsl:with-param name="layoutInfo" select="$appLayout"/>
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
        sectionNumber
    -->
    <xsl:template match="sectionNumber[not(following-sibling::sectionTitle) and not(preceding-sibling::sectionTitle)]" mode="header-footer">
        <xsl:call-template name="DoHeaderFooterItemFontInfo"/>
        <xsl:call-template name="SetMarkPerOddEvenPage">
            <xsl:with-param name="bIsChapter" select="'N'"/>
        </xsl:call-template>
        <xsl:call-template name="DoHeaderFooterItemFontInfoEnd"/>
    </xsl:template>
    <xsl:template match="sectionNumber" mode="header-footer">
        <!-- there is also a sectionTitle so we do nothing here.  
            The formatting of the sectionNumber is handled in the \markright command and the second part of the \markboth command.-->
    </xsl:template>
    <!--
        sectionTitle
    -->
    <xsl:template match="sectionTitle" mode="header-footer">
        <xsl:call-template name="DoHeaderFooterItemFontInfo"/>
        <xsl:call-template name="SetMarkPerOddEvenPage">
            <xsl:with-param name="bIsChapter" select="'N'"/>
        </xsl:call-template>
        <xsl:call-template name="DoHeaderFooterItemFontInfoEnd"/>
    </xsl:template>
    <!--
      sectionRef
      -->
    <xsl:template match="sectionRef">
        <xsl:param name="fDoHyperlink" select="'Y'"/>
        <xsl:call-template name="OutputAnyTextBeforeSectionRef"/>
        <xsl:variable name="secRefToUse">
            <!-- adjust reference to a section that is actually present per the style sheet -->
            <xsl:call-template name="GetSectionRefToUse">
                <xsl:with-param name="section" select="id(@sec)"/>
                <xsl:with-param name="bodyLayoutInfo" select="$bodyLayoutInfo"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:if test="$fDoHyperlink='Y'">
            <xsl:call-template name="DoInternalHyperlinkBegin">
                <xsl:with-param name="sName" select="$secRefToUse"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:choose>
            <xsl:when test="@showTitle = 'short' or @showTitle='full'">
                <xsl:if test="exsl:node-set($contentLayoutInfo)/sectionRefTitleLayout">
                    <xsl:call-template name="OutputFontAttributes">
                        <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/sectionRefTitleLayout"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="exsl:node-set($contentLayoutInfo)/sectionRefLayout">
                    <xsl:call-template name="OutputFontAttributes">
                        <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/sectionRefLayout"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="$fDoHyperlink='Y'">
            <xsl:call-template name="LinkAttributesBegin">
                <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/sectionRefLinkLayout"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="DoSectionRef">
            <xsl:with-param name="secRefToUse" select="$secRefToUse"/>
        </xsl:call-template>
        <xsl:if test="$fDoHyperlink='Y'">
            <xsl:call-template name="LinkAttributesEnd">
                <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/sectionRefLinkLayout"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:choose>
            <xsl:when test="@showTitle = 'short' or @showTitle='full'">
                <xsl:if test="exsl:node-set($contentLayoutInfo)/sectionRefTitleLayout">
                    <xsl:call-template name="OutputFontAttributesEnd">
                        <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/sectionRefTitleLayout"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="exsl:node-set($contentLayoutInfo)/sectionRefLayout">
                    <xsl:call-template name="OutputFontAttributesEnd">
                        <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/sectionRefLayout"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="$fDoHyperlink='Y'">
            <xsl:call-template name="DoExternalHyperRefEnd"/>
        </xsl:if>
    </xsl:template>
    <!--
      appendixRef
      -->
    <xsl:template match="appendixRef">
        <xsl:param name="fDoHyperlink" select="'Y'"/>
        <xsl:call-template name="OutputAnyTextBeforeAppendixRef"/>
        <xsl:if test="$fDoHyperlink='Y'">
            <xsl:call-template name="DoInternalHyperlinkBegin">
                <xsl:with-param name="sName" select="@app"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:choose>
            <xsl:when test="@showTitle = 'short' or @showTitle='full'">
                <xsl:if test="exsl:node-set($contentLayoutInfo)/sectionRefTitleLayout">
                    <xsl:call-template name="OutputFontAttributes">
                        <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/sectionRefTitleLayout"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="exsl:node-set($contentLayoutInfo)/sectionRefLayout">
                    <xsl:call-template name="OutputFontAttributes">
                        <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/sectionRefLayout"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="$fDoHyperlink='Y'">
            <xsl:call-template name="LinkAttributesBegin">
                <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/appendixRefLinkLayout"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="DoAppendixRef"/>
        <xsl:if test="$fDoHyperlink='Y'">
            <xsl:call-template name="LinkAttributesEnd">
                <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/appendixRefLinkLayout"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:choose>
            <xsl:when test="@showTitle = 'short' or @showTitle='full'">
                <xsl:if test="exsl:node-set($contentLayoutInfo)/sectionRefTitleLayout">
                    <xsl:call-template name="OutputFontAttributesEnd">
                        <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/sectionRefTitleLayout"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="exsl:node-set($contentLayoutInfo)/sectionRefLayout">
                    <xsl:call-template name="OutputFontAttributesEnd">
                        <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/sectionRefLayout"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="$fDoHyperlink='Y'">
            <xsl:call-template name="DoExternalHyperRefEnd"/>
        </xsl:if>
    </xsl:template>
    <!--
      genericRef
      -->
    <xsl:template match="genericRef">
        <xsl:param name="originalContext"/>
        <xsl:call-template name="DoInternalHyperlinkBegin">
            <xsl:with-param name="sName" select="@gref"/>
        </xsl:call-template>
        <xsl:call-template name="LinkAttributesBegin">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/genericRefLinkLayout"/>
        </xsl:call-template>
        <xsl:call-template name="OutputGenericRef">
            <xsl:with-param name="originalContext" select="$originalContext"/>
        </xsl:call-template>
        <xsl:call-template name="LinkAttributesEnd">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/genericRefLinkLayout"/>
        </xsl:call-template>
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
        <xsl:call-template name="LinkAttributesBegin">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/linkLinkLayout"/>
        </xsl:call-template>
        <xsl:apply-templates/>
        <xsl:call-template name="LinkAttributesEnd">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/linkLinkLayout"/>
        </xsl:call-template>
        <xsl:call-template name="DoExternalHyperRefEnd"/>
    </xsl:template>
    <!-- ===========================================================
        PARAGRAPH
        =========================================================== -->
    <xsl:template match="p | pc" mode="endnote-content">
        <xsl:param name="originalContext"/>
        <xsl:param name="iTablenumberedAdjust" select="0"/>
        <xsl:call-template name="OutputTypeAttributes">
            <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
        </xsl:call-template>
        <xsl:for-each select="parent::endnote">
            <xsl:if test="not(exsl:node-set($backMatterLayoutInfo)/useEndNotesLayout)">
                <tex:spec cat="esc"/>
                <xsl:text>footnotesize</xsl:text>
            </xsl:if>
            <tex:spec cat="bg"/>
            <tex:spec cat="esc"/>
            <xsl:text>textsuperscript</xsl:text>
            <tex:spec cat="bg"/>
            <xsl:call-template name="GetFootnoteMarkWhenUsingEndnotes">
                <xsl:with-param name="originalContext" select="$originalContext"/>
                <xsl:with-param name="iTablenumberedAdjust" select="$iTablenumberedAdjust"/>
            </xsl:call-template>
            <tex:spec cat="eg"/>
            <tex:spec cat="eg"/>
        </xsl:for-each>
        <xsl:call-template name="OutputTypeAttributesEnd">
            <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
        </xsl:call-template>
        <xsl:if test="string-length($sContentBetweenFootnoteNumberAndFootnoteContent) &gt; 0">
            <xsl:value-of select="$sContentBetweenFootnoteNumberAndFootnoteContent"/>
        </xsl:if>
        <xsl:apply-templates/>
    </xsl:template>
    <xsl:template match="p | pc" mode="contentOnly">
        <xsl:call-template name="OutputTypeAttributes">
            <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
        </xsl:call-template>
        <xsl:apply-templates/>
        <xsl:call-template name="OutputTypeAttributesEnd">
            <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
        </xsl:call-template>
    </xsl:template>
    <xsl:template match="p | pc">
        <xsl:if test="not(parent::endnote or parent::abstract or parent::blockquote) or count(preceding-sibling::*) &gt; 0">
            <xsl:call-template name="DoSpaceBefore">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($contentLayoutInfo)/paragraphLayout"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:choose>
            <xsl:when test="string-length(.)=0 and count(*)=0">
                <!-- this paragraph is empty; do nothing -->
            </xsl:when>
            <xsl:when test="count(child::node())=1 and name(child::node())='comment' and exsl:node-set($lingPaper)/@showcommentinoutput!='yes'">
                <!-- this paragraph is effectively empty since all it has is a comment; do nothing -->
            </xsl:when>
            <xsl:when test="parent::acknowledgements and count(preceding-sibling::p)=0 and exsl:node-set($frontMatterLayoutInfo)/acknowledgementsLayout/@showAsFootnoteAtEndOfAbstract='yes'">
                <!-- we're in a footnote now -->
                <xsl:apply-templates/>
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
                <xsl:if test="string-length($sContentBetweenFootnoteNumberAndFootnoteContent) &gt; 0">
                    <xsl:value-of select="$sContentBetweenFootnoteNumberAndFootnoteContent"/>
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
                        <xsl:choose>
                            <xsl:when test="count(preceding-sibling::*[name()!='secTitle' and name()!='shortTitle' and name()!='frontMatter'])=0">
                                <!-- is the first item -->
                                <xsl:choose>
                                    <xsl:when test="parent::appendix and exsl:node-set($backMatterLayoutInfo)/appendixLayout/@firstParagraphHasIndent='no'">
                                        <tex:cmd name="noindent" gr="0" nl2="0" sp="1"/>
                                    </xsl:when>
                                    <xsl:when test="parent::chapter and exsl:node-set($bodyLayoutInfo)/chapterLayout/@firstParagraphHasIndent='no'">
                                        <tex:cmd name="noindent" gr="0" nl2="0" sp="1"/>
                                    </xsl:when>
                                    <xsl:when test="parent::chapterInCollection and exsl:node-set($bodyLayoutInfo)/chapterInCollectionLayout/@firstParagraphHasIndent='no'">
                                        <tex:cmd name="noindent" gr="0" nl2="0" sp="1"/>
                                    </xsl:when>
                                    <xsl:when test="parent::section1 and exsl:node-set($bodyLayoutInfo)/section1Layout/@firstParagraphHasIndent='no'">
                                        <tex:cmd name="noindent" gr="0" nl2="0" sp="1"/>
                                    </xsl:when>
                                    <xsl:when test="parent::section2 and exsl:node-set($bodyLayoutInfo)/section2Layout/@firstParagraphHasIndent='no'">
                                        <tex:cmd name="noindent" gr="0" nl2="0" sp="1"/>
                                    </xsl:when>
                                    <xsl:when test="parent::section3 and exsl:node-set($bodyLayoutInfo)/section3Layout/@firstParagraphHasIndent='no'">
                                        <tex:cmd name="noindent" gr="0" nl2="0" sp="1"/>
                                    </xsl:when>
                                    <xsl:when test="parent::section4 and exsl:node-set($bodyLayoutInfo)/section4Layout/@firstParagraphHasIndent='no'">
                                        <tex:cmd name="noindent" gr="0" nl2="0" sp="1"/>
                                    </xsl:when>
                                    <xsl:when test="parent::section5 and exsl:node-set($bodyLayoutInfo)/section5Layout/@firstParagraphHasIndent='no'">
                                        <tex:cmd name="noindent" gr="0" nl2="0" sp="1"/>
                                    </xsl:when>
                                    <xsl:when test="parent::section6 and exsl:node-set($bodyLayoutInfo)/section6Layout/@firstParagraphHasIndent='no'">
                                        <tex:cmd name="noindent" gr="0" nl2="0" sp="1"/>
                                    </xsl:when>
                                    <xsl:when test="parent::abstract and exsl:node-set($frontMatterLayoutInfo)/abstractLayout/@firstParagraphHasIndent='no'">
                                        <tex:cmd name="noindent" gr="0" nl2="0" sp="1"/>
                                    </xsl:when>
                                    <xsl:when test="parent::preface and exsl:node-set($frontMatterLayoutInfo)/prefaceLayout/@firstParagraphHasIndent='no'">
                                        <tex:cmd name="noindent" gr="0" nl2="0" sp="1"/>
                                    </xsl:when>
                                    <xsl:when test="parent::acknowledgements and exsl:node-set($frontMatterLayoutInfo)/acknowledgementsLayout/@firstParagraphHasIndent='no'">
                                        <tex:cmd name="noindent" gr="0" nl2="0" sp="1"/>
                                    </xsl:when>
                                    <xsl:when test="parent::acknowledgements and exsl:node-set($backMatterLayoutInfo)/acknowledgementsLayout/@firstParagraphHasIndent='no'">
                                        <tex:cmd name="noindent" gr="0" nl2="0" sp="1"/>
                                    </xsl:when>
                                    <xsl:when test="parent::glossary and exsl:node-set($backMatterLayoutInfo)/glossaryLayout/@firstParagraphHasIndent='no'">
                                        <tex:cmd name="noindent" gr="0" nl2="0" sp="1"/>
                                    </xsl:when>
                                    <xsl:when test="parent::index and exsl:node-set($backMatterLayoutInfo)/indexLayout/@firstParagraphHasIndent='no'">
                                        <tex:cmd name="noindent" gr="0" nl2="0" sp="1"/>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <tex:cmd name="indent" gr="0" nl2="0" sp="1"/>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:when>
                            <xsl:otherwise>
                                <tex:cmd name="indent" gr="0" nl2="0" sp="1"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:call-template name="OutputTypeAttributes">
                    <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
                </xsl:call-template>
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
                    <!-- want to do these in prose-text, but many font info kinds of things cannot cross paragraph boundaries, so have to do here -->
                    <xsl:call-template name="DoType">
                        <xsl:with-param name="type" select="parent::prose-text/@type"/>
                    </xsl:call-template>
                    <xsl:call-template name="OutputFontAttributes">
                        <xsl:with-param name="language" select="exsl:node-set($documentLayoutInfo)/prose-textTextLayout"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:apply-templates/>
                <xsl:if test="parent::prose-text">
                    <xsl:call-template name="OutputFontAttributesEnd">
                        <xsl:with-param name="language" select="exsl:node-set($documentLayoutInfo)/prose-textTextLayout"/>
                    </xsl:call-template>
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
                <xsl:call-template name="OutputTypeAttributesEnd">
                    <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
                </xsl:call-template>
                <xsl:choose>
                    <xsl:when test="ancestor::td">
                        <xsl:text>&#xa;</xsl:text>
                    </xsl:when>
                    <xsl:when test="parent::li and count(preceding-sibling::*)=0 and following-sibling::*[1][name()='p' or name()='pc']">
                        <tex:cmd name="par"/>
                    </xsl:when>
                    <xsl:when test="parent::li and count(preceding-sibling::*)=0">
                        <!-- do nothing in this case -->
                    </xsl:when>
                    <xsl:when
                        test="parent::abstract and parent::abstract[preceding-sibling::acknowledgements] and count(following-sibling::p | following-sibling::pc)=0 and exsl:node-set($frontMatterLayoutInfo)/acknowledgementsLayout/@showAsFootnoteAtEndOfAbstract='yes'">
                        <tex:cmd name="renewcommand">
                            <tex:parm>
                                <tex:spec cat="esc"/>
                                <xsl:text>thefootnote</xsl:text>
                            </tex:parm>
                            <tex:parm>
                                <tex:cmd name="fnsymbol">
                                    <tex:parm>footnote</tex:parm>
                                </tex:cmd>
                            </tex:parm>
                        </tex:cmd>
                        <tex:cmd name="protect" gr="0"/>
                        <tex:cmd name="footnote">
                            <tex:parm>
                                <tex:group>
                                    <!--                                    <tex:spec cat="esc"/>
                                    <xsl:text>leftskip0pt</xsl:text>
                                    <tex:spec cat="esc"/>
                                    <xsl:text>parindent1em</xsl:text>
-->
                                    <xsl:call-template name="DoInternalTargetBegin">
                                        <xsl:with-param name="sName">
                                            <xsl:value-of select="$sAcknowledgementsID"/>
                                        </xsl:with-param>
                                    </xsl:call-template>
                                    <xsl:call-template name="DoInternalTargetEnd"/>
                                    <xsl:apply-templates select="exsl:node-set($lingPaper)/frontMatter/acknowledgements/*"/>
                                </tex:group>
                            </tex:parm>
                        </tex:cmd>
                        <tex:cmd name="par"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <tex:cmd name="par"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="not(parent::acknowledgements and count(preceding-sibling::p)=0 and exsl:node-set($frontMatterLayoutInfo)/acknowledgementsLayout/@showAsFootnoteAtEndOfAbstract='yes')">
            <!-- some chunk items come with space before them already so we do not want to add the extra space after a p/pc -->
            <xsl:variable name="nextChunkItem" select="following-sibling::*[1]"/>
            <xsl:if test="exsl:node-set($nextChunkItem)[name()!='blockquote' and name()!='ol' and name()!='ul' and name()!='dl']">
                <xsl:choose>
                    <xsl:when test="exsl:node-set($nextChunkItem)[name()='example' or name()='tablenumbered' or name()='figure']">
                        <!-- do nothing -->
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="DoSpaceAfter">
                            <xsl:with-param name="layoutInfo" select="exsl:node-set($contentLayoutInfo)/paragraphLayout"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:if>
        </xsl:if>
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
        <xsl:for-each select="key('RefWorkID',@citation)">
            <tex:cmd name="noindent"/>
            <xsl:call-template name="DoRefWork">
                <xsl:with-param name="works" select="."/>
                <xsl:with-param name="bDoTarget" select="'N'"/>
            </xsl:call-template>
        </xsl:for-each>
        <xsl:call-template name="DoNestedAnnotations">
            <xsl:with-param name="sList" select="@annotation"/>
        </xsl:call-template>
    </xsl:template>

    <!--
        pageNumber
    -->
    <xsl:template match="pageNumber" mode="header-footer">
        <xsl:call-template name="DoHeaderFooterItemFontInfo"/>
        <tex:cmd name="thepage" gr="0"/>
        <xsl:call-template name="DoHeaderFooterItemFontInfoEnd"/>
    </xsl:template>
    <!--
        paperAuthor
    -->
    <xsl:template match="paperAuthor" mode="header-footer">
        <xsl:call-template name="DoHeaderFooterItemFontInfo"/>
        <xsl:choose>
            <xsl:when test="string-length(normalize-space(exsl:node-set($lingPaper)/frontMatter/shortAuthor)) &gt; 0">
                <xsl:apply-templates select="exsl:node-set($lingPaper)/frontMatter/shortAuthor"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="exsl:node-set($lingPaper)/frontMatter/author" mode="contentOnly"/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="DoHeaderFooterItemFontInfoEnd"/>
    </xsl:template>
    <!--
        paperTitle
    -->
    <xsl:template match="paperTitle" mode="header-footer">
        <xsl:call-template name="DoHeaderFooterItemFontInfo"/>
        <xsl:choose>
            <xsl:when test="string-length(normalize-space(//frontMatter/shortTitle)) &gt; 0">
                <xsl:apply-templates select="//frontMatter/shortTitle"/>
            </xsl:when>
            <xsl:otherwise>
                <!--                              <xsl:apply-templates select="//frontMatter//title/child::node()[name()!='endnote']" mode="contentOnly"/>-->
                <xsl:apply-templates select="//frontMatter//title/child::node()[name()!='endnote' and name()!='img' and name()!='br']"/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="DoHeaderFooterItemFontInfoEnd"/>
    </xsl:template>
    <!--
        paperPublishingBlurb
    -->
    <xsl:template match="paperPublishingBlurb" mode="header-footer">
        <xsl:call-template name="DoHeaderFooterItemFontInfo"/>
        <xsl:variable name="sVerticalAdjustment" select="normalize-space(@verticalAdjustment)"/>
        <xsl:if test="string-length($sVerticalAdjustment) &gt; 0">
            <tex:cmd name="vspace">
                <tex:parm>
                    <xsl:value-of select="$sVerticalAdjustment"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:apply-templates select="exsl:node-set($lingPaper)/publishingInfo/publishingBlurb">
            <xsl:with-param name="bInHeader" select="'Y'"/>
        </xsl:apply-templates>
        <xsl:call-template name="DoHeaderFooterItemFontInfoEnd"/>
    </xsl:template>
    <!-- ===========================================================
      LISTS
      =========================================================== -->
    <!-- handled elsewhere -->
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
                        <!--<xsl:value-of select="$sBasicPointSize"/>
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
                        <!--<xsl:value-of select="$sBasicPointSize"/>
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
            <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespaceexamples='yes' and not(parent::td)">
                <!-- Note that if this example is embedded in a table, whatever line spacing the table has is used, not the line spacing for examples -->
                <tex:spec cat="bg"/>
                <xsl:if test="not(ancestor::endnote and exsl:node-set($lineSpacing)/@singlespaceendnotes='yes')">
                    <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
                </xsl:if>
            </xsl:if>
            <tex:cmd name="{$sXLingPaperExample}" nl1="0" nl2="1">
                <tex:parm>
                    <xsl:value-of select="exsl:node-set($contentLayoutInfo)/exampleLayout/@indent-before"/>
                </tex:parm>
                <tex:parm>
                    <xsl:choose>
                        <xsl:when test="exsl:node-set($lingPaper)/@automaticallywrapinterlinears='yes'">
                            <xsl:choose>
                                <!-- for some reason, the right offset causes an indent at the left so we do this special check -->
                                <xsl:when test="child::*[1][name()='exampleHeading'] and child::*[2][name()='interlinear']">
                                    <xsl:text>0pt</xsl:text>
                                </xsl:when>
                                <xsl:when test="child::*[1][name()='interlinear'][child::*[1][name()='exampleHeading']]">
                                    <xsl:text>0pt</xsl:text>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:value-of select="exsl:node-set($contentLayoutInfo)/exampleLayout/@indent-after"/>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="exsl:node-set($contentLayoutInfo)/exampleLayout/@indent-after"/>
                        </xsl:otherwise>
                    </xsl:choose>
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
                    <xsl:call-template name="HandleAnyInterlinearAlignedWordSkipOverride"/>
                    <xsl:call-template name="OutputTypeAttributes">
                        <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
                    </xsl:call-template>
                    <xsl:apply-templates>
                        <xsl:with-param name="bListsShareSameCode" select="$bListsShareSameCode"/>
                    </xsl:apply-templates>
                    <xsl:call-template name="OutputTypeAttributesEnd">
                        <xsl:with-param name="sList" select="@XeLaTeXSpecial"/>
                    </xsl:call-template>
                </tex:parm>
            </tex:cmd>
            <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespaceexamples='yes' and not(parent::td)">
                <!-- Note that if this example is embedded in a table, whatever line spacing the table has is used, not the line spacing for examples -->
                <tex:spec cat="eg"/>
            </xsl:if>
            <!--        </tex:env>-->
            <!--<tex:spec cat="esc"/>
            <tex:spec cat="esc"/>-->
            <!--            <tex:cmd name="vspace">
                <tex:parm><tex:cmd name="baselineskip"/></tex:parm>
            </tex:cmd>
-->
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
      interlinearSource
   -->
    <xsl:template match="interlinearSource" mode="contents">
        <xsl:variable name="interlinearSourceStyleLayout" select="exsl:node-set($contentLayoutInfo)/interlinearSourceStyle"/>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="$interlinearSourceStyleLayout"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:call-template name="DoFormatLayoutInfoTextBefore">
            <xsl:with-param name="layoutInfo" select="$interlinearSourceStyleLayout"/>
        </xsl:call-template>
        <xsl:apply-templates/>
        <xsl:call-template name="DoFormatLayoutInfoTextAfter">
            <xsl:with-param name="layoutInfo" select="$interlinearSourceStyleLayout"/>
        </xsl:call-template>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="$interlinearSourceStyleLayout"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
    </xsl:template>
    <!--
        definition
    -->
    <!--
        Not needed??
        <xsl:template match="example/definition">
        <fo:block>
        <xsl:call-template name="DoType"/>
        <xsl:apply-templates/>
        </fo:block>
        </xsl:template>
    -->
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
            <xsl:call-template name="LinkAttributesBegin">
                <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/exampleRefLinkLayout"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="DoExampleRefContent"/>
        <xsl:if test="$fDoHyperlink='Y'">
            <xsl:call-template name="LinkAttributesEnd">
                <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/exampleRefLinkLayout"/>
            </xsl:call-template>
            <xsl:call-template name="DoExternalHyperRefEnd"/>
        </xsl:if>
    </xsl:template>
    <!--
        iso639-3codeRef
    -->
    <xsl:template match="iso639-3codeRef">
        <xsl:param name="fDoHyperlink" select="'Y'"/>
        <xsl:choose>
            <xsl:when test="$fDoHyperlink='Y'">
                <xsl:call-template name="DoInternalHyperlinkBegin">
                    <xsl:with-param name="sName" select="@lang"/>
                </xsl:call-template>
                <xsl:call-template name="DoISO639-3codeRefContentXeLaTeX"/>
                <xsl:call-template name="DoExternalHyperRefEnd"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="DoISO639-3codeRefContentXeLaTeX"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        figure
    -->
    <xsl:template match="figure">
        <xsl:choose>
            <xsl:when test="descendant::endnote or @location='here'">
                <!--  cannot have endnotes in floats... If the user says, Put it here, don't treat it like a float -->
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
        <xsl:call-template name="DoInternalHyperlinkBegin">
            <xsl:with-param name="sName" select="@figure"/>
        </xsl:call-template>
        <xsl:choose>
            <xsl:when test="@showCaption = 'short' or @showCaption='full'">
                <xsl:if test="exsl:node-set($contentLayoutInfo)/figureRefCaptionLayout">
                    <xsl:call-template name="OutputFontAttributes">
                        <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/figureRefCaptionLayout"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="exsl:node-set($contentLayoutInfo)/figureRefLayout">
                    <xsl:call-template name="OutputFontAttributes">
                        <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/figureRefLayout"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="LinkAttributesBegin">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/figureRefLinkLayout"/>
        </xsl:call-template>
        <xsl:call-template name="DoFigureRef"/>
        <xsl:choose>
            <xsl:when test="@showCaption = 'short' or @showCaption='full'">
                <xsl:if test="exsl:node-set($contentLayoutInfo)/figureRefCaptionLayout">
                    <xsl:call-template name="OutputFontAttributesEnd">
                        <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/figureRefCaptionLayout"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="exsl:node-set($contentLayoutInfo)/figureRefLayout">
                    <xsl:call-template name="OutputFontAttributesEnd">
                        <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/figureRefLayout"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="DoInternalHyperlinkEnd"/>
        <xsl:call-template name="LinkAttributesEnd">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/figureRefLinkLayout"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        fixedText
    -->
    <xsl:template match="fixedText" mode="header-footer">
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="ancestor::headerFooterPageStyles"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="."/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:apply-templates/>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="."/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="ancestor::headerFooterPageStyles"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
    </xsl:template>
    <!--
        listOfFiguresShownHere
    -->
    <xsl:template match="listOfFiguresShownHere">
        <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacecontents='yes'">
            <tex:spec cat="bg"/>
            <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:if test="exsl:node-set($contentLayoutInfo)/figureLayout/@listOfFiguresUsesFigureAndPageHeaders='yes'">
            <tex:cmd name="noindent"/>
            <xsl:call-template name="OutputFigureLabel"/>
            <tex:cmd name="hfill"/>
            <xsl:variable name="sLabel" select="normalize-space(exsl:node-set($contentLayoutInfo)/figureLayout/@pageLabelInListOfFigures)"/>
            <xsl:choose>
                <xsl:when test="string-length($sLabel)&gt;0">
                    <xsl:value-of select="$sLabel"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>Page</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            <tex:cmd name="par" nl2="1"/>
        </xsl:if>
        <xsl:for-each select="//figure[not(ancestor::endnote or ancestor::framedUnit)]">
            <xsl:variable name="sFigureNumber">
                <xsl:call-template name="GetFigureNumber">
                    <xsl:with-param name="figure" select="."/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:if test="exsl:node-set($contentLayoutInfo)/figureLayout/@useSingleSpacingForLongCaptions='yes' and $sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacecontents!='yes'">
                <tex:spec cat="bg"/>
                <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
            </xsl:if>
            <xsl:call-template name="OutputTOCLine">
                <xsl:with-param name="sLink" select="@id"/>
                <xsl:with-param name="sLabel">
                    <xsl:choose>
                        <xsl:when test="exsl:node-set($contentLayoutInfo)/figureLayout/@listOfFiguresUsesFigureAndPageHeaders='yes'">
                            <xsl:value-of select="exsl:node-set($styleSheetFigureNumberLayout)/@textbefore"/>
                            <xsl:value-of select="$sFigureNumber"/>
                            <xsl:value-of select="exsl:node-set($styleSheetFigureNumberLayout)/@textafter"/>
                            <xsl:text>&#xa0;</xsl:text>
                            <xsl:text>&#xa0;</xsl:text>
                            <!--                            <xsl:value-of select="exsl:node-set($styleSheetFigureCaptionLayout)/@textbefore"/>-->
                            <xsl:apply-templates select="caption" mode="contents"/>
                            <xsl:value-of select="exsl:node-set($styleSheetFigureCaptionLayout)/@textafter"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="OutputFigureLabelAndCaption">
                                <xsl:with-param name="bDoStyles" select="'N'"/>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:with-param>
                <xsl:with-param name="sIndent">
                    <xsl:text>0pt</xsl:text>
                </xsl:with-param>
                <xsl:with-param name="sNumWidth">
                    <xsl:choose>
                        <xsl:when test="exsl:node-set($contentLayoutInfo)/figureLayout/@listOfFiguresUsesFigureAndPageHeaders='yes'">
                            <xsl:choose>
                                <xsl:when test="string-length($sFigureNumber)=1">
                                    <tex:cmd name="XLingPapersingledigitlistofwidth"/>
                                </xsl:when>
                                <xsl:when test="string-length($sFigureNumber)=2">
                                    <tex:cmd name="XLingPaperdoubledigitlistofwidth"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <tex:cmd name="XLingPapertripledigitlistofwidth"/>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>0pt</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:with-param>
            </xsl:call-template>
            <xsl:if test="exsl:node-set($contentLayoutInfo)/figureLayout/@useSingleSpacingForLongCaptions='yes' and $sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacecontents!='yes'">
                <tex:spec cat="eg"/>
            </xsl:if>
        </xsl:for-each>
        <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacecontents='yes'">
            <tex:spec cat="eg"/>
        </xsl:if>
    </xsl:template>
    <!--
        tablenumbered
    -->
    <xsl:template match="tablenumbered">
        <xsl:choose>
            <xsl:when test="descendant::endnote or @location='here'">
                <!--  cannot have endnotes in floats... If the user says, Put it here, don't treat it like a float-->
                <!--  why do we do this?? -->
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
                <xsl:if
                    test="exsl:node-set($contentLayoutInfo)/tablenumberedLayout/@captionLocation='after' or not(exsl:node-set($contentLayoutInfo)/tablenumberedLayout) and exsl:node-set($lingPaper)/@tablenumberedLabelAndCaptionLocation='after'">
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
                <xsl:if test="$sBasicPointSize!=$sLaTeXBasicPointSize">
                    <tex:spec cat="bg"/>
                    <tex:cmd name="fontsize">
                        <tex:parm>
                            <xsl:value-of select="$sBasicPointSize"/>
                        </tex:parm>
                        <tex:parm>
                            <xsl:value-of select="number($sBasicPointSize) * 1.2"/>
                        </tex:parm>
                    </tex:cmd>
                    <tex:cmd name="selectfont" gr="0" sp="1"/>
                </xsl:if>
                <xsl:call-template name="DoTableNumbered"/>
                <xsl:if test="$sBasicPointSize!=$sLaTeXBasicPointSize">
                    <tex:spec cat="eg"/>
                </xsl:if>
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
        <xsl:call-template name="DoInternalHyperlinkBegin">
            <xsl:with-param name="sName" select="@table"/>
        </xsl:call-template>
        <xsl:choose>
            <xsl:when test="@showCaption = 'short' or @showCaption='full'">
                <xsl:if test="exsl:node-set($contentLayoutInfo)/tablenumberedRefCaptionLayout">
                    <xsl:call-template name="OutputFontAttributes">
                        <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/tablenumberedRefCaptionLayout"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="exsl:node-set($contentLayoutInfo)/tablenumberedRefLayout">
                    <xsl:call-template name="OutputFontAttributes">
                        <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/tablenumberedRefLayout"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="LinkAttributesBegin">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/tablenumberedRefLinkLayout"/>
        </xsl:call-template>
        <xsl:call-template name="DoTablenumberedRef"/>
        <xsl:choose>
            <xsl:when test="@showCaption = 'short' or @showCaption='full'">
                <xsl:if test="exsl:node-set($contentLayoutInfo)/tablenumberedRefCaptionLayout">
                    <xsl:call-template name="OutputFontAttributesEnd">
                        <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/tablenumberedRefCaptionLayout"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="exsl:node-set($contentLayoutInfo)/tablenumberedRefLayout">
                    <xsl:call-template name="OutputFontAttributesEnd">
                        <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/tablenumberedRefLayout"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="DoInternalHyperlinkEnd"/>
        <xsl:call-template name="LinkAttributesEnd">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/tablenumberedRefLinkLayout"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        listOfTablesShownHere
    -->
    <xsl:template match="listOfTablesShownHere">
        <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacecontents='yes'">
            <tex:spec cat="bg"/>
            <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:if test="exsl:node-set($contentLayoutInfo)/tablenumberedLayout/@listOfTablesUsesTableAndPageHeaders='yes'">
            <tex:cmd name="noindent"/>
            <xsl:call-template name="OutputTableNumberedLabel"/>
            <tex:cmd name="hfill"/>
            <xsl:variable name="sLabel" select="normalize-space(exsl:node-set($contentLayoutInfo)/tablenumberedLayout/@pageLabelInListOfTables)"/>
            <xsl:choose>
                <xsl:when test="string-length($sLabel)&gt;0">
                    <xsl:value-of select="$sLabel"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>Page</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            <tex:cmd name="par" nl2="1"/>
        </xsl:if>
        <xsl:for-each select="//tablenumbered[not(ancestor::endnote or ancestor::framedUnit)]">
            <xsl:variable name="sTableNumber">
                <xsl:call-template name="GetTableNumberedNumber">
                    <xsl:with-param name="tablenumbered" select="."/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:if test="exsl:node-set($contentLayoutInfo)/tablenumberedLayout/@useSingleSpacingForLongCaptions='yes' and $sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacecontents!='yes'">
                <tex:spec cat="bg"/>
                <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
            </xsl:if>
            <xsl:call-template name="OutputTOCLine">
                <xsl:with-param name="sLink" select="@id"/>
                <xsl:with-param name="sLabel">
                    <xsl:choose>
                        <xsl:when test="exsl:node-set($contentLayoutInfo)/tablenumberedLayout/@listOfTablesUsesTableAndPageHeaders='yes'">
                            <xsl:value-of select="exsl:node-set($styleSheetTableNumberedNumberLayout)/@textbefore"/>
                            <xsl:value-of select="$sTableNumber"/>
                            <xsl:value-of select="exsl:node-set($styleSheetTableNumberedNumberLayout)/@textafter"/>
                            <xsl:text>&#xa0;</xsl:text>
                            <xsl:text>&#xa0;</xsl:text>
                            <!--                            <xsl:value-of select="exsl:node-set($styleSheetFigureCaptionLayout)/@textbefore"/>-->
                            <xsl:apply-templates select="table/caption | table/endCaption | caption" mode="contents"/>
                            <xsl:value-of select="exsl:node-set($styleSheetTableNumberedCaptionLayout)/@textafter"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="OutputTableNumberedLabelAndCaption">
                                <xsl:with-param name="bDoStyles" select="'N'"/>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:with-param>
                <xsl:with-param name="sIndent">
                    <xsl:text>0pt</xsl:text>
                </xsl:with-param>
                <xsl:with-param name="sNumWidth">
                    <xsl:choose>
                        <xsl:when test="exsl:node-set($contentLayoutInfo)/tablenumberedLayout/@listOfTablesUsesTableAndPageHeaders='yes'">
                            <xsl:choose>
                                <xsl:when test="string-length($sTableNumber)=1">
                                    <tex:cmd name="XLingPapersingledigitlistofwidth"/>
                                </xsl:when>
                                <xsl:when test="string-length($sTableNumber)=2">
                                    <tex:cmd name="XLingPaperdoubledigitlistofwidth"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <tex:cmd name="XLingPapertripledigitlistofwidth"/>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>0pt</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:with-param>
            </xsl:call-template>
            <xsl:if test="exsl:node-set($contentLayoutInfo)/tablenumberedLayout/@useSingleSpacingForLongCaptions='yes' and $sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacecontents!='yes'">
                <tex:spec cat="eg"/>
            </xsl:if>
        </xsl:for-each>
        <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacecontents='yes'">
            <tex:spec cat="eg"/>
        </xsl:if>
    </xsl:template>
    <!-- ===========================================================
        GLOSS
        =========================================================== -->
    <xsl:template match="gloss">
        <xsl:param name="originalContext"/>
        <xsl:param name="bReversing" select="'N'"/>
        <xsl:param name="bInMarker" select="'N'"/>
        <xsl:param name="fInContents" select="'N'"/>
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
        <xsl:variable name="sGlossContext">
            <xsl:call-template name="GetContextOfItem"/>
        </xsl:variable>
        <xsl:variable name="glossLayout" select="exsl:node-set($contentLayoutInfo)/glossLayout"/>
        <xsl:call-template name="HandleGlossTextBeforeOutside">
            <xsl:with-param name="glossLayout" select="$glossLayout"/>
            <xsl:with-param name="sGlossContext" select="$sGlossContext"/>
        </xsl:call-template>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="$language"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:call-template name="HandleGlossTextBeforeAndFontOverrides">
            <xsl:with-param name="glossLayout" select="$glossLayout"/>
            <xsl:with-param name="sGlossContext" select="$sGlossContext"/>
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
            <xsl:with-param name="fInContents" select="$fInContents"/>
        </xsl:call-template>
        <xsl:call-template name="DoEmbeddedBrEnd">
            <xsl:with-param name="iCountBr" select="$iCountBr"/>
        </xsl:call-template>
        <xsl:call-template name="HandleGlossTextAfterAndFontOverrides">
            <xsl:with-param name="glossLayout" select="$glossLayout"/>
            <xsl:with-param name="sGlossContext" select="$sGlossContext"/>
        </xsl:call-template>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="$language"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:call-template name="HandleGlossTextAfterOutside">
            <xsl:with-param name="glossLayout" select="$glossLayout"/>
            <xsl:with-param name="sGlossContext" select="$sGlossContext"/>
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
        LANGDATA
        =========================================================== -->
    <xsl:template match="langData" mode="InMarker">
        <xsl:apply-templates select="self::*"/>
    </xsl:template>
    <xsl:template match="langData">
        <xsl:param name="originalContext"/>
        <xsl:param name="bReversing" select="'N'"/>
        <xsl:param name="bInMarker" select="'N'"/>
        <xsl:param name="fInContents" select="'N'"/>
        <!-- if we are using \mbox{} to deal with unwanted hyphenation, and the langData begins with a space, we need to insert a space here -->
        <xsl:if test="substring(.,1,1)=' ' and string-length(normalize-space(//lingPaper/@xml:lang))&gt;0">
            <xsl:if test="ancestor::p or ancestor::pc or ancestor::hangingIndent">
                <xsl:text>&#x20;</xsl:text>
            </xsl:if>
        </xsl:if>
        <tex:spec cat="bg"/>
        <xsl:variable name="language" select="key('LanguageID',@lang)"/>
        <xsl:variable name="sLangDataContext">
            <xsl:call-template name="GetContextOfItem"/>
        </xsl:variable>
        <xsl:variable name="langDataLayout">
            <xsl:call-template name="GetBestLangDataLayout"/>
        </xsl:variable>
        <xsl:call-template name="HandleLangDataTextBeforeOutside">
            <xsl:with-param name="langDataLayout" select="exsl:node-set($langDataLayout)/*"/>
            <xsl:with-param name="sLangDataContext" select="$sLangDataContext"/>
        </xsl:call-template>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="$language"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:call-template name="HandleLangDataTextBeforeAndFontOverrides">
            <xsl:with-param name="langDataLayout" select="exsl:node-set($langDataLayout)/*"/>
            <xsl:with-param name="sLangDataContext" select="$sLangDataContext"/>
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
            <xsl:with-param name="fInContents" select="$fInContents"/>
        </xsl:call-template>
        <xsl:call-template name="DoEmbeddedBrEnd">
            <xsl:with-param name="iCountBr" select="$iCountBr"/>
        </xsl:call-template>
        <xsl:call-template name="HandleLangDataTextAfterAndFontOverrides">
            <xsl:with-param name="langDataLayout" select="exsl:node-set($langDataLayout)/*"/>
            <xsl:with-param name="sLangDataContext" select="$sLangDataContext"/>
        </xsl:call-template>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="$language"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:call-template name="HandleLangDataTextAfterOutside">
            <xsl:with-param name="langDataLayout" select="exsl:node-set($langDataLayout)/*"/>
            <xsl:with-param name="sLangDataContext" select="$sLangDataContext"/>
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
        endnote in back matter
    -->
    <xsl:template match="endnote" mode="backMatter">
        <xsl:param name="originalContext"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($contentLayoutInfo)/tablenumberedLayout/@captionLocation='after' or not(exsl:node-set($contentLayoutInfo)/tablenumberedLayout) and exsl:node-set($lingPaper)/@tablenumberedLabelAndCaptionLocation='after'">
                <xsl:choose>
                    <xsl:when test="ancestor::tablenumbered/table/descendant::endnote and ancestor::caption">
                        <!-- skip these for now -->
                    </xsl:when>
                    <xsl:when test="ancestor::tablenumbered/table/caption/descendant-or-self::endnote and ancestor::table">
                        <xsl:call-template name="HandleEndnoteInBackMatter">
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                            <xsl:with-param name="iTablenumberedAdjust" select="-count(ancestor::tablenumbered/table/caption/descendant-or-self::endnote)"/>
                        </xsl:call-template>
                        <xsl:if test="ancestor::tablenumbered/table/descendant::endnote[position()=last()]=.">
                            <!-- this is the last endnote in the table; now handle all endnotes in the caption -->
                            <xsl:variable name="iTablenumberedAdjust" select="count(ancestor::tablenumbered/table/tr/descendant::endnote)"/>
                            <xsl:for-each select="ancestor::tablenumbered/table/caption/descendant-or-self::endnote">
                                <xsl:call-template name="HandleEndnoteInBackMatter">
                                    <xsl:with-param name="originalContext" select="$originalContext"/>
                                    <xsl:with-param name="iTablenumberedAdjust" select="$iTablenumberedAdjust"/>
                                </xsl:call-template>
                            </xsl:for-each>
                        </xsl:if>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="HandleEndnoteInBackMatter">
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="HandleEndnoteInBackMatter">
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>
    <xsl:template name="HandleEndnoteInBackMatter">
        <xsl:param name="originalContext"/>
        <xsl:param name="iTablenumberedAdjust" select="0"/>
        <xsl:if test="$bIsBook">
            <xsl:call-template name="DoBookEndnoteSectionLabel">
                <xsl:with-param name="originalContext" select="$originalContext"/>
            </xsl:call-template>
        </xsl:if>
        <tex:cmd name="indent" gr="0" sp="1"/>
        <xsl:call-template name="DoInternalTargetBegin">
            <xsl:with-param name="sName" select="@id"/>
        </xsl:call-template>
        <xsl:call-template name="DoInternalTargetEnd"/>
        <tex:spec cat="bg"/>
        <xsl:apply-templates select="*[1]" mode="endnote-content">
            <xsl:with-param name="originalContext" select="$originalContext"/>
            <xsl:with-param name="iTablenumberedAdjust" select="$iTablenumberedAdjust"/>
        </xsl:apply-templates>
        <tex:spec cat="eg"/>
        <xsl:apply-templates select="*[position() &gt; 1]"/>
        <tex:cmd name="par" nl2="1"/>

    </xsl:template>
    <!--
        endnote in langData
    -->
    <xsl:template match="endnote[parent::langData]">
        <xsl:param name="sTeXFootnoteKind" select="'footnote'"/>
        <xsl:param name="originalContext"/>
        <!-- need to end any font attributes in effect, do the endnote, and then re-start any font attributes-->
        <xsl:variable name="language" select="key('LanguageID',../@lang)"/>
        <xsl:variable name="langDataLayout">
            <xsl:call-template name="GetBestLangDataLayout"/>
        </xsl:variable>
        <xsl:variable name="sLangDataContext">
            <xsl:call-template name="GetContextOfItem"/>
        </xsl:variable>
        <xsl:if test="$sTeXFootnoteKind='footnote'">
            <xsl:call-template name="HandleLangDataFontOverridesEnd">
                <xsl:with-param name="langDataLayout" select="exsl:node-set($langDataLayout)/*"/>
                <xsl:with-param name="sLangDataContext" select="$sLangDataContext"/>
            </xsl:call-template>
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="$language"/>
                <xsl:with-param name="originalContext" select=".."/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="DoEndnote">
            <xsl:with-param name="sTeXFootnoteKind" select="$sTeXFootnoteKind"/>
            <xsl:with-param name="originalContext" select="$originalContext"/>
        </xsl:call-template>
        <xsl:if test="$sTeXFootnoteKind='footnote'">
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="$language"/>
                <xsl:with-param name="originalContext" select=".."/>
            </xsl:call-template>
            <xsl:call-template name="HandleLangDataFontOverrides">
                <xsl:with-param name="langDataLayout" select="exsl:node-set($langDataLayout)/*"/>
                <xsl:with-param name="sLangDataContext" select="$sLangDataContext"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--
        endnote in gloss
    -->
    <xsl:template match="endnote[parent::gloss]">
        <xsl:param name="sTeXFootnoteKind" select="'footnote'"/>
        <xsl:param name="originalContext"/>
        <!-- need to end any font attributes in effect, do the endnote, and then re-start any font attributes-->
        <xsl:variable name="language" select="key('LanguageID',../@lang)"/>
        <xsl:variable name="glossLayout" select="exsl:node-set($contentLayoutInfo)/glossLayout"/>
        <xsl:variable name="sGlossContext">
            <xsl:call-template name="GetContextOfItem"/>
        </xsl:variable>
        <xsl:if test="$sTeXFootnoteKind='footnote'">
            <xsl:call-template name="HandleGlossFontOverridesEnd">
                <xsl:with-param name="glossLayout" select="$glossLayout"/>
                <xsl:with-param name="sGlossContext" select="$sGlossContext"/>
            </xsl:call-template>
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="$language"/>
                <xsl:with-param name="originalContext" select=".."/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="DoEndnote">
            <xsl:with-param name="sTeXFootnoteKind" select="$sTeXFootnoteKind"/>
            <xsl:with-param name="originalContext" select="$originalContext"/>
        </xsl:call-template>
        <xsl:if test="$sTeXFootnoteKind='footnote'">
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="$language"/>
                <xsl:with-param name="originalContext" select=".."/>
            </xsl:call-template>
            <xsl:call-template name="HandleGlossFontOverrides">
                <xsl:with-param name="glossLayout" select="$glossLayout"/>
                <xsl:with-param name="sGlossContext" select="$sGlossContext"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--
        endnote in secTitle
    -->
    <xsl:template match="endnote[parent::secTitle]">
        <xsl:param name="sTeXFootnoteKind" select="'footnote'"/>
        <xsl:param name="originalContext"/>
        <!-- need to end any font attributes in effect, do the endnote, and then re-start any font attributes-->
        <xsl:variable name="secTitleParent" select="../.."/>
        <xsl:variable name="layoutToUse">
            <xsl:choose>
                <xsl:when test="name($secTitleParent)='appendix'">
                    <xsl:copy-of select="exsl:node-set($backMatterLayoutInfo)/appendixLayout/sectionTitleLayout"/>
                </xsl:when>
                <xsl:when test="name($secTitleParent)='chapter'">
                    <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/chapterLayout/sectionTitleLayout"/>
                </xsl:when>
                <xsl:when test="name($secTitleParent)='chapterInCollection'">
                    <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/chapterInCollectionLayout/sectionTitleLayout"/>
                </xsl:when>
                <xsl:when test="name($secTitleParent)='section1'">
                    <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/section1Layout/sectionTitleLayout"/>
                </xsl:when>
                <xsl:when test="name($secTitleParent)='section2'">
                    <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/section2Layout/sectionTitleLayout"/>
                </xsl:when>
                <xsl:when test="name($secTitleParent)='section3'">
                    <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/section3Layout/sectionTitleLayout"/>
                </xsl:when>
                <xsl:when test="name($secTitleParent)='section4'">
                    <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/section4Layout/sectionTitleLayout"/>
                </xsl:when>
                <xsl:when test="name($secTitleParent)='section5'">
                    <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/section5Layout/sectionTitleLayout"/>
                </xsl:when>
                <xsl:when test="name($secTitleParent)='section6'">
                    <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/section6Layout/sectionTitleLayout"/>
                </xsl:when>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="language" select="exsl:node-set($layoutToUse)/*"/>
        <xsl:if test="$sTeXFootnoteKind='footnote' and exsl:node-set($language)/@text-transform='uppercase'">
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="$language"/>
                <xsl:with-param name="originalContext" select="$originalContext"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="DoEndnote">
            <xsl:with-param name="sTeXFootnoteKind" select="$sTeXFootnoteKind"/>
            <xsl:with-param name="originalContext" select="$originalContext"/>
        </xsl:call-template>
        <xsl:if test="$sTeXFootnoteKind='footnote' and exsl:node-set($language)/@text-transform='uppercase'">
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="$language"/>
                <xsl:with-param name="originalContext" select="$originalContext"/>
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
            <xsl:when test="exsl:node-set($backMatterLayoutInfo)/useEndNotesLayout">
                <xsl:call-template name="InsertCommaBetweenConsecutiveEndnotesUsingSuperscript"/>
                <xsl:call-template name="DoInternalHyperlinkBegin">
                    <xsl:with-param name="sName" select="@note"/>
                </xsl:call-template>
                <xsl:call-template name="LinkAttributesBegin">
                    <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/endnoteRefLinkLayout"/>
                </xsl:call-template>
                <tex:spec cat="bg"/>
                <tex:spec cat="esc"/>
                <xsl:text>textsuperscript</xsl:text>
                <tex:spec cat="bg"/>
                <xsl:call-template name="GetFootnoteNumber">
                    <xsl:with-param name="iAdjust" select="0"/>
                    <xsl:with-param name="originalContext" select="."/>
                </xsl:call-template>
                <tex:spec cat="eg"/>
                <tex:spec cat="eg"/>
                <xsl:call-template name="LinkAttributesEnd">
                    <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/endnoteRefLinkLayout"/>
                </xsl:call-template>
                <xsl:call-template name="DoInternalHyperlinkEnd"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="sFootnoteNumber">
                    <xsl:call-template name="GetFootnoteNumber">
                        <xsl:with-param name="iAdjust" select="0"/>
                        <xsl:with-param name="originalContext" select="."/>
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
                    </tex:parm>
                </tex:cmd>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        endnoteRef when using endnotes (not footnotes)
    -->
    <xsl:template match="endnoteRef" mode="backMatter">
        <xsl:if test="$bIsBook">
            <xsl:call-template name="DoBookEndnoteSectionLabel"/>
        </xsl:if>
        <tex:cmd name="indent" gr="0" sp="1"/>
        <xsl:call-template name="DoInternalTargetBegin">
            <xsl:with-param name="sName" select="@note"/>
        </xsl:call-template>
        <xsl:call-template name="DoInternalTargetEnd"/>
        <tex:spec cat="bg"/>
        <tex:spec cat="esc"/>
        <xsl:text>textsuperscript</xsl:text>
        <tex:spec cat="bg"/>
        <xsl:call-template name="GetFootnoteNumber">
            <xsl:with-param name="iAdjust" select="1"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <tex:spec cat="eg"/>
        <tex:spec cat="eg"/>
        <xsl:variable name="endnoteRefLayout" select="exsl:node-set($contentLayoutInfo)/endnoteRefLayout"/>
        <tex:group>
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="$endnoteRefLayout"/>
            </xsl:call-template>
            <xsl:choose>
                <xsl:when test="string-length(exsl:node-set($endnoteRefLayout)/@textbefore) &gt; 0">
                    <xsl:value-of select="exsl:node-set($endnoteRefLayout)/@textbefore"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>See footnote </xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="$endnoteRefLayout"/>
            </xsl:call-template>
        </tex:group>
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
        <xsl:if test="string-length(exsl:node-set($endnoteRefLayout)/@textafter) &gt; 0">
            <tex:group>
                <xsl:call-template name="OutputFontAttributes">
                    <xsl:with-param name="language" select="$endnoteRefLayout"/>
                </xsl:call-template>
                <xsl:value-of select="exsl:node-set($endnoteRefLayout)/@textafter"/>
                <xsl:call-template name="OutputFontAttributesEnd">
                    <xsl:with-param name="language" select="$endnoteRefLayout"/>
                </xsl:call-template>
            </tex:group>
        </xsl:if>
        <tex:cmd name="par" nl2="1"/>
    </xsl:template>
    <!--
      endnotes
   -->
    <xsl:template match="endnotes">
        <xsl:if test="exsl:node-set($backMatterLayoutInfo)/useEndNotesLayout">
            <xsl:choose>
                <xsl:when test="$chapters">
                    <xsl:call-template name="DoPageBreakFormatInfo">
                        <xsl:with-param name="layoutInfo" select="exsl:node-set($backMatterLayoutInfo)/useEndNotesLayout"/>
                    </xsl:call-template>
                    <xsl:call-template name="DoEndnotes"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="DoEndnotes"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <xsl:template match="img" mode="header-footer">
        <xsl:call-template name="HandleImg"/>
    </xsl:template>
    <!-- ===========================================================
      CITATIONS, Glossary, Indexes and REFERENCES 
      =========================================================== -->
    <!--
      citation
      -->
    <xsl:template match="citation[not(parent::selectedBibliography)]">
        <xsl:variable name="refer" select="id(@ref)"/>
        <xsl:call-template name="DoInternalHyperlinkBegin">
            <xsl:with-param name="sName" select="@ref"/>
        </xsl:call-template>
        <xsl:call-template name="LinkAttributesBegin">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/citationLinkLayout"/>
        </xsl:call-template>
        <xsl:call-template name="DoOutputCitationContents">
            <xsl:with-param name="refer" select="$refer"/>
        </xsl:call-template>
        <xsl:call-template name="LinkAttributesEnd">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/citationLinkLayout"/>
        </xsl:call-template>
        <xsl:call-template name="DoInternalHyperlinkEnd"/>
        <xsl:if test="parent::blockquote and count(following-sibling::text())=0 and not(following-sibling::endnote)">
            <!-- a citation ends the initial text in a blockquote; need to insert a \par -->
            <tex:cmd name="par"/>
        </xsl:if>
    </xsl:template>
    <!--
      index
      -->
    <xsl:template match="index">
        <xsl:choose>
            <xsl:when test="$bIsBook">
                <xsl:call-template name="DoPageBreakFormatInfo">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($backMatterLayoutInfo)/indexLayout"/>
                </xsl:call-template>
                <xsl:call-template name="DoIndex"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="DoIndex"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        interlinearRefCitation, show title
    -->
    <xsl:template match="interlinearRefCitation[@showTitleOnly='short' or @showTitleOnly='full']">
        <xsl:variable name="interlinearSourceStyleLayout" select="exsl:node-set($contentLayoutInfo)/interlinearSourceStyle"/>
        <xsl:call-template name="LinkAttributesBegin">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/interlinearRefLinkLayout"/>
        </xsl:call-template>
        <xsl:if test="exsl:node-set($contentLayoutInfo)/interlinearRefCitationTitleLayout">
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/interlinearRefCitationTitleLayout"/>
            </xsl:call-template>
        </xsl:if>
        <tex:group>
            <xsl:call-template name="DoInterlinearTextReferenceLinkBegin"/>
            <!-- we do not show any brackets when these options are set -->
            <xsl:call-template name="DoFormatLayoutInfoTextBefore">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($contentLayoutInfo)/interlinearRefCitationTitleLayout"/>
            </xsl:call-template>
            <xsl:call-template name="DoInterlinearRefCitationShowTitleOnly"/>
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($contentLayoutInfo)/interlinearRefCitationTitleLayout"/>
            </xsl:call-template>
            <!-- whether we used an external ref or an internal link, both end the same way -->
            <xsl:call-template name="DoInternalHyperlinkEnd"/>
        </tex:group>
        <xsl:if test="exsl:node-set($contentLayoutInfo)/interlinearRefCitationTitleLayout">
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="exsl:node-set($contentLayoutInfo)/interlinearRefCitationTitleLayout"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="LinkAttributesEnd">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/interlinearRefLinkLayout"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        interlinearRef with endnote(s) for backmatter
    -->
    <xsl:template match="interlinearRef" mode="backMatter">
        <xsl:variable name="originalContext" select="."/>
        <xsl:for-each select="key('InterlinearReferenceID',@textref)[1]">
            <xsl:apply-templates select="descendant::endnote" mode="backMatter">
                <xsl:with-param name="originalContext" select="$originalContext"/>
            </xsl:apply-templates>
        </xsl:for-each>
    </xsl:template>
    <!--
        interlinearRefCitation
    -->
    <xsl:template match="interlinearRefCitation">
        <xsl:variable name="interlinearSourceStyleLayout" select="exsl:node-set($contentLayoutInfo)/interlinearSourceStyle"/>
        <tex:spec cat="bg"/>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="$interlinearSourceStyleLayout"/>
        </xsl:call-template>
        <xsl:if test="not(@bracket) or @bracket='both' or @bracket='initial'">
            <xsl:call-template name="DoFormatLayoutInfoTextBefore">
                <xsl:with-param name="layoutInfo" select="$interlinearSourceStyleLayout"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="LinkAttributesBegin">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/interlinearRefLinkLayout"/>
        </xsl:call-template>
        <xsl:variable name="interlinear" select="key('InterlinearReferenceID',@textref)"/>
        <xsl:choose>
            <xsl:when test="name($interlinear)='interlinear-text'">
                <tex:group>
                    <xsl:call-template name="DoInterlinearTextReferenceLinkBegin"/>
                    <xsl:call-template name="LinkAttributesBegin">
                        <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/interlinearRefLinkLayout"/>
                    </xsl:call-template>
                    <xsl:choose>
                        <xsl:when test="exsl:node-set($interlinear)/textInfo/shortTitle and string-length(exsl:node-set($interlinear)/textInfo/shortTitle) &gt; 0">
                            <xsl:apply-templates select="exsl:node-set($interlinear)/textInfo/shortTitle/child::node()[name()!='endnote']"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:apply-templates select="exsl:node-set($interlinear)/textInfo/textTitle/child::node()[name()!='endnote']"/>
                        </xsl:otherwise>
                    </xsl:choose>
                    <xsl:call-template name="LinkAttributesEnd">
                        <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/interlinearRefLinkLayout"/>
                    </xsl:call-template>
                    <xsl:call-template name="DoInternalHyperlinkEnd"/>
                </tex:group>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="DoInterlinearRefCitationHyperlinkAndContent">
                    <xsl:with-param name="sRef" select="@textref"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="LinkAttributesEnd">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/interlinearRefLinkLayout"/>
        </xsl:call-template>
        <xsl:if test="not(@bracket) or @bracket='both' or @bracket='final'">
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="$interlinearSourceStyleLayout"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="$interlinearSourceStyleLayout"/>
        </xsl:call-template>
        <tex:spec cat="eg"/>
    </xsl:template>
    <!--
        backMatter
    -->
    <xsl:template match="backMatter">
        <xsl:param name="backMatterLayout" select="$backMatterLayoutInfo"/>
        <xsl:if test="exsl:node-set($backMatterLayout)/titleHeaderFooterPageStyles">
            <tex:cmd name="pagestyle">
                <tex:parm>backmattertitle</tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:call-template name="DoBackMatterPerLayout">
            <xsl:with-param name="backMatter" select="."/>
            <xsl:with-param name="backMatterLayout" select="$backMatterLayout"/>
            <xsl:with-param name="frontMatter" select="./preceding-sibling::frontMatter"/>
        </xsl:call-template>
    </xsl:template>
    <!--
      references
      -->
    <xsl:template match="references">
        <xsl:param name="backMatterLayout" select="$backMatterLayoutInfo"/>
        <xsl:choose>
            <xsl:when test="$bIsBook">
                <!--  This gets done any way in DoReferences when there are some;
        If there aren't any, then the cleardoublepage can make it so that the table of contents .toc does not get the final </toc>
        (I have no idea why...)
    <xsl:call-template name="DoPageBreakFormatInfo">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($backMatterLayoutInfo)/referencesTitleLayout"/>
                </xsl:call-template>
-->
                <xsl:call-template name="DoReferences">
                    <xsl:with-param name="backMatterLayout" select="$backMatterLayout"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="DoReferences">
                    <xsl:with-param name="backMatterLayout" select="$backMatterLayout"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        refAuthorLastName
    -->
    <xsl:template match="refAuthorLastName">
        <tex:spec cat="bg"/>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="exsl:node-set($referencesLayoutInfo)/refAuthorLayouts/refAuthorLastNameLayout"/>
        </xsl:call-template>
        <xsl:apply-templates/>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="exsl:node-set($referencesLayoutInfo)/refAuthorLayouts/refAuthorLastNameLayout"/>
        </xsl:call-template>
        <tex:spec cat="eg"/>
    </xsl:template>
    <!--
        refAuthorName
    -->
    <xsl:template match="refAuthorName">
        <tex:spec cat="bg"/>
        <xsl:apply-templates/>
        <tex:spec cat="eg"/>
    </xsl:template>
    <!--
        authorContactInfo
    -->
    <xsl:template match="authorContactInfo">
        <xsl:param name="layoutInfo"/>
        <xsl:choose>
            <xsl:when test="preceding-sibling::authorContactInfo">
                <tex:cmd name="hfill"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="firstLayoutItem" select="exsl:node-set($layoutInfo)/*[position()=1]"/>
                <xsl:if test="exsl:node-set($firstLayoutItem)/@pagebreakbefore='yes'">
                    <tex:cmd name="pagebreak"/>
                </xsl:if>
                <xsl:call-template name="DoSpaceBefore">
                    <xsl:with-param name="layoutInfo" select="$firstLayoutItem"/>
                </xsl:call-template>
                <tex:cmd name="noindent"/>
                <xsl:if test="not(following-sibling::authorContactInfo)">
                    <!-- there's only one -->
                    <xsl:if test="exsl:node-set($layoutInfo)/@textalign='right' or exsl:node-set($layoutInfo)/@textalign='end' or exsl:node-set($layoutInfo)/@textalign='center'">
                        <tex:cmd name="hfill"/>
                    </xsl:if>
                </xsl:if>
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
                    <xsl:call-template name="DoAuthorContactInfoPerLayout">
                        <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                        <xsl:with-param name="authorInfo" select="key('AuthorContactID',@author)"/>
                    </xsl:call-template>
                </tex:env>
            </tex:parm>
        </tex:cmd>
        <xsl:if test="not(preceding-sibling::authorContactInfo) and not(following-sibling::authorContactInfo)">
            <!-- there's only one -->
            <xsl:if test="exsl:node-set($layoutInfo)/@textalign='center'">
                <tex:cmd name="hfill"/>
            </xsl:if>
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
                        <xsl:call-template name="LinkAttributesBegin">
                            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/abbrRefLinkLayout"/>
                        </xsl:call-template>
                    </xsl:if>
                    <xsl:call-template name="OutputFontAttributes">
                        <xsl:with-param name="language" select="key('LanguageID',../@lang)"/>
                    </xsl:call-template>
                    <xsl:variable name="sGlossContext">
                        <xsl:call-template name="GetContextOfItem"/>
                    </xsl:variable>
                    <xsl:variable name="glossLayout" select="exsl:node-set($contentLayoutInfo)/glossLayout"/>
                    <xsl:if test="$glossLayout">
                        <xsl:call-template name="HandleGlossFontOverrides">
                            <xsl:with-param name="sGlossContext" select="$sGlossContext"/>
                            <xsl:with-param name="glossLayout" select="$glossLayout"/>
                        </xsl:call-template>
                    </xsl:if>
                    <xsl:call-template name="OutputAbbrTerm">
                        <xsl:with-param name="abbr" select="id(@abbr)"/>
                    </xsl:call-template>
                    <xsl:if test="$glossLayout">
                        <xsl:call-template name="HandleGlossFontOverridesEnd">
                            <xsl:with-param name="sGlossContext" select="$sGlossContext"/>
                            <xsl:with-param name="glossLayout" select="$glossLayout"/>
                        </xsl:call-template>
                    </xsl:if>
                    <xsl:call-template name="OutputFontAttributesEnd">
                        <xsl:with-param name="language" select="key('LanguageID',../@lang)"/>
                    </xsl:call-template>
                    <xsl:if test="$bInMarker!='Y'">
                        <xsl:call-template name="LinkAttributesEnd">
                            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/abbrRefLinkLayout"/>
                        </xsl:call-template>
                        <xsl:call-template name="DoInternalHyperlinkEnd"/>
                    </xsl:if>
                </tex:group>
            </xsl:otherwise>
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
                <xsl:call-template name="DoInternalHyperlinkBegin">
                    <xsl:with-param name="sName" select="@glossaryTerm"/>
                </xsl:call-template>
                <xsl:call-template name="LinkAttributesBegin">
                    <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/glossaryTermRefLinkLayout"/>
                </xsl:call-template>
                <xsl:call-template name="OutputGlossaryTerm">
                    <xsl:with-param name="glossaryTerm" select="id(@glossaryTerm)"/>
                    <xsl:with-param name="glossaryTermRef" select="."/>
                </xsl:call-template>
                <xsl:call-template name="LinkAttributesEnd">
                    <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/glossaryTermRefLinkLayout"/>
                </xsl:call-template>
                <xsl:call-template name="DoInternalHyperlinkEnd"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- ===========================================================
        ELEMENTS TO IGNORE
        =========================================================== -->
    <!--  ignore these -->
    <xsl:template match="basicPointSize"/>
    <xsl:template match="blockQuoteIndent"/>
    <xsl:template match="citation[parent::selectedBibliography]"/>
    <xsl:template match="defaultFontFamily"/>
    <xsl:template match="fixedText"/>
    <xsl:template match="footerMargin"/>
    <xsl:template match="footnotePointSize"/>
    <xsl:template match="footnoteIndent"/>
    <xsl:template match="hangingIndentInitialIndent"/>
    <xsl:template match="hangingIndentNormalIndent"/>
    <xsl:template match="headerMargin"/>
    <xsl:template match="interlinearSource"/>
    <xsl:template match="magnificationFactor"/>
    <xsl:template match="pageBottomMargin"/>
    <xsl:template match="pageHeight"/>
    <xsl:template match="pageInsideMargin"/>
    <xsl:template match="pageOutsideMargin"/>
    <xsl:template match="pageTopMargin"/>
    <xsl:template match="pageWidth"/>
    <xsl:template match="paragraphIndent"/>
    <xsl:template match="publisherStyleSheetName"/>
    <xsl:template match="publisherStyleSheetPublisher"/>
    <xsl:template match="publisherStyleSheetReferencesName"/>
    <xsl:template match="publisherStyleSheetReferencesVersion"/>
    <xsl:template match="publisherStyleSheetVersion"/>
    <xsl:template match="referencedInterlinearTexts"/>
    <!-- ===========================================================
      NAMED TEMPLATES
      =========================================================== -->
    <!--
        AddWordSpace
    -->
    <xsl:template name="AddWordSpace">
        <tex:spec cat="esc"/>
        <xsl:text>&#x20;</xsl:text>
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
        DoBookEndnotesLabeling
    -->
    <xsl:template name="DoBookEndnotesLabeling">
        <xsl:param name="originalContext"/>
        <xsl:param name="chapterOrAppendixUnit"/>
        <xsl:variable name="sFootnoteNumber">
            <xsl:call-template name="GetFootnoteNumber">
                <xsl:with-param name="originalContext" select="$originalContext"/>
            </xsl:call-template>
        </xsl:variable>
        <!-- need to consider case of a footnote in a title or author of a chapter in a collection -->
        <xsl:variable name="firstEndnote" select="ancestor::chapterInCollection/descendant::endnote[1]"/>
        <!--  and ancestor::frontMatter -->
        <xsl:if test="$sFootnoteNumber='1' and not(ancestor::chapterInCollection) or $sFootnoteNumber='1' and .=$firstEndnote">
            <tex:cmd name="vspace" nl2="1">
                <tex:parm>
                    <tex:cmd name="baselineskip"/>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="XLingPaperneedspace">
                <tex:parm>
                    <xsl:text>2</xsl:text>
                    <tex:cmd name="baselineskip" gr="0"/>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="indent" gr="0" sp="1"/>
            <tex:spec cat="bg"/>
            <tex:spec cat="esc"/>
            <xsl:text>textit</xsl:text>
            <tex:spec cat="bg"/>
            <tex:spec cat="esc"/>
            <xsl:text>textbf</xsl:text>
            <tex:spec cat="bg"/>
            <tex:cmd name="large"/>
            <xsl:call-template name="DoBookEndnotesLabelingContent">
                <xsl:with-param name="chapterOrAppendixUnit" select="$chapterOrAppendixUnit"/>
            </xsl:call-template>
            <xsl:text>&#x20;</xsl:text>
            <xsl:for-each select="$chapterOrAppendixUnit">
                <xsl:call-template name="OutputChapterNumber"/>
            </xsl:for-each>
            <tex:spec cat="eg"/>
            <tex:spec cat="eg"/>
            <tex:spec cat="eg"/>
            <tex:cmd name="par" nl2="1"/>
        </xsl:if>
    </xsl:template>
    <!--
        DoAbstractPerBookLayout
    -->
    <xsl:template name="DoAbstractPerBookLayout">
        <xsl:param name="abstractLayout"/>
        <xsl:call-template name="DoFrontMatterItemNewPage">
            <xsl:with-param name="id" select="concat($sAbstractID,count(preceding-sibling::abstract))"/>
            <xsl:with-param name="sTitle">
                <xsl:call-template name="OutputAbstractLabel"/>
            </xsl:with-param>
            <xsl:with-param name="layoutInfo" select="$abstractLayout"/>
            <xsl:with-param name="sRunningHeader">
                <xsl:call-template name="OutputAbstractLabel">
                    <xsl:with-param name="fUseShortTitleIfExists" select="'Y'"/>
                </xsl:call-template>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--
        DoAbstractPerPaperLayout
    -->
    <xsl:template name="DoAbstractPerPaperLayout">
        <xsl:param name="abstractLayout"/>
        <xsl:variable name="abstractTextLayoutInfo" select="exsl:node-set($abstractLayout)/following-sibling::*[1][name()='abstractTextFontInfo']"/>
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:call-template name="OutputFrontOrBackMatterTitle">
            <xsl:with-param name="id">
                <xsl:call-template name="GetIdToUse">
                    <xsl:with-param name="sBaseId" select="concat($sAbstractID,count(preceding-sibling::abstract))"/>
                </xsl:call-template>
            </xsl:with-param>
            <xsl:with-param name="sTitle">
                <xsl:call-template name="OutputAbstractLabel"/>
            </xsl:with-param>
            <xsl:with-param name="bIsBook" select="'N'"/>
            <xsl:with-param name="layoutInfo" select="$abstractLayout"/>
            <xsl:with-param name="sRunningHeader">
                <xsl:call-template name="OutputAbstractLabel">
                    <xsl:with-param name="fUseShortTitleIfExists" select="'Y'"/>
                </xsl:call-template>
            </xsl:with-param>
        </xsl:call-template>
        <xsl:choose>
            <xsl:when test="$abstractTextLayoutInfo">
                <tex:group>
                    <!-- Note: I do not know yet if these work well with RTL scripts or if they need to be flipped -->
                    <xsl:if test="string-length(normalize-space(exsl:node-set($abstractTextLayoutInfo)/@start-indent)) &gt; 0">
                        <tex:spec cat="esc"/>
                        <xsl:text>leftskip</xsl:text>
                        <xsl:value-of select="normalize-space(exsl:node-set($abstractTextLayoutInfo)/@start-indent)"/>
                        <xsl:text>&#x20;</xsl:text>
                    </xsl:if>
                    <xsl:if test="string-length(normalize-space(exsl:node-set($abstractTextLayoutInfo)/@end-indent)) &gt; 0">
                        <tex:spec cat="esc"/>
                        <xsl:text>rightskip</xsl:text>
                        <xsl:value-of select="normalize-space(exsl:node-set($abstractTextLayoutInfo)/@end-indent)"/>
                        <xsl:text>&#x20;</xsl:text>
                    </xsl:if>
                    <xsl:if test="exsl:node-set($abstractTextLayoutInfo)/@textalign='start' or exsl:node-set($abstractTextLayoutInfo)/@textalign='left'">
                        <tex:cmd name="noindent" gr="0" nl2="1"/>
                    </xsl:if>
                    <xsl:call-template name="OutputFontAttributesInAbstract">
                        <xsl:with-param name="language" select="$abstractTextLayoutInfo"/>
                        <xsl:with-param name="originalContext" select="."/>
                    </xsl:call-template>
                    <xsl:if test="exsl:node-set($abstractTextLayoutInfo)/@textalign">
                        <xsl:call-template name="DoTextAlign">
                            <xsl:with-param name="layoutInfo" select="$abstractTextLayoutInfo"/>
                        </xsl:call-template>
                    </xsl:if>
                    <xsl:apply-templates/>
                    <xsl:variable name="contentForThisElement">
                        <xsl:apply-templates/>
                    </xsl:variable>
                    <xsl:if test="exsl:node-set($abstractTextLayoutInfo)/@textalign">
                        <xsl:call-template name="DoTextAlignEnd">
                            <xsl:with-param name="layoutInfo" select="$abstractTextLayoutInfo"/>
                            <xsl:with-param name="contentForThisElement" select="$contentForThisElement"/>
                        </xsl:call-template>
                    </xsl:if>
                    <xsl:call-template name="OutputFontAttributesInAbstractEnd">
                        <xsl:with-param name="language" select="$abstractTextLayoutInfo"/>
                        <xsl:with-param name="originalContext" select="."/>
                    </xsl:call-template>
                </tex:group>
                <xsl:call-template name="DoSpaceAfter">
                    <xsl:with-param name="layoutInfo" select="$abstractLayout"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="endlandscape" gr="0" nl2="1"/>
        </xsl:if>
    </xsl:template>
    <!--  
        DoAppendiciesTitlePage
    -->
    <xsl:template name="DoAppendiciesTitlePage">
        <xsl:call-template name="OutputFrontOrBackMatterTitle">
            <xsl:with-param name="id" select="$sAppendiciesPageID"/>
            <xsl:with-param name="sTitle">
                <xsl:call-template name="OutputAppendiciesLabel"/>
            </xsl:with-param>
            <xsl:with-param name="layoutInfo" select="exsl:node-set($backMatterLayoutInfo)/appendicesTitlePageLayout"/>
            <xsl:with-param name="sRunningHeader">
                <xsl:call-template name="OutputAppendiciesLabel"/>
            </xsl:with-param>
        </xsl:call-template>
        <xsl:call-template name="OutputBookmark">
            <xsl:with-param name="sLink" select="$sAppendiciesPageID"/>
            <xsl:with-param name="sLabel">
                <xsl:call-template name="OutputAppendiciesLabel"/>
            </xsl:with-param>
        </xsl:call-template>
        <xsl:apply-templates/>
    </xsl:template>
    <!--  
        DoAnnotation
    -->
    <xsl:template name="DoAnnotation">
    <xsl:param name="sAnnotation"/>
    <xsl:if test="$sAnnotation">
        <tex:group>
            <xsl:variable name="sStartIndent" select="normalize-space(exsl:node-set($annotationLayoutInfo)/@start-indent)"/>
            <tex:spec cat="esc"/>
            <xsl:text>leftskip</xsl:text>
            <xsl:choose>
                <xsl:when test="parent::example">
                    <tex:cmd name="XLingPaperannoinexampleindent" gr="0" nl2="0"/>
                </xsl:when>
                <xsl:when test="string-length($sStartIndent) &gt; 0">
                    <xsl:value-of select="$sStartIndent"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>.25in</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            <tex:cmd name="relax" gr="0" nl2="1"/>
            <xsl:variable name="sEndIndent" select="normalize-space(exsl:node-set($annotationLayoutInfo)/@end-indent)"/>
            <xsl:if test="string-length($sEndIndent) &gt; 0">
                <tex:spec cat="esc"/>
                <xsl:text>rightskip</xsl:text>
                <xsl:value-of select="$sEndIndent"/>
                <tex:cmd name="relax" gr="0" nl2="1"/>
            </xsl:if>
            <tex:cmd name="vspace">
                <tex:parm>
                    <xsl:variable name="sSpaceBefore" select="normalize-space(exsl:node-set($annotationLayoutInfo)/@spacebefore)"/>
                    <xsl:choose>
                        <xsl:when test="string-length($sSpaceBefore) &gt; 0">
                            <xsl:value-of select="$sSpaceBefore"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>3pt</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </tex:parm>
            </tex:cmd>
            <tex:cmd name="noindent"/>
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="$annotationLayoutInfo"/>
            </xsl:call-template>
            <xsl:call-template name="OutputCannedText">
                <xsl:with-param name="sCannedText" select="exsl:node-set($annotationLayoutInfo)/@textbefore"/>
            </xsl:call-template>
            <xsl:apply-templates select="key('AnnotationID',$sAnnotation)"/>
            <xsl:call-template name="OutputCannedText">
                <xsl:with-param name="sCannedText" select="exsl:node-set($annotationLayoutInfo)/@textafter"/>
            </xsl:call-template>
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="$annotationLayoutInfo"/>
            </xsl:call-template>
            <tex:cmd name="par"/>
            <tex:cmd name="vspace">
                <tex:parm>
                    <xsl:variable name="sSpaceAfter" select="normalize-space(exsl:node-set($annotationLayoutInfo)/@spaceafter)"/>
                    <xsl:choose>
                        <xsl:when test="string-length($sSpaceAfter) &gt; 0">
                            <xsl:value-of select="$sSpaceAfter"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>3pt</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </tex:parm>
            </tex:cmd>
        </tex:group>
    </xsl:if>
</xsl:template>
    <!--  
        DoAuthorOfChapterInCollectionInContents
    -->
    <xsl:template name="DoAuthorOfChapterInCollectionInContents">
        <xsl:if test="saxon:node-set($authorInContentsLayoutInfo)/authorLayout">
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
                <xsl:call-template name="DoSpaceBefore">
                    <xsl:with-param name="layoutInfo" select="saxon:node-set($authorInContentsLayoutInfo)/authorLayout"/>
                </xsl:call-template>
                <!-- do author(s) -->
                <xsl:call-template name="OutputPlainTOCLine">
                    <xsl:with-param name="sIndent">
                        <tex:cmd name="leveloneindent" gr="0"/>
                    </xsl:with-param>
                    <xsl:with-param name="sLabel">
                        <xsl:call-template name="OutputFontAttributes">
                            <xsl:with-param name="language" select="saxon:node-set($authorInContentsLayoutInfo)/authorLayout"/>
                        </xsl:call-template>
                        <xsl:value-of select="saxon:node-set($authorInContentsLayoutInfo)/authorLayout/@textbefore"/>
                        <xsl:call-template name="GetAuthorsAsCommaSeparatedList"/>
                        <xsl:value-of select="saxon:node-set($authorInContentsLayoutInfo)/authorLayout/@textafter"/>
                        <xsl:call-template name="OutputFontAttributesEnd">
                            <xsl:with-param name="language" select="saxon:node-set($authorInContentsLayoutInfo)/authorLayout"/>
                        </xsl:call-template>
                    </xsl:with-param>
                </xsl:call-template>
                <xsl:call-template name="DoSpaceAfter">
                    <xsl:with-param name="layoutInfo" select="saxon:node-set($authorInContentsLayoutInfo)/authorLayout"/>
                </xsl:call-template>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
      DoBackMatterBookmarksPerLayout
   -->
    <xsl:template name="DoBackMatterBookmarksPerLayout">
        <xsl:param name="nLevel"/>
        <xsl:param name="backMatter" select="exsl:node-set($lingPaper)/backMatter"/>
        <xsl:param name="backMatterLayout" select="$backMatterLayoutInfo"/>
        <xsl:for-each select="exsl:node-set($backMatterLayout)/*">
            <xsl:choose>
                <xsl:when test="name(.)='acknowledgementsLayout'">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/acknowledgements" mode="bookmarks"/>
                </xsl:when>
                <xsl:when test="name(.)='appendicesTitlePageLayout'">
                    <xsl:if test="count(//appendix)&gt;1">
                        <xsl:call-template name="OutputBookmark">
                            <xsl:with-param name="sLink" select="$sAppendiciesPageID"/>
                            <xsl:with-param name="sLabel">
                                <xsl:call-template name="OutputAppendiciesLabel"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="name(.)='appendixLayout'">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/appendix" mode="bookmarks">
                        <xsl:with-param name="nLevel" select="$nLevel"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='glossaryLayout'">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/glossary" mode="bookmarks">
                        <xsl:with-param name="iLayoutPosition">
                            <xsl:choose>
                                <xsl:when test="preceding-sibling::glossaryLayout or following-sibling::glossaryLayout">
                                    <xsl:value-of select="count(preceding-sibling::glossaryLayout) + 1"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>0</xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:with-param>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='contentsLayout'">
                    <xsl:apply-templates select="exsl:node-set($lingPaper)/frontMatter/contents" mode="bookmarks"/>
                </xsl:when>
                <xsl:when test="name(.)='indexLayout'">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/index" mode="bookmarks"/>
                </xsl:when>
                <xsl:when test="name(.)='keywordsLayout'">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/keywordsShownHere[@showincontents='yes']" mode="bookmarks"/>
                </xsl:when>
                <xsl:when test="name(.)='referencesLayout'">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/references" mode="bookmarks"/>
                </xsl:when>
                <xsl:when test="name(.)='useEndNotesLayout'">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/endnotes" mode="bookmarks"/>
                </xsl:when>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>
    <!--  
        DoBackMatterContentsPerLayout
    -->
    <xsl:template name="DoBackMatterContentsPerLayout">
        <xsl:param name="nLevel" select="$nLevel"/>
        <xsl:param name="backMatter" select="exsl:node-set($lingPaper)/backMatter"/>
        <xsl:param name="backMatterLayout" select="$backMatterLayoutInfo"/>
        <xsl:param name="contentsLayoutToUse" select="."/>
        <xsl:for-each select="exsl:node-set($backMatterLayout)/*">
            <xsl:choose>
                <xsl:when test="name(.)='acknowledgementsLayout'">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/acknowledgements" mode="contents">
                        <xsl:with-param name="text-transform" select="@text-transform"/>
                        <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='appendicesTitlePageLayout'">
                    <xsl:if test="count(//appendix)&gt;1">
                        <xsl:call-template name="OutputTOCLine">
                            <xsl:with-param name="sLink" select="$sAppendiciesPageID"/>
                            <xsl:with-param name="sLabel">
                                <xsl:call-template name="OutputAppendiciesLabel"/>
                            </xsl:with-param>
                            <xsl:with-param name="text-transform" select="@text-transform"/>
                            <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                        </xsl:call-template>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="name(.)='appendixLayout'">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/appendix" mode="contents">
                        <xsl:with-param name="nLevel" select="$nLevel"/>
                        <xsl:with-param name="text-transform" select="appendixTitleLayout/@text-transform"/>
                        <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='glossaryLayout'">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/glossary" mode="contents">
                        <xsl:with-param name="iLayoutPosition">
                            <xsl:choose>
                                <xsl:when test="preceding-sibling::glossaryLayout or following-sibling::glossaryLayout">
                                    <xsl:value-of select="count(preceding-sibling::glossaryLayout) + 1"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>0</xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:with-param>
                        <xsl:with-param name="text-transform" select="@text-transform"/>
                        <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='indexLayout'">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/index" mode="contents">
                        <xsl:with-param name="text-transform" select="@text-transform"/>
                        <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='keywordsLayout'">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/keywordsShownHere[@showincontents='yes']" mode="contents">
                        <xsl:with-param name="text-transform" select="@text-transform"/>
                        <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='referencesTitleLayout' and exsl:node-set($backMatter)[ancestor::chapterInCollection]">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/references" mode="contents">
                        <xsl:with-param name="text-transform" select="@text-transform"/>
                        <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='referencesLayout' and not(exsl:node-set($backMatter)[ancestor::chapterInCollection])">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/references" mode="contents">
                        <xsl:with-param name="text-transform" select="../referencesTitleLayout/@text-transform"/>
                        <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='useEndNotesLayout'">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/endnotes" mode="contents">
                        <xsl:with-param name="text-transform" select="@text-transform"/>
                        <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='contentsLayout'">
                    <xsl:if test="@showcontents='yes' and exsl:node-set($frontMatterLayoutInfo)/contentsLayout and exsl:node-set($backMatterLayout)/contentsLayout">
                        <xsl:apply-templates select="exsl:node-set($lingPaper)/frontMatter/contents" mode="contents">
                            <xsl:with-param name="text-transform" select="@text-transform"/>
                            <xsl:with-param name="contentsLayoutToUse" select="."/>
                        </xsl:apply-templates>
                    </xsl:if>
                </xsl:when>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>
    <!--  
        DoBackMatterPerLayout
    -->
    <xsl:template name="DoBackMatterPerLayout">
        <xsl:param name="backMatter"/>
        <xsl:param name="backMatterLayout" select="$backMatterLayoutInfo"/>
        <xsl:param name="frontMatter"/>
        <xsl:if test="exsl:node-set($lingPaper)/chapterInCollection | exsl:node-set($lingPaper)/part/chapterInCollection">
            <xsl:if test="exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles/descendant::chapterInCollectionAuthor and not(ancestor::chapterInCollection)">
                <!-- Following is a bit of a trick; find out which layout item is the first with real content by creating a variable
                    containing the position and a comma.  When done, the first one is the number before the first comma. -->
                <xsl:variable name="sItemsWithContent">
                    <xsl:for-each select="exsl:node-set($backMatterLayout)/*">
                        <xsl:choose>
                            <xsl:when test="name(.)='acknowledgementsLayout'">
                                <xsl:if test="exsl:node-set($backMatter)/acknowledgements">
                                    <xsl:value-of select="position()"/>
                                    <xsl:text>,</xsl:text>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='appendicesTitlePageLayout'">
                                <xsl:if test="exsl:node-set($backMatter)/appendix">
                                    <xsl:value-of select="position()"/>
                                    <xsl:text>,</xsl:text>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='appendixLayout'">
                                <xsl:if test="exsl:node-set($backMatter)/appendix">
                                    <xsl:value-of select="position()"/>
                                    <xsl:text>,</xsl:text>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='authorContactInfoLayout'">
                                <xsl:if test="exsl:node-set($backMatter)/authorContactInfo">
                                    <xsl:value-of select="position()"/>
                                    <xsl:text>,</xsl:text>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='glossaryLayout'">
                                <xsl:if test="exsl:node-set($backMatter)/glossary">
                                    <xsl:value-of select="position()"/>
                                    <xsl:text>,</xsl:text>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='contentsLayout' and ancestor::backMatterLayout and $chapters">
                                <xsl:value-of select="position()"/>
                                <xsl:text>,</xsl:text>
                            </xsl:when>
                            <xsl:when test="name(.)='indexLayout'">
                                <xsl:if test="exsl:node-set($backMatter)/index">
                                    <xsl:value-of select="position()"/>
                                    <xsl:text>,</xsl:text>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='keywordsLayout'">
                                <xsl:if test="exsl:node-set($backMatter)/keywordsShownHere">
                                    <xsl:value-of select="position()"/>
                                    <xsl:text>,</xsl:text>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='referencesTitleLayout'">
                                <xsl:if test="exsl:node-set($backMatter)/references">
                                    <xsl:value-of select="position()"/>
                                    <xsl:text>,</xsl:text>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='useEndNotesLayout'">
                                <xsl:if test="exsl:node-set($backMatter)/endnotes">
                                    <xsl:value-of select="position()"/>
                                    <xsl:text>,</xsl:text>
                                </xsl:if>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:for-each>
                </xsl:variable>
                <xsl:variable name="firstLayout" select="substring-before($sItemsWithContent,',')"/>
                <xsl:call-template name="DoPageBreakFormatInfo">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($backMatterLayout)/*[position()=$firstLayout]"/>
                </xsl:call-template>
            </xsl:if>
        </xsl:if>
        <xsl:if test="not(parent::chapterInCollection) and exsl:node-set($backMatterLayout)/headerFooterPageStyles">
            <tex:cmd name="pagestyle">
                <tex:parm>
                    <xsl:text>backmatter</xsl:text>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:for-each select="exsl:node-set($backMatterLayout)/*">
            <xsl:choose>
                <xsl:when test="name(.)='acknowledgementsLayout'">
                    <xsl:choose>
                        <xsl:when test="$bIsBook and not(exsl:node-set($backMatter)/ancestor::chapterInCollection)">
                            <xsl:apply-templates select="exsl:node-set($backMatter)/acknowledgements" mode="backmatter-book">
                                <xsl:with-param name="backMatterLayout" select="$backMatterLayout"/>
                            </xsl:apply-templates>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:apply-templates select="exsl:node-set($backMatter)/acknowledgements" mode="paper">
                                <xsl:with-param name="backMatterLayout" select="$backMatterLayout"/>
                            </xsl:apply-templates>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="name(.)='appendicesTitlePageLayout'">
                    <xsl:if test="count(//appendix)&gt;1">
                        <xsl:choose>
                            <xsl:when test="$bIsBook">
                                <xsl:call-template name="DoPageBreakFormatInfo">
                                    <xsl:with-param name="layoutInfo" select="exsl:node-set($backMatterLayout)/appendicesTitlePageLayout"/>
                                </xsl:call-template>
                                <xsl:call-template name="DoAppendiciesTitlePage"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="DoAppendiciesTitlePage"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="name(.)='appendixLayout'">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/appendix"/>
                </xsl:when>
                <xsl:when test="name(.)='authorContactInfoLayout'">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/authorContactInfo">
                        <xsl:with-param name="layoutInfo" select="exsl:node-set($backMatterLayout)/authorContactInfoLayout"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='glossaryLayout'">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/glossary">
                        <xsl:with-param name="backMatterLayout" select="$backMatterLayout"/>
                        <xsl:with-param name="iLayoutPosition">
                            <xsl:choose>
                                <xsl:when test="preceding-sibling::glossaryLayout or following-sibling::glossaryLayout">
                                    <xsl:value-of select="count(preceding-sibling::glossaryLayout) + 1"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>0</xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:with-param>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='contentsLayout' and exsl:node-set($backMatter)[ancestor::chapterInCollection]">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/contents" mode="paper">
                        <xsl:with-param name="frontMatterLayout" select="$backMatterLayout"/>
                        <xsl:with-param name="contentsLayoutToUse" select="exsl:node-set($backMatterLayout)/contentsLayout"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='contentsLayout' and ancestor::backMatterLayout and $chapters">
                    <xsl:apply-templates select="exsl:node-set($lingPaper)/frontMatter/contents" mode="book">
                        <xsl:with-param name="frontMatterLayout" select="$frontMatterLayoutInfo"/>
                        <xsl:with-param name="contentsLayoutToUse" select="exsl:node-set($backMatterLayoutInfo)/contentsLayout"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='contentsLayout'">
                    <xsl:apply-templates select="exsl:node-set($lingPaper)/frontMatter/contents" mode="paper">
                        <xsl:with-param name="frontMatterLayout" select="$frontMatterLayoutInfo"/>
                        <xsl:with-param name="contentsLayoutToUse" select="exsl:node-set($backMatterLayoutInfo)/contentsLayout"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='indexLayout'">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/index"/>
                </xsl:when>
                <xsl:when test="name(.)='keywordsLayout'">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/keywordsShownHere">
                        <xsl:with-param name="frontMatterLayout" select="$backMatterLayout"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='referencesLayout'">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/references">
                        <xsl:with-param name="backMatterLayout" select="$backMatterLayout"/>
                    </xsl:apply-templates>
                    <xsl:if test="@defaultfontsize != concat($sBasicPointSize,'pt') and count($refWorks) &gt; 0">
                        <!-- references changed the font size and there might be something after them; reset font size -->
                        <xsl:call-template name="HandleFontSize">
                            <xsl:with-param name="sSize">
                                <xsl:value-of select="$sBasicPointSize"/>
                                <xsl:text>pt</xsl:text>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="name(.)='referencesTitleLayout' and exsl:node-set($backMatter)[ancestor::chapterInCollection]">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/references">
                        <xsl:with-param name="backMatterLayout" select="$backMatterLayout"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='useEndNotesLayout'">
                    <xsl:apply-templates select="exsl:node-set($backMatter)/endnotes">
                        <xsl:with-param name="backMatterLayout" select="$backMatterLayout"/>
                    </xsl:apply-templates>
                </xsl:when>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>
    <!--
        DoChapterLabelInContents
    -->
    <xsl:template name="DoChapterLabelInContents">
        <xsl:param name="contentsLayoutToUse" select="saxon:node-set($contentsLayout)/contentsLayout"/>
        <xsl:variable name="sLabel" select="normalize-space(exsl:node-set($contentsLayoutToUse)/@chapterlabel)"/>
        <tex:spec cat="bg"/>
        <tex:cmd name="{$sSingleSpacingCommand}"/>
        <tex:cmd name="noindent"/>
        <xsl:choose>
            <xsl:when test="string-length($sLabel)&gt;0">
                <xsl:value-of select="$sLabel"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>Chapter</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <tex:cmd name="par"/>
        <tex:spec cat="eg"/>
    </xsl:template>
    <!--
        DoChapterNumberWidth
    -->
    <xsl:template name="DoChapterNumberWidth" priority="10">
        <xsl:param name="sChapterLineIndent"/>
        <xsl:choose>
            <xsl:when test="string-length($sChapterLineIndent)&gt;0">
                <tex:cmd name="levelonewidth" gr="0" nl2="0"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>0pt</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        DoContactInfo
    -->
    <xsl:template name="DoContactInfo">
        <xsl:param name="currentLayoutInfo"/>
        <xsl:variable name="sSpaceBefore" select="normalize-space(exsl:node-set($currentLayoutInfo)/@spacebefore)"/>
        <xsl:if test="string-length($sSpaceBefore) &gt; 0">
            <!-- create a strut (a rule with zero width but height) -->
            <tex:cmd name="rule">
                <tex:parm>
                    <xsl:text>0pt</xsl:text>
                </tex:parm>
                <tex:parm>
                    <xsl:value-of select="$sSpaceBefore"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <tex:spec cat="bg"/>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="$currentLayoutInfo"/>
        </xsl:call-template>
        <xsl:apply-templates select="."/>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="$currentLayoutInfo"/>
        </xsl:call-template>
        <tex:spec cat="eg"/>
        <tex:spec cat="esc"/>
        <tex:spec cat="esc"/>
        <xsl:variable name="sSpaceAfter" select="normalize-space(exsl:node-set($currentLayoutInfo)/@spaceafter)"/>
        <xsl:if test="string-length($sSpaceAfter) &gt; 0">
            <tex:spec cat="lsb"/>
            <xsl:value-of select="$sSpaceAfter"/>
            <tex:spec cat="rsb"/>
        </xsl:if>
    </xsl:template>
    <!--
                  DoContents
    -->
    <xsl:template name="DoContents">
        <xsl:param name="bIsBook" select="'Y'"/>
        <xsl:param name="frontMatterLayout" select="$frontMatterLayoutInfo"/>
        <xsl:param name="contentsLayoutToUse" select="$contentsLayout"/>
        <!--        <tex:cmd name="XLingPapertableofcontents" gr="0" nl2="0"/>-->
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:choose>
            <xsl:when test="$bIsBook='Y'">
                <xsl:call-template name="OutputFrontOrBackMatterTitle">
                    <xsl:with-param name="id">
                        <xsl:call-template name="CreateContentsID">
                            <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                        </xsl:call-template>
                    </xsl:with-param>
                    <xsl:with-param name="sTitle">
                        <xsl:call-template name="OutputContentsLabel">
                            <xsl:with-param name="layoutInfo" select="$contentsLayoutToUse"/>
                        </xsl:call-template>
                    </xsl:with-param>
                    <xsl:with-param name="bIsBook" select="'Y'"/>
                    <xsl:with-param name="layoutInfo" select="$contentsLayoutToUse"/>
                    <xsl:with-param name="sFirstPageStyle" select="'frontmatterfirstpage'"/>
                    <!-- page break stuff has already been done; when we changed to use raisebox for hypertarget and made the
                        content of the hypertarget be empty, we suddenly got an extra page break here.
                    -->
                    <xsl:with-param name="fDoPageBreakFormatInfo" select="'N'"/>
                    <xsl:with-param name="sRunningHeader">
                        <xsl:call-template name="OutputContentsLabel">
                            <xsl:with-param name="fUseShortTitleIfExists" select="'Y'"/>
                            <xsl:with-param name="layoutInfo" select="$contentsLayoutToUse"/>
                        </xsl:call-template>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="OutputFrontOrBackMatterTitle">
                    <xsl:with-param name="id">
                        <xsl:call-template name="CreateContentsID">
                            <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                        </xsl:call-template>
                    </xsl:with-param>
                    <xsl:with-param name="sTitle">
                        <xsl:call-template name="OutputContentsLabel">
                            <xsl:with-param name="layoutInfo" select="$contentsLayoutToUse"/>
                        </xsl:call-template>
                    </xsl:with-param>
                    <xsl:with-param name="bIsBook" select="'N'"/>
                    <xsl:with-param name="layoutInfo" select="$contentsLayoutToUse"/>
                    <xsl:with-param name="sRunningHeader">
                        <xsl:call-template name="OutputContentsLabel">
                            <xsl:with-param name="fUseShortTitleIfExists" select="'Y'"/>
                            <xsl:with-param name="layoutInfo" select="$contentsLayoutToUse"/>
                        </xsl:call-template>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacecontents='yes'">
            <tex:spec cat="bg"/>
            <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:call-template name="DoFrontMatterContentsPerLayout">
            <xsl:with-param name="frontMatter" select=".."/>
            <xsl:with-param name="frontMatterLayout" select="$frontMatterLayout"/>
            <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
        </xsl:call-template>
        <xsl:variable name="nLevelToUse">
            <xsl:call-template name="GetContentsLevelToUse">
                <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="chapterInCollection" select="ancestor::chapterInCollection"/>
        <xsl:choose>
            <xsl:when test="$chapterInCollection">
                <xsl:apply-templates select="exsl:node-set($chapterInCollection)/section1" mode="contents">
                    <xsl:with-param name="nLevel" select="$nLevelToUse"/>
                    <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                </xsl:apply-templates>
                <xsl:call-template name="DoBackMatterContentsPerLayout">
                    <xsl:with-param name="nLevel" select="$nLevelToUse"/>
                    <xsl:with-param name="backMatter" select="exsl:node-set($chapterInCollection)/backMatter"/>
                    <xsl:with-param name="backMatterLayout" select="exsl:node-set($bodyLayoutInfo)/chapterInCollectionBackMatterLayout"/>
                    <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <!-- part -->
                <xsl:apply-templates select="exsl:node-set($lingPaper)/part" mode="contents">
                    <xsl:with-param name="nLevel" select="$nLevelToUse"/>
                    <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                </xsl:apply-templates>
                <!--                 chapter, no parts -->
                <xsl:apply-templates select="exsl:node-set($lingPaper)/chapter[not($parts)] | exsl:node-set($lingPaper)//chapterInCollection[not($parts)]" mode="contents">
                    <xsl:with-param name="nLevel" select="$nLevelToUse"/>
                    <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                </xsl:apply-templates>
                <!-- section, no chapters -->
                <xsl:apply-templates select="//lingPaper/section1" mode="contents">
                    <xsl:with-param name="nLevel" select="$nLevelToUse"/>
                    <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                </xsl:apply-templates>
                <xsl:call-template name="DoBackMatterContentsPerLayout">
                    <xsl:with-param name="nLevel" select="$nLevelToUse"/>
                    <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacecontents='yes'">
            <tex:spec cat="eg"/>
        </xsl:if>
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="endlandscape" gr="0" nl2="1"/>
        </xsl:if>
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
        DoEndnote
    -->
    <xsl:template name="DoEndnote">
        <xsl:param name="sTeXFootnoteKind"/>
        <xsl:param name="originalContext"/>
        <xsl:param name="sPrecalculatedNumber" select="''"/>
        <xsl:choose>
            <xsl:when test="$originalContext and ancestor::interlinear-text">
                <!-- do nothing for an interlinearRef containing an endnote -->
            </xsl:when>
            <xsl:when test="exsl:node-set($backMatterLayoutInfo)/useEndNotesLayout">
                <xsl:call-template name="InsertCommaBetweenConsecutiveEndnotesUsingSuperscript"/>
                <xsl:choose>
                    <xsl:when test="ancestor::tablenumbered">
                        <tex:cmd name="footnotemark"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="DoFootnoteNumberInText">
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                            <xsl:with-param name="sPrecalculatedNumber" select="$sPrecalculatedNumber"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="$sTeXFootnoteKind!='footnotetext'">
                    <xsl:call-template name="InsertCommaBetweenConsecutiveEndnotesUsingSuperscript"/>
                </xsl:if>
                <xsl:choose>
                        <xsl:when test="exsl:node-set($documentLayoutInfo)/footnoteLayout/@linkNumberToText='yes'">
                        <tex:cmd name="hyperlink">
                            <tex:parm>
                                <xsl:value-of select="@id"/>
                            </tex:parm>
                            <tex:parm>
                                <xsl:call-template name="DoEndnoteContent">
                                    <xsl:with-param name="sTeXFootnoteKind" select="$sTeXFootnoteKind"/>
                                    <xsl:with-param name="originalContext" select="$originalContext"/>
                                    <xsl:with-param name="sPrecalculatedNumber" select="$sPrecalculatedNumber"/>
                                </xsl:call-template>
                            </tex:parm>
                        </tex:cmd>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="DoEndnoteContent">
                            <xsl:with-param name="sTeXFootnoteKind" select="$sTeXFootnoteKind"/>
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                            <xsl:with-param name="sPrecalculatedNumber" select="$sPrecalculatedNumber"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="parent::blockquote and count(following-sibling::text())=0 and not(following-sibling::endnote)">
            <!-- an endnote ends the initial text in a blockquote; need to insert a \par -->
            <tex:cmd name="par"/>
        </xsl:if>
    </xsl:template>
    <!--  
        DoEndnoteContent
    -->
    <xsl:template name="DoEndnoteContent">
        <xsl:param name="sTeXFootnoteKind"/>
        <xsl:param name="originalContext"/>
        <xsl:param name="sPrecalculatedNumber"/>
        <xsl:choose>
            <xsl:when test="ancestor::td[@rowspan &gt; 0] and $sTeXFootnoteKind!='footnotetext'">
                <tex:cmd name="footnotemark">
                    <xsl:if test="not(ancestor::interlinear-text)">
                        <tex:opt>
                            <xsl:call-template name="DoFootnoteNumberInText">
                                <xsl:with-param name="originalContext" select="$originalContext"/>
                            </xsl:call-template>
                        </tex:opt>
                    </xsl:if>
                </tex:cmd>
            </xsl:when>
            <xsl:when test="count(ancestor::table) &gt; 1 and $sTeXFootnoteKind!='footnotetext' ">
                <tex:cmd name="footnotemark" gr="0"/>
                <xsl:call-template name="SetLaTeXFootnoteCounter">
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
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
                            <xsl:call-template name="DoFootnoteNumberInText">
                                <xsl:with-param name="originalContext" select="$originalContext"/>
                            </xsl:call-template>
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
                            <xsl:call-template name="DoFootnoteNumberInText">
                                <xsl:with-param name="originalContext" select="$originalContext"/>
                            </xsl:call-template>
                        </tex:opt>
                    </xsl:if>
                </tex:cmd>
            </xsl:when>
            <xsl:otherwise>
                <!--                        <xsl:if test="$originalContext and $sTeXFootnoteKind!='footnotetext'">-->
                <xsl:if test="$originalContext">
                    <xsl:call-template name="AdjustFootnoteNumberPerInterlinearRefs">
                        <xsl:with-param name="originalContext" select="$originalContext"/>
                        <xsl:with-param name="iAdjust">
                            <xsl:choose>
                                <xsl:when test="$sTeXFootnoteKind='footnotetext'">1</xsl:when>
                                <xsl:otherwise>0</xsl:otherwise>
                            </xsl:choose>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:if>
                <!-- in some contexts, \footnote needs to be \protected; we do it always since it is not easy to determine such contexts-->
                <tex:cmd name="protect" gr="0"/>
                <tex:cmd name="{$sTeXFootnoteKind}">
                    <xsl:if test="$sTeXFootnoteKind='footnotetext' or not(ancestor::table)">
                        <!-- longtable will not handle the forced footnote number if the column has a 'p' columns spec, so we punt and just use plain \footnote -->
                        <xsl:if test="not(ancestor::interlinear-text) and not(ancestor::listDefinition) and not(ancestor::listSingle)">
                            <tex:opt>
                                <xsl:call-template name="DoFootnoteNumberInText">
                                    <xsl:with-param name="originalContext" select="$originalContext"/>
                                    <xsl:with-param name="sPrecalculatedNumber" select="$sPrecalculatedNumber"/>
                                </xsl:call-template>
                            </tex:opt>
                        </xsl:if>
                        <xsl:if test="ancestor::interlinear-text and following-sibling::endnote">
                            <xsl:if test="ancestor::free or ancestor::literal">
                                <tex:opt>
                                    <xsl:call-template name="DoFootnoteNumberInText">
                                        <xsl:with-param name="originalContext" select="$originalContext"/>
                                        <xsl:with-param name="sPrecalculatedNumber" select="$sPrecalculatedNumber"/>
                                    </xsl:call-template>
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
    </xsl:template>
    <!--  
      DoEndnotes
   -->
    <xsl:template name="DoEndnotes">
        <xsl:if test="contains($endnotesToShow,'X')">
            <xsl:call-template name="OutputBackMatterItemTitle">
                <xsl:with-param name="sId" select="$sEndnotesID"/>
                <xsl:with-param name="sLabel">
                    <xsl:call-template name="OutputEndnotesLabel"/>
                </xsl:with-param>
                <xsl:with-param name="layoutInfo" select="exsl:node-set($backMatterLayoutInfo)/useEndNotesLayout"/>
                <xsl:with-param name="sRunningHeader">
                    <xsl:call-template name="OutputEndnotesLabel">
                        <xsl:with-param name="fUseShortTitleIfExists" select="'Y'"/>
                    </xsl:call-template>
                </xsl:with-param>
            </xsl:call-template>
            <xsl:if test="$sLineSpacing and $sLineSpacing!='single'">
                <xsl:choose>
                    <xsl:when test="exsl:node-set($lineSpacing)/@singlespaceendnotes='yes'">
                        <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
                    </xsl:when>
                    <xsl:when test="$sLineSpacing='double'">
                        <tex:cmd name="doublespacing" gr="0" nl2="1"/>
                    </xsl:when>
                    <xsl:when test="$sLineSpacing='spaceAndAHalf'">
                        <tex:cmd name="onehalfspacing" gr="0" nl2="1"/>
                    </xsl:when>
                </xsl:choose>
            </xsl:if>
            <xsl:apply-templates select="//endnote[not(ancestor::referencedInterlinearText)] | //endnoteRef[not(ancestor::endnote)][not(@showNumberOnly='yes')]" mode="backMatter"/>
            <!--        <xsl:for-each select="//endnote">
            <tex:cmd name="indent" gr="0" sp="1"/>
            <xsl:if test="exsl:node-set($backMatterLayoutInfo)/useEndNotesLayout">
                <xsl:call-template name="DoInternalTargetBegin">
                    <xsl:with-param name="sName" select="@id"/>
                </xsl:call-template>
                <xsl:call-template name="DoInternalTargetEnd"/>
            </xsl:if>
            <!-\-            <tex:spec cat="esc"/>-\->
            <!-\-       <xsl:text>footnotesize</xsl:text>
            <tex:spec cat="bg"/>
            <tex:spec cat="esc"/>
            <xsl:text>textsuperscript</xsl:text> -\->
            <tex:spec cat="bg"/>
            <xsl:apply-templates select="*[1]" mode="endnote-content"/>
            <tex:spec cat="eg"/>
            <xsl:apply-templates select="*[position() &gt; 1]"/>
            <tex:cmd name="par" nl2="1"/>
        </xsl:for-each>-->
        </xsl:if>
    </xsl:template>
    <!--  
        DoEndnoteRefCannedText
    -->
    <xsl:template name="DoEndnoteRefCannedText">
        <xsl:variable name="endnoteRefLayout" select="exsl:node-set($contentLayoutInfo)/endnoteRefLayout"/>
        <tex:group>
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="$endnoteRefLayout"/>
            </xsl:call-template>
            <xsl:choose>
                <xsl:when test="string-length(exsl:node-set($endnoteRefLayout)/@textbefore) &gt; 0">
                    <xsl:value-of select="exsl:node-set($endnoteRefLayout)/@textbefore"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>See footnote </xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="$endnoteRefLayout"/>
            </xsl:call-template>
        </tex:group>
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
        <xsl:if test="string-length(exsl:node-set($endnoteRefLayout)/@textafter) &gt; 0">
            <tex:group>
                <xsl:call-template name="OutputFontAttributes">
                    <xsl:with-param name="language" select="$endnoteRefLayout"/>
                </xsl:call-template>
                <xsl:value-of select="exsl:node-set($endnoteRefLayout)/@textafter"/>
                <xsl:call-template name="OutputFontAttributesEnd">
                    <xsl:with-param name="language" select="$endnoteRefLayout"/>
                </xsl:call-template>
            </tex:group>
        </xsl:if>
    </xsl:template>
    <!--  
        DoEndnoteRefNumber
    -->
    <xsl:template name="DoEndnoteRefNumber">
        <xsl:call-template name="DoInternalHyperlinkBegin">
            <xsl:with-param name="sName" select="@note"/>
        </xsl:call-template>
        <xsl:call-template name="LinkAttributesBegin">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/endnoteRefLinkLayout"/>
        </xsl:call-template>
        <xsl:for-each select="key('EndnoteID',@note)">
            <xsl:call-template name="GetFootnoteNumber">
                <xsl:with-param name="iAdjust" select="0"/>
                <xsl:with-param name="originalContext" select="."/>
            </xsl:call-template>
        </xsl:for-each>
        <xsl:call-template name="LinkAttributesEnd">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/endnoteRefLinkLayout"/>
        </xsl:call-template>
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
                                <xsl:call-template name="GetAndFormatExampleNumber"/>
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
                <xsl:call-template name="GetAndFormatExampleNumber"/>
                <xsl:call-template name="DoInternalTargetEnd"/>
            </xsl:otherwise>
        </xsl:choose>
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
        <xsl:if test="exsl:node-set($contentLayoutInfo)/figureLayout/@captionLocation='before' or not(exsl:node-set($contentLayoutInfo)/figureLayout) and exsl:node-set($lingPaper)/@figureLabelAndCaptionLocation='before'">
            <tex:cmd name="XLingPaperneedspace">
                <tex:parm>
                    <xsl:text>3</xsl:text>
                    <tex:cmd name="baselineskip" gr="0"/>
                </tex:parm>
            </tex:cmd>
            <xsl:call-template name="DoInternalTargetBegin">
                <xsl:with-param name="sName" select="@id"/>
                <xsl:with-param name="fDoRaisebox" select="'N'"/>
            </xsl:call-template>
            <xsl:call-template name="DoInternalTargetEnd"/>
            <xsl:call-template name="CreateAddToContents">
                <xsl:with-param name="id" select="@id"/>
            </xsl:call-template>
            <xsl:call-template name="OutputFigureLabelAndCaption"/>
            <xsl:call-template name="HandleEndnotesInCaptionOfFigure"/>
            <tex:cmd name="vspace">
                <tex:parm>
                    <xsl:choose>
                        <xsl:when test="string-length($sSpaceBetweenFigureAndCaption) &gt; 0">
                            <xsl:value-of select="$sSpaceBetweenFigureAndCaption"/>
                        </xsl:when>
                        <xsl:otherwise>0pt</xsl:otherwise>
                    </xsl:choose>
                </tex:parm>
            </tex:cmd>
            <!--            <tex:spec cat="esc"/>
            <tex:spec cat="esc"/>
            <tex:spec cat="lsb"/>
            <xsl:choose>
                <xsl:when test="string-length($sSpaceBetweenFigureAndCaption) &gt; 0">
                    <xsl:value-of select="$sSpaceBetweenFigureAndCaption"/>
                </xsl:when>
                <xsl:otherwise>0pt</xsl:otherwise>
            </xsl:choose>
            <tex:spec cat="rsb"/>
-->
        </xsl:if>
        <xsl:if test="not(contains(descendant::img/@XeLaTeXSpecial,'vertical-adjustment='))">
            <tex:cmd name="leavevmode" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:apply-templates select="*[name()!='caption' and name()!='shortCaption']"/>
        <xsl:if test="exsl:node-set($contentLayoutInfo)/figureLayout/@captionLocation='before' or not(exsl:node-set($contentLayoutInfo)/figureLayout) and exsl:node-set($lingPaper)/@figureLabelAndCaptionLocation='before'">
            <xsl:if test="chart/*[position()=last()][name()='img' and not(contains(@XeLaTeXSpecial,'vertical-adjustment='))]">
                <tex:spec cat="esc"/>
                <tex:spec cat="esc"/>
            </xsl:if>
        </xsl:if>
        <xsl:call-template name="DoTypeEnd">
            <xsl:with-param name="type" select="@type"/>
        </xsl:call-template>
        <xsl:if test="exsl:node-set($contentLayoutInfo)/figureLayout/@captionLocation='after' or not(exsl:node-set($contentLayoutInfo)/figureLayout) and exsl:node-set($lingPaper)/@figureLabelAndCaptionLocation='after'">
            <xsl:for-each select="chart/*[name()!='comment']">
                <xsl:if test="position()=last() and name()='img'">
                    <tex:spec cat="esc"/>
                    <tex:spec cat="esc"/>
                </xsl:if>
            </xsl:for-each>
            <xsl:if test="not(chart/dl) and not(chart/ol) and not(chart/ul)">
                <tex:spec cat="lsb"/>
                <xsl:choose>
                    <xsl:when test="string-length($sSpaceBetweenFigureAndCaption) &gt; 0">
                        <xsl:value-of select="$sSpaceBetweenFigureAndCaption"/>
                    </xsl:when>
                    <xsl:otherwise>0pt</xsl:otherwise>
                </xsl:choose>
                <tex:spec cat="rsb"/>
            </xsl:if>
            <xsl:call-template name="DoInternalTargetBegin">
                <xsl:with-param name="sName" select="@id"/>
                <xsl:with-param name="fDoRaisebox" select="'N'"/>
            </xsl:call-template>
            <xsl:call-template name="DoInternalTargetEnd"/>
            <xsl:call-template name="CreateAddToContents">
                <xsl:with-param name="id" select="@id"/>
            </xsl:call-template>
            <xsl:call-template name="OutputFigureLabelAndCaption"/>
            <xsl:call-template name="HandleEndnotesInCaptionOfFigure"/>
            <!--            <tex:spec cat="esc"/>
            <tex:spec cat="esc"/>
-->
        </xsl:if>
        <tex:spec cat="eg"/>
        <xsl:if test="caption and descendant::img">
            <tex:cmd name="box0" gr="0"/>
            <xsl:if test="not(exsl:node-set($backMatterLayoutInfo)/useEndNotesLayout) and caption/endnote">
                <xsl:for-each select="caption/endnote">
                    <xsl:call-template name="DoEndnote">
                        <xsl:with-param name="sTeXFootnoteKind" select="'footnotetext'"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:if>
            <tex:cmd name="par"/>
            <!-- \box0\par -->
        </xsl:if>
    </xsl:template>
    <!--  
      DoFontVariant
   -->
    <xsl:template name="DoFontVariant">
        <xsl:param name="item"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($item)/@font-variant='small-caps'">
                <xsl:call-template name="HandleSmallCaps"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:attribute name="font-variant">
                    <xsl:value-of select="exsl:node-set($item)/@font-variant"/>
                </xsl:attribute>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
      DoFootnoteNumberInText
   -->
    <xsl:template name="DoFootnoteNumberInText">
        <xsl:param name="originalContext"/>
        <xsl:param name="sPrecalculatedNumber" select="''"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($backMatterLayoutInfo)/useEndNotesLayout">
                <xsl:call-template name="DoInternalHyperlinkBegin">
                    <xsl:with-param name="sName" select="@id"/>
                </xsl:call-template>
                <xsl:call-template name="LinkAttributesBegin">
                    <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/endnoteRefLinkLayout"/>
                </xsl:call-template>
                <!--                <tex:spec cat="esc"/>
                <xsl:text>footnotesize</xsl:text>
                <tex:spec cat="bg"/>
-->
                <tex:spec cat="esc"/>
                <xsl:text>textsuperscript</xsl:text>
                <tex:spec cat="bg"/>
                <xsl:choose>
                    <xsl:when test="string-length($sPrecalculatedNumber) &gt; 0">
                        <xsl:value-of select="$sPrecalculatedNumber"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="GetFootnoteMarkWhenUsingEndnotes">
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                            <xsl:with-param name="iTablenumberedAdjust" select="0"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
                <tex:spec cat="eg"/>
                <!--                <tex:spec cat="eg"/>-->
                <xsl:call-template name="LinkAttributesEnd">
                    <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/endnoteRefLinkLayout"/>
                </xsl:call-template>
                <xsl:call-template name="DoInternalHyperlinkEnd"/>
            </xsl:when>
            <xsl:otherwise>
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
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoFootnoteTextAfterFree
    -->
    <xsl:template name="DoFootnoteTextAfterFree">
        <xsl:param name="originalContext"/>
        <xsl:if test="not(exsl:node-set($backMatterLayoutInfo)/useEndNotesLayout)">
            <xsl:for-each select="descendant-or-self::endnote">
                <xsl:apply-templates select=".">
                    <xsl:with-param name="sTeXFootnoteKind" select="'footnotetext'"/>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:apply-templates>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <!--  
        DoFootnoteTextAtEndOfInLineGroup
    -->
    <xsl:template name="DoFootnoteTextAtEndOfInLineGroup">
        <xsl:param name="originalContext"/>
        <xsl:if test="not(exsl:node-set($backMatterLayoutInfo)/useEndNotesLayout)">
            <xsl:call-template name="HandleFootnoteTextInLineGroup">
                <xsl:with-param name="originalContext" select="$originalContext"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--  
        DoFootnoteTextWithinWrappableWrd
    -->
    <xsl:template name="DoFootnoteTextWithinWrappableWrd">
        <xsl:param name="originalContext"/>
        <xsl:if test="not(exsl:node-set($backMatterLayoutInfo)/useEndNotesLayout)">
            <xsl:for-each select="descendant-or-self::endnote">
                <xsl:apply-templates select=".">
                    <xsl:with-param name="sTeXFootnoteKind" select="'footnotetext'"/>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:apply-templates>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <!--  
        DoFormatLayoutInfoTextBefore
    -->
    <xsl:template name="DoFormatLayoutInfoTextBefore">
        <xsl:param name="layoutInfo"/>
        <xsl:if test="string-length(exsl:node-set($layoutInfo)/@textbefore) &gt; 0">
            <xsl:value-of select="exsl:node-set($layoutInfo)/@textbefore"/>
        </xsl:if>
    </xsl:template>
    <!--  
        DoFrontMatterFormatInfoBegin
    -->
    <xsl:template name="DoFrontMatterFormatInfoBegin">
        <xsl:param name="layoutInfo"/>
        <xsl:param name="originalContext"/>
        <xsl:param name="fSpaceBeforeAlreadyDone" select="'N'"/>
        <xsl:param name="sId" select="''"/>
        <xsl:if test="not(exsl:node-set($layoutInfo)/../@beginsparagraph='yes') and $fSpaceBeforeAlreadyDone='N'">
            <xsl:call-template name="DoSpaceBefore">
                <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:if test="not(exsl:node-set($layoutInfo)/../@beginsparagraph='yes')">
            <!-- We need to do the needspace here or we get too much extra vertical space or we can strand a title 
             at the bottom of a page. -->
            <tex:cmd name="XLingPaperneedspace">
                <tex:parm>
                    <xsl:text>3</xsl:text>
                    <tex:cmd name="baselineskip" gr="0"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:if test="exsl:node-set($layoutInfo)/@linebefore='yes'">
            <xsl:call-template name="DoLineBefore">
                <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:if test="exsl:node-set($layoutInfo)/@textalign='start' or exsl:node-set($layoutInfo)/@textalign='left' or exsl:node-set($layoutInfo)/@textalign='center'">
            <tex:cmd name="noindent" gr="0" nl2="1"/>
        </xsl:if>
        <!--<xsl:if test="ancestor::chapterInCollection and (name()='acknowledgements' or name()='abstract' or name()='preface' or name()='glossary' or name()='references')">
            <tex:cmd name="XLingPaperneedspace">
                <tex:parm>
                    <xsl:text>3</xsl:text>
                    <tex:cmd name="baselineskip" gr="0"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>-->
        <xsl:if test="string-length($sId) &gt; 0">
            <xsl:call-template name="DoInternalTargetBegin">
                <xsl:with-param name="sName" select="$sId"/>
            </xsl:call-template>
            <xsl:call-template name="DoInternalTargetEnd"/>
            <xsl:call-template name="DoBookMark"/>
        </xsl:if>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="$layoutInfo"/>
            <xsl:with-param name="originalContext" select="$originalContext"/>
        </xsl:call-template>
        <xsl:if test="string-length(exsl:node-set($layoutInfo)/@textalign) &gt; 0">
            <xsl:call-template name="DoTextAlign">
                <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="DoFormatLayoutInfoTextBefore">
            <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        DoFrontMatterFormatInfoEnd
    -->
    <xsl:template name="DoFrontMatterFormatInfoEnd">
        <xsl:param name="layoutInfo"/>
        <xsl:param name="originalContext"/>
        <xsl:param name="contentOfThisElement"/>
        <xsl:if test="string-length(exsl:node-set($layoutInfo)/@textalign) &gt; 0">
            <xsl:call-template name="DoTextAlignEnd">
                <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                <xsl:with-param name="contentForThisElement" select="$contentOfThisElement"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="$layoutInfo"/>
            <xsl:with-param name="originalContext" select="$originalContext"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
      DoFrontMatterBookmarksPerLayout
   -->
    <xsl:template name="DoFrontMatterBookmarksPerLayout">
        <xsl:param name="frontMatter" select=".."/>
        <xsl:param name="frontMatterLayout" select="$frontMatterLayoutInfo"/>
        <xsl:for-each select="exsl:node-set($frontMatterLayout)/*">
            <xsl:choose>
                <xsl:when test="name(.)='acknowledgementsLayout'">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/acknowledgements" mode="bookmarks"/>
                </xsl:when>
                <xsl:when test="name(.)='abstractLayout'">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/abstract" mode="bookmarks"/>
                </xsl:when>
                <xsl:when test="name(.)='contentsLayout'">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/contents" mode="bookmarks"/>
                </xsl:when>
                <xsl:when test="name(.)='keywordsLayout'">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/keywordsShownHere" mode="bookmarks"/>
                </xsl:when>
                <xsl:when test="name(.)='prefaceLayout'">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/preface" mode="bookmarks">
                        <xsl:with-param name="iLayoutPosition">
                            <xsl:choose>
                                <xsl:when test="preceding-sibling::prefaceLayout or following-sibling::prefaceLayout">
                                    <xsl:value-of select="count(preceding-sibling::prefaceLayout) + 1"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>0</xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:with-param>
                    </xsl:apply-templates>
                </xsl:when>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>
    <!--  
        DoFrontMatterContentsPerLayout
    -->
    <xsl:template name="DoFrontMatterContentsPerLayout">
        <xsl:param name="frontMatter" select=".."/>
        <xsl:param name="frontMatterLayout" select="$frontMatterLayoutInfo"/>
        <xsl:param name="contentsLayoutToUse" select="exsl:node-set($frontMatterLayoutInfo)/contentsLayout"/>
        <xsl:for-each select="exsl:node-set($frontMatterLayout)/*">
            <xsl:choose>
                <xsl:when test="name(.)='acknowledgementsLayout'">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/acknowledgements" mode="contents">
                        <xsl:with-param name="text-transform" select="@text-transform"/>
                        <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='abstractLayout'">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/abstract" mode="contents">
                        <xsl:with-param name="iLayoutPosition">
                            <xsl:choose>
                                <xsl:when test="preceding-sibling::abstractLayout or following-sibling::abstractLayout">
                                    <xsl:value-of select="count(preceding-sibling::abstractLayout) + 1"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>0</xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:with-param>
                        <xsl:with-param name="text-transform" select="@text-transform"/>
                        <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='keywordsLayout'">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/keywordsShownHere[@showincontents='yes']" mode="contents">
                        <xsl:with-param name="text-transform" select="@text-transform"/>
                        <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='prefaceLayout'">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/preface" mode="contents">
                        <xsl:with-param name="iLayoutPosition">
                            <xsl:choose>
                                <xsl:when test="preceding-sibling::prefaceLayout or following-sibling::prefaceLayout">
                                    <xsl:value-of select="count(preceding-sibling::prefaceLayout) + 1"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>0</xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:with-param>
                        <xsl:with-param name="text-transform" select="@text-transform"/>
                        <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='contentsLayout'">
                    <xsl:if test="@showcontents='yes'">
                        <xsl:apply-templates select="exsl:node-set($lingPaper)/frontMatter/contents" mode="contents">
                            <xsl:with-param name="text-transform" select="@text-transform"/>
                            <xsl:with-param name="contentsLayoutToUse" select="."/>
                        </xsl:apply-templates>
                    </xsl:if>
                </xsl:when>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>
    <!--  
        DoBookFrontMatterFirstStuffPerLayout
    -->
    <xsl:template name="DoBookFrontMatterFirstStuffPerLayout">
        <xsl:param name="frontMatter"/>
        <xsl:param name="frontMatterLayout" select="$frontMatterLayoutInfo"/>
        <xsl:if test="not(ancestor::chapterInCollection)">
            <tex:cmd name="pagenumbering" nl2="1">
                <tex:parm>
                    <xsl:call-template name="GetPageNumberingFormat">
                        <xsl:with-param name="sPageFormat" select="normalize-space(exsl:node-set($frontMatterLayoutInfo)/headerFooterPageStyles/descendant::pageNumber[1]/@format)"/>
                    </xsl:call-template>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:call-template name="SetStartingPageNumber"/>
        <xsl:if test="exsl:node-set($frontMatterLayout)/headerFooterPageStyles">
            <tex:cmd name="pagestyle">
                <tex:parm>frontmattertitle</tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:call-template name="HandleBasicFrontMatterPerLayout">
            <xsl:with-param name="frontMatter" select="$frontMatter"/>
            <xsl:with-param name="frontMatterLayout" select="$frontMatterLayout"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        DoBookFrontMatterPagedStuffPerLayout
    -->
    <xsl:template name="DoBookFrontMatterPagedStuffPerLayout">
        <xsl:param name="frontMatter"/>
        <xsl:param name="frontMatterLayout" select="$frontMatterLayoutInfo"/>
        <xsl:if test="exsl:node-set($frontMatterLayout)/headerFooterPageStyles">
            <xsl:choose>
                <xsl:when test="exsl:node-set($frontMatterLayout)/titleLayout/@startonoddpage='yes'">
                    <tex:cmd name="cleardoublepage" gr="0" nl2="1"/>
                </xsl:when>
                <xsl:otherwise>
                    <tex:cmd name="clearpage" gr="0" nl2="1"/>
                </xsl:otherwise>
            </xsl:choose>
            <tex:cmd name="pagestyle">
                <tex:parm>frontmatter</tex:parm>
            </tex:cmd>
            <tex:cmd name="thispagestyle">
                <tex:parm>frontmatterfirstpage</tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:for-each select="exsl:node-set($frontMatterLayout)/*">
            <xsl:choose>
                <xsl:when test="name(.)='contentsLayout'">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/contents" mode="book"/>
                </xsl:when>
                <xsl:when test="name(.)='acknowledgementsLayout'">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/acknowledgements" mode="frontmatter-book"/>
                </xsl:when>
                <xsl:when test="name(.)='abstractLayout'">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/abstract" mode="book">
                        <xsl:with-param name="iLayoutPosition">
                            <xsl:choose>
                                <xsl:when test="preceding-sibling::abstractLayout or following-sibling::abstractLayout">
                                    <xsl:value-of select="count(preceding-sibling::abstractLayout) + 1"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>0</xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:with-param>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='prefaceLayout'">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/preface" mode="book">
                        <xsl:with-param name="iLayoutPosition">
                            <xsl:choose>
                                <xsl:when test="preceding-sibling::prefaceLayout or following-sibling::prefaceLayout">
                                    <xsl:value-of select="count(preceding-sibling::prefaceLayout) + 1"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>0</xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:with-param>
                    </xsl:apply-templates>
                </xsl:when>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>
    <!--  
        DoBookMark
    -->
    <xsl:template name="DoBookMark">
        <xsl:param name="id"/>
        <xsl:param name="sTitle"/>
        <xsl:if test="saxon:node-set($contentsLayout)/contentsLayout/@showbookmarks!='no'">
            <xsl:apply-templates select="." mode="bookmarks">
                <xsl:with-param name="id" select="$id"/>
                <xsl:with-param name="sTitle" select="$sTitle"/>
            </xsl:apply-templates>
        </xsl:if>
    </xsl:template>
    <!--  
        DoBackMatterItemNewPage
    -->
    <xsl:template name="DoBackMatterItemNewPage">
        <xsl:param name="id"/>
        <xsl:param name="sTitle"/>
        <xsl:param name="layoutInfo"/>
        <xsl:param name="sRunningHeader"/>
        <xsl:call-template name="DoPageBreakFormatInfo">
            <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
        </xsl:call-template>
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:call-template name="OutputFrontOrBackMatterTitle">
            <xsl:with-param name="id" select="$id"/>
            <xsl:with-param name="sTitle" select="$sTitle"/>
            <xsl:with-param name="bIsBook" select="'Y'"/>
            <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
            <xsl:with-param name="sFirstPageStyle">
                <xsl:choose>
                    <xsl:when test="exsl:node-set($backMatterLayoutInfo)/headerFooterPageStyles/headerFooterFirstPage">
                        <xsl:text>backmatterfirstpage</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>bodyfirstpage</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:with-param>
            <!-- page break stuff has already been done; when we changed to use raisebox for hypertarget and made the
                content of the hypertarget be empty, we suddenly got an extra page break here.
            -->
            <xsl:with-param name="fDoPageBreakFormatInfo" select="'N'"/>
            <xsl:with-param name="sRunningHeader" select="$sRunningHeader"/>
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
        DoFrontMatterItemNewPage
    -->
    <xsl:template name="DoFrontMatterItemNewPage">
        <xsl:param name="id"/>
        <xsl:param name="sTitle"/>
        <xsl:param name="layoutInfo"/>
        <xsl:param name="sRunningHeader"/>
        <xsl:call-template name="DoPageBreakFormatInfo">
            <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
        </xsl:call-template>
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:call-template name="OutputFrontOrBackMatterTitle">
            <xsl:with-param name="id" select="$id"/>
            <xsl:with-param name="sTitle" select="$sTitle"/>
            <xsl:with-param name="bIsBook" select="'Y'"/>
            <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
            <xsl:with-param name="sFirstPageStyle" select="'frontmatterfirstpage'"/>
            <!-- page break stuff has already been done; when we changed to use raisebox for hypertarget and made the
                content of the hypertarget be empty, we suddenly got an extra page break here.
            -->
            <xsl:with-param name="fDoPageBreakFormatInfo" select="'N'"/>
            <xsl:with-param name="sRunningHeader" select="$sRunningHeader"/>
        </xsl:call-template>
        <xsl:apply-templates/>
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="endlandscape" gr="0" nl2="1"/>
        </xsl:if>
    </xsl:template>
    <!--  
        DoFrontMatterPerLayout
    -->
    <xsl:template name="DoFrontMatterPerLayout">
        <xsl:param name="frontMatter"/>
        <xsl:param name="frontMatterLayout" select="$frontMatterLayoutInfo"/>
        <tex:cmd name="thispagestyle" nl2="1">
            <tex:parm>fancyfirstpage</tex:parm>
        </tex:cmd>
        <xsl:call-template name="HandleBasicFrontMatterPerLayout">
            <xsl:with-param name="frontMatter" select="$frontMatter"/>
            <xsl:with-param name="frontMatterLayout" select="$frontMatterLayout"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
                  DoGlossary
-->
    <xsl:template name="DoGlossary">
        <xsl:param name="iPos" select="'1'"/>
        <xsl:param name="glossaryLayout"/>
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:call-template name="OutputBackMatterItemTitle">
            <xsl:with-param name="sId">
                <xsl:call-template name="GetIdToUse">
                    <xsl:with-param name="sBaseId" select="concat($sGlossaryID,$iPos)"/>
                </xsl:call-template>
            </xsl:with-param>
            <xsl:with-param name="sLabel">
                <xsl:call-template name="OutputGlossaryLabel"/>
            </xsl:with-param>
            <xsl:with-param name="layoutInfo" select="$glossaryLayout"/>
            <xsl:with-param name="sRunningHeader">
                <xsl:call-template name="OutputGlossaryLabel">
                    <xsl:with-param name="fUseShortTitleIfExists" select="'Y'"/>
                </xsl:call-template>
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
        DoGlossaryPerLayout
    -->
    <xsl:template name="DoGlossaryPerLayout">
        <xsl:param name="iPos"/>
        <xsl:param name="glossaryLayout"/>
        <xsl:choose>
            <xsl:when test="$bIsBook and not(ancestor::chapterInCollection)">
                <xsl:call-template name="DoPageBreakFormatInfo">
                    <xsl:with-param name="layoutInfo" select="$glossaryLayout"/>
                </xsl:call-template>
                <xsl:call-template name="DoGlossary">
                    <xsl:with-param name="iPos" select="$iPos"/>
                    <xsl:with-param name="glossaryLayout" select="$glossaryLayout"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="DoGlossary">
                    <xsl:with-param name="iPos" select="$iPos"/>
                    <xsl:with-param name="glossaryLayout" select="$glossaryLayout"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
      DoHeaderFooterItem
   -->
    <xsl:template name="DoHeaderFooterItem">
        <xsl:param name="item"/>
        <xsl:param name="originalContext"/>
        <xsl:param name="sOddEven"/>
        <tex:cmd nl2="1">
            <xsl:attribute name="name">
                <xsl:text>fancy</xsl:text>
                <xsl:choose>
                    <xsl:when test="parent::header">head</xsl:when>
                    <xsl:otherwise>foot</xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
            <tex:opt>
                <xsl:choose>
                    <xsl:when test="name()='leftHeaderFooterItem'">L</xsl:when>
                    <xsl:when test="name()='rightHeaderFooterItem'">R</xsl:when>
                    <xsl:otherwise>C</xsl:otherwise>
                </xsl:choose>
                <xsl:value-of select="$sOddEven"/>
            </tex:opt>
            <tex:parm>
                <!-- the content of this part of the header/footer -->
                <tex:parm>
                    <xsl:apply-templates select="*" mode="header-footer">
                        <xsl:with-param name="originalContext" select="$originalContext"/>
                    </xsl:apply-templates>
                </tex:parm>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        DoHeaderFooterItemFontInfo
    -->
    <xsl:template name="DoHeaderFooterItemFontInfo">
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="ancestor::headerFooterPageStyles"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="."/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:call-template name="DoFormatLayoutInfoTextBefore">
            <xsl:with-param name="layoutInfo" select="."/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        DoHeaderFooterItemFontInfoEnd
    -->
    <xsl:template name="DoHeaderFooterItemFontInfoEnd">
        <xsl:call-template name="DoFormatLayoutInfoTextAfter">
            <xsl:with-param name="layoutInfo" select="."/>
        </xsl:call-template>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="."/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="ancestor::headerFooterPageStyles"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
    </xsl:template>
    <!--  
                  DoIndex
-->
    <xsl:template name="DoIndex">
        <xsl:if test="exsl:node-set($backMatterLayoutInfo)/indexLayout/@useDoubleColumns='yes'">
            <xsl:variable name="doubleColSep" select="normalize-space(exsl:node-set($backMatterLayoutInfo)/indexLayout/@doubleColumnSeparation)"/>
            <xsl:if test="string-length($doubleColSep) &gt; 0">
                <tex:cmd name="setlength">
                    <tex:parm>
                        <tex:cmd name="columnsep" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <xsl:value-of select="$doubleColSep"/>
                    </tex:parm>
                </tex:cmd>
            </xsl:if>
            <tex:cmd name="twocolumn" gr="0"/>
            <tex:spec cat="lsb"/>
        </xsl:if>
        <xsl:variable name="sIndexLabel">
            <xsl:call-template name="OutputIndexLabel"/>
        </xsl:variable>
        <xsl:call-template name="OutputBackMatterItemTitle">
            <xsl:with-param name="sId">
                <xsl:call-template name="CreateIndexID"/>
            </xsl:with-param>
            <xsl:with-param name="sLabel" select="$sIndexLabel"/>
            <xsl:with-param name="layoutInfo" select="exsl:node-set($backMatterLayoutInfo)/indexLayout"/>
            <xsl:with-param name="sRunningHeader">
                <xsl:call-template name="OutputIndexLabel">
                    <xsl:with-param name="fUseShortTitleIfExists" select="'Y'"/>
                </xsl:call-template>
            </xsl:with-param>
        </xsl:call-template>
        <!-- process any paragraphs, etc. that may be at the beginning -->
        <xsl:apply-templates/>
        <xsl:if test="exsl:node-set($backMatterLayoutInfo)/indexLayout/@useDoubleColumns='yes'">
            <tex:spec cat="rsb"/>
            <!-- following does not 'take' in two column mode so do it again here -->
            <xsl:call-template name="DoRunningHeader">
                <xsl:with-param name="sHeader" select="$sIndexLabel"/>
            </xsl:call-template>
        </xsl:if>
        <!-- now process the contents of this index -->
        <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespaceindexes='yes'">
            <tex:spec cat="bg"/>
            <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:variable name="defaultFontSize" select="normalize-space(exsl:node-set($backMatterLayoutInfo)/indexLayout/@defaultfontize)"/>
        <xsl:if test="string-length($defaultFontSize) &gt; 0">
            <xsl:call-template name="HandleFontSize">
                <xsl:with-param name="sSize" select="$defaultFontSize"/>
            </xsl:call-template>
        </xsl:if>
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
        <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespaceindexes='yes'">
            <tex:spec cat="eg"/>
        </xsl:if>
        <!--<xsl:if test="exsl:node-set($backMatterLayoutInfo)/indexLayout/@useDoubleColumns='yes'">
            <!-\- starts a new page and we do not want one; also messes up end toc and end idx -\->
            <tex:cmd name="onecolumn" gr="0"/>
            <!-\-<tex:spec cat="lsb"/>
            <tex:spec cat="rsb"/>-\->
        </xsl:if>-->
        <xsl:if test="string-length($defaultFontSize) &gt; 0">
            <xsl:call-template name="HandleFontSize">
                <xsl:with-param name="sSize" select="concat($sBasicPointSize,'pt')"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--  
        DoInterlinearRefCitation
    -->
    <xsl:template name="DoInterlinearRefCitation">
        <xsl:param name="sRef"/>
        <tex:group>
            <xsl:variable name="interlinearSourceStyleLayout" select="exsl:node-set($contentLayoutInfo)/interlinearSourceStyle"/>
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="$interlinearSourceStyleLayout"/>
            </xsl:call-template>
            <xsl:call-template name="DoFormatLayoutInfoTextBefore">
                <xsl:with-param name="layoutInfo" select="$interlinearSourceStyleLayout"/>
            </xsl:call-template>
            <xsl:call-template name="DoInterlinearRefCitationHyperlinkAndContent">
                <xsl:with-param name="sRef" select="$sRef"/>
            </xsl:call-template>
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="$interlinearSourceStyleLayout"/>
            </xsl:call-template>
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="$interlinearSourceStyleLayout"/>
            </xsl:call-template>
        </tex:group>
    </xsl:template>
    <!--  
        DoInterlinearRefCitationHyperlinkAndContent
    -->
    <xsl:template name="DoInterlinearRefCitationHyperlinkAndContent">
        <xsl:param name="sRef"/>
        <xsl:call-template name="DoInterlinearTextReferenceLinkBegin">
            <xsl:with-param name="sRef" select="$sRef"/>
        </xsl:call-template>
        <xsl:call-template name="LinkAttributesBegin">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/interlinearRefLinkLayout"/>
        </xsl:call-template>
        <xsl:call-template name="DoInterlinearRefCitationContent">
            <xsl:with-param name="sRef" select="$sRef"/>
        </xsl:call-template>
        <xsl:call-template name="LinkAttributesEnd">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/interlinearRefLinkLayout"/>
        </xsl:call-template>
        <xsl:call-template name="DoInternalHyperlinkEnd"/>

    </xsl:template>
    <!--  
        DoISO639-3codeRefContentXeLaTeX
    -->
    <xsl:template name="DoISO639-3codeRefContentXeLaTeX">
        <xsl:if test="not(@brackets) or @brackets='both' or @brackets='initial'">[</xsl:if>
        <xsl:call-template name="LinkAttributesBegin">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/iso639-3CodesLinkLayout"/>
        </xsl:call-template>
        <xsl:call-template name="GetISO639-3CodeFromLanguage">
            <xsl:with-param name="language" select="id(@lang)"/>
        </xsl:call-template>
        <xsl:call-template name="LinkAttributesEnd">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/iso639-3CodesLinkLayout"/>
        </xsl:call-template>
        <xsl:if test="not(@brackets) or @brackets='both' or @brackets='final'">]</xsl:if>
    </xsl:template>
    <!--  
        DoLineBefore
    -->
    <xsl:template name="DoLineBefore">
        <xsl:param name="layoutInfo"/>
        <tex:cmd name="XLingPaperneedspace" nl2="1">
            <tex:parm>
                <xsl:text>3</xsl:text>
                <tex:cmd name="baselineskip" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <tex:cmd name="noindent">
            <tex:cmd name="rule" nl2="1">
                <tex:parm>
                    <tex:cmd name="textwidth" gr="0"/>
                </tex:parm>
                <tex:parm>
                    <xsl:choose>
                        <xsl:when test="exsl:node-set($layoutInfo)/sectionTitleLayout/@linebefore-weight">
                            <xsl:value-of select="normalize-space(exsl:node-set($layoutInfo)/sectionTitleLayout/@linebefore-weight)"/>
                        </xsl:when>
                        <xsl:when test="exsl:node-set($layoutInfo)/@linebefore-weight">
                            <xsl:value-of select="normalize-space(exsl:node-set($layoutInfo)/@linebefore-weight)"/>
                        </xsl:when>
                        <xsl:otherwise>0.4pt</xsl:otherwise>
                    </xsl:choose>
                </tex:parm>
            </tex:cmd>
        </tex:cmd>
        <xsl:call-template name="DoNotBreakHere"/>
    </xsl:template>
    <!--  
        DoPageBreakFormatInfo
    -->
    <xsl:template name="DoPageBreakFormatInfo">
        <xsl:param name="layoutInfo"/>
        <xsl:param name="bUseClearEmptyDoublePage" select="'N'"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($layoutInfo)/descendant-or-self::*/@startonoddpage='yes'">
                <xsl:choose>
                    <xsl:when test="$bUseClearEmptyDoublePage='Y' or exsl:node-set($layoutInfo)/descendant-or-self::*/@useblankextrapage='yes'">
                        <tex:cmd name="clearemptydoublepage" gr="0" nl2="1"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <tex:cmd name="cleardoublepage" gr="0" nl2="1"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="exsl:node-set($layoutInfo)/descendant-or-self::*/@pagebreakbefore='yes'">
                <tex:cmd name="clearpage" gr="0" nl2="1"/>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoPrefacePerBookLayout
    -->
    <xsl:template name="DoPrefacePerBookLayout">
        <xsl:param name="prefaceLayout"/>
        <xsl:call-template name="DoFrontMatterItemNewPage">
            <xsl:with-param name="id">
                <xsl:call-template name="GetIdToUse">
                    <xsl:with-param name="sBaseId" select="concat($sPrefaceID,position())"/>
                </xsl:call-template>
            </xsl:with-param>
            <xsl:with-param name="sTitle">
                <xsl:call-template name="OutputPrefaceLabel"/>
            </xsl:with-param>
            <xsl:with-param name="layoutInfo" select="$prefaceLayout"/>
            <xsl:with-param name="sRunningHeader">
                <xsl:call-template name="OutputPrefaceLabel">
                    <xsl:with-param name="fUseShortTitleIfExists" select="'Y'"/>
                </xsl:call-template>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--  
        DoPrefacePerPaperLayout
    -->
    <xsl:template name="DoPrefacePerPaperLayout">
        <xsl:param name="prefaceLayout"/>
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:call-template name="OutputFrontOrBackMatterTitle">
            <xsl:with-param name="id">
                <xsl:call-template name="GetIdToUse">
                    <xsl:with-param name="sBaseId" select="concat($sPrefaceID,position())"/>
                </xsl:call-template>
            </xsl:with-param>
            <xsl:with-param name="sTitle">
                <xsl:call-template name="OutputPrefaceLabel"/>
            </xsl:with-param>
            <xsl:with-param name="bIsBook" select="'N'"/>
            <xsl:with-param name="layoutInfo" select="$prefaceLayout"/>
            <xsl:with-param name="sRunningHeader">
                <xsl:call-template name="OutputPrefaceLabel">
                    <xsl:with-param name="fUseShortTitleIfExists" select="'Y'"/>
                </xsl:call-template>
            </xsl:with-param>
        </xsl:call-template>
        <xsl:apply-templates/>
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="endlandscape" gr="0" nl2="1"/>
        </xsl:if>
    </xsl:template>
    <!--  
        DoReferences
    -->
    <xsl:template name="DoReferences">
        <xsl:param name="backMatterLayout" select="$backMatterLayoutInfo"/>
        <xsl:variable name="refAuthors" select="refAuthor"/>
        <xsl:variable name="gtAuthors" select="exsl:node-set($refAuthors)[refWork/@id=//citation[ancestor::glossaryTerm[key('GlossaryTermRefs',@id)]]/@ref]"/>
        <xsl:variable name="directlyCitedAuthors" select="exsl:node-set($refAuthors)[refWork/@id=//citation[not(ancestor::comment) and not(ancestor::annotation) and not(ancestor::glossaryTerm)]/@ref]"/>
        <xsl:variable name="directlyCitedAuthorsAnno" select="exsl:node-set($refAuthors)[refWork/@id=//citation[ancestor::annotation[@id=//annotationRef/@annotation]]/@ref]"/>
        <xsl:if test="$directlyCitedAuthors or $directlyCitedAuthorsAnno or $gtAuthors">
            <xsl:if test="@showinlandscapemode='yes'">
                <tex:cmd name="landscape" gr="0" nl2="1"/>
            </xsl:if>
            <xsl:call-template name="OutputBackMatterItemTitle">
                <xsl:with-param name="sId">
                    <xsl:call-template name="GetIdToUse">
                        <xsl:with-param name="sBaseId" select="$sReferencesID"/>
                    </xsl:call-template>
                </xsl:with-param>
                <xsl:with-param name="sLabel">
                    <xsl:call-template name="OutputReferencesLabel"/>
                </xsl:with-param>
                <xsl:with-param name="layoutInfo" select="exsl:node-set($backMatterLayout)/referencesTitleLayout"/>
                <xsl:with-param name="sRunningHeader">
                    <xsl:call-template name="OutputReferencesLabel">
                        <xsl:with-param name="fUseShortTitleIfExists" select="'Y'"/>
                    </xsl:call-template>
                </xsl:with-param>
            </xsl:call-template>
            <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacereferences='yes'">
                <tex:spec cat="bg"/>
                <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
            </xsl:if>
            <tex:cmd name="raggedright" gr="0" nl2="1"/>
            <!--            <xsl:for-each select="$authors">
                <xsl:variable name="works" select="refWork[@id=//citation[not(ancestor::comment)]/@ref]"/>
                <xsl:for-each select="$works">
            -->
            <xsl:call-template name="HandleRefAuthors"/>
            <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacereferences='yes'">
                <tex:spec cat="eg"/>
            </xsl:if>
            <xsl:if test="@showinlandscapemode='yes'">
                <xsl:if test="contains(@XeLaTeXSpecial,'fix-final-landscape')">
                    <tex:cmd name="XLingPaperendtableofcontents" gr="0"/>
                </xsl:if>
                <tex:cmd name="endlandscape" gr="0" nl2="1"/>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        DoRefWorkPrep
    -->
    <xsl:template name="DoRefWorkPrep"/>
    <!--  
        DoRefWork
    -->
    <xsl:template name="DoRefWork">
        <xsl:param name="works"/>
        <xsl:param name="sortedWorks"/>
        <xsl:param name="bDoTarget" select="'Y'"/>
        <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak')">
            <tex:cmd name="pagebreak" gr="0" nl2="0"/>
        </xsl:if>
        <xsl:if test="exsl:node-set($referencesLayoutInfo)/@useAuthorOverDateStyle='yes' and position()!=1">
            <xsl:if test="string-length($sSpaceBetweenDates)&gt;0">
                <tex:cmd name="vspace">
                    <tex:parm>
                        <xsl:value-of select="$sSpaceBetweenDates"/>
                    </tex:parm>
                </tex:cmd>
            </xsl:if>
        </xsl:if>
        <xsl:variable name="sSpaceBefore" select="normalize-space(exsl:node-set($referencesLayoutInfo)/@spacebefore)"/>
        <xsl:if test="string-length($sSpaceBefore) &gt; 0">
            <tex:cmd name="vspace">
                <tex:parm>
                    <xsl:value-of select="$sSpaceBefore"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <tex:cmd name="hangindent" gr="0"/>
        <xsl:value-of select="exsl:node-set($referencesLayoutInfo)/@hangingindentsize"/>
        <tex:cmd name="relax" gr="0" nl2="1"/>
        <tex:cmd name="hangafter" gr="0"/>
        <xsl:text>1</xsl:text>
        <tex:cmd name="relax" gr="0" nl2="1"/>
        <xsl:variable name="work" select="."/>
        <xsl:if test="$bDoTarget='Y'">
            <xsl:if test="exsl:node-set($referencesLayoutInfo)/@defaultfontsize">
                <xsl:call-template name="HandleFontSize">
                    <xsl:with-param name="sSize" select="exsl:node-set($referencesLayoutInfo)/@defaultfontsize"/>
                </xsl:call-template>
            </xsl:if>
        </xsl:if>
        <xsl:call-template name="DoAuthorLayout">
            <xsl:with-param name="referencesLayoutInfo" select="$referencesLayoutInfo"/>
            <xsl:with-param name="work" select="$work"/>
            <xsl:with-param name="works" select="$works"/>
            <xsl:with-param name="sortedWorks" select="$sortedWorks"/>
            <xsl:with-param name="iPos" select="position()"/>
            <xsl:with-param name="bDoTarget" select="$bDoTarget"/>
        </xsl:call-template>
        <xsl:apply-templates select="book | collection | dissertation | article | fieldNotes | ms | paper | proceedings | thesis | webPage"/>
        <tex:cmd name="par" gr="0" nl2="1"/>
        <xsl:variable name="sSpaceAfter" select="normalize-space(exsl:node-set($referencesLayoutInfo)/@spaceafter)"/>
        <xsl:if test="string-length($sSpaceAfter) &gt; 0">
            <tex:cmd name="vspace">
                <tex:parm>
                    <xsl:value-of select="$sSpaceAfter"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:if test="exsl:node-set($referencesLayoutInfo)/@useAuthorOverDateStyle='yes' and position()=last()">
            <xsl:if test="string-length($sSpaceBetweenEntryAndAuthor)&gt;0">
                <tex:cmd name="vspace">
                    <tex:parm>
                        <xsl:value-of select="$sSpaceBetweenEntryAndAuthor"/>
                    </tex:parm>
                </tex:cmd>
            </xsl:if>
        </xsl:if>
        <xsl:if test="$sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacereferencesbetween='no'">
            <xsl:variable name="sExtraSpace">
                <xsl:choose>
                    <xsl:when test="$sLineSpacing='double'">
                        <xsl:value-of select="$sBasicPointSize"/>
                    </xsl:when>
                    <xsl:when test="$sLineSpacing='spaceAndAHalf'">
                        <xsl:value-of select=" number($sBasicPointSize div 2)"/>
                    </xsl:when>
                </xsl:choose>
            </xsl:variable>
            <tex:cmd name="vspace">
                <tex:parm>
                    <xsl:value-of select="$sExtraSpace"/>
                    <xsl:text>pt plus 2pt minus 1pt</xsl:text>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
    </xsl:template>
    <!--  
        DoRefWorks
    -->
<!--    <xsl:template name="DoRefWorks">
        <xsl:variable name="thisAuthor" select="."/>
        <xsl:variable name="works"
            select="refWork[@id=exsl:node-set($citations)[not(ancestor::comment) and not(ancestor::annotation)][not(ancestor::refWork) or ancestor::refWork[@id=exsl:node-set($citations)[not(ancestor::refWork)]/@ref]]/@ref] | exsl:node-set($refWorks)[@id=saxon:node-set($collOrProcVolumesToInclude)/refWork/@id][parent::refAuthor=$thisAuthor] | refWork[@id=exsl:node-set($citationsInAnnotationsReferredTo)[not(ancestor::comment)]/@ref]"/>
        <xsl:for-each select="$works">
            <xsl:call-template name="DoRefWork">
                <xsl:with-param name="works" select="$works"/>
            </xsl:call-template>
        </xsl:for-each>
    </xsl:template>
-->    <!--  
        DoSection
    -->
    <xsl:template name="DoSection">
        <xsl:param name="layoutInfo"/>
        <xsl:variable name="formatTitleLayoutInfo" select="exsl:node-set($layoutInfo)/*[name()!='numberLayout'][1]"/>
        <xsl:variable name="numberLayoutInfo" select="exsl:node-set($layoutInfo)/numberLayout"/>
        <xsl:if test="contains(@XeLaTeXSpecial,'clearpage')">
            <tex:cmd name="clearpage" gr="0" nl2="0"/>
        </xsl:if>
        <xsl:if test="contains(@XeLaTeXSpecial,'pagebreak')">
            <tex:cmd name="pagebreak" nl2="0"/>
        </xsl:if>
        <xsl:if test="@showinlandscapemode='yes'">
            <tex:cmd name="landscape" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:call-template name="DoType"/>
        <xsl:variable name="sContentsPeriod">
            <xsl:if test="not($numberLayoutInfo) and exsl:node-set($layoutInfo)/sectionTitleLayout/@useperiodafternumber='yes'">
                <xsl:text>.</xsl:text>
            </xsl:if>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="exsl:node-set($layoutInfo)/@ignore='yes'">
                <xsl:apply-templates select="child::node()[name()!='secTitle']"/>
            </xsl:when>
            <xsl:when test="exsl:node-set($layoutInfo)/@beginsparagraph='yes'">
                <xsl:call-template name="DoSectionBeginsParagraph">
                    <xsl:with-param name="formatTitleLayoutInfo" select="$formatTitleLayoutInfo"/>
                    <xsl:with-param name="numberLayoutInfo" select="$numberLayoutInfo"/>
                    <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                    <xsl:with-param name="sContentsPeriod" select="$sContentsPeriod"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="DoSectionAsTitle">
                    <xsl:with-param name="formatTitleLayoutInfo" select="$formatTitleLayoutInfo"/>
                    <xsl:with-param name="numberLayoutInfo" select="$numberLayoutInfo"/>
                    <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                    <xsl:with-param name="sContentsPeriod" select="$sContentsPeriod"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="DoTypeEnd"/>
        <xsl:if test="@showinlandscapemode='yes'">
            <xsl:if test="contains(@XeLaTeXSpecial,'fix-final-landscape')">
                <tex:cmd name="XLingPaperendtableofcontents" gr="0"/>
            </xsl:if>
            <tex:cmd name="endlandscape" gr="0" nl2="1"/>
        </xsl:if>
    </xsl:template>
    <!--  
      DoSectionAsTitle
   -->
    <xsl:template name="DoSectionAsTitle">
        <xsl:param name="formatTitleLayoutInfo"/>
        <xsl:param name="numberLayoutInfo"/>
        <xsl:param name="layoutInfo"/>
        <xsl:param name="sContentsPeriod"/>
        <tex:group>
            <xsl:if test="contains(key('TypeID',@type)/@XeLaTeXSpecial,'clearpage')">
                <tex:cmd name="clearpage" gr="0" nl2="0"/>
            </xsl:if>
            <xsl:if test="contains(key('TypeID',@type)/@XeLaTeXSpecial,'pagebreak')">
                <tex:cmd name="pagebreak" gr="0" nl2="0"/>
            </xsl:if>
            <!-- 2020.08.17
                We used to put the book mark info here because of there was a text transform, PDF would fail.
                It also caused some cases of section items to format incorrectly.
                Now it seems to work fine for sections.  Not sure what changed.
                (Maybe thr ptoblem was for chapter, appendix, front and back matter titles and not sections??)
                So we are just using the normal case for sections for now.
            -->
<!--            <xsl:variable name="sTextTransform" select="exsl:node-set($formatTitleLayoutInfo)/@text-transform"/>
            <xsl:if test="$sTextTransform='uppercase' or $sTextTransform='lowercase'">
                <xsl:call-template name="DoBookMark"/>
                <xsl:call-template name="DoInternalTargetBegin">
                    <xsl:with-param name="sName" select="@id"/>
                </xsl:call-template>
            </xsl:if>-->
            <xsl:call-template name="DoTitleFormatInfo">
                <xsl:with-param name="layoutInfo" select="$formatTitleLayoutInfo"/>
            </xsl:call-template>
<!--            <xsl:if test="string-length($sTextTransform)=0 or not($sTextTransform='uppercase' or $sTextTransform='lowercase')">-->
                <xsl:call-template name="DoBookMark"/>
                <xsl:call-template name="DoInternalTargetBegin">
                    <xsl:with-param name="sName" select="@id"/>
                </xsl:call-template>
<!--            </xsl:if>-->
            <xsl:call-template name="OutputSectionNumber">
                <xsl:with-param name="layoutInfo" select="$numberLayoutInfo"/>
                <xsl:with-param name="sContentsPeriod" select="$sContentsPeriod"/>
            </xsl:call-template>
            <xsl:call-template name="OutputSectionTitle"/>
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="$formatTitleLayoutInfo"/>
            </xsl:call-template>
            <xsl:call-template name="DoInternalTargetEnd"/>
            <xsl:variable name="contentForThisElement">
                <xsl:call-template name="OutputSectionNumber">
                    <xsl:with-param name="layoutInfo" select="$numberLayoutInfo"/>
                </xsl:call-template>
                <xsl:call-template name="OutputSectionTitle"/>
                <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                    <xsl:with-param name="layoutInfo" select="$formatTitleLayoutInfo"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:call-template name="DoTitleFormatInfoEnd">
                <xsl:with-param name="layoutInfo" select="$formatTitleLayoutInfo"/>
                <xsl:with-param name="contentOfThisElement" select="$contentForThisElement"/>
            </xsl:call-template>
            <xsl:if test="exsl:node-set($layoutInfo)/@showInHeader!='no'">
                <!-- put title in marker so it can show up in running header -->
                <xsl:call-template name="DoSectionRunningHeader">
                    <xsl:with-param name="sContentsPeriod" select="$sContentsPeriod"/>
                </xsl:call-template>

                <!-- put title in marker so it can show up in running header -->
                <!--<tex:cmd name="markright" nl2="1">
                    <tex:parm>
                        <xsl:call-template name="DoSecTitleRunningHeader">
                            <xsl:with-param name="number" select="$sectionNumberInHeaderLayout"/>
                            <xsl:with-param name="bNumberIsBeforeTitle" select="$bSectionNumberIsBeforeTitle"/>
                            <xsl:with-param name="sContentsPeriod" select="$sContentsPeriod"/>
                        </xsl:call-template>
                    </tex:parm>
                </tex:cmd>-->
            </xsl:if>
            <xsl:call-template name="CreateAddToContents">
                <xsl:with-param name="id" select="@id"/>
            </xsl:call-template>
            <!--<xsl:call-template name="DoBookMark"/>-->
        </tex:group>
        <tex:cmd name="par" nl2="1"/>
        <xsl:call-template name="DoNotBreakHere"/>
        <xsl:call-template name="DoSpaceAfter">
            <xsl:with-param name="layoutInfo" select="$formatTitleLayoutInfo"/>
        </xsl:call-template>
        <xsl:call-template name="DoNotBreakHere"/>
        <xsl:apply-templates select="child::node()[name()!='secTitle']"/>
    </xsl:template>
    <!--  
      DoSectionBeginsParagraph
   -->
    <xsl:template name="DoSectionBeginsParagraph">
        <xsl:param name="formatTitleLayoutInfo"/>
        <xsl:param name="numberLayoutInfo"/>
        <xsl:param name="layoutInfo"/>
        <xsl:param name="sContentsPeriod"/>
        <xsl:call-template name="DoSpaceBefore">
            <xsl:with-param name="layoutInfo" select="$formatTitleLayoutInfo"/>
        </xsl:call-template>
        <xsl:call-template name="DoSpaceBefore">
            <xsl:with-param name="layoutInfo" select="$numberLayoutInfo"/>
        </xsl:call-template>
        <xsl:choose>
            <xsl:when test="exsl:node-set($formatTitleLayoutInfo)/../@firstParagraphHasIndent='no'">
                <tex:cmd name="noindent" gr="0"/>
            </xsl:when>
            <xsl:otherwise>
                <tex:cmd name="indent" gr="0"/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="DoBookMark"/>
        <xsl:call-template name="DoInternalTargetBegin">
            <xsl:with-param name="sName" select="@id"/>
        </xsl:call-template>
        <xsl:call-template name="OutputSectionNumber">
            <xsl:with-param name="layoutInfo" select="$numberLayoutInfo"/>
            <xsl:with-param name="sContentsPeriod" select="$sContentsPeriod"/>
        </xsl:call-template>
        <xsl:call-template name="DoInternalTargetEnd"/>
        <xsl:call-template name="DoSpaceAfter">
            <xsl:with-param name="layoutInfo" select="$numberLayoutInfo"/>
        </xsl:call-template>
        <tex:group>
            <xsl:call-template name="DoTitleFormatInfo">
                <xsl:with-param name="layoutInfo" select="$formatTitleLayoutInfo"/>
            </xsl:call-template>
            <xsl:call-template name="OutputSectionTitle"/>
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="$formatTitleLayoutInfo"/>
            </xsl:call-template>
            <xsl:variable name="contentOfThisElement">
                <xsl:call-template name="OutputSectionTitle"/>
                <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                    <xsl:with-param name="layoutInfo" select="$formatTitleLayoutInfo"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:call-template name="DoTitleFormatInfoEnd">
                <xsl:with-param name="layoutInfo" select="$formatTitleLayoutInfo"/>
                <xsl:with-param name="contentOfThisElement" select="$contentOfThisElement"/>
            </xsl:call-template>
        </tex:group>
        <xsl:if test="exsl:node-set($layoutInfo)/@showInHeader!='no'">
            <!-- put title in marker so it can show up in running header -->
            <xsl:call-template name="DoSectionRunningHeader">
                <xsl:with-param name="sContentsPeriod" select="$sContentsPeriod"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="CreateAddToContents">
            <xsl:with-param name="id" select="@id"/>
        </xsl:call-template>
        <!--<xsl:call-template name="DoBookMark"/>-->
        <xsl:call-template name="DoSpaceAfter">
            <xsl:with-param name="layoutInfo" select="$formatTitleLayoutInfo"/>
        </xsl:call-template>
        <xsl:variable name="firstParagraph" select="child::node()[name()!='secTitle'][1][name()='p' or name()='pc']"/>
        <xsl:choose>
            <xsl:when test="$firstParagraph">
                <xsl:apply-templates select="child::node()[name()!='secTitle'][1][name()='p' or name()='pc']" mode="contentOnly"/>
                <tex:cmd name="par"/>
            </xsl:when>
            <xsl:when test="child::node()[name()!='secTitle'][1][name()='table']">
                <tex:cmd name="par"/>
            </xsl:when>
        </xsl:choose>
        <xsl:choose>
            <xsl:when test="child::node()[name()!='secTitle'][1][name()='p' or name()='pc']">
                <xsl:apply-templates select="child::node()[name()!='secTitle'][position()&gt;1]"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="child::node()[name()!='secTitle']"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoSectionRunningHeader
    -->
    <xsl:template name="DoSectionRunningHeader">
        <xsl:param name="sContentsPeriod"/>
        <xsl:choose>
            <xsl:when test="$bIsBook and ancestor::*[starts-with(name(),'chapter') or name()='appendix']">
                <tex:cmd name="markboth">
                    <xsl:if test="$chapterTitleOnOddPage">
                        <tex:parm>
                            <xsl:call-template name="DoSectionRunningHeaderAncestorName"/>
                        </tex:parm>
                    </xsl:if>
                    <tex:parm>
                        <xsl:call-template name="DoSecTitleRunningHeader">
                            <xsl:with-param name="number" select="$sectionNumberInHeaderLayout"/>
                            <xsl:with-param name="bNumberIsBeforeTitle" select="$bSectionNumberIsBeforeTitle"/>
                            <xsl:with-param name="sContentsPeriod" select="$sContentsPeriod"/>
                        </xsl:call-template>
                    </tex:parm>
                    <xsl:if test="not($chapterTitleOnOddPage)">
                        <tex:parm>
                            <xsl:call-template name="DoSectionRunningHeaderAncestorName"/>
                        </tex:parm>
                    </xsl:if>
                </tex:cmd>
            </xsl:when>
            <xsl:otherwise>
                <tex:cmd name="markboth">
                    <tex:parm>
                        <xsl:call-template name="DoSecTitleRunningHeader">
                            <xsl:with-param name="number" select="$sectionNumberInHeaderLayout"/>
                            <xsl:with-param name="bNumberIsBeforeTitle" select="$bSectionNumberIsBeforeTitle"/>
                            <xsl:with-param name="sContentsPeriod" select="$sContentsPeriod"/>
                        </xsl:call-template>
                    </tex:parm>
                    <tex:parm>
                        <xsl:call-template name="DoSecTitleRunningHeader">
                            <xsl:with-param name="number" select="$sectionNumberInHeaderLayout"/>
                            <xsl:with-param name="bNumberIsBeforeTitle" select="$bSectionNumberIsBeforeTitle"/>
                            <xsl:with-param name="sContentsPeriod" select="$sContentsPeriod"/>
                        </xsl:call-template>
                    </tex:parm>
                </tex:cmd>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoSectionRunningHeaderAncestorName
    -->
    <xsl:template name="DoSectionRunningHeaderAncestorName">
        <xsl:variable name="chapterAncestor" select="ancestor::*[starts-with(name(),'chapter')]"/>
        <xsl:choose>
            <xsl:when test="$chapterAncestor">
                <xsl:for-each select="ancestor::*[starts-with(name(),'chapter')]">
                    <xsl:call-template name="DoSecTitleRunningHeader">
                        <xsl:with-param name="number" select="$chapterNumberInHeaderLayout"/>
                        <xsl:with-param name="bNumberIsBeforeTitle" select="$bChapterNumberIsBeforeTitle"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <xsl:for-each select="ancestor::appendix">
                    <xsl:call-template name="DoSecTitleRunningHeader">
                        <xsl:with-param name="number" select="$chapterNumberInHeaderLayout"/>
                        <xsl:with-param name="bNumberIsBeforeTitle" select="$bChapterNumberIsBeforeTitle"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoRunningHeader
    -->
    <xsl:template name="DoRunningHeader">
        <xsl:param name="sHeader"/>
        <xsl:param name="fNewlineAfterMarkBoth" select="'Y'"/>
        <xsl:choose>
            <xsl:when test="ancestor-or-self::*[starts-with(name(),'chapter') or name()='appendix']">
                <xsl:variable name="chapterAncestor" select="ancestor-or-self::*[starts-with(name(),'chapter')]"/>
                <xsl:choose>
                    <xsl:when test="$chapterAncestor">
                        <xsl:for-each select="ancestor-or-self::*[starts-with(name(),'chapter')]">
                            <xsl:call-template name="DoRunningHeaderChapterAncestorName">
                                <xsl:with-param name="sHeader" select="$sHeader"/>
                            </xsl:call-template>
                        </xsl:for-each>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:for-each select="ancestor-or-self::appendix">
                            <xsl:call-template name="DoRunningHeaderChapterAncestorName">
                                <xsl:with-param name="sHeader" select="$sHeader"/>
                            </xsl:call-template>
                        </xsl:for-each>
                    </xsl:otherwise>
                </xsl:choose>

                <!--<xsl:for-each select="ancestor-or-self::*[starts-with(name(),'chapter') or name()='appendix']">
                    <tex:cmd name="markboth" nl2="1">
                        <xsl:if test="$chapterTitleOnOddPage">
                            <tex:parm>
                                <xsl:call-template name="DoSecTitleRunningHeader">
                                    <xsl:with-param name="number" select="$chapterNumberInHeaderLayout"/>
                                    <xsl:with-param name="bNumberIsBeforeTitle" select="$bChapterNumberIsBeforeTitle"/>
                                </xsl:call-template>
                            </tex:parm>
                        </xsl:if>
                        <tex:parm>
                            <xsl:apply-templates select="$sHeader"/>
                        </tex:parm>
                        <xsl:if test="not($chapterTitleOnOddPage)">
                            <tex:parm>
                                <xsl:call-template name="DoSecTitleRunningHeader">
                                    <xsl:with-param name="number" select="$chapterNumberInHeaderLayout"/>
                                    <xsl:with-param name="bNumberIsBeforeTitle" select="$bChapterNumberIsBeforeTitle"/>
                                </xsl:call-template>
                            </tex:parm>
                        </xsl:if>
                    </tex:cmd>
                </xsl:for-each>-->
            </xsl:when>
            <xsl:otherwise>
                <tex:cmd name="markboth">
                    <xsl:if test="$fNewlineAfterMarkBoth='Y'">
                        <xsl:attribute name="nl2">
                            <xsl:text>1</xsl:text>
                        </xsl:attribute>
                    </xsl:if>
                    <tex:parm>
                        <xsl:value-of select="$sHeader"/>
                    </tex:parm>
                    <tex:parm>
                        <xsl:value-of select="$sHeader"/>
                    </tex:parm>
                </tex:cmd>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        DoRunningHeaderChapterAncestorName
    -->
    <xsl:template name="DoRunningHeaderChapterAncestorName">
        <xsl:param name="sHeader"/>
        <tex:cmd name="markboth" nl2="1">
            <xsl:if test="$chapterTitleOnOddPage">
                <tex:parm>
                    <xsl:call-template name="DoSecTitleRunningHeader">
                        <xsl:with-param name="number" select="$chapterNumberInHeaderLayout"/>
                        <xsl:with-param name="bNumberIsBeforeTitle" select="$bChapterNumberIsBeforeTitle"/>
                    </xsl:call-template>
                </tex:parm>
            </xsl:if>
            <tex:parm>
                <xsl:apply-templates select="$sHeader"/>
            </tex:parm>
            <xsl:if test="not($chapterTitleOnOddPage)">
                <tex:parm>
                    <xsl:call-template name="DoSecTitleRunningHeader">
                        <xsl:with-param name="number" select="$chapterNumberInHeaderLayout"/>
                        <xsl:with-param name="bNumberIsBeforeTitle" select="$bChapterNumberIsBeforeTitle"/>
                    </xsl:call-template>
                </tex:parm>
            </xsl:if>
        </tex:cmd>
    </xsl:template>
    <!--
        DoSecNumberRunningHeader
    -->
    <xsl:template name="DoSecNumberRunningHeader">
        <xsl:param name="number"/>
        <xsl:param name="sContentsPeriod"/>
        <xsl:if test="$number">
            <!-- format and output number -->
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="$number"/>
                <xsl:with-param name="originalContext" select="$number"/>
            </xsl:call-template>
            <xsl:call-template name="DoFormatLayoutInfoTextBefore">
                <xsl:with-param name="layoutInfo" select="$number"/>
            </xsl:call-template>
            <xsl:choose>
                <xsl:when test="name($number)='sectionNumber'">
                    <xsl:call-template name="OutputSectionNumber">
                        <xsl:with-param name="layoutInfo" select="$number"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="OutputChapterNumber"/>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="$number"/>
            </xsl:call-template>
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="$number"/>
                <xsl:with-param name="originalContext" select="$number"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--  
        DoSecTitleRunningHeader
    -->
    <xsl:template name="DoSecTitleRunningHeader">
        <xsl:param name="number"/>
        <xsl:param name="bNumberIsBeforeTitle" select="'Y'"/>
        <xsl:param name="sContentsPeriod"/>
        <xsl:variable name="shortTitle" select="shortTitle | frontMatter/shortTitle"/>
        <xsl:if test="$bNumberIsBeforeTitle='Y'">
            <xsl:call-template name="DoSecNumberRunningHeader">
                <xsl:with-param name="number" select="$number"/>
                <xsl:with-param name="sContentsPeriod" select="$sContentsPeriod"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:choose>
            <xsl:when test="string-length($shortTitle) &gt; 0">
                <xsl:apply-templates select="$shortTitle" mode="InMarker"/>
            </xsl:when>
            <xsl:when test="string-length(frontMatter/title) &gt; 0">
                <xsl:apply-templates select="frontMatter/title" mode="InMarker"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="secTitle" mode="InMarker"/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="$bNumberIsBeforeTitle!='Y'">
            <xsl:call-template name="DoSecNumberRunningHeader">
                <xsl:with-param name="number" select="$number"/>
                <xsl:with-param name="sContentsPeriod" select="$sContentsPeriod"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--  
      DoSpaceAfter
   -->
    <xsl:template name="DoSpaceAfter">
        <xsl:param name="layoutInfo"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($layoutInfo)/@verticalfillafter!='0'">
                <xsl:call-template name="DoVerticalFill">
                    <xsl:with-param name="iLevel" select="exsl:node-set($layoutInfo)/@verticalfillafter"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="string-length(normalize-space(exsl:node-set($layoutInfo)/@spaceafter)) &gt; 0">
                    <tex:cmd name="vspace">
                        <tex:parm>
                            <xsl:value-of select="normalize-space(exsl:node-set($layoutInfo)/@spaceafter)"/>
                        </tex:parm>
                    </tex:cmd>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoSpaceBefore
    -->
    <xsl:template name="DoSpaceBefore">
        <xsl:param name="layoutInfo"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($layoutInfo)/@verticalfillbefore!='0'">
                <xsl:call-template name="DoVerticalFill">
                    <xsl:with-param name="iLevel" select="exsl:node-set($layoutInfo)/@verticalfillbefore"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="string-length(normalize-space(exsl:node-set($layoutInfo)/@spacebefore)) &gt; 0">
                    <xsl:variable name="sVSpace">
                        <xsl:text>vspace</xsl:text>
                        <xsl:if test="exsl:node-set($layoutInfo)/@pagebreakbefore='yes' or exsl:node-set($layoutInfo)/@startonoddpage='yes'">
                            <xsl:text>*</xsl:text>
                        </xsl:if>
                    </xsl:variable>
                    <tex:cmd name="{$sVSpace}">
                        <tex:parm>
                            <xsl:value-of select="normalize-space(exsl:node-set($layoutInfo)/@spacebefore)"/>
                        </tex:parm>
                    </tex:cmd>
                </xsl:if>
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
                    <!--                <xsl:value-of select="$sBasicPointSize"/>
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
            <xsl:with-param name="fDoRaisebox" select="'N'"/>
        </xsl:call-template>
        <xsl:call-template name="DoInternalTargetEnd"/>
        <xsl:call-template name="CreateAddToContents">
            <xsl:with-param name="id" select="@id"/>
        </xsl:call-template>
        <xsl:call-template name="DoType">
            <xsl:with-param name="type" select="@type"/>
        </xsl:call-template>
        <xsl:if test="exsl:node-set($contentLayoutInfo)/tablenumberedLayout/@captionLocation='before' or not(exsl:node-set($contentLayoutInfo)/tablenumberedLayout) and exsl:node-set($lingPaper)/@tablenumberedLabelAndCaptionLocation='before'">
            <xsl:call-template name="OutputTableNumberedLabelAndCaption"/>
            <tex:cmd name="vspace">
                <tex:parm>
                    <xsl:choose>
                        <xsl:when test="string-length($sSpaceBetweenTableAndCaption) &gt; 0">
                            <xsl:value-of select="$sSpaceBetweenTableAndCaption"/>
                        </xsl:when>
                        <xsl:otherwise>0pt</xsl:otherwise>
                    </xsl:choose>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <!--        <tex:cmd name="leavevmode" gr="0" nl2="1"/>-->
        <xsl:call-template name="HandleTableLineSpacing">
            <xsl:with-param name="bDoBeginGroup" select="'Y'"/>
        </xsl:call-template>
        <!--        <xsl:call-template name="HandleTableLineSpacing"/>-->
        <xsl:apply-templates select="*[name()!='shortCaption']"/>
        <xsl:if test="$sLineSpacing and $sLineSpacing!='single'">
            <tex:spec cat="eg"/>
        </xsl:if>
        <xsl:call-template name="DoTypeEnd">
            <xsl:with-param name="type" select="@type"/>
        </xsl:call-template>
        <xsl:if test="exsl:node-set($contentLayoutInfo)/tablenumberedLayout/@captionLocation='after' or not(exsl:node-set($contentLayoutInfo)/tablenumberedLayout) and exsl:node-set($lingPaper)/@tablenumberedLabelAndCaptionLocation='after'">
            <xsl:if test="not(ancestor::framedUnit) and not($sLineSpacing and $sLineSpacing!='single' and exsl:node-set($lineSpacing)/@singlespacetables!='yes')">
                <tex:cmd name="vspace*">
                    <tex:parm>
                        <xsl:choose>
                            <xsl:when test="$sLineSpacing and $sLineSpacing='double' and exsl:node-set($lineSpacing)/@singlespacetables='yes'">
                                <xsl:text>-</xsl:text>
                            </xsl:when>
                            <xsl:when test="$sLineSpacing and $sLineSpacing='spaceAndAHalf' and exsl:node-set($lineSpacing)/@singlespacetables='yes'">
                                <xsl:text>-1.25</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>-.65</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                        <tex:cmd name="baselineskip" gr="0"/>
                    </tex:parm>
                </tex:cmd>
            </xsl:if>
            <tex:cmd name="vspace">
                <tex:parm>
                    <xsl:choose>
                        <xsl:when test="string-length($sSpaceBetweenTableAndCaption) &gt; 0">
                            <xsl:value-of select="$sSpaceBetweenTableAndCaption"/>
                        </xsl:when>
                        <xsl:otherwise>0pt</xsl:otherwise>
                    </xsl:choose>
                </tex:parm>
            </tex:cmd>
            <xsl:call-template name="OutputTableNumberedLabelAndCaption"/>
            <xsl:call-template name="HandleEndnotesTextInCaptionAfterTablenumbered"/>
            <tex:cmd name="vspace">
                <tex:parm>.3em</tex:parm>
            </tex:cmd>
        </xsl:if>
    </xsl:template>
    <!--  
        DoTextAlign
    -->
    <xsl:template name="DoTextAlign">
        <xsl:param name="layoutInfo"/>
        <!-- Note: need to be sure to enclose this in a group or it will become the case from now until the next text align -->
        <xsl:choose>
            <xsl:when test="exsl:node-set($layoutInfo)/@textalign='start' or exsl:node-set($layoutInfo)/@textalign='left'">
                <tex:spec cat="bg"/>
                <xsl:if test="string-length(exsl:node-set($layoutInfo)/@text-transform) &gt; 0 or exsl:node-set($layoutInfo)/@font-variant='small-caps'">
                    <!-- \MakeUppercase and \MakeLowercase will break the \centering unless we \protect it.-->
                    <tex:cmd name="protect" gr="0"/>
                </xsl:if>
                <tex:cmd name="noindent" gr="0" nl2="1"/>
            </xsl:when>
            <xsl:when test="exsl:node-set($layoutInfo)/@textalign='end' or exsl:node-set($layoutInfo)/@textalign='right'">
                <tex:spec cat="bg"/>
                <xsl:if test="string-length(exsl:node-set($layoutInfo)/@text-transform) &gt; 0 or exsl:node-set($layoutInfo)/@font-variant='small-caps'">
                    <!-- \MakeUppercase and \MakeLowercase will break the \raggedleft unless we \protect it.-->
                    <tex:cmd name="protect" gr="0"/>
                </xsl:if>
                <tex:cmd name="raggedleft" gr="0" nl2="1"/>
            </xsl:when>
            <xsl:when test="exsl:node-set($layoutInfo)/@textalign='center'">
                <!-- adjust for center environment -->
                <!--                <tex:cmd name="vspace*">
                    <tex:parm>
                        <xsl:text>-2</xsl:text>
                        <tex:cmd name="topsep" gr="0"/>
                    </tex:parm>
                </tex:cmd>
-->
                <!--                <tex:spec cat="esc"/>
                <xsl:text>begin</xsl:text>
                <tex:spec cat="bg"/>
                <xsl:text>center</xsl:text>
                <tex:spec cat="eg"/>
-->
                <tex:spec cat="bg"/>
                <xsl:if test="string-length(exsl:node-set($layoutInfo)/@text-transform) &gt; 0 or exsl:node-set($layoutInfo)/@font-variant='small-caps'">
                    <!-- \MakeUppercase and \MakeLowercase will break the \centering unless we \protect it.-->
                    <tex:cmd name="protect" gr="0"/>
                </xsl:if>
                <tex:cmd name="centering" gr="0" nl2="1"/>
                <!--                <tex:cmd name="centerline" gr="0" nl2="1"/>
                <tex:spec cat="bg"/>
-->
            </xsl:when>
            <xsl:otherwise/>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoTextAlignEnd
    -->
    <xsl:template name="DoTextAlignEnd">
        <xsl:param name="layoutInfo"/>
        <xsl:param name="contentForThisElement"/>
        <!-- Note: need to be sure to enclose this in a group or it will become the case from now until the next text align -->
        <xsl:choose>
            <xsl:when test="exsl:node-set($layoutInfo)/@textalign='center' or exsl:node-set($layoutInfo)/@textalign='right' or exsl:node-set($layoutInfo)/@textalign='end'">
                <!-- must have \\ at end or it will not actually center -->
                <xsl:if test="string-length($contentForThisElement) &gt; 0">
                    <xsl:if test="child::*[position()=last()][name()='br'][not(following-sibling::text())]">
                        <!-- cannot have two \\ in a row, so need to insert something; we'll use a non-breaking space -->
                        <xsl:text>&#xa0;</xsl:text>
                    </xsl:if>
                    <xsl:choose>
                        <xsl:when test="ancestor-or-self::abstract and exsl:node-set($frontMatterLayoutInfo)/acknowledgementsLayout/@showAsFootnoteAtEndOfAbstract='yes' and exsl:node-set($contentForThisElement)/tex:cmd[@name='renewcommand'] and exsl:node-set($contentForThisElement)/tex:cmd[@name='footnote']">
                            <!-- do nothing because the \\ will block XeLaTeX in this unusual case -->
                        </xsl:when>
                        <xsl:otherwise>
                            <!-- may need to protect the following with MakeUppercase, etc. so we just always do it-->
                            <tex:cmd name="protect" gr="0"/>
                            <tex:spec cat="esc"/>
                            <tex:spec cat="esc"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:if>
            </xsl:when>
            <xsl:otherwise/>
        </xsl:choose>
        <tex:spec cat="eg"/>
    </xsl:template>
    <!--  
        DoTextDecoration
    -->
    <xsl:template name="DoTextDecoration">
        <xsl:param name="sDecoration"/>
        <xsl:choose>
            <xsl:when test="$sDecoration='underline'">
                <tex:spec cat="esc"/>
                <xsl:text>uline</xsl:text>
                <tex:spec cat="bg"/>
            </xsl:when>
            <xsl:when test="$sDecoration='line-through'">
                <tex:spec cat="esc"/>
                <xsl:text>sout</xsl:text>
                <tex:spec cat="bg"/>
            </xsl:when>
            <xsl:otherwise>
                <!-- not using overline and blink; but see umoline package if we need overline-->
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoTextDecorationEnd
    -->
    <xsl:template name="DoTextDecorationEnd">
        <xsl:param name="sDecoration"/>
        <xsl:choose>
            <xsl:when test="$sDecoration='underline'">
                <tex:spec cat="eg"/>
            </xsl:when>
            <xsl:when test="$sDecoration='line-through'">
                <tex:spec cat="eg"/>
            </xsl:when>
            <xsl:otherwise>
                <!-- not using overline and blink; but see umoline package if we need overline-->
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoTitleFormatInfo
    -->
    <xsl:template name="DoTitleFormatInfo">
        <xsl:param name="layoutInfo"/>
        <xsl:param name="originalContext"/>
        <xsl:param name="fDoPageBreakFormatInfo" select="'Y'"/>
        <xsl:param name="fSpaceBeforeAlreadyDone" select="'N'"/>
        <xsl:param name="sId" select="''"/>
        <xsl:if test="$fDoPageBreakFormatInfo='Y'">
            <xsl:call-template name="DoPageBreakFormatInfo">
                <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="DoFrontMatterFormatInfoBegin">
            <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
            <xsl:with-param name="originalContext" select="$originalContext"/>
            <xsl:with-param name="fSpaceBeforeAlreadyDone" select="$fSpaceBeforeAlreadyDone"/>
            <xsl:with-param name="sId" select="$sId"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        DoTitleFormatInfoEnd
    -->
    <xsl:template name="DoTitleFormatInfoEnd">
        <xsl:param name="layoutInfo"/>
        <xsl:param name="originalContext"/>
        <xsl:param name="contentOfThisElement"/>
        <xsl:call-template name="DoFrontMatterFormatInfoEnd">
            <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
            <xsl:with-param name="originalContext" select="$originalContext"/>
            <xsl:with-param name="contentOfThisElement" select="$contentOfThisElement"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        DoTitleNeedsSpace
    -->
    <xsl:template name="DoTitleNeedsSpace">
        <tex:cmd name="XLingPaperneedspace" nl2="1">
            <tex:parm>
                <xsl:text>3</xsl:text>
                <tex:cmd name="baselineskip" gr="0"/>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        DoVerticalFill
    -->
    <xsl:template name="DoVerticalFill">
        <xsl:param name="iLevel"/>
        <xsl:choose>
            <xsl:when test="$iLevel='1'">
                <tex:cmd name="vfil" gr="0" nl2="1"/>
            </xsl:when>
            <xsl:when test="$iLevel='2'">
                <tex:cmd name="vfill" gr="0" nl2="1"/>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetBestLayout
    -->
    <xsl:template name="GetBestLayout">
        <xsl:param name="iPos"/>
        <xsl:param name="iLayouts"/>
        <xsl:choose>
            <xsl:when test="$iPos &gt; $iLayouts">
                <xsl:value-of select="$iLayouts"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$iPos"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetStylesheetFontFamily
    -->
    <xsl:template name="GetStylesheetFontFamily">
        <xsl:param name="layoutInfo"/>
        <xsl:variable name="sFontFamily" select="exsl:node-set($layoutInfo)/@font-family"/>
        <xsl:choose>
            <xsl:when test="string-length($sFontFamily) &gt; 0">
                <xsl:value-of select="$sFontFamily"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sDefaultFontFamily"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetFirstLevelContentsIdent
    -->
    <xsl:template name="GetFirstLevelContentsIdent">
        <tex:cmd name="leveloneindent" gr="0" nl2="0"/>
    </xsl:template>
    <!--  
        GetFontFamilyName
    -->
    <xsl:template name="GetFontFamilyName">
        <!-- set the font family name to 
            'XLingPaper' plus 
            the font name (being careful to convert any digits to letters and changing any spaces to Z so TeX won't complain) plus
            'FontFamily'.
            This should guarantee a unique name. -->
        <xsl:value-of select="concat(concat('XLingPaper',translate(.,$sDigits,$sLetters)),'FontFamily')"/>
    </xsl:template>
    <!--
        GetFootnoteMarkWhenUsingEndnotes
    -->
    <xsl:template name="GetFootnoteMarkWhenUsingEndnotes">
        <xsl:param name="originalContext"/>
        <xsl:param name="iTablenumberedAdjust"/>
        <xsl:choose>
            <xsl:when test="ancestor::title and exsl:node-set($frontMatterLayoutInfo)/titleLayout/@useFootnoteSymbols='yes' or ancestor::author">
                <tex:cmd name="renewcommand">
                    <tex:parm>
                        <tex:spec cat="esc"/>
                        <xsl:text>thefootnote</xsl:text>
                    </tex:parm>
                    <tex:parm>
                        <tex:cmd name="fnsymbol">
                            <tex:parm>footnote</tex:parm>
                        </tex:cmd>
                    </tex:parm>
                </tex:cmd>
                <tex:cmd name="footnotemark">
                    <tex:opt>
                        <xsl:call-template name="GetFootnoteNumber">
                            <xsl:with-param name="iAdjust" select="1"/>
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                            <xsl:with-param name="iTablenumberedAdjust" select="$iTablenumberedAdjust"/>
                        </xsl:call-template>
                    </tex:opt>
                </tex:cmd>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="GetFootnoteNumber">
                    <xsl:with-param name="iAdjust" select="1"/>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                    <xsl:with-param name="iTablenumberedAdjust" select="$iTablenumberedAdjust"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetPageNumberingFormat
    -->
    <xsl:template name="GetPageNumberingFormat">
        <xsl:param name="sPageFormat"/>
        <xsl:param name="sDefault" select="'roman'"/>
        <xsl:choose>
            <xsl:when test="contains($sPageFormat,'1')">
                <xsl:text>arabic</xsl:text>
            </xsl:when>
            <xsl:when test="$sPageFormat='i'">
                <xsl:text>roman</xsl:text>
            </xsl:when>
            <xsl:when test="$sPageFormat='I'">
                <xsl:text>Roman</xsl:text>
            </xsl:when>
            <xsl:when test="$sPageFormat='a'">
                <xsl:text>alph</xsl:text>
            </xsl:when>
            <xsl:when test="$sPageFormat='A'">
                <xsl:text>Alph</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sDefault"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        HandleFreeTextAfterAndFontOverrides
    -->
    <xsl:template name="HandleFreeTextAfterAndFontOverrides">
        <xsl:param name="freeLayout"/>
        <xsl:if test="$freeLayout">
            <xsl:call-template name="HandleFreeTextAfterInside">
                <xsl:with-param name="freeLayout" select="$freeLayout"/>
            </xsl:call-template>
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="$freeLayout"/>
                <xsl:with-param name="originalContext" select="."/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleFreeLanguageFontInfo
    -->
    <xsl:template name="HandleFreeLanguageFontInfo">
        <xsl:param name="freeLayout" select="exsl:node-set($contentLayoutInfo)/freeLayout"/>
        <xsl:param name="originalContext"/>
        <xsl:variable name="language" select="key('LanguageID',@lang)"/>
        <xsl:variable name="sFontFamily" select="normalize-space(exsl:node-set($language)/@font-family)"/>
        <xsl:choose>
            <xsl:when test="string-length($sFontFamily) &gt; 0">
                <xsl:call-template name="HandleFreeTextBeforeOutside">
                    <xsl:with-param name="freeLayout" select="$freeLayout"/>
                </xsl:call-template>
                <xsl:call-template name="HandleFontFamily">
                    <xsl:with-param name="sFontFamily" select="$sFontFamily"/>
                </xsl:call-template>
                <xsl:call-template name="OutputFontAttributes">
                    <xsl:with-param name="language" select="$language"/>
                </xsl:call-template>
                <xsl:call-template name="HandleFreeTextBeforeAndFontOverrides">
                    <xsl:with-param name="freeLayout" select="$freeLayout"/>
                </xsl:call-template>
                <xsl:call-template name="HandleLanguageContent">
                    <xsl:with-param name="language" select="$language"/>
                    <xsl:with-param name="bReversing" select="'N'"/>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
                <xsl:call-template name="HandleFreeTextAfterAndFontOverrides">
                    <xsl:with-param name="freeLayout" select="$freeLayout"/>
                </xsl:call-template>
                <xsl:call-template name="OutputFontAttributesEnd">
                    <xsl:with-param name="language" select="$language"/>
                </xsl:call-template>
                <xsl:call-template name="HandleFreeTextAfterOutside">
                    <xsl:with-param name="freeLayout" select="$freeLayout"/>
                </xsl:call-template>
                <tex:spec cat="eg"/>
            </xsl:when>
            <xsl:otherwise>
                <!--                <tex:group>-->
                <xsl:call-template name="HandleFreeTextBeforeOutside">
                    <xsl:with-param name="freeLayout" select="$freeLayout"/>
                </xsl:call-template>
                <xsl:call-template name="OutputFontAttributes">
                    <xsl:with-param name="language" select="$language"/>
                </xsl:call-template>
                <xsl:call-template name="HandleFreeTextBeforeAndFontOverrides">
                    <xsl:with-param name="freeLayout" select="$freeLayout"/>
                </xsl:call-template>
                <xsl:call-template name="HandleLanguageContent">
                    <xsl:with-param name="language" select="$language"/>
                    <xsl:with-param name="bReversing" select="'N'"/>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:call-template>
                <xsl:call-template name="HandleFreeTextAfterAndFontOverrides">
                    <xsl:with-param name="freeLayout" select="$freeLayout"/>
                </xsl:call-template>
                <xsl:call-template name="OutputFontAttributesEnd">
                    <xsl:with-param name="language" select="$language"/>
                </xsl:call-template>
                <xsl:call-template name="HandleFreeTextAfterOutside">
                    <xsl:with-param name="freeLayout" select="$freeLayout"/>
                </xsl:call-template>
                <!--                </tex:group>-->
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        HandleFreeNoLanguageFontInfo
    -->
    <xsl:template name="HandleFreeNoLanguageFontInfo">
        <xsl:param name="originalContext"/>
        <xsl:param name="freeLayout" select="exsl:node-set($contentLayoutInfo)/freeLayout"/>
        <!--        <tex:group>-->
        <xsl:call-template name="HandleFreeTextBeforeOutside">
            <xsl:with-param name="freeLayout" select="$freeLayout"/>
        </xsl:call-template>
        <xsl:call-template name="HandleFreeTextBeforeAndFontOverrides">
            <xsl:with-param name="freeLayout" select="$freeLayout"/>
        </xsl:call-template>
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
        <xsl:call-template name="HandleFreeTextAfterAndFontOverrides">
            <xsl:with-param name="freeLayout" select="$freeLayout"/>
        </xsl:call-template>
        <xsl:call-template name="HandleFreeTextAfterOutside">
            <xsl:with-param name="freeLayout" select="$freeLayout"/>
        </xsl:call-template>
        <!--        </tex:group>-->
    </xsl:template>
    <!--  
        HandleFontFamily
    -->
    <xsl:template name="HandleFontFamily">
        <xsl:param name="language"/>
        <xsl:param name="sFontFamily"/>
        <xsl:param name="bIsOverride" select="'N'"/>
        <xsl:choose>
            <xsl:when test="$bIsOverride='Y' and $language and contains(exsl:node-set($language)/@XeLaTeXSpecial,$sGraphite) or $bIsOverride='Y' and $language and contains(exsl:node-set($language)/@XeLaTeXSpecial,$sFontFeature)">
                <tex:spec cat="esc"/>
                <xsl:text>fontspec</xsl:text>
                <tex:opt>
                    <xsl:call-template name="HandleXeLaTeXSpecialGraphiteOrFontFeature">
                        <xsl:with-param name="language" select="$language"/>
                    </xsl:call-template>
                </tex:opt>
                <tex:parm>
                    <xsl:value-of select="$sFontFamily"/>
                </tex:parm>
            </xsl:when>
            <xsl:otherwise>
                <tex:spec cat="esc"/>
                <xsl:text>XLingPaper</xsl:text>
                <xsl:value-of select="translate($sFontFamily,$sDigits, $sLetters)"/>
                <xsl:text>FontFamily</xsl:text>
                <xsl:if test="$language and contains(exsl:node-set($language)/@XeLaTeXSpecial,'graphite')">
                    <xsl:value-of select="$sGraphiteForFontName"/>
                    <xsl:call-template name="HandleXeLaTeXSpecialFontFeatureForFontName">
                        <xsl:with-param name="sList" select="exsl:node-set($language)/@XeLaTeXSpecial"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
        <tex:spec cat="bg"/>
    </xsl:template>
    <!--
        HandleLiteralLabelLayoutInfo
    -->
    <xsl:template name="HandleLiteralLabelLayoutInfo">
        <xsl:param name="layoutInfo"/>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="$layoutInfo"/>
        </xsl:call-template>
        <xsl:value-of select="exsl:node-set($layoutInfo)/../literalLabelLayout"/>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="$layoutInfo"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        HandleGlossFontOverridesEnd
    -->
    <xsl:template name="HandleGlossFontOverridesEnd">
        <xsl:param name="sGlossContext"/>
        <xsl:param name="glossLayout"/>
        <xsl:choose>
            <xsl:when test="$sGlossContext='listWord'">
                <xsl:call-template name="OutputFontAttributesEnd">
                    <xsl:with-param name="language" select="exsl:node-set($glossLayout)/glossInListWordLayout"/>
                    <xsl:with-param name="originalContext" select="."/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$sGlossContext='example'">
                <xsl:call-template name="OutputFontAttributesEnd">
                    <xsl:with-param name="language" select="exsl:node-set($glossLayout)/glossInExampleLayout"/>
                    <xsl:with-param name="originalContext" select="."/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$sGlossContext='table'">
                <xsl:call-template name="OutputFontAttributesEnd">
                    <xsl:with-param name="language" select="exsl:node-set($glossLayout)/glossInTableLayout"/>
                    <xsl:with-param name="originalContext" select="."/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$sGlossContext='prose'">
                <xsl:call-template name="OutputFontAttributesEnd">
                    <xsl:with-param name="language" select="exsl:node-set($glossLayout)/glossInProseLayout"/>
                    <xsl:with-param name="originalContext" select="."/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  
        HandleGlossTextAfterAndFontOverrides
    -->
    <xsl:template name="HandleGlossTextAfterAndFontOverrides">
        <xsl:param name="glossLayout"/>
        <xsl:param name="sGlossContext"/>
        <xsl:if test="$glossLayout">
            <xsl:call-template name="HandleGlossTextAfterInside">
                <xsl:with-param name="glossLayout" select="$glossLayout"/>
                <xsl:with-param name="sGlossContext" select="$sGlossContext"/>
            </xsl:call-template>
            <xsl:call-template name="HandleGlossFontOverridesEnd">
                <xsl:with-param name="sGlossContext" select="$sGlossContext"/>
                <xsl:with-param name="glossLayout" select="$glossLayout"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleLangDataFontOverridesEnd
    -->
    <xsl:template name="HandleLangDataFontOverridesEnd">
        <xsl:param name="sLangDataContext"/>
        <xsl:param name="langDataLayout"/>
        <xsl:choose>
            <xsl:when test="$sLangDataContext='example'">
                <xsl:call-template name="OutputFontAttributesEnd">
                    <xsl:with-param name="language" select="exsl:node-set($langDataLayout)/langDataInExampleLayout"/>
                    <xsl:with-param name="originalContext" select="."/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$sLangDataContext='table'">
                <xsl:call-template name="OutputFontAttributesEnd">
                    <xsl:with-param name="language" select="exsl:node-set($langDataLayout)/langDataInTableLayout"/>
                    <xsl:with-param name="originalContext" select="."/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$sLangDataContext='prose'">
                <xsl:call-template name="OutputFontAttributesEnd">
                    <xsl:with-param name="language" select="exsl:node-set($langDataLayout)/langDataInProseLayout"/>
                    <xsl:with-param name="originalContext" select="."/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  
        HandleLangDataTextAfterAndFontOverrides
    -->
    <xsl:template name="HandleLangDataTextAfterAndFontOverrides">
        <xsl:param name="langDataLayout"/>
        <xsl:param name="sLangDataContext"/>
        <xsl:if test="$langDataLayout">
            <xsl:call-template name="HandleLangDataTextAfterInside">
                <xsl:with-param name="langDataLayout" select="$langDataLayout"/>
                <xsl:with-param name="sLangDataContext" select="$sLangDataContext"/>
            </xsl:call-template>
            <xsl:call-template name="HandleLangDataFontOverridesEnd">
                <xsl:with-param name="sLangDataContext" select="$sLangDataContext"/>
                <xsl:with-param name="langDataLayout" select="$langDataLayout"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleSectionNumberOutput
    -->
    <xsl:template name="HandleSectionNumberOutput">
        <xsl:param name="layoutInfo"/>
        <xsl:param name="bAppendix"/>
        <xsl:param name="sContentsPeriod"/>
        <tex:group>
            <xsl:if test="$layoutInfo">
                <xsl:if test="name($layoutInfo)!='sectionNumber'">
                    <!-- no need for this when it is a running header's section number -->
                    <xsl:call-template name="DoTitleFormatInfo">
                        <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:if>
            <xsl:choose>
                <xsl:when test="$bAppendix='Y'">
                    <xsl:apply-templates select="." mode="numberAppendix"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates select="." mode="number"/>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:if test="count($chapters)!=0 or count(//section1)&gt;1 or count(//section1/section2)&gt;0">
                <xsl:value-of select="$sContentsPeriod"/>
            </xsl:if>
            <xsl:choose>
                <xsl:when test="$layoutInfo and name($layoutInfo)='sectionNumber'">
                    <!-- special case for running header -->
                    <xsl:if test="string-length(exsl:node-set($layoutInfo)/@textafter)=0 or exsl:node-set($layoutInfo)/@textafter=' '">
                        <xsl:text>&#xa0;</xsl:text>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="$layoutInfo">
                    <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                        <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                    </xsl:call-template>
                    <xsl:variable name="contentForThisElement">
                        <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                            <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:call-template name="DoTitleFormatInfoEnd">
                        <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                        <xsl:with-param name="contentOfThisElement" select="$contentForThisElement"/>
                    </xsl:call-template>
                    <xsl:choose>
                        <xsl:when test="exsl:node-set($layoutInfo)/../@beginsparagraph!='yes' and string-length(exsl:node-set($layoutInfo)/@spaceafter) &gt; 0">
                            <tex:cmd name="par" nl2="1"/>
                        </xsl:when>
                        <xsl:when test="exsl:node-set($layoutInfo)/../@beginsparagraph='yes'">
                            <!-- do nothing; all handled by other information -->
                        </xsl:when>
                        <xsl:otherwise>
                            <!-- insert a non-breaking space -->
                            <xsl:text>&#xa0;</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                    <xsl:call-template name="DoSpaceAfter">
                        <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:when test="count($chapters)=0 and count(//section1)=1 and count(//section1/section2)=0">
                    <!-- do nothing: there is no number -->
                </xsl:when>
                <xsl:otherwise>
                    <!-- make sure there's a (non-breaking) space between the number and the title -->
                    <xsl:text>&#xa0;</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </tex:group>
    </xsl:template>
    <!--  
      HandleSmallCaps
   -->
    <xsl:template name="HandleSmallCaps">
        <xsl:choose>
            <xsl:when test="$sFOProcessor = 'XEP'">
                <!-- HACK for RenderX XEP: it does not (yet) support small-caps -->
                <!-- Use font-size:smaller and do a text-transform to uppercase -->
                <xsl:attribute name="font-size">
                    <xsl:text>smaller</xsl:text>
                </xsl:attribute>
                <xsl:attribute name="text-transform">
                    <xsl:text>uppercase</xsl:text>
                </xsl:attribute>
            </xsl:when>
            <xsl:otherwise>
                <xsl:attribute name="font-variant">
                    <xsl:text>small-caps</xsl:text>
                </xsl:attribute>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        HandleTableLineSpacing
    -->
    <xsl:template name="HandleTableLineSpacing">
        <xsl:param name="bDoBeginGroup" select="'N'"/>
        <xsl:if test="$sLineSpacing and $sLineSpacing!='single'">
            <xsl:if test="$bDoBeginGroup='Y'">
                <tex:spec cat="bg"/>
            </xsl:if>
            <xsl:choose>
                <xsl:when test="exsl:node-set($lineSpacing)/@singlespacetables='yes'">
                    <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
                </xsl:when>
                <xsl:when test="$sLineSpacing='double'">
                    <tex:cmd name="doublespacing" gr="0" nl2="1"/>
                </xsl:when>
                <xsl:when test="$sLineSpacing='spaceAndAHalf'">
                    <tex:cmd name="onehalfspacing" gr="0" nl2="1"/>
                </xsl:when>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--
        ItalicizeString
    -->
    <xsl:template name="ItalicizeString">
        <xsl:param name="contents"/>
        <xsl:if test="string-length($contents) &gt; 0">
            <tex:spec cat="bg"/>
            <tex:spec cat="esc"/>
            <xsl:text>textit</xsl:text>
            <tex:spec cat="bg"/>
            <xsl:value-of select="$contents"/>
            <tex:spec cat="eg"/>
            <tex:spec cat="eg"/>
        </xsl:if>
    </xsl:template>
    <!--
        LinkAttributesBegin
    -->
    <xsl:template name="LinkAttributesBegin">
        <xsl:param name="override"/>
        <xsl:if test="exsl:node-set($override)/@showmarking='yes'">
            <xsl:variable name="sOverrideColor" select="exsl:node-set($override)/@color"/>
            <xsl:variable name="sOverrideDecoration" select="exsl:node-set($override)/@decoration"/>
            <xsl:choose>
                <xsl:when test="$sOverrideColor != 'default'">
                    <xsl:call-template name="DoColor">
                        <xsl:with-param name="sFontColor" select="$sOverrideColor"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:if test="string-length($sLinkColor) &gt; 0">
                        <xsl:call-template name="DoColor">
                            <xsl:with-param name="sFontColor" select="$sLinkColor"/>
                        </xsl:call-template>
                    </xsl:if>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="$sOverrideDecoration != 'default'">
                    <xsl:call-template name="DoTextDecoration">
                        <xsl:with-param name="sDecoration" select="$sOverrideDecoration"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:if test="$sLinkTextDecoration != 'none'">
                        <xsl:call-template name="DoTextDecoration">
                            <xsl:with-param name="sDecoration" select="$sLinkTextDecoration"/>
                        </xsl:call-template>
                    </xsl:if>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--
        LinkAttributesEnd
    -->
    <xsl:template name="LinkAttributesEnd">
        <xsl:param name="override"/>
        <xsl:if test="exsl:node-set($override)/@showmarking='yes'">
            <xsl:variable name="sOverrideColor" select="exsl:node-set($override)/@color"/>
            <xsl:variable name="sOverrideDecoration" select="exsl:node-set($override)/@decoration"/>
            <xsl:choose>
                <xsl:when test="$sOverrideColor != 'default'">
                    <tex:spec cat="eg"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:if test="string-length($sLinkColor) &gt; 0">
                        <tex:spec cat="eg"/>
                    </xsl:if>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="$sOverrideDecoration != 'default'">
                    <xsl:call-template name="DoTextDecorationEnd">
                        <xsl:with-param name="sDecoration" select="$sOverrideDecoration"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:if test="$sLinkTextDecoration != 'none'">
                        <tex:spec cat="eg"/>
                    </xsl:if>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--
        OutputAppendixInChapterInCollectionTOC
    -->
    <xsl:template name="OutputAppendixInChapterInCollectionTOC">
        <xsl:param name="frontMatterLayout"/>
        <!-- figure out what the new value of the indent based on the section number itself -->
        <xsl:variable name="sSectionNumberIndentFormula">
            <xsl:call-template name="CalculateSectionNumberIndent">
                <xsl:with-param name="contentsLayout" select="exsl:node-set($frontMatterLayout)/contentsLayout"/>
            </xsl:call-template>
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
                <xsl:if test="exsl:node-set($frontMatterLayout)/contentsLayout/@useappendixlabelbeforeappendixletter='yes'">
                    <xsl:choose>
                        <xsl:when test="string-length(@label) &gt; 0">
                            <xsl:value-of select="@label"/>
                        </xsl:when>
                        <xsl:otherwise>Appendix</xsl:otherwise>
                    </xsl:choose>
                    <xsl:text>&#x20;</xsl:text>
                </xsl:if>
                <xsl:call-template name="OutputChapterNumber">
                    <xsl:with-param name="fDoTextAfterLetter" select="'N'"/>
                </xsl:call-template>
                <xsl:apply-templates select="secTitle" mode="contents"/>
            </xsl:with-param>
            <xsl:with-param name="sSpaceBefore">
                <xsl:call-template name="DoSpaceBeforeContentsLine"/>
            </xsl:with-param>
            <xsl:with-param name="sIndent">
                <tex:cmd name="leveloneindent" gr="0" nl2="0"/>
            </xsl:with-param>
            <xsl:with-param name="sNumWidth">
                <tex:cmd name="levelonewidth" gr="0" nl2="0"/>
            </xsl:with-param>
        </xsl:call-template>
        <xsl:apply-templates select="section1 | section2" mode="contents">
            <xsl:with-param name="contentsLayoutToUse" select="exsl:node-set($frontMatterLayout)/contentsLayout"/>
        </xsl:apply-templates>
    </xsl:template>
    <!--
                   OutputBackMatterItemTitle
-->
    <xsl:template name="OutputBackMatterItemTitle">
        <xsl:param name="sId"/>
        <xsl:param name="sLabel"/>
        <xsl:param name="layoutInfo"/>
        <xsl:param name="sRunningHeader"/>
        <xsl:choose>
            <xsl:when test="$bIsBook">
                <tex:group>
                    <xsl:call-template name="DoPageBreakFormatInfo">
                        <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                    </xsl:call-template>
                    <xsl:if test="not(ancestor::chapterInCollection)">
                        <tex:cmd name="thispagestyle">
                            <tex:parm>
                                <xsl:choose>
                                    <xsl:when test="exsl:node-set($backMatterLayoutInfo)/headerFooterPageStyles">backmatterfirstpage</xsl:when>
                                    <xsl:when test="exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles/headerFooterFirstPage">bodyfirstpage</xsl:when>
                                    <xsl:otherwise>body</xsl:otherwise>
                                </xsl:choose>
                            </tex:parm>
                        </tex:cmd>
                    </xsl:if>
                    <xsl:call-template name="DoSpaceBefore">
                        <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                    </xsl:call-template>
                    <xsl:call-template name="DoTitleFormatInfo">
                        <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                        <xsl:with-param name="originalContext" select="$sLabel"/>
                        <xsl:with-param name="fDoPageBreakFormatInfo" select="'N'"/>
                        <xsl:with-param name="fSpaceBeforeAlreadyDone" select="'Y'"/>
                        <xsl:with-param name="sId" select="$sId"/>
                    </xsl:call-template>
                    <xsl:call-template name="OutputChapTitle">
                        <xsl:with-param name="sTitle" select="$sLabel"/>
                    </xsl:call-template>
                    <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                        <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                    </xsl:call-template>
                    <xsl:variable name="contentForThisElement">
                        <xsl:call-template name="OutputChapTitle">
                            <xsl:with-param name="sTitle" select="$sLabel"/>
                        </xsl:call-template>
                        <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                            <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:call-template name="DoTitleFormatInfoEnd">
                        <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                        <xsl:with-param name="originalContext" select="$sLabel"/>
                        <xsl:with-param name="contentOfThisElement" select="$contentForThisElement"/>
                    </xsl:call-template>
                    <xsl:call-template name="CreateAddToContents">
                        <xsl:with-param name="id" select="$sId"/>
                    </xsl:call-template>
                    <xsl:call-template name="DoRunningHeader">
                        <xsl:with-param name="sHeader" select="$sRunningHeader"/>
                    </xsl:call-template>
                </tex:group>
                <tex:cmd name="par" nl2="1"/>
                <xsl:call-template name="DoSpaceAfter">
                    <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <tex:group>
                    <!--                    <xsl:call-template name="DoTitleNeedsSpace"/> Now do this in DoTitleFormatInfo-->
                    <xsl:if test="exsl:node-set($layoutInfo)/@text-transform='uppercase' or exsl:node-set($layoutInfo)/@text-transform='lowercase'">
                        <xsl:call-template name="DoBookMark"/>
                        <xsl:call-template name="DoInternalTargetBegin">
                            <xsl:with-param name="sName" select="$sId"/>
                        </xsl:call-template>
                    </xsl:if>
                    <xsl:call-template name="DoType"/>
                    <xsl:call-template name="DoTitleFormatInfo">
                        <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                        <xsl:with-param name="originalContext" select="$sLabel"/>
                    </xsl:call-template>
                    <xsl:if test="not(exsl:node-set($layoutInfo)/@text-transform) or exsl:node-set($layoutInfo)/@text-transform!='uppercase' and exsl:node-set($layoutInfo)/@text-transform!='lowercase'">
                        <xsl:call-template name="DoBookMark"/>
                        <xsl:call-template name="DoInternalTargetBegin">
                            <xsl:with-param name="sName" select="$sId"/>
                        </xsl:call-template>
                    </xsl:if>
                    <xsl:value-of select="$sLabel"/>
                    <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                        <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                    </xsl:call-template>
                    <xsl:variable name="contentForThisElement">
                        <xsl:value-of select="$sLabel"/>
                        <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                            <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:call-template name="DoTitleFormatInfoEnd">
                        <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                        <xsl:with-param name="originalContext" select="$sLabel"/>
                        <xsl:with-param name="contentOfThisElement" select="$contentForThisElement"/>
                    </xsl:call-template>
                    <xsl:call-template name="DoTypeEnd"/>
                    <xsl:call-template name="DoInternalTargetEnd"/>
                    <xsl:call-template name="DoRunningHeader">
                        <xsl:with-param name="sHeader" select="$sRunningHeader"/>
                    </xsl:call-template>
                    <xsl:call-template name="CreateAddToContents">
                        <xsl:with-param name="id" select="$sId"/>
                    </xsl:call-template>
                </tex:group>
                <tex:cmd name="par" nl2="1"/>
                <xsl:call-template name="DoSpaceAfter">
                    <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
                  OutputChapterNumber
-->
    <xsl:template name="OutputChapterNumber">
        <xsl:param name="fDoTextAfterLetter" select="'Y'"/>
        <xsl:param name="fDoingContents" select="'N'"/>
        <xsl:param name="contentsLayoutToUse" select="exsl:node-set($contentsLayout)/contentsLayout"/>
        <xsl:choose>
            <xsl:when test="name()='chapter'">
                <xsl:apply-templates select="." mode="numberChapter"/>
                <xsl:if test="$fDoingContents='N' and not(exsl:node-set($bodyLayoutInfo)/chapterLayout/numberLayout) and string-length(exsl:node-set($bodyLayoutInfo)/chapterLayout/chapterTitleLayout/@textafternumber) &gt; 0">
                    <xsl:value-of select="exsl:node-set($bodyLayoutInfo)/chapterLayout/chapterTitleLayout/@textafternumber"/>
                </xsl:if>
            </xsl:when>
            <xsl:when test="name()='chapterInCollection'">
                <xsl:apply-templates select="." mode="numberChapter"/>
                <xsl:if
                    test="$fDoingContents='N' and not(exsl:node-set($bodyLayoutInfo)/chapterInCollectionLayout/numberLayout) and string-length(exsl:node-set($bodyLayoutInfo)/chapterInCollectionLayout/chapterTitleLayout/@textafternumber) &gt; 0">
                    <xsl:value-of select="exsl:node-set($bodyLayoutInfo)/chapterInCollectionLayout/chapterTitleLayout/@textafternumber"/>
                </xsl:if>
            </xsl:when>
            <xsl:when test="name()='chapterBeforePart'">
                <xsl:text>0</xsl:text>
            </xsl:when>
            <xsl:when test="name()='part'">
                <xsl:apply-templates select="." mode="numberPart"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="appLayout">
                    <xsl:choose>
                        <xsl:when test="ancestor::chapterInCollection">
                            <xsl:copy-of select="exsl:node-set($bodyLayoutInfo)/chapterInCollectionBackMatterLayout/appendixLayout/appendixTitleLayout"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:copy-of select="exsl:node-set($backMatterLayoutInfo)/appendixLayout/appendixTitleLayout"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:if test="exsl:node-set($appLayout)/appendixTitleLayout/@showletter!='no'">
                    <xsl:apply-templates select="." mode="numberAppendix"/>
                    <xsl:choose>
                        <xsl:when test="$fDoTextAfterLetter='Y'">
                            <xsl:value-of select="exsl:node-set($appLayout)/appendixTitleLayout/@textafterletter"/>
                        </xsl:when>
                        <xsl:when test="saxon:node-set($contentsLayoutToUse)/@useperiodafterappendixletter='yes'">
                            <xsl:text>.&#xa0; </xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>&#xa0; </xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
                  OutputChapTitle
-->
    <xsl:template name="OutputChapTitle">
        <xsl:param name="sTitle"/>
        <!--        <xsl:attribute name="span">all</xsl:attribute>-->
        <!--      <fo:block span="all">-->
        <xsl:value-of select="$sTitle"/>
        <!--      </fo:block>-->
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
        OutputFigureLabel
    -->
    <xsl:template name="OutputFigureLabel">
        <xsl:variable name="styleSheetLabelLayout" select="$styleSheetFigureLabelLayout"/>
        <xsl:variable name="styleSheetLabelLayoutLabel" select="exsl:node-set($styleSheetLabelLayout)/@label"/>
        <xsl:variable name="label" select="exsl:node-set($lingPaper)/@figureLabel"/>
        <tex:spec cat="bg"/>
        <xsl:value-of select="exsl:node-set($styleSheetLabelLayout)/@textbefore"/>
        <xsl:choose>
            <xsl:when test="string-length($styleSheetLabelLayoutLabel) &gt; 0">
                <xsl:value-of select="$styleSheetLabelLayoutLabel"/>
            </xsl:when>
            <xsl:when test="string-length($label) &gt; 0">
                <xsl:value-of select="$label"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>Figure</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:value-of select="exsl:node-set($styleSheetLabelLayout)/@textafter"/>
        <tex:spec cat="eg"/>
    </xsl:template>
    <!--  
        OutputFigureLabelAndCaption
    -->
    <xsl:template name="OutputFigureLabelAndCaption">
        <xsl:param name="bDoStyles" select="'Y'"/>
        <xsl:if test="$bDoStyles='Y'">
            <xsl:if test="$sLineSpacing and $sLineSpacing!='single'">
                <tex:spec cat="bg"/>
                <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
            </xsl:if>
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="$styleSheetFigureLabelLayout"/>
                <xsl:with-param name="originalContext" select="."/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="OutputFigureLabel"/>
        <xsl:if test="$bDoStyles='Y'">
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="$styleSheetFigureLabelLayout"/>
                <xsl:with-param name="originalContext" select="."/>
            </xsl:call-template>
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="$styleSheetFigureNumberLayout"/>
                <xsl:with-param name="originalContext" select="."/>
            </xsl:call-template>
        </xsl:if>
        <tex:spec cat="bg"/>
        <xsl:value-of select="exsl:node-set($styleSheetFigureNumberLayout)/@textbefore"/>
        <!--        <xsl:apply-templates select="." mode="figure"/>-->
        <xsl:call-template name="GetFigureNumber">
            <xsl:with-param name="figure" select="."/>
        </xsl:call-template>
        <xsl:value-of select="exsl:node-set($styleSheetFigureNumberLayout)/@textafter"/>
        <tex:spec cat="eg"/>
        <xsl:if test="$bDoStyles='Y'">
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="$styleSheetFigureNumberLayout"/>
                <xsl:with-param name="originalContext" select="."/>
            </xsl:call-template>
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="$styleSheetFigureCaptionLayout"/>
                <xsl:with-param name="originalContext" select="."/>
            </xsl:call-template>
        </xsl:if>
        <tex:spec cat="bg"/>
        <xsl:value-of select="exsl:node-set($styleSheetFigureCaptionLayout)/@textbefore"/>
        <xsl:choose>
            <xsl:when test="$bDoStyles='Y'">
                <xsl:apply-templates select="caption" mode="show"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="caption" mode="contents"/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:value-of select="exsl:node-set($styleSheetFigureCaptionLayout)/@textafter"/>
        <xsl:if test="$bDoStyles='Y'">
            <tex:spec cat="esc"/>
            <tex:spec cat="esc"/>
        </xsl:if>
        <tex:spec cat="eg"/>
        <xsl:if test="$bDoStyles='Y'">
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="$styleSheetFigureCaptionLayout"/>
                <xsl:with-param name="originalContext" select="."/>
            </xsl:call-template>
            <xsl:if test="$sLineSpacing and $sLineSpacing!='single'">
                <tex:spec cat="eg"/>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <xsl:template match="caption | endCaption" mode="show">
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
        <xsl:variable name="styleSheetLabelLayout" select="exsl:node-set($contentLayoutInfo)/figureLabelLayout"/>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="."/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="$styleSheetLabelLayout"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:call-template name="DoType"/>
        <xsl:apply-templates/>
        <xsl:call-template name="DoTypeEnd"/>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="$styleSheetLabelLayout"/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="."/>
            <xsl:with-param name="originalContext" select="."/>
        </xsl:call-template>
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
                <xsl:apply-templates select="text() | *[not(self::indexedItem)][not(self::endnote)]">
                    <xsl:with-param name="bInMarker" select="'Y'"/>
                </xsl:apply-templates>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        OutputFontAttributesInAbstract
    -->
    <xsl:template name="OutputFontAttributesInAbstract">
        <xsl:param name="language"/>
        <xsl:param name="originalContext"/>
        <xsl:param name="bIsOverride" select="'N'"/>
        <xsl:variable name="sFontFamily" select="normalize-space(exsl:node-set($language)/@font-family)"/>
        <xsl:if test="string-length($sFontFamily) &gt; 0">
            <xsl:call-template name="HandleFontFamily">
                <xsl:with-param name="language" select="$language"/>
                <xsl:with-param name="sFontFamily" select="$sFontFamily"/>
                <xsl:with-param name="bIsOverride" select="$bIsOverride"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:variable name="sFontSize" select="normalize-space(exsl:node-set($language)/@font-size)"/>
        <xsl:if test="string-length($sFontSize) &gt; 0">
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
                    <xsl:text>itshape </xsl:text>
                </xsl:when>
                <xsl:when test="$sFontStyle='oblique'">
                    <tex:spec cat="esc"/>
                    <xsl:text>slshape </xsl:text>
                </xsl:when>
                <xsl:when test="$sFontStyle='normal'">
                    <tex:spec cat="esc"/>
                    <xsl:text>upshape </xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <!-- use italic as default -->
                    <tex:spec cat="esc"/>
                    <xsl:text>itshape </xsl:text>
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
                    <xsl:text>upshape </xsl:text>
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
                    <xsl:text>bfseries </xsl:text>
                </xsl:when>
                <xsl:when test="$sFontStyle='italic'">
                    <!-- do nothing - we do *not* want to do a 'normal' or we'll cancel the italic -->
                </xsl:when>
                <xsl:when test="$sFontWeight='normal'">
                    <tex:spec cat="esc"/>
                    <xsl:text>mdseries </xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <!-- use bold as default -->
                    <tex:spec cat="esc"/>
                    <xsl:text>bfseries </xsl:text>
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
        <xsl:if test="not(name()='type') and  string-length($sBackgroundColor) &gt; 0">
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
        <xsl:variable name="sTextTransform" select="normalize-space(exsl:node-set($language)/@text-transform)"/>
        <xsl:if test="string-length($sTextTransform) &gt; 0 and $originalContext and name(exsl:node-set($originalContext)/*)=''">
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
    </xsl:template>
    <!--  
        OutputFontAttributesInAbstractEnd
    -->
    <xsl:template name="OutputFontAttributesInAbstractEnd">
        <xsl:param name="language"/>
        <xsl:param name="originalContext"/>
        <!-- unsuccessful attempt at dealing with "normal" to override inherited values 
            <xsl:param name="bStartParent" select="'Y'"/>
        -->
        <xsl:variable name="sTextTransform" select="normalize-space(exsl:node-set($language)/@text-transform)"/>
        <xsl:if test="string-length($sTextTransform) &gt; 0 and $originalContext and name(exsl:node-set($originalContext)/*)=''">
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
        <xsl:variable name="sBackgroundColor" select="normalize-space(exsl:node-set($language)/@backgroundcolor)"/>
        <xsl:if test="not(name()='type') and  string-length($sBackgroundColor) &gt; 0">
            <tex:spec cat="eg"/>
            <tex:spec cat="eg"/>
        </xsl:if>
        <xsl:variable name="sFontFamily" select="normalize-space(exsl:node-set($language)/@font-family)"/>
        <xsl:if test="string-length($sFontFamily) &gt; 0">
            <tex:spec cat="eg"/>
        </xsl:if>
        <!-- font size does not end with an open brace 
            <xsl:variable name="sFontSize" select="normalize-space(exsl:node-set($language)/@font-size)"/>
            <xsl:if test="string-length($sFontSize) &gt; 0">
            <tex:spec cat="eg"/>
            </xsl:if>
        -->
        <!--        <xsl:variable name="sFontStyle" select="normalize-space(exsl:node-set($language)/@font-style)"/>
        <xsl:if test="string-length($sFontStyle) &gt; 0">
            <tex:spec cat="eg"/>
        </xsl:if>
-->
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
        <!--        <xsl:variable name="sFontWeight" select="normalize-space(exsl:node-set($language)/@font-weight)"/>
        <xsl:if test="string-length($sFontWeight) &gt; 0">
            <xsl:choose>
                <xsl:when test="$sFontStyle='italic' and $sFontWeight!='bold'">
                    <!-\- do nothing - we do *not* want to do a 'normal' or we'll cancel the italic -\->
                </xsl:when>
                <xsl:when test="$sFontWeight='normal'">
                    <tex:spec cat="eg"/>
                </xsl:when>
                <xsl:otherwise>
                    <tex:spec cat="eg"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
-->
        <xsl:variable name="sFontColor" select="normalize-space(exsl:node-set($language)/@color)"/>
        <xsl:if test="string-length($sFontColor) &gt; 0">
            <tex:spec cat="eg"/>
        </xsl:if>
    </xsl:template>
    <!--  
                  OutputFrontOrBackMatterTitle
    -->
    <xsl:template name="OutputFrontOrBackMatterTitle">
        <xsl:param name="id"/>
        <xsl:param name="sTitle"/>
        <xsl:param name="titlePart2"/>
        <xsl:param name="bIsBook" select="'Y'"/>
        <xsl:param name="bDoTwoColumns" select="'N'"/>
        <xsl:param name="layoutInfo"/>
        <xsl:param name="sFirstPageStyle" select="'fancyfirstpage'"/>
        <xsl:param name="fDoPageBreakFormatInfo" select="'Y'"/>
        <xsl:param name="sRunningHeader"/>
        <xsl:choose>
            <xsl:when test="$bIsBook='Y'">
                <xsl:if test="$bDoTwoColumns = 'Y'">
                    <tex:spec cat="esc" nl1="1"/>
                    <xsl:text>twocolumn</xsl:text>
                    <tex:spec cat="lsb"/>
                </xsl:if>
                <tex:cmd name="thispagestyle">
                    <tex:parm>
                        <xsl:choose>
                            <xsl:when test="exsl:node-set($layoutInfo)/@useemptyheaderfooter='yes'">
                                <xsl:text>empty</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="$sFirstPageStyle"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </tex:parm>
                </tex:cmd>
            </xsl:when>
        </xsl:choose>
        <tex:group nl1="1" nl2="1">
            <!--            <xsl:call-template name="DoTitleNeedsSpace"/> Now do this in DoTitleFormatInfo-->
            <xsl:variable name="sTextTransform" select="exsl:node-set($layoutInfo)/@text-transform"/>
            <xsl:choose>
                <xsl:when test="$sTextTransform='uppercase' or $sTextTransform='lowercase'">
                    <xsl:call-template name="DoSpaceBefore">
                        <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                    </xsl:call-template>
                    <xsl:if test="exsl:node-set($layoutInfo)/@textalign='start' or exsl:node-set($layoutInfo)/@textalign='left' or exsl:node-set($layoutInfo)/@textalign='center'">
                        <tex:cmd name="noindent" gr="0" nl2="1"/>
                    </xsl:if>
                    <xsl:call-template name="DoBookMark"/>
                    <xsl:call-template name="DoInternalTargetBegin">
                        <xsl:with-param name="sName" select="$id"/>
                    </xsl:call-template>
                    <xsl:call-template name="DoTitleFormatInfo">
                        <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                        <xsl:with-param name="originalContext" select="$sTitle"/>
                        <xsl:with-param name="fDoPageBreakFormatInfo" select="$fDoPageBreakFormatInfo"/>
                        <xsl:with-param name="fSpaceBeforeAlreadyDone" select="'Y'"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="DoTitleFormatInfo">
                        <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                        <xsl:with-param name="originalContext" select="$sTitle"/>
                        <xsl:with-param name="fDoPageBreakFormatInfo" select="$fDoPageBreakFormatInfo"/>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
            <!--            
            <xsl:if test="$sTextTransform='uppercase' or $sTextTransform='lowercase'">
                <xsl:call-template name="DoSpaceBefore">
                    <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                </xsl:call-template>
                <xsl:call-template name="DoBookMark"/>
                <xsl:call-template name="DoInternalTargetBegin">
                    <xsl:with-param name="sName" select="$id"/>
                </xsl:call-template>
            </xsl:if>
            <xsl:call-template name="DoTitleFormatInfo">
                <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                <xsl:with-param name="originalContext" select="$sTitle"/>
                <xsl:with-param name="fDoPageBreakFormatInfo" select="$fDoPageBreakFormatInfo"/>
            </xsl:call-template>
-->
            <xsl:if test="string-length($sTextTransform)=0 or not($sTextTransform='uppercase' or $sTextTransform='lowercase')">
                <xsl:call-template name="DoBookMark">
                    <xsl:with-param name="id" select="$id"/>
                    <xsl:with-param name="sTitle" select="$sTitle"/>
                </xsl:call-template>
                <xsl:call-template name="DoInternalTargetBegin">
                    <xsl:with-param name="sName" select="$id"/>
                </xsl:call-template>
            </xsl:if>
            <xsl:choose>
                <xsl:when test="$bIsBook='Y'">
                    <xsl:call-template name="OutputChapTitle">
                        <xsl:with-param name="sTitle" select="$sTitle"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:if test="not(exsl:node-set($layoutInfo)/@useLabel) or exsl:node-set($layoutInfo)/@useLabel='yes'">
                        <xsl:value-of select="$sTitle"/>
                    </xsl:if>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:variable name="contentForThisElement">
                <xsl:choose>
                    <xsl:when test="$bIsBook='Y'">
                        <xsl:call-template name="OutputChapTitle">
                            <xsl:with-param name="sTitle" select="$sTitle"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:if test="not(exsl:node-set($layoutInfo)/@useLabel) or exsl:node-set($layoutInfo)/@useLabel='yes'">
                            <xsl:value-of select="$sTitle"/>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
            </xsl:call-template>
            <xsl:call-template name="DoTitleFormatInfoEnd">
                <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                <xsl:with-param name="originalContext" select="$sTitle"/>
                <xsl:with-param name="contentOfThisElement" select="$contentForThisElement"/>
            </xsl:call-template>
            <xsl:call-template name="DoInternalTargetEnd"/>
            <xsl:if test="$titlePart2">
                <xsl:apply-templates select="$titlePart2"/>
            </xsl:if>
            <xsl:variable name="sHeader">
                <xsl:choose>
                    <xsl:when test="string-length($sRunningHeader) &gt; 0">
                        <xsl:value-of select="$sRunningHeader"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$sTitle"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:call-template name="DoRunningHeader">
                <xsl:with-param name="sHeader" select="$sHeader"/>
            </xsl:call-template>
            <xsl:call-template name="CreateAddToContents">
                <xsl:with-param name="id" select="$id"/>
            </xsl:call-template>
        </tex:group>
        <xsl:call-template name="DoNotBreakHere"/>
        <tex:cmd name="par" nl2="1"/>
        <xsl:call-template name="DoSpaceAfter">
            <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        OutputIndexedItemsPageNumber
    -->
    <xsl:template name="OutputIndexedItemsPageNumber">
        <xsl:param name="sIndexedItemID"/>
        <xsl:call-template name="DoInternalHyperlinkBegin">
            <xsl:with-param name="sName" select="$sIndexedItemID"/>
        </xsl:call-template>
        <xsl:call-template name="LinkAttributesBegin">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/indexLinkLayout"/>
        </xsl:call-template>
        <xsl:variable name="sPage" select="document($sIndexFile)/idx/indexitem[@ref=$sIndexedItemID]/@page"/>
        <xsl:choose>
            <xsl:when test="$sPage">
                <xsl:value-of select="$sPage"/>
            </xsl:when>
            <xsl:otherwise>??</xsl:otherwise>
        </xsl:choose>
        <xsl:if test="ancestor::endnote">
            <xsl:text>n</xsl:text>
        </xsl:if>
        <xsl:call-template name="LinkAttributesEnd">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/indexLinkLayout"/>
        </xsl:call-template>
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
        OutputInterlinearLineAsTableCells
    -->
    <xsl:template name="OutputInterlinearLineTableCellContent">
        <xsl:param name="lang"/>
        <xsl:param name="sFirst"/>
        <xsl:variable name="sContext">
            <xsl:call-template name="GetContextOfItem"/>
        </xsl:variable>
        <xsl:variable name="langDataLayout">
            <xsl:call-template name="GetBestLangDataLayout"/>
        </xsl:variable>
        <xsl:variable name="glossLayout" select="exsl:node-set($contentLayoutInfo)/glossLayout"/>
        <xsl:choose>
            <xsl:when test="langData">
                <xsl:call-template name="HandleLangDataTextBeforeOutside">
                    <xsl:with-param name="langDataLayout" select="exsl:node-set($langDataLayout)/*"/>
                    <xsl:with-param name="sLangDataContext" select="$sContext"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="HandleGlossTextBeforeOutside">
                    <xsl:with-param name="glossLayout" select="$glossLayout"/>
                    <xsl:with-param name="sGlossContext" select="$sContext"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="key('LanguageID',$lang)"/>
            <xsl:with-param name="originalContext" select="$sFirst"/>
        </xsl:call-template>
        <xsl:choose>
            <xsl:when test="langData">
                <xsl:call-template name="HandleLangDataTextBeforeAndFontOverrides">
                    <xsl:with-param name="langDataLayout" select="exsl:node-set($langDataLayout)/*"/>
                    <xsl:with-param name="sLangDataContext" select="$sContext"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="HandleGlossTextBeforeAndFontOverrides">
                    <xsl:with-param name="glossLayout" select="$glossLayout"/>
                    <xsl:with-param name="sGlossContext" select="$sContext"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:value-of select="$sFirst"/>
        <xsl:choose>
            <xsl:when test="langData">
                <xsl:call-template name="HandleLangDataTextAfterAndFontOverrides">
                    <xsl:with-param name="langDataLayout" select="exsl:node-set($langDataLayout)/*"/>
                    <xsl:with-param name="sLangDataContext" select="$sContext"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="HandleGlossTextAfterAndFontOverrides">
                    <xsl:with-param name="glossLayout" select="$glossLayout"/>
                    <xsl:with-param name="sGlossContext" select="$sContext"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="key('LanguageID',$lang)"/>
            <xsl:with-param name="originalContext" select="$sFirst"/>
        </xsl:call-template>
        <xsl:choose>
            <xsl:when test="langData">
                <xsl:call-template name="HandleLangDataTextAfterOutside">
                    <xsl:with-param name="langDataLayout" select="exsl:node-set($langDataLayout)/*"/>
                    <xsl:with-param name="sLangDataContext" select="$sContext"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="HandleGlossTextAfterOutside">
                    <xsl:with-param name="glossLayout" select="$glossLayout"/>
                    <xsl:with-param name="sGlossContext" select="$sContext"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
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
        <xsl:choose>
            <xsl:when test="$sSource">
                <xsl:apply-templates select="$sSource" mode="contents">
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:apply-templates>
            </xsl:when>
            <xsl:when test="string-length(normalize-space($sRef)) &gt; 0">
                <xsl:call-template name="DoInterlinearRefCitation">
                    <xsl:with-param name="sRef" select="$sRef"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  
        OutputKeywordsTitleAndContent
    -->
    <xsl:template name="OutputKeywordsTitleAndContent">
        <xsl:param name="sKeywordsID"/>
        <xsl:param name="layoutInfo"/>
        <tex:group>
            <xsl:variable name="sId">
                <xsl:call-template name="GetIdToUse">
                    <xsl:with-param name="sBaseId" select="$sKeywordsID"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="sLabel">
                <xsl:call-template name="OutputKeywordsLabel"/>
            </xsl:variable>
            <xsl:variable name="keywordsLayoutInfo" select="exsl:node-set($layoutInfo)/keywordsLayout"/>
            <tex:group>
                <xsl:if test="$bIsBook">
                    <xsl:call-template name="DoPageBreakFormatInfo">
                        <xsl:with-param name="layoutInfo" select="$keywordsLayoutInfo"/>
                    </xsl:call-template>
                    <xsl:if test="not(ancestor::chapterInCollection)">
                        <tex:cmd name="thispagestyle">
                            <tex:parm>
                                <xsl:choose>
                                    <xsl:when test="exsl:node-set($backMatterLayoutInfo)/headerFooterPageStyles">backmatterfirstpage</xsl:when>
                                    <xsl:when test="exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles/headerFooterFirstPage">bodyfirstpage</xsl:when>
                                    <xsl:otherwise>body</xsl:otherwise>
                                </xsl:choose>
                            </tex:parm>
                        </tex:cmd>
                    </xsl:if>
                </xsl:if>
                <xsl:call-template name="DoSpaceBefore">
                    <xsl:with-param name="layoutInfo" select="$keywordsLayoutInfo"/>
                </xsl:call-template>
                <!-- We need to do the needspace here or we get too much extra vertical space or we can strand a title 
                    at the bottom of a page. -->
                <tex:cmd name="XLingPaperneedspace">
                    <tex:parm>
                        <xsl:text>3</xsl:text>
                        <tex:cmd name="baselineskip" gr="0"/>
                    </tex:parm>
                </tex:cmd>
                <xsl:if test="exsl:node-set($keywordsLayoutInfo)/@textalign='start' or exsl:node-set($keywordsLayoutInfo)/@textalign='left' or exsl:node-set($keywordsLayoutInfo)/@textalign='center'">
                    <tex:cmd name="noindent"/>
                </xsl:if>
                <xsl:if test="@showincontents='yes'">
                    <xsl:call-template name="DoInternalTargetBegin">
                        <xsl:with-param name="sName" select="$sId"/>
                    </xsl:call-template>
                    <xsl:call-template name="DoInternalTargetEnd"/>
                    <xsl:call-template name="DoBookMark"/>
                    <xsl:call-template name="CreateAddToContents">
                        <xsl:with-param name="id" select="$sId"/>
                    </xsl:call-template>
                    <xsl:call-template name="DoRunningHeader">
                        <xsl:with-param name="sHeader" select="$sLabel"/>
                        <xsl:with-param name="fNewlineAfterMarkBoth" select="'N'"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:call-template name="OutputFontAttributes">
                    <xsl:with-param name="language" select="$keywordsLayoutInfo"/>
                    <xsl:with-param name="originalContext" select="."/>
                </xsl:call-template>
                <xsl:if test="string-length(exsl:node-set($keywordsLayoutInfo)/@textalign) &gt; 0">
                    <xsl:call-template name="DoTextAlign">
                        <xsl:with-param name="layoutInfo" select="$keywordsLayoutInfo"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:call-template name="DoFormatLayoutInfoTextBefore">
                    <xsl:with-param name="layoutInfo" select="$keywordsLayoutInfo"/>
                </xsl:call-template>
                <xsl:call-template name="OutputChapTitle">
                    <xsl:with-param name="sTitle" select="$sLabel"/>
                </xsl:call-template>
                <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                    <xsl:with-param name="layoutInfo" select="$keywordsLayoutInfo"/>
                </xsl:call-template>
                <xsl:variable name="contentForThisElement">
                    <xsl:call-template name="OutputChapTitle">
                        <xsl:with-param name="sTitle" select="$sLabel"/>
                    </xsl:call-template>
                    <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                        <xsl:with-param name="layoutInfo" select="$keywordsLayoutInfo"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:if test="string-length(exsl:node-set($keywordsLayoutInfo)/@textalign) &gt; 0">
                    <!-- Note: need to be sure to enclose this in a group or it will become the case from now until the next text align -->
                    <xsl:choose>
                        <xsl:when test="exsl:node-set($keywordsLayoutInfo)/@textalign='center' or exsl:node-set($keywordsLayoutInfo)/@textalign='right' or exsl:node-set($keywordsLayoutInfo)/@textalign='end'">
                            <!-- must have \\ at end or it will not actually center -->
                            <xsl:if test="string-length($contentForThisElement) &gt; 0">
                                <xsl:if test="child::*[position()=last()][name()='br'][not(following-sibling::text())]">
                                    <!-- cannot have two \\ in a row, so need to insert something; we'll use a non-breaking space -->
                                    <xsl:text>&#xa0;</xsl:text>
                                </xsl:if>
                                <xsl:if test="exsl:node-set($keywordsLayoutInfo)/@keywordLabelOnSameLineAsKeywords!='no'">
                                    <tex:group>
                                        <xsl:call-template name="OutputFontAttributes">
                                            <xsl:with-param name="language" select="exsl:node-set($keywordsLayoutInfo)/keywordLayout"/>
                                        </xsl:call-template>
                                        <xsl:call-template name="OutputKeywordsShownHere">
                                            <xsl:with-param name="sTextBetweenKeywords">
                                                <xsl:call-template name="GetTextBetweenKeywords">
                                                    <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                                                </xsl:call-template>
                                            </xsl:with-param>
                                        </xsl:call-template>
                                        <xsl:call-template name="OutputFontAttributesEnd">
                                            <xsl:with-param name="language" select="exsl:node-set($keywordsLayoutInfo)/keywordLayout"/>
                                        </xsl:call-template>
                                    </tex:group>
                                </xsl:if>
                                <tex:spec cat="esc"/>
                                <tex:spec cat="esc"/>
                            </xsl:if>
                        </xsl:when>
                        <xsl:when test="exsl:node-set($keywordsLayoutInfo)/@textalign='start' or exsl:node-set($keywordsLayoutInfo)/@textalign='left'">
                            <xsl:if test="exsl:node-set($keywordsLayoutInfo)/@keywordLabelOnSameLineAsKeywords!='no'">
                                <tex:group>
                                    <xsl:call-template name="OutputFontAttributes">
                                        <xsl:with-param name="language" select="exsl:node-set($keywordsLayoutInfo)/keywordLayout"/>
                                    </xsl:call-template>
                                    <xsl:call-template name="OutputKeywordsShownHere">
                                        <xsl:with-param name="sTextBetweenKeywords">
                                            <xsl:call-template name="GetTextBetweenKeywords">
                                                <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                                            </xsl:call-template>
                                        </xsl:with-param>
                                    </xsl:call-template>
                                    <xsl:call-template name="OutputFontAttributesEnd">
                                        <xsl:with-param name="language" select="exsl:node-set($keywordsLayoutInfo)/keywordLayout"/>
                                    </xsl:call-template>
                                </tex:group>
                            </xsl:if>
                            <tex:cmd name="par"/>
                        </xsl:when>
                        <xsl:otherwise/>
                    </xsl:choose>
                    <tex:spec cat="eg"/>
                </xsl:if>
                <xsl:call-template name="OutputFontAttributesEnd">
                    <xsl:with-param name="language" select="$keywordsLayoutInfo"/>
                    <xsl:with-param name="originalContext" select="."/>
                </xsl:call-template>
                <xsl:if test="exsl:node-set($keywordsLayoutInfo)/@keywordLabelOnSameLineAsKeywords='no'">
                    <xsl:if test="exsl:node-set($keywordsLayoutInfo)/@textalign='start' or exsl:node-set($keywordsLayoutInfo)/@textalign='left'">
                        <tex:cmd name="par"/>
                    </xsl:if>
                    <xsl:call-template name="DoSpaceAfter">
                        <xsl:with-param name="layoutInfo" select="$keywordsLayoutInfo"/>
                    </xsl:call-template>
                    <tex:group>
                        <xsl:if test="exsl:node-set($keywordsLayoutInfo)/@textalign='right' or exsl:node-set($keywordsLayoutInfo)/@textalign='end'">
                            <tex:cmd name="raggedleft"/>
                        </xsl:if>
                        <xsl:call-template name="OutputFontAttributes">
                            <xsl:with-param name="language" select="exsl:node-set($keywordsLayoutInfo)/keywordLayout"/>
                        </xsl:call-template>
                        <xsl:if test="exsl:node-set($keywordsLayoutInfo)/@textalign='start' or exsl:node-set($keywordsLayoutInfo)/@textalign='left'">
                            <tex:cmd name="noindent"/>
                        </xsl:if>
                        <xsl:call-template name="OutputKeywordsShownHere">
                            <xsl:with-param name="sTextBetweenKeywords">
                                <xsl:call-template name="GetTextBetweenKeywords">
                                    <xsl:with-param name="layoutInfo" select="$keywordsLayoutInfo"/>
                                </xsl:call-template>
                            </xsl:with-param>
                        </xsl:call-template>
                        <xsl:call-template name="OutputFontAttributesEnd">
                            <xsl:with-param name="language" select="exsl:node-set($keywordsLayoutInfo)/keywordLayout"/>
                        </xsl:call-template>
                        <xsl:if test="exsl:node-set($keywordsLayoutInfo)/@textalign!='center'">
                            <tex:cmd name="par"/>
                        </xsl:if>
                    </tex:group>
                </xsl:if>
            </tex:group>
            <xsl:if test="exsl:node-set($keywordsLayoutInfo)/@keywordLabelOnSameLineAsKeywords!='no'">
                <xsl:call-template name="DoSpaceAfter">
                    <xsl:with-param name="layoutInfo" select="$keywordsLayoutInfo"/>
                </xsl:call-template>
            </xsl:if>
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="exsl:node-set($keywordsLayoutInfo)/keywordsLayout"/>
            </xsl:call-template>
        </tex:group>
    </xsl:template>
    <!--  
        OutputSectionNumber
    -->
    <xsl:template name="OutputSectionNumber">
        <xsl:param name="layoutInfo"/>
        <xsl:param name="bIsForBookmark" select="'N'"/>
        <xsl:param name="sContentsPeriod"/>
        <xsl:variable name="bAppendix">
            <xsl:if test="ancestor-or-self::*[name()='appendix']">
                <xsl:text>Y</xsl:text>
            </xsl:if>
            <!--            <xsl:for-each select="ancestor::*">
                <xsl:if test="name(.)='appendix'">Y</xsl:if>
            </xsl:for-each>-->
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$bIsForBookmark='N'">
                <xsl:call-template name="OutputSectionNumberProper">
                    <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                    <xsl:with-param name="bAppendix" select="$bAppendix"/>
                    <xsl:with-param name="sContentsPeriod" select="$sContentsPeriod"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="OutputSectionNumberProper">
                    <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                    <xsl:with-param name="bAppendix" select="$bAppendix"/>
                    <xsl:with-param name="sContentsPeriod" select="$sContentsPeriod"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
      OutputSectionNumberAndTitle
   -->
    <xsl:template name="OutputSectionNumberAndTitle">
        <xsl:param name="layoutInfo"/>
        <xsl:call-template name="OutputSectionNumber">
            <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
        </xsl:call-template>
        <xsl:call-template name="OutputSectionTitle"/>
    </xsl:template>
    <!--  
      OutputSectionNumberAndTitleInContents
   -->
    <xsl:template name="OutputSectionNumberAndTitleInContents">
        <xsl:param name="contentsLayoutToUse" select="exsl:node-set($contentsLayout)/contentsLayout"/>
        <xsl:param name="layoutInfo"/>
        <xsl:call-template name="OutputSectionNumber">
            <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
            <xsl:with-param name="sContentsPeriod">
                <xsl:if test="saxon:node-set($contentsLayoutToUse)/@useperiodaftersectionnumber='yes'">
                    <xsl:text>.</xsl:text>
                </xsl:if>
            </xsl:with-param>
        </xsl:call-template>
        <xsl:call-template name="OutputSectionTitleInContents"/>
    </xsl:template>
    <!--  
      OutputSectionTitle
   -->
    <xsl:template name="OutputSectionTitle">
        <!--        <xsl:text disable-output-escaping="yes">&#x20;</xsl:text>-->
        <xsl:apply-templates select="secTitle"/>
    </xsl:template>
    <!--  
      OutputSectionTitleInContents
   -->
    <xsl:template name="OutputSectionTitleInContents">
        <xsl:text disable-output-escaping="yes">&#x20;</xsl:text>
        <xsl:apply-templates select="secTitle" mode="contents"/>
    </xsl:template>
    <!--  
        OutputTableNumberedLabel
    -->
    <xsl:template name="OutputTableNumberedLabel">
        <xsl:variable name="styleSheetLabelLayout" select="$styleSheetTableNumberedLabelLayout"/>
        <xsl:variable name="styleSheetLabelLayoutLabel" select="exsl:node-set($styleSheetLabelLayout)/@label"/>
        <xsl:variable name="label" select="exsl:node-set($lingPaper)/@tablenumberedLabel"/>
        <tex:spec cat="bg"/>
        <xsl:value-of select="exsl:node-set($styleSheetLabelLayout)/@textbefore"/>
        <xsl:choose>
            <xsl:when test="string-length($styleSheetLabelLayoutLabel) &gt; 0">
                <xsl:value-of select="$styleSheetLabelLayoutLabel"/>
            </xsl:when>
            <xsl:when test="string-length($label) &gt; 0">
                <xsl:value-of select="$label"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>Table</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:value-of select="exsl:node-set($styleSheetLabelLayout)/@textafter"/>
        <tex:spec cat="eg"/>
    </xsl:template>
    <!--  
        OutputTableNumberedLabelAndCaption
    -->
    <xsl:template name="OutputTableNumberedLabelAndCaption">
        <xsl:param name="bDoStyles" select="'Y'"/>
        <tex:spec cat="bg"/>
        <xsl:if test="$bDoStyles='Y'">
            <tex:spec cat="esc"/>
            <xsl:text>protect</xsl:text>
            <xsl:choose>
                <xsl:when test="table/@align='center'">
                    <tex:spec cat="esc"/>
                    <xsl:text>centering </xsl:text>
                </xsl:when>
                <xsl:when test="table/@align='right'">
                    <tex:spec cat="esc"/>
                    <xsl:text>raggedleft</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <tex:spec cat="esc"/>
                    <xsl:text>raggedright</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="HandleTableLineSpacing">
                <xsl:with-param name="bDoBeginGroup" select="'Y'"/>
            </xsl:call-template>
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="$styleSheetTableNumberedLabelLayout"/>
                <xsl:with-param name="originalContext" select="."/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="OutputTableNumberedLabel"/>
        <xsl:if test="$bDoStyles='Y'">
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="$styleSheetTableNumberedLabelLayout"/>
                <xsl:with-param name="originalContext" select="."/>
            </xsl:call-template>
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="$styleSheetTableNumberedNumberLayout"/>
                <xsl:with-param name="originalContext" select="."/>
            </xsl:call-template>
        </xsl:if>
        <tex:spec cat="bg"/>
        <xsl:value-of select="exsl:node-set($styleSheetTableNumberedNumberLayout)/@textbefore"/>
        <!--        <xsl:apply-templates select="." mode="tablenumbered"/>-->
        <xsl:call-template name="GetTableNumberedNumber">
            <xsl:with-param name="tablenumbered" select="."/>
        </xsl:call-template>
        <xsl:value-of select="exsl:node-set($styleSheetTableNumberedNumberLayout)/@textafter"/>
        <tex:spec cat="eg"/>
        <xsl:if test="$bDoStyles='Y'">
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="$styleSheetTableNumberedNumberLayout"/>
                <xsl:with-param name="originalContext" select="."/>
            </xsl:call-template>
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="$styleSheetTableNumberedCaptionLayout"/>
                <xsl:with-param name="originalContext" select="."/>
            </xsl:call-template>
        </xsl:if>
        <tex:spec cat="bg"/>
        <xsl:value-of select="exsl:node-set($styleSheetTableNumberedCaptionLayout)/@textbefore"/>
        <xsl:choose>
            <xsl:when test="$bDoStyles='Y'">
                <xsl:apply-templates select="table/caption | table/endCaption | caption" mode="show"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="table/caption | table/endCaption | caption" mode="contents"/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:value-of select="exsl:node-set($styleSheetTableNumberedCaptionLayout)/@textafter"/>
        <!--        <xsl:if test="table/@align='center' or table/@align='right'">-->
        <xsl:if test="$bDoStyles='Y'">
            <tex:spec cat="esc"/>
            <tex:spec cat="esc"/>
        </xsl:if>
        <!--        </xsl:if>-->
        <tex:spec cat="eg"/>
        <xsl:if test="$bDoStyles='Y'">
            <xsl:call-template name="OutputFontAttributesEnd">
                <xsl:with-param name="language" select="$styleSheetTableNumberedCaptionLayout"/>
                <xsl:with-param name="originalContext" select="."/>
            </xsl:call-template>
            <xsl:if test="$sLineSpacing and $sLineSpacing!='single'">
                <tex:spec cat="eg"/>
            </xsl:if>
        </xsl:if>
        <tex:spec cat="eg"/>
    </xsl:template>
    <!--  
        ProcessDocument
    -->
    <xsl:template name="ProcessDocument">
        <xsl:if test="$sBasicPointSize!=$sLaTeXBasicPointSize">
            <xsl:call-template name="HandleFontSize">
                <xsl:with-param name="sSize">
                    <xsl:value-of select="$sBasicPointSize"/>
                    <xsl:text>pt</xsl:text>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:if>
        <xsl:if test="$contents">
            <tex:cmd name="XLingPapertableofcontents" gr="0" nl2="0"/>
        </xsl:if>
        <xsl:choose>
            <xsl:when test="$chapters">
                <!--                            <xsl:if test="exsl:node-set($frontMatterLayoutInfo)/contentsLayout/@showbookmarks!='no'">
                    <xsl:call-template name="DoBookmarksForPaper"/>
                    </xsl:if>
                -->
                <xsl:apply-templates select="child::node()[name()!='publishingInfo']"/>
            </xsl:when>
            <xsl:otherwise>
                <!--                            <xsl:if test="exsl:node-set($frontMatterLayoutInfo)/contentsLayout/@showbookmarks!='no'">
                    <xsl:call-template name="DoBookmarksForPaper"/>
                    </xsl:if>
                -->
                <xsl:apply-templates select="frontMatter"/>
                <xsl:apply-templates select="//section1[not(parent::appendix)]"/>
                <xsl:apply-templates select="//backMatter"/>
            </xsl:otherwise>
        </xsl:choose>
        <!-- somewhere there's an opening bracket... -->
        <!--                    <tex:spec cat="eg"/>-->
        <xsl:if test="$bHasContents='Y' or $bHasIndex='Y'">
            <tex:cmd name="clearpage" gr="0"/>
        </xsl:if>
        <xsl:if test="$bHasContents='Y'">
            <tex:cmd name="XLingPaperendtableofcontents" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:if test="$bHasIndex='Y'">
            <tex:cmd name="XLingPaperendindex" gr="0" nl2="1"/>
        </xsl:if>
        <!-- every once in a great while, the running headers and footers will be wrong on the last page; this \pagebreak fixes it -->
        <tex:cmd name="pagebreak" gr="0"/>
    </xsl:template>
    <!--  
        SetChapterNumberWidth
    -->
    <xsl:template name="SetChapterNumberWidth" priority="10">
        <xsl:param name="contentsLayoutToUse" select="saxon:node-set($contentsLayout)/contentsLayout"/>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
            <xsl:with-param name="sCommandToSet" select="'levelonewidth'"/>
            <xsl:with-param name="sValue">
                <xsl:call-template name="OutputChapterNumber"/>
                <xsl:if test="exsl:node-set($contentsLayoutToUse)/@useperiodafterchapternumber='yes'">
                    <xsl:text>.</xsl:text>
                </xsl:if>
                <xsl:text>&#xa0;</xsl:text>
                <tex:spec cat="esc"/>
                <xsl:text>&#x20;</xsl:text>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--  
        SetFonts
    -->
    <xsl:template name="SetFonts">
        <xsl:choose>
            <xsl:when test="contains($sDefaultFontFamilyXeLaTeXSpecial,'graphite')">
                <tex:cmd name="setmainfont" nl2="1">
                    <tex:opt>
                        <xsl:value-of select="$sRendererIsGraphite"/>
                        <xsl:call-template name="HandleXeLaTeXSpecialFontFeature">
                            <xsl:with-param name="sList" select="$sDefaultFontFamilyXeLaTeXSpecial"/>
                            <xsl:with-param name="bIsFirstOpt" select="'N'"/>
                        </xsl:call-template>
                    </tex:opt>
                    <tex:parm>
                        <xsl:value-of select="$sDefaultFontFamily"/>
                    </tex:parm>
                </tex:cmd>
            </xsl:when>
            <xsl:otherwise>
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
            </xsl:otherwise>
        </xsl:choose>
        <xsl:variable name="fontFamiliesWithGraphite" select="//@font-family[string-length(normalize-space(.)) &gt; 0][parent::*[contains(@XeLaTeXSpecial,'graphite')]]"/>
        <xsl:variable name="fontFamiliesWithoutGraphite" select="//@font-family[string-length(normalize-space(.)) &gt; 0][parent::*[not(contains(@XeLaTeXSpecial,'graphite'))]]"/>
        <xsl:variable name="fontFamilies" select="$fontFamiliesWithGraphite | $fontFamiliesWithoutGraphite"/>
        <xsl:for-each select="$fontFamiliesWithGraphite">
            <xsl:variable name="iPos" select="position()"/>
            <xsl:variable name="language" select=".."/>
            <xsl:variable name="thisOne">
                <xsl:value-of select="normalize-space(.)"/>
            </xsl:variable>
            <xsl:variable name="thisOneXeLaTeXSpecial">
                <xsl:value-of select="normalize-space(exsl:node-set($language)/@XeLaTeXSpecial)"/>
            </xsl:variable>
            <xsl:variable name="seenBefore" select="exsl:node-set($fontFamiliesWithGraphite)[position() &lt; $iPos][.=$thisOne and ../@XeLaTeXSpecial=$thisOneXeLaTeXSpecial]"/>
            <xsl:if test="not($seenBefore)">
                <xsl:call-template name="DefineAFontFamily">
                    <xsl:with-param name="sFontFamilyName">
                        <xsl:call-template name="GetFontFamilyName"/>
                        <xsl:value-of select="$sGraphiteForFontName"/>
                        <xsl:call-template name="HandleXeLaTeXSpecialFontFeatureForFontName">
                            <xsl:with-param name="sList" select="parent::*/@XeLaTeXSpecial"/>
                        </xsl:call-template>
                    </xsl:with-param>
                    <xsl:with-param name="sBaseFontName" select="."/>
                </xsl:call-template>
            </xsl:if>
        </xsl:for-each>
        <xsl:for-each select="$fontFamiliesWithoutGraphite">
            <xsl:variable name="iPos" select="position()"/>
            <xsl:variable name="language" select=".."/>
            <xsl:variable name="thisOne">
                <xsl:value-of select="normalize-space(.)"/>
            </xsl:variable>
            <!--            
    Used to ignore if there was one with Graphite; now we use distinct names.
    <xsl:variable name="seenBefore" select="exsl:node-set($fontFamiliesWithoutGraphite)[position() &lt; $iPos]/. = $thisOne or exsl:node-set($fontFamiliesWithGraphite)/. = $thisOne"/>-->
            <xsl:variable name="seenBefore" select="exsl:node-set($fontFamiliesWithoutGraphite)[position() &lt; $iPos]/. = $thisOne"/>
            <xsl:if test="not($seenBefore)">
                <xsl:call-template name="DefineAFontFamily">
                    <xsl:with-param name="sFontFamilyName">
                        <xsl:call-template name="GetFontFamilyName"/>
                    </xsl:with-param>
                    <xsl:with-param name="sBaseFontName" select="."/>
                </xsl:call-template>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>
    <!--  
        SetFootnoteRule
    -->
    <xsl:template name="SetFootnoteRule">
        <xsl:variable name="layoutInfo" select="exsl:node-set($pageLayoutInfo)/footnoteLine"/>
        <xsl:if test="$layoutInfo">
            <!-- the only thing I could find that did anything but hang xelatex was this:
                \makeatletter\renewcommand\footnoterule{\kern-3\p@\hrule\@width4in\kern2.6\p@}\makeatother
                
                Note that the width is some special value;  we can change the length and that works (the 4in above).
            -->
            <!--<xsl:if test="exsl:node-set($layoutInfo)/@leaderpattern and exsl:node-set($layoutInfo)/@leaderpattern!='none'">
                <!-\-                        <fo:leader>-\->
                <xsl:attribute name="leader-pattern">
                <xsl:value-of select="exsl:node-set($layoutInfo)/@leaderpattern"/>
                </xsl:attribute>
                <xsl:if test="exsl:node-set($layoutInfo)/@leaderlength">
                <xsl:attribute name="leader-length">
                <xsl:value-of select="exsl:node-set($layoutInfo)/@leaderlength"/>
                </xsl:attribute>
                </xsl:if>
                <xsl:if test="exsl:node-set($layoutInfo)/@leaderwidth">
                <xsl:attribute name="leader-pattern-width">
                <xsl:value-of select="exsl:node-set($layoutInfo)/@leaderwidth"/>
                </xsl:attribute>
                </xsl:if>
                <!-\-                        </fo:leader>-\->
                </xsl:if>-->
        </xsl:if>
    </xsl:template>
    <!--  
        SetHeaderFooter
    -->
    <xsl:template name="SetHeaderFooter">
        <!-- general style -->
        <xsl:call-template name="SetHeaderFooterStyle">
            <xsl:with-param name="sStyleName" select="'fancyfirstpage'"/>
            <xsl:with-param name="layoutInfo" select="exsl:node-set($pageLayoutInfo)/headerFooterPageStyles/headerFooterFirstPage"/>
        </xsl:call-template>
        <xsl:call-template name="SetHeaderFooterStyle">
            <xsl:with-param name="sStyleName" select="'fancy'"/>
            <xsl:with-param name="layoutInfo" select="exsl:node-set($pageLayoutInfo)/headerFooterPageStyles/*[not(name()='headerFooterFirstPage')]"/>
            <xsl:with-param name="sPageStyle" select="'pagestyle'"/>
        </xsl:call-template>
        <!-- front matter title -->
        <xsl:call-template name="SetHeaderFooterStyle">
            <xsl:with-param name="sStyleName" select="'frontmattertitle'"/>
            <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/titleHeaderFooterPageStyles"/>
        </xsl:call-template>
        <!-- front matter-->
        <xsl:call-template name="SetHeaderFooterStyle">
            <xsl:with-param name="sStyleName" select="'frontmatterfirstpage'"/>
            <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/headerFooterPageStyles/headerFooterFirstPage"/>
        </xsl:call-template>
        <xsl:call-template name="SetHeaderFooterStyle">
            <xsl:with-param name="sStyleName" select="'frontmatter'"/>
            <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/headerFooterPageStyles/*[not(name()='headerFooterFirstPage')]"/>
        </xsl:call-template>
        <!-- body-->
        <xsl:call-template name="SetHeaderFooterStyle">
            <xsl:with-param name="sStyleName" select="'bodyfirstpage'"/>
            <xsl:with-param name="layoutInfo" select="exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles/headerFooterFirstPage"/>
        </xsl:call-template>
        <xsl:call-template name="SetHeaderFooterStyle">
            <xsl:with-param name="sStyleName" select="'body'"/>
            <xsl:with-param name="layoutInfo" select="exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles/*[not(name()='headerFooterFirstPage')]"/>
        </xsl:call-template>
        <!-- back matter-->
        <xsl:call-template name="SetHeaderFooterStyle">
            <xsl:with-param name="sStyleName" select="'backmatterfirstpage'"/>
            <xsl:with-param name="layoutInfo" select="exsl:node-set($backMatterLayoutInfo)/headerFooterPageStyles/headerFooterFirstPage"/>
        </xsl:call-template>
        <xsl:call-template name="SetHeaderFooterStyle">
            <xsl:with-param name="sStyleName" select="'backmatter'"/>
            <xsl:with-param name="layoutInfo" select="exsl:node-set($backMatterLayoutInfo)/headerFooterPageStyles/*[not(name()='headerFooterFirstPage')]"/>
        </xsl:call-template>
        <!-- the first page exception -->
        <!--   doing above now
    <tex:cmd name="fancypagestyle" nl2="1">
            <tex:parm>plain</tex:parm>
            <tex:parm>
                <tex:cmd name="fancyhf" nl2="1"/>
                <xsl:for-each select="exsl:node-set($pageLayoutInfo)/headerFooterPageStyles/headerFooterFirstPage">
                    <!-\- uses the same layout for all pages -\->
                    <xsl:for-each select="*[not(nothing)]">
                        <!-\- for each left, center, right item -\->
                        <xsl:call-template name="DoHeaderFooterItem">
                            <xsl:with-param name="item" select="."/>
                        </xsl:call-template>
                    </xsl:for-each>
                </xsl:for-each>
                <xsl:call-template name="SetHeaderFooterRuleWidths"/>
            </tex:parm>
        </tex:cmd>
-->
    </xsl:template>
    <!--  
        SetHeaderFooterStyle
    -->
    <xsl:template name="SetHeaderFooterStyle">
        <xsl:param name="sStyleName"/>
        <xsl:param name="layoutInfo"/>
        <xsl:param name="sPageStyle" select="'fancypagestyle'"/>
        <xsl:if test="$layoutInfo">
            <tex:cmd name="{$sPageStyle}" nl2="1">
                <tex:parm>
                    <xsl:value-of select="$sStyleName"/>
                </tex:parm>
            </tex:cmd>
            <xsl:if test="$sPageStyle='fancypagestyle'">
                <tex:spec cat="bg"/>
            </xsl:if>
            <tex:cmd name="fancyhf" nl2="1"/>
            <xsl:variable name="originalContext" select="."/>
            <xsl:for-each select="exsl:node-set($layoutInfo)[name()='headerFooterPage' or name()='headerFooterFirstPage']/*">
                <!-- uses the same layout for all pages -->
                <xsl:for-each select="*">
                    <!-- for each left, center, right item -->
                    <xsl:if test="not(descendant::nothing)">
                        <xsl:call-template name="DoHeaderFooterItem">
                            <xsl:with-param name="item" select="."/>
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                        </xsl:call-template>
                    </xsl:if>
                </xsl:for-each>
            </xsl:for-each>
            <xsl:for-each select="exsl:node-set($layoutInfo)[name()='headerFooterOddEvenPages']/*">
                <!-- uses odd/even page layout -->
                <xsl:for-each select="*/*[not(descendant::nothing)]">
                    <!-- for each left, center, right item -->
                    <xsl:call-template name="DoHeaderFooterItem">
                        <xsl:with-param name="item" select="."/>
                        <xsl:with-param name="originalContext" select="$originalContext"/>
                        <xsl:with-param name="sOddEven">
                            <xsl:choose>
                                <xsl:when test="ancestor::headerFooterEvenPage">E</xsl:when>
                                <xsl:otherwise>O</xsl:otherwise>
                            </xsl:choose>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:for-each>
            <xsl:call-template name="SetHeaderFooterRuleWidths">
                <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
            </xsl:call-template>
            <xsl:if test="$sPageStyle='fancypagestyle'">
                <tex:spec cat="eg"/>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        SetListOfWidths
    -->
    <xsl:template name="SetListOfWidths">
        <tex:cmd name="newlength" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPapersingledigitlistofwidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
            <xsl:with-param name="sCommandToSet" select="'XLingPapersingledigitlistofwidth'"/>
            <xsl:with-param name="sValue">
                <xsl:text>8.</xsl:text>
                <xsl:text>&#xa0;</xsl:text>
                <xsl:text>&#xa0;</xsl:text>
            </xsl:with-param>
        </xsl:call-template>
        <tex:cmd name="newlength" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPaperdoubledigitlistofwidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
            <xsl:with-param name="sCommandToSet" select="'XLingPaperdoubledigitlistofwidth'"/>
            <xsl:with-param name="sValue">
                <xsl:text>88.</xsl:text>
                <xsl:text>&#xa0;</xsl:text>
                <xsl:text>&#xa0;</xsl:text>
            </xsl:with-param>
        </xsl:call-template>
        <tex:cmd name="newlength" nl2="1">
            <tex:parm>
                <tex:cmd name="XLingPapertripledigitlistofwidth" gr="0" nl2="0"/>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="SetTeXCommand">
            <xsl:with-param name="sTeXCommand" select="'settowidth'"/>
            <xsl:with-param name="sCommandToSet" select="'XLingPapertripledigitlistofwidth'"/>
            <xsl:with-param name="sValue">
                <xsl:text>888.</xsl:text>
                <xsl:text>&#xa0;</xsl:text>
                <xsl:text>&#xa0;</xsl:text>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--  
        SetMarkPerOddEvenPage
    -->
    <xsl:template name="SetMarkPerOddEvenPage">
        <xsl:param name="bIsChapter" select="'Y'"/>
        <xsl:choose>
            <xsl:when test="$bIsChapter='Y' and $chapterTitleOnEvenPage and $chapterTitleOnOddPage">
                <!-- chapter item is on both pages; use leftmark -->
                <tex:cmd name="leftmark" gr="0"/>
            </xsl:when>
            <xsl:when test="$bHasChapter='Y' and $bIsChapter='N' and $sectionTitleOnEvenPage and $sectionTitleOnOddPage and not($chapterTitleOnEvenPage or $chapterTitleOnOddPage)">
                <!-- has chapters but no chapter item and section item is on both pages; use lefttmark -->
                <tex:cmd name="leftmark" gr="0"/>
            </xsl:when>
            <xsl:when test="$bHasChapter='Y' and $bIsChapter='N' and not($sectionTitleOnEvenPage or $sectionTitleOnOddPage or chapterTitleOnEvenPage or $chapterTitleOnOddPage)">
                <!-- has chapters but no chapter item and section item is on non-odd even page(s); use lefttmark -->
                <tex:cmd name="leftmark" gr="0"/>
            </xsl:when>
            <xsl:when test="$bIsChapter!='Y' and $sectionTitleOnEvenPage and $sectionTitleOnOddPage">
                <!-- section item is on both pages; use rightmark -->
                <tex:cmd name="rightmark" gr="0"/>
            </xsl:when>
            <xsl:when test="ancestor::headerFooterOddPage">
                <tex:cmd name="leftmark" gr="0"/>
            </xsl:when>
            <xsl:otherwise>
                <tex:cmd name="rightmark" gr="0"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        SetPageNumberingForBody
    -->
    <xsl:template name="SetPageNumberingForBody">
        <xsl:variable name="pageNumber" select="exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles/descendant::pageNumber[1]"/>
        <xsl:variable name="sPageNumberFrontMatter" select="normalize-space(exsl:node-set($frontMatterLayoutInfo)/headerFooterPageStyles/descendant::pageNumber[1]/@format)"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($pageNumber)/@format=$sPageNumberFrontMatter and exsl:node-set($pageNumber)/@restartCount!='yes'">
                <!-- nothing to do -->
            </xsl:when>
            <xsl:when test="$pageNumber and $sPageNumberFrontMatter">
                <xsl:if test="exsl:node-set($pageNumber)/@restartCount!='yes'">
                    <!-- save current page number -->
                    <tex:cmd name="newcounter" nl1="0" nl2="0">
                        <tex:parm>XLingPaperpagecount</tex:parm>
                    </tex:cmd>
                    <tex:cmd name="setcounter" nl1="0" nl2="0">
                        <tex:parm>
                            <xsl:text>XLingPaperpagecount</xsl:text>
                        </tex:parm>
                        <tex:parm>
                            <tex:cmd name="thepage" gr="0" nl1="0" nl2="0"/>
                        </tex:parm>
                    </tex:cmd>
                </xsl:if>
                <tex:cmd name="pagenumbering">
                    <tex:parm>
                        <xsl:call-template name="GetPageNumberingFormat">
                            <xsl:with-param name="sPageFormat" select="normalize-space(exsl:node-set($pageNumber)/@format)"/>
                            <xsl:with-param name="sDefault" select="'arabic'"/>
                        </xsl:call-template>
                    </tex:parm>
                </tex:cmd>
                <xsl:if test="exsl:node-set($pageNumber)/@restartCount!='yes'">
                    <!-- reset page number -->
                    <tex:cmd name="setcounter" nl1="0" nl2="0">
                        <tex:parm>
                            <xsl:text>page</xsl:text>
                        </tex:parm>
                        <tex:parm>
                            <tex:cmd name="theXLingPaperpagecount" gr="0" nl1="0" nl2="0"/>
                        </tex:parm>
                    </tex:cmd>
                </xsl:if>
            </xsl:when>
            <xsl:otherwise>
                <tex:cmd name="pagenumbering">
                    <tex:parm>
                        <xsl:call-template name="GetPageNumberingFormat">
                            <xsl:with-param name="sPageFormat" select="normalize-space(exsl:node-set($pageNumber)/@format)"/>
                            <xsl:with-param name="sDefault" select="'arabic'"/>
                        </xsl:call-template>
                    </tex:parm>
                </tex:cmd>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        SetXLingPaperEntrySpaceAuthorOverDateMacro
    -->
    <xsl:template name="SetXLingPaperEntrySpaceAuthorOverDateMacro">
        <!--\newdimen\XLingPaperdatelen
        \newdimen\XLingPaperindentanddate
        \newdimen\XLingPapertemplen-->
        <tex:cmd name="newdimen" gr="0"/>
        <tex:cmd name="XLingPaperdatelen" gr="0" nl2="1"/>
        <tex:cmd name="newdimen" gr="0"/>
        <tex:cmd name="XLingPaperindentanddate" gr="0" nl2="1"/>
        <tex:cmd name="newdimen" gr="0"/>
        <tex:cmd name="XLingPapertemplen" gr="0" nl2="1"/>
        <!--\newcommand{\XLingPaperentryspaceauthoroverdate}[3]{%
        \settowidth{\XLingPaperdatelen}{#2}%
        \setlength{\XLingPaperindentanddate}{#1 + \XLingPaperdatelen}%
        \setlength{\XLingPapertemplen}{#3 - \XLingPaperindentanddate}%-->
        <tex:cmd name="newcommand">
            <tex:parm>
                <tex:cmd name="XLingPaperentryspaceauthoroverdate" gr="0"/>
            </tex:parm>
            <tex:opt>
                <xsl:text>3</xsl:text>
            </tex:opt>
            <tex:parm>
                <tex:spec cat="comment" nl2="1"/>
                <tex:cmd name="settowidth">
                    <tex:parm>
                        <tex:cmd name="XLingPaperdatelen" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <tex:spec cat="parm"/>
                        <xsl:text>2</xsl:text>
                    </tex:parm>
                </tex:cmd>
                <tex:spec cat="comment" nl2="1"/>
                <tex:cmd name="setlength">
                    <tex:parm>
                        <tex:cmd name="XLingPaperindentanddate" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <tex:spec cat="parm"/>
                        <xsl:text>1 + </xsl:text>
                        <tex:cmd name="XLingPaperdatelen" gr="0"/>
                    </tex:parm>
                </tex:cmd>
                <tex:spec cat="comment" nl2="1"/>
                <tex:cmd name="setlength">
                    <tex:parm>
                        <tex:cmd name="XLingPapertemplen" gr="0"/>
                    </tex:parm>
                    <tex:parm>
                        <tex:spec cat="parm"/>
                        <xsl:text>3 - </xsl:text>
                        <tex:cmd name="XLingPaperindentanddate" gr="0"/>
                    </tex:parm>
                </tex:cmd>
                <tex:spec cat="comment" nl2="1"/>
                <!--\ifdim\XLingPapertemplen<0pt%
                        \hspace*{1em}%
                        \else%
                        \hspace*{\XLingPapertemplen}%
                        \fi%
                        }-->
                <tex:cmd name="ifdim" gr="0"/>
                <tex:cmd name="XLingPapertemplen" gr="0"/>
                <tex:spec cat="lt"/>
                <xsl:text>0pt</xsl:text>
                <tex:spec cat="comment" nl2="1"/>
                <tex:cmd name="hspace*">
                    <tex:parm>1em</tex:parm>
                </tex:cmd>
                <tex:spec cat="comment" nl2="1"/>
                <tex:cmd name="else" gr="0"/>
                <tex:spec cat="comment" nl2="1"/>
                <tex:cmd name="hspace*">
                    <tex:parm>
                        <tex:cmd name="XLingPapertemplen" gr="0"/>
                    </tex:parm>
                </tex:cmd>
                <tex:spec cat="comment" nl2="1"/>
                <tex:cmd name="fi" gr="0"/>
            </tex:parm>
        </tex:cmd>
    </xsl:template>
    <!--  
        SetXLingPaperSingelSpacingMacro
    -->
    <xsl:template name="SetXLingPaperSingleSpacingMacro">
        <tex:cmd name="def">
            <tex:cmd name="XLingPapersinglespacing">
                <tex:parm>
                    <tex:cmd name="singlespacing" gr="0"/>
                    <xsl:call-template name="HandleFontSize">
                        <xsl:with-param name="sSize">
                            <xsl:value-of select="$sBasicPointSize"/>
                            <xsl:text>pt</xsl:text>
                        </xsl:with-param>
                    </xsl:call-template>
                </tex:parm>
            </tex:cmd>
        </tex:cmd>
    </xsl:template>
    <!-- ===========================================================
      ELEMENTS TO IGNORE
      =========================================================== -->
    <xsl:template match="language"/>
    <xsl:template match="abstract/shortTitle"/>
    <xsl:template match="acknowledgements/shortTitle"/>
    <xsl:template match="appendix/shortTitle"/>
    <xsl:template match="chapter/shortTitle"/>
    <xsl:template match="contents/shortTitle"/>
    <xsl:template match="glossary/shortTitle"/>
    <xsl:template match="index/shortTitle"/>
    <xsl:template match="keywordsShownHere/shortTitle"/>
    <xsl:template match="part/shortTitle"/>
    <xsl:template match="preface/shortTitle"/>
    <xsl:template match="section1/shortTitle"/>
    <xsl:template match="section2/shortTitle"/>
    <xsl:template match="section3/shortTitle"/>
    <xsl:template match="section4/shortTitle"/>
    <xsl:template match="section5/shortTitle"/>
    <xsl:template match="section6/shortTitle"/>
    <xsl:template match="selectedBibliography/shortTitle"/>
    <xsl:template match="textInfo/shortTitle"/>
    <xsl:template match="styles"/>
    <xsl:template match="style"/>
    <xsl:template match="dd"/>
    <xsl:template match="term"/>
    <xsl:template match="type"/>
    <!-- ===========================================================
        TRANSFORMS TO INCLUDE
        =========================================================== -->
    <xsl:include href="XLingPapPublisherStylesheetXeLaTeXBookmarks.xsl"/>
    <xsl:include href="XLingPapPublisherStylesheetXeLaTeXContents.xsl"/>
    <xsl:include href="XLingPapPublisherStylesheetXeLaTeXReferences.xsl"/>
    <xsl:include href="XLingPapCommon.xsl"/>
    <xsl:include href="XLingPapXeLaTeXCommon.xsl"/>
    <xsl:include href="XLingPapPublisherStylesheetCommon.xsl"/>
</xsl:stylesheet>
