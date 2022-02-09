<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0" xmlns:saxon="http://icl.com/saxon" xmlns:exsl="http://exslt.org/common">
    <!-- global variables -->
    <xsl:variable name="locationPublisherLayouts" select="exsl:node-set($referencesLayoutInfo)/locationPublisherLayouts"/>
    <xsl:variable name="urlDateAccessedLayouts" select="exsl:node-set($referencesLayoutInfo)/urlDateAccessedLayouts"/>
    <xsl:variable name="chapterNumberInHeaderLayout" select="exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles/descendant::chapterNumber"/>
    <xsl:variable name="bChapterNumberIsBeforeTitle">
        <xsl:choose>
            <xsl:when test="exsl:node-set($chapterNumberInHeaderLayout)[following-sibling::chapterTitle]">
                <xsl:text>Y</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>N</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="sectionNumberInHeaderLayout" select="exsl:node-set($bodyLayoutInfo)/headerFooterPageStyles/descendant::sectionNumber | exsl:node-set($pageLayoutInfo)/headerFooterPageStyles/descendant::sectionNumber"/>
    <xsl:variable name="bSectionNumberIsBeforeTitle">
        <xsl:choose>
            <xsl:when test="exsl:node-set($sectionNumberInHeaderLayout)[1][following-sibling::sectionTitle]">
                <xsl:text>Y</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>N</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="sContentBetweenFootnoteNumberAndFootnoteContent" select="exsl:node-set($pageLayoutInfo)/@contentBetweenFootnoteNumberAndFootnoteContent"/>
    <xsl:variable name="citationLayout" select="exsl:node-set($contentLayoutInfo)/citationLayout"/>
    <xsl:variable name="sTextBetweenAuthorAndDate" select="exsl:node-set($citationLayout)/@textbetweenauthoranddate"/>
    <!--    <xsl:variable name="contentsLayout" select="exsl:node-set($frontMatterLayoutInfo)/contentsLayout"/>-->
    <xsl:variable name="contentsLayout">
        <xsl:choose>
            <xsl:when test="exsl:node-set($backMatterLayoutInfo)/contentsLayout">
                <xsl:copy-of select="exsl:node-set($backMatterLayoutInfo)/contentsLayout"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:copy-of select="exsl:node-set($frontMatterLayoutInfo)/contentsLayout"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <!--    <xsl:variable name="sChapterLineIndent" select="normalize-space(saxon:node-set($contentsLayout)/contentsLayout/@chapterlineindent)"/>-->
    <!--    <xsl:variable name="authorInContentsLayoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/authorLayout[preceding-sibling::*[1][name()='contentsLayout']]"/>-->
    <xsl:variable name="authorInContentsLayoutInfo">
        <xsl:choose>
            <xsl:when test="exsl:node-set($backMatterLayoutInfo)/authorLayout[preceding-sibling::*[1][name()='contentsLayout']]">
                <xsl:copy-of select="exsl:node-set($backMatterLayoutInfo)/authorLayout[preceding-sibling::*[1][name()='contentsLayout']]"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:copy-of select="exsl:node-set($frontMatterLayoutInfo)/authorLayout[preceding-sibling::*[1][name()='contentsLayout']]"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="annotationLayoutInfo" select="exsl:node-set($contentLayoutInfo)/annotationLayout"/>
    <xsl:variable name="nLevel">
        <xsl:choose>
            <xsl:when test="exsl:node-set($contents)/@showLevel">
                <xsl:value-of select="number(exsl:node-set($contents)/@showLevel)"/>
            </xsl:when>
            <xsl:otherwise>3</xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="nBackMatterLevel">
        <xsl:choose>
            <xsl:when test="exsl:node-set($contents)/@backmattershowLevel">
                <xsl:value-of select="number(exsl:node-set($contents)/@backmattershowLevel)"/>
            </xsl:when>
            <xsl:otherwise>3</xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="sEtAl" select="'et al.'"/>
    <xsl:variable name="sEtAlSpaces" select="' et al. '"/>
    <xsl:variable name="sSpaceBetweenDates" select="normalize-space(exsl:node-set($referencesLayoutInfo)/@spaceBetweenEntriesAuthorOverDateStyle)"/>
    <xsl:variable name="sSpaceBetweenEntryAndAuthor" select="normalize-space(exsl:node-set($referencesLayoutInfo)/@spaceBetweenEntryAndAuthorInAuthorOverDateStyle)"/>
    <xsl:variable name="sSpaceForDateInAuthorOverDateStyle">
        <xsl:choose>
            <xsl:when test="string-length(normalize-space(exsl:node-set($referencesLayoutInfo)/@dateToEntrySpaceAuthorOverDateStyle)) &gt; 0">
                <xsl:value-of select="normalize-space(exsl:node-set($referencesLayoutInfo)/@dateToEntrySpaceAuthorOverDateStyle)"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>2.5em</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <!-- ===========================================================
        NUMBERING PROCESSING 
        =========================================================== -->
    <!--  
        section
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
        <xsl:choose>
            <xsl:when test="exsl:node-set($bodyLayoutInfo)/section1Layout/@startSection1NumberingAtZero='yes'">
                <xsl:variable name="numAt1">
                    <xsl:number level="multiple" count="section1 | section2 | section3 | section4 | section5 | section6" format="1.1"/>
                </xsl:variable>
                <!--  adjust section1 number down by one to start with 0 -->
                <xsl:variable name="num1" select="substring-before($numAt1,'.')"/>
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
            </xsl:when>
            <xsl:when test="count($chapters)=0 and count(//section1)=1 and count(//section1/section2)=0">
                <!-- if there are no chapters and there is but one section1 (with no subsections), there's no need to have a number so don't  -->
            </xsl:when>
            <xsl:otherwise>
                <xsl:number level="multiple" count="section1 | section2 | section3 | section4 | section5 | section6" format="1.1"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        endnote
    -->
    <xsl:template mode="endnote" match="endnote[parent::author]">
        <xsl:variable name="iAuthorPosition" select="count(ancestor::author/preceding-sibling::author[endnote]) + 1"/>
        <xsl:call-template name="OutputAuthorFootnoteSymbol">
            <xsl:with-param name="iAuthorPosition" select="$iAuthorPosition"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        figure
    -->
    <xsl:template mode="figure" match="*" priority="10">
        <xsl:choose>
            <xsl:when test="$bIsBook and exsl:node-set($styleSheetFigureNumberLayout)/@showchapternumber='yes'">
                <xsl:for-each select="ancestor::chapter | ancestor::appendix | ancestor::chapterBeforePart | ancestor::chapterInCollection">
                    <xsl:call-template name="OutputChapterNumber">
                        <xsl:with-param name="fIgnoreTextAfterLetter" select="'Y'"/>
                        <!-- while this is not technically in the contents, we still want just the number to show, not also any textafter the number -->
                        <xsl:with-param name="fDoingContents" select="'Y'"/>
                    </xsl:call-template>
                </xsl:for-each>
                <xsl:value-of select="exsl:node-set($styleSheetFigureNumberLayout)/@textbetweenchapterandnumber"/>
                <xsl:number level="any" count="figure[not(ancestor::endnote or ancestor::framedUnit)]" from="chapter | appendix | chapterBeforePart | chapterInCollection"
                    format="{exsl:node-set($styleSheetFigureNumberLayout)/@format}"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:number level="any" count="figure[not(ancestor::endnote or ancestor::framedUnit)]" format="{exsl:node-set($styleSheetFigureNumberLayout)/@format}"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        tablenumbered
    -->
    <xsl:template mode="tablenumbered" match="*" priority="10">
        <xsl:choose>
            <xsl:when test="$bIsBook and exsl:node-set($styleSheetTableNumberedNumberLayout)/@showchapternumber='yes'">
                <xsl:for-each select="ancestor::chapter | ancestor::appendix | ancestor::chapterBeforePart | ancestor::chapterInCollection">
                    <xsl:call-template name="OutputChapterNumber">
                        <xsl:with-param name="fIgnoreTextAfterLetter" select="'Y'"/>
                        <!-- while this is not technically in the contents, we still want just the number to show, not also any textafter the number -->
                        <xsl:with-param name="fDoingContents" select="'Y'"/>
                    </xsl:call-template>
                </xsl:for-each>
                <xsl:value-of select="exsl:node-set($styleSheetTableNumberedNumberLayout)/@textbetweenchapterandnumber"/>
                <xsl:number level="any" count="tablenumbered[not(ancestor::endnote or ancestor::framedUnit)]" from="chapter | appendix | chapterBeforePart | chapterInCollection"
                    format="{exsl:node-set($styleSheetTableNumberedNumberLayout)/@format}"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:number level="any" count="tablenumbered[not(ancestor::endnote or ancestor::framedUnit)]" format="{exsl:node-set($styleSheetTableNumberedNumberLayout)/@format}"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        letter
    -->
    <xsl:template mode="letter" match="*">
        <xsl:number level="single" count="listWord | listSingle | listInterlinear | listDefinition | lineSet" format="a"/>
    </xsl:template>
    <!--  
        dateLetter
    -->
    <xsl:template match="*" mode="dateLetter">
        <xsl:param name="date"/>
        <xsl:number level="single" count="refWork[@id=//citation/@ref][refDate=$date or refDate/@citedate=$date]" format="a"/>
    </xsl:template>
    <!--
        authorRole
    -->
    <xsl:template match="authorRole">
        <xsl:value-of select="normalize-space(.)"/>
    </xsl:template>
    <!--
        book
    -->
    <xsl:template match="book">
        <xsl:call-template name="DoBookLayout"/>
        <xsl:apply-templates select="comment"/>
    </xsl:template>
    <!--
        collCitation
    -->
    <xsl:template match="collCitation">
        <xsl:param name="layout"/>
        <xsl:call-template name="DoCitation">
            <xsl:with-param name="layout" select="$layout"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        collection
    -->
    <xsl:template match="collection">
        <xsl:call-template name="DoCollectionLayout"/>
        <xsl:apply-templates select="comment"/>
    </xsl:template>
    <!--
        dissertation
    -->
    <xsl:template match="dissertation">
        <xsl:call-template name="DoDissertationLayout">
            <xsl:with-param name="layout" select="exsl:node-set($referencesLayoutInfo)/dissertationLayouts"/>
        </xsl:call-template>
        <xsl:apply-templates select="comment"/>
    </xsl:template>
    <!--
        article
    -->
    <xsl:template match="article">
        <xsl:call-template name="DoArticleLayout"/>
        <xsl:apply-templates select="comment"/>
    </xsl:template>
    <!--
        field notes
    -->
    <xsl:template match="fieldNotes">
        <xsl:call-template name="DoFieldNotesLayout"/>
        <xsl:apply-templates select="comment"/>
    </xsl:template>
    <!--
        glossary
    -->
    <xsl:template match="glossary">
        <xsl:param name="backMatterLayout" select="$backMatterLayoutInfo"/>
        <xsl:param name="iLayoutPosition" select="0"/>
        <xsl:variable name="iPos" select="count(preceding-sibling::glossary) + 1"/>
        <xsl:variable name="glossaryLayout" select="exsl:node-set($backMatterLayout)/glossaryLayout"/>
        <xsl:variable name="fLayoutIsLastOfMany">
            <xsl:choose>
                <xsl:when test="$iLayoutPosition=0">
                    <xsl:text>N</xsl:text>
                </xsl:when>
                <xsl:when test="count(exsl:node-set($glossaryLayout)[number($iLayoutPosition)]/following-sibling::glossaryLayout)=0">
                    <xsl:text>Y</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>N</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$iLayoutPosition = 0">
                <!-- there's one and only one glossaryLayout; use it -->
                <xsl:call-template name="DoGlossaryPerLayout">
                    <xsl:with-param name="iPos" select="$iPos"/>
                    <xsl:with-param name="glossaryLayout" select="$glossaryLayout"/>
                    <xsl:with-param name="iLayoutPosition" select="$iLayoutPosition"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$iLayoutPosition = $iPos">
                <!-- there are many glossaryLayouts; use the one that matches in position -->
                <xsl:call-template name="DoGlossaryPerLayout">
                    <xsl:with-param name="iPos" select="$iPos"/>
                    <xsl:with-param name="glossaryLayout" select="exsl:node-set($glossaryLayout)[number($iLayoutPosition)]"/>
                    <xsl:with-param name="iLayoutPosition" select="$iLayoutPosition"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$fLayoutIsLastOfMany='Y' and $iPos &gt; $iLayoutPosition">
                <!-- there are many glossaryLayouts and there are more glossary elements than glossaryLayout elements; use the last layout -->
                <xsl:call-template name="DoGlossaryPerLayout">
                    <xsl:with-param name="iPos" select="$iPos"/>
                    <xsl:with-param name="glossaryLayout" select="exsl:node-set($glossaryLayout)[number(last())]"/>
                    <xsl:with-param name="iLayoutPosition" select="$iLayoutPosition"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--
        ms
    -->
    <xsl:template match="ms">
        <xsl:call-template name="DoMsLayout"/>
        <xsl:apply-templates select="comment"/>
    </xsl:template>
    <!--
        paper
    -->
    <xsl:template match="paper">
        <xsl:call-template name="DoPaperLayout"/>
        <xsl:apply-templates select="comment"/>
    </xsl:template>
    <!--
        abstract (book)
    -->
    <xsl:template match="abstract" mode="book">
        <xsl:param name="iLayoutPosition" select="0"/>
        <xsl:variable name="iPos" select="count(preceding-sibling::abstract) + 1"/>
        <xsl:variable name="fLayoutIsLastOfMany">
            <xsl:choose>
                <xsl:when test="$iLayoutPosition=0">
                    <xsl:text>N</xsl:text>
                </xsl:when>
                <xsl:when test="count(exsl:node-set($frontMatterLayoutInfo)/abstractLayout[number($iLayoutPosition)]/following-sibling::abstractLayout)=0">
                    <xsl:text>Y</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>N</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$iLayoutPosition = 0">
                <!-- there's one and only one abstractLayout; use it -->
                <xsl:call-template name="DoAbstractPerBookLayout">
                    <xsl:with-param name="iPos" select="$iPos"/>
                    <xsl:with-param name="abstractLayout" select="exsl:node-set($frontMatterLayoutInfo)/abstractLayout"/>
                    <xsl:with-param name="iLayoutPosition" select="$iLayoutPosition"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$iLayoutPosition = $iPos">
                <!-- there are many abstractLayouts; use the one that matches in position -->
                <xsl:call-template name="DoAbstractPerBookLayout">
                    <xsl:with-param name="iPos" select="$iPos"/>
                    <xsl:with-param name="abstractLayout" select="exsl:node-set($frontMatterLayoutInfo)/abstractLayout[number($iLayoutPosition)]"/>
                    <xsl:with-param name="iLayoutPosition" select="$iLayoutPosition"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$fLayoutIsLastOfMany='Y' and $iPos &gt; $iLayoutPosition">
                <!-- there are many abstractLayouts and there are more abstract elements than abstractLayout elements; use the last layout -->
                <xsl:call-template name="DoAbstractPerBookLayout">
                    <xsl:with-param name="iPos" select="$iPos"/>
                    <xsl:with-param name="abstractLayout" select="exsl:node-set($frontMatterLayoutInfo)/abstractLayout[number(last())]"/>
                    <xsl:with-param name="iLayoutPosition" select="$iLayoutPosition"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--
        abstract (paper)
    -->
    <xsl:template match="abstract" mode="paper">
        <xsl:param name="frontMatterLayout" select="$frontMatterLayoutInfo"/>
        <xsl:param name="iLayoutPosition" select="0"/>
        <xsl:variable name="iPos" select="count(preceding-sibling::abstract) + 1"/>
        <xsl:variable name="fLayoutIsLastOfMany">
            <xsl:choose>
                <xsl:when test="$iLayoutPosition=0">
                    <xsl:text>N</xsl:text>
                </xsl:when>
                <xsl:when test="count(exsl:node-set($frontMatterLayout)/abstractLayout[number($iLayoutPosition)]/following-sibling::abstractLayout)=0">
                    <xsl:text>Y</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>N</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$iLayoutPosition = 0">
                <!-- there's one and only one abstractLayout; use it -->
                <xsl:call-template name="DoAbstractPerPaperLayout">
                    <xsl:with-param name="iPos" select="$iPos"/>
                    <xsl:with-param name="abstractLayout" select="exsl:node-set($frontMatterLayout)/abstractLayout[1]"/>
                    <xsl:with-param name="iLayoutPosition" select="$iLayoutPosition"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$iLayoutPosition = $iPos">
                <!-- there are many abstractLayouts; use the one that matches in position -->
                <xsl:call-template name="DoAbstractPerPaperLayout">
                    <xsl:with-param name="iPos" select="$iPos"/>
                    <xsl:with-param name="abstractLayout" select="exsl:node-set($frontMatterLayout)/abstractLayout[number($iLayoutPosition)]"/>
                    <xsl:with-param name="iLayoutPosition" select="$iLayoutPosition"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$fLayoutIsLastOfMany='Y' and $iPos &gt; $iLayoutPosition">
                <!-- there are many abstractLayouts and there are more abstract elements than abstractLayout elements; use the last layout -->
                <xsl:call-template name="DoAbstractPerPaperLayout">
                    <xsl:with-param name="iPos" select="$iPos"/>
                    <xsl:with-param name="abstractLayout" select="exsl:node-set($frontMatterLayout)/abstractLayout[number(last())]"/>
                    <xsl:with-param name="iLayoutPosition" select="$iLayoutPosition"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--
        preface (book)
    -->
    <xsl:template match="preface" mode="book">
        <xsl:param name="iLayoutPosition" select="0"/>
        <xsl:variable name="iPos" select="count(preceding-sibling::preface) + 1"/>
        <xsl:variable name="fLayoutIsLastOfMany">
            <xsl:choose>
                <xsl:when test="$iLayoutPosition=0">
                    <xsl:text>N</xsl:text>
                </xsl:when>
                <xsl:when test="count(exsl:node-set($frontMatterLayoutInfo)/prefaceLayout[number($iLayoutPosition)]/following-sibling::prefaceLayout)=0">
                    <xsl:text>Y</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>N</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$iLayoutPosition = 0">
                <!-- there's one and only one prefaceLayout; use it -->
                <xsl:call-template name="DoPrefacePerBookLayout">
                    <xsl:with-param name="iPos" select="$iPos"/>
                    <xsl:with-param name="prefaceLayout" select="exsl:node-set($frontMatterLayoutInfo)/prefaceLayout"/>
                    <xsl:with-param name="iLayoutPosition" select="$iLayoutPosition"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$iLayoutPosition = $iPos">
                <!-- there are many prefaceLayouts; use the one that matches in position -->
                <xsl:call-template name="DoPrefacePerBookLayout">
                    <xsl:with-param name="iPos" select="$iPos"/>
                    <xsl:with-param name="prefaceLayout" select="exsl:node-set($frontMatterLayoutInfo)/prefaceLayout[number($iLayoutPosition)]"/>
                    <xsl:with-param name="iLayoutPosition" select="$iLayoutPosition"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$fLayoutIsLastOfMany='Y' and $iPos &gt; $iLayoutPosition">
                <!-- there are many prefaceLayouts and there are more preface elements than prefaceLayout elements; use the last layout -->
                <xsl:call-template name="DoPrefacePerBookLayout">
                    <xsl:with-param name="iPos" select="$iPos"/>
                    <xsl:with-param name="prefaceLayout" select="exsl:node-set($frontMatterLayoutInfo)/prefaceLayout[number(last())]"/>
                    <xsl:with-param name="iLayoutPosition" select="$iLayoutPosition"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--
        preface (paper)
    -->
    <xsl:template match="preface" mode="paper">
        <xsl:param name="iLayoutPosition" select="0"/>
        <xsl:variable name="iPos" select="count(preceding-sibling::preface) + 1"/>
        <xsl:variable name="fLayoutIsLastOfMany">
            <xsl:choose>
                <xsl:when test="$iLayoutPosition=0">
                    <xsl:text>N</xsl:text>
                </xsl:when>
                <xsl:when test="count(exsl:node-set($frontMatterLayoutInfo)/prefaceLayout[number($iLayoutPosition)]/following-sibling::prefaceLayout)=0">
                    <xsl:text>Y</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>N</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$iLayoutPosition = 0">
                <!-- there's one and only one prefaceLayout; use it -->
                <xsl:call-template name="DoPrefacePerPaperLayout">
                    <xsl:with-param name="iPos" select="$iPos"/>
                    <xsl:with-param name="prefaceLayout" select="exsl:node-set($frontMatterLayoutInfo)/prefaceLayout"/>
                    <xsl:with-param name="iLayoutPosition" select="$iLayoutPosition"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$iLayoutPosition = $iPos">
                <!-- there are many prefaceLayouts; use the one that matches in position -->
                <xsl:call-template name="DoPrefacePerPaperLayout">
                    <xsl:with-param name="iPos" select="$iPos"/>
                    <xsl:with-param name="prefaceLayout" select="exsl:node-set($frontMatterLayoutInfo)/prefaceLayout[number($iLayoutPosition)]"/>
                    <xsl:with-param name="iLayoutPosition" select="$iLayoutPosition"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$fLayoutIsLastOfMany='Y' and $iPos &gt; $iLayoutPosition">
                <!-- there are many prefaceLayouts and there are more preface elements than prefaceLayout elements; use the last layout -->
                <xsl:call-template name="DoPrefacePerPaperLayout">
                    <xsl:with-param name="iPos" select="$iPos"/>
                    <xsl:with-param name="prefaceLayout" select="exsl:node-set($frontMatterLayoutInfo)/prefaceLayout[number(last())]"/>
                    <xsl:with-param name="iLayoutPosition" select="$iLayoutPosition"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--
        procCitation
    -->
    <xsl:template match="procCitation">
        <xsl:param name="layout"/>
        <xsl:call-template name="DoCitation">
            <xsl:with-param name="layout" select="$layout"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        proceedings
    -->
    <xsl:template match="proceedings">
        <xsl:call-template name="DoProceedingsLayout"/>
        <xsl:apply-templates select="comment"/>
    </xsl:template>
    <!--
        thesis
    -->
    <xsl:template match="thesis">
        <xsl:call-template name="DoDissertationLayout">
            <xsl:with-param name="layout" select="exsl:node-set($referencesLayoutInfo)/thesisLayouts"/>
        </xsl:call-template>
        <xsl:apply-templates select="comment"/>
    </xsl:template>
    <!--
        doi
    -->
    <xsl:template match="doi">
        <xsl:call-template name="DoDoiLayout"/>
    </xsl:template>
    <!--
        iso639-3code
    -->
    <xsl:template match="iso639code">
        <xsl:value-of select="normalize-space(.)"/>
    </xsl:template>
    <!--
        url
    -->
    <xsl:template match="url">
        <xsl:call-template name="DoUrlLayout"/>
    </xsl:template>
    <!--
        webPage
    -->
    <xsl:template match="webPage">
        <xsl:call-template name="DoWebPageLayout"/>
        <xsl:apply-templates select="comment"/>
    </xsl:template>
    <!--
        refAuthor
    -->
    <xsl:template match="refAuthor">
        <xsl:choose>
            <xsl:when test="$authorForm='full' or not(refAuthorInitials)">
                <xsl:choose>
                    <xsl:when test="exsl:node-set($referencesLayoutInfo)/refAuthorLayouts/refAuthorLastNameLayout and string-length(refAuthorName) &gt;0">
                        <xsl:apply-templates select="refAuthorName"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="DoAuthorNameChange">
                            <xsl:with-param name="sName" select="@name"/>
                            <xsl:with-param name="fNormalizeSpace" select="'Y'"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="refAuthorInitials"/>
                <!--                <xsl:value-of select="normalize-space(refAuthorInitials)"/>-->
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        refDate
    -->
    <xsl:template match="refDate">
        <xsl:param name="works"/>
        <xsl:param name="sortedWorks"/>
        <xsl:variable name="date" select="."/>
        <xsl:call-template name="OutputRefDateValue">
            <xsl:with-param name="date" select="$date"/>
            <xsl:with-param name="sortedWorks" select="$sortedWorks"/>
            <xsl:with-param name="works" select="$works"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        refTitle
    -->
    <xsl:template match="refTitle">
        <xsl:variable name="sTitle" select="normalize-space(.)"/>
        <xsl:if test="string-length($sTitle) &gt; 0">
            <xsl:choose>
                <xsl:when test="$titleForm='uppercase' or not(following-sibling::refTitleLowerCase)">
                    <xsl:apply-templates/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates select="following-sibling::refTitleLowerCase"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--
        Elements to ignore
    -->
    <xsl:template match="literalLabelLayout"/>
    <xsl:template match="refAuthorNameChange"/>
    <!--  
        AdjustPageNumbers
    -->
    <xsl:template name="AdjustPageNumbers">
        <xsl:param name="normalizedPages"/>
        <xsl:param name="sSeparator" select="'-'"/>
        <xsl:variable name="startPage" select="substring-before($normalizedPages,$sSeparator)"/>
        <xsl:variable name="endPage" select="substring-after($normalizedPages,$sSeparator)"/>
        <xsl:choose>
            <xsl:when test="string-length($startPage) = 3 and string-length($endPage) = 3 and substring($startPage,1,1)=substring($endPage,1,1)">
                <xsl:value-of select="$startPage"/>
                <xsl:value-of select="$sSeparator"/>
                <xsl:value-of select="substring($endPage,2)"/>
            </xsl:when>
            <xsl:when test="string-length($startPage) = 4 and string-length($endPage) = 4 and substring($startPage,1,2)=substring($endPage,1,2)">
                <xsl:value-of select="$startPage"/>
                <xsl:value-of select="$sSeparator"/>
                <xsl:value-of select="substring($endPage,3)"/>
            </xsl:when>
            <xsl:when test="string-length($startPage) = 5 and string-length($endPage) = 5 and substring($startPage,1,3)=substring($endPage,1,3)">
                <xsl:value-of select="$startPage"/>
                <xsl:value-of select="$sSeparator"/>
                <xsl:value-of select="substring($endPage,4)"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$normalizedPages"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DetermineIfDateAccessedMatchesLayoutPattern
    -->
    <xsl:template name="DetermineIfDateAccessedMatchesLayoutPattern">
        <xsl:param name="sOptionsPresent"/>
        <xsl:param name="dateAccessedPos"/>
        <xsl:choose>
            <xsl:when test="substring($sOptionsPresent, $dateAccessedPos, 1)='y' and dateAccessedItem">x</xsl:when>
            <xsl:when test="substring($sOptionsPresent, $dateAccessedPos, 1)='y' and urlDateAccessedLayoutsRef and exsl:node-set($urlDateAccessedLayouts)/urlDateAccessedLayout/dateAccessedItem">x</xsl:when>
            <xsl:when test="substring($sOptionsPresent, $dateAccessedPos, 1)='n' and not(dateAccessedItem)">
                <xsl:choose>
                    <xsl:when test="not(urlDateAccessedLayoutsRef)">x</xsl:when>
                    <xsl:when test="urlDateAccessedLayoutsRef and exsl:node-set($urlDateAccessedLayouts)/urlDateAccessedLayout/missingItem">x</xsl:when>
                </xsl:choose>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  
        DetermineIfDoiMatchesLayoutPattern
    -->
    <xsl:template name="DetermineIfDoiMatchesLayoutPattern">
        <xsl:param name="sOptionsPresent"/>
        <xsl:param name="doiPos"/>
        <xsl:choose>
            <xsl:when test="substring($sOptionsPresent, $doiPos, 1)='y' and doiItem">x</xsl:when>
            <xsl:when test="substring($sOptionsPresent, $doiPos, 1)='y' and urlDateAccessedLayoutsRef and exsl:node-set($urlDateAccessedLayouts)/urlDateAccessedLayout/doiItem">x</xsl:when>
            <xsl:when test="substring($sOptionsPresent, $doiPos, 1)='n' and not(doiItem)">
                <xsl:choose>
                    <xsl:when test="not(urlDateAccessedLayoutsRef)">x</xsl:when>
                    <xsl:when test="urlDateAccessedLayoutsRef and exsl:node-set($urlDateAccessedLayouts)/urlDateAccessedLayout/missingItem">x</xsl:when>
                </xsl:choose>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  
        DetermineIfLocationPublisherMatchesLayoutPattern
    -->
    <xsl:template name="DetermineIfLocationPublisherMatchesLayoutPattern">
        <xsl:param name="sOptionsPresent"/>
        <xsl:param name="locationPublisherPos"/>
        <xsl:choose>
            <xsl:when test="substring($sOptionsPresent, $locationPublisherPos, 1)='y' and locationPublisherLayoutsRef">x</xsl:when>
            <xsl:when test="substring($sOptionsPresent, $locationPublisherPos, 1)='n' and not(locationPublisherLayoutsRef)">x</xsl:when>
            <xsl:when test="substring($sOptionsPresent, $locationPublisherPos, 1)='n' and exsl:node-set($locationPublisherLayouts)/locationPublisherLayout/missingItem">x</xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  
        DetermineIfUrlMatchesLayoutPattern
    -->
    <xsl:template name="DetermineIfUrlMatchesLayoutPattern">
        <xsl:param name="sOptionsPresent"/>
        <xsl:param name="urlPos"/>
        <xsl:choose>
            <xsl:when test="substring($sOptionsPresent, $urlPos, 1)='y' and urlItem">x</xsl:when>
            <xsl:when test="substring($sOptionsPresent, $urlPos, 1)='y' and urlDateAccessedLayoutsRef and exsl:node-set($urlDateAccessedLayouts)/urlDateAccessedLayout/urlItem">x</xsl:when>
            <xsl:when test="substring($sOptionsPresent, $urlPos, 1)='n' and not(urlItem)">
                <xsl:choose>
                    <xsl:when test="not(urlDateAccessedLayoutsRef)">x</xsl:when>
                    <xsl:when test="urlDateAccessedLayoutsRef and exsl:node-set($urlDateAccessedLayouts)/urlDateAccessedLayout/missingItem">x</xsl:when>
                </xsl:choose>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--
        DoAppendixRef
    -->
    <xsl:template name="DoAppendixRef">
        <xsl:variable name="appendix" select="id(@app)"/>
        <xsl:choose>
            <xsl:when test="@showTitle='short'">
                <xsl:call-template name="DoFormatLayoutInfoTextBefore">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($contentLayoutInfo)/sectionRefTitleLayout"/>
                </xsl:call-template>
                <xsl:choose>
                    <xsl:when test="exsl:node-set($appendix)/shortTitle and string-length(exsl:node-set($appendix)/shortTitle) &gt; 0">
                        <xsl:apply-templates select="exsl:node-set($appendix)/shortTitle/child::node()[name()!='endnote']"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:apply-templates select="exsl:node-set($appendix)/secTitle/child::node()[name()!='endnote']"/>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($contentLayoutInfo)/sectionRefTitleLayout"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="@showTitle='full'">
                <xsl:call-template name="DoFormatLayoutInfoTextBefore">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($contentLayoutInfo)/sectionRefTitleLayout"/>
                </xsl:call-template>
                <xsl:apply-templates select="exsl:node-set($appendix)/secTitle/child::node()[name()!='endnote']"/>
                <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($contentLayoutInfo)/sectionRefTitleLayout"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="$appendix" mode="numberAppendix"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoArticleLayout
    -->
    <xsl:template name="DoArticleLayout">
        <xsl:variable name="article" select="."/>
        <xsl:variable name="work" select=".."/>
        <xsl:variable name="articleLayoutToUsePosition">
            <xsl:call-template name="GetArticleLayoutToUsePosition"/>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$articleLayoutToUsePosition=0 or string-length($articleLayoutToUsePosition)=0">
                <xsl:call-template name="ReportNoPatternMatched"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/articleLayouts/*[position()=$articleLayoutToUsePosition]">
                    <xsl:for-each select="*">
                        <xsl:choose>
                            <xsl:when test="name(.)='refTitleItem' and string-length(exsl:node-set($work)/refTitle) &gt; 0">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($work)/refTitle"/>
                                </xsl:call-template>
                                <xsl:if test="exsl:node-set($work)/../@showAuthorName='no'">
                                    <xsl:call-template name="DoDateLayout">
                                        <xsl:with-param name="refDateItem" select="ancestor::referencesLayout/refAuthorLayouts/refAuthorLayout[position()=last()]/refDateItem"/>
                                        <xsl:with-param name="work" select="$work"/>
                                    </xsl:call-template>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='jTitleItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($article)/jTitle"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='jVolItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="normalize-space(exsl:node-set($article)/jVol)"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='jIssueNumberItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="normalize-space(exsl:node-set($article)/jIssueNumber)"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='jPagesItem'">
                                <xsl:variable name="normalizedPages" select="normalize-space(exsl:node-set($article)/jPages)"/>
                                <xsl:variable name="pages">
                                    <xsl:call-template name="GetFormattedPageNumbers">
                                        <xsl:with-param name="normalizedPages" select="$normalizedPages"/>
                                    </xsl:call-template>
                                </xsl:variable>
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="$pages"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='jArticleNumberItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="normalize-space(exsl:node-set($article)/jArticleNumber)"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='reprintInfoItem'">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($article)/reprintInfo"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem' and name(following-sibling::*[2])='doiItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$article"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[2])='urlItem' and name(preceding-sibling::*[1])='dateAccessedItem' and name(.)='doi'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$article"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[1])='urlItem' and name(.)='dateAccessedItem'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem'">
                                <xsl:call-template name="HandleUrlLayout">
                                    <xsl:with-param name="kindOfWork" select="$article"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='dateAccessedItem'">
                                <xsl:call-template name="HandleDateAccessedLayout">
                                    <xsl:with-param name="kindOfWork" select="$article"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='doiItem'">
                                <xsl:call-template name="HandleDoiLayout">
                                    <xsl:with-param name="kindOfWork" select="$article"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='locationPublisherLayoutsRef'">
                                <xsl:call-template name="DoLocationPublisherLayout">
                                    <xsl:with-param name="reference" select="$article"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlDateAccessedLayoutsRef'">
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="$article"/>
                                </xsl:call-template>
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="exsl:node-set($article)/.."/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='iso639-3codeItemRef'">
                                <xsl:call-template name="DoISO639-3Codes">
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoAuthorContactInfoPerLayout
    -->
    <xsl:template name="DoAuthorContactInfoPerLayout">
        <xsl:param name="layoutInfo"/>
        <xsl:param name="authorInfo"/>
        <xsl:for-each select="exsl:node-set($layoutInfo)/*">
            <xsl:variable name="currentLayoutInfo" select="."/>
            <xsl:choose>
                <xsl:when test="name()='contactNameLayout'">
                    <xsl:for-each select="exsl:node-set($authorInfo)/contactName">
                        <xsl:call-template name="DoContactInfo">
                            <xsl:with-param name="currentLayoutInfo" select="$currentLayoutInfo"/>
                        </xsl:call-template>
                    </xsl:for-each>
                </xsl:when>
                <xsl:when test="name()='contactAddressLayout'">
                    <xsl:for-each select="exsl:node-set($authorInfo)/contactAddress">
                        <xsl:call-template name="DoContactInfo">
                            <xsl:with-param name="currentLayoutInfo" select="$currentLayoutInfo"/>
                        </xsl:call-template>
                    </xsl:for-each>
                </xsl:when>
                <xsl:when test="name()='contactAffiliationLayout'">
                    <xsl:for-each select="exsl:node-set($authorInfo)/contactAffiliation">
                        <xsl:call-template name="DoContactInfo">
                            <xsl:with-param name="currentLayoutInfo" select="$currentLayoutInfo"/>
                        </xsl:call-template>
                    </xsl:for-each>
                </xsl:when>
                <xsl:when test="name()='contactEmailLayout'">
                    <xsl:for-each select="exsl:node-set($authorInfo)/contactEmail">
                        <xsl:call-template name="DoContactInfo">
                            <xsl:with-param name="currentLayoutInfo" select="$currentLayoutInfo"/>
                        </xsl:call-template>
                    </xsl:for-each>
                </xsl:when>
                <xsl:when test="name()='contactElectronicLayout'">
                    <xsl:for-each select="exsl:node-set($authorInfo)/contactElectronic[@show='yes']">
                        <xsl:call-template name="DoContactInfo">
                            <xsl:with-param name="currentLayoutInfo" select="$currentLayoutInfo"/>
                        </xsl:call-template>
                    </xsl:for-each>
                </xsl:when>
                <xsl:when test="name()='contactPhoneLayout'">
                    <xsl:for-each select="exsl:node-set($authorInfo)/contactPhone">
                        <xsl:call-template name="DoContactInfo">
                            <xsl:with-param name="currentLayoutInfo" select="$currentLayoutInfo"/>
                        </xsl:call-template>
                    </xsl:for-each>
                </xsl:when>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>
    <!--  
        DoAuthorNameChange
    -->
    <xsl:template name="DoAuthorNameChange">
        <xsl:param name="sName"/>
        <xsl:param name="fNormalizeSpace" select="'N'"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($referencesLayoutInfo)/refAuthorNameChange and contains($sName,exsl:node-set($referencesLayoutInfo)/refAuthorNameChange/@from)">
                <xsl:variable name="sNameChange">
                    <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/refAuthorNameChange">
                        <xsl:value-of select="substring-before($sName,@from)"/>
                        <xsl:value-of select="@to"/>
                        <xsl:value-of select="substring-after($sName,@from)"/>
                    </xsl:for-each>
                </xsl:variable>
                <xsl:value-of select="$sNameChange"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="$fNormalizeSpace='Y'">
                        <xsl:value-of select="normalize-space($sName)"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$sName"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoAuthorRelatedElementsPerSingleSetOfLayouts
    -->
    <xsl:template name="DoAuthorRelatedElementsPerSingleSetOfLayouts">
        <xsl:param name="authors"/>
        <xsl:param name="currentAuthors"/>
        <xsl:param name="thisAffiliationLayout" select="following-sibling::affiliationLayout"/>
        <xsl:param name="thisEmailAddressLayout" select="following-sibling::emailAddressLayout"/>
        <xsl:variable name="thisAuthorLayout" select="."/>
        <xsl:for-each select="$authors">
            <xsl:variable name="thisAuthor" select="."/>
            <xsl:if test="exsl:node-set($currentAuthors)[.=$thisAuthor]">
                <!-- format the author -->
                <!--            <xsl:for-each select="$thisAuthorLayout">-->
                <xsl:apply-templates select="$thisAuthor">
                    <xsl:with-param name="authorLayoutToUse" select="$thisAuthorLayout"/>
                </xsl:apply-templates>
                <!--            </xsl:for-each>-->
                <!-- figure out how to format any affiliations or emailAddress of this author -->
                <xsl:variable name="iThisAuthorPos" select="position()"/>
                <xsl:variable name="myAffiliations" select="following-sibling::*[name()='affiliation' and count(preceding-sibling::author) = $iThisAuthorPos]"/>
                <xsl:variable name="myEmailAddress" select="following-sibling::*[name()='emailAddress' and count(preceding-sibling::author) = $iThisAuthorPos]"/>
                <xsl:choose>
                    <xsl:when test="exsl:node-set($thisAuthorLayout)/following-sibling::*[1][name()='affiliationLayout']">
                        <!-- format any affiliations first -->
                        <!--                        <xsl:for-each select="$thisAffiliationLayout">-->
                        <xsl:apply-templates select="$myAffiliations">
                            <xsl:with-param name="affiliationLayoutToUse" select="$thisAffiliationLayout"/>
                        </xsl:apply-templates>
                        <!--                        </xsl:for-each>-->
                        <!--                        <xsl:for-each select="$thisEmailAddressLayout">-->
                        <xsl:apply-templates select="$myEmailAddress">
                            <xsl:with-param name="emailAddressLayoutToUse" select="$thisEmailAddressLayout"/>
                        </xsl:apply-templates>
                        <!--                        </xsl:for-each>-->
                    </xsl:when>
                    <xsl:when test="exsl:node-set($thisAuthorLayout)/following-sibling::*[1][name()='emailAddressLayout']">
                        <!-- format any email addresses first -->
                        <!--                        <xsl:for-each select="$thisEmailAddressLayout">-->
                        <xsl:apply-templates select="$myEmailAddress">
                            <xsl:with-param name="emailAddressLayoutToUse" select="$thisEmailAddressLayout"/>
                        </xsl:apply-templates>
                        <!--                        </xsl:for-each>-->
                        <!--                        <xsl:for-each select="$thisAffiliationLayout">-->
                        <xsl:apply-templates select="$myAffiliations">
                            <xsl:with-param name="affiliationLayoutToUse" select="$thisAffiliationLayout"/>
                        </xsl:apply-templates>
                        <!--                        </xsl:for-each>-->
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- nothing to do -->
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>
    <!--  
        DoBookEndnotesLabelingContent
    -->
    <xsl:template name="DoBookEndnotesLabelingContent">
        <xsl:param name="chapterOrAppendixUnit"/>
        <xsl:variable name="endnotes" select="//endnotes"/>
        <xsl:choose>
            <xsl:when test="name($chapterOrAppendixUnit)='chapter' or name($chapterOrAppendixUnit)='chapterInCollection' or name($chapterOrAppendixUnit)='chapterBeforePart'">
                <xsl:call-template name="DoEndnoteSectionLabel">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($bodyLayoutInfo)/chapterLayout/chapterTitleLayout"/>
                    <!--                    <xsl:with-param name="sDefault" select="'Chapter'"/>-->
                    <xsl:with-param name="sDefault">
                        <xsl:variable name="choices" select="exsl:node-set($endnotes)/chapterLabelContentChoices"/>
                        <xsl:choose>
                            <xsl:when test="$choices">
                                <xsl:for-each select="exsl:node-set($endnotes)/chapterLabelContentChoices">
                                    <xsl:call-template name="OutputLabel">
                                        <xsl:with-param name="sDefault" select="'Chapter'"/>
                                        <xsl:with-param name="pLabel" select="@label"/>
                                    </xsl:call-template>
                                </xsl:for-each>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="OutputLabel">
                                    <xsl:with-param name="sDefault" select="'Chapter'"/>
                                    <xsl:with-param name="pLabel" select="@label"/>
                                </xsl:call-template>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="name($chapterOrAppendixUnit)='appendix'">
                <xsl:call-template name="DoEndnoteSectionLabel">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($backMatterLayoutInfo)/appendixLayout/appendixTitleLayout"/>
                    <!--                    <xsl:with-param name="sDefault" select="'Appendix'"/>-->
                    <xsl:with-param name="sDefault">
                        <xsl:variable name="choices" select="exsl:node-set($endnotes)/appendixLabelContentChoices"/>
                        <xsl:choose>
                            <xsl:when test="$choices">
                                <xsl:for-each select="exsl:node-set($endnotes)/appendixLabelContentChoices">
                                    <xsl:call-template name="OutputLabel">
                                        <xsl:with-param name="sDefault" select="'Appendix'"/>
                                        <xsl:with-param name="pLabel" select="@label"/>
                                    </xsl:call-template>
                                </xsl:for-each>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="OutputLabel">
                                    <xsl:with-param name="sDefault" select="'Appendix'"/>
                                    <xsl:with-param name="pLabel" select="@label"/>
                                </xsl:call-template>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="name($chapterOrAppendixUnit)='part'">
                <xsl:call-template name="DoEndnoteSectionLabel">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($backMatterLayoutInfo)/partLayout/partTitleLayout"/>
                    <!--                    <xsl:with-param name="sDefault" select="'Appendix'"/>-->
                    <xsl:with-param name="sDefault">
                        <xsl:for-each select="exsl:node-set($endnotes)/partLabelContentChoices">
                            <xsl:call-template name="OutputLabel">
                                <xsl:with-param name="sDefault" select="'Part'"/>
                                <xsl:with-param name="pLabel" select="@label"/>
                            </xsl:call-template>
                        </xsl:for-each>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="name($chapterOrAppendixUnit)='glossary'">
                <xsl:call-template name="DoEndnoteSectionLabel">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($backMatterLayoutInfo)/glossaryLayout/glossaryTitleLayout"/>
                    <xsl:with-param name="sDefault">
                        <xsl:for-each select="$chapterOrAppendixUnit">
                            <xsl:call-template name="OutputGlossaryLabel"/>
                        </xsl:for-each>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="name($chapterOrAppendixUnit)='acknowledgements'">
                <xsl:choose>
                    <xsl:when test="ancestor::frontMatter">
                        <xsl:call-template name="DoEndnoteSectionLabel">
                            <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/acknowledgementsLayout/acknowledgementsTitleLayout"/>
                            <!--                            <xsl:with-param name="sDefault" select="'Acknowledgements'"/>-->
                            <xsl:with-param name="sDefault">
                                <xsl:for-each select="$chapterOrAppendixUnit">
                                    <xsl:call-template name="OutputAcknowledgementsLabel"/>
                                </xsl:for-each>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="DoEndnoteSectionLabel">
                            <xsl:with-param name="layoutInfo" select="exsl:node-set($backMatterLayoutInfo)/acknowledgementsLayout/acknowledgementsTitleLayout"/>
                            <!--                            <xsl:with-param name="sDefault" select="'Acknowledgements'"/>-->
                            <xsl:with-param name="sDefault">
                                <xsl:for-each select="$chapterOrAppendixUnit">
                                    <xsl:call-template name="OutputAcknowledgementsLabel"/>
                                </xsl:for-each>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="name($chapterOrAppendixUnit)='preface'">
                <xsl:call-template name="DoEndnoteSectionLabel">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/prefaceLayout/prefaceTitleLayout"/>
                    <xsl:with-param name="sDefault">
                        <xsl:for-each select="$chapterOrAppendixUnit">
                            <xsl:call-template name="OutputPrefaceLabel">
                                <xsl:with-param name="iPos" select="count(exsl:node-set($chapterOrAppendixUnit)/preceding-sibling::preface)+1"/>
                            </xsl:call-template>
                        </xsl:for-each>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="name($chapterOrAppendixUnit)='abstract'">
                <xsl:call-template name="DoEndnoteSectionLabel">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/abstractLayout/abstractTitleLayout"/>
                    <!--                    <xsl:with-param name="sDefault" select="'Abstract'"/>-->
                    <xsl:with-param name="sDefault">
                        <xsl:for-each select="$chapterOrAppendixUnit">
                            <xsl:call-template name="OutputAbstractLabel">
                                <xsl:with-param name="iPos" select="count(exsl:node-set($chapterOrAppendixUnit)/preceding-sibling::abstract)+1"/>
                            </xsl:call-template>
                        </xsl:for-each>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoBookEndnoteSectionLabel
    -->
    <xsl:template name="DoBookEndnoteSectionLabel">
        <xsl:param name="originalContext"/>
        <xsl:choose>
            <xsl:when test="$originalContext">
                <xsl:for-each select="$originalContext">
                    <xsl:variable name="chapterOrAppendixUnit"
                        select="ancestor::chapter | ancestor::chapterBeforePart | ancestor::appendix | ancestor::glossary | ancestor::acknowledgements | ancestor::preface | ancestor::abstract | ancestor::chapterInCollection | ancestor::part"/>
                    <xsl:call-template name="DoBookEndnotesLabeling">
                        <xsl:with-param name="originalContext" select="$originalContext"/>
                        <xsl:with-param name="chapterOrAppendixUnit" select="$chapterOrAppendixUnit"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="thisEndnote" select="."/>
                <xsl:variable name="chapterOrAppendixUnit"
                    select="ancestor::chapter | ancestor::chapterBeforePart | ancestor::appendix | ancestor::glossary | ancestor::acknowledgements | ancestor::preface | ancestor::abstract | ancestor::chapterInCollection | ancestor::part[not(exsl:node-set($thisEndnote)[ancestor::chapter])]"/>
                <xsl:choose>
                    <xsl:when test="starts-with(name($chapterOrAppendixUnit),'chapter') and /xlingpaper/styledPaper/publisherStyleSheet[1]/bodyLayout/chapterLayout/@resetEndnoteNumbering='no'">
                        <!-- do nothing -->
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="DoBookEndnotesLabeling">
                            <xsl:with-param name="originalContext" select="$originalContext"/>
                            <xsl:with-param name="chapterOrAppendixUnit" select="$chapterOrAppendixUnit"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoBookLayout
    -->
    <xsl:template name="DoBookLayout">
        <xsl:variable name="book" select="."/>
        <xsl:variable name="work" select=".."/>
        <xsl:variable name="bookLayoutToUsePosition">
            <xsl:call-template name="GetBookLayoutToUsePosition"/>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$bookLayoutToUsePosition=0 or string-length($bookLayoutToUsePosition)=0">
                <xsl:call-template name="ReportNoPatternMatched"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/bookLayouts/*[position()=$bookLayoutToUsePosition]">
                    <xsl:for-each select="*">
                        <xsl:choose>
                            <xsl:when test="name(.)='refTitleItem' and string-length(exsl:node-set($work)/refTitle) &gt; 0">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($work)/refTitle"/>
                                </xsl:call-template>
                                <xsl:if test="exsl:node-set($work)/../@showAuthorName='no'">
                                    <xsl:call-template name="DoDateLayout">
                                        <xsl:with-param name="refDateItem" select="ancestor::referencesLayout/refAuthorLayouts/refAuthorLayout[position()=last()]/refDateItem"/>
                                        <xsl:with-param name="work" select="$work"/>
                                    </xsl:call-template>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='translatedByItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($book)/translatedBy"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='editorItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($book)/editor"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='editionItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($book)/edition"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='seriesItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($book)/series"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='seriesEdItem'">
                                <xsl:variable name="item" select="exsl:node-set($book)/seriesEd"/>
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($book)/seriesEd"/>
                                </xsl:call-template>
                                <xsl:if test="@appendEdAbbreviation != 'no'">
                                    <xsl:call-template name="DoEditorAbbreviation">
                                        <xsl:with-param name="item" select="$item"/>
                                    </xsl:call-template>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='bVolItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="normalize-space(exsl:node-set($book)/bVol)"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='multivolumeWorkItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($book)/multivolumeWork"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='bookTotalPagesItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="normalize-space(exsl:node-set($book)/bookTotalPages)"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='reprintInfoItem'">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($book)/reprintInfo"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem' and name(following-sibling::*[2])='doiItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$book"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[2])='urlItem' and name(preceding-sibling::*[1])='dateAccessedItem' and name(.)='doi'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$book"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[1])='urlItem' and name(.)='dateAccessedItem'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem'">
                                <xsl:call-template name="HandleUrlLayout">
                                    <xsl:with-param name="kindOfWork" select="$book"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='dateAccessedItem'">
                                <xsl:call-template name="HandleDateAccessedLayout">
                                    <xsl:with-param name="kindOfWork" select="$book"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='doiItem'">
                                <xsl:call-template name="HandleDoiLayout">
                                    <xsl:with-param name="kindOfWork" select="$book"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='locationPublisherLayoutsRef'">
                                <xsl:call-template name="DoLocationPublisherLayout">
                                    <xsl:with-param name="reference" select="$book"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlDateAccessedLayoutsRef'">
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="$book"/>
                                </xsl:call-template>
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="exsl:node-set($book)/.."/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='iso639-3codeItemRef'">
                                <xsl:call-template name="DoISO639-3Codes">
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoCitation
    -->
    <xsl:template name="DoCitation">
        <xsl:param name="layout"/>
        <xsl:variable name="sThisRefToBook" select="@refToBook"/>
        <xsl:choose>
            <xsl:when test="saxon:node-set($collOrProcVolumesToInclude)/refWork[@id=$sThisRefToBook]">
                <xsl:call-template name="DoRefCitation">
                    <xsl:with-param name="citation" select="."/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="FleshOutRefCitation">
                    <xsl:with-param name="citation" select="."/>
                    <xsl:with-param name="citationLayout" select="exsl:node-set($layout)/.."/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoCitedCollectionLayout
    -->
    <xsl:template name="DoCitedCollectionLayout">
        <xsl:param name="book"/>
        <xsl:param name="citation"/>
        <xsl:param name="citationLayout"/>
        <xsl:variable name="work" select="exsl:node-set($book)/.."/>
        <xsl:variable name="citedCollectionLayoutToUsePosition">
            <xsl:for-each select="$book">
                <xsl:call-template name="GetCitedCollectionLayoutToUsePosition">
                    <xsl:with-param name="collCitation" select="$citation"/>
                </xsl:call-template>
            </xsl:for-each>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$citedCollectionLayoutToUsePosition=0 or string-length($citedCollectionLayoutToUsePosition)=0">
                <xsl:for-each select="$book">
                    <xsl:call-template name="ReportNoPatternMatchedForCollCitation">
                        <xsl:with-param name="collCitation" select="$citation"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/collectionLayouts/*[position()=$citedCollectionLayoutToUsePosition]">
                    <xsl:for-each select="*">
                        <xsl:choose>
                            <xsl:when test="name(.)='collEdItem'">
                                <xsl:for-each select="exsl:node-set($citationLayout)/authorRoleItem">
                                    <xsl:call-template name="OutputReferenceItem">
                                        <xsl:with-param name="item" select="exsl:node-set($work)/authorRole"/>
                                    </xsl:call-template>
                                </xsl:for-each>
                            </xsl:when>
                            <xsl:when test="name(.)='collTitleItem' and string-length(exsl:node-set($work)/refTitle) &gt; 0">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($work)/refTitle"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='editionItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($book)/edition"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='collVolItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="normalize-space(exsl:node-set($book)/bVol)"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='collPagesItem'">
                                <xsl:call-template name="OutputCitationPages">
                                    <xsl:with-param name="citation" select="$citation"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='seriesEdItem'">
                                <xsl:variable name="item" select="exsl:node-set($book)/seriesEd"/>
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="$item"/>
                                </xsl:call-template>
                                <xsl:if test="@appendEdAbbreviation != 'no'">
                                    <xsl:call-template name="DoEditorAbbreviation">
                                        <xsl:with-param name="item" select="$item"/>
                                    </xsl:call-template>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='seriesItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($book)/series"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='multivolumeWorkItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($book)/multivolumeWork"/>
                                </xsl:call-template>
                            </xsl:when>
                            <!--        in a series??                    <xsl:when test="name(.)='bVolItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="normalize-space(exsl:node-set($collection)/bVol)"/>
                                </xsl:call-template>
                            </xsl:when>
-->
                            <xsl:when test="name(.)='reprintInfoItem'">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($book)/reprintInfo"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem' and name(following-sibling::*[2])='doiItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$book"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[2])='urlItem' and name(preceding-sibling::*[1])='dateAccessedItem' and name(.)='doi'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$book"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[1])='urlItem' and name(.)='dateAccessedItem'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem'">
                                <xsl:call-template name="HandleUrlLayout">
                                    <xsl:with-param name="kindOfWork" select="$book"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='dateAccessedItem'">
                                <xsl:call-template name="HandleDateAccessedLayout">
                                    <xsl:with-param name="kindOfWork" select="$book"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='doiItem'">
                                <xsl:call-template name="HandleDoiLayout">
                                    <xsl:with-param name="kindOfWork" select="$book"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='locationPublisherLayoutsRef'">
                                <xsl:call-template name="DoLocationPublisherLayout">
                                    <xsl:with-param name="reference" select="$book"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlDateAccessedLayoutsRef'">
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="$book"/>
                                </xsl:call-template>
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="exsl:node-set($book)/.."/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='iso639-3codeItemRef'">
                                <xsl:call-template name="DoISO639-3Codes">
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoCitedProceedingsLayout
    -->
    <xsl:template name="DoCitedProceedingsLayout">
        <xsl:param name="book"/>
        <xsl:param name="citation"/>
        <xsl:param name="citationLayout"/>
        <xsl:variable name="work" select="exsl:node-set($book)/.."/>
        <xsl:variable name="citedProceedingsLayoutToUsePosition">
            <xsl:for-each select="$book">
                <xsl:call-template name="GetCitedProceedingsLayoutToUsePosition">
                    <xsl:with-param name="procCitation" select="$citation"/>
                </xsl:call-template>
            </xsl:for-each>
        </xsl:variable>
        <xsl:variable name="proceedings" select="."/>
        <xsl:choose>
            <xsl:when test="$citedProceedingsLayoutToUsePosition=0 or string-length($citedProceedingsLayoutToUsePosition)=0">
                <xsl:for-each select="$book">
                    <xsl:call-template name="ReportNoPatternMatchedForProcCitation">
                        <xsl:with-param name="procCitation" select="$citation"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/proceedingsLayouts/*[position()=$citedProceedingsLayoutToUsePosition]">
                    <xsl:for-each select="*">
                        <xsl:choose>
                            <xsl:when test="name(.)='procEdItem'">
                                <xsl:for-each select="exsl:node-set($citationLayout)/authorRoleItem">
                                    <xsl:call-template name="OutputReferenceItem">
                                        <xsl:with-param name="item" select="exsl:node-set($work)/authorRole"/>
                                    </xsl:call-template>
                                </xsl:for-each>
                            </xsl:when>
                            <xsl:when test="name(.)='procTitleItem' and string-length(exsl:node-set($work)/refTitle) &gt; 0">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($work)/refTitle"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='procVolItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="normalize-space(exsl:node-set($book)/bVol)"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='procPagesItem'">
                                <xsl:call-template name="OutputCitationPages">
                                    <xsl:with-param name="citation" select="$citation"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='reprintInfoItem'">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($book)/reprintInfo"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem' and name(following-sibling::*[2])='doiItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$book"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[2])='urlItem' and name(preceding-sibling::*[1])='dateAccessedItem' and name(.)='doi'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$book"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[1])='urlItem' and name(.)='dateAccessedItem'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem'">
                                <xsl:call-template name="HandleUrlLayout">
                                    <xsl:with-param name="kindOfWork" select="$book"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='dateAccessedItem'">
                                <xsl:call-template name="HandleDateAccessedLayout">
                                    <xsl:with-param name="kindOfWork" select="$book"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='doiItem'">
                                <xsl:call-template name="HandleDoiLayout">
                                    <xsl:with-param name="kindOfWork" select="$book"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='locationPublisherLayoutsRef'">
                                <xsl:call-template name="DoLocationPublisherLayout">
                                    <xsl:with-param name="reference" select="$book"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlDateAccessedLayoutsRef'">
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="$book"/>
                                </xsl:call-template>
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="exsl:node-set($book)/.."/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='iso639-3codeItemRef'">
                                <xsl:call-template name="DoISO639-3Codes">
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoCollectionLayout
    -->
    <xsl:template name="DoCollectionLayout">
        <xsl:variable name="collection" select="."/>
        <xsl:variable name="work" select=".."/>
        <xsl:variable name="collectionLayoutToUsePosition">
            <xsl:call-template name="GetCollectionLayoutToUsePosition"/>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$collectionLayoutToUsePosition=0 or string-length($collectionLayoutToUsePosition)=0">
                <xsl:call-template name="ReportNoPatternMatched"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="bHasCollCitation">
                    <xsl:choose>
                        <xsl:when test="collCitation">Y</xsl:when>
                        <xsl:otherwise>N</xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:variable name="bUseCitationAsLink">
                    <xsl:variable name="sThisRefToBook" select="collCitation/@refToBook"/>
                    <xsl:choose>
                        <xsl:when test="saxon:node-set($collOrProcVolumesToInclude)/refWork[@id=$sThisRefToBook]">
                            <xsl:text>Y</xsl:text>
                        </xsl:when>
                        <xsl:otherwise>N</xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/collectionLayouts/*[position()=$collectionLayoutToUsePosition]">
                    <xsl:for-each select="*">
                        <xsl:choose>
                            <xsl:when test="name(.)='refTitleItem' and string-length(exsl:node-set($work)/refTitle) &gt; 0">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($work)/refTitle"/>
                                </xsl:call-template>
                                <xsl:if test="exsl:node-set($work)/../@showAuthorName='no'">
                                    <xsl:call-template name="DoDateLayout">
                                        <xsl:with-param name="refDateItem" select="ancestor::referencesLayout/refAuthorLayouts/refAuthorLayout[position()=last()]/refDateItem"/>
                                        <xsl:with-param name="work" select="$work"/>
                                    </xsl:call-template>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='collCitationItem'">
                                <xsl:call-template name="OutputCitation">
                                    <xsl:with-param name="item" select="exsl:node-set($collection)/collCitation"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='authorRoleItem'">
                                <xsl:if test="$bHasCollCitation='Y' and $bUseCitationAsLink='Y'">
                                    <xsl:call-template name="OutputReferenceItem">
                                        <xsl:with-param name="item" select="key('RefWorkID',exsl:node-set($collection)/collCitation/@refToBook)/authorRole"/>
                                    </xsl:call-template>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='collEdItem'">
                                <xsl:variable name="item" select="exsl:node-set($collection)/collEd"/>
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="$item"/>
                                </xsl:call-template>
                                <xsl:if test="@appendEdAbbreviation != 'no'">
                                    <xsl:call-template name="DoEditorAbbreviation">
                                        <xsl:with-param name="item" select="$item"/>
                                    </xsl:call-template>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='collTitleItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($collection)/collTitle"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='editionItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($collection)/edition"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='collVolItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="normalize-space(exsl:node-set($collection)/collVol)"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='collPagesItem'">
                                <xsl:if test="$bHasCollCitation='N' or $bUseCitationAsLink='Y'">
                                    <xsl:variable name="sNormalizedPages">
                                        <xsl:variable name="sCitationPages" select="normalize-space(exsl:node-set($collection)/collCitation/@page)"/>
                                        <xsl:choose>
                                            <xsl:when test="not(exsl:node-set($collection)/collPages) and string-length($sCitationPages) &gt; 0">
                                                <xsl:value-of select="$sCitationPages"/>
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <xsl:value-of select="normalize-space(exsl:node-set($collection)/collPages)"/>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </xsl:variable>
                                    <xsl:variable name="pages">
                                        <xsl:call-template name="GetFormattedPageNumbers">
                                            <xsl:with-param name="normalizedPages" select="$sNormalizedPages"/>
                                        </xsl:call-template>
                                    </xsl:variable>
                                    <xsl:call-template name="OutputReferenceItem">
                                        <xsl:with-param name="item" select="$pages"/>
                                    </xsl:call-template>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='seriesEdItem'">
                                <xsl:variable name="item" select="exsl:node-set($collection)/seriesEd"/>
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="$item"/>
                                </xsl:call-template>
                                <xsl:if test="@appendEdAbbreviation != 'no'">
                                    <xsl:call-template name="DoEditorAbbreviation">
                                        <xsl:with-param name="item" select="$item"/>
                                    </xsl:call-template>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='seriesItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($collection)/series"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='bVolItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="normalize-space(exsl:node-set($collection)/bVol)"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='multivolumeWorkItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($collection)/multivolumeWork"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='reprintInfoItem'">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($collection)/reprintInfo"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem' and name(following-sibling::*[2])='doiItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$collection"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[2])='urlItem' and name(preceding-sibling::*[1])='dateAccessedItem' and name(.)='doi'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$collection"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[1])='urlItem' and name(.)='dateAccessedItem'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem'">
                                <xsl:call-template name="HandleUrlLayout">
                                    <xsl:with-param name="kindOfWork" select="$collection"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='dateAccessedItem'">
                                <xsl:call-template name="HandleDateAccessedLayout">
                                    <xsl:with-param name="kindOfWork" select="$collection"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='doiItem'">
                                <xsl:call-template name="HandleDoiLayout">
                                    <xsl:with-param name="kindOfWork" select="$collection"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='locationPublisherLayoutsRef'">
                                <xsl:call-template name="DoLocationPublisherLayout">
                                    <xsl:with-param name="reference" select="$collection"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlDateAccessedLayoutsRef'">
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="$collection"/>
                                </xsl:call-template>
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="exsl:node-set($collection)/.."/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='iso639-3codeItemRef'">
                                <xsl:call-template name="DoISO639-3Codes">
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoDissertationLayout
    -->
    <xsl:template name="DoDissertationLayout">
        <xsl:param name="layout"/>
        <xsl:variable name="dissertation" select="."/>
        <xsl:variable name="work" select=".."/>
        <xsl:variable name="dissertationLayoutToUsePosition">
            <xsl:call-template name="GetDissertationLayoutToUsePosition">
                <xsl:with-param name="layout" select="$layout"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$dissertationLayoutToUsePosition=0 or string-length($dissertationLayoutToUsePosition)=0">
                <xsl:call-template name="ReportNoPatternMatched"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:for-each select="exsl:node-set($layout)/*[position()=$dissertationLayoutToUsePosition]">
                    <xsl:for-each select="*">
                        <xsl:choose>
                            <xsl:when test="name(.)='refTitleItem' and string-length(exsl:node-set($work)/refTitle) &gt; 0">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($work)/refTitle"/>
                                </xsl:call-template>
                                <xsl:if test="exsl:node-set($work)/../@showAuthorName='no'">
                                    <xsl:call-template name="DoDateLayout">
                                        <xsl:with-param name="refDateItem" select="ancestor::referencesLayout/refAuthorLayouts/refAuthorLayout[position()=last()]/refDateItem"/>
                                        <xsl:with-param name="work" select="$work"/>
                                    </xsl:call-template>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='dissertationLabelItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item">
                                        <xsl:choose>
                                            <xsl:when test="string-length(normalize-space(@label)) &gt; 0">
                                                <xsl:value-of select="@label"/>
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <xsl:call-template name="OutputLabel">
                                                    <xsl:with-param name="sDefault" select="$sPhDDissertationDefaultLabel"/>
                                                    <xsl:with-param name="pLabel">
                                                        <xsl:choose>
                                                            <xsl:when test="string-length(normalize-space(exsl:node-set($dissertation)/@labelDissertation)) &gt; 0">
                                                                <xsl:value-of select="exsl:node-set($dissertation)/@labelDissertation"/>
                                                            </xsl:when>
                                                            <xsl:otherwise>
                                                                <xsl:value-of select="//references/@labelDissertation"/>
                                                            </xsl:otherwise>
                                                        </xsl:choose>
                                                    </xsl:with-param>
                                                </xsl:call-template>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </xsl:with-param>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='thesisLabelItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item">
                                        <xsl:choose>
                                            <xsl:when test="string-length(normalize-space(@label)) &gt; 0">
                                                <xsl:value-of select="@label"/>
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <xsl:call-template name="OutputLabel">
                                                    <xsl:with-param name="sDefault" select="$sMAThesisDefaultLabel"/>
                                                    <xsl:with-param name="pLabel">
                                                        <xsl:choose>
                                                            <xsl:when test="string-length(normalize-space(exsl:node-set($dissertation)/@labelThesis)) &gt; 0">
                                                                <xsl:value-of select="exsl:node-set($dissertation)/@labelThesis"/>
                                                            </xsl:when>
                                                            <xsl:otherwise>
                                                                <xsl:value-of select="//references/@labelThesis"/>
                                                            </xsl:otherwise>
                                                        </xsl:choose>
                                                    </xsl:with-param>
                                                </xsl:call-template>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </xsl:with-param>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='institutionItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($dissertation)/institution"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='locationItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($dissertation)/location"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='publishedLayoutRef'">
                                <xsl:call-template name="DoPublishedLayout">
                                    <xsl:with-param name="reference" select="exsl:node-set($dissertation)/published"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='reprintInfoItem'">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($dissertation)/reprintInfo"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem' and name(following-sibling::*[2])='doiItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$dissertation"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[2])='urlItem' and name(preceding-sibling::*[1])='dateAccessedItem' and name(.)='doi'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$dissertation"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[1])='urlItem' and name(.)='dateAccessedItem'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem'">
                                <xsl:call-template name="HandleUrlLayout">
                                    <xsl:with-param name="kindOfWork" select="$dissertation"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='dateAccessedItem'">
                                <xsl:call-template name="HandleDateAccessedLayout">
                                    <xsl:with-param name="kindOfWork" select="$dissertation"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='doiItem'">
                                <xsl:call-template name="HandleDoiLayout">
                                    <xsl:with-param name="kindOfWork" select="$dissertation"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlDateAccessedLayoutsRef'">
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="$dissertation"/>
                                </xsl:call-template>
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="exsl:node-set($dissertation)/.."/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='iso639-3codeItemRef'">
                                <xsl:call-template name="DoISO639-3Codes">
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
      DoEditorAbbreviation
   -->
    <xsl:template name="DoEditorAbbreviation">
        <xsl:param name="item"/>
        <xsl:if test="string-length(normalize-space($item)) &gt; 0">
            <xsl:choose>
                <xsl:when test="string-length(@edTextbefore) &gt; 0">
                    <xsl:value-of select="@edTextbefore"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>, </xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="exsl:node-set($item)/@plural='no'">
                    <xsl:choose>
                        <xsl:when test="string-length(@edTextSingular) &gt; 0">
                            <xsl:value-of select="@edTextSingular"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>ed</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:choose>
                        <xsl:when test="string-length(@edTextPlural) &gt; 0">
                            <xsl:value-of select="@edTextPlural"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>eds</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="string-length(@edTextafter) &gt; 0">
                    <xsl:value-of select="@edTextafter"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>. </xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--  
        DoFigureRef
    -->
    <xsl:template name="DoFigureRef">
        <xsl:variable name="figure" select="id(@figure)"/>
        <xsl:choose>
            <xsl:when test="@showCaption='short'">
                <xsl:call-template name="DoFormatLayoutInfoTextBefore">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($contentLayoutInfo)/figureRefCaptionLayout"/>
                </xsl:call-template>
                <xsl:choose>
                    <xsl:when test="exsl:node-set($figure)/shortCaption and string-length(exsl:node-set($figure)/shortCaption) &gt; 0">
                        <xsl:apply-templates select="exsl:node-set($figure)/shortCaption/child::node()[name()!='endnote']"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:apply-templates select="exsl:node-set($figure)/caption/child::node()[name()!='endnote']"/>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($contentLayoutInfo)/figureRefCaptionLayout"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="@showCaption='full'">
                <xsl:call-template name="DoFormatLayoutInfoTextBefore">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($contentLayoutInfo)/figureRefCaptionLayout"/>
                </xsl:call-template>
                <xsl:apply-templates select="exsl:node-set($figure)/caption/child::node()[name()!='endnote']"/>
                <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($contentLayoutInfo)/figureRefCaptionLayout"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <!--                <xsl:apply-templates select="$figure" mode="figure"/>-->
                <xsl:call-template name="GetFigureNumber">
                    <xsl:with-param name="figure" select="$figure"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoFormatLayoutInfoTextAfter
    -->
    <xsl:template name="DoFormatLayoutInfoTextAfter">
        <xsl:param name="layoutInfo"/>
        <xsl:param name="sPrecedingText"/>
        <xsl:variable name="sAfter" select="exsl:node-set($layoutInfo)/@textafter"/>
        <xsl:if test="string-length($sAfter) &gt; 0">
            <xsl:choose>
                <xsl:when test="starts-with($sAfter,'.')">
                    <xsl:variable name="sLastChar" select="substring($sPrecedingText,string-length($sPrecedingText),string-length($sPrecedingText))"/>
                    <xsl:choose>
                        <xsl:when test="$sLastChar='.' or $sLastChar='?' or $sLastChar='!'">
                            <xsl:value-of select="substring($sAfter, 2)"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$sAfter"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$sAfter"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--  
        DoInterlinearRefCitationShowTitleOnly
    -->
    <xsl:template name="DoInterlinearRefCitationShowTitleOnly">
        <xsl:variable name="interlinear" select="key('InterlinearReferenceID',@textref)"/>
        <xsl:choose>
            <xsl:when test="@showTitleOnly='short'">
                <!-- only one of these will work -->
                <xsl:apply-templates select="exsl:node-set($interlinear)/textInfo/shortTitle/child::node()[name()!='endnote']"/>
                <xsl:apply-templates select="exsl:node-set($interlinear)/../textInfo/shortTitle/child::node()[name()!='endnote']"/>
            </xsl:when>
            <xsl:otherwise>
                <!-- only one of these will work -->
                <xsl:apply-templates select="exsl:node-set($interlinear)/textInfo/textTitle/child::node()[name()!='endnote']"/>
                <xsl:apply-templates select="exsl:node-set($interlinear)/../textInfo/textTitle/child::node()[name()!='endnote']"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
      DoISO639-3Codes
   -->
    <xsl:template name="DoISO639-3Codes">
        <xsl:param name="work"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($iso639-3codeItem)/@sort='no'">
                <xsl:for-each select="exsl:node-set($work)/iso639-3code | exsl:node-set($work)/descendant::iso639-3code">
                    <xsl:call-template name="OutputISO639-3Code"/>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <xsl:for-each select="exsl:node-set($work)/iso639-3code | exsl:node-set($work)/descendant::iso639-3code">
                    <xsl:sort/>
                    <xsl:call-template name="OutputISO639-3Code"/>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoItemRefLabel
    -->
    <xsl:template name="DoItemRefLabel">
        <xsl:param name="sLabel"/>
        <xsl:param name="sDefault"/>
        <xsl:param name="sOverride"/>
        <xsl:choose>
            <xsl:when test="string-length($sOverride) &gt; 0">
                <xsl:value-of select="$sOverride"/>
            </xsl:when>
            <xsl:when test="string-length($sLabel) &gt; 0">
                <xsl:value-of select="$sLabel"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sDefault"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoLocationPublisherLayout
    -->
    <xsl:template name="DoLocationPublisherLayout">
        <xsl:param name="reference"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($reference)/location and exsl:node-set($reference)/publisher">
                <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/locationPublisherLayouts/*[locationItem and publisherItem]">
                    <xsl:for-each select="*">
                        <xsl:choose>
                            <xsl:when test="name(.)='locationItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($reference)/location"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='publisherItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($reference)/publisher"/>
                                </xsl:call-template>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:when>
            <xsl:when test="exsl:node-set($reference)/location and not(exsl:node-set($reference)/publisher)">
                <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/locationPublisherLayouts/*[locationItem and not(publisherItem)]">
                    <xsl:for-each select="*">
                        <xsl:call-template name="OutputReferenceItem">
                            <xsl:with-param name="item" select="exsl:node-set($reference)/location"/>
                        </xsl:call-template>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:when>
            <xsl:when test="not(exsl:node-set($reference)/location) and exsl:node-set($reference)/publisher">
                <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/locationPublisherLayouts/*[not(locationItem) and publisherItem]">
                    <xsl:for-each select="*">
                        <xsl:call-template name="OutputReferenceItem">
                            <xsl:with-param name="item" select="exsl:node-set($reference)/publisher"/>
                        </xsl:call-template>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoEndnoteSectionLabel
    -->
    <xsl:template name="DoEndnoteSectionLabel">
        <xsl:param name="layoutInfo"/>
        <xsl:param name="sDefault"/>
        <xsl:variable name="sTextBefore" select="normalize-space(exsl:node-set($layoutInfo)/@textbefore)"/>
        <xsl:choose>
            <xsl:when test="string-length($sTextBefore) &gt; 0">
                <xsl:value-of select="$sTextBefore"/>
            </xsl:when>
            <xsl:when test="string-length(normalize-space(exsl:node-set($lingPaper)/@chapterlabel)) &gt; 0">
                <xsl:value-of select="exsl:node-set($lingPaper)/@chapterlabel"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sDefault"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoExampleRefContent
    -->
    <xsl:template name="DoExampleRefContent">
        <xsl:if test="exsl:node-set($contentLayoutInfo)/exampleLayout/@referencesUseParens!='no'">
            <xsl:if test="not(@paren) or @paren='both' or @paren='initial'">(</xsl:if>
        </xsl:if>
        <xsl:if test="@equal='yes'">=</xsl:if>
        <xsl:choose>
            <xsl:when test="@letter and name(id(@letter))!='example'">
                <xsl:if test="not(@letterOnly='yes')">
                    <xsl:call-template name="GetExampleNumber">
                        <xsl:with-param name="example" select="id(@letter)"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:apply-templates select="id(@letter)" mode="letter"/>
            </xsl:when>
            <xsl:when test="@num">
                <xsl:call-template name="GetExampleNumber">
                    <xsl:with-param name="example" select="id(@num)"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
        <xsl:if test="@punct">
            <xsl:value-of select="@punct"/>
        </xsl:if>
        <xsl:if test="exsl:node-set($contentLayoutInfo)/exampleLayout/@referencesUseParens!='no'">
            <xsl:if test="not(@paren) or @paren='both' or @paren='final'">)</xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
      DoFieldNotesLayout
   -->
    <xsl:template name="DoFieldNotesLayout">
        <xsl:variable name="fieldNotes" select="."/>
        <xsl:variable name="work" select=".."/>
        <xsl:variable name="fieldNotesLayoutToUsePosition">
            <xsl:call-template name="GetFieldNotesLayoutToUsePosition"/>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$fieldNotesLayoutToUsePosition=0 or string-length($fieldNotesLayoutToUsePosition)=0">
                <xsl:call-template name="ReportNoPatternMatched"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/fieldNotesLayouts/*[position()=$fieldNotesLayoutToUsePosition]">
                    <xsl:for-each select="*">
                        <xsl:choose>
                            <xsl:when test="name(.)='refTitleItem' and string-length(exsl:node-set($work)/refTitle) &gt; 0">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($work)/refTitle"/>
                                </xsl:call-template>
                                <xsl:if test="exsl:node-set($work)/../@showAuthorName='no'">
                                    <xsl:call-template name="DoDateLayout">
                                        <xsl:with-param name="refDateItem" select="ancestor::referencesLayout/refAuthorLayouts/refAuthorLayout[position()=last()]/refDateItem"/>
                                        <xsl:with-param name="work" select="$work"/>
                                    </xsl:call-template>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='institutionItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($fieldNotes)/institution"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='locationItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($fieldNotes)/location"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem' and name(following-sibling::*[2])='doiItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$fieldNotes"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[2])='urlItem' and name(preceding-sibling::*[1])='dateAccessedItem' and name(.)='doi'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$fieldNotes"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[1])='urlItem' and name(.)='dateAccessedItem'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem'">
                                <xsl:call-template name="HandleUrlLayout">
                                    <xsl:with-param name="kindOfWork" select="$fieldNotes"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='dateAccessedItem'">
                                <xsl:call-template name="HandleDateAccessedLayout">
                                    <xsl:with-param name="kindOfWork" select="$fieldNotes"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='doiItem'">
                                <xsl:call-template name="HandleDoiLayout">
                                    <xsl:with-param name="kindOfWork" select="$fieldNotes"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlDateAccessedLayoutsRef'">
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="$fieldNotes"/>
                                </xsl:call-template>
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="exsl:node-set($fieldNotes)/.."/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='iso639-3codeItemRef'">
                                <xsl:call-template name="DoISO639-3Codes">
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoMsLayout
    -->
    <xsl:template name="DoMsLayout">
        <xsl:variable name="ms" select="."/>
        <xsl:variable name="work" select=".."/>
        <xsl:variable name="msLayoutToUsePosition">
            <xsl:call-template name="GetMsLayoutToUsePosition"/>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$msLayoutToUsePosition=0 or string-length($msLayoutToUsePosition)=0">
                <xsl:call-template name="ReportNoPatternMatched"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/msLayouts/*[position()=$msLayoutToUsePosition]">
                    <xsl:for-each select="*">
                        <xsl:choose>
                            <xsl:when test="name(.)='refTitleItem' and string-length(exsl:node-set($work)/refTitle) &gt; 0">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($work)/refTitle"/>
                                </xsl:call-template>
                                <xsl:if test="exsl:node-set($work)/../@showAuthorName='no'">
                                    <xsl:call-template name="DoDateLayout">
                                        <xsl:with-param name="refDateItem" select="ancestor::referencesLayout/refAuthorLayouts/refAuthorLayout[position()=last()]/refDateItem"/>
                                        <xsl:with-param name="work" select="$work"/>
                                    </xsl:call-template>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='institutionItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($ms)/institution"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='locationItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($ms)/location"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='emptyItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="normalize-space(exsl:node-set($ms)/empty)"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='msVersionItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="normalize-space(exsl:node-set($ms)/msVersion)"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem' and name(following-sibling::*[2])='doiItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$ms"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[2])='urlItem' and name(preceding-sibling::*[1])='dateAccessedItem' and name(.)='doi'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$ms"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[1])='urlItem' and name(.)='dateAccessedItem'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem'">
                                <xsl:call-template name="HandleUrlLayout">
                                    <xsl:with-param name="kindOfWork" select="$ms"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='dateAccessedItem'">
                                <xsl:call-template name="HandleDateAccessedLayout">
                                    <xsl:with-param name="kindOfWork" select="$ms"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='doiItem'">
                                <xsl:call-template name="HandleDoiLayout">
                                    <xsl:with-param name="kindOfWork" select="$ms"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlDateAccessedLayoutsRef'">
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="$ms"/>
                                </xsl:call-template>
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="exsl:node-set($ms)/.."/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='iso639-3codeItemRef'">
                                <xsl:call-template name="DoISO639-3Codes">
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoPaperLayout
    -->
    <xsl:template name="DoPaperLayout">
        <xsl:variable name="paper" select="."/>
        <xsl:variable name="work" select=".."/>
        <xsl:variable name="paperLayoutToUsePosition">
            <xsl:call-template name="GetPaperLayoutToUsePosition"/>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$paperLayoutToUsePosition=0 or string-length($paperLayoutToUsePosition)=0">
                <xsl:call-template name="ReportNoPatternMatched"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/paperLayouts/*[position()=$paperLayoutToUsePosition]">
                    <xsl:for-each select="*">
                        <xsl:choose>
                            <xsl:when test="name(.)='refTitleItem' and string-length(exsl:node-set($work)/refTitle) &gt; 0">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($work)/refTitle"/>
                                </xsl:call-template>
                                <xsl:if test="exsl:node-set($work)/../@showAuthorName='no'">
                                    <xsl:call-template name="DoDateLayout">
                                        <xsl:with-param name="refDateItem" select="ancestor::referencesLayout/refAuthorLayouts/refAuthorLayout[position()=last()]/refDateItem"/>
                                        <xsl:with-param name="work" select="$work"/>
                                    </xsl:call-template>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='paperLabelItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item">
                                        <xsl:call-template name="OutputLabel">
                                            <xsl:with-param name="sDefault" select="$sPaperDefaultLabel"/>
                                            <xsl:with-param name="pLabel">
                                                <xsl:choose>
                                                    <xsl:when test="string-length(normalize-space(exsl:node-set($paper)/@labelPaper)) &gt; 0">
                                                        <xsl:value-of select="exsl:node-set($paper)/@labelPaper"/>
                                                    </xsl:when>
                                                    <xsl:when test="string-length(normalize-space(@label)) &gt; 0">
                                                        <xsl:value-of select="@label"/>
                                                    </xsl:when>
                                                    <xsl:otherwise>
                                                        <xsl:value-of select="//references/@labelPaper"/>
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                            </xsl:with-param>
                                        </xsl:call-template>
                                    </xsl:with-param>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='conferenceItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="normalize-space(exsl:node-set($paper)/conference)"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='locationItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($paper)/location"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem' and name(following-sibling::*[2])='doiItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$paper"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[2])='urlItem' and name(preceding-sibling::*[1])='dateAccessedItem' and name(.)='doi'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$paper"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[1])='urlItem' and name(.)='dateAccessedItem'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem'">
                                <xsl:call-template name="HandleUrlLayout">
                                    <xsl:with-param name="kindOfWork" select="$paper"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='dateAccessedItem'">
                                <xsl:call-template name="HandleDateAccessedLayout">
                                    <xsl:with-param name="kindOfWork" select="$paper"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='doiItem'">
                                <xsl:call-template name="HandleDoiLayout">
                                    <xsl:with-param name="kindOfWork" select="$paper"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlDateAccessedLayoutsRef'">
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="$paper"/>
                                </xsl:call-template>
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="exsl:node-set($paper)/.."/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='iso639-3codeItemRef'">
                                <xsl:call-template name="DoISO639-3Codes">
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoProceedingsLayout
    -->
    <xsl:template name="DoProceedingsLayout">
        <xsl:variable name="proceedings" select="."/>
        <xsl:variable name="work" select=".."/>
        <xsl:variable name="proceedingsLayoutToUsePosition">
            <xsl:call-template name="GetProceedingsLayoutToUsePosition"/>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$proceedingsLayoutToUsePosition=0 or string-length($proceedingsLayoutToUsePosition)=0">
                <xsl:call-template name="ReportNoPatternMatched"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="bHasProcCitation">
                    <xsl:choose>
                        <xsl:when test="procCitation">Y</xsl:when>
                        <xsl:otherwise>N</xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:variable name="bUseCitationAsLink">
                    <xsl:variable name="sThisRefToBook" select="procCitation/@refToBook"/>
                    <xsl:choose>
                        <xsl:when test="saxon:node-set($collOrProcVolumesToInclude)/refWork[@id=$sThisRefToBook]">
                            <xsl:text>Y</xsl:text>
                        </xsl:when>
                        <xsl:otherwise>N</xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/proceedingsLayouts/*[position()=$proceedingsLayoutToUsePosition]">
                    <xsl:for-each select="*">
                        <xsl:choose>
                            <xsl:when test="name(.)='refTitleItem' and string-length(exsl:node-set($work)/refTitle) &gt; 0">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($work)/refTitle"/>
                                </xsl:call-template>
                                <xsl:if test="exsl:node-set($work)/../@showAuthorName='no'">
                                    <xsl:call-template name="DoDateLayout">
                                        <xsl:with-param name="refDateItem" select="ancestor::referencesLayout/refAuthorLayouts/refAuthorLayout[position()=last()]/refDateItem"/>
                                        <xsl:with-param name="work" select="$work"/>
                                    </xsl:call-template>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='procCitationItem'">
                                <xsl:call-template name="OutputCitation">
                                    <xsl:with-param name="item" select="exsl:node-set($proceedings)/procCitation"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='authorRoleItem'">
                                <xsl:if test="$bHasProcCitation='Y' and $bUseCitationAsLink='Y'">
                                    <xsl:call-template name="OutputReferenceItem">
                                        <xsl:with-param name="item" select="key('RefWorkID',exsl:node-set($proceedings)/procCitation/@refToBook)/authorRole"/>
                                    </xsl:call-template>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='procEdItem'">
                                <xsl:variable name="item" select="exsl:node-set($proceedings)/procEd"/>
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="$item"/>
                                </xsl:call-template>
                                <xsl:if test="@appendEdAbbreviation != 'no'">
                                    <xsl:call-template name="DoEditorAbbreviation">
                                        <xsl:with-param name="item" select="$item"/>
                                    </xsl:call-template>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='procTitleItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="normalize-space(exsl:node-set($proceedings)/procTitle)"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='procVolItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="normalize-space(exsl:node-set($proceedings)/procVol)"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='procPagesItem'">
                                <xsl:if test="$bHasProcCitation='N' or $bUseCitationAsLink='Y'">
                                    <xsl:variable name="sNormalizedPages">
                                        <xsl:variable name="sCitationPages" select="normalize-space(exsl:node-set($proceedings)/procCitation/@page)"/>
                                        <xsl:choose>
                                            <xsl:when test="not(exsl:node-set($proceedings)/procPages) and string-length($sCitationPages) &gt; 0">
                                                <xsl:value-of select="$sCitationPages"/>
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <xsl:value-of select="normalize-space(exsl:node-set($proceedings)/procPages)"/>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </xsl:variable>
                                    <xsl:variable name="pages">
                                        <xsl:call-template name="GetFormattedPageNumbers">
                                            <xsl:with-param name="normalizedPages" select="$sNormalizedPages"/>
                                        </xsl:call-template>
                                    </xsl:variable>
                                    <xsl:call-template name="OutputReferenceItem">
                                        <xsl:with-param name="item" select="$pages"/>
                                    </xsl:call-template>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='seriesEdItem'">
                                <xsl:variable name="item" select="exsl:node-set($proceedings)/seriesEd"/>
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="$item"/>
                                </xsl:call-template>
                                <xsl:if test="@appendEdAbbreviation != 'no'">
                                    <xsl:call-template name="DoEditorAbbreviation">
                                        <xsl:with-param name="item" select="$item"/>
                                    </xsl:call-template>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='seriesItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($proceedings)/series"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='bVolItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="normalize-space(exsl:node-set($proceedings)/bVol)"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='multivolumeWorkItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($proceedings)/multivolumeWork"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='reprintInfoItem'">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($proceedings)/reprintInfo"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem' and name(following-sibling::*[2])='doiItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$proceedings"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[2])='urlItem' and name(preceding-sibling::*[1])='dateAccessedItem' and name(.)='doi'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$proceedings"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[1])='urlItem' and name(.)='dateAccessedItem'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem'">
                                <xsl:call-template name="HandleUrlLayout">
                                    <xsl:with-param name="kindOfWork" select="$proceedings"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='dateAccessedItem'">
                                <xsl:call-template name="HandleDateAccessedLayout">
                                    <xsl:with-param name="kindOfWork" select="$proceedings"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='doiItem'">
                                <xsl:call-template name="HandleDoiLayout">
                                    <xsl:with-param name="kindOfWork" select="$proceedings"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='locationPublisherLayoutsRef'">
                                <xsl:call-template name="DoLocationPublisherLayout">
                                    <xsl:with-param name="reference" select="$proceedings"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlDateAccessedLayoutsRef'">
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="$proceedings"/>
                                </xsl:call-template>
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="exsl:node-set($proceedings)/.."/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='iso639-3codeItemRef'">
                                <xsl:call-template name="DoISO639-3Codes">
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoPublishedLayout
    -->
    <xsl:template name="DoPublishedLayout">
        <xsl:param name="reference"/>
        <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/publishedLayout/*">
            <xsl:choose>
                <xsl:when test="name(.)='locationItem'">
                    <xsl:call-template name="OutputReferenceItem">
                        <xsl:with-param name="item" select="exsl:node-set($reference)/location"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:when test="name(.)='publisherItem'">
                    <xsl:call-template name="OutputReferenceItem">
                        <xsl:with-param name="item" select="exsl:node-set($reference)/publisher"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:when test="name(.)='pubDateItem'">
                    <xsl:call-template name="OutputReferenceItem">
                        <xsl:with-param name="item" select="normalize-space(exsl:node-set($reference)/pubDate)"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:when test="name(.)='reprintInfoItem'">
                    <xsl:call-template name="OutputReferenceItemNode">
                        <xsl:with-param name="item" select="exsl:node-set($reference)/reprintInfo"/>
                    </xsl:call-template>
                </xsl:when>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>
    <!--  
        DoSectionRef
    -->
    <xsl:template name="DoSectionRef">
        <xsl:param name="secRefToUse"/>
        <xsl:variable name="section" select="id($secRefToUse)"/>
        <xsl:choose>
            <xsl:when test="@showTitle='short'">
                <xsl:call-template name="DoFormatLayoutInfoTextBefore">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($contentLayoutInfo)/sectionRefTitleLayout"/>
                </xsl:call-template>
                <xsl:choose>
                    <xsl:when test="exsl:node-set($section)/shortTitle and string-length(exsl:node-set($section)/shortTitle) &gt; 0">
                        <xsl:apply-templates select="exsl:node-set($section)/shortTitle/child::node()[name()!='endnote']"/>
                    </xsl:when>
                    <xsl:when test="exsl:node-set($section)/frontMatter/shortTitle and string-length(exsl:node-set($section)/frontMatter/shortTitle) &gt; 0">
                        <xsl:apply-templates select="exsl:node-set($section)/frontMatter/shortTitle/child::node()[name()!='endnote']"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:apply-templates select="exsl:node-set($section)/secTitle/child::node()[name()!='endnote']"/>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($contentLayoutInfo)/sectionRefTitleLayout"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="@showTitle='full'">
                <xsl:call-template name="DoFormatLayoutInfoTextBefore">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($contentLayoutInfo)/sectionRefTitleLayout"/>
                </xsl:call-template>
                <xsl:choose>
                    <xsl:when test="name($section)='chapterInCollection'">
                        <xsl:apply-templates select="exsl:node-set($section)/frontMatter/title/child::node()[name()!='endnote']"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:apply-templates select="exsl:node-set($section)/secTitle/child::node()[name()!='endnote']"/>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($contentLayoutInfo)/sectionRefTitleLayout"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="sNum">
                    <xsl:choose>
                        <xsl:when test="name($section)='part'">
                            <xsl:apply-templates select="$section" mode="numberPart"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:apply-templates select="$section" mode="number"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:value-of select="$sNum"/>
                <xsl:if test="exsl:node-set($contentLayoutInfo)/sectionRefLayout/@AddPeriodAfterFinalDigit='yes'">
                    <xsl:text>.</xsl:text>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoTablenumberedRef
    -->
    <xsl:template name="DoTablenumberedRef">
        <xsl:variable name="table" select="id(@table)"/>
        <xsl:choose>
            <xsl:when test="@showCaption='short'">
                <xsl:call-template name="DoFormatLayoutInfoTextBefore">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($contentLayoutInfo)/tablenumberedRefCaptionLayout"/>
                </xsl:call-template>
                <xsl:choose>
                    <xsl:when test="exsl:node-set($table)/shortCaption and string-length(exsl:node-set($table)/shortCaption) &gt; 0">
                        <xsl:apply-templates select="exsl:node-set($table)/shortCaption/child::node()[name()!='endnote']"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:apply-templates select="exsl:node-set($table)/table/caption/child::node()[name()!='endnote']"/>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($contentLayoutInfo)/tablenumberedRefCaptionLayout"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="@showCaption='full'">
                <xsl:call-template name="DoFormatLayoutInfoTextBefore">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($contentLayoutInfo)/tablenumberedRefCaptionLayout"/>
                </xsl:call-template>
                <xsl:apply-templates select="exsl:node-set($table)/table/caption/child::node()[name()!='endnote']"/>
                <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                    <xsl:with-param name="layoutInfo" select="exsl:node-set($contentLayoutInfo)/tablenumberedRefCaptionLayout"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <!--                <xsl:apply-templates select="$table" mode="tablenumbered"/>-->
                <xsl:call-template name="GetTableNumberedNumber">
                    <xsl:with-param name="tablenumbered" select="$table"/>
                </xsl:call-template>

            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoUrlDateAccessedLayout
    -->
    <xsl:template name="DoUrlDateAccessedLayout">
        <xsl:param name="reference"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($reference)/url and exsl:node-set($reference)/dateAccessed and exsl:node-set($reference)/doi">
                <xsl:for-each select="exsl:node-set($urlDateAccessedLayouts)/*[urlItem and dateAccessedItem and doiItem]">
                    <xsl:for-each select="*">
                        <xsl:choose>
                            <xsl:when test="name(.)='urlItem'">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($reference)/url"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='dateAccessedItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="normalize-space(exsl:node-set($reference)/dateAccessed)"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='doiItem'">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($reference)/doi"/>
                                </xsl:call-template>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:when>
            <xsl:when test="exsl:node-set($reference)/url and exsl:node-set($reference)/dateAccessed and not(exsl:node-set($reference)/doi)">
                <xsl:for-each select="exsl:node-set($urlDateAccessedLayouts)/*[urlItem and dateAccessedItem and not(doiItem)]">
                    <xsl:for-each select="*">
                        <xsl:choose>
                            <xsl:when test="name(.)='urlItem'">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($reference)/url"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='dateAccessedItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="normalize-space(exsl:node-set($reference)/dateAccessed)"/>
                                </xsl:call-template>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:when>
            <xsl:when test="exsl:node-set($reference)/url and not(exsl:node-set($reference)/dateAccessed) and exsl:node-set($reference)/doi">
                <xsl:for-each select="exsl:node-set($urlDateAccessedLayouts)/*[urlItem and not(dateAccessedItem) and doiItem]">
                    <xsl:for-each select="*">
                        <xsl:choose>
                            <xsl:when test="name()='urlItem'">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($reference)/url"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name()='doiItem'">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($reference)/doi"/>
                                </xsl:call-template>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:when>
            <xsl:when test="exsl:node-set($reference)/dateAccessed and not(exsl:node-set($reference)/url) and exsl:node-set($reference)/doi">
                <xsl:for-each select="exsl:node-set($urlDateAccessedLayouts)/*[not(urlItem) and dateAccessedItem and doiItem]">
                    <xsl:for-each select="*">
                        <xsl:choose>
                            <xsl:when test="name()='dateAccessedItem'">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($reference)/dateAccessed"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name()='doiItem'">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($reference)/doi"/>
                                </xsl:call-template>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:when>
            <xsl:when test="exsl:node-set($reference)/url and not(exsl:node-set($reference)/dateAccessed) and not(exsl:node-set($reference)/doi)">
                <xsl:for-each select="exsl:node-set($urlDateAccessedLayouts)/*[urlItem and not(dateAccessedItem) and not(doiItem)]">
                    <xsl:for-each select="*">
                        <xsl:call-template name="OutputReferenceItemNode">
                            <xsl:with-param name="item" select="exsl:node-set($reference)/url"/>
                        </xsl:call-template>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:when>
            <xsl:when test="exsl:node-set($reference)/doi and not(exsl:node-set($reference)/url) and not(exsl:node-set($reference)/dateAccessed)">
                <xsl:for-each select="exsl:node-set($urlDateAccessedLayouts)/*[doiItem and not(urlItem) and not(dateAccessedItem)]">
                    <xsl:for-each select="*">
                        <xsl:call-template name="OutputReferenceItemNode">
                            <xsl:with-param name="item" select="exsl:node-set($reference)/doi"/>
                        </xsl:call-template>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:when>
            <xsl:when test="not(exsl:node-set($reference)/url) and exsl:node-set($reference)/dateAccessed and not(exsl:node-set($reference)/doi)">
                <xsl:for-each select="exsl:node-set($urlDateAccessedLayouts)/*[not(urlItem) and dateAccessedItem]">
                    <xsl:for-each select="*">
                        <xsl:call-template name="OutputReferenceItem">
                            <xsl:with-param name="item" select="exsl:node-set($reference)/dateAccessed"/>
                        </xsl:call-template>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoWebPageLayout
    -->
    <xsl:template name="DoWebPageLayout">
        <xsl:variable name="webPage" select="."/>
        <xsl:variable name="work" select=".."/>
        <xsl:variable name="webPageLayoutToUsePosition">
            <xsl:call-template name="GetWebPageLayoutToUsePosition"/>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$webPageLayoutToUsePosition=0 or string-length($webPageLayoutToUsePosition)=0">
                <xsl:call-template name="ReportNoPatternMatched"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/webPageLayouts/*[position()=$webPageLayoutToUsePosition]">
                    <xsl:for-each select="*">
                        <xsl:choose>
                            <xsl:when test="name(.)='refTitleItem' and string-length(exsl:node-set($work)/refTitle) &gt; 0">
                                <xsl:call-template name="OutputReferenceItemNode">
                                    <xsl:with-param name="item" select="exsl:node-set($work)/refTitle"/>
                                </xsl:call-template>
                                <xsl:if test="exsl:node-set($work)/../@showAuthorName='no'">
                                    <xsl:call-template name="DoDateLayout">
                                        <xsl:with-param name="refDateItem" select="ancestor::referencesLayout/refAuthorLayouts/refAuthorLayout[position()=last()]/refDateItem"/>
                                        <xsl:with-param name="work" select="$work"/>
                                    </xsl:call-template>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name(.)='editionItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($webPage)/edition"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='locationItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($webPage)/location"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='institutionItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($webPage)/institution"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='publisherItem'">
                                <xsl:call-template name="OutputReferenceItem">
                                    <xsl:with-param name="item" select="exsl:node-set($webPage)/publisher"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem' and name(following-sibling::*[2])='doiItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$webPage"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[2])='urlItem' and name(preceding-sibling::*[1])='dateAccessedItem' and name(.)='doi'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem' and name(following-sibling::*[1])='dateAccessedItem'">
                                <xsl:call-template name="HandleUrlAndDateAccessedLayouts">
                                    <xsl:with-param name="typeOfWork" select="$webPage"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(preceding-sibling::*[1])='urlItem' and name(.)='dateAccessedItem'">
                                <!-- do nothing; was handled above -->
                            </xsl:when>
                            <xsl:when test="name(.)='urlItem'">
                                <xsl:call-template name="HandleUrlLayout">
                                    <xsl:with-param name="kindOfWork" select="$webPage"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='dateAccessedItem'">
                                <xsl:call-template name="HandleDateAccessedLayout">
                                    <xsl:with-param name="kindOfWork" select="$webPage"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='doiItem'">
                                <xsl:call-template name="HandleDoiLayout">
                                    <xsl:with-param name="kindOfWork" select="$webPage"/>
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='urlDateAccessedLayoutsRef'">
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="$webPage"/>
                                </xsl:call-template>
                                <xsl:call-template name="DoUrlDateAccessedLayout">
                                    <xsl:with-param name="reference" select="exsl:node-set($webPage)/.."/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:when test="name(.)='iso639-3codeItemRef'">
                                <xsl:call-template name="DoISO639-3Codes">
                                    <xsl:with-param name="work" select="$work"/>
                                </xsl:call-template>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        FleshOutRefCitation
    -->
    <xsl:template name="FleshOutRefCitation">
        <xsl:param name="citation"/>
        <xsl:param name="citationLayout"/>
        <xsl:variable name="citedWork" select="key('RefWorkID',exsl:node-set($citation)/@refToBook)"/>
        <xsl:call-template name="ConvertLastNameFirstNameToFirstNameLastName">
            <xsl:with-param name="sCitedWorkAuthor" select="exsl:node-set($citedWork)/../@name"/>
        </xsl:call-template>
        <xsl:choose>
            <xsl:when test="name($citation)='collCitation'">
                <xsl:call-template name="DoCitedCollectionLayout">
                    <xsl:with-param name="book" select="exsl:node-set($citedWork)/book"/>
                    <xsl:with-param name="citation" select="$citation"/>
                    <xsl:with-param name="citationLayout" select="$citationLayout"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="DoCitedProceedingsLayout">
                    <xsl:with-param name="book" select="exsl:node-set($citedWork)/book"/>
                    <xsl:with-param name="citation" select="$citation"/>
                    <xsl:with-param name="citationLayout" select="$citationLayout"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetAndFormatExampleNumber
    -->
    <xsl:template name="GetAndFormatExampleNumber">
        <xsl:if test="exsl:node-set($contentLayoutInfo)/exampleLayout/@numberProperUseParens!='no'">
            <xsl:text>(</xsl:text>
        </xsl:if>
        <xsl:call-template name="GetExampleNumber">
            <xsl:with-param name="example" select="."/>
        </xsl:call-template>
        <xsl:if test="exsl:node-set($contentLayoutInfo)/exampleLayout/@numberProperAddPeriodAfterFinalDigit='yes'">
            <xsl:text>.</xsl:text>
        </xsl:if>
        <xsl:if test="exsl:node-set($contentLayoutInfo)/exampleLayout/@numberProperUseParens!='no'">
            <xsl:text>)</xsl:text>
        </xsl:if>
    </xsl:template>
    <!--  
        GetArticleLayoutToUsePosition
    -->
    <xsl:template name="GetArticleLayoutToUsePosition">
        <xsl:variable name="sOptionsPresent">
            <!-- for each possible option, in order, set it to 'y' if present, otherwise 'n' -->
            <!-- first, indicate that the required refTitle is present -->
            <xsl:text>y</xsl:text>
            <xsl:choose>
                <xsl:when test="jTitle">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="jVol">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="jIssueNumber">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="jPages">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="jArticleNumber">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="location or publisher">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="GetUrlEtcLayoutToUseInfo"/>
            <xsl:choose>
                <xsl:when test="reprintInfo">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="sPosition">
            <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/articleLayouts/*">
                <xsl:variable name="sItemsWhichMatchOptions">
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='y' and refTitleItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='n' and not(refTitleItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='y' and jTitleItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='n' and not(jTitleItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='y' and jVolItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='n' and not(jVolItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 4, 1)='y' and jIssueNumberItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 4, 1)='n' and not(jIssueNumberItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 5, 1)='y' and jPagesItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 5, 1)='n' and not(jPagesItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 6, 1)='y' and jArticleNumberItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 6, 1)='n' and not(jArticleNumberItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:call-template name="DetermineIfLocationPublisherMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="locationPublisherPos">7</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfUrlMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="urlPos">8</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDateAccessedMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="dateAccessedPos">9</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDoiMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="doiPos">10</xsl:with-param>
                    </xsl:call-template>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 12, 1)='y' and reprintInfoItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 12, 1)='n' and not(reprintInfoItem)">x</xsl:when>
                    </xsl:choose>
                    <!--                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent,10, 1)='y' and iso639-3codeItemRef">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent,10, 1)='n' and not(iso639-3codeItemRef)">x</xsl:when>
                    </xsl:choose>
-->
                    <!-- now we always set the x for the ISO whether the pattern is there or not; it all comes out in the wash -->
                    <xsl:text>x</xsl:text>
                </xsl:variable>
                <xsl:if test="string-length($sItemsWhichMatchOptions) = 12">
                    <xsl:call-template name="RecordPosition"/>
                </xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:value-of select="substring-before($sPosition,';')"/>
    </xsl:template>
    <!--  
        GetAuthorLayoutToUsePosition
    -->
    <xsl:template name="GetAuthorLayoutToUsePosition">
        <xsl:param name="referencesLayoutInfo"/>
        <xsl:variable name="sPosition">
            <xsl:choose>
                <xsl:when test="authorRole">
                    <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/refAuthorLayouts/*">
                        <xsl:if test="authorRoleItem">
                            <xsl:call-template name="RecordPosition"/>
                        </xsl:if>
                    </xsl:for-each>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/refAuthorLayouts/*">
                        <xsl:if test="not(authorRoleItem) and not(name()='comment')">
                            <xsl:call-template name="RecordPosition"/>
                        </xsl:if>
                    </xsl:for-each>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:value-of select="substring-before($sPosition,';')"/>
    </xsl:template>
    <!--  
        GetBestHangingIndentInitialIndent
    -->
    <xsl:template name="GetBestHangingIndentInitialIndent">
        <xsl:param name="sThisHangingIndent"/>
        <xsl:param name="sThisInitialIndent"/>
        <xsl:variable name="sValue" select="substring($sThisInitialIndent,1,string-length($sThisHangingIndent)-2)"/>
        <xsl:choose>
            <xsl:when test="$sValue=0">
                <xsl:call-template name="GetHangingIndentNormalIndent">
                    <xsl:with-param name="sThisHangingIndent" select="$sThisHangingIndent"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sThisInitialIndent"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        GetBestLangDataLayout
    -->
    <xsl:template name="GetBestLangDataLayout">
        <xsl:variable name="sThisLang">
            <xsl:value-of select="@lang"/>
        </xsl:variable>
        <xsl:variable name="layoutSpecificToThisLanguage" select="exsl:node-set($contentLayoutInfo)/langDataLayout[@language=$sThisLang]"/>
        <xsl:variable name="firstLayout" select="exsl:node-set($contentLayoutInfo)/langDataLayout[1]"/>
        <xsl:choose>
            <xsl:when test="$layoutSpecificToThisLanguage">
                <xsl:copy-of select="$layoutSpecificToThisLanguage"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:copy-of select="$firstLayout"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetBookLayoutToUsePosition
    -->
    <xsl:template name="GetBookLayoutToUsePosition">
        <xsl:variable name="sOptionsPresent">
            <!-- for each possible option, in order, set it to 'y' if present, otherwise 'n' -->
            <!-- first, indicate that the required refTitle is present -->
            <xsl:text>y</xsl:text>
            <xsl:choose>
                <xsl:when test="translatedBy">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="editor">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="edition">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="seriesEd">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="series">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="bVol">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="multivolumeWork">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="bookTotalPages">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="location or publisher">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="GetUrlEtcLayoutToUseInfo"/>
            <xsl:choose>
                <xsl:when test="reprintInfo">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="sPosition">
            <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/bookLayouts/*">
                <xsl:variable name="sItemsWhichMatchOptions">
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='y' and refTitleItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='n' and not(refTitleItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='y' and translatedByItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='n' and not(translatedByItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='y' and editorItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='n' and not(editorItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 4, 1)='y' and editionItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 4, 1)='n' and not(editionItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 5, 1)='y' and seriesEdItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 5, 1)='n' and not(seriesEdItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 6, 1)='y' and seriesItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 6, 1)='n' and not(seriesItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 7, 1)='y' and bVolItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 7, 1)='n' and not(bVolItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 8, 1)='y' and multivolumeWorkItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 8, 1)='n' and not(multivolumeWorkItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 9, 1)='y' and bookTotalPagesItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 9, 1)='n' and not(bookTotalPagesItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:call-template name="DetermineIfLocationPublisherMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="locationPublisherPos">10</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfUrlMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="urlPos">11</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDateAccessedMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="dateAccessedPos">12</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDoiMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="doiPos">13</xsl:with-param>
                    </xsl:call-template>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 15, 1)='y' and reprintInfoItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 15, 1)='n' and not(reprintInfoItem)">x</xsl:when>
                    </xsl:choose>
                    <!--<xsl:choose>
                        <xsl:when test="substring($sOptionsPresent,11, 1)='y' and iso639-3codeItemRef">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent,11, 1)='n' and not(iso639-3codeItemRef)">x</xsl:when>
                    </xsl:choose>-->
                    <!-- now we always set the x for the ISO whether the pattern is there or not; it all comes out in the wash -->
                    <xsl:text>x</xsl:text>
                </xsl:variable>
                <xsl:if test="string-length($sItemsWhichMatchOptions) = 15">
                    <xsl:call-template name="RecordPosition"/>
                </xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:value-of select="substring-before($sPosition,';')"/>
    </xsl:template>
    <!--  
        GetCitedCollectionLayoutToUsePosition
    -->
    <xsl:template name="GetCitedCollectionLayoutToUsePosition">
        <xsl:param name="collCitation"/>
        <xsl:variable name="sOptionsPresent">
            <!-- for each possible option, in order, set it to 'y' if present, otherwise 'n' -->
            <xsl:choose>
                <xsl:when test="../authorRole">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="../refTitle">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="bVol">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="string-length(normalize-space(exsl:node-set($collCitation)/@page)) &gt; 0">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="seriesEd">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="series">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="location or publisher">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="GetUrlEtcLayoutToUseInfo"/>
            <xsl:choose>
                <xsl:when test="edition">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="reprintInfo">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="sPosition">
            <xsl:variable name="refWork" select="."/>
            <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/collectionLayouts/*">
                <xsl:variable name="sItemsWhichMatchOptions">
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='y' and collEdItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='n' and not(collEdItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='y' and collTitleItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='n' and not(collTitleItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='y' and collVolItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='n' and not(collVolItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 4, 1)='y' and collPagesItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 4, 1)='n' and not(collPagesItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 5, 1)='y' and seriesEdItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 5, 1)='n' and not(seriesEdItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 6, 1)='y' and seriesItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 6, 1)='n' and not(seriesItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:call-template name="DetermineIfLocationPublisherMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="locationPublisherPos">7</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfUrlMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="urlPos">8</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDateAccessedMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="dateAccessedPos">9</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDoiMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="doiPos">10</xsl:with-param>
                    </xsl:call-template>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 12, 1)='y' and editionItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 12, 1)='n' and not(editionItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 13, 1)='y' and reprintInfoItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 13, 1)='n' and not(reprintInfoItem)">x</xsl:when>
                    </xsl:choose>
                    <!--<xsl:choose>
                        <xsl:when test="substring($sOptionsPresent,10, 1)='y' and iso639-3codeItemRef">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent,10, 1)='n' and not(iso639-3codeItemRef)">x</xsl:when>
                        </xsl:choose>-->
                    <!-- now we always set the x for the ISO whether the pattern is there or not; it all comes out in the wash -->
                    <xsl:text>x</xsl:text>
                </xsl:variable>
                <xsl:if test="string-length($sItemsWhichMatchOptions) = 13">
                    <xsl:call-template name="RecordPosition"/>
                </xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:value-of select="substring-before($sPosition,';')"/>
    </xsl:template>
    <!--  
        GetCitedProceedingsLayoutToUsePosition
    -->
    <xsl:template name="GetCitedProceedingsLayoutToUsePosition">
        <xsl:param name="procCitation"/>
        <xsl:variable name="sOptionsPresent">
            <!-- for each possible option, in order, set it to 'y' if present, otherwise 'n' -->
            <xsl:choose>
                <xsl:when test="../authorRole">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="../refTitle">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="bVol">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="string-length(normalize-space(exsl:node-set($procCitation)/@page)) &gt; 0">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="location or publisher">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="GetUrlEtcLayoutToUseInfo"/>
            <xsl:choose>
                <xsl:when test="reprintInfo">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="sPosition">
            <xsl:variable name="refWork" select="."/>
            <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/proceedingsLayouts/*">
                <xsl:variable name="sItemsWhichMatchOptions">
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='y' and procEdItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='n' and not(procEdItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='y' and procTitleItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='n' and not(procTitleItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='y' and procVolItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='n' and not(procVolItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 4, 1)='y' and procPagesItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 4, 1)='n' and not(procPagesItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:call-template name="DetermineIfLocationPublisherMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="locationPublisherPos">5</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfUrlMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="urlPos">6</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDateAccessedMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="dateAccessedPos">7</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDoiMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="doiPos">8</xsl:with-param>
                    </xsl:call-template>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 10, 1)='y' and reprintInfoItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 10, 1)='n' and not(reprintInfoItem)">x</xsl:when>
                    </xsl:choose>
                    <!--                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 8, 1)='y' and iso639-3codeItemRef">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 8, 1)='n' and not(iso639-3codeItemRef)">x</xsl:when>
                        </xsl:choose>-->
                    <!-- now we always set the x for the ISO whether the pattern is there or not; it all comes out in the wash -->
                    <xsl:text>x</xsl:text>
                </xsl:variable>
                <xsl:if test="string-length($sItemsWhichMatchOptions) = 10">
                    <xsl:call-template name="RecordPosition"/>
                </xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:value-of select="substring-before($sPosition,';')"/>
    </xsl:template>
    <!--  
        GetCollectionLayoutToUsePosition
    -->
    <xsl:template name="GetCollectionLayoutToUsePosition">
        <xsl:variable name="sOptionsPresent">
            <!-- for each possible option, in order, set it to 'y' if present, otherwise 'n' -->
            <!-- first, indicate that the required refTitle is present -->
            <xsl:text>y</xsl:text>
            <xsl:choose>
                <xsl:when test="collEd">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="collTitle">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="collVol">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="collPages">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="seriesEd">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="series">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="bVol">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="multivolumeWork">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="location or publisher">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="collCitation">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="GetUrlEtcLayoutToUseInfo"/>
            <xsl:choose>
                <xsl:when test="key('RefWorkID',collCitation/@refToBook)/authorRole">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="edition">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="reprintInfo">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="sPosition">
            <xsl:variable name="refWork" select="."/>
            <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/collectionLayouts/*">
                <xsl:variable name="sItemsWhichMatchOptions">
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='y' and refTitleItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='n' and not(refTitleItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='y' and collEdItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='n' and not(collEdItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='y' and collTitleItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='n' and not(collTitleItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 4, 1)='y' and collVolItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 4, 1)='n' and not(collVolItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 5, 1)='y' and collPagesItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 5, 1)='n' and not(collPagesItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 6, 1)='y' and seriesEdItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 6, 1)='n' and not(seriesEdItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 7, 1)='y' and seriesItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 7, 1)='n' and not(seriesItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 8, 1)='y' and bVolItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 8, 1)='n' and not(bVolItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 9, 1)='y' and multivolumeWorkItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 9, 1)='n' and not(multivolumeWorkItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:call-template name="DetermineIfLocationPublisherMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="locationPublisherPos">10</xsl:with-param>
                    </xsl:call-template>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent,11, 1)='y' and collCitationItem">
                            <xsl:choose>
                                <xsl:when test="substring($sOptionsPresent, 5, 1)='n' and collPagesItem and string-length(normalize-space(exsl:node-set($refWork)/collCitation/@page)) &gt; 0">xx</xsl:when>
                                <xsl:otherwise>x</xsl:otherwise>
                            </xsl:choose>
                        </xsl:when>
                        <xsl:when test="substring($sOptionsPresent,11, 1)='n' and not(collCitationItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:call-template name="DetermineIfUrlMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="urlPos">12</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDateAccessedMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="dateAccessedPos">13</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDoiMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="doiPos">14</xsl:with-param>
                    </xsl:call-template>
                    <!--<xsl:choose>
                        <xsl:when test="substring($sOptionsPresent,13, 1)='y' and iso639-3codeItemRef">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent,13, 1)='n' and not(iso639-3codeItemRef)">x</xsl:when>
                        </xsl:choose>-->
                    <!-- now we always set the x for the ISO whether the pattern is there or not; it all comes out in the wash -->
                    <xsl:text>x</xsl:text>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent,16, 1)='y' and authorRoleItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent,16, 1)='n' and not(authorRoleItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 17, 1)='y' and editionItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 17, 1)='n' and not(editionItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 18, 1)='y' and reprintInfoItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 18, 1)='n' and not(reprintInfoItem)">x</xsl:when>
                    </xsl:choose>
                </xsl:variable>
                <!--                <xsl:variable name="iLen" select="string-length($sItemsWhichMatchOptions)"/>-->
                <xsl:if test="string-length($sItemsWhichMatchOptions) = 18">
                    <xsl:call-template name="RecordPosition"/>
                </xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:value-of select="substring-before($sPosition,';')"/>
    </xsl:template>
    <!--  
        GetContentsLevelToUse
    -->
    <xsl:template name="GetContentsLevelToUse">
        <xsl:param name="contentsLayoutToUse"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($contentsLayoutToUse)[ancestor-or-self::backMatterLayout]">
                <xsl:value-of select="$nBackMatterLevel"/>
            </xsl:when>
            <xsl:when test="name(.)='contents'">
                <xsl:value-of select="@showLevel"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$nLevel"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetContextOfItem
    -->
    <xsl:template name="GetContextOfItem">
        <xsl:variable name="closestRelevantAncestor" select="ancestor::*[name()='endnote' or name()='listWord' or name()='word' or name()='example' or name()='table' or name()='interlinear-text' or name()='annotation' or name()='refAuthor'][1]"/>
        <xsl:choose>
            <xsl:when test="name()='gloss' and name($closestRelevantAncestor)='listWord' or name()='gloss' and name($closestRelevantAncestor)='word'">
                <xsl:choose>
                    <xsl:when test="exsl:node-set($contentLayoutInfo)/glossLayout/glossInListWordLayout">
                        <xsl:text>listWord</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>example</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="name()='abbrRef' and name($closestRelevantAncestor)='listWord' or name()='abbrRef' and name($closestRelevantAncestor)='word'">
                <xsl:choose>
                    <xsl:when test="exsl:node-set($contentLayoutInfo)/glossLayout/glossInListWordLayout">
                        <xsl:text>listWord</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>example</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="name($closestRelevantAncestor)='listWord' or name($closestRelevantAncestor)='word'">
                <xsl:text>example</xsl:text>
            </xsl:when>
            <xsl:when test="name($closestRelevantAncestor)='example' or name($closestRelevantAncestor)='interlinear-text'">
                <xsl:choose>
                    <xsl:when test="ancestor::exampleHeading">
                        <xsl:text>prose</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>example</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="name($closestRelevantAncestor)='table'">
                <xsl:text>table</xsl:text>
            </xsl:when>
            <xsl:when test="name($closestRelevantAncestor)='refAuthor'">
                <xsl:text>reference</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>prose</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetDissertationLayoutToUsePosition
    -->
    <xsl:template name="GetDissertationLayoutToUsePosition">
        <xsl:param name="layout"/>
        <xsl:variable name="sOptionsPresent">
            <!-- for each possible option, in order, set it to 'y' if present, otherwise 'n' -->
            <!-- first, indicate that the required refTitle is present -->
            <xsl:text>y</xsl:text>
            <xsl:choose>
                <xsl:when test="location">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <!-- indicate that the implied dissertation/thesis label is present -->
            <xsl:text>y</xsl:text>
            <xsl:choose>
                <xsl:when test="institution">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="published">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="GetUrlEtcLayoutToUseInfo"/>
            <xsl:choose>
                <xsl:when test="reprintInfo">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="sPosition">
            <xsl:for-each select="exsl:node-set($layout)/*">
                <xsl:variable name="sItemsWhichMatchOptions">
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='y' and refTitleItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='n' and not(refTitleItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='y' and locationItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='n' and not(locationItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='y' and dissertationLabelItem or substring($sOptionsPresent, 3, 1)='y' and thesisLabelItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='n' and not(dissertationLabelItem) and not(thesisLabelItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 4, 1)='y' and institutionItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 4, 1)='n' and not(institutionItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 5, 1)='y' and publishedLayoutRef">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 5, 1)='n' and not(publishedLayoutRef)">x</xsl:when>
                    </xsl:choose>
                    <xsl:call-template name="DetermineIfUrlMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="urlPos">6</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDateAccessedMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="dateAccessedPos">7</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDoiMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="doiPos">8</xsl:with-param>
                    </xsl:call-template>
                    <!--<xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 8, 1)='y' and iso639-3codeItemRef">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 8, 1)='n' and not(iso639-3codeItemRef)">x</xsl:when>
                        </xsl:choose>-->
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 10, 1)='y' and reprintInfoItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 10, 1)='n' and not(reprintInfoItem)">x</xsl:when>
                    </xsl:choose>
                    <!-- now we always set the x for the ISO whether the pattern is there or not; it all comes out in the wash -->
                    <xsl:text>x</xsl:text>
                </xsl:variable>
                <xsl:if test="string-length($sItemsWhichMatchOptions) = 10">
                    <xsl:call-template name="RecordPosition"/>
                </xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:value-of select="substring-before($sPosition,';')"/>
    </xsl:template>
    <!--  
     GetFieldNotesLayoutToUsePosition
   -->
    <xsl:template name="GetFieldNotesLayoutToUsePosition">
        <xsl:variable name="sOptionsPresent">
            <!-- for each possible option, in order, set it to 'y' if present, otherwise 'n' -->
            <!-- first, indicate that the required refTitle is present -->
            <xsl:text>y</xsl:text>
            <xsl:choose>
                <xsl:when test="location">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="institution">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="GetUrlEtcLayoutToUseInfo"/>
        </xsl:variable>
        <xsl:variable name="sPosition">
            <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/fieldNotesLayouts/*">
                <xsl:variable name="sItemsWhichMatchOptions">
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='y' and refTitleItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='n' and not(refTitleItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='y' and locationItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='n' and not(locationItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='y' and institutionItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='n' and not(institutionItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:call-template name="DetermineIfUrlMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="urlPos">4</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDateAccessedMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="dateAccessedPos">5</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDoiMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="doiPos">6</xsl:with-param>
                    </xsl:call-template>
                    <!--<xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 6, 1)='y' and iso639-3codeItemRef">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 6, 1)='n' and not(iso639-3codeItemRef)">x</xsl:when>
                        </xsl:choose>-->
                    <!-- now we always set the x for the ISO whether the pattern is there or not; it all comes out in the wash -->
                    <xsl:text>x</xsl:text>
                </xsl:variable>
                <xsl:if test="string-length($sItemsWhichMatchOptions) = 7">
                    <xsl:call-template name="RecordPosition"/>
                </xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:value-of select="substring-before($sPosition,';')"/>
    </xsl:template>
    <!--  
        GetFormattedPageNumbers
    -->
    <xsl:template name="GetFormattedPageNumbers">
        <xsl:param name="normalizedPages"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($referencesLayoutInfo)/@removecommonhundredsdigitsinpages='yes'">
                <xsl:variable name="sSeparator" select="normalize-space(exsl:node-set($references)/@pageRangeSeparator)"/>
                <xsl:choose>
                    <xsl:when test="string-length($sSeparator) &gt; 0">
                        <xsl:call-template name="AdjustPageNumbers">
                            <xsl:with-param name="normalizedPages" select="$normalizedPages"/>
                            <xsl:with-param name="sSeparator" select="$sSeparator"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="AdjustPageNumbers">
                            <xsl:with-param name="normalizedPages" select="$normalizedPages"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$normalizedPages"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetHangingIndentNormalIndent
    -->
    <xsl:template name="GetHangingIndentNormalIndent">
        <xsl:param name="sThisHangingIndent"/>
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
    </xsl:template>
    <!--  
      GetMsLayoutToUsePosition
   -->
    <xsl:template name="GetMsLayoutToUsePosition">
        <xsl:variable name="sOptionsPresent">
            <!-- for each possible option, in order, set it to 'y' if present, otherwise 'n' -->
            <!-- first, indicate that the required refTitle is present -->
            <xsl:text>y</xsl:text>
            <xsl:choose>
                <xsl:when test="location">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="institution">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="empty">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="msVersion">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="GetUrlEtcLayoutToUseInfo"/>
        </xsl:variable>
        <xsl:variable name="sPosition">
            <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/msLayouts/*">
                <xsl:variable name="sItemsWhichMatchOptions">
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='y' and refTitleItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='n' and not(refTitleItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='y' and locationItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='n' and not(locationItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='y' and institutionItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='n' and not(institutionItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 4, 1)='y' and emptyItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 4, 1)='n' and not(emptyItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 5, 1)='y' and msVersionItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 5, 1)='n' and not(msVersionItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:call-template name="DetermineIfUrlMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="urlPos">6</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDateAccessedMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="dateAccessedPos">7</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDoiMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="doiPos">8</xsl:with-param>
                    </xsl:call-template>
                    <!--<xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 6, 1)='y' and iso639-3codeItemRef">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 6, 1)='n' and not(iso639-3codeItemRef)">x</xsl:when>
                        </xsl:choose>-->
                    <!-- now we always set the x for the ISO whether the pattern is there or not; it all comes out in the wash -->
                    <xsl:text>x</xsl:text>
                </xsl:variable>
                <xsl:if test="string-length($sItemsWhichMatchOptions) = 9">
                    <xsl:call-template name="RecordPosition"/>
                </xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:value-of select="substring-before($sPosition,';')"/>
    </xsl:template>
    <!--  
        GetPaperLayoutToUsePosition
    -->
    <xsl:template name="GetPaperLayoutToUsePosition">
        <xsl:variable name="sOptionsPresent">
            <!-- for each possible option, in order, set it to 'y' if present, otherwise 'n' -->
            <!-- first, indicate that the required refTitle is present -->
            <xsl:text>y</xsl:text>
            <!-- indicate that the implied paper label is present -->
            <xsl:text>y</xsl:text>
            <xsl:choose>
                <xsl:when test="conference">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="location">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="GetUrlEtcLayoutToUseInfo"/>
        </xsl:variable>
        <xsl:variable name="sPosition">
            <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/paperLayouts/*">
                <xsl:variable name="sItemsWhichMatchOptions">
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='y' and refTitleItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='n' and not(refTitleItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='y' and paperLabelItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='y' and not(paperLabelItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='y' and conferenceItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='n' and not(conferenceItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 4, 1)='y' and locationItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 4, 1)='n' and not(locationItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:call-template name="DetermineIfUrlMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="urlPos">5</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDateAccessedMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="dateAccessedPos">6</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDoiMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="doiPos">7</xsl:with-param>
                    </xsl:call-template>
                    <!--<xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 6, 1)='y' and iso639-3codeItemRef">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 6, 1)='n' and not(iso639-3codeItemRef)">x</xsl:when>
                        </xsl:choose>-->
                    <!-- now we always set the x for the ISO whether the pattern is there or not; it all comes out in the wash -->
                    <xsl:text>x</xsl:text>
                </xsl:variable>
                <xsl:if test="string-length($sItemsWhichMatchOptions) = 8">
                    <xsl:call-template name="RecordPosition"/>
                </xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:value-of select="substring-before($sPosition,';')"/>
    </xsl:template>
    <!--  
        GetProceedingsLayoutToUsePosition
    -->
    <xsl:template name="GetProceedingsLayoutToUsePosition">
        <xsl:variable name="sOptionsPresent">
            <!-- for each possible option, in order, set it to 'y' if present, otherwise 'n' -->
            <!-- first, indicate that the required refTitle is present -->
            <xsl:text>y</xsl:text>
            <xsl:choose>
                <xsl:when test="procEd">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="procTitle">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="procVol">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="procPages">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="seriesEd">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="series">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="bVol">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="multivolumeWork">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="location or publisher">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="procCitation">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="GetUrlEtcLayoutToUseInfo"/>
            <xsl:choose>
                <xsl:when test="reprintInfo">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="sPosition">
            <xsl:variable name="refWork" select="."/>
            <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/proceedingsLayouts/*">
                <xsl:variable name="sItemsWhichMatchOptions">
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='y' and refTitleItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='n' and not(refTitleItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='y' and procEdItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='n' and not(procEdItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='y' and procTitleItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='n' and not(procTitleItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 4, 1)='y' and procVolItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 4, 1)='n' and not(procVolItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 5, 1)='y' and procPagesItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 5, 1)='n' and not(procPagesItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 6, 1)='y' and seriesEdItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 6, 1)='n' and not(seriesEdItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 7, 1)='y' and seriesItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 7, 1)='n' and not(seriesItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 8, 1)='y' and bVolItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 8, 1)='n' and not(bVolItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 9, 1)='y' and multivolumeWorkItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 9, 1)='n' and not(multivolumeWorkItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:call-template name="DetermineIfLocationPublisherMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="locationPublisherPos">10</xsl:with-param>
                    </xsl:call-template>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 11, 1)='y' and procCitationItem">
                            <xsl:choose>
                                <xsl:when test="substring($sOptionsPresent, 5, 1)='n' and procPagesItem and string-length(normalize-space(exsl:node-set($refWork)/procCitation/@page)) &gt; 0">xx</xsl:when>
                                <xsl:otherwise>x</xsl:otherwise>
                            </xsl:choose>
                        </xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 11, 1)='n' and not(procCitationItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:call-template name="DetermineIfUrlMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="urlPos">12</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDateAccessedMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="dateAccessedPos">13</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDoiMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="doiPos">14</xsl:with-param>
                    </xsl:call-template>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 16, 1)='y' and reprintInfoItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 16, 1)='n' and not(reprintInfoItem)">x</xsl:when>
                    </xsl:choose>
                    <!--<xsl:choose>
                        <xsl:when test="substring($sOptionsPresent,10, 1)='y' and iso639-3codeItemRef">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent,10, 1)='n' and not(iso639-3codeItemRef)">x</xsl:when>
                        </xsl:choose>-->
                    <!-- now we always set the x for the ISO whether the pattern is there or not; it all comes out in the wash -->
                    <xsl:text>x</xsl:text>
                </xsl:variable>
                <xsl:if test="string-length($sItemsWhichMatchOptions) = 16">
                    <xsl:call-template name="RecordPosition"/>
                </xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:value-of select="substring-before($sPosition,';')"/>
    </xsl:template>
    <!--  
        GetSectionRefToUse
    -->
    <xsl:template name="GetSectionRefToUse">
        <xsl:param name="section"/>
        <xsl:choose>
            <xsl:when test="name($section)='section1' or contains(name($section),'chapter') or name($section)='part'">
                <!-- just use section1, chapter, and part;   if section1 is being ignored, that's the style sheet's problem... -->
                <xsl:value-of select="exsl:node-set($section)/@id"/>
            </xsl:when>
            <xsl:when test="name($section)='section2'">
                <xsl:call-template name="TrySectionRef">
                    <xsl:with-param name="section" select="$section"/>
                    <xsl:with-param name="sectionLayoutInfo" select="exsl:node-set($bodyLayoutInfo)/section2Layout"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="name($section)='section3'">
                <xsl:call-template name="TrySectionRef">
                    <xsl:with-param name="section" select="$section"/>
                    <xsl:with-param name="sectionLayoutInfo" select="exsl:node-set($bodyLayoutInfo)/section3Layout"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="name($section)='section4'">
                <xsl:call-template name="TrySectionRef">
                    <xsl:with-param name="section" select="$section"/>
                    <xsl:with-param name="sectionLayoutInfo" select="exsl:node-set($bodyLayoutInfo)/section4Layout"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="name($section)='section5'">
                <xsl:call-template name="TrySectionRef">
                    <xsl:with-param name="section" select="$section"/>
                    <xsl:with-param name="sectionLayoutInfo" select="exsl:node-set($bodyLayoutInfo)/section5Layout"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="name($section)='section6'">
                <xsl:call-template name="TrySectionRef">
                    <xsl:with-param name="section" select="$section"/>
                    <xsl:with-param name="sectionLayoutInfo" select="exsl:node-set($bodyLayoutInfo)/section6Layout"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetTextBetweenKeywords
    -->
    <xsl:template name="GetTextBetweenKeywords">
        <xsl:param name="layoutInfo" select="$frontMatterLayoutInfo"/>
        <xsl:variable name="sLayoutText" select="exsl:node-set($layoutInfo)/keywordsLayout/@textBetweenKeywords"/>
        <xsl:choose>
            <xsl:when test="string-length($sLayoutText) &gt; 0">
                <xsl:value-of select="$sLayoutText"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>, </xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetUrlEtcLayoutToUseInfo
    -->
    <xsl:template name="GetUrlEtcLayoutToUseInfo">
        <xsl:choose>
            <xsl:when test="../url or url">y</xsl:when>
            <xsl:otherwise>n</xsl:otherwise>
        </xsl:choose>
        <xsl:choose>
            <xsl:when test="../dateAccessed or dateAccessed">y</xsl:when>
            <xsl:otherwise>n</xsl:otherwise>
        </xsl:choose>
        <xsl:choose>
            <xsl:when test="doi">y</xsl:when>
            <xsl:otherwise>n</xsl:otherwise>
        </xsl:choose>
        <xsl:choose>
            <xsl:when test="../iso639-3code and exsl:node-set($lingPaper)/@showiso639-3codeininterlinear='yes'">y</xsl:when>
            <xsl:when test="../iso639-3code and ancestor-or-self::refWork/@showiso639-3codes='yes'">y</xsl:when>
            <xsl:when test="iso639-3code and exsl:node-set($lingPaper)/@showiso639-3codeininterlinear='yes'">y</xsl:when>
            <xsl:when test="iso639-3code and ancestor-or-self::refWork/@showiso639-3codes='yes'">y</xsl:when>
            <xsl:otherwise>n</xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetWebPageLayoutToUsePosition
    -->
    <xsl:template name="GetWebPageLayoutToUsePosition">
        <xsl:variable name="sOptionsPresent">
            <!-- for each possible option, in order, set it to 'y' if present, otherwise 'n' -->
            <!-- first, indicate that the required refTitle is present -->
            <xsl:text>y</xsl:text>
            <xsl:choose>
                <xsl:when test="edition">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="location">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="institution">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="publisher">y</xsl:when>
                <xsl:otherwise>n</xsl:otherwise>
            </xsl:choose>
            <xsl:call-template name="GetUrlEtcLayoutToUseInfo"/>
        </xsl:variable>
        <xsl:variable name="sPosition">
            <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/webPageLayouts/*">
                <xsl:variable name="sItemsWhichMatchOptions">
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='y' and refTitleItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 1, 1)='n' and not(refTitleItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='y' and editionItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 2, 1)='n' and not(editionItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='y' and locationItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 3, 1)='n' and not(locationItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 4, 1)='y' and institutionItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 4, 1)='n' and not(institutionItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 5, 1)='y' and publisherItem">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 5, 1)='n' and not(publisherItem)">x</xsl:when>
                    </xsl:choose>
                    <xsl:call-template name="DetermineIfUrlMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="urlPos">6</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDateAccessedMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="dateAccessedPos">7</xsl:with-param>
                    </xsl:call-template>
                    <xsl:call-template name="DetermineIfDoiMatchesLayoutPattern">
                        <xsl:with-param name="sOptionsPresent" select="$sOptionsPresent"/>
                        <xsl:with-param name="doiPos">8</xsl:with-param>
                    </xsl:call-template>
                    <!--<xsl:choose>
                        <xsl:when test="substring($sOptionsPresent, 8, 1)='y' and iso639-3codeItemRef">x</xsl:when>
                        <xsl:when test="substring($sOptionsPresent, 8, 1)='n' and not(iso639-3codeItemRef)">x</xsl:when>
                        </xsl:choose>-->
                    <!-- now we always set the x for the ISO whether the pattern is there or not; it all comes out in the wash -->
                    <xsl:text>x</xsl:text>
                </xsl:variable>
                <xsl:if test="string-length($sItemsWhichMatchOptions) = 9">
                    <xsl:call-template name="RecordPosition"/>
                </xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <xsl:value-of select="substring-before($sPosition,';')"/>
    </xsl:template>
    <!--  
        HandleBasicFrontMatterPerLayout
    -->
    <xsl:template name="HandleBasicFrontMatterPerLayout">
        <xsl:param name="frontMatter"/>
        <xsl:param name="frontMatterLayout" select="$frontMatterLayoutInfo"/>
        <xsl:variable name="iAuthorLayouts" select="count(exsl:node-set($frontMatterLayout)/authorLayout[count(preceding-sibling::*[1])=0 or preceding-sibling::*[1][name()!='contentsLayout']])"/>
        <xsl:variable name="iAffiliationLayouts" select="count(exsl:node-set($frontMatterLayout)/affiliationLayout)"/>
        <xsl:variable name="iEmailAddressLayouts" select="count(exsl:node-set($frontMatterLayout)/emailAddressLayout)"/>
        <xsl:for-each select="exsl:node-set($frontMatterLayout)/*">
            <xsl:choose>
                <xsl:when test="name(.)='titleLayout'">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/title"/>
                </xsl:when>
                <xsl:when test="name(.)='subtitleLayout'">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/subtitle"/>
                </xsl:when>
                <xsl:when test="name(.)='authorLayout' and count(preceding-sibling::*[1])=0 or name(.)='authorLayout' and preceding-sibling::*[1][name()!='contentsLayout']">
                    <xsl:variable name="iPos" select="count(preceding-sibling::authorLayout) + 1"/>
                    <xsl:choose>
                        <xsl:when test="following-sibling::authorLayout[preceding-sibling::*[1][name()!='contentsLayout']]">
                            <xsl:call-template name="DoAuthorRelatedElementsPerSingleSetOfLayouts">
                                <xsl:with-param name="authors" select="exsl:node-set($frontMatter)/author"/>
                                <xsl:with-param name="currentAuthors" select="exsl:node-set($frontMatter)/author[$iPos]"/>
                                <xsl:with-param name="thisAffiliationLayout" select="following-sibling::*[name()='affiliationLayout' and count(preceding-sibling::authorLayout) = $iPos]"/>
                                <xsl:with-param name="thisEmailAddressLayout" select="following-sibling::*[name()='emailAddressLayout' and count(preceding-sibling::authorLayout) = $iPos]"/>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:when test="preceding-sibling::authorLayout and not(following-sibling::authorLayout[preceding-sibling::*[1][name()!='contentsLayout']])">
                            <xsl:call-template name="DoAuthorRelatedElementsPerSingleSetOfLayouts">
                                <xsl:with-param name="authors" select="exsl:node-set($frontMatter)/author"/>
                                <xsl:with-param name="currentAuthors" select="exsl:node-set($frontMatter)/author[position() &gt;= $iPos]"/>
                                <xsl:with-param name="thisAffiliationLayout" select="following-sibling::*[name()='affiliationLayout' and count(preceding-sibling::authorLayout) = $iPos]"/>
                                <xsl:with-param name="thisEmailAddressLayout" select="following-sibling::*[name()='emailAddressLayout' and count(preceding-sibling::authorLayout) = $iPos]"/>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:when test="$iAuthorLayouts = 1 and $iAffiliationLayouts &lt;= 1 and $iEmailAddressLayouts &lt;= 1 ">
                            <!-- 
                                only one author layout and at most one affiliation layout and at most one email layout : 
                                want to try to apply each set of author/affiliation/email elements to this pattern, allowing for
                                multiple affiliations
                            -->
                            <xsl:variable name="thisAffiliationLayout" select="following-sibling::affiliationLayout"/>
                            <xsl:variable name="thisEmailAddressLayout" select="following-sibling::emailAddressLayout"/>
                            <xsl:call-template name="DoAuthorRelatedElementsPerSingleSetOfLayouts">
                                <xsl:with-param name="authors" select="exsl:node-set($frontMatter)/author"/>
                                <xsl:with-param name="currentAuthors" select="exsl:node-set($frontMatter)/author"/>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:apply-templates select="exsl:node-set($frontMatter)/author"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="name(.)='affiliationLayout'">
                    <xsl:choose>
                        <xsl:when test="following-sibling::affiliationLayout ">
                            <!-- already handled under the author layout case-->
                        </xsl:when>
                        <xsl:when test="preceding-sibling::affiliationLayout and not(following-sibling::affiliationLayout)">
                            <!-- already handled under the author layout case-->
                        </xsl:when>
                        <xsl:when test="$iAuthorLayouts = 1 and $iAffiliationLayouts &lt;= 1 and $iEmailAddressLayouts &lt;= 1 ">
                            <!-- already handled under the author layout case-->
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:apply-templates select="exsl:node-set($frontMatter)/affiliation">
                                <xsl:with-param name="affiliationLayoutToUse" select="."/>
                            </xsl:apply-templates>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="name(.)='emailAddressLayout'">
                    <xsl:choose>
                        <xsl:when test="following-sibling::emailAddressLayout ">
                            <!-- already handled under the author layout case-->
                        </xsl:when>
                        <xsl:when test="preceding-sibling::emailAddressLayout and not(following-sibling::emailAddressLayout)">
                            <!-- already handled under the author layout case-->
                        </xsl:when>
                        <xsl:when test="$iAuthorLayouts = 1 and $iAffiliationLayouts &lt;= 1 and $iEmailAddressLayouts &lt;= 1 ">
                            <!-- already handled under the author layout case-->
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:apply-templates select="exsl:node-set($frontMatter)/emailAddress">
                                <xsl:with-param name="emailAddressLayoutToUse" select="."/>
                            </xsl:apply-templates>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="name(.)='authorContactInfoLayout'">
                    <xsl:apply-templates select="exsl:node-set($lingPaper)/frontMatter/authorContactInfo">
                        <xsl:with-param name="layoutInfo" select="exsl:node-set($frontMatterLayoutInfo)/authorContactInfoLayout"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='presentedAtLayout'">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/presentedAt"/>
                </xsl:when>
                <xsl:when test="name(.)='dateLayout'">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/date">
                        <xsl:with-param name="frontMatterLayout" select="$frontMatterLayout"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='versionLayout'">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/version">
                        <xsl:with-param name="frontMatterLayout" select="$frontMatterLayout"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='keywordsLayout'">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/keywordsShownHere">
                        <xsl:with-param name="frontMatterLayout" select="$frontMatterLayout"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='publishingBlurbLayout'">
                    <xsl:apply-templates select="exsl:node-set($lingPaper)/publishingInfo/publishingBlurb"/>
                </xsl:when>
                <xsl:when test="name(.)='contentsLayout' and exsl:node-set($frontMatter)[ancestor::chapterInCollection]">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/contents" mode="paper">
                        <xsl:with-param name="frontMatterLayout" select="$frontMatterLayout"/>
                        <xsl:with-param name="contentsLayoutToUse" select="exsl:node-set($frontMatterLayout)/contentsLayout"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='contentsLayout' and not($bIsBook)">
                    <xsl:apply-templates select="exsl:node-set($lingPaper)/frontMatter/contents" mode="paper">
                        <xsl:with-param name="frontMatterLayout" select="$frontMatterLayoutInfo"/>
                        <xsl:with-param name="contentsLayoutToUse" select="exsl:node-set($frontMatterLayoutInfo)/contentsLayout"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='acknowledgementsLayout' and exsl:node-set($frontMatter)[ancestor::chapterInCollection]">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/acknowledgements" mode="paper">
                        <xsl:with-param name="frontMatterLayout" select="$frontMatterLayout"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='acknowledgementsLayout' and not($bIsBook)">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/acknowledgements" mode="paper"/>
                </xsl:when>
                <xsl:when test="name(.)='keywordsLayout' and exsl:node-set($frontMatter)[ancestor::chapterInCollection]">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/keywordsShownHere" mode="paper">
                        <xsl:with-param name="frontMatterLayout" select="$frontMatterLayout"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='keywordsLayout' and not($bIsBook)">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/keywordsShownHere" mode="paper">
                        <xsl:with-param name="frontMatterLayout" select="$frontMatterLayout"/>
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:when test="name(.)='abstractLayout' and exsl:node-set($frontMatter)[ancestor::chapterInCollection]">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/abstract" mode="paper">
                        <xsl:with-param name="frontMatterLayout" select="$frontMatterLayout"/>
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
                <xsl:when test="name(.)='abstractLayout' and not($bIsBook)">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/abstract" mode="paper">
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
                <xsl:when test="name(.)='prefaceLayout' and exsl:node-set($frontMatter)[ancestor::chapterInCollection]">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/preface" mode="paper">
                        <xsl:with-param name="frontMatterLayout" select="$frontMatterLayout"/>
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
                <xsl:when test="name(.)='prefaceLayout' and not($bIsBook)">
                    <xsl:apply-templates select="exsl:node-set($frontMatter)/preface" mode="paper">
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
        HandleDateAccessedLayout
    -->
    <xsl:template name="HandleDateAccessedLayout">
        <xsl:param name="kindOfWork"/>
        <xsl:param name="work"/>
        <xsl:variable name="currentItem" select="."/>
        <xsl:for-each select="exsl:node-set($kindOfWork)/dateAccessed | exsl:node-set($work)/dateAccessed">
            <xsl:variable name="item" select="."/>
            <xsl:for-each select="$currentItem">
                <xsl:call-template name="OutputReferenceItem">
                    <xsl:with-param name="item" select="$item"/>
                </xsl:call-template>
            </xsl:for-each>
        </xsl:for-each>
    </xsl:template>
    <!--  
        HandleDoiLayout
    -->
    <xsl:template name="HandleDoiLayout">
        <xsl:param name="kindOfWork"/>
        <xsl:param name="work"/>
        <xsl:variable name="currentItem" select="."/>
        <xsl:for-each select="exsl:node-set($kindOfWork)/doi | exsl:node-set($work)/doi">
            <xsl:variable name="item" select="."/>
            <xsl:for-each select="$currentItem">
                <xsl:call-template name="OutputReferenceItemNode">
                    <xsl:with-param name="item" select="$item"/>
                </xsl:call-template>
            </xsl:for-each>
        </xsl:for-each>
    </xsl:template>
    <!--  
        HandleFreeTextAfterInside
    -->
    <xsl:template name="HandleFreeTextAfterInside">
        <xsl:param name="freeLayout"/>
        <xsl:if test="exsl:node-set($freeLayout)/@textbeforeafterusesfontinfo='yes'">
            <xsl:choose>
                <xsl:when test="string-length(normalize-space(@textafter)) &gt; 0">
                    <xsl:value-of select="normalize-space(@textafter)"/>
                </xsl:when>
                <xsl:when test="string-length(normalize-space(exsl:node-set($freeLayout)/@textafter)) &gt; 0">
                    <xsl:value-of select="normalize-space(exsl:node-set($freeLayout)/@textafter)"/>
                </xsl:when>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleFreeTextAfterOutside
    -->
    <xsl:template name="HandleFreeTextAfterOutside">
        <xsl:param name="freeLayout"/>
        <xsl:if test="$freeLayout">
            <xsl:if test="exsl:node-set($freeLayout)/@textbeforeafterusesfontinfo='no'">
                <xsl:choose>
                    <xsl:when test="string-length(normalize-space(@textafter)) &gt; 0">
                        <xsl:value-of select="normalize-space(@textafter)"/>
                    </xsl:when>
                    <xsl:when test="string-length(normalize-space(exsl:node-set($freeLayout)/@textafter)) &gt; 0">
                        <xsl:value-of select="normalize-space(exsl:node-set($freeLayout)/@textafter)"/>
                    </xsl:when>
                </xsl:choose>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleFreeTextBeforeAndFontOverrides
    -->
    <xsl:template name="HandleFreeTextBeforeAndFontOverrides">
        <xsl:param name="freeLayout"/>
        <xsl:if test="$freeLayout">
            <xsl:call-template name="OutputFontAttributes">
                <xsl:with-param name="language" select="$freeLayout"/>
                <xsl:with-param name="originalContext" select="."/>
                <xsl:with-param name="bIsOverride" select="'Y'"/>
            </xsl:call-template>
            <xsl:if test="exsl:node-set($freeLayout)/@textbeforeafterusesfontinfo='yes'">
                <xsl:choose>
                    <xsl:when test="string-length(@textbefore) &gt; 0">
                        <xsl:value-of select="@textbefore"/>
                    </xsl:when>
                    <xsl:when test="string-length(exsl:node-set($freeLayout)/@textbefore) &gt; 0">
                        <xsl:value-of select="exsl:node-set($freeLayout)/@textbefore"/>
                    </xsl:when>
                </xsl:choose>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleFreeTextBeforeOutside
    -->
    <xsl:template name="HandleFreeTextBeforeOutside">
        <xsl:param name="freeLayout"/>
        <xsl:if test="$freeLayout">
            <xsl:if test="exsl:node-set($freeLayout)/@textbeforeafterusesfontinfo='no'">
                <xsl:choose>
                    <xsl:when test="string-length(@textbefore) &gt; 0">
                        <xsl:value-of select="@textbefore"/>
                    </xsl:when>
                    <xsl:when test="string-length(exsl:node-set($freeLayout)/@textbefore) &gt; 0">
                        <xsl:value-of select="exsl:node-set($freeLayout)/@textbefore"/>
                    </xsl:when>
                </xsl:choose>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleGlossFontOverrides
    -->
    <xsl:template name="HandleGlossFontOverrides">
        <xsl:param name="sGlossContext"/>
        <xsl:param name="glossLayout"/>
        <xsl:choose>
            <xsl:when test="$sGlossContext='listWord'">
                <xsl:call-template name="OutputFontAttributes">
                    <xsl:with-param name="language" select="exsl:node-set($glossLayout)/glossInListWordLayout"/>
                    <xsl:with-param name="originalContext" select="."/>
                    <xsl:with-param name="bIsOverride" select="'Y'"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$sGlossContext='example'">
                <xsl:call-template name="OutputFontAttributes">
                    <xsl:with-param name="language" select="exsl:node-set($glossLayout)/glossInExampleLayout"/>
                    <xsl:with-param name="originalContext" select="."/>
                    <xsl:with-param name="bIsOverride" select="'Y'"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$sGlossContext='table'">
                <xsl:call-template name="OutputFontAttributes">
                    <xsl:with-param name="language" select="exsl:node-set($glossLayout)/glossInTableLayout"/>
                    <xsl:with-param name="originalContext" select="."/>
                    <xsl:with-param name="bIsOverride" select="'Y'"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$sGlossContext='prose'">
                <xsl:call-template name="OutputFontAttributes">
                    <xsl:with-param name="language" select="exsl:node-set($glossLayout)/glossInProseLayout"/>
                    <xsl:with-param name="originalContext" select="."/>
                    <xsl:with-param name="bIsOverride" select="'Y'"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  
        HandleGlossTextAfterInside
    -->
    <xsl:template name="HandleGlossTextAfterInside">
        <xsl:param name="glossLayout"/>
        <xsl:param name="sGlossContext"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($glossLayout)/glossInListWordLayout/@textbeforeafterusesfontinfo='yes' and $sGlossContext='listWord'">
                <xsl:choose>
                    <xsl:when test="string-length(normalize-space(@textafter)) &gt; 0">
                        <xsl:value-of select="normalize-space(@textafter)"/>
                    </xsl:when>
                    <xsl:when test="string-length(normalize-space(exsl:node-set($glossLayout)/glossInListWordLayout/@textafter)) &gt; 0">
                        <xsl:value-of select="normalize-space(exsl:node-set($glossLayout)/glossInListWordLayout/@textafter)"/>
                    </xsl:when>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="exsl:node-set($glossLayout)/glossInExampleLayout/@textbeforeafterusesfontinfo='yes' and $sGlossContext='example'">
                <xsl:choose>
                    <xsl:when test="string-length(normalize-space(@textafter)) &gt; 0">
                        <xsl:value-of select="normalize-space(@textafter)"/>
                    </xsl:when>
                    <xsl:when test="name()='line' and string-length(normalize-space(gloss/@textafter)) &gt; 0">
                        <xsl:value-of select="normalize-space(gloss/@textafter)"/>
                    </xsl:when>
                    <xsl:when test="string-length(normalize-space(exsl:node-set($glossLayout)/glossInExampleLayout/@textafter)) &gt; 0">
                        <xsl:value-of select="normalize-space(exsl:node-set($glossLayout)/glossInExampleLayout/@textafter)"/>
                    </xsl:when>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="exsl:node-set($glossLayout)/glossInTableLayout/@textbeforeafterusesfontinfo='yes' and $sGlossContext='table'">
                <xsl:choose>
                    <xsl:when test="string-length(normalize-space(@textafter)) &gt; 0">
                        <xsl:value-of select="normalize-space(@textafter)"/>
                    </xsl:when>
                    <xsl:when test="string-length(normalize-space(exsl:node-set($glossLayout)/glossInTableLayout/@textafter)) &gt; 0">
                        <xsl:value-of select="normalize-space(exsl:node-set($glossLayout)/glossInTableLayout/@textafter)"/>
                    </xsl:when>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="exsl:node-set($glossLayout)/glossInProseLayout/@textbeforeafterusesfontinfo='yes' and $sGlossContext='prose'">
                <xsl:choose>
                    <xsl:when test="string-length(normalize-space(@textafter)) &gt; 0">
                        <xsl:value-of select="normalize-space(@textafter)"/>
                    </xsl:when>
                    <xsl:when test="string-length(normalize-space(exsl:node-set($glossLayout)/glossInProseLayout/@textafter)) &gt; 0">
                        <xsl:value-of select="normalize-space(exsl:node-set($glossLayout)/glossInProseLayout/@textafter)"/>
                    </xsl:when>
                </xsl:choose>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  
        HandleGlossTextAfterOutside
    -->
    <xsl:template name="HandleGlossTextAfterOutside">
        <xsl:param name="glossLayout"/>
        <xsl:param name="sGlossContext"/>
        <xsl:if test="$glossLayout">
            <xsl:choose>
                <xsl:when test="exsl:node-set($glossLayout)/glossInListWordLayout/@textbeforeafterusesfontinfo='no' and $sGlossContext='listWord'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textafter)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textafter)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($glossLayout)/glossInListWordLayout/@textafter)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($glossLayout)/glossInListWordLayout/@textafter)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="exsl:node-set($glossLayout)/glossInExampleLayout/@textbeforeafterusesfontinfo='no' and $sGlossContext='example'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textafter)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textafter)"/>
                        </xsl:when>
                        <xsl:when test="name()='line' and string-length(normalize-space(gloss/@textafter)) &gt; 0">
                            <xsl:value-of select="normalize-space(gloss/@textafter)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($glossLayout)/glossInExampleLayout/@textafter)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($glossLayout)/glossInExampleLayout/@textafter)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="exsl:node-set($glossLayout)/glossInTableLayout/@textbeforeafterusesfontinfo='no' and $sGlossContext='table'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textafter)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textafter)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($glossLayout)/glossInTableLayout/@textafter)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($glossLayout)/glossInTableLayout/@textafter)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="exsl:node-set($glossLayout)/glossInProseLayout/@textbeforeafterusesfontinfo='no' and $sGlossContext='prose'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textafter)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textafter)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($glossLayout)/glossInProseLayout/@textafter)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($glossLayout)/glossInProseLayout/@textafter)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleGlossTextBeforeAndFontOverrides
    -->
    <xsl:template name="HandleGlossTextBeforeAndFontOverrides">
        <xsl:param name="glossLayout"/>
        <xsl:param name="sGlossContext"/>
        <xsl:if test="$glossLayout">
            <xsl:call-template name="HandleGlossFontOverrides">
                <xsl:with-param name="sGlossContext" select="$sGlossContext"/>
                <xsl:with-param name="glossLayout" select="$glossLayout"/>
            </xsl:call-template>
            <xsl:choose>
                <xsl:when test="exsl:node-set($glossLayout)/glossInListWordLayout/@textbeforeafterusesfontinfo='yes' and $sGlossContext='listWord'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textbefore)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($glossLayout)/glossInListWordLayout/@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($glossLayout)/glossInListWordLayout/@textbefore)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="exsl:node-set($glossLayout)/glossInExampleLayout/@textbeforeafterusesfontinfo='yes' and $sGlossContext='example'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textbefore)"/>
                        </xsl:when>
                        <xsl:when test="name()='line' and string-length(normalize-space(gloss/@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(gloss/@textbefore)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($glossLayout)/glossInExampleLayout/@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($glossLayout)/glossInExampleLayout/@textbefore)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="exsl:node-set($glossLayout)/glossInTableLayout/@textbeforeafterusesfontinfo='yes' and $sGlossContext='table'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textbefore)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($glossLayout)/glossInTableLayout/@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($glossLayout)/glossInTableLayout/@textbefore)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="exsl:node-set($glossLayout)/glossInProseLayout/@textbeforeafterusesfontinfo='yes' and $sGlossContext='prose'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textbefore)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($glossLayout)/glossInProseLayout/@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($glossLayout)/glossInProseLayout/@textbefore)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleGlossTextBeforeOutside
    -->
    <xsl:template name="HandleGlossTextBeforeOutside">
        <xsl:param name="glossLayout"/>
        <xsl:param name="sGlossContext"/>
        <xsl:if test="$glossLayout">
            <xsl:choose>
                <xsl:when test="exsl:node-set($glossLayout)/glossInListWordLayout/@textbeforeafterusesfontinfo='no' and $sGlossContext='listWord'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textbefore)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($glossLayout)/glossInListWordLayout/@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($glossLayout)/glossInListWordLayout/@textbefore)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="exsl:node-set($glossLayout)/glossInExampleLayout/@textbeforeafterusesfontinfo='no' and $sGlossContext='example'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textbefore)"/>
                        </xsl:when>
                        <xsl:when test="name()='line' and string-length(normalize-space(gloss/@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(gloss/@textbefore)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($glossLayout)/glossInExampleLayout/@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($glossLayout)/glossInExampleLayout/@textbefore)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="exsl:node-set($glossLayout)/glossInTableLayout/@textbeforeafterusesfontinfo='no' and $sGlossContext='table'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textbefore)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($glossLayout)/glossInTableLayout/@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($glossLayout)/glossInTableLayout/@textbefore)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="exsl:node-set($glossLayout)/glossInProseLayout/@textbeforeafterusesfontinfo='no' and $sGlossContext='prose'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textbefore)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($glossLayout)/glossInProseLayout/@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($glossLayout)/glossInProseLayout/@textbefore)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleLangDataFontOverrides
    -->
    <xsl:template name="HandleLangDataFontOverrides">
        <xsl:param name="sLangDataContext"/>
        <xsl:param name="langDataLayout"/>
        <xsl:choose>
            <xsl:when test="$sLangDataContext='example'">
                <xsl:call-template name="OutputFontAttributes">
                    <xsl:with-param name="language" select="exsl:node-set($langDataLayout)/langDataInExampleLayout"/>
                    <xsl:with-param name="originalContext" select="."/>
                    <xsl:with-param name="bIsOverride" select="'Y'"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$sLangDataContext='table'">
                <xsl:call-template name="OutputFontAttributes">
                    <xsl:with-param name="language" select="exsl:node-set($langDataLayout)/langDataInTableLayout"/>
                    <xsl:with-param name="originalContext" select="."/>
                    <xsl:with-param name="bIsOverride" select="'Y'"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$sLangDataContext='prose'">
                <xsl:call-template name="OutputFontAttributes">
                    <xsl:with-param name="language" select="exsl:node-set($langDataLayout)/langDataInProseLayout"/>
                    <xsl:with-param name="originalContext" select="."/>
                    <xsl:with-param name="bIsOverride" select="'Y'"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  
        HandleLangDataTextAfterInside
    -->
    <xsl:template name="HandleLangDataTextAfterInside">
        <xsl:param name="langDataLayout"/>
        <xsl:param name="sLangDataContext"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($langDataLayout)/langDataInExampleLayout/@textbeforeafterusesfontinfo='yes' and $sLangDataContext='example'">
                <xsl:choose>
                    <xsl:when test="string-length(normalize-space(@textafter)) &gt; 0">
                        <xsl:value-of select="normalize-space(@textafter)"/>
                    </xsl:when>
                    <xsl:when test="name()='line' and string-length(normalize-space(langData/@textafter)) &gt; 0">
                        <xsl:value-of select="normalize-space(langData/@textafter)"/>
                    </xsl:when>
                    <xsl:when test="string-length(normalize-space(exsl:node-set($langDataLayout)/langDataInExampleLayout/@textafter)) &gt; 0">
                        <xsl:value-of select="normalize-space(exsl:node-set($langDataLayout)/langDataInExampleLayout/@textafter)"/>
                    </xsl:when>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="exsl:node-set($langDataLayout)/langDataInTableLayout/@textbeforeafterusesfontinfo='yes' and $sLangDataContext='table'">
                <xsl:choose>
                    <xsl:when test="string-length(normalize-space(@textafter)) &gt; 0">
                        <xsl:value-of select="normalize-space(@textafter)"/>
                    </xsl:when>
                    <xsl:when test="string-length(normalize-space(exsl:node-set($langDataLayout)/langDataInTableLayout/@textafter)) &gt; 0">
                        <xsl:value-of select="normalize-space(exsl:node-set($langDataLayout)/langDataInTableLayout/@textafter)"/>
                    </xsl:when>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="exsl:node-set($langDataLayout)/langDataInProseLayout/@textbeforeafterusesfontinfo='yes' and $sLangDataContext='prose'">
                <xsl:choose>
                    <xsl:when test="string-length(normalize-space(@textafter)) &gt; 0">
                        <xsl:value-of select="normalize-space(@textafter)"/>
                    </xsl:when>
                    <xsl:when test="string-length(normalize-space(exsl:node-set($langDataLayout)/langDataInProseLayout/@textafter)) &gt; 0">
                        <xsl:value-of select="normalize-space(exsl:node-set($langDataLayout)/langDataInProseLayout/@textafter)"/>
                    </xsl:when>
                </xsl:choose>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  
        HandleLangDataTextAfterOutside
    -->
    <xsl:template name="HandleLangDataTextAfterOutside">
        <xsl:param name="langDataLayout"/>
        <xsl:param name="sLangDataContext"/>
        <xsl:if test="$langDataLayout">
            <xsl:choose>
                <xsl:when test="exsl:node-set($langDataLayout)/langDataInExampleLayout/@textbeforeafterusesfontinfo='no' and $sLangDataContext='example'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textafter)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textafter)"/>
                        </xsl:when>
                        <xsl:when test="name()='line' and string-length(normalize-space(langData/@textafter)) &gt; 0">
                            <xsl:value-of select="normalize-space(langData/@textafter)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($langDataLayout)/langDataInExampleLayout/@textafter)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($langDataLayout)/langDataInExampleLayout/@textafter)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="exsl:node-set($langDataLayout)/langDataInTableLayout/@textbeforeafterusesfontinfo='no' and $sLangDataContext='table'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textafter)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textafter)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($langDataLayout)/langDataInTableLayout/@textafter)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($langDataLayout)/langDataInTableLayout/@textafter)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="exsl:node-set($langDataLayout)/langDataInProseLayout/@textbeforeafterusesfontinfo='no' and $sLangDataContext='prose'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textafter)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textafter)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($langDataLayout)/langDataInProseLayout/@textafter)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($langDataLayout)/langDataInProseLayout/@textafter)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleLangDataTextBeforeAndFontOverrides
    -->
    <xsl:template name="HandleLangDataTextBeforeAndFontOverrides">
        <xsl:param name="langDataLayout"/>
        <xsl:param name="sLangDataContext"/>
        <xsl:if test="$langDataLayout">
            <xsl:call-template name="HandleLangDataFontOverrides">
                <xsl:with-param name="sLangDataContext" select="$sLangDataContext"/>
                <xsl:with-param name="langDataLayout" select="$langDataLayout"/>
            </xsl:call-template>
            <xsl:choose>
                <xsl:when test="exsl:node-set($langDataLayout)/langDataInExampleLayout/@textbeforeafterusesfontinfo='yes' and $sLangDataContext='example'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textbefore)"/>
                        </xsl:when>
                        <xsl:when test="name()='line' and string-length(normalize-space(langData/@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(langData/@textbefore)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($langDataLayout)/langDataInExampleLayout/@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($langDataLayout)/langDataInExampleLayout/@textbefore)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="exsl:node-set($langDataLayout)/langDataInTableLayout/@textbeforeafterusesfontinfo='yes' and $sLangDataContext='table'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textbefore)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($langDataLayout)/langDataInTableLayout/@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($langDataLayout)/langDataInTableLayout/@textbefore)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="exsl:node-set($langDataLayout)/langDataInProseLayout/@textbeforeafterusesfontinfo='yes' and $sLangDataContext='prose'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textbefore)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($langDataLayout)/langDataInProseLayout/@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($langDataLayout)/langDataInProseLayout/@textbefore)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleLangDataTextBeforeOutside
    -->
    <xsl:template name="HandleLangDataTextBeforeOutside">
        <xsl:param name="langDataLayout"/>
        <xsl:param name="sLangDataContext"/>
        <xsl:if test="$langDataLayout">
            <xsl:choose>
                <xsl:when test="exsl:node-set($langDataLayout)/langDataInExampleLayout/@textbeforeafterusesfontinfo='no' and $sLangDataContext='example'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textbefore)"/>
                        </xsl:when>
                        <xsl:when test="name()='line' and string-length(normalize-space(langData/@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(langData/@textbefore)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($langDataLayout)/langDataInExampleLayout/@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($langDataLayout)/langDataInExampleLayout/@textbefore)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="exsl:node-set($langDataLayout)/langDataInTableLayout/@textbeforeafterusesfontinfo='no' and $sLangDataContext='table'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textbefore)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($langDataLayout)/langDataInTableLayout/@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($langDataLayout)/langDataInTableLayout/@textbefore)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
                <xsl:when test="exsl:node-set($langDataLayout)/langDataInProseLayout/@textbeforeafterusesfontinfo='no' and $sLangDataContext='prose'">
                    <xsl:choose>
                        <xsl:when test="string-length(normalize-space(@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(@textbefore)"/>
                        </xsl:when>
                        <xsl:when test="string-length(normalize-space(exsl:node-set($langDataLayout)/langDataInProseLayout/@textbefore)) &gt; 0">
                            <xsl:value-of select="normalize-space(exsl:node-set($langDataLayout)/langDataInProseLayout/@textbefore)"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleUrlAndDateAccessedLayouts
    -->
    <xsl:template name="HandleUrlAndDateAccessedLayouts">
        <xsl:param name="typeOfWork"/>
        <xsl:param name="work"/>
        <xsl:if test="exsl:node-set($typeOfWork)/url">
            <xsl:call-template name="OutputReferenceItemNode">
                <xsl:with-param name="item" select="exsl:node-set($typeOfWork)/url"/>
            </xsl:call-template>
            <xsl:if test="exsl:node-set($typeOfWork)/dateAccessed">
                <xsl:for-each select="following-sibling::dateAccessedItem[1]">
                    <xsl:call-template name="OutputReferenceItem">
                        <xsl:with-param name="item" select="exsl:node-set($typeOfWork)/dateAccessed"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:if>
        </xsl:if>
        <xsl:if test="exsl:node-set($work)/url">
            <xsl:call-template name="OutputReferenceItemNode">
                <xsl:with-param name="item" select="exsl:node-set($work)/url"/>
            </xsl:call-template>
            <xsl:if test="exsl:node-set($work)/dateAccessed">
                <xsl:for-each select="following-sibling::dateAccessedItem[1]">
                    <xsl:call-template name="OutputReferenceItem">
                        <xsl:with-param name="item" select="exsl:node-set($work)/dateAccessed"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:if>
        </xsl:if>
        <xsl:if test="exsl:node-set($typeOfWork)/doi">
            <xsl:call-template name="OutputReferenceItemNode">
                <xsl:with-param name="item" select="exsl:node-set($typeOfWork)/doi"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:if test="exsl:node-set($work)/doi">
            <xsl:call-template name="OutputReferenceItemNode">
                <xsl:with-param name="item" select="exsl:node-set($work)/doi"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--  
        HandleUrlLayout
    -->
    <xsl:template name="HandleUrlLayout">
        <xsl:param name="kindOfWork"/>
        <xsl:param name="work"/>
        <xsl:variable name="currentItem" select="."/>
        <xsl:for-each select="exsl:node-set($kindOfWork)/url | exsl:node-set($work)/url">
            <xsl:variable name="item" select="."/>
            <xsl:for-each select="$currentItem">
                <xsl:call-template name="OutputReferenceItemNode">
                    <xsl:with-param name="item" select="$item"/>
                </xsl:call-template>
            </xsl:for-each>
        </xsl:for-each>
    </xsl:template>
    <!--
        OutputAnyTextBeforeRef
    -->
    <xsl:template name="OutputAnyTextBeforeRef">
        <!-- output any canned text before a reference -->
        <xsl:param name="ssingular" select="'section '"/>
        <xsl:param name="splural" select="'sections '"/>
        <xsl:param name="sSingular" select="'Section '"/>
        <xsl:param name="sPlural" select="'Sections '"/>
        <xsl:param name="default" select="exsl:node-set($lingPaper)/@sectionRefDefault"/>
        <xsl:param name="singularLabel" select="exsl:node-set($lingPaper)/@sectionRefSingularLabel"/>
        <xsl:param name="SingularLabel" select="exsl:node-set($lingPaper)/@sectionRefCapitalizedSingularLabel"/>
        <xsl:param name="pluralLabel" select="exsl:node-set($lingPaper)/@sectionRefPluralLabel"/>
        <xsl:param name="PluralLabel" select="exsl:node-set($lingPaper)/@sectionRefCapitalizedPluralLabel"/>
        <xsl:param name="refLayout" select="exsl:node-set($contentLayoutInfo)/sectionRefLayout"/>
        <xsl:variable name="singularOverride" select="exsl:node-set($refLayout)/@textBeforeSingularOverride"/>
        <xsl:variable name="pluralOverride" select="exsl:node-set($refLayout)/@textBeforePluralOverride"/>
        <xsl:variable name="capitalizedSingularOverride" select="exsl:node-set($refLayout)/@textBeforeCapitalizedSingularOverride"/>
        <xsl:variable name="capitalizedPluralOverride" select="exsl:node-set($refLayout)/@textBeforeCapitalizedPluralOverride"/>
        <xsl:choose>
            <xsl:when test="@textBefore='useDefault'">
                <xsl:choose>
                    <xsl:when test="$default='none'">
                        <!-- do nothing -->
                    </xsl:when>
                    <xsl:when test="$default='singular'">
                        <xsl:call-template name="DoItemRefLabel">
                            <xsl:with-param name="sLabel" select="$singularLabel"/>
                            <xsl:with-param name="sDefault" select="$ssingular"/>
                            <xsl:with-param name="sOverride" select="$singularOverride"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:when test="$default='capitalizedSingular'">
                        <xsl:call-template name="DoItemRefLabel">
                            <xsl:with-param name="sLabel" select="$SingularLabel"/>
                            <xsl:with-param name="sDefault" select="$sSingular"/>
                            <xsl:with-param name="sOverride" select="$capitalizedSingularOverride"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:when test="$default='plural'">
                        <xsl:call-template name="DoItemRefLabel">
                            <xsl:with-param name="sLabel" select="$pluralLabel"/>
                            <xsl:with-param name="sDefault" select="$splural"/>
                            <xsl:with-param name="sOverride" select="$pluralOverride"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:when test="$default='capitalizedPlural'">
                        <xsl:call-template name="DoItemRefLabel">
                            <xsl:with-param name="sLabel" select="$PluralLabel"/>
                            <xsl:with-param name="sDefault" select="$sPlural"/>
                            <xsl:with-param name="sOverride" select="$capitalizedPluralOverride"/>
                        </xsl:call-template>
                    </xsl:when>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="@textBefore='singular'">
                <xsl:call-template name="DoItemRefLabel">
                    <xsl:with-param name="sLabel" select="$singularLabel"/>
                    <xsl:with-param name="sDefault" select="$ssingular"/>
                    <xsl:with-param name="sOverride" select="$singularOverride"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="@textBefore='capitalizedSingular'">
                <xsl:call-template name="DoItemRefLabel">
                    <xsl:with-param name="sLabel" select="$SingularLabel"/>
                    <xsl:with-param name="sDefault" select="$sSingular"/>
                    <xsl:with-param name="sOverride" select="$capitalizedSingularOverride"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="@textBefore='plural'">
                <xsl:call-template name="DoItemRefLabel">
                    <xsl:with-param name="sLabel" select="$pluralLabel"/>
                    <xsl:with-param name="sDefault" select="$splural"/>
                    <xsl:with-param name="sOverride" select="$pluralOverride"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="@textBefore='capitalizedPlural'">
                <xsl:call-template name="DoItemRefLabel">
                    <xsl:with-param name="sLabel" select="$PluralLabel"/>
                    <xsl:with-param name="sDefault" select="$sPlural"/>
                    <xsl:with-param name="sOverride" select="$capitalizedPluralOverride"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--
        OutputAnyTextBeforeAppendixRef
    -->
    <xsl:template name="OutputAnyTextBeforeAppendixRef">
        <xsl:call-template name="OutputAnyTextBeforeRef">
            <xsl:with-param name="ssingular" select="'appendix '"/>
            <xsl:with-param name="splural" select="'appendices '"/>
            <xsl:with-param name="sSingular" select="'Appendix '"/>
            <xsl:with-param name="sPlural" select="'Appendices '"/>
            <xsl:with-param name="default" select="exsl:node-set($lingPaper)/@appendixRefDefault"/>
            <xsl:with-param name="refLayout" select="exsl:node-set($contentLayoutInfo)/appendixRefLayout"/>
            <xsl:with-param name="singularLabel" select="exsl:node-set($lingPaper)/@appendixRefSingularLabel"/>
            <xsl:with-param name="SingularLabel" select="exsl:node-set($lingPaper)/@appendixRefCapitalizedSingularLabel"/>
            <xsl:with-param name="pluralLabel" select="exsl:node-set($lingPaper)/@appendixRefPluralLabel"/>
            <xsl:with-param name="PluralLabel" select="exsl:node-set($lingPaper)/@appendixRefCapitalizedPluralLabel"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        OutputAnyTextBeforeFigureRef
    -->
    <xsl:template name="OutputAnyTextBeforeFigureRef">
        <xsl:call-template name="OutputAnyTextBeforeRef">
            <xsl:with-param name="ssingular" select="'figure '"/>
            <xsl:with-param name="splural" select="'figures '"/>
            <xsl:with-param name="sSingular" select="'Figure '"/>
            <xsl:with-param name="sPlural" select="'Figures '"/>
            <xsl:with-param name="default" select="exsl:node-set($lingPaper)/@figureRefDefault"/>
            <xsl:with-param name="refLayout" select="exsl:node-set($contentLayoutInfo)/figureRefLayout"/>
            <xsl:with-param name="singularLabel" select="exsl:node-set($lingPaper)/@figureRefSingularLabel"/>
            <xsl:with-param name="SingularLabel" select="exsl:node-set($lingPaper)/@figureRefCapitalizedSingularLabel"/>
            <xsl:with-param name="pluralLabel" select="exsl:node-set($lingPaper)/@figureRefPluralLabel"/>
            <xsl:with-param name="PluralLabel" select="exsl:node-set($lingPaper)/@figureRefCapitalizedPluralLabel"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        OutputAnyTextBeforeSectionRef
    -->
    <xsl:template name="OutputAnyTextBeforeSectionRef">
        <xsl:call-template name="OutputAnyTextBeforeRef">
            <xsl:with-param name="ssingular" select="'section '"/>
            <xsl:with-param name="splural" select="'sections '"/>
            <xsl:with-param name="sSingular" select="'Section '"/>
            <xsl:with-param name="sPlural" select="'Sections '"/>
            <xsl:with-param name="default" select="exsl:node-set($lingPaper)/@sectionRefDefault"/>
            <xsl:with-param name="refLayout" select="exsl:node-set($contentLayoutInfo)/sectionRefLayout"/>
            <xsl:with-param name="singularLabel" select="exsl:node-set($lingPaper)/@sectionRefSingularLabel"/>
            <xsl:with-param name="SingularLabel" select="exsl:node-set($lingPaper)/@sectionRefCapitalizedSingularLabel"/>
            <xsl:with-param name="pluralLabel" select="exsl:node-set($lingPaper)/@sectionRefPluralLabel"/>
            <xsl:with-param name="PluralLabel" select="exsl:node-set($lingPaper)/@sectionRefCapitalizedPluralLabel"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        OutputAnyTextBeforeSectionRef
    -->
    <xsl:template name="OutputAnyTextBeforeTablenumberedRef">
        <xsl:call-template name="OutputAnyTextBeforeRef">
            <xsl:with-param name="ssingular" select="'table '"/>
            <xsl:with-param name="splural" select="'tables '"/>
            <xsl:with-param name="sSingular" select="'Table '"/>
            <xsl:with-param name="sPlural" select="'Tables '"/>
            <xsl:with-param name="default" select="exsl:node-set($lingPaper)/@tablenumberedRefDefault"/>
            <xsl:with-param name="refLayout" select="exsl:node-set($contentLayoutInfo)/tablenumberedRefLayout"/>
            <xsl:with-param name="singularLabel" select="exsl:node-set($lingPaper)/@tablenumberedRefSingularLabel"/>
            <xsl:with-param name="SingularLabel" select="exsl:node-set($lingPaper)/@tablenumberedRefCapitalizedSingularLabel"/>
            <xsl:with-param name="pluralLabel" select="exsl:node-set($lingPaper)/@tablenumberedRefPluralLabel"/>
            <xsl:with-param name="PluralLabel" select="exsl:node-set($lingPaper)/@tablenumberedRefCapitalizedPluralLabel"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        OutputAppendiciesLabel
    -->
    <xsl:template name="OutputAppendiciesLabel">
        <xsl:call-template name="OutputLabel">
            <xsl:with-param name="sDefault">Appendicies</xsl:with-param>
            <xsl:with-param name="pLabel" select="exsl:node-set($backMatterLayoutInfo)/appendicesTitlePageLayout/@label"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        OutputCannedText
    -->
    <xsl:template name="OutputCannedText">
        <xsl:param name="sCannedText"/>
        <xsl:if test="string-length($sCannedText)&gt;0">
            <xsl:value-of select="$sCannedText"/>
        </xsl:if>
    </xsl:template>
    <!--  
        OutputCitation
    -->
    <xsl:template name="OutputCitation">
        <xsl:param name="item"/>
        <xsl:variable name="sThisRefToBook" select="exsl:node-set($item)/@refToBook"/>
        <xsl:choose>
            <xsl:when test="saxon:node-set($collOrProcVolumesToInclude)/refWork[@id=$sThisRefToBook]">
                <xsl:call-template name="OutputReferenceItemNode">
                    <xsl:with-param name="item" select="$item"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="OutputReferenceItemNode">
                    <xsl:with-param name="item" select="$item"/>
                    <xsl:with-param name="fDoTextAfter" select="'N'"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        OutputCitationContents
    -->
    <xsl:template name="OutputCitationContents">
        <xsl:param name="refer"/>
        <xsl:param name="refWorks" select="$refWorks"/>
        <xsl:if test="@paren='citationBoth' or @paren='citationInitial'">
            <xsl:text>(</xsl:text>
        </xsl:if>
        <xsl:if test="@author='yes'">
            <xsl:call-template name="OutputCitationName">
                <xsl:with-param name="citeName" select="exsl:node-set($refer)/../@citename"/>
            </xsl:call-template>
            <xsl:choose>
                <xsl:when test="@date!='yes'">
                    <!-- do nothing -->
                </xsl:when>
                <xsl:when test="string-length($sTextBetweenAuthorAndDate) &gt; 0 and @paren!='both' and @paren!='initial'">
                    <xsl:value-of select="exsl:node-set($citationLayout)/@textbetweenauthoranddate"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>&#x20;</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:if test="not(@paren) or @paren='both' or @paren='initial'">
            <xsl:text>(</xsl:text>
        </xsl:if>
        <xsl:variable name="works" select="exsl:node-set($refWorks)[../@name=exsl:node-set($refer)/../@name and @id=//citation/@ref]"/>
        <xsl:variable name="date">
            <xsl:variable name="sCiteDate" select="exsl:node-set($refer)/refDate/@citedate"/>
            <xsl:choose>
                <xsl:when test="string-length($sCiteDate) &gt; 0">
                    <xsl:value-of select="$sCiteDate"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="exsl:node-set($refer)/refDate"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:if test="@author='yes' and not(not(@paren) or @paren='both' or @paren='initial')">
            <xsl:choose>
                <xsl:when test="@date!='yes'">
                    <!-- do nothing -->
                </xsl:when>
                <xsl:when test="string-length($sTextBetweenAuthorAndDate) &gt; 0">
                    <!-- do nothing; it's already there -->
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>&#x20;</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:if test="@date!='no'">
            <xsl:value-of select="$date"/>
            <xsl:if test="count(exsl:node-set($works)[refDate=$date or refDate/@citedate=$date])>1">
                <xsl:apply-templates select="$refer" mode="dateLetter">
                    <xsl:with-param name="date" select="$date"/>
                </xsl:apply-templates>
            </xsl:if>
        </xsl:if>
        <xsl:variable name="sPage" select="normalize-space(@page)"/>
        <xsl:if test="string-length($sPage) &gt; 0">
            <xsl:variable name="sColon" select="exsl:node-set($citationLayout)/@replacecolonwith"/>
            <xsl:choose>
                <xsl:when test="string-length($sColon) &gt; 0">
                    <xsl:value-of select="$sColon"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>:</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:if test="string-length(exsl:node-set($citationLayout)/@textbeforepages) &gt; 0">
                <xsl:value-of select="exsl:node-set($citationLayout)/@textbeforepages"/>
            </xsl:if>
            <xsl:value-of select="$sPage"/>
        </xsl:if>
        <xsl:variable name="sTimestamp" select="normalize-space(@timestamp)"/>
        <xsl:if test="string-length($sTimestamp) &gt; 0">
            <xsl:variable name="sBefore" select="exsl:node-set($citationLayout)/@textbeforetimestamp"/>
            <xsl:choose>
                <xsl:when test="string-length($sBefore) &gt; 0">
                    <xsl:value-of select="$sBefore"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>&#x20;</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:value-of select="$sTimestamp"/>
            <xsl:variable name="sAfter" select="exsl:node-set($citationLayout)/@textaftertimestamp"/>
            <xsl:if test="string-length($sAfter) &gt; 0">
                <xsl:value-of select="$sAfter"/>
            </xsl:if>
        </xsl:if>
        <xsl:if test="not(@paren) or @paren='both' or @paren='final' or @paren='citationBoth'">
            <xsl:text>)</xsl:text>
         </xsl:if>
    </xsl:template>
    <!--  
        OutputCitationName
    -->
    <xsl:template name="OutputCitationName">
        <xsl:param name="citeName"/>
        <xsl:variable name="sNameWithSpaces" select="concat(' ',$citeName,' ')"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($citationLayout)/@italicizeetal='yes' and contains($sNameWithSpaces,$sEtAlSpaces)">
                <xsl:call-template name="DoAuthorNameChange">
                    <xsl:with-param name="sName" select="substring-before($citeName, $sEtAl)"/>
                </xsl:call-template>
                <xsl:call-template name="ItalicizeString">
                    <xsl:with-param name="contents" select="$sEtAl"/>
                </xsl:call-template>
                <xsl:call-template name="DoAuthorNameChange">
                    <xsl:with-param name="sName" select="substring-after($citeName,$sEtAl)"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="DoAuthorNameChange">
                    <xsl:with-param name="sName" select="$citeName"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        OutputCitationPages
    -->
    <xsl:template name="OutputCitationPages">
        <xsl:param name="citation"/>
        <xsl:variable name="sNormalizedPages">
            <xsl:variable name="sCitationPages" select="normalize-space(exsl:node-set($citation)/@page)"/>
            <xsl:if test="string-length($sCitationPages) &gt; 0">
                <xsl:value-of select="$sCitationPages"/>
            </xsl:if>
        </xsl:variable>
        <xsl:variable name="pages">
            <xsl:call-template name="GetFormattedPageNumbers">
                <xsl:with-param name="normalizedPages" select="$sNormalizedPages"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:call-template name="OutputReferenceItem">
            <xsl:with-param name="item" select="$pages"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        OutputISO639-3CodeCase
    -->
    <xsl:template name="OutputISO639-3CodeCase">
        <xsl:param name="iso639-3codeItem"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($iso639-3codeItem)/@case='uppercase'">
                <xsl:value-of select="translate(.,'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        OutputSectionNumberProper
    -->
    <xsl:template name="OutputSectionNumberProper">
        <xsl:param name="layoutInfo"/>
        <xsl:param name="bAppendix"/>
        <xsl:param name="sContentsPeriod"/>
        <xsl:variable name="bUseNumber">
            <xsl:choose>
                <xsl:when test="name()='section1' and exsl:node-set($bodyLayoutInfo)/section1Layout/@showNumber='no'">N</xsl:when>
                <xsl:when test="name()='section2' and exsl:node-set($bodyLayoutInfo)/section2Layout/@showNumber='no'">N</xsl:when>
                <xsl:when test="name()='section3' and exsl:node-set($bodyLayoutInfo)/section3Layout/@showNumber='no'">N</xsl:when>
                <xsl:when test="name()='section4' and exsl:node-set($bodyLayoutInfo)/section4Layout/@showNumber='no'">N</xsl:when>
                <xsl:when test="name()='section5' and exsl:node-set($bodyLayoutInfo)/section5Layout/@showNumber='no'">N</xsl:when>
                <xsl:when test="name()='section6' and exsl:node-set($bodyLayoutInfo)/section6Layout/@showNumber='no'">N</xsl:when>
                <xsl:otherwise>Y</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:if test="$bUseNumber='Y'">
            <xsl:call-template name="HandleSectionNumberOutput">
                <xsl:with-param name="layoutInfo" select="$layoutInfo"/>
                <xsl:with-param name="bAppendix" select="$bAppendix"/>
                <xsl:with-param name="sContentsPeriod" select="$sContentsPeriod"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--  
        RecordPosition
    -->
    <xsl:template name="RecordPosition">
        <xsl:value-of select="position()"/>
        <xsl:text>;</xsl:text>
    </xsl:template>
    <!--  
        ReportPattern
    -->
    <xsl:template name="ReportPattern">
        <xsl:variable name="followingSiblings" select="following-sibling::*[name()!='comment']"/>
        <xsl:variable name="children" select="./*"/>
        <xsl:text>  It is a </xsl:text>
        <xsl:value-of select="name(.)"/>
        <xsl:text>   pattern that contains these elements: </xsl:text>
        <xsl:choose>
            <xsl:when test="count($followingSiblings) + count($children) =0">
                <xsl:text>(it is empty).</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <!--                <xsl:text>, </xsl:text>-->
            </xsl:otherwise>
        </xsl:choose>
        <xsl:for-each select="exsl:node-set($children)[name()!='iso639-3code']">
            <xsl:if test="not(contains(name(.), 'LowerCase'))">
                <xsl:value-of select="name(.)"/>
                <xsl:if test="name()='collCitation'">
                    <xsl:if test="key('RefWorkID',@refToBook)/authorRole">
                        <xsl:text>, authorRole</xsl:text>
                    </xsl:if>
                </xsl:if>
                <xsl:choose>
                    <xsl:when test="position()=last() and count($followingSiblings) = 0">
                        <xsl:text>.</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>, </xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:if>
        </xsl:for-each>
        <xsl:for-each select="$followingSiblings">
            <xsl:value-of select="name(.)"/>
            <xsl:choose>
                <xsl:when test="position()=last()">
                    <xsl:text>.</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>, </xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:for-each>
        <xsl:if test="name()='dissertation' or name()='thesis'">
            <xsl:text>  You will also need a </xsl:text>
            <xsl:value-of select="name()"/>
            <xsl:text>LabelItem in the pattern.</xsl:text>
        </xsl:if>
    </xsl:template>
    <!--  
        ReportPatternForCollCitation
    -->
    <xsl:template name="ReportPatternForCollCitation">
        <xsl:param name="collCitation"/>
        <xsl:variable name="followingSiblings" select="following-sibling::*"/>
        <xsl:variable name="children" select="./*"/>
        <xsl:text>  It is a collection pattern that contains these elements: refTitle</xsl:text>
        <xsl:if test="../authorRole">
            <xsl:text>, collEd</xsl:text>
        </xsl:if>
        <xsl:if test="../refTitle">
            <xsl:text>, collTitle</xsl:text>
        </xsl:if>
        <xsl:if test="edition">
            <xsl:text>, edition</xsl:text>
        </xsl:if>
        <xsl:if test="bVol">
            <xsl:text>, collVol</xsl:text>
        </xsl:if>
        <xsl:if test="string-length(normalize-space(exsl:node-set($collCitation)/@page)) &gt; 0">
            <xsl:text>, collPages</xsl:text>
        </xsl:if>
        <xsl:if test="seriesEd">
            <xsl:text>, seriesEd</xsl:text>
        </xsl:if>
        <xsl:if test="series">
            <xsl:text>, series</xsl:text>
        </xsl:if>
        <xsl:if test="location or publisher">
            <xsl:text>, location or publisher</xsl:text>
        </xsl:if>
        <xsl:if test="../url">
            <xsl:text>, url</xsl:text>
        </xsl:if>
        <xsl:if test="../dateAccessed">
            <xsl:text>, dateAccessed</xsl:text>
        </xsl:if>
        <xsl:if test="../iso639-3code and exsl:node-set($lingPaper)/@showiso639-3codeininterlinear='yes' or ../iso639-3code and ancestor-or-self::refWork/@showiso639-3codes='yes'">
            <xsl:text>, iso639-3code</xsl:text>
        </xsl:if>
        <xsl:text>.</xsl:text>
    </xsl:template>
    <!--  
        ReportPatternForPorcCitation
    -->
    <xsl:template name="ReportPatternForProcCitation">
        <xsl:param name="procCitation"/>
        <xsl:variable name="followingSiblings" select="following-sibling::*"/>
        <xsl:variable name="children" select="./*"/>
        <xsl:text>  It is a proceedings pattern that contains these elements:</xsl:text>
        <xsl:if test="../authorRole">
            <xsl:text>, procEd</xsl:text>
        </xsl:if>
        <xsl:if test="../refTitle">
            <xsl:text>, procTitle</xsl:text>
        </xsl:if>
        <xsl:if test="bVol">
            <xsl:text>, procVol</xsl:text>
        </xsl:if>
        <xsl:if test="string-length(normalize-space(exsl:node-set($procCitation)/@page)) &gt; 0">
            <xsl:text>, procPages</xsl:text>
        </xsl:if>
        <xsl:if test="location or publisher">
            <xsl:text>, location or publisher</xsl:text>
        </xsl:if>
        <xsl:if test="../url">
            <xsl:text>, url</xsl:text>
        </xsl:if>
        <xsl:if test="../dateAccessed">
            <xsl:text>, dateAccessed</xsl:text>
        </xsl:if>
        <xsl:if test="../iso639-3code and exsl:node-set($lingPaper)/@showiso639-3codeininterlinear='yes' or ../iso639-3code and ancestor-or-self::refWork/@showiso639-3codes='yes'">
            <xsl:text>, iso639-3code</xsl:text>
        </xsl:if>
        <xsl:text>.</xsl:text>
    </xsl:template>
    <!--  
        TrySectionRef
    -->
    <xsl:template name="TrySectionRef">
        <xsl:param name="section"/>
        <xsl:param name="sectionLayoutInfo"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($sectionLayoutInfo)/@ignore!='yes'">
                <xsl:value-of select="exsl:node-set($section)/@id"/>
            </xsl:when>
            <xsl:otherwise>
                <!-- recurse on the section's parent -->
                <xsl:call-template name="GetSectionRefToUse">
                    <xsl:with-param name="section" select="exsl:node-set($section)/parent::*"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>
