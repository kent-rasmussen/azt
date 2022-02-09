<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:tex="http://getfo.sourceforge.net/texml/ns1" xmlns:saxon="http://icl.com/saxon"
xmlns:exsl="http://exslt.org/common">
    <xsl:variable name="authorForm" select="//publisherStyleSheet[1]/backMatterLayout/referencesLayout/@authorform"/>
    <xsl:variable name="titleForm" select="//publisherStyleSheet[1]/backMatterLayout/referencesLayout/@titleform"/>
    <xsl:variable name="iso639-3codeItem" select="//publisherStyleSheet[1]/backMatterLayout/referencesLayout/iso639-3codeItem"/>
    <xsl:variable name="sDateIndent" select="normalize-space(exsl:node-set($referencesLayoutInfo)/@dateIndentAuthorOverDateStyle)"/>
    <!--  
        DoAuthorLayout
    -->
    <xsl:template name="DoAuthorLayout">
        <xsl:param name="referencesLayoutInfo"/>
        <xsl:param name="work"/>
        <xsl:param name="works"/>
        <xsl:param name="sortedWorks"/>
        <xsl:param name="iPos" select="'0'"/>
        <xsl:param name="bDoTarget" select="'Y'"/>
        <xsl:if test="$bDoTarget='Y'">
            <xsl:call-template name="DoInternalTargetBegin">
                <xsl:with-param name="sName" select="@id"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:variable name="authorLayoutToUsePosition">
            <xsl:call-template name="GetAuthorLayoutToUsePosition">
                <xsl:with-param name="referencesLayoutInfo" select="$referencesLayoutInfo"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$authorLayoutToUsePosition=0 or string-length($authorLayoutToUsePosition)=0">
                <xsl:call-template name="ReportNoPatternMatched"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="exsl:node-set($work)/../@showAuthorName!='no'">
                    <xsl:for-each select="exsl:node-set($referencesLayoutInfo)/refAuthorLayouts/*[position()=$authorLayoutToUsePosition]">
                        <xsl:for-each select="*">
                            <tex:spec cat="bg"/>
                            <xsl:choose>
                                <xsl:when test="name(.)='refAuthorItem'">
                                    <xsl:choose>
                                        <xsl:when test="exsl:node-set($referencesLayoutInfo)/@useAuthorOverDateStyle='yes'">
                                            <xsl:if test="$work=exsl:node-set($works)[position()=1]">
                                                <xsl:call-template name="DoAuthorName">
                                                    <xsl:with-param name="work" select="$work"/>
                                                    <xsl:with-param name="referencesLayoutInfo" select="$referencesLayoutInfo"/>
                                                    <xsl:with-param name="iPos" select="$iPos"/>
                                                </xsl:call-template>
                                            </xsl:if>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <xsl:call-template name="DoAuthorName">
                                                <xsl:with-param name="work" select="$work"/>
                                                <xsl:with-param name="referencesLayoutInfo" select="$referencesLayoutInfo"/>
                                                <xsl:with-param name="iPos" select="$iPos"/>
                                            </xsl:call-template>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </xsl:when>
                                <xsl:when test="name(.)='authorRoleItem'">
                                    <xsl:choose>
                                        <xsl:when test="exsl:node-set($referencesLayoutInfo)/@useAuthorOverDateStyle='yes'">
                                            <xsl:if test="$work=exsl:node-set($works)[position()=1]">
                                                <xsl:call-template name="DoAuthorRole">
                                                    <xsl:with-param name="work" select="$work"/>
                                                </xsl:call-template>
                                            </xsl:if>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <xsl:call-template name="DoAuthorRole">
                                                <xsl:with-param name="work" select="$work"/>
                                            </xsl:call-template>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </xsl:when>
                                <xsl:when test="name(.)='refDateItem'">
                                    <xsl:if test="exsl:node-set($referencesLayoutInfo)/@useAuthorOverDateStyle='yes'">
                                        <xsl:if test="$work=exsl:node-set($works)[position()=1]">
                                            <tex:cmd name="par" nl2="1"/>
                                        </xsl:if>
                                        <xsl:if test="string-length($sDateIndent)&gt;0">
                                            <tex:cmd name="hspace*">
                                                <tex:parm>
                                                    <xsl:value-of select="$sDateIndent"/>
                                                </tex:parm>
                                            </tex:cmd>
                                        </xsl:if>
                                    </xsl:if>
                                    <xsl:call-template name="DoDateLayout">
                                        <xsl:with-param name="refDateItem" select="."/>
                                        <xsl:with-param name="work" select="$work"/>
                                        <xsl:with-param name="works" select="$works"/>
                                        <xsl:with-param name="sortedWorks" select="$sortedWorks"/>
                                    </xsl:call-template>
                                    <xsl:if test="exsl:node-set($referencesLayoutInfo)/@useAuthorOverDateStyle='yes'">
                                        <tex:cmd name="XLingPaperentryspaceauthoroverdate">
                                            <tex:parm>
                                                <xsl:value-of select="$sDateIndent"/>
                                            </tex:parm>
                                            <tex:parm>
                                                <xsl:call-template name="DoDateLayout">
                                                    <xsl:with-param name="refDateItem" select="."/>
                                                    <xsl:with-param name="work" select="$work"/>
                                                    <xsl:with-param name="works" select="$works"/>
                                                </xsl:call-template>
                                            </tex:parm>
                                            <tex:parm>
                                                <xsl:value-of select="exsl:node-set($referencesLayoutInfo)/@hangingindentsize"/>
                                            </tex:parm>
                                        </tex:cmd>
                                    </xsl:if>
                                </xsl:when>
                            </xsl:choose>
                            <tex:spec cat="eg"/>
                        </xsl:for-each>
                    </xsl:for-each>
                    <xsl:if test="$bDoTarget='Y'">
                        <xsl:call-template name="DoInternalTargetEnd"/>
                    </xsl:if>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoAuthorName
    -->
    <xsl:template name="DoAuthorName">
        <xsl:param name="work"/>
        <xsl:param name="referencesLayoutInfo"/>
        <xsl:param name="iPos"/>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="."/>
            <xsl:with-param name="originalContext" select="exsl:node-set($work)/.."/>
        </xsl:call-template>
        <xsl:call-template name="DoFormatLayoutInfoTextBefore">
            <xsl:with-param name="layoutInfo" select="."/>
        </xsl:call-template>
        <xsl:variable name="sAuthorName">
            <xsl:choose>
                <xsl:when test="exsl:node-set($referencesLayoutInfo)/@uselineforrepeatedauthor='yes' and $iPos &gt; 1">
                    <xsl:text>______</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates select="exsl:node-set($work)/.."/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:choose>
            <xsl:when
                test="$sAuthorName!='______' and $authorForm='full' and exsl:node-set($referencesLayoutInfo)/refAuthorLayouts/refAuthorLastNameLayout or not(refAuthorInitials) and exsl:node-set($referencesLayoutInfo)/refAuthorLayouts/refAuthorLastNameLayout">
                <xsl:apply-templates select="exsl:node-set($work)/.."/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:copy-of select="$sAuthorName"/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="DoFormatLayoutInfoTextAfter">
            <xsl:with-param name="layoutInfo" select="."/>
            <xsl:with-param name="sPrecedingText" select="$sAuthorName"/>
        </xsl:call-template>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="."/>
            <xsl:with-param name="originalContext" select="exsl:node-set($work)/.."/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        DoAuthorRole
    -->
    <xsl:template name="DoAuthorRole">
        <xsl:param name="work"/>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="."/>
            <xsl:with-param name="originalContext" select="exsl:node-set($work)/authorRole"/>
        </xsl:call-template>
        <xsl:call-template name="DoFormatLayoutInfoTextBefore">
            <xsl:with-param name="layoutInfo" select="."/>
        </xsl:call-template>
        <xsl:apply-templates select="exsl:node-set($work)/authorRole"/>
        <xsl:call-template name="DoFormatLayoutInfoTextAfter">
            <xsl:with-param name="layoutInfo" select="."/>
            <xsl:with-param name="sPrecedingText" select="exsl:node-set($work)/authorRole"/>
        </xsl:call-template>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="."/>
            <xsl:with-param name="originalContext" select="exsl:node-set($work)/authorRole"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        DoDateLayout
    -->
    <xsl:template name="DoDateLayout">
        <xsl:param name="refDateItem"/>
        <xsl:param name="work"/>
        <xsl:param name="works"/>
        <xsl:param name="sortedWorks"/>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="$refDateItem"/>
            <xsl:with-param name="originalContext" select="exsl:node-set($work)/refDate"/>
        </xsl:call-template>
        <xsl:call-template name="DoFormatLayoutInfoTextBefore">
            <xsl:with-param name="layoutInfo" select="$refDateItem"/>
        </xsl:call-template>
        <xsl:apply-templates select="exsl:node-set($work)/refDate">
            <xsl:with-param name="works" select="$works"/>
            <xsl:with-param name="sortedWorks" select="$sortedWorks"/>
        </xsl:apply-templates>
        <xsl:call-template name="DoFormatLayoutInfoTextAfter">
            <xsl:with-param name="layoutInfo" select="$refDateItem"/>
            <xsl:with-param name="sPrecedingText" select="exsl:node-set($work)/refDate"/>
        </xsl:call-template>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="$refDateItem"/>
            <xsl:with-param name="originalContext" select="exsl:node-set($work)/refDate"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        DoDoiLayout
    -->
    <xsl:template name="DoDoiLayout">
        <xsl:call-template name="DoExternalHyperRefBegin">
            <!-- remove any zero width spaces in the hyperlink -->
            <xsl:with-param name="sName" select="concat('https://doi.org/',normalize-space(translate(.,$sStripFromUrl,'')))"/>
        </xsl:call-template>
        <xsl:call-template name="LinkAttributesBegin">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/doiLinkLayout"/>
        </xsl:call-template>
        <xsl:value-of select="normalize-space(.)"/>
        <xsl:call-template name="LinkAttributesEnd">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/doiLinkLayout"/>
        </xsl:call-template>
        <xsl:call-template name="DoExternalHyperRefEnd"/>
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
            <xsl:call-template name="LinkAttributesBegin">
                <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/citationLinkLayout"/>
            </xsl:call-template>
            <xsl:call-template name="OutputCitationName">
                <xsl:with-param name="citeName" select="exsl:node-set($refer)/../@citename"/>
            </xsl:call-template>
            <xsl:call-template name="LinkAttributesEnd">
                <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/citationLinkLayout"/>
            </xsl:call-template>
            <xsl:call-template name="DoExternalHyperRefEnd"/>
        </xsl:for-each>
    </xsl:template>
    <!--  
        DoUrlLayout
    -->
    <xsl:template name="DoUrlLayout">
        <xsl:call-template name="DoExternalHyperRefBegin">
            <!-- remove any zero width spaces in the hyperlink -->
            <xsl:with-param name="sName" select="normalize-space(translate(.,$sStripFromUrl,''))"/>
        </xsl:call-template>
        <xsl:call-template name="LinkAttributesBegin">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/urlLinkLayout"/>
        </xsl:call-template>
        <xsl:value-of select="normalize-space(.)"/>
        <xsl:call-template name="LinkAttributesEnd">
            <xsl:with-param name="override" select="exsl:node-set($pageLayoutInfo)/linkLayout/urlLinkLayout"/>
        </xsl:call-template>
        <xsl:call-template name="DoExternalHyperRefEnd"/>
    </xsl:template>
    <!--  
        DoWebPageUrlItem
    -->
    <xsl:template name="DoWebPageUrlItem">
        <xsl:param name="webPage"/>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="."/>
            <xsl:with-param name="originalContext" select="exsl:node-set($webPage)/url"/>
        </xsl:call-template>
        <xsl:call-template name="DoFormatLayoutInfoTextBefore">
            <xsl:with-param name="layoutInfo" select="."/>
        </xsl:call-template>
        <xsl:apply-templates select="exsl:node-set($webPage)/url"/>
        <xsl:call-template name="DoFormatLayoutInfoTextAfter">
            <xsl:with-param name="layoutInfo" select="."/>
        </xsl:call-template>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="."/>
            <xsl:with-param name="originalContext" select="exsl:node-set($webPage)/url"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
      OutputISO639-3Code
   -->
    <xsl:template name="OutputISO639-3Code">
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="$iso639-3codeItem"/>
        </xsl:call-template>
        <xsl:if test="position() = 1">
            <xsl:value-of select="exsl:node-set($iso639-3codeItem)/@textbeforefirst"/>
        </xsl:if>
        <xsl:value-of select="exsl:node-set($iso639-3codeItem)/@textbefore"/>
        <xsl:choose>
            <xsl:when test="$bShowISO639-3Codes='Y'">
                <xsl:variable name="sThisCode" select="."/>
                <xsl:call-template name="DoInternalHyperlinkBegin">
                    <xsl:with-param name="sName" select="exsl:node-set($languages)[@ISO639-3Code=$sThisCode]/@id"/>
                </xsl:call-template>
                <xsl:call-template name="OutputISO639-3CodeCase">
                    <xsl:with-param name="iso639-3codeItem" select="$iso639-3codeItem"/>
                </xsl:call-template>
                <xsl:call-template name="DoInternalHyperlinkEnd"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="OutputISO639-3CodeCase">
                    <xsl:with-param name="iso639-3codeItem" select="$iso639-3codeItem"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:value-of select="exsl:node-set($iso639-3codeItem)/@text"/>
        <xsl:value-of select="exsl:node-set($iso639-3codeItem)/@textafter"/>
        <xsl:if test="position() != last()">
            <xsl:value-of select="exsl:node-set($iso639-3codeItem)/@textbetween"/>
        </xsl:if>
        <xsl:if test="position() = last()">
            <xsl:value-of select="exsl:node-set($iso639-3codeItem)/@textafterlast"/>
        </xsl:if>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="$iso639-3codeItem"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        OutputReferenceItem
    -->
    <xsl:template name="OutputReferenceItem">
        <xsl:param name="item"/>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="."/>
            <xsl:with-param name="originalContext" select="$item"/>
        </xsl:call-template>
        <xsl:call-template name="DoFormatLayoutInfoTextBefore">
            <xsl:with-param name="layoutInfo" select="."/>
        </xsl:call-template>
        <xsl:apply-templates select="saxon:node-set($item)"/>
        <xsl:call-template name="DoFormatLayoutInfoTextAfter">
            <xsl:with-param name="layoutInfo" select="."/>
            <xsl:with-param name="sPrecedingText" select="$item"/>
        </xsl:call-template>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="."/>
            <xsl:with-param name="originalContext" select="$item"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        OutputReferenceItemNode
    -->
    <xsl:template name="OutputReferenceItemNode">
        <xsl:param name="item"/>
        <xsl:param name="fDoTextAfter" select="'Y'"/>
        <xsl:call-template name="OutputFontAttributes">
            <xsl:with-param name="language" select="."/>
            <xsl:with-param name="originalContext" select="$item"/>
        </xsl:call-template>
        <xsl:call-template name="DoFormatLayoutInfoTextBefore">
            <xsl:with-param name="layoutInfo" select="."/>
        </xsl:call-template>
        <xsl:apply-templates select="$item">
            <xsl:with-param name="layout" select="."/>
        </xsl:apply-templates>
        <xsl:if test="$fDoTextAfter='Y'">
            <xsl:call-template name="DoFormatLayoutInfoTextAfter">
                <xsl:with-param name="layoutInfo" select="."/>
                <xsl:with-param name="sPrecedingText" select="normalize-space($item)"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:call-template name="OutputFontAttributesEnd">
            <xsl:with-param name="language" select="."/>
            <xsl:with-param name="originalContext" select="$item"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        ReportNoPatternMatched
    -->
    <xsl:template name="ReportNoPatternMatched">
        <xsl:call-template name="ReportTeXCannotHandleThisMessage">
            <xsl:with-param name="sMessage">
                <xsl:text>Sorry, but there is no matching layout for this item in the publisher style sheet.  Please add  (or have someone add) the pattern.</xsl:text>
                <xsl:call-template name="ReportPattern"/>

            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--  
        ReportNoPatternMatchedForCollCitation
    -->
    <xsl:template name="ReportNoPatternMatchedForCollCitation">
        <xsl:param name="collCitation"/>
        <xsl:call-template name="ReportTeXCannotHandleThisMessage">
            <xsl:with-param name="sMessage">
                <xsl:text>Sorry, but there is no matching layout for this item in the publisher style sheet.  Please add  (or have someone add) the pattern.</xsl:text>
                <xsl:call-template name="ReportPatternForCollCitation">
                    <xsl:with-param name="collCitation" select="$collCitation"/>
                </xsl:call-template>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--  
        ReportNoPatternMatchedForProcCitation
    -->
    <xsl:template name="ReportNoPatternMatchedForProcCitation">
        <xsl:param name="procCitation"/>
        <xsl:call-template name="ReportTeXCannotHandleThisMessage">
            <xsl:with-param name="sMessage">
                <xsl:text>Sorry, but there is no matching layout for this item in the publisher style sheet.  Please add  (or have someone add) the pattern.</xsl:text>
                <xsl:call-template name="ReportPatternForProcCitation">
                    <xsl:with-param name="procCitation" select="$procCitation"/>
                </xsl:call-template>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
</xsl:stylesheet>
