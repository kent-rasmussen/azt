<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:tex="http://getfo.sourceforge.net/texml/ns1" xmlns:saxon="http://icl.com/saxon" xmlns:xhtml="http://www.w3.org/1999/xhtml"
    xmlns:exsl="http://exslt.org/common" version="1.0" exclude-result-prefixes="saxon xhtml">
    <!-- 
        XLingPapCommon.xsl
        Contains common global variables and common templates common to many of the XLingPaper output transforms.
    -->
    <!-- ===========================================================
        Keys
        =========================================================== -->
    <xsl:key name="AnnotationID" match="//annotation" use="@id"/>
    <xsl:key name="EndnoteID" match="//endnote" use="@id"/>
    <xsl:key name="GlossaryTermRefs" match="//glossaryTermRef" use="@glossaryTerm"/>
    <xsl:key name="IndexTermID" match="//indexTerm" use="@id"/>
    <xsl:key name="InterlinearReferenceID" match="//interlinear | //interlinear-text" use="@text"/>
    <xsl:key name="InterlinearRef" match="//interlinearRef" use="@textref"/>
    <xsl:key name="LanguageID" match="//language" use="@id"/>
    <xsl:key name="RefWorkID" match="//refWork" use="@id"/>
    <xsl:key name="TypeID" match="//type" use="@id"/>
    <xsl:key name="AuthorContactID" match="//authorContact" use="@id"/>
    <xsl:key name="LiInOlID" match="//li[parent::ol]" use="@id"/>
    <xsl:key name="FramedTypeID" match="//framedType" use="@id"/>
    <!-- ===========================================================
        Version of this stylesheet
        =========================================================== -->
    <xsl:variable name="sVersion">3.10.0</xsl:variable>
    <xsl:variable name="lingPaper" select="//lingPaper"/>
    <xsl:variable name="documentLang" select="normalize-space(exsl:node-set($lingPaper)/@xml:lang)"/>
    <xsl:variable name="abbrLang">
        <xsl:variable name="abbrLangTemp" select="normalize-space(exsl:node-set($lingPaper)/@abbreviationlang) "/>
        <xsl:choose>
            <xsl:when test="string-length($abbrLangTemp) &gt; 0">
                <xsl:value-of select="$abbrLangTemp"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$documentLang"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="glossaryTermLang">
        <xsl:variable name="glossaryTermLangTemp" select="normalize-space(exsl:node-set($lingPaper)/@glossarytermlang) "/>
        <xsl:choose>
            <xsl:when test="string-length($glossaryTermLangTemp) &gt; 0">
                <xsl:value-of select="$glossaryTermLangTemp"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$documentLang"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="indexLang">
        <xsl:variable name="indexLangTemp" select="normalize-space(exsl:node-set($lingPaper)/@indexlang) "/>
        <xsl:choose>
            <xsl:when test="string-length($indexLangTemp) &gt; 0">
                <xsl:value-of select="$indexLangTemp"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$documentLang"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="isoCodeLang">
        <xsl:variable name="isoCodeLangTemp" select="normalize-space(exsl:node-set($lingPaper)/@iso639-3codeslang) "/>
        <xsl:choose>
            <xsl:when test="string-length($isoCodeLangTemp) &gt; 0">
                <xsl:value-of select="$isoCodeLangTemp"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$documentLang"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="indexSeeDefinition" select="exsl:node-set($lingPaper)/indexTerms/seeDefinitions/seeDefinition[@lang=$indexLang]"/>
    <xsl:variable name="contents" select="//contents"/>
    <xsl:variable name="abbreviations" select="//abbreviations"/>
    <xsl:variable name="glossaryTerms" select="exsl:node-set($lingPaper)/backMatter/glossaryTerms"/>
    <xsl:variable name="refWorks" select="//refWork"/>
    <xsl:variable name="citations" select="//citation"/>
    <xsl:variable name="annotationRefs" select="//annotationRef"/>
    <xsl:variable name="citationsInAnnotations" select="exsl:node-set($citations)[ancestor::annotation]"/>
    <xsl:variable name="citationsInAnnotationsReferredTo" select="exsl:node-set($citationsInAnnotations)[ancestor::annotation/@id=exsl:node-set($annotationRefs)/@annotation]"/>
    <xsl:variable name="referencesLayoutInfo" select="//publisherStyleSheet[1]/backMatterLayout/referencesLayout"/>
    <xsl:variable name="collOrProcVolumesToInclude">
        <xsl:call-template name="GetCollOrProcVolumesToInclude"/>
    </xsl:variable>
    <xsl:variable name="sMAThesisDefaultLabel" select="'M.A. thesis'"/>
    <xsl:variable name="sPaperDefaultLabel" select="'  Paper presented at the '"/>
    <xsl:variable name="sPhDDissertationDefaultLabel" select="'Ph.D. dissertation'"/>
    <xsl:variable name="sAbstractID" select="'rXLingPapAbstract'"/>
    <xsl:variable name="sAcknowledgementsID" select="'rXLingPapAcknowledgements'"/>
    <xsl:variable name="sContentsID" select="'rXLingPapContents'"/>
    <xsl:variable name="sGlossaryID" select="'rXLingPapGlossary'"/>
    <xsl:variable name="sEndnotesID" select="'rXLingPapEndnotes'"/>
    <xsl:variable name="sPrefaceID" select="'rXLingPapPreface'"/>
    <xsl:variable name="sReferencesID" select="'rXLingPapReferences'"/>
    <xsl:variable name="sKeywordsInFrontMatterID" select="'rXLingPaperKeywordsInFrontMatter'"/>
    <xsl:variable name="sKeywordsInBackMatterID" select="'rXLingPaperKeywordsInBackMatter'"/>
    <xsl:variable name="sAppendiciesPageID" select="'rXLingPapAppendiciesPage'"/>
    <xsl:variable name="endnotesToShow">
        <xsl:for-each select="//endnote[not(ancestor::referencedInterlinearText)][not(ancestor::chapterInCollection/backMatter/endnotes)][not(ancestor::comment)]">
            <xsl:text>X</xsl:text>
        </xsl:for-each>
        <xsl:for-each select="//interlinearRef[not(ancestor::chapterInCollection/backMatter/endnotes)]">
            <xsl:for-each select="key('InterlinearReferenceID',@textref)[1]">
                <xsl:if test="descendant::endnote">
                    <xsl:text>X</xsl:text>
                </xsl:if>
            </xsl:for-each>
        </xsl:for-each>
    </xsl:variable>
    <xsl:variable name="parts" select="//part"/>
    <xsl:variable name="chapters" select="//chapter | //chapterInCollection"/>
    <xsl:variable name="bIsBook" select="$chapters"/>
    <xsl:variable name="sYs" select="'YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY'"/>
    <xsl:variable name="sLiteralLabel" select="exsl:node-set($lingPaper)/@literalLabel"/>
    <xsl:variable name="literalLabelLayoutInfo" select="//publisherStyleSheet[1]/contentLayout/literalLayout/literalLabelLayout"/>
    <xsl:variable name="sIndentOfNonInitialGroup" select="normalize-space(//publisherStyleSheet[1]/contentLayout/interlinearMultipleLineGroupLayout/@indentOfNonInitialGroup)"/>
    <xsl:variable name="sSpaceBetweenGroups" select="normalize-space(//publisherStyleSheet[1]/contentLayout/interlinearMultipleLineGroupLayout/@spaceBetweenGroups)"/>
    <xsl:variable name="bodyLayoutInfo" select="//publisherStyleSheet[1]/bodyLayout"/>
    <xsl:variable name="contentLayoutInfo" select="//publisherStyleSheet[1]/contentLayout"/>
    <xsl:variable name="backMatterLayoutInfo" select="//publisherStyleSheet[1]/backMatterLayout"/>
    <xsl:variable name="frontMatterLayoutInfo" select="//publisherStyleSheet[1]/frontMatterLayout"/>
    <xsl:variable name="chapterNumberFormat" select="exsl:node-set($bodyLayoutInfo)/chapterLayout/@numeralFormat"/>
    <xsl:variable name="sContentBetweenMultipleFootnoteNumbersInText" select="//publisherStyleSheet[1]/pageLayout/@contentBetweenMultipleFootnoteNumbersInText"/>
    <!-- Now we convert all of these to points -->
    <xsl:variable name="iPageWidth">
        <xsl:call-template name="ConvertToPoints">
            <xsl:with-param name="sValue" select="$sPageWidth"/>
            <xsl:with-param name="iValue" select="number(substring($sPageWidth,1,string-length($sPageWidth) - 2))"/>
        </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="iPageHeight">
        <xsl:call-template name="ConvertToPoints">
            <xsl:with-param name="sValue" select="$sPageHeight"/>
            <xsl:with-param name="iValue" select="number(substring($sPageHeight,1,string-length($sPageHeight) - 2))"/>
        </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="iPageInsideMargin">
        <xsl:call-template name="ConvertToPoints">
            <xsl:with-param name="sValue" select="$sPageInsideMargin"/>
            <xsl:with-param name="iValue" select="number(substring($sPageInsideMargin,1,string-length($sPageInsideMargin) - 2))"/>
        </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="iPageOutsideMargin">
        <xsl:call-template name="ConvertToPoints">
            <xsl:with-param name="sValue" select="$sPageOutsideMargin"/>
            <xsl:with-param name="iValue" select="number(substring($sPageOutsideMargin,1,string-length($sPageOutsideMargin) - 2))"/>
        </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="sAuthorNamesWordForAnd" select="exsl:node-set($lingPaper)/references/@authorNamesWordForAnd"/>
    <xsl:variable name="languages" select="//language"/>
    <xsl:variable name="bShowISO639-3Codes">
        <xsl:choose>
            <xsl:when test="//iso639-3codesShownHere">
                <xsl:text>Y</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>N</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="sTextBetweenChapterNumberAndExampleNumber">
        <xsl:if test="$documentLayoutInfo">
            <xsl:value-of select="exsl:node-set($documentLayoutInfo)/exampleLayout/@textBetweenChapterNumberAndExampleNumber"/>
        </xsl:if>
    </xsl:variable>
    <xsl:variable name="sMediaObjectFontFamily" select="'Symbola'"/>
    <xsl:variable name="sBackMatterContentsIdAddOn" select="'BM'"/>
    <xsl:variable name="sTextAfterTerm" select="exsl:node-set($backMatterLayoutInfo)/indexLayout/@textafterterm"/>
    <xsl:variable name="sTextBeforeSeeAlso" select="exsl:node-set($backMatterLayoutInfo)/indexLayout/@textBeforeSeeAlso"/>
    <xsl:variable name="sStripFromUrl" select="'&#x200b;&#x200d;'"/>

    <!-- 
        abbrRef 
    -->
    <xsl:template match="abbrRef" mode="contentOnly">
        <xsl:apply-templates select="id(@abbr)/abbrInLang[1]/abbrTerm" mode="contentOnly"/>
    </xsl:template>
    <!-- 
        afterTerm 
    -->
    <xsl:template match="afterTerm"/>
    <!-- 
        appendixRef (contents) 
    -->
    <xsl:template match="appendixRef" mode="contents">
        <xsl:apply-templates select="self::*"/>
    </xsl:template>
    <!-- 
        beforeTerm 
    -->
    <xsl:template match="beforeTerm"/>
    <!-- 
        br (bookmarks) 
    -->
    <xsl:template match="br" mode="bookmarks">
        <xsl:text>&#x20;</xsl:text>
    </xsl:template>
    <!-- 
        br (contents) 
    -->
    <xsl:template match="br" mode="contents">
        <xsl:text>&#x20;</xsl:text>
    </xsl:template>
    <xsl:template match="br" mode="contentOnly">
        <xsl:text>&#x20;</xsl:text>
    </xsl:template>
    <!-- 
        br (InMarker) 
    -->
    <xsl:template match="br" mode="InMarker">
        <xsl:text>&#x20;</xsl:text>
    </xsl:template>
    <!--
        comment
    -->
    <xsl:template match="comment">
        <xsl:if test="ancestor::lingPaper and exsl:node-set($lingPaper)/@showcommentinoutput='yes' and not(parent::types)">
            <xsl:call-template name="OutputComment"/>
        </xsl:if>
    </xsl:template>
    <!--
        contentControl  (ignore it)
    -->
    <xsl:template match="contentControl"/>
    <!--
        counter
    -->
    <xsl:template match="counter">
        <!-- First tried setting the from attrbute to just table, but then if there was a table embedded within a sister td of
            a td containing a counter, the numbering started over at one.  Using 'table[descendant::counter]' seemed to work, too.
        -->
        <xsl:variable name="sNumberFormat" select="normalize-space(ancestor::table[1]/@counterNumberFormat)"/>
        <xsl:choose>
            <xsl:when test="string-length($sNumberFormat) &gt; 0">
                <xsl:number from="table[descendant::counter]" level="any" format="{$sNumberFormat}"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="ancestor::table[1]/tr/*/table[descendant::counter]">
                        <xsl:value-of select="count(ancestor::tr[1]/preceding-sibling::tr[*/counter]) + 1"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:number from="table[descendant::counter]" level="any"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:text>.</xsl:text>
    </xsl:template>
    <!-- 
        comment (contents) 
    -->
    <xsl:template match="comment" mode="contents"/>
    <!-- 
        endnote (contents) 
    -->
    <xsl:template match="endnote" mode="contents"/>
    <xsl:template match="endnoteRef" mode="contents"/>
    <!-- 
        exampleRef (contents) 
    -->
    <xsl:template match="exampleRef" mode="contents">
        <xsl:apply-templates select="self::*"/>
    </xsl:template>
    <!-- 
        genericRef (contents) 
    -->
    <xsl:template match="genericRef" mode="contents">
        <xsl:apply-templates select="self::*"/>
    </xsl:template>
    <!-- 
        gloss (contents) 
    -->
    <xsl:template match="gloss" mode="contents">
        <xsl:apply-templates select="self::*">
            <xsl:with-param name="fInContents" select="'Y'"/>
        </xsl:apply-templates>
    </xsl:template>
    <xsl:template match="gloss" mode="contentOnly">
        <xsl:value-of select="key('LanguageID',@type)/@textbefore"/>
        <xsl:apply-templates select="child::node()" mode="contentOnly"/>
        <xsl:value-of select="key('LanguageID',@type)/@textafter"/>
    </xsl:template>
    <!-- 
        glossary terms
    -->
    <xsl:template match="glossaryTermDefinition" mode="Use">
        <xsl:apply-templates/>
    </xsl:template>
    <xsl:template match="glossaryTermRef" mode="Use">
        <xsl:apply-templates select="self::*"/>
    </xsl:template>
    <xsl:template match="glossaryTermTerm" mode="Use">
        <xsl:param name="glossaryTermRef"/>
        <xsl:choose>
            <xsl:when test="$glossaryTermRef and exsl:node-set($glossaryTermRef)/@capitalize='yes'">
                <xsl:value-of select="translate(substring(.,1,1),'abcdefghijklmnñopqrstuvwxyzáéíóúü', 'ABCDEFGHIJKLMNÑOPQRSTUVWXYZÁÉÍÓÚÜ')"/>
                <xsl:value-of select="substring(.,2)"/>
            </xsl:when>
            <xsl:otherwise>
                <!--                <xsl:apply-templates select="self::*"/>    -->
                <xsl:apply-templates/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <xsl:template match="glossaryTermsShownHere">
        <xsl:call-template name="HandleGlossaryTermsInTable"/>
    </xsl:template>
    <xsl:template match="glossaryTermsShownHereAsDefinitionList">
        <xsl:call-template name="HandleGlossaryTermsAsDefinitionList"/>
    </xsl:template>
    <xsl:template match="glossaryTermTerm | glossaryTermDefinition"/>
    <!--
        interlinearSource in single or listSingle
    -->
    <xsl:template match="interlinearSource[parent::single or parent::listSingle]">
        <xsl:call-template name="OutputInterlinearTextReference">
            <xsl:with-param name="sSource" select="."/>
        </xsl:call-template>
    </xsl:template>
    <!--
        iso639-3codesShownHere
    -->
    <xsl:template match="iso639-3codesShownHere">
        <xsl:choose>
            <xsl:when test="ancestor::endnote">
                <xsl:choose>
                    <xsl:when test="parent::p">
                        <xsl:call-template name="HandleISO639-3CodesInCommaSeparatedList"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <p>
                            <xsl:call-template name="HandleISO639-3CodesInCommaSeparatedList"/>
                        </p>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="not(ancestor::p)">
                <!-- ignore any other iso639-3codesShownHere in a p except when also in an endnote; everything else goes in a table -->
                <xsl:call-template name="HandleISO639-3CodesInTable"/>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--
        keyword
    -->
    <xsl:template match="keyword"/>
    <!-- 
        langData (contents) 
    -->
    <xsl:template match="langData" mode="contents">
        <xsl:apply-templates select="self::*">
            <xsl:with-param name="fInContents" select="'Y'"/>
        </xsl:apply-templates>
    </xsl:template>
    <xsl:template match="langData" mode="contentOnly">
        <xsl:value-of select="key('LanguageID',@type)/@textbefore"/>
        <xsl:value-of select="."/>
        <xsl:value-of select="key('LanguageID',@type)/@textafter"/>
    </xsl:template>
    <!--
        labelContent  (ignore it)
    -->
    <xsl:template match="labelContent"/>
    <!-- 
        object (contents) 
    -->
    <xsl:template match="object" mode="contents">
        <xsl:choose>
            <xsl:when test="ancestor::secTitle and key('TypeID',@type)/@font-style='normal'">
                <xsl:choose>
                    <xsl:when test="ancestor::langData or ancestor::gloss">
                        <xsl:choose>
                            <xsl:when test="ancestor::appendix and exsl:node-set($backMatterLayoutInfo)/appendixLayout/appendixTitleLayout/@font-style='italic'">
                                <xsl:call-template name="ForceItalicsInContentsTitle"/>
                            </xsl:when>
                            <xsl:when test="ancestor::chapter and exsl:node-set($bodyLayoutInfo)/chapterLayout/chapterTitleLayout/@font-style='italic'">
                                <xsl:call-template name="ForceItalicsInContentsTitle"/>
                            </xsl:when>
                            <xsl:when test="ancestor::chapterBeforePart and exsl:node-set($bodyLayoutInfo)/chapterLayout/chapterTitleLayout/@font-style='italic'">
                                <xsl:call-template name="ForceItalicsInContentsTitle"/>
                            </xsl:when>
                            <xsl:when test="ancestor::chapterInCollection and exsl:node-set($bodyLayoutInfo)/chapterInCollectionLayout/chapterTitleLayout/@font-style='italic'">
                                <xsl:call-template name="ForceItalicsInContentsTitle"/>
                            </xsl:when>
                            <xsl:when test="ancestor::part and exsl:node-set($bodyLayoutInfo)/partLayout/partTitleLayout/@font-style='italic'">
                                <xsl:call-template name="ForceItalicsInContentsTitle"/>
                            </xsl:when>
                            <xsl:when test="ancestor::section1 and exsl:node-set($bodyLayoutInfo)/section1Layout/sectionTitleLayout/@font-style='italic'">
                                <xsl:call-template name="ForceItalicsInContentsTitle"/>
                            </xsl:when>
                            <xsl:when test="ancestor::section2 and exsl:node-set($bodyLayoutInfo)/section2Layout/sectionTitleLayout/@font-style='italic'">
                                <xsl:call-template name="ForceItalicsInContentsTitle"/>
                            </xsl:when>
                            <xsl:when test="ancestor::section3 and exsl:node-set($bodyLayoutInfo)/section3Layout/sectionTitleLayout/@font-style='italic'">
                                <xsl:call-template name="ForceItalicsInContentsTitle"/>
                            </xsl:when>
                            <xsl:when test="ancestor::section4 and exsl:node-set($bodyLayoutInfo)/section4Layout/sectionTitleLayout/@font-style='italic'">
                                <xsl:call-template name="ForceItalicsInContentsTitle"/>
                            </xsl:when>
                            <xsl:when test="ancestor::section5 and exsl:node-set($bodyLayoutInfo)/section5Layout/sectionTitleLayout/@font-style='italic'">
                                <xsl:call-template name="ForceItalicsInContentsTitle"/>
                            </xsl:when>
                            <xsl:when test="ancestor::section6 and exsl:node-set($bodyLayoutInfo)/section6Layout/sectionTitleLayout/@font-style='italic'">
                                <xsl:call-template name="ForceItalicsInContentsTitle"/>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:apply-templates select="self::*"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="self::*"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <xsl:template match="object" mode="contentOnly">
        <xsl:value-of select="key('TypeID',@type)/@before"/>
        <xsl:value-of select="."/>
        <xsl:value-of select="key('TypeID',@type)/@after"/>
    </xsl:template>
    <!-- 
        sectionRef (contents) 
    -->
    <xsl:template match="sectionRef" mode="contents">
        <xsl:apply-templates select="self::*"/>
    </xsl:template>
    <!--
        annotatedBibliographyType
    -->
    <xsl:template match="annotatedBibliographyType"/>
    <!--
        annotation
    -->
    <xsl:template match="annotation">
        <xsl:apply-templates/>
    </xsl:template>
    <!--  
        appendix
    -->
    <xsl:template mode="numberAppendix" match="*">
        <xsl:if test="ancestor::chapterInCollection">
            <xsl:apply-templates select="ancestor::chapterInCollection" mode="numberChapter"/>
            <xsl:text>.</xsl:text>
        </xsl:if>
        <xsl:number level="multiple" count="appendix | section1 | section2 | section3 | section4 | section5 | section6" format="A.1"/>
    </xsl:template>
    <xsl:template mode="labelNumberAppendix" match="*">
        <xsl:choose>
            <xsl:when test="@label">
                <xsl:value-of select="@label"/>
            </xsl:when>
            <xsl:otherwise>Appendix</xsl:otherwise>
        </xsl:choose>
        <xsl:text>&#x20;</xsl:text>
        <xsl:number level="single" count="appendix" format="A"/>
    </xsl:template>
    <!--  
        chapter
    -->
    <xsl:template mode="numberChapter" match="*">
        <xsl:choose>
            <xsl:when test="$chapterNumberFormat='lowerroman'">
                <xsl:number level="any" count="chapter | chapterInCollection" format="i"/>
            </xsl:when>
            <xsl:when test="$chapterNumberFormat='upperroman'">
                <xsl:number level="any" count="chapter | chapterInCollection" format="I"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:number level="any" count="chapter | chapterInCollection" format="1"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        part
    -->
    <xsl:template mode="numberPart" match="*">
        <xsl:number level="multiple" count="part" format="I"/>
    </xsl:template>
    <!--  
        endnote
    -->
    <xsl:template mode="endnote" match="*">
        <xsl:choose>
            <xsl:when test="$chapters">
                <xsl:choose>
                    <xsl:when test="/xlingpaper/styledPaper/publisherStyleSheet[1]/bodyLayout/chapterLayout/@resetEndnoteNumbering='no'">
                        <xsl:number level="any" count="endnote[not(parent::author or ancestor::framedUnit)] | endnoteRef[not(ancestor::endnote)]" format="1"/>
                    </xsl:when>
                    <xsl:when test="ancestor::appendix">
                        <xsl:number level="any" count="endnote[not(parent::author or ancestor::framedUnit)] | endnoteRef" from="appendix" format="1"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:number level="any" count="endnote[not(parent::author or ancestor::framedUnit)] | endnoteRef" from="chapter | chapterInCollection" format="1"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:number level="any" count="endnote[not(parent::author or ancestor::framedUnit)] | endnoteRef[not(ancestor::endnote)]" format="1"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        example
    -->
    <xsl:template mode="example" match="*">
        <xsl:choose>
            <xsl:when test="exsl:node-set($contentLayoutInfo)/exampleLayout/@startNumberingOverAtEachChapter='yes'">
                <xsl:number level="any" from="chapter | chapterInCollection | appendix" count="example[not(ancestor::endnote or ancestor::framedUnit)]" format="1"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:number level="any" count="example[not(ancestor::endnote or ancestor::framedUnit)]" format="1"/>
            </xsl:otherwise>
        </xsl:choose>


    </xsl:template>
    <!--  
        exampleInEndnote
    -->
    <xsl:template mode="exampleInEndnote" match="*">
        <xsl:number level="single" count="example" format="i"/>
    </xsl:template>
    <!--  
        exampleInFramedUnit
    -->
    <xsl:template mode="exampleInFramedUnit" match="*">
        <xsl:number level="single" count="example" format="1"/>
    </xsl:template>
    <!--  
        figure
    -->
    <xsl:template mode="figure" match="*">
        <xsl:number level="any" count="figure[not(ancestor::endnote or ancestor::framedUnit)]" format="1"/>
    </xsl:template>
    <!--  
        figureInEndnote
    -->
    <xsl:template mode="figureInEndnote" match="*">
        <xsl:number level="single" count="figure" format="i"/>
    </xsl:template>
    <!--  
        figureInFramedUnit
    -->
    <xsl:template mode="figureInFramedUnit" match="*">
        <xsl:number level="single" count="figure" format="1"/>
    </xsl:template>
    <!--  
        tablenumbered
    -->
    <xsl:template mode="tablenumbered" match="*">
        <xsl:number level="any" count="tablenumbered[not(ancestor::endnote or ancestor::framedUnit)]" format="1"/>
    </xsl:template>
    <!--  
        tablenumberedInEndnote
    -->
    <xsl:template mode="tablenumberedInEndnote" match="*">
        <xsl:number level="single" count="tablenumbered" format="1"/>
    </xsl:template>
    <!--  
        exampleInFramedUnit
    -->
    <xsl:template mode="tablenumberedInFramedUnit" match="*">
        <xsl:number level="single" count="tablenumbered" format="1"/>
    </xsl:template>
    <!--
        exampleHeading in NotTextRef mode
    -->
    <xsl:template match="exampleHeading" mode="NoTextRef">
        <xsl:apply-templates select="."/>
    </xsl:template>
    <!--
        AddAnyTitleAttribute
    -->
    <xsl:template name="AddAnyTitleAttribute">
        <xsl:param name="sId"/>
        <xsl:if test="exsl:node-set($lingPaper)/@showExampleIdOnHoverInWebpage='yes'">
            <xsl:attribute name="title">
                <xsl:value-of select="$sId"/>
            </xsl:attribute>
        </xsl:if>
    </xsl:template>
    <!--
        ConvertLastNameFirstNameToFirstNameLastName
    -->
    <xsl:template name="ConvertLastNameFirstNameToFirstNameLastName">
        <xsl:param name="sCitedWorkAuthor"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($referencesLayoutInfo)/@useAuthorSurnameCommaGivenNameInCitations='yes'">
                <xsl:value-of select="$sCitedWorkAuthor"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="sFirstAuthorLastName" select="substring-before($sCitedWorkAuthor,',')"/>
                <xsl:variable name="sFirstAuthorFirstName">
                    <xsl:variable name="sTryOne" select="normalize-space(substring-before(substring-after($sCitedWorkAuthor,','),','))"/>
                    <xsl:choose>
                        <xsl:when test="string-length($sTryOne) &gt; 0">
                            <!-- there are three or more names (we assume), so what comes before the second comma should be the first name -->
                            <xsl:value-of select="$sTryOne"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:variable name="sTryTwo" select="normalize-space(substring-before(substring-after($sCitedWorkAuthor,','),';'))"/>
                            <xsl:choose>
                                <xsl:when test="string-length($sTryTwo) &gt; 0">
                                    <!-- there are three or more names (we assume), so what comes before the semi-colon should be the first name -->
                                    <xsl:value-of select="$sTryTwo"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <!-- assume it is only one or two authors -->
                                    <xsl:choose>
                                        <xsl:when test="string-length($sAuthorNamesWordForAnd) &gt; 0 and contains($sCitedWorkAuthor,$sAuthorNamesWordForAnd)">
                                            <xsl:value-of select="normalize-space(substring-before(substring-after($sCitedWorkAuthor,','),concat(' ',$sAuthorNamesWordForAnd,' ')))"/>
                                        </xsl:when>
                                        <xsl:when test="contains($sCitedWorkAuthor,' &amp; ')">
                                            <!-- there is an ampersand, so assume there are two authors and the first name is what comes between the first comma and the ampersand -->
                                            <xsl:value-of select="normalize-space(substring-before(substring-after($sCitedWorkAuthor,','),' &amp; '))"/>
                                        </xsl:when>
                                        <xsl:when test="contains($sCitedWorkAuthor,' and ')">
                                            <!-- there is an 'and', so assume there are two authors and the first name is what comes between the first comma and the 'and' -->
                                            <xsl:value-of select="normalize-space(substring-before(substring-after($sCitedWorkAuthor,','),' and '))"/>
                                        </xsl:when>
                                        <xsl:when test="contains($sCitedWorkAuthor,' y ')">
                                            <!-- there is an 'y' (Spanish), so assume there are two authors and the rest is what comes after the 'y' -->
                                            <xsl:value-of select="normalize-space(substring-before(substring-after($sCitedWorkAuthor,','),' y '))"/>
                                        </xsl:when>
                                        <xsl:when test="contains($sCitedWorkAuthor,' e I') or contains($sCitedWorkAuthor,' e i')">
                                            <!-- there is an 'e [Ii]' (Spanish), so assume there are two authors and the rest is what comes after the 'e' -->
                                            <xsl:value-of select="normalize-space(substring-before(substring-after($sCitedWorkAuthor,','),' e '))"/>
                                        </xsl:when>
                                        <xsl:when test="contains($sCitedWorkAuthor,' et ')">
                                            <!-- there is an 'et' (French), so assume there are two authors and the rest is what comes after the 'et' -->
                                            <xsl:value-of select="normalize-space(substring-before(substring-after($sCitedWorkAuthor,','),' et '))"/>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <!-- it must be only one author -->
                                            <xsl:value-of select="normalize-space(substring-after($sCitedWorkAuthor,','))"/>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:variable name="sSecondAuthorEtc">
                    <xsl:variable name="sTryOne" select="substring-after(substring-after($sCitedWorkAuthor,','),',')"/>
                    <xsl:choose>
                        <xsl:when test="string-length($sTryOne) &gt; 0">
                            <!-- there are three or more names (we assume), so what comes before the second comma should be the rest -->
                            <xsl:text>, </xsl:text>
                            <xsl:value-of select="$sTryOne"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:variable name="sTryTwo" select="substring-after(substring-after($sCitedWorkAuthor,','),';')"/>
                            <xsl:choose>
                                <xsl:when test="string-length($sTryTwo) &gt; 0">
                                    <!-- there are three or more names (we assume), so what comes before the semi-colon should be the first name -->
                                    <xsl:text>; </xsl:text>
                                    <xsl:value-of select="$sTryTwo"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <!-- assume it is only one or two authors -->
                                    <xsl:choose>
                                        <xsl:when test="contains($sCitedWorkAuthor,' &amp; ')">
                                            <!-- there is an ampersand, so assume there are two authors and the rest is what comes after the ampersand -->
                                            <xsl:text> &amp; </xsl:text>
                                            <xsl:value-of select="normalize-space(substring-after(substring-after($sCitedWorkAuthor,','),' &amp; '))"/>
                                        </xsl:when>
                                        <xsl:when test="contains($sCitedWorkAuthor,' and ')">
                                            <!-- there is an 'and', so assume there are two authors and the rest is what comes after the 'and' -->
                                            <xsl:text> and </xsl:text>
                                            <xsl:value-of select="normalize-space(substring-after(substring-after($sCitedWorkAuthor,','),' and '))"/>
                                        </xsl:when>
                                        <xsl:when test="contains($sCitedWorkAuthor,' y ')">
                                            <!-- there is an 'y' (Spanish), so assume there are two authors and the rest is what comes after the 'y' -->
                                            <xsl:text> y </xsl:text>
                                            <xsl:value-of select="normalize-space(substring-after(substring-after($sCitedWorkAuthor,','),' y '))"/>
                                        </xsl:when>
                                        <xsl:when test="contains($sCitedWorkAuthor,' e I') or contains($sCitedWorkAuthor,' e i')">
                                            <!-- there is an 'e [Ii]' (Spanish), so assume there are two authors and the rest is what comes after the 'e' -->
                                            <xsl:text> e </xsl:text>
                                            <xsl:value-of select="normalize-space(substring-after(substring-after($sCitedWorkAuthor,','),' e '))"/>
                                        </xsl:when>
                                        <xsl:when test="contains($sCitedWorkAuthor,' et ')">
                                            <!-- there is an 'et' (French), so assume there are two authors and the rest is what comes after the 'et' -->
                                            <xsl:text> et </xsl:text>
                                            <xsl:value-of select="normalize-space(substring-after(substring-after($sCitedWorkAuthor,','),' et '))"/>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <!-- it must be only one author -->
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:value-of select="$sFirstAuthorFirstName"/>
                <xsl:text>&#x20;</xsl:text>
                <xsl:value-of select="$sFirstAuthorLastName"/>
                <xsl:if test="string-length($sSecondAuthorEtc) &gt; 0">
                    <xsl:value-of select="$sSecondAuthorEtc"/>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>
    <!--  
        ConvertToPoints
    -->
    <xsl:template name="ConvertToPoints">
        <xsl:param name="sValue"/>
        <xsl:param name="iValue"/>
        <xsl:variable name="sUnit">
            <xsl:call-template name="GetUnitOfMeasure">
                <xsl:with-param name="sValue" select="$sValue"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$sUnit='in'">
                <xsl:value-of select="number($iValue * 72.27)"/>
            </xsl:when>
            <xsl:when test="$sUnit='mm'">
                <xsl:value-of select="number($iValue * 2.845275591)"/>
            </xsl:when>
            <xsl:when test="$sUnit='cm'">
                <xsl:value-of select="number($iValue * 28.45275591)"/>
            </xsl:when>
            <xsl:otherwise>
                <!-- if it's not inches and not millimeters and not centimeters, punt -->
                <xsl:value-of select="$iValue"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        CreateContentsID
    -->
    <xsl:template name="CreateContentsID">
        <xsl:param name="contentsLayoutToUse"/>
        <xsl:call-template name="GetIdToUse">
            <xsl:with-param name="sBaseId" select="$sContentsID"/>
        </xsl:call-template>
        <xsl:if test="exsl:node-set($contentsLayoutToUse)[ancestor-or-self::backMatterLayout]">
            <xsl:value-of select="$sBackMatterContentsIdAddOn"/>
        </xsl:if>
    </xsl:template>
    <!--
        DetermineIfListsShareSameISOCode
    -->
    <xsl:template name="DetermineIfListsShareSameISOCode">
        <xsl:choose>
            <xsl:when test="exsl:node-set($lingPaper)/@showiso639-3codeininterlinear='yes' or ancestor-or-self::example/@showiso639-3codes='yes'">
                <xsl:choose>
                    <xsl:when test="listInterlinear or listWord or listSingle">
                        <xsl:variable name="sIsoCodeOfFirst"
                            select="key('LanguageID',(descendant::langData[1] | key('InterlinearReferenceID',child::*[substring(name(),1,4)='list'][1]/interlinearRef/@textref)[1]/descendant::langData[1])/@lang)/@ISO639-3Code"/>
                        <xsl:for-each select="*/following-sibling::*">
                            <xsl:variable name="sIsoCodeOfFollowingFirst"
                                select="key('LanguageID',(descendant::langData[1] | key('InterlinearReferenceID',interlinearRef/@textref)[1]/descendant::langData[1])/@lang)/@ISO639-3Code"/>
                            <xsl:if test="$sIsoCodeOfFollowingFirst != $sIsoCodeOfFirst">
                                <xsl:text>N</xsl:text>
                            </xsl:if>
                        </xsl:for-each>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>Y</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>Y</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoAnyEqualsSignBetweenAbbrAndDefinition
    -->
    <xsl:template name="DoAnyEqualsSignBetweenAbbrAndDefinition">
        <xsl:choose>
            <xsl:when test="string-length(exsl:node-set($contentLayoutInfo)/abbreviationsInFootnoteLayout/@textBetweenAbbreviationAndDefinition) &gt; 0">
                <xsl:value-of select="exsl:node-set($contentLayoutInfo)/abbreviationsInFootnoteLayout/@textBetweenAbbreviationAndDefinition"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text> = </xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        DoInterlinearRefCitationContent
    -->
    <xsl:template name="DoInterlinearRefCitationContent">
        <xsl:param name="sRef"/>
        <xsl:variable name="interlinear" select="key('InterlinearReferenceID',$sRef)"/>
        <xsl:if test="not(@lineNumberOnly) or @lineNumberOnly!='yes'">
            <xsl:choose>
                <xsl:when test="exsl:node-set($interlinear)/../textInfo/shortTitle and string-length(exsl:node-set($interlinear)/../textInfo/shortTitle) &gt; 0">
                    <xsl:apply-templates select="exsl:node-set($interlinear)/../textInfo/shortTitle/child::node()[name()!='endnote']"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates select="exsl:node-set($interlinear)/../textInfo/textTitle/child::node()[name()!='endnote']"/>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="string-length(exsl:node-set($contentLayoutInfo)/interlinearTextLayout/@textbeforeReferenceNumber) &gt; 0">
                    <!-- do nothing here; it is handled in DoInterlinearTextNumber -->
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>:</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:call-template name="DoInterlinearTextNumber">
            <xsl:with-param name="sRef" select="$sRef"/>
            <xsl:with-param name="interlinear" select="$interlinear"/>
        </xsl:call-template>
    </xsl:template>
    <!--  
        DoInterlinearTextNumber
    -->
    <xsl:template name="DoInterlinearTextNumber">
        <xsl:param name="sRef"/>
        <xsl:param name="interlinear"/>
        <xsl:variable name="sBefore" select="exsl:node-set($contentLayoutInfo)/interlinearTextLayout/@textbeforeReferenceNumber"/>
        <xsl:variable name="sAfter" select="exsl:node-set($contentLayoutInfo)/interlinearTextLayout/@textafterReferenceNumber"/>
        <xsl:if test="string-length($sBefore) &gt; 0">
            <xsl:value-of select="$sBefore"/>
        </xsl:if>
        <xsl:choose>
            <xsl:when test="substring($sRef,1,4)='T-ID'">
                <xsl:value-of select="substring-after(substring-after($sRef,'-'),'-')"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="count(exsl:node-set($interlinear)/preceding-sibling::interlinear) + 1"/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="string-length($sAfter) &gt; 0">
            <xsl:value-of select="$sAfter"/>
        </xsl:if>
    </xsl:template>
    <!--  
        DoInterlinearTextReferenceLink
    -->
    <xsl:template name="DoInterlinearTextReferenceLink">
        <xsl:param name="sRef" select="@textref"/>
        <xsl:param name="sAttrName" select="'href'"/>
        <xsl:param name="sExtension" select="'pdf'"/>
        <xsl:attribute name="{$sAttrName}">
            <xsl:variable name="referencedInterlinear" select="key('InterlinearReferenceID',$sRef)"/>
            <xsl:choose>
                <xsl:when test="exsl:node-set($referencedInterlinear)[ancestor::referencedInterlinearTexts]">
                    <xsl:value-of select="exsl:node-set($referencedInterlinear)/ancestor::referencedInterlinearText/@url"/>
                    <xsl:text>.</xsl:text>
                    <xsl:value-of select="$sExtension"/>
                    <xsl:text>#</xsl:text>
                    <xsl:value-of select="$sRef"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:if test="$sAttrName='href'">
                        <xsl:text>#</xsl:text>
                    </xsl:if>
                    <xsl:value-of select="$sRef"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:attribute>
    </xsl:template>
    <!--  
        DoISO639-3codeRefContent
    -->
    <xsl:template name="DoISO639-3codeRefContent">
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
        DoLiteralLabel
    -->
    <xsl:template name="DoLiteralLabel">
        <xsl:if test="name()='literal'">
            <xsl:choose>
                <xsl:when test="$literalLabelLayoutInfo">
                    <xsl:call-template name="HandleLiteralLabelLayoutInfo">
                        <xsl:with-param name="layoutInfo" select="$literalLabelLayoutInfo"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:when test="string-length($sLiteralLabel) &gt; 0">
                    <xsl:value-of select="$sLiteralLabel"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>Lit. </xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--  
        DoNestedAnnotations
    -->
    <xsl:template name="DoNestedAnnotations">
        <xsl:param name="sList"/>
        <xsl:variable name="sNewList" select="concat(normalize-space($sList),' ')"/>
        <xsl:variable name="sFirst" select="substring-before($sNewList,' ')"/>
        <xsl:variable name="sRest" select="substring-after($sNewList,' ')"/>
        <xsl:if test="string-length($sFirst) &gt; 0">
            <xsl:call-template name="DoAnnotation">
                <xsl:with-param name="sAnnotation" select="$sFirst"/>
            </xsl:call-template>
            <xsl:if test="$sRest">
                <xsl:call-template name="DoNestedAnnotations">
                    <xsl:with-param name="sList" select="$sRest"/>
                </xsl:call-template>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--  
        DoOutputCitationContents
    -->
    <xsl:template name="DoOutputCitationContents">
        <xsl:param name="refer"/>
        <xsl:choose>
            <xsl:when test="ancestor::chapterInCollection/descendant::references">
                <xsl:call-template name="OutputCitationContents">
                    <xsl:with-param name="refer" select="$refer"/>
                    <xsl:with-param name="refWorks" select="ancestor::chapterInCollection/descendant::references/refWork"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="OutputCitationContents">
                    <xsl:with-param name="refer" select="$refer"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoQuoteTextAfter
    -->
    <xsl:template name="DoQuoteTextAfter">
        <xsl:variable name="sTextAfter" select="exsl:node-set($contentLayoutInfo)/quoteLayout/@textafter"/>
        <xsl:choose>
            <xsl:when test="string-length($sTextAfter)&gt;0">
                <xsl:value-of select="$sTextAfter"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sRdquo"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoQuoteTextBefore
    -->
    <xsl:template name="DoQuoteTextBefore">
        <xsl:variable name="sTextBefore" select="exsl:node-set($contentLayoutInfo)/quoteLayout/@textbefore"/>
        <xsl:choose>
            <xsl:when test="string-length($sTextBefore)&gt;0">
                <xsl:value-of select="$sTextBefore"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sLdquo"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        DoRefAuthors
    -->
    <xsl:template name="DoRefAuthors">
        <xsl:param name="refAuthors" select="//refAuthor[not(ancestor::chapterInCollection/backMatter/references)]"/>
        <xsl:param name="citations" select="//citation[not(ancestor::chapterInCollection/backMatter/references) and not(ancestor::abbrDefinition)]"/>
        <xsl:variable name="directlyCitedAuthors"
            select="exsl:node-set($refAuthors)[refWork[@id=exsl:node-set($citations)[not(ancestor::comment) and not(ancestor::referencedInterlinearText) and not(ancestor::glossaryTerm) and not(ancestor::abbrDefinition)][not(ancestor::refWork) or ancestor::annotation[@id=//annotationRef/@annotation] or ancestor::refWork[@id=exsl:node-set($citations)[not(ancestor::refWork)]/@ref]]/@ref]]"/>
        <xsl:variable name="impliedAuthors" select="exsl:node-set($refWorks)[@id=saxon:node-set($collOrProcVolumesToInclude)/refWork/@id]/parent::refAuthor"/>
        <xsl:variable name="gtAuthors" select="//refAuthor[refWork/@id=//citation[ancestor::glossaryTerm[key('GlossaryTermRefs',@id)]]/@ref]"/>
        <xsl:variable name="abbreviations">
            <xsl:choose>
                <xsl:when test="ancestor::chapterInCollection/backMatter/abbreviations">
                    <xsl:copy-of select="ancestor::chapterInCollection/backMatter/abbreviations/abbreviation[descendant::citation[not(ancestor::comment)]]"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:copy-of select="//abbreviation[not(ancestor::chapterInCollection/backMatter/abbreviations)][descendant::citation[not(ancestor::comment)]]"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="abbrRefs">
            <xsl:choose>
                <xsl:when test="ancestor::chapterInCollection/backMatter/abbreviations">
                    <xsl:copy-of select="ancestor::chapterInCollection/descendant::abbrRef"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:copy-of select="//abbrRef[not(ancestor::chapterInCollection/backMatter/abbreviations)]"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="citationsInUsedAbbreviations"
            select="saxon:node-set($abbreviations)/abbreviation[saxon:node-set($abbrRefs)/abbrRef[not(ancestor::referencedInterlinearText) or ancestor::interlinear[key('InterlinearRef',@text)]]/@abbr=@id]/descendant::citation[not(ancestor::comment)]"/>
        <xsl:variable name="worksCitedInUsedAbbreviationDefinitions" select="exsl:node-set($refWorks)[@id=exsl:node-set($citationsInUsedAbbreviations)/@ref]/parent::refAuthor"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($lingPaper)/@sortRefsAbbrsByDocumentLanguage='yes'">
                <xsl:variable name="sLang">
                    <xsl:variable name="sLangCode" select="normalize-space(exsl:node-set($lingPaper)/@xml:lang)"/>
                    <xsl:choose>
                        <xsl:when test="string-length($sLangCode) &gt; 0">
                            <xsl:value-of select="$sLangCode"/>
                        </xsl:when>
                        <xsl:otherwise>en</xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:for-each select="$directlyCitedAuthors | $impliedAuthors | $gtAuthors | saxon:node-set($worksCitedInUsedAbbreviationDefinitions)">
                    <xsl:sort lang="{$sLang}" select="@name"/>
                    <xsl:call-template name="DoRefWorks">
                        <xsl:with-param name="sLang" select="$sLang"/>
                        <xsl:with-param name="citations" select="$citations | $citationsInUsedAbbreviations"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <xsl:for-each select="$directlyCitedAuthors | $impliedAuthors | $gtAuthors | saxon:node-set($worksCitedInUsedAbbreviationDefinitions)">
                    <xsl:call-template name="DoRefWorks">
                        <xsl:with-param name="citations" select="$citations | $citationsInUsedAbbreviations"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        DoRefWorks
    -->
    <xsl:template name="DoRefWorks">
        <xsl:param name="sLang"/>
        <xsl:param name="citations"/>
        <xsl:variable name="thisAuthor" select="."/>
        <xsl:variable name="works"
        select="refWork[@id=exsl:node-set($citations)[not(ancestor::comment) and not(ancestor::annotation)][not(ancestor::refWork) or ancestor::refWork[@id=exsl:node-set($citations)[not(ancestor::refWork)]/@ref]]/@ref] | exsl:node-set($refWorks)[@id=saxon:node-set($collOrProcVolumesToInclude)/refWork/@id][parent::refAuthor=$thisAuthor] | refWork[@id=exsl:node-set($citationsInAnnotationsReferredTo)[not(ancestor::comment)]/@ref]"/>
        <xsl:choose>
            <xsl:when test="string-length($sLang) &gt; 0">
                <xsl:variable name="sortedWorks">
                    <xsl:for-each select="$works">
                        <xsl:sort lang="{$sLang}" select="refDate"/>
                        <xsl:sort lang="{$sLang}" select="refTitle"/>
                        <xsl:copy-of select="."/>
                    </xsl:for-each>
                </xsl:variable>
                <xsl:for-each select="$works">
                    <xsl:sort lang="{$sLang}" select="refDate"/>
                    <xsl:sort lang="{$sLang}" select="refTitle"/>
                    <xsl:call-template name="DoRefWorkPrep"/>
                    <xsl:call-template name="DoRefWork">
                        <xsl:with-param name="works" select="$works"/>
                        <xsl:with-param name="author" select="$thisAuthor"/>
                        <xsl:with-param name="sortedWorks" select="saxon:node-set($sortedWorks)"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <xsl:for-each select="$works">
                    <xsl:call-template name="DoRefWorkPrep"/>
                    <xsl:call-template name="DoRefWork">
                        <xsl:with-param name="works" select="$works"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetAbbreviationLanguageCode
    -->
    <xsl:template name="GetAbbreviationLanguageCode">
        <xsl:variable name="sLangCode">
            <xsl:choose>
                <xsl:when test="string-length($abbrLang) &gt; 0">
                    <xsl:value-of select="$abbrLang"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$documentLang"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="string-length($sLangCode) &gt; 0">
                <xsl:value-of select="$sLangCode"/>
            </xsl:when>
            <xsl:otherwise>en</xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        GetAuthorsAsCommaSeparatedList
    -->
    <xsl:template name="GetAuthorsAsCommaSeparatedList">
        <xsl:for-each select="frontMatter/author/child::node()[name()!='endnote' and name()!='xxe-sn']">
            <xsl:value-of select="."/>
            <xsl:if test="position()!=last()">
                <xsl:text>, </xsl:text>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>
    <!--
        GetCollOrProcVolumesToInclude
    -->
    <xsl:template name="GetCollOrProcVolumesToInclude">
        <xsl:choose>
            <xsl:when test="exsl:node-set($referencesLayoutInfo)/@usecitationformatwhennumberofsharedpaperis=0">
                <!-- do nothing -->
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="iSharedPapers">
                    <xsl:choose>
                        <xsl:when test="string(number(exsl:node-set($referencesLayoutInfo)/@usecitationformatwhennumberofsharedpaperis))='NaN'">
                            <xsl:text>1</xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="exsl:node-set($referencesLayoutInfo)/@usecitationformatwhennumberofsharedpaperis - 1"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:variable name="directlyCitedWorks" select="exsl:node-set($refWorks)[@id=//citation[not(ancestor::comment)]/@ref]"/>
                <xsl:variable name="citedCollOrProcWithCitation">
                    <xsl:for-each select="exsl:node-set($directlyCitedWorks)/collection/collCitation | exsl:node-set($directlyCitedWorks)/proceedings/procCitation">
                        <xsl:sort select="@refToBook"/>
                        <xsl:copy-of select="."/>
                    </xsl:for-each>
                </xsl:variable>
                <xsl:for-each select="saxon:node-set($citedCollOrProcWithCitation)/collCitation | saxon:node-set($citedCollOrProcWithCitation)/procCitation">
                    <xsl:variable name="thisRefToBook" select="@refToBook"/>
                    <xsl:variable name="precedingSiblings" select="preceding-sibling::*[@refToBook=$thisRefToBook]"/>
                    <!-- to set the required number, use count of preceding is greater than or equal to threshold minus 1 -->
                    <xsl:if test="$precedingSiblings and count($precedingSiblings) &gt;= $iSharedPapers">
                        <xsl:copy-of select="exsl:node-set($refWorks)[@id=$thisRefToBook]"/>
                    </xsl:if>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetCountOfEndnotesIncludingAnyInInterlinearRefs
    -->
    <xsl:template name="GetCountOfEndnotesIncludingAnyInInterlinearRefs">
        <xsl:param name="iAdjust"/>
        <xsl:param name="iPreviousEndnotesInCurrentInterlinearRef" select="0"/>
        <xsl:param name="iTablenumberedAdjust" select="0"/>
        <xsl:variable name="iPreviousEndnotes">
            <xsl:variable name="iPreviousEndnotesPass1">
                <xsl:choose>
                    <xsl:when test="$bEndnoteRefIsDirectLinkToEndnote='Y'">
                        <xsl:number level="any" count="endnote[not(parent::author)]" format="1"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:number level="any" count="endnote[not(parent::author)] | endnoteRef[not(ancestor::endnote)][not(@showNumberOnly='yes')]" format="1"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:variable name="iEndnoteInTitle">
                <xsl:call-template name="GetCountOfEndnoteInTitleUsingSymbol"/>
            </xsl:variable>
            <xsl:choose>
                <xsl:when test="$iPreviousEndnotesPass1!=''">
                    <xsl:value-of select="$iPreviousEndnotesPass1 - $iEndnoteInTitle"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$iEndnoteInTitle"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <!-- Following was original attempt at keeping track of endnotes in interlinears referred to by interlinearRef elements.
            Beginning with version 3.5.3 (2.35.3) we always ignore endnotes in interlinears referred to by interlinearRef elements. -->
        <!--<xsl:variable name="iIncludeCurrentInterlinearRef">
            <xsl:choose>
                <xsl:when test="name()='interlinearRef'">
                    <xsl:value-of select="$iAdjust"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>0</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>-->
     <!--   <xsl:variable name="endnotesInPrecedingInterlinearRefs" select="(descendant::interlinearRef[ancestor::referencedInterlinearTexts] | preceding::interlinearRef)[key('InterlinearReferenceID',@textref)[ancestor::referencedInterlinearTexts]/descendant::endnote]"/>
        <xsl:variable name="sCount">
            <xsl:for-each select="$endnotesInPrecedingInterlinearRefs">
                <xsl:variable name="iCountOfEndnotes" select="count(key('InterlinearReferenceID',@textref)/descendant::endnote)"/>
                <xsl:value-of select="substring($sYs,1,$iCountOfEndnotes)"/>
            </xsl:for-each>
        </xsl:variable>
        <xsl:variable name="iCountOfEndnotesInPrecedingInterlinearRefs" select="string-length($sCount)"/>
        <!-\-        <xsl:variable name="iCountOfEndnotesInPrecedingInterlinearRefs" select="count((descendant::interlinearRef | preceding::interlinearRef)[key('InterlinearReferenceID',@textref)/descendant::endnote])"/>-\->
        <!-\-        <xsl:variable name="i2CountOfEndnotesInPrecedingInterlinearRefs" select="count((descendant::interlinearRef | preceding::interlinearRef)[key('InterlinearReferenceID',@textref)/descendant::endnote])"/>-\->
        <xsl:value-of select="$iPreviousEndnotes + $iCountOfEndnotesInPrecedingInterlinearRefs + $iIncludeCurrentInterlinearRef + $iPreviousEndnotesInCurrentInterlinearRef+$iTablenumberedAdjust"/>-->
        <xsl:value-of select="$iPreviousEndnotes + $iPreviousEndnotesInCurrentInterlinearRef+$iTablenumberedAdjust"/>
    </xsl:template>
    <!--  
        GetCountOfEndnotesIncludingAnyInInterlinearRefsBook
    -->
    <xsl:template name="GetCountOfEndnotesIncludingAnyInInterlinearRefsBook">
        <xsl:param name="iAdjust"/>
        <xsl:param name="iTablenumberedAdjust" select="0"/>
        <xsl:variable name="iPreviousEndnotes">
            <xsl:variable name="iPreviousEndnotesPass1">
                <xsl:choose>
                    <xsl:when test="$bEndnoteRefIsDirectLinkToEndnote='Y'">
                        <xsl:choose>
                            <xsl:when test="$chapters and /xlingpaper/styledPaper/publisherStyleSheet[1]/bodyLayout/chapterLayout/@resetEndnoteNumbering='no'">
                                <xsl:number level="any" count="endnote[not(parent::author)] | endnoteRef[not(ancestor::endnote)]" format="1"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:choose>
                                    <xsl:when test="ancestor::part and not(ancestor::chapter) and not(ancestor::chapterInCollection)">
                                        <xsl:number level="any" count="endnote[not(parent::author)]" format="1" from="part"/>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:number level="any" count="endnote[not(parent::author)]" format="1"
                                            from="chapter | chapterInCollection | appendix | glossary | acknowledgements | preface | abstract"/>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:choose>
                            <xsl:when test="$chapters and /xlingpaper/styledPaper/publisherStyleSheet[1]/bodyLayout/chapterLayout/@resetEndnoteNumbering='no'">
                                <xsl:number level="any" count="endnote[not(parent::author or ancestor::framedUnit)] | endnoteRef[not(ancestor::endnote)]" format="1"/>
                            </xsl:when>
                            <xsl:when test="ancestor::part and not(ancestor::chapter) and not(ancestor::chapterInCollection)">
                                <xsl:number level="any" count="endnote[not(parent::autho or ancestor::framedUnitr)]" format="1" from="part"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:number level="any" count="endnote[not(ancestor::author or ancestor::framedUnit)] | endnoteRef[not(ancestor::endnote)][not(@showNumberOnly='yes')]" format="1"
                                    from="chapter | chapterInCollection | appendix | glossary | acknowledgements | preface | abstract"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:variable name="iEndnoteInTitle">
                <xsl:call-template name="GetCountOfEndnoteInTitleUsingSymbol"/>
            </xsl:variable>
            <xsl:choose>
                <xsl:when test="$iPreviousEndnotesPass1!=''">
                    <xsl:value-of select="$iPreviousEndnotesPass1 - $iEndnoteInTitle"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$iEndnoteInTitle"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <!-- Following was original attempt at keeping track of endnotes in interlinears referred to by interlinearRef elements.
            Beginning with version 3.5.3 (2.35.3) we always ignore endnotes in interlinears referred to by interlinearRef elements. -->
        <!--<xsl:variable name="iIncludeCurrentInterlinearRef">
            <xsl:choose>
                <xsl:when test="name()='interlinearRef'">
                    <xsl:value-of select="$iAdjust"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>0</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>-->
         <!--we use the following for efficiency sake even though we treat some elments the same (i.e. they do not have an @id)
        <xsl:variable name="sCurrentAncestorId"
            select="ancestor::chapter/@id | ancestor::chapterInCollection/@id | ancestor::appendix/@id | ancestor::glossary/@id | ancestor::acknowledgements/@id | ancestor::preface/@id | ancestor::abstract/@id"/>
        <xsl:variable name="endnotesInPrecedingInterlinearRefs"
            select="(descendant::interlinearRef[ancestor::referencedInterlinearTexts] | preceding::interlinearRef)[ancestor::*[@id=$sCurrentAncestorId]][key('InterlinearReferenceID',@textref)[ancestor::referencedInterlinearTexts]/descendant::endnote]"/>
        <xsl:variable name="sCount">
            <xsl:for-each select="$endnotesInPrecedingInterlinearRefs">
                <xsl:variable name="iCountOfEndnotes" select="count(key('InterlinearReferenceID',@textref)/descendant::endnote)"/>
                <xsl:value-of select="substring($sYs,1,$iCountOfEndnotes)"/>
            </xsl:for-each>
        </xsl:variable>
        <xsl:variable name="iCountOfEndnotesInPrecedingInterlinearRefs" select="string-length($sCount)"/>
        <xsl:value-of select="$iPreviousEndnotes + $iCountOfEndnotesInPrecedingInterlinearRefs + $iIncludeCurrentInterlinearRef+$iTablenumberedAdjust"/>-->
        <xsl:value-of select="$iPreviousEndnotes + $iTablenumberedAdjust"/>
    </xsl:template>
    <!--  
        GetCountOfEndnoteInTitleUsingSymbol
    -->
    <xsl:template name="GetCountOfEndnoteInTitleUsingSymbol">
        <xsl:choose>
            <xsl:when test="exsl:node-set($frontMatterLayoutInfo)/titleLayout/@useFootnoteSymbols='yes' and not(parent::title)">
                <xsl:value-of select="count(ancestor::lingPaper/frontMatter/title[endnote])"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>0</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        GetExampleNumber
    -->
    <xsl:template name="GetExampleNumber">
        <xsl:param name="example"/>
        <xsl:for-each select="$example">
            <xsl:choose>
                <xsl:when test="ancestor::endnote">
                    <xsl:apply-templates select="." mode="exampleInEndnote"/>
                </xsl:when>
                <xsl:when test="ancestor::framedUnit">
                    <xsl:variable name="iStartNumber">
                        <xsl:variable name="sStartNumber" select="normalize-space(ancestor::framedUnit/@initialexamplenumber)"/>
                        <xsl:choose>
                            <xsl:when test="string-length($sStartNumber) &gt; 0 and number($sStartNumber)!='NaN'">
                                <xsl:value-of select="$sStartNumber - 1"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>0</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:variable>
                    <xsl:variable name="iRelNumber">
                        <xsl:apply-templates select="." mode="exampleInFramedUnit"/>
                    </xsl:variable>
                    <xsl:value-of select="$iRelNumber + $iStartNumber"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:if test="$documentLayoutInfo">
                        <xsl:if test="exsl:node-set($documentLayoutInfo)/exampleLayout/@showChapterNumberBeforeExampleNumber='yes' and exsl:node-set($documentLayoutInfo)/exampleLayout/@startNumberingOverAtEachChapter='yes'">
                            <xsl:choose>
                                <xsl:when test="ancestor-or-self::appendix">
                                    <xsl:apply-templates select="." mode="numberAppendix"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:apply-templates select="." mode="numberChapter"/>
                                </xsl:otherwise>
                            </xsl:choose>
                            <xsl:choose>
                                <xsl:when test="string-length($sTextBetweenChapterNumberAndExampleNumber) &gt; 0">
                                    <xsl:value-of select="$sTextBetweenChapterNumberAndExampleNumber"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>.</xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:if>
                    </xsl:if>
                    <xsl:apply-templates select="." mode="example"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>
    <!--  
        GetFigureNumber
    -->
    <xsl:template name="GetFigureNumber">
        <xsl:param name="figure"/>
        <xsl:for-each select="$figure">
            <xsl:choose>
                <xsl:when test="ancestor::endnote">
                    <xsl:apply-templates select="." mode="figureInEndnote"/>
                </xsl:when>
                <xsl:when test="ancestor::framedUnit">
                    <xsl:variable name="iStartNumber">
                        <xsl:variable name="sStartNumber" select="normalize-space(ancestor::framedUnit/@initialfigurenumber)"/>
                        <xsl:choose>
                            <xsl:when test="string-length($sStartNumber) &gt; 0 and number($sStartNumber)!='NaN'">
                                <xsl:value-of select="$sStartNumber - 1"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>0</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:variable>
                    <xsl:variable name="iRelNumber">
                        <xsl:apply-templates select="." mode="figureInFramedUnit"/>
                    </xsl:variable>
                    <xsl:value-of select="$iRelNumber + $iStartNumber"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates select="." mode="figure"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>
    <!--
        GetFootnoteNumber
    -->
    <xsl:template name="GetFootnoteNumber">
        <xsl:param name="originalContext"/>
        <xsl:param name="iAdjust" select="1"/>
        <xsl:param name="iTablenumberedAdjust" select="0"/>
        <xsl:choose>
            <xsl:when test="parent::title and exsl:node-set($frontMatterLayoutInfo)/titleLayout/@useFootnoteSymbols='yes'">
                <xsl:call-template name="DoAuthorFootnoteNumber"/>
            </xsl:when>
            <xsl:when test="parent::author">
                <xsl:call-template name="DoAuthorFootnoteNumber"/>
            </xsl:when>
            <xsl:when test="ancestor::framedUnit">
                <xsl:variable name="thisFramedUnit" select="ancestor::framedUnit"/>
                <xsl:number level="any" count="endnote[ancestor::framedUnit=$thisFramedUnit]"/>
            </xsl:when>
            <xsl:when test="$bIsBook">
                <xsl:choose>
                    <xsl:when test="$originalContext">
                        <xsl:for-each select="$originalContext">
                            <xsl:call-template name="GetCountOfEndnotesIncludingAnyInInterlinearRefsBook">
                                <xsl:with-param name="iAdjust" select="$iAdjust"/>
                                <xsl:with-param name="iTablenumberedAdjust" select="$iTablenumberedAdjust"/>
                            </xsl:call-template>
                        </xsl:for-each>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="GetCountOfEndnotesIncludingAnyInInterlinearRefsBook">
                            <xsl:with-param name="iAdjust" select="$iAdjust"/>
                            <xsl:with-param name="iTablenumberedAdjust" select="$iTablenumberedAdjust"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
                <!--                <xsl:choose>
                    <xsl:when test="$originalContext">
                        <xsl:for-each select="$originalContext">
                            <xsl:number level="any" count="endnote[not(ancestor::author)] | endnoteRef[not(ancestor::endnote)][not(@showNumberOnly='yes')]" from="chapter | appendix | glossary | acknowledgements | preface | abstract" format="1"/>
                        </xsl:for-each>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:number level="any" count="endnote[not(ancestor::author)] | endnoteRef[not(ancestor::endnote)][not(@showNumberOnly='yes')]" from="chapter | appendix | glossary | acknowledgements | preface | abstract" format="1"/>
                    </xsl:otherwise>
                </xsl:choose>
