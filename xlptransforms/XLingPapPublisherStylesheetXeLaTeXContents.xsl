<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:tex="http://getfo.sourceforge.net/texml/ns1" xmlns:saxon="http://icl.com/saxon"
xmlns:exsl="http://exslt.org/common">
    <xsl:include href="XLingPapPublisherStylesheetCommonContents.xsl"/>
    <!-- 
        part (contents) 
    -->
    <xsl:template match="part" mode="contents">
        <xsl:param name="nLevel" select="$nLevel"/>
        <xsl:param name="contentsLayoutToUse" select="saxon:node-set($contentsLayout)/contentsLayout"/>
        <xsl:if test="count(preceding-sibling::part)=0">
            <xsl:for-each select="preceding-sibling::*[name()='chapterBeforePart']">
                <xsl:apply-templates select="." mode="contents">
                    <xsl:with-param name="nLevel" select="$nLevel"/>
                    <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                </xsl:apply-templates>
            </xsl:for-each>
        </xsl:if>
        <tex:cmd name="vspace">
            <tex:parm>
                <xsl:call-template name="DoSpaceBeforeContentsLine">
                    <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                </xsl:call-template>
                <xsl:text>pt</xsl:text>
            </tex:parm>
        </tex:cmd>
        <xsl:if test="contains(@XeLaTeXSpecial,'contentsbreak')">
            <tex:cmd name="pagebreak" nl2="0"/>
        </xsl:if>
        <xsl:call-template name="DoInternalHyperlinkBegin">
            <xsl:with-param name="sName" select="@id"/>
        </xsl:call-template>
        <xsl:choose>
            <xsl:when test="exsl:node-set($contentsLayoutToUse)/@partCentered='yes' and exsl:node-set($contentsLayoutToUse)/@partShowPageNumber!='yes'">
                <tex:cmd name="centering">
                    <tex:parm>
                        <xsl:call-template name="OutputPartTOCLine">
                            <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                        </xsl:call-template>
                        <tex:spec cat="esc"/>
                        <tex:spec cat="esc"/>
                    </tex:parm>
                </tex:cmd>
            </xsl:when>
            <xsl:when test="exsl:node-set($contentsLayoutToUse)/@partShowPageNumber='yes'">
                <tex:cmd name="XLingPaperdottedtocline" nl2="1">
                    <tex:parm>
                        <xsl:text>0pt</xsl:text>
                    </tex:parm>
                    <tex:parm>
                        <xsl:text>0pt</xsl:text>
                    </tex:parm>
                    <tex:parm>
                        <xsl:call-template name="OutputPartTOCLine">
                            <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                        </xsl:call-template>
                    </tex:parm>
                    <tex:parm>
                        <xsl:call-template name="OutputTOCPageNumber">
                            <xsl:with-param name="linkLayout" select="exsl:node-set($pageLayoutInfo)/linkLayout/contentsLinkLayout"/>
                            <xsl:with-param name="sLink" select="@id"/>
                        </xsl:call-template>
                    </tex:parm>
                </tex:cmd>
            </xsl:when>
            <xsl:otherwise>
                <tex:cmd name="XLingPaperplaintocline" nl2="1">
                    <tex:parm>
                        <xsl:text>0pt</xsl:text>
                    </tex:parm>
                    <tex:parm>
                        <xsl:text>0pt</xsl:text>
                    </tex:parm>
                    <tex:parm>
                        <xsl:call-template name="OutputPartTOCLine">
                            <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                        </xsl:call-template>
                    </tex:parm>
                </tex:cmd>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="DoInternalHyperlinkEnd"/>
        <xsl:if test="exsl:node-set($contentsLayoutToUse)/@partSpaceAfter">
            <tex:cmd name="vspace">
                <tex:parm>
                    <xsl:value-of select="exsl:node-set($contentsLayoutToUse)/@partSpaceAfter"/>
                    <xsl:text>pt</xsl:text>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:apply-templates select="child::*[contains(name(),'chapter')]" mode="contents">
            <xsl:with-param name="nLevel" select="$nLevel"/>
            <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
        </xsl:apply-templates>
    </xsl:template>
    <!-- 
        section1 (contents) 
    -->
    <xsl:template match="section1" mode="contents">
        <xsl:param name="nLevel" select="$nLevel"/>
        <xsl:param name="contentsLayoutToUse"/>
        <xsl:variable name="iLevel">
            <xsl:value-of select="count(ancestor::chapter | ancestor::chapterInCollection) + count(ancestor::appendix) + 1"/>
        </xsl:variable>
        <xsl:call-template name="OutputSectionTOC">
            <xsl:with-param name="sLevel" select="$iLevel"/>
            <xsl:with-param name="sSpaceBefore">
                <xsl:choose>
                    <xsl:when
                        test="saxon:node-set($contentsLayoutToUse)/@spacebeforemainsection and not(ancestor::chapter) and not(ancestor::appendix) and not(ancestor::chapterBeforePart and not(ancestor::chapterInCollection))">
                        <xsl:value-of select="saxon:node-set($contentsLayoutToUse)/@spacebeforemainsection"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>0</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:with-param>
            <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
        </xsl:call-template>
        <xsl:if test="$nLevel>=2 and exsl:node-set($bodyLayoutInfo)/section2Layout/@ignore!='yes'">
            <xsl:apply-templates select="section2" mode="contents">
                <xsl:with-param name="nLevel" select="$nLevel"/>
                <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
            </xsl:apply-templates>
        </xsl:if>
    </xsl:template>
    <!--
        OutputPartTOCLine
    -->
    <xsl:template name="OutputPartTOCLine">
        <xsl:param name="contentsLayoutToUse" select="saxon:node-set($contentsLayout)/contentsLayout"/>
        <xsl:if test="exsl:node-set($contentsLayoutToUse)/@singlespaceeachcontentline='yes'">
            <tex:spec cat="bg"/>
            <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
        </xsl:if>
        <xsl:call-template name="OutputPartLabelNumberAndTitle">
            <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
            <xsl:with-param name="fInContents" select="'Y'"/>
        </xsl:call-template>
        <xsl:if test="exsl:node-set($contentsLayoutToUse)/@singlespaceeachcontentline='yes'">
            <tex:spec cat="eg"/>
        </xsl:if>
    </xsl:template>
    <!--
        OutputSectionTOC
    -->
    <xsl:template name="OutputSectionTOC">
        <xsl:param name="sLevel"/>
        <xsl:param name="sSpaceBefore" select="'0'"/>
        <xsl:param name="contentsLayoutToUse"/>
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
            <xsl:call-template name="CalculateSectionNumberIndent">
                <xsl:with-param name="contentsLayout" select="$contentsLayoutToUse"/>
            </xsl:call-template>
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
        <xsl:variable name="sChapterLineIndent" select="normalize-space(exsl:node-set($contentsLayoutToUse)/@chapterlineindent)"/>
        <xsl:if test="string-length($sChapterLineIndent)&gt;0">
            <tex:cmd name="addtolength">
                <tex:parm>
                    <tex:cmd name="{$sLevelName}indent" gr="0"/>
                </tex:parm>
                <tex:parm>
                    <xsl:value-of select="$sChapterLineIndent"/>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <!-- output the toc line -->
        <xsl:call-template name="OutputTOCLine">
            <xsl:with-param name="sLink" select="@id"/>
            <xsl:with-param name="sLabel">
                <xsl:call-template name="OutputSectionNumberAndTitleInContents">
                    <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                </xsl:call-template>
            </xsl:with-param>
            <xsl:with-param name="sIndent">
                <tex:cmd name="{$sLevelName}indent" gr="0" nl2="0"/>
            </xsl:with-param>
            <xsl:with-param name="sNumWidth">
                <tex:cmd name="{$sLevelName}width" gr="0" nl2="0"/>
            </xsl:with-param>
            <xsl:with-param name="sSpaceBefore" select="$sSpaceBefore"/>
            <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        OutputTOCLine
    -->
    <xsl:template name="OutputTOCLine">
        <xsl:param name="sLink"/>
        <xsl:param name="sLabel"/>
        <xsl:param name="sSpaceBefore" select="'0'"/>
        <xsl:param name="sIndent" select="'0pt'"/>
        <xsl:param name="override"/>
        <xsl:param name="sNumWidth" select="'0pt'"/>
        <xsl:param name="fUseHalfSpacing"/>
        <xsl:param name="text-transform"/>
        <xsl:param name="contentsLayoutToUse" select="saxon:node-set($contentsLayout)/contentsLayout"/>
        <xsl:variable name="linkLayout" select="exsl:node-set($pageLayoutInfo)/linkLayout/contentsLinkLayout"/>
        <xsl:if test="number($sSpaceBefore)>0">
            <tex:cmd name="vspace">
                <tex:parm>
                    <xsl:value-of select="$sSpaceBefore"/>
                    <xsl:text>pt</xsl:text>
                </tex:parm>
            </tex:cmd>
        </xsl:if>
        <xsl:if test="saxon:node-set($contentsLayout)/contentsLayout/@singlespaceeachcontentline='yes'">
            <tex:spec cat="bg"/>
            <tex:cmd name="{$sSingleSpacingCommand}" gr="0" nl2="1"/>
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
                <xsl:call-template name="OutputTOCTitle">
                    <xsl:with-param name="linkLayout" select="$linkLayout"/>
                    <xsl:with-param name="sLabel" select="$sLabel"/>
                    <xsl:with-param name="text-transform" select="$text-transform"/>
                    <xsl:with-param name="contentsLayoutToUse" select="$contentsLayoutToUse"/>
                </xsl:call-template>
            </tex:parm>
            <tex:parm>
                <xsl:if test="exsl:node-set($contentsLayoutToUse)/@showpagenumber!='no'">
                    <xsl:call-template name="OutputTOCPageNumber">
                        <xsl:with-param name="linkLayout" select="$linkLayout"/>
                        <xsl:with-param name="sLink" select="$sLink"/>
                    </xsl:call-template>
                </xsl:if>
            </tex:parm>
        </tex:cmd>
        <xsl:call-template name="DoInternalHyperlinkEnd"/>
        <xsl:if test="saxon:node-set($contentsLayout)/contentsLayout/@singlespaceeachcontentline='yes'">
            <tex:spec cat="eg"/>
        </xsl:if>
    </xsl:template>
    <!--  
      OutputTOCPageNumber
   -->
    <xsl:template name="OutputTOCPageNumber">
        <xsl:param name="linkLayout"/>
        <xsl:param name="sLink"/>
        <xsl:if test="exsl:node-set($linkLayout)/@linkpagenumber!='no'">
            <xsl:call-template name="LinkAttributesBegin">
                <xsl:with-param name="override" select="$linkLayout"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:variable name="sPage" select="document($sTableOfContentsFile)/toc/tocline[@ref=translate($sLink,$sIDcharsToMap,$sIDcharsMapped)]/@page"/>
        <xsl:choose>
            <xsl:when test="$sPage">
                <xsl:value-of select="$sPage"/>
            </xsl:when>
            <xsl:otherwise>??</xsl:otherwise>
        </xsl:choose>
        <xsl:if test="exsl:node-set($linkLayout)/@linkpagenumber!='no'">
            <xsl:call-template name="LinkAttributesEnd">
                <xsl:with-param name="override" select="$linkLayout"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
    <!--  
      OutputTOCTitle
   -->
    <xsl:template name="OutputTOCTitle">
        <xsl:param name="linkLayout"/>
        <xsl:param name="sLabel"/>
        <xsl:param name="text-transform"/>
        <xsl:param name="contentsLayoutToUse" select="exsl:node-set($contentsLayout)/contentsLayout"/>
        <xsl:if test="exsl:node-set($linkLayout)/@linktitle!='no'">
            <xsl:call-template name="LinkAttributesBegin">
                <xsl:with-param name="override" select="$linkLayout"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:if test="exsl:node-set($contentsLayoutToUse)/@usetext-transformofitem='yes'">
            <xsl:call-template name="OutputTextTransform">
                <xsl:with-param name="sTextTransform" select="normalize-space($text-transform)"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:copy-of select="$sLabel"/>
        <xsl:if test="exsl:node-set($contentsLayoutToUse)/@usetext-transformofitem='yes'">
            <xsl:call-template name="OutputTextTransformEnd">
                <xsl:with-param name="sTextTransform" select="normalize-space($text-transform)"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:if test="exsl:node-set($linkLayout)/@linktitle!='no'">
            <xsl:call-template name="LinkAttributesEnd">
                <xsl:with-param name="override" select="$linkLayout"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>
</xsl:stylesheet>
