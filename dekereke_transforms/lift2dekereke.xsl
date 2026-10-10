<?xml version="1.0" encoding="UTF-8"?>
<!--
    LIFT -> Dekereke, by MERGING into the original Dekereke file.

    The source document of this transform is the user's ORIGINAL Dekereke
    database, not the LIFT. Everything is copied through by the identity
    template, and only the columns A-Z+T actually owns are overridden from the
    LIFT passed in $lift. That is the whole point: a Dekereke database holds
    other speakers' columns, elicitation frames, acoustic measurements and
    notes that A-Z+T has no concept of, and regenerating the file from the LIFT
    alone would silently discard every one of them.

    Records A-Z+T never imported (no form to analyze, or flagged) simply never
    match an entry and pass through the identity template untouched.

    Two things here are load-bearing and easy to get wrong:

    * The <xsl:for-each select="$lift"> before key(). In XSLT 1.0 key() only
      indexes the CURRENT document, so looking up an entry in a second document
      requires switching context into it first. Without this the lookup silently
      returns nothing; with a naive predicate instead it is ~190x slower on a
      field-sized database.

    * exsl:node-set() around that result. XSLT 1.0 forbids stepping into a
      result-tree fragment ("XPath evaluation returned no result"), so the
      copied entry has to be turned back into a node-set before it can be
      read. libxslt ships EXSLT, so this costs nothing.

    * The existence guard in every override. If an entry was deleted in A-Z+T,
      or simply has nothing in that field, the override must fall back to the
      original cell rather than blanking the user's data.
-->
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:exsl="http://exslt.org/common"
                extension-element-prefixes="exsl">

<xsl:output method="xml" encoding="UTF-8" indent="yes"/>

<xsl:param name="lift"/>
<xsl:param name="map"/>

<xsl:variable name="l" select="document($lift)/lift"/>
<xsl:variable name="m" select="document($map)/dekerekeSource"/>
<xsl:variable name="analang" select="string($m/@analang)"/>
<xsl:variable name="audiolang" select="string($m/@audio)"/>
<xsl:variable name="g1" select="string($m/@g1)"/>
<xsl:variable name="refcol" select="string($m/column[@role='reference']/@name)"/>

<!-- Index the LIFT by the Dekereke row key it carries. -->
<xsl:key name="entry-by-ref"
         match="entry"
         use="field[@type='Dekereke-Reference']/form/text"/>

<!-- Identity: everything not explicitly overridden survives byte for byte. -->
<xsl:template match="@*|node()">
  <xsl:copy><xsl:apply-templates select="@*|node()"/></xsl:copy>
</xsl:template>

<xsl:template match="data_form">
  <xsl:variable name="ref" select="normalize-space(*[name()=$refcol])"/>
  <xsl:variable name="found">
    <xsl:for-each select="$l">
      <!-- context switch into the LIFT document, so key() can see it -->
      <xsl:copy-of select="key('entry-by-ref',$ref)[1]"/>
    </xsl:for-each>
  </xsl:variable>
  <xsl:variable name="entry" select="exsl:node-set($found)/entry"/>
  <xsl:copy>
    <xsl:apply-templates select="@*"/>
    <xsl:apply-templates select="node()">
      <xsl:with-param name="entry" select="$entry"/>
    </xsl:apply-templates>
  </xsl:copy>
</xsl:template>

<!--
    One column of one record. $entry is the matching LIFT entry, or an empty
    result-tree fragment when A-Z+T never had this row — in which case every
    test below is false and the original value is copied.
-->
<xsl:template match="data_form/*">
  <xsl:param name="entry"/>
  <xsl:variable name="col" select="name()"/>
  <xsl:variable name="role" select="string($m/column[@name=$col]/@role)"/>
  <xsl:variable name="lang" select="string($m/column[@name=$col]/@lang)"/>
  <xsl:variable name="new">
    <xsl:choose>
      <xsl:when test="$role='phonetic'">
        <xsl:value-of select="$entry/citation/form[@lang=$analang]/text"/>
      </xsl:when>
      <xsl:when test="$role='orthographic'">
        <xsl:value-of select="$entry/lexical-unit/form[@lang=$analang]/text"/>
      </xsl:when>
      <xsl:when test="$role='phonemic'">
        <xsl:value-of
            select="$entry/citation/form[@lang=concat($analang,'-x-ipa')]/text"/>
      </xsl:when>
      <xsl:when test="$role='audio'">
        <xsl:value-of select="$entry/citation/form[@lang=$audiolang]/text"/>
      </xsl:when>
      <xsl:when test="$role='pos'">
        <xsl:value-of select="$entry/sense/grammatical-info/@value"/>
      </xsl:when>
      <xsl:when test="$role='gloss'">
        <!-- sense.glosses is a list per language; join, rather than lose. -->
        <xsl:for-each select="$entry/sense/gloss[@lang=$lang]/text">
          <xsl:if test="position()&gt;1">, </xsl:if>
          <xsl:value-of select="."/>
        </xsl:for-each>
      </xsl:when>
      <xsl:when test="$role='note'">
        <xsl:value-of select="$entry/field[@type='Dk_Notes']/form/text"/>
      </xsl:when>
      <xsl:when test="$role='frame'">
        <!-- The example whose location string is this column's name. -->
        <xsl:value-of select="$entry/sense/example
                    [field[@type='location']/form/text=$col]/form[@lang=$analang]/text"/>
      </xsl:when>
      <xsl:when test="$role='pitchtwin'">
        <xsl:variable name="frame"
                      select="string($m/column[@pitch=$col]/@name)"/>
        <xsl:value-of select="$entry/sense/example
                    [field[@type='location']/form/text=$frame]
                    /field[@type='tone']/form/text"/>
      </xsl:when>
      <xsl:when test="$role='tone'">
        <xsl:value-of select="$entry/sense/field[@type='tone']/form/text"/>
      </xsl:when>
      <xsl:when test="$role='cvprofileok'">
        <!-- the confirmed form: what the speaker's sorting was organised by -->
        <xsl:value-of select="$entry/sense/field[@type='cvprofile_lc']
                    /form[@lang=concat($analang,'-x-cvprofile')]/text"/>
      </xsl:when>
      <xsl:when test="$role='cvprofile'">
        <xsl:value-of select="$entry/sense/field[@type='cvprofile_lc']
                    /form[@lang=concat($analang,'-x-cvprofile_MT')]/text"/>
      </xsl:when>
      <xsl:when test="$role='field'">
        <xsl:variable name="type" select="string($m/column[@name=$col]/@field)"/>
        <xsl:value-of select="$entry/field[@type=$type]/form/text"/>
      </xsl:when>
      <!-- reference, skipflag and anything unmapped: never overwritten. -->
    </xsl:choose>
  </xsl:variable>
  <xsl:copy>
    <xsl:apply-templates select="@*"/>
    <xsl:choose>
      <!-- Only replace when A-Z+T actually has something to say. An empty
           result here means "no opinion", not "make it empty". -->
      <xsl:when test="string-length($new)&gt;0">
        <xsl:value-of select="$new"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates select="node()"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:copy>
</xsl:template>

</xsl:stylesheet>