-->
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="$originalContext and ancestor::interlinear-text and $originalContext != .">
                        <xsl:variable name="iPreviousEndnotesInCurrentInterlinearRef">
                            <xsl:variable name="iIncludingCurrentEndnote">
                                <xsl:number level="any" count="endnote" format="1" from="interlinear[string-length(@text) &gt; 0]"/>
                            </xsl:variable>
                            <xsl:value-of select="number($iIncludingCurrentEndnote) - 1"/>
                        </xsl:variable>
                        <xsl:for-each select="$originalContext">
                            <xsl:call-template name="GetCountOfEndnotesIncludingAnyInInterlinearRefs">
                                <xsl:with-param name="iAdjust" select="$iAdjust"/>
                                <xsl:with-param name="iPreviousEndnotesInCurrentInterlinearRef" select="$iPreviousEndnotesInCurrentInterlinearRef"/>
                                <xsl:with-param name="iTablenumberedAdjust" select="$iTablenumberedAdjust"/>
                            </xsl:call-template>
                        </xsl:for-each>
                    </xsl:when>
                    <xsl:otherwise>
                        <!--                        <xsl:number level="any" count="endnote[not(parent::author)] | endnoteRef[not(ancestor::endnote)]" format="1"/>-->
                        <xsl:call-template name="GetCountOfEndnotesIncludingAnyInInterlinearRefs">
                            <xsl:with-param name="iAdjust" select="$iAdjust"/>
                            <xsl:with-param name="iTablenumberedAdjust" select="$iTablenumberedAdjust"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        GetGlossaryTermLanguageCode
    -->
    <xsl:template name="GetGlossaryTermLanguageCode">
        <xsl:variable name="sLangCode">
            <xsl:choose>
                <xsl:when test="string-length($glossaryTermLang) &gt; 0">
                    <xsl:value-of select="$glossaryTermLang"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$documentLang"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="string-length($sLangCode) &gt; 0">
                <xsl:value-of select="$sLangCode"/>
            </xsl:when>
            <xsl:otherwise>en</xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        GetIdToUse
    -->
    <xsl:template name="GetIdToUse">
        <xsl:param name="sBaseId"/>
        <xsl:value-of select="$sBaseId"/>
        <xsl:if test="ancestor::chapterInCollection">
            <xsl:text>.</xsl:text>
            <xsl:value-of select="ancestor::chapterInCollection/@id"/>
        </xsl:if>
    </xsl:template>
    <!--
        GetInterlinearTextShortTitleAndNumber
    -->
    <xsl:template name="GetInterlinearTextShortTitleAndNumber">
        <xsl:variable name="sTextShortTitle" select="../textInfo/shortTitle"/>
        <xsl:if test="string-length($sTextShortTitle) &gt; 0">
            <xsl:value-of select="$sTextShortTitle"/>
            <xsl:choose>
                <xsl:when test="string-length(exsl:node-set($contentLayoutInfo)/interlinearTextLayout/@textbeforeReferenceNumber) &gt; 0">
                    <!-- do nothing here; it is handled in DoInterlinearTextNumber -->
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>:</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:call-template name="DoInterlinearTextNumber">
            <xsl:with-param name="interlinear" select="."/>
            <xsl:with-param name="sRef" select="@text"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        GetISO639-3CodeFromLanguage
    -->
    <xsl:template name="GetISO639-3CodeFromLanguage">
        <xsl:param name="language"/>
        <xsl:value-of select="exsl:node-set($language)/@ISO639-3Code"/>
    </xsl:template>
    <!--  
        GetISO639-3CodeLanguageCode
    -->
    <xsl:template name="GetISO639-3CodeLanguageCode">
        <xsl:variable name="sLangCode">
            <xsl:choose>
                <xsl:when test="string-length($isoCodeLang) &gt; 0">
                    <xsl:value-of select="$isoCodeLang"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$documentLang"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="string-length($sLangCode) &gt; 0">
                <xsl:value-of select="$sLangCode"/>
            </xsl:when>
            <xsl:otherwise>en</xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- 
        GetISOCode
    -->
    <xsl:template name="GetISOCode">
        <xsl:param name="originalContext"/>
        <xsl:if
            test="exsl:node-set($lingPaper)/@showiso639-3codeininterlinear='yes' or ancestor-or-self::example/@showiso639-3codes='yes' or $originalContext and exsl:node-set($originalContext)/ancestor-or-self::example/@showiso639-3codes='yes'">
            <xsl:variable name="firstLangData"
                select="descendant::langData[1] | key('InterlinearReferenceID',interlinearRef/@textref)[1]/descendant::langData[1] | key('InterlinearReferenceID',child::*[substring(name(),1,4)='list'][1]/interlinearRef/@textref)[1]/descendant::langData[1]"/>
            <xsl:if test="$firstLangData">
                <xsl:value-of select="key('LanguageID',exsl:node-set($firstLangData)/@lang)/@ISO639-3Code"/>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!--
        GetKeywordsID
    -->
    <xsl:template name="GetKeywordsID">
        <xsl:choose>
            <xsl:when test="parent::backMatter">
                <xsl:value-of select="$sKeywordsInBackMatterID"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sKeywordsInFrontMatterID"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        GetLabelOrShortTitle
    -->
    <xsl:template name="GetLabelOrShortTitle">
        <xsl:param name="fUseShortTitleIfExists" select="'N'"/>
        <xsl:choose>
            <xsl:when test="$fUseShortTitleIfExists='Y' and shortTitle and string-length(shortTitle) &gt; 0">
                <xsl:value-of select="shortTitle"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="@label"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        GetLiInOlNumberOrLetter
    -->
    <xsl:template name="GetLiInOlNumberOrLetter">
        <xsl:param name="li"/>
        <xsl:for-each select="$li">
            <xsl:variable name="NestingLevel">
                <xsl:choose>
                    <xsl:when test="ancestor::endnote">
                        <xsl:value-of select="count(../ancestor::ol[not(descendant::endnote)])"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="count(../ancestor::ol)"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:choose>
                <xsl:when test="($NestingLevel mod 3)=0">
                    <xsl:number format="1"/>
                </xsl:when>
                <xsl:when test="($NestingLevel mod 3)=1">
                    <xsl:number format="a"/>
                </xsl:when>
                <xsl:when test="($NestingLevel mod 3)=2">
                    <xsl:number format="i"/>
                </xsl:when>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>
    <!-- 
        GetMediaObjectIconCode
    -->
    <xsl:template name="GetMediaObjectIconCode">
        <xsl:param name="mode" select="'TeX'"/>
        <xsl:choose>
            <xsl:when test="$mode='TeX'">
                <xsl:text>"</xsl:text>
                <xsl:choose>
                    <xsl:when test="@icon='moviecamera'">
                        <xsl:text>1F3A5</xsl:text>
                    </xsl:when>
                    <xsl:when test="@icon='cinema'">
                        <xsl:text>1F3A6</xsl:text>
                    </xsl:when>
                    <xsl:when test="@icon='opticaldisk'">
                        <xsl:text>1F4BF</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>1F50A</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="@icon='moviecamera'">
                        <xsl:text>&#x1F3A5;</xsl:text>
                    </xsl:when>
                    <xsl:when test="@icon='cinema'">
                        <xsl:text>&#x1F3A6;</xsl:text>
                    </xsl:when>
                    <xsl:when test="@icon='opticaldisk'">
                        <xsl:text>&#x1F4BF;</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>&#x1F50A;</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- 
        GetOrderedListItemNumberOrLetter
    -->
    <xsl:template name="GetOrderedListItemNumberOrLetter">
        <xsl:variable name="sNumberFormat" select="../@numberFormat"/>
        <xsl:variable name="sNumberLevel" select="../@numberLevel"/>
        <xsl:choose>
            <xsl:when test="string-length($sNumberFormat) &gt; 0">
                <!-- the user has defined a format to use -->
                <xsl:choose>
                    <xsl:when test="$sNumberLevel='multiple'">
                        <xsl:number level="multiple" count="li" format="{$sNumberFormat}"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:number level="single" count="li" format="{$sNumberFormat}"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="NestingLevel">
                    <xsl:choose>
                        <xsl:when test="ancestor::endnote">
                            <xsl:value-of select="count(ancestor::ol[not(descendant::endnote)])"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="count(ancestor::ol)"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:choose>
                    <xsl:when test="($NestingLevel mod 3)=1">
                        <xsl:number level="single" count="li" format="1"/>
                    </xsl:when>
                    <xsl:when test="($NestingLevel mod 3)=2">
                        <xsl:number level="single" count="li" format="a"/>
                    </xsl:when>
                    <xsl:when test="($NestingLevel mod 3)=0">
                        <xsl:number level="single" count="li" format="i"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="position()"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:text>.</xsl:text>
    </xsl:template>
    <!--  
        GetTableNumberedNumber
    -->
    <xsl:template name="GetTableNumberedNumber">
        <xsl:param name="tablenumbered"/>
        <xsl:for-each select="$tablenumbered">
            <xsl:choose>
                <xsl:when test="ancestor::endnote">
                    <xsl:apply-templates select="." mode="tablenumberedInEndnote"/>
                </xsl:when>
                <xsl:when test="ancestor::framedUnit">
                    <xsl:variable name="iStartNumber">
                        <xsl:variable name="sStartNumber" select="normalize-space(ancestor::framedUnit/@initialnumberedtablenumber)"/>
                        <xsl:choose>
                            <xsl:when test="string-length($sStartNumber) &gt; 0 and number($sStartNumber)!='NaN'">
                                <xsl:value-of select="$sStartNumber - 1"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>0</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:variable>
                    <xsl:variable name="iRelNumber">
                        <xsl:apply-templates select="." mode="tablenumberedInFramedUnit"/>
                    </xsl:variable>
                    <xsl:value-of select="$iRelNumber + $iStartNumber"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates select="." mode="tablenumbered"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>
    <!--  
        GetUnitOfMeasure
    -->
    <xsl:template name="GetUnitOfMeasure">
        <xsl:param name="sValue"/>
        <xsl:value-of select="substring($sValue, string-length($sValue)-1)"/>
    </xsl:template>
    <!--
        HandleAbbreviationsInCommaSeparatedList
    -->
    <xsl:template name="HandleAbbreviationsInCommaSeparatedList">
        <xsl:choose>
            <xsl:when test="ancestor::chapterInCollection/backMatter/abbreviations">
                <xsl:call-template name="OutputAbbreviationsInCommaSeparatedList">
                    <xsl:with-param name="abbreviations" select="ancestor::chapterInCollection/backMatter/abbreviations/abbreviation"/>
                    <xsl:with-param name="abbrRefs" select="ancestor::chapterInCollection/descendant::abbrRef"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="OutputAbbreviationsInCommaSeparatedList"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        HandleAbbreviationsInTable
    -->
    <xsl:template name="HandleAbbreviationsInTable">
        <xsl:choose>
            <xsl:when test="ancestor::chapterInCollection/backMatter/abbreviations">
                <xsl:call-template name="OutputAbbreviationsInTable">
                    <xsl:with-param name="abbrsUsed" select="ancestor::chapterInCollection/backMatter/abbreviations/abbreviation[ancestor::chapterInCollection/descendant::abbrRef/@abbr=@id]"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="OutputAbbreviationsInTable"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        HandleGlossaryTermsAsDefinitionList
    -->
    <xsl:template name="HandleGlossaryTermsAsDefinitionList">
        <xsl:choose>
            <xsl:when test="ancestor::chapterInCollection/backMatter/glossaryTerms">
                <xsl:call-template name="OutputGlossaryTermsAsDefinitionList">
                    <xsl:with-param name="glossaryTermsUsed"
                        select="ancestor::chapterInCollection/backMatter/glossaryTerms/glossaryTerm[ancestor::chapterInCollection/descendant::glossaryTermRef/@glossaryTerm=@id]"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="OutputGlossaryTermsAsDefinitionList"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        HandleGlossaryTermsInTable
    -->
    <xsl:template name="HandleGlossaryTermsInTable">
        <xsl:choose>
            <xsl:when test="ancestor::chapterInCollection/backMatter/glossaryTerms">
                <xsl:call-template name="OutputGlossaryTermsInTable">
                    <xsl:with-param name="glossaryTermsUsed"
                        select="ancestor::chapterInCollection/backMatter/glossaryTerms/glossaryTerm[ancestor::chapterInCollection/descendant::glossaryTermRef/@glossaryTerm=@id]"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="OutputGlossaryTermsInTable"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        HandleISO639-3CodesInCommaSeparatedList
    -->
    <xsl:template name="HandleISO639-3CodesInCommaSeparatedList">
        <xsl:choose>
            <xsl:when test="ancestor::chapterInCollection">
                <xsl:call-template name="OutputISO639-3CodesInCommaSeparatedList">
                    <xsl:with-param name="codeRefs"
                        select="ancestor::chapterInCollection/descendant::iso639-3codeRef or ancestor::chapterInCollection/descendant::lineGroup/line[1]/descendant::langData[1] or ancestor::chapterInCollection/descendant::word/langData[1] or ancestor::chapterInCollection/descendant::listWord/langData[1]"
                    />
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="OutputISO639-3CodesInCommaSeparatedList"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        HandleISO639-3CodesInTable
    -->
    <xsl:template name="HandleISO639-3CodesInTable">
        <xsl:choose>
            <xsl:when test="ancestor::chapterInCollection/backMatter/abbreviations">
                <xsl:call-template name="OutputISO639-3CodesInTable">
                    <xsl:with-param name="codesUsed"
                        select="//language[//iso639-3codeRef[ancestor::chapterInCollection]/@lang=@id or //lineGroup/line[1]/descendant::langData[1][ancestor::chapterInCollection]/@lang=@id or //word/langData[1][ancestor::chapterInCollection]/@lang=@id or //listWord/langData[1][ancestor::chapterInCollection]/@lang=@id]"
                    />
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="OutputISO639-3CodesInTable"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        HandleRefAuthors
    -->
    <xsl:template name="HandleRefAuthors">
        <xsl:choose>
            <xsl:when test="ancestor::chapterInCollection">
                <xsl:call-template name="DoRefAuthors">
                    <xsl:with-param name="refAuthors" select="descendant::refAuthor"/>
                    <xsl:with-param name="citations" select="ancestor::chapterInCollection/descendant::citation[not(ancestor::abbrDefinition)]"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="DoRefAuthors"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        InsertCommaBetweenConsecutiveEndnotes
    -->
    <xsl:template name="InsertCommaBetweenConsecutiveEndnotes">
        <xsl:if test="preceding-sibling::node()[1][name()='endnote' or name()='endnoteRef']">
            <!-- the immediately preceding element is also an endnote; separate the numbers by a comma and non-breaking space
                 unless overridden by what's in style sheet -->
            <xsl:variable name="sAfterComma">
                <xsl:choose>
                    <xsl:when test="string-length($sContentBetweenMultipleFootnoteNumbersInText) &gt; 0">
                        <xsl:value-of select="$sContentBetweenMultipleFootnoteNumbersInText"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>,&#xa0;</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:value-of select="$sAfterComma"/>
        </xsl:if>
    </xsl:template>
    <!--
        OutputAbbrDefinition
    -->
    <xsl:template name="OutputAbbrDefinition">
        <xsl:param name="abbr"/>
        <xsl:choose>
            <xsl:when test="string-length($abbrLang) &gt; 0">
                <xsl:choose>
                    <xsl:when test="string-length(exsl:node-set($abbr)//abbrInLang[@lang=$abbrLang]/abbrTerm) &gt; 0">
                        <xsl:apply-templates select="exsl:node-set($abbr)/abbrInLang[@lang=$abbrLang]/abbrDefinition/text() | exsl:node-set($abbr)/abbrInLang[@lang=$abbrLang]/abbrDefinition/*"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- a language is specified, but this abbreviation does not have anything; try using the default;
                            this assumes that something is better than nothing -->
                        <xsl:apply-templates select="exsl:node-set($abbr)/abbrInLang[1]/abbrDefinition/text() | exsl:node-set($abbr)/abbrInLang[1]/abbrDefinition/*"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <!--  no language specified; just use the first one -->
                <xsl:apply-templates select="exsl:node-set($abbr)/abbrInLang[1]/abbrDefinition/text() | exsl:node-set($abbr)/abbrInLang[1]/abbrDefinition/*"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        OutputAbbreviationsInCommaSeparatedList
    -->
    <xsl:template name="OutputAbbreviationsInCommaSeparatedList">
        <xsl:param name="abbreviations" select="//abbreviation[not(ancestor::chapterInCollection/backMatter/abbreviations)]"/>
        <xsl:param name="abbrRefs" select="//abbrRef[not(ancestor::chapterInCollection/backMatter/abbreviations) and not(ancestor::comment)]"/>
        <xsl:choose>
            <xsl:when test="exsl:node-set($lingPaper)/@sortRefsAbbrsByDocumentLanguage='yes'">
                <xsl:variable name="sLang">
                    <xsl:call-template name="GetAbbreviationLanguageCode"/>
                </xsl:variable>
                <xsl:for-each select="$abbreviations[$abbrRefs[not(ancestor::referencedInterlinearText) or ancestor::interlinear[key('InterlinearRef',@text)]]/@abbr=@id]">
                    <xsl:sort lang="{$sLang}" select="abbrInLang[@lang=$sLang or position()=1 and not (following-sibling::abbrInLang[@lang=$sLang])]/abbrTerm"/>
                    <xsl:call-template name="OutputAbbreviationInCommaSeparatedList"/>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <xsl:for-each select="$abbreviations[$abbrRefs[not(ancestor::referencedInterlinearText) or ancestor::interlinear[key('InterlinearRef',@text)]]/@abbr=@id]">
                    <xsl:call-template name="OutputAbbreviationInCommaSeparatedList"/>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        OutputAbbreviationsLabel
    -->
    <xsl:template name="OutputAbbreviationsLabel">
        <xsl:param name="fUseShortTitleIfExists" select="'N'"/>
        <xsl:call-template name="OutputLabel">
            <xsl:with-param name="sDefault">Abbreviations</xsl:with-param>
            <!--            <xsl:with-param name="pLabel" select="//abbreviations/@label"/>-->
            <xsl:with-param name="pLabel">
                <xsl:call-template name="GetLabelOrShortTitle">
                    <xsl:with-param name="fUseShortTitleIfExists" select="$fUseShortTitleIfExists"/>
                </xsl:call-template>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--
        OutputAbstractLabel
    -->
    <xsl:template name="OutputAbstractLabel">
        <xsl:param name="fUseShortTitleIfExists" select="'N'"/>
        <xsl:call-template name="OutputLabel">
            <xsl:with-param name="sDefault">Abstract</xsl:with-param>
            <xsl:with-param name="pLabel">
                <xsl:call-template name="GetLabelOrShortTitle">
                    <xsl:with-param name="fUseShortTitleIfExists" select="$fUseShortTitleIfExists"/>
                </xsl:call-template>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--
        OutputAcknowledgementsLabel
    -->
    <xsl:template name="OutputAcknowledgementsLabel">
        <xsl:param name="fUseShortTitleIfExists" select="'N'"/>
        <xsl:call-template name="OutputLabel">
            <xsl:with-param name="sDefault">Acknowledgements</xsl:with-param>
            <!--            <xsl:with-param name="pLabel" select="//acknowledgements/@label"/>-->
            <xsl:with-param name="pLabel">
                <xsl:for-each select="//acknowledgements">
                    <xsl:call-template name="GetLabelOrShortTitle">
                        <xsl:with-param name="fUseShortTitleIfExists" select="$fUseShortTitleIfExists"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--
        OutputAuthorFootnoteSymbol
    -->
    <xsl:template name="OutputAuthorFootnoteSymbol">
        <xsl:param name="iAuthorPosition"/>
        <xsl:choose>
            <xsl:when test="$iAuthorPosition &lt; 10">
                <xsl:call-template name="OutputAuthorFootnoteSymbol1-9">
                    <xsl:with-param name="iPos" select="$iAuthorPosition"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="iPos" select="floor($iAuthorPosition div 9)"/>
                <xsl:call-template name="OutputAuthorFootnoteSymbol1-9">
                    <xsl:with-param name="iPos" select="$iPos"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        OutputAuthorFootnoteSymbol1-9
    -->
    <xsl:template name="OutputAuthorFootnoteSymbol1-9">
        <xsl:param name="iPos"/>
        <xsl:choose>
            <xsl:when test="$iPos=1">
                <xsl:text>*</xsl:text>
            </xsl:when>
            <xsl:when test="$iPos=2">
                <xsl:text>†</xsl:text>
            </xsl:when>
            <xsl:when test="$iPos=3">
                <xsl:text>‡</xsl:text>
            </xsl:when>
            <xsl:when test="$iPos=4">
                <xsl:text>§</xsl:text>
            </xsl:when>
            <xsl:when test="$iPos=5">
                <xsl:text>¶</xsl:text>
            </xsl:when>
            <xsl:when test="$iPos=6">
                <xsl:text>.</xsl:text>
            </xsl:when>
            <xsl:when test="$iPos=7">
                <xsl:text>**</xsl:text>
            </xsl:when>
            <xsl:when test="$iPos=8">
                <xsl:text>††</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>‡‡</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        OutputContentsLabel
    -->
    <xsl:template name="OutputContentsLabel">
        <xsl:param name="fUseShortTitleIfExists" select="'N'"/>
        <xsl:param name="layoutInfo"/>
        <xsl:call-template name="OutputLabel">
            <xsl:with-param name="sDefault">Contents</xsl:with-param>
            <xsl:with-param name="pLabel">
                <xsl:choose>
                    <xsl:when test="$layoutInfo and $layoutInfo/parent::backMatterLayout">
                        <xsl:variable name="sBackMatterLabel" select="normalize-space(@backmatterlabel)"/>
                        <xsl:choose>
                            <xsl:when test="string-length($sBackMatterLabel) &gt; 0">
                                <xsl:value-of select="$sBackMatterLabel"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="GetLabelOrShortTitle">
                                    <xsl:with-param name="fUseShortTitleIfExists" select="$fUseShortTitleIfExists"/>
                                </xsl:call-template>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="GetLabelOrShortTitle">
                            <xsl:with-param name="fUseShortTitleIfExists" select="$fUseShortTitleIfExists"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--
        OutputEndnotesLabel
    -->
    <xsl:template name="OutputEndnotesLabel">
        <xsl:param name="fUseShortTitleIfExists" select="'N'"/>
        <xsl:call-template name="OutputLabel">
            <xsl:with-param name="sDefault">Endnotes</xsl:with-param>
            <!--            <xsl:with-param name="pLabel" select="//endnotes/@label"/>-->
            <xsl:with-param name="pLabel">
                <xsl:call-template name="GetLabelOrShortTitle">
                    <xsl:with-param name="fUseShortTitleIfExists" select="$fUseShortTitleIfExists"/>
                </xsl:call-template>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--
        OutputExampleLevelISOCode
    -->
    <xsl:template name="OutputExampleLevelISOCode">
        <xsl:param name="bListsShareSameCode"/>
        <xsl:param name="sIsoCode"/>
        <xsl:if test="$lingPaper/@showiso639-3codeininterlinear='yes' or ancestor-or-self::example/@showiso639-3codes='yes'">
            <xsl:choose>
                <xsl:when test="listInterlinear or listWord or listSingle">
                    <xsl:if test="not(contains($bListsShareSameCode,'N'))">
                        <xsl:call-template name="OutputISOCodeInExample">
                            <xsl:with-param name="sIsoCode" select="$sIsoCode"/>
                        </xsl:call-template>
                    </xsl:if>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="OutputISOCodeInExample">
                        <xsl:with-param name="sIsoCode" select="$sIsoCode"/>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--
        OutputGenericRef
    -->
    <xsl:template name="OutputGenericRef">
        <xsl:param name="originalContext"/>
        <xsl:variable name="targetIsLiInOl" select="key('LiInOlID',@gref)"/>
        <xsl:choose>
            <xsl:when test="$targetIsLiInOl">
                <xsl:choose>
                    <xsl:when test="@showlivalue='before'">
                        <xsl:call-template name="GetLiInOlNumberOrLetter">
                            <xsl:with-param name="li" select="$targetIsLiInOl"/>
                        </xsl:call-template>
                        <xsl:apply-templates/>
                    </xsl:when>
                    <xsl:when test="@showlivalue='after'">
                        <xsl:apply-templates/>
                        <xsl:call-template name="GetLiInOlNumberOrLetter">
                            <xsl:with-param name="li" select="$targetIsLiInOl"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:when test="@showlivalue='only'">
                        <xsl:call-template name="GetLiInOlNumberOrLetter">
                            <xsl:with-param name="li" select="$targetIsLiInOl"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:when test="@showlivalue='no'">
                        <xsl:apply-templates/>
                    </xsl:when>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates>
                    <xsl:with-param name="originalContext" select="$originalContext"/>
                </xsl:apply-templates>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        OutputGlossaryLabel
    -->
    <xsl:template name="OutputGlossaryLabel">
        <xsl:param name="fUseShortTitleIfExists" select="'N'"/>
        <xsl:call-template name="OutputLabel">
            <xsl:with-param name="sDefault">Glossary</xsl:with-param>
            <!--            <xsl:with-param name="pLabel" select="@label"/>-->
            <xsl:with-param name="pLabel">
                <xsl:call-template name="GetLabelOrShortTitle">
                    <xsl:with-param name="fUseShortTitleIfExists" select="$fUseShortTitleIfExists"/>
                </xsl:call-template>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--
        OutputGlossaryTermContentInContext
    -->
    <xsl:template name="OutputGlossaryTermContentInContext">
        <xsl:param name="bIsRef"/>
        <xsl:param name="glossaryTerm"/>
        <xsl:param name="glossaryTermRef"/>
        <xsl:choose>
            <xsl:when test="$bIsRef='Y' and string-length(.) &gt; 0">
                <xsl:value-of select="."/>
            </xsl:when>
            <xsl:when test="string-length($glossaryTermLang) &gt; 0">
                <xsl:choose>
                    <xsl:when test="string-length($glossaryTerm//glossaryTermInLang[@lang=$glossaryTermLang]/glossaryTermTerm) &gt; 0">
                        <xsl:apply-templates select="$glossaryTerm/glossaryTermInLang[@lang=$glossaryTermLang]/glossaryTermTerm" mode="Use">
                            <xsl:with-param name="glossaryTermRef" select="$glossaryTermRef"/>
                        </xsl:apply-templates>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- a language is specified, but this glossary term does not have anything; try using the default;
                            this assumes that something is better than nothing -->
                        <xsl:apply-templates select="$glossaryTerm/glossaryTermInLang[1]/glossaryTermTerm" mode="Use">
                            <xsl:with-param name="glossaryTermRef" select="$glossaryTermRef"/>
                        </xsl:apply-templates>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <!--  no language specified; just use the first one -->
                <xsl:apply-templates select="$glossaryTerm/glossaryTermInLang[1]/glossaryTermTerm" mode="Use">
                    <xsl:with-param name="glossaryTermRef" select="$glossaryTermRef"/>
                </xsl:apply-templates>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        OutputGlossaryTermDefinition
    -->
    <xsl:template name="OutputGlossaryTermDefinition">
        <xsl:param name="glossaryTerm"/>
        <xsl:choose>
            <xsl:when test="string-length($glossaryTermLang) &gt; 0">
                <xsl:choose>
                    <xsl:when test="string-length($glossaryTerm//glossaryTermInLang[@lang=$glossaryTermLang]/glossaryTermDefinition) &gt; 0">
                        <xsl:apply-templates select="$glossaryTerm/glossaryTermInLang[@lang=$glossaryTermLang]/glossaryTermDefinition" mode="Use"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- a language is specified, but this abbreviation does not have anything; try using the default;
                            this assumes that something is better than nothing -->
                        <xsl:apply-templates select="$glossaryTerm/glossaryTermInLang[1]/glossaryTermDefinition" mode="Use"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <!--  no language specified; just use the first one -->
                <xsl:apply-templates select="$glossaryTerm/glossaryTermInLang[1]/glossaryTermDefinition" mode="Use"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        OutputIndexLabel
    -->
    <xsl:template name="OutputIndexLabel">
        <xsl:param name="fUseShortTitleIfExists" select="'N'"/>
        <xsl:variable name="sDefaultIndexLabel">
            <xsl:choose>
                <xsl:when test="@kind='name'">
                    <xsl:text>Name Index</xsl:text>
                </xsl:when>
                <xsl:when test="@kind='language'">
                    <xsl:text>Language Index</xsl:text>
                </xsl:when>
                <xsl:when test="@kind='subject'">
                    <xsl:text>Subject Index</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>Index</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:call-template name="OutputLabel">
            <xsl:with-param name="sDefault" select="$sDefaultIndexLabel"/>
            <!--            <xsl:with-param name="pLabel" select="@label"/>-->
            <xsl:with-param name="pLabel">
                <xsl:call-template name="GetLabelOrShortTitle">
                    <xsl:with-param name="fUseShortTitleIfExists" select="$fUseShortTitleIfExists"/>
                </xsl:call-template>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--  
        OutputIndexTermSeeAloneAfter
    -->
    <xsl:template name="OutputIndexTermSeeAloneAfter">
        <xsl:if test="$indexSeeDefinition">
            <xsl:value-of select="$indexSeeDefinition/seeTerm/afterTerm"/>
        </xsl:if>
        <xsl:text>.</xsl:text>
    </xsl:template>
    <!--  
        OutputIndexTermSeeAloneBefore
    -->
    <xsl:template name="OutputIndexTermSeeAloneBefore">
        <xsl:choose>
            <xsl:when test="string-length($sTextBeforeSeeAlso) &gt; 0">
                <xsl:value-of select="$sTextBeforeSeeAlso"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>&#xa0;&#xa0;</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:choose>
            <xsl:when test="$indexSeeDefinition">
                <xsl:value-of select="$indexSeeDefinition/seeTerm/beforeTerm"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>see</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:text>&#x20;</xsl:text>
    </xsl:template>
    <!--  
        OutputIndexTermSeeAfter
    -->
    <xsl:template name="OutputIndexTermSeeAfter">
        <xsl:param name="indexedItems"/>
        <xsl:choose>
            <xsl:when test="$indexedItems">
                <xsl:if test="$indexSeeDefinition">
                    <xsl:value-of select="$indexSeeDefinition/seeAlsoTerm/afterTerm"/>
                </xsl:if>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="$indexSeeDefinition">
                    <xsl:value-of select="$indexSeeDefinition/seeTerm/afterTerm"/>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:text>.</xsl:text>
    </xsl:template>
    <!--  
        OutputIndexTermSeeBefore
    -->
    <xsl:template name="OutputIndexTermSeeBefore">
        <xsl:param name="indexedItems"/>
        <xsl:choose>
            <xsl:when test="$indexedItems">
                <xsl:text>.  </xsl:text>
                <xsl:choose>
                    <xsl:when test="$indexSeeDefinition">
                        <xsl:value-of select="$indexSeeDefinition/seeAlsoTerm/beforeTerm"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>See also</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:text>&#x20;</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="$indexSeeDefinition">
                        <xsl:value-of select="$indexSeeDefinition/seeTerm/beforeTerm"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>see</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:text>&#x20;</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        OutputIndexTermsTerm
    -->
    <xsl:template name="OutputIndexTermsTerm">
        <xsl:param name="lang"/>
        <xsl:param name="indexTerm"/>
        <xsl:choose>
            <xsl:when test="$lang and $indexTerm/term[@lang=$lang]">
                <xsl:apply-templates select="$indexTerm/term[@lang=$lang]" mode="InIndex"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="$indexTerm/term[1]" mode="InIndex"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        OutputIndexTermsTermFullPath
    -->
    <xsl:template name="OutputIndexTermsTermFullPath">
        <xsl:param name="lang"/>
        <xsl:param name="indexTerm"/>
        <xsl:if test="$indexTerm/ancestor::indexTerm[1]">
            <xsl:call-template name="OutputIndexTermsTermFullPath">
                <xsl:with-param name="lang" select="$lang"/>
                <xsl:with-param name="indexTerm" select="$indexTerm/ancestor::indexTerm[1]"/>
            </xsl:call-template>
            <xsl:text>, </xsl:text>
        </xsl:if>
        <xsl:call-template name="OutputIndexTermsTerm">
            <xsl:with-param name="lang" select="$lang"/>
            <xsl:with-param name="indexTerm" select="$indexTerm"/>
        </xsl:call-template>
    </xsl:template>
    <!--
        OutputISO639-3CodeLanguageName
    -->
    <xsl:template name="OutputISO639-3CodeLanguageName">
        <xsl:param name="language"/>
        <xsl:choose>
            <xsl:when test="string-length($isoCodeLang) &gt; 0">
                <xsl:choose>
                    <xsl:when test="string-length($language/langName[@xml:lang=$isoCodeLang]) &gt; 0">
                        <xsl:value-of select="$language/langName[@xml:lang=$isoCodeLang]"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- a language is specified, but this ISO code does not have anything; try using the default;
                            this assumes that something is better than nothing -->
                        <xsl:value-of select="$language/langName[1]"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <!--  no language specified; just use the first one -->
                <xsl:value-of select="$language/langName[1]"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        OutputISO639-3CodesInCommaSeparatedList
    -->
    <xsl:template name="OutputISO639-3CodesInCommaSeparatedList">
        <xsl:param name="codesUsed"
            select="//language[//iso639-3codeRef[not(ancestor::chapterInCollection)]/@lang=@id or //lineGroup/line[1]/descendant::langData[1][not(ancestor::chapterInCollection)]/@lang=@id or //word/langData[1][not(ancestor::chapterInCollection)]/@lang=@id or //listWord/langData[1][not(ancestor::chapterInCollection)]/@lang=@id]"/>

        <xsl:choose>
            <xsl:when test="$lingPaper/@sortRefsAbbrsByDocumentLanguage='yes'">
                <xsl:variable name="sLang">
                    <xsl:call-template name="GetISO639-3CodeLanguageCode"/>
                </xsl:variable>
                <xsl:for-each select="$codesUsed">
                    <!--                    <xsl:sort lang="{$sLang}" select="langName[@xml:lang=$sLang or position()=1 and not (following-sibling::langName[@xml:lang=$sLang])]"/>-->
                    <xsl:sort lang="{$sLang}" select="@ISO639-3Code"/>
                    <xsl:call-template name="OutputISO639-3CodeInCommaSeparatedList"/>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <xsl:for-each select="$codesUsed">
                    <!--                    <xsl:for-each select="$ISOcodes/langName[$codeRefs[not(ancestor::referencedInterlinearText) or ancestor::interlinear[key('InterlinearRef',@text)]]/@xml:lang=@id]">-->
                    <xsl:call-template name="OutputISO639-3CodeInCommaSeparatedList"/>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        OutputKeywordsLabel
    -->
    <xsl:template name="OutputKeywordsLabel">
        <xsl:variable name="labelContent" select="descendant-or-self::labelContent[1]"/>
        <xsl:choose>
            <xsl:when test="string-length($labelContent) &gt; 0">
                <xsl:value-of select="$labelContent"/>
            </xsl:when>
            <xsl:when test="@label and string-length(@label) &gt;= 0">
                <xsl:value-of select="@label"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>Keywords</xsl:text>
                <xsl:choose>
                    <xsl:when test="ancestor::frontMatter">
                        <xsl:text>: </xsl:text>
                    </xsl:when>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        OutputKeywordsShownHere
    -->
    <xsl:template name="OutputKeywordsShownHere">
        <xsl:param name="sTextBetweenKeywords" select="', '"/>
        <xsl:for-each select="../../publishingInfo/keywords/keyword">
            <xsl:value-of select="."/>
            <xsl:if test="position()!=last()">
                <xsl:choose>
                    <xsl:when test="string-length($sTextBetweenKeywords) &gt; 0">
                        <xsl:value-of select="$sTextBetweenKeywords"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>, </xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>
    <!--  
        OutputLabel
    -->
    <xsl:template name="OutputLabel">
        <xsl:param name="sDefault"/>
        <xsl:param name="pLabel"/>
        <xsl:variable name="labelContent" select="descendant-or-self::labelContent[1]"/>
        <xsl:choose>
            <xsl:when test="string-length($labelContent) &gt; 0">
                <xsl:value-of select="$labelContent"/>
            </xsl:when>
            <xsl:when test="string-length($pLabel) &gt; 0">
                <xsl:value-of select="$pLabel"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$sDefault"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        OutputPartLabel
    -->
    <xsl:template name="OutputPartLabel">
        <xsl:choose>
            <xsl:when test="$lingPaper/@partlabel">
                <xsl:value-of select="$lingPaper/@partlabel"/>
            </xsl:when>
            <xsl:otherwise>Part</xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--  
        OutputPeriodIfNeeded
    -->
    <xsl:template name="OutputPeriodIfNeeded">
        <xsl:param name="sText"/>
        <xsl:variable name="sString">
            <xsl:value-of select="normalize-space($sText)"/>
        </xsl:variable>
        <xsl:if test="substring($sString, string-length($sString))!='.'">
            <xsl:text>.</xsl:text>
        </xsl:if>
    </xsl:template>
    <!--
        OutputPrefaceLabel
    -->
    <xsl:template name="OutputPrefaceLabel">
        <xsl:param name="fUseShortTitleIfExists" select="'N'"/>
        <xsl:call-template name="OutputLabel">
            <xsl:with-param name="sDefault">Preface</xsl:with-param>
            <!--            <xsl:with-param name="pLabel" select="@label"/>-->
            <xsl:with-param name="pLabel">
                <xsl:call-template name="GetLabelOrShortTitle">
                    <xsl:with-param name="fUseShortTitleIfExists" select="$fUseShortTitleIfExists"/>
                </xsl:call-template>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    <!--
        OutputRefDateValue
    -->
    <xsl:template name="OutputRefDateValue">
        <xsl:param name="date"/>
        <xsl:param name="sortedWorks"/>
        <xsl:param name="works"/>
        <xsl:value-of select="$date"/>
        <xsl:if test="../../@showAuthorName!='no'">
            <xsl:choose>
                <xsl:when test="$sortedWorks">
                    <xsl:if test="count($sortedWorks/refWork[refDate=$date])>1">
                        <xsl:variable name="thisRef" select=".."/>
                        <xsl:variable name="pos">
                            <xsl:for-each select="$sortedWorks/refWork[refDate=$date]">
                                <xsl:if test=".=$thisRef">
                                    <xsl:value-of select="position()"/>
                                </xsl:if>
                            </xsl:for-each>
                        </xsl:variable>
                        <xsl:if test="string-length($pos) &gt; 0">
                            <xsl:value-of select="substring('abcdefghijklmnñopqrstuvwxyz',$pos,1)"/>
                        </xsl:if>
                    </xsl:if>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:if test="count($works[refDate=$date])>1">
                        <xsl:apply-templates select="." mode="dateLetter">
                            <xsl:with-param name="date" select="$date"/>
                        </xsl:apply-templates>
                    </xsl:if>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!--
        OutputReferencesLabel
    -->
    <xsl:template name="OutputReferencesLabel">
        <xsl:param name="fUseShortTitleIfExists" select="'N'"/>
        <xsl:variable name="selectedBibliography" select="//selectedBibliography"/>
        <xsl:choose>
            <xsl:when test="$selectedBibliography">
                <xsl:for-each select="$selectedBibliography">
                    <xsl:call-template name="OutputLabel">
                        <xsl:with-param name="sDefault">Selected Bibliography</xsl:with-param>
                        <!--                        <xsl:with-param name="pLabel" select="@label"/>-->
                        <xsl:with-param name="pLabel">
                            <xsl:call-template name="GetLabelOrShortTitle">
                                <xsl:with-param name="fUseShortTitleIfExists" select="$fUseShortTitleIfExists"/>
                            </xsl:call-template>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="OutputLabel">
                    <xsl:with-param name="sDefault">References</xsl:with-param>
                    <!--                    <xsl:with-param name="pLabel" select="@label"/>-->
                    <xsl:with-param name="pLabel">
                        <xsl:call-template name="GetLabelOrShortTitle">
                            <xsl:with-param name="fUseShortTitleIfExists" select="$fUseShortTitleIfExists"/>
                        </xsl:call-template>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        OutputTextAfterIndexTerm
    -->
    <xsl:template name="OutputTextAfterIndexTerm">
        <xsl:variable name="sTextAfterTerm" select="$backMatterLayoutInfo/indexLayout/@textafterterm"/>
        <xsl:if test="string-length($sTextAfterTerm) &gt; 0">
            <xsl:value-of select="$sTextAfterTerm"/>
        </xsl:if>
    </xsl:template>
    <!--
        SetMetadataAuthor
    -->
    <xsl:template name="SetMetadataAuthor">
        <xsl:for-each select="$lingPaper/frontMatter/author">
            <xsl:apply-templates select="child::node()[name()!='endnote' and name()!='comment']" mode="contentOnly"/>
            <xsl:if test="position()!=last()">
                <xsl:text>, </xsl:text>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>
    <!--
        SetMetadataCreator
    -->
    <xsl:template name="SetMetadataCreator">
        <xsl:text>XLingPaper version </xsl:text>
        <xsl:value-of select="$sVersion"/>
        <xsl:text> (https://software.sil.org/xlingpaper/)</xsl:text>
    </xsl:template>
    <!--
        SetMetadataKeywords
    -->
    <xsl:template name="SetMetadataKeywords">
        <xsl:for-each select="$lingPaper/publishingInfo/keywords/keyword">
            <xsl:value-of select="."/>
            <xsl:if test="position()!=last()">
                <xsl:text>, </xsl:text>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>
    <!--
        SetMetadataTitle
    -->
    <xsl:template name="SetMetadataTitle">
        <xsl:apply-templates select="$lingPaper/frontMatter/title/child::node()[name()!='endnote' and name()!='comment']" mode="contentOnly"/>
        <xsl:if test="$lingPaper/frontMatter/subtitle != ''">
            <xsl:text>: </xsl:text>
            <xsl:value-of select="$lingPaper/frontMatter/subtitle/child::node()[name()!='endnote' and name()!='comment']"/>
        </xsl:if>
    </xsl:template>
    <!--
        SortAbbreviationsInTable
    -->
    <xsl:template name="SortAbbreviationsInTable">
        <xsl:param name="abbrsUsed"/>
        <xsl:variable name="abbrsShownHere" select="."/>
        <!--                 <xsl:variable name="iHalfwayPoint" select="ceiling(count($abbrsUsed) div 2)"/>
            <xsl:for-each select="$abbrsUsed[position() &lt;= $iHalfwayPoint]">
        -->
        <xsl:variable name="iHalfwayPoint" select="ceiling(count($abbrsUsed) div 2)"/>
        <xsl:choose>
            <xsl:when test="$lingPaper/@sortRefsAbbrsByDocumentLanguage='yes'">
                <xsl:variable name="sLang">
                    <xsl:call-template name="GetAbbreviationLanguageCode"/>
                </xsl:variable>
                <xsl:for-each select="$abbrsUsed">
                    <xsl:sort lang="{$sLang}" select="abbrInLang[@lang=$sLang or position()=1 and not (following-sibling::abbrInLang[@lang=$sLang])]/abbrTerm"/>
                    <xsl:choose>
                        <xsl:when test="$contentLayoutInfo/abbreviationsInTableLayout/@useDoubleColumns='yes'">
                            <xsl:if test="position() &lt;= $iHalfwayPoint">
                                <xsl:variable name="iPos" select="position()"/>
                                <xsl:call-template name="OutputAbbreviationInTable">
                                    <xsl:with-param name="abbrsShownHere" select="$abbrsShownHere"/>
                                    <xsl:with-param name="abbrInSecondColumn" select="$abbrsUsed[$iPos + $iHalfwayPoint]"/>
                                </xsl:call-template>
                            </xsl:if>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="OutputAbbreviationInTable">
                                <xsl:with-param name="abbrsShownHere" select="$abbrsShownHere"/>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="$contentLayoutInfo/abbreviationsInTableLayout/@useDoubleColumns='yes'">
                        <xsl:for-each select="$abbrsUsed[position() &lt;= $iHalfwayPoint]">
                            <xsl:variable name="iPos" select="position()"/>
                            <xsl:call-template name="OutputAbbreviationInTable">
                                <xsl:with-param name="abbrsShownHere" select="$abbrsShownHere"/>
                                <xsl:with-param name="abbrInSecondColumn" select="$abbrsUsed[$iPos + $iHalfwayPoint]"/>
                            </xsl:call-template>
                        </xsl:for-each>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:for-each select="$abbrsUsed">
                            <xsl:call-template name="OutputAbbreviationInTable">
                                <xsl:with-param name="abbrsShownHere" select="$abbrsShownHere"/>
                            </xsl:call-template>
                        </xsl:for-each>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        SortGlossaryTermsAsDefinitionList
    -->
    <xsl:template name="SortGlossaryTermsAsDefinitionList">
        <xsl:param name="glossaryTermsUsed"/>
        <xsl:variable name="glossaryTermsShownHere" select="."/>
        <xsl:choose>
            <xsl:when test="$lingPaper/@sortRefsAbbrsByDocumentLanguage='yes'">
                <xsl:variable name="sLang">
                    <xsl:call-template name="GetGlossaryTermLanguageCode"/>
                </xsl:variable>
                <xsl:for-each select="$glossaryTermsUsed">
                    <xsl:sort lang="{$sLang}" select="glossaryTermInLang[@lang=$sLang or position()=1 and not (following-sibling::glossaryTermInLang[@lang=$sLang])]/glossaryTermTerm"/>
                    <xsl:call-template name="OutputGlossaryTermInDefinitionList">
                        <xsl:with-param name="glossaryTermsShownHere" select="$glossaryTermsShownHere"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <xsl:for-each select="$glossaryTermsUsed">
                    <xsl:call-template name="OutputGlossaryTermInDefinitionList">
                        <xsl:with-param name="glossaryTermsShownHere" select="$glossaryTermsShownHere"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        SortGlossaryTermsInTable
    -->
    <xsl:template name="SortGlossaryTermsInTable">
        <xsl:param name="glossaryTermsUsed"/>
        <xsl:variable name="glossaryTermsShownHere" select="."/>
        <xsl:variable name="iHalfwayPoint" select="ceiling(count($glossaryTermsUsed) div 2)"/>
        <xsl:choose>
            <xsl:when test="$lingPaper/@sortRefsAbbrsByDocumentLanguage='yes'">
                <xsl:variable name="sLang">
                    <xsl:call-template name="GetGlossaryTermLanguageCode"/>
                </xsl:variable>
                <xsl:for-each select="$glossaryTermsUsed">
                    <xsl:sort lang="{$sLang}" select="glossaryTermInLang[@lang=$sLang or position()=1 and not (following-sibling::glossaryTermInLang[@lang=$sLang])]/glossaryTermTerm"/>
                    <xsl:choose>
                        <xsl:when test="$contentLayoutInfo/glossaryTermsInTableLayout/@useDoubleColumns='yes'">
                            <xsl:if test="position() &lt;= $iHalfwayPoint">
                                <xsl:variable name="iPos" select="position()"/>
                                <xsl:call-template name="OutputGlossaryTermInTable">
                                    <xsl:with-param name="glossaryTermsShownHere" select="$glossaryTermsShownHere"/>
                                    <xsl:with-param name="glossaryTermInSecondColumn" select="$glossaryTermsUsed[$iPos + $iHalfwayPoint]"/>
                                </xsl:call-template>
                            </xsl:if>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="OutputGlossaryTermInTable">
                                <xsl:with-param name="glossaryTermsShownHere" select="$glossaryTermsShownHere"/>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="$contentLayoutInfo/glossaryTermsInTableLayout/@useDoubleColumns='yes'">
                        <xsl:for-each select="$glossaryTermsUsed[position() &lt;= $iHalfwayPoint]">
                            <xsl:variable name="iPos" select="position()"/>
                            <xsl:call-template name="OutputGlossaryTermInTable">
                                <xsl:with-param name="glossaryTermsShownHere" select="$glossaryTermsShownHere"/>
                                <xsl:with-param name="glossaryTermInSecondColumn" select="$glossaryTermsUsed[$iPos + $iHalfwayPoint]"/>
                            </xsl:call-template>
                        </xsl:for-each>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:for-each select="$glossaryTermsUsed">
                            <xsl:call-template name="OutputGlossaryTermInTable">
                                <xsl:with-param name="glossaryTermsShownHere" select="$glossaryTermsShownHere"/>
                            </xsl:call-template>
                        </xsl:for-each>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--
        SortISO639-3CodesInTable
    -->
    <xsl:template name="SortISO639-3CodesInTable">
        <xsl:param name="codesUsed"/>
        <xsl:variable name="codesShownHere" select="."/>
        <xsl:variable name="iHalfwayPoint" select="ceiling(count($codesUsed) div 2)"/>
        <xsl:choose>
            <xsl:when test="$lingPaper/@sortRefsAbbrsByDocumentLanguage='yes'">
                <xsl:variable name="sLang">
                    <xsl:call-template name="GetISO639-3CodeLanguageCode"/>
                </xsl:variable>
                <xsl:for-each select="$codesUsed">
                    <!--                    <xsl:sort lang="{$sLang}" select="langName[@xml:lang=$sLang or position()=1 and not (following-sibling::langName[@xml:lang=$sLang])]"/>-->
                    <xsl:sort lang="{$sLang}" select="@ISO639-3Code"/>
                    <xsl:choose>
                        <xsl:when test="$contentLayoutInfo/iso639-3CodesInTableLayout/@useDoubleColumns='yes'">
                            <xsl:if test="position() &lt;= $iHalfwayPoint">
                                <xsl:variable name="iPos" select="position()"/>
                                <xsl:call-template name="OutputISO639-3CodeInTable">
                                    <xsl:with-param name="codesShownHere" select="$codesShownHere"/>
                                    <xsl:with-param name="codeInSecondColumn" select="$codesUsed[$iPos + $iHalfwayPoint]"/>
                                </xsl:call-template>
                            </xsl:if>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="OutputISO639-3CodeInTable">
                                <xsl:with-param name="codesShownHere" select="$codesShownHere"/>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="$contentLayoutInfo/iso639-3CodesInTableLayout/@useDoubleColumns='yes'">
                        <xsl:for-each select="$codesUsed[position() &lt;= $iHalfwayPoint]">
                            <xsl:variable name="iPos" select="position()"/>
                            <xsl:call-template name="OutputISO639-3CodeInTable">
                                <xsl:with-param name="codesShownHere" select="$codesShownHere"/>
                                <xsl:with-param name="codeInSecondColumn" select="$codesUsed[$iPos + $iHalfwayPoint]"/>
                            </xsl:call-template>
                        </xsl:for-each>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:for-each select="$codesUsed">
                            <xsl:call-template name="OutputISO639-3CodeInTable">
                                <xsl:with-param name="codesShownHere" select="$codesShownHere"/>
                            </xsl:call-template>
                        </xsl:for-each>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>
