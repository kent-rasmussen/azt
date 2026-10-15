<?xml version="1.0" encoding="UTF-8"?>
<!--
    Dekereke <phon_data> -> LIFT, for A-Z+T.

    Dekereke column names are defined by the user, per database, so this
    stylesheet matches on NO column name of its own. Every name it uses comes
    from the mapping document io_put/dekereke.py writes and passes in $map,
    and columns are reached with *[name()=$column]. Roles, not names.

    io_put/dekereke.py has already stamped each <data_form> with @guid,
    @senseid and @date (XSLT 1.0 can mint none of those) and marked with @skip
    the records that cannot become entries.

    The LIFT written here is the profile A-Z+T itself writes — see
    planning/research/lift-profile.md. In particular the headword goes in
    <citation>, not <lexical-unit>; the audio language tag carries -Zxxx-;
    and imported tone and CV profiles use the _MT (machine) form, because the
    plain form means "a speaker confirmed this by ear" and nobody has yet.
-->
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:output method="xml" encoding="UTF-8" indent="yes"/>
<xsl:strip-space elements="*"/>

<xsl:param name="map"/>

<xsl:variable name="m" select="document($map)/dekerekeMap"/>
<xsl:variable name="analang" select="string($m/@analang)"/>
<xsl:variable name="audiolang" select="string($m/@audio)"/>
<!-- A-Z+T tags its own bookkeeping with the first gloss language it finds in
     the file, which is not necessarily the project's first. -->
<xsl:variable name="g1" select="string($m/@g1)"/>
<xsl:variable name="tonelang" select="concat($analang,'-x-tone_MT')"/>
<xsl:variable name="profilelang" select="concat($analang,'-x-cvprofile_MT')"/>
<xsl:variable name="okprofilelang" select="concat($analang,'-x-cvprofile')"/>
<xsl:variable name="phoncol" select="string($m/column[@role='phonetic']/@name)"/>
<xsl:variable name="refcol" select="string($m/column[@role='reference']/@name)"/>

<!--
    A record may hold several takes of one word: Dekereke names them by
    suffixing the record's sound file per column ('Speaker2' -> '-sp2'), so
    each column's own recording sits beside that column's text.
-->
<xsl:template name="audio-form">
  <xsl:param name="rec"/>
  <xsl:param name="suffix"/>
  <xsl:if test="$suffix and $rec/@soundstem">
    <form lang="{$audiolang}">
      <text><xsl:value-of select="concat($rec/@soundstem,$suffix,$rec/@soundext)"/></text>
    </form>
  </xsl:if>
</xsl:template>

<xsl:template match="/phon_data">
  <lift producer="A-Z+T Dekereke import" version="0.13">
    <xsl:if test="$refcol">
      <!-- Declaring the custom field is what keeps the row key legible to
           FLEx and WeSay instead of being dropped on their import. -->
      <header>
        <fields>
          <field tag="Dekereke-Reference">
            <description>
              <form lang="{$g1}">
                <text>Record key from the source Dekereke database.</text>
              </form>
            </description>
          </field>
        </fields>
      </header>
    </xsl:if>
    <xsl:apply-templates select="data_form[not(@skip)]"/>
  </lift>
</xsl:template>

<xsl:template match="data_form">
  <xsl:variable name="rec" select="."/>
  <xsl:variable name="headword"
                select="normalize-space($rec/*[name()=$phoncol])"/>
  <entry guid="{@guid}" id="{concat($headword,'_',@guid)}"
         dateCreated="{@date}" dateModified="{@date}">

    <!-- Orthography, where the user has a column for it. A-Z+T leaves this
         element empty; FLEx and WeSay both read it as the headword. -->
    <lexical-unit>
      <xsl:for-each select="$m/column[@role='orthographic']">
        <xsl:variable name="col" select="string(@name)"/>
        <xsl:if test="normalize-space($rec/*[name()=$col])">
          <form lang="{$analang}">
            <text><xsl:value-of select="normalize-space($rec/*[name()=$col])"/></text>
          </form>
        </xsl:if>
      </xsl:for-each>
    </lexical-unit>

    <!-- The form A-Z+T sorts. Its language scan only looks at citation,
         lexical-unit and pronunciation, so this placement is not optional. -->
    <citation>
      <form lang="{$analang}"><text><xsl:value-of select="$headword"/></text></form>
      <xsl:for-each select="$m/column[@role='phonemic']">
        <xsl:variable name="col" select="string(@name)"/>
        <xsl:if test="normalize-space($rec/*[name()=$col])">
          <form lang="{concat($analang,'-x-ipa')}">
            <text><xsl:value-of select="normalize-space($rec/*[name()=$col])"/></text>
          </form>
        </xsl:if>
      </xsl:for-each>
      <!-- Bare filename on both sides; the driver copies the .wav into the
           project's audio folder, which LIFT never names. -->
      <xsl:choose>
        <xsl:when test="$m/column[@name=$phoncol]/@suffix">
          <xsl:call-template name="audio-form">
            <xsl:with-param name="rec" select="$rec"/>
            <xsl:with-param name="suffix"
                            select="string($m/column[@name=$phoncol]/@suffix)"/>
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:for-each select="$m/column[@role='audio']">
            <xsl:variable name="col" select="string(@name)"/>
            <xsl:if test="normalize-space($rec/*[name()=$col])">
              <form lang="{$audiolang}">
                <text><xsl:value-of select="normalize-space($rec/*[name()=$col])"/></text>
              </form>
            </xsl:if>
          </xsl:for-each>
        </xsl:otherwise>
      </xsl:choose>
    </citation>

    <!-- The row key, so a second import updates instead of duplicating. -->
    <xsl:if test="normalize-space($rec/*[name()=$refcol])">
      <field type="Dekereke-Reference">
        <form lang="{$g1}">
          <text><xsl:value-of select="normalize-space($rec/*[name()=$refcol])"/></text>
        </form>
      </field>
    </xsl:if>

    <!-- Every column A-Z+T has no home for still travels, as a named field,
         so nothing in the user's database silently disappears. -->
    <xsl:for-each select="$m/column[@role='field']">
      <xsl:variable name="col" select="string(@name)"/>
      <xsl:if test="normalize-space($rec/*[name()=$col])">
        <field type="{@field}">
          <form lang="{$analang}">
            <text><xsl:value-of select="normalize-space($rec/*[name()=$col])"/></text>
          </form>
          <xsl:call-template name="audio-form">
            <xsl:with-param name="rec" select="$rec"/>
            <xsl:with-param name="suffix" select="string(@suffix)"/>
          </xsl:call-template>
        </field>
      </xsl:if>
    </xsl:for-each>

    <xsl:for-each select="$m/column[@role='note']">
      <xsl:variable name="col" select="string(@name)"/>
      <xsl:if test="string($rec/*[name()=$col])">
        <field type="Dk_Notes">
          <form lang="{$g1}">
            <!-- Not normalized: a note's own spacing is the linguist's. -->
            <text><xsl:value-of select="$rec/*[name()=$col]"/></text>
          </form>
        </field>
      </xsl:if>
    </xsl:for-each>

    <sense id="{@senseid}">
      <xsl:for-each select="$m/column[@role='pos']">
        <xsl:variable name="col" select="string(@name)"/>
        <xsl:if test="normalize-space($rec/*[name()=$col])">
          <grammatical-info value="{normalize-space($rec/*[name()=$col])}"/>
        </xsl:if>
      </xsl:for-each>

      <!-- A-Z+T's own addentry writes the same text to definition and gloss,
           so an imported entry looks like one it made itself. At least one
           gloss must exist somewhere in the file or A-Z+T cannot open it. -->
      <definition>
        <xsl:for-each select="$m/column[@role='gloss']">
          <xsl:variable name="col" select="string(@name)"/>
          <xsl:if test="normalize-space($rec/*[name()=$col])">
            <form lang="{@lang}">
              <text><xsl:value-of select="normalize-space($rec/*[name()=$col])"/></text>
            </form>
          </xsl:if>
        </xsl:for-each>
      </definition>
      <xsl:for-each select="$m/column[@role='gloss']">
        <xsl:variable name="col" select="string(@name)"/>
        <xsl:if test="normalize-space($rec/*[name()=$col])">
          <gloss lang="{@lang}">
            <text><xsl:value-of select="normalize-space($rec/*[name()=$col])"/></text>
          </gloss>
        </xsl:if>
      </xsl:for-each>

      <xsl:for-each select="$m/column[@role='tone']">
        <xsl:variable name="col" select="string(@name)"/>
        <xsl:if test="normalize-space($rec/*[name()=$col])">
          <field type="tone">
            <form lang="{$tonelang}">
              <text><xsl:value-of select="normalize-space($rec/*[name()=$col])"/></text>
            </form>
          </field>
        </xsl:if>
      </xsl:for-each>

      <!--
          A-Z+T slices words by the CONFIRMED profile (the plain form) and only
          fills in from the machine form (…_MT) where there is no confirmed one,
          never overwriting it. So a syllable-profile column the researcher
          curated by hand goes in the plain form and is honoured as it stands;
          one that was auto-generated goes in the machine form, where A-Z+T
          will treat it as a guess to be checked.
      -->
      <xsl:for-each select="$m/column[@role='cvprofileok' or @role='cvprofile']">
        <xsl:variable name="col" select="string(@name)"/>
        <xsl:if test="normalize-space($rec/*[name()=$col])">
          <field type="cvprofile_lc">
            <xsl:if test="@role='cvprofileok'">
              <form lang="{$okprofilelang}">
                <text><xsl:value-of select="normalize-space($rec/*[name()=$col])"/></text>
              </form>
            </xsl:if>
            <form lang="{$profilelang}">
              <text><xsl:value-of select="normalize-space($rec/*[name()=$col])"/></text>
            </form>
          </field>
        </xsl:if>
      </xsl:for-each>

      <!-- An elicitation frame column becomes one example per record that has
           a value in it: A-Z+T keys examples by the location string, which is
           exactly the column name, so the frame set survives a round trip. -->
      <xsl:for-each select="$m/column[@role='frame']">
        <xsl:variable name="col" select="string(@name)"/>
        <xsl:variable name="pitch" select="string(@pitch)"/>
        <xsl:if test="normalize-space($rec/*[name()=$col])">
          <example>
            <form lang="{$analang}">
              <text><xsl:value-of select="normalize-space($rec/*[name()=$col])"/></text>
            </form>
            <xsl:call-template name="audio-form">
              <xsl:with-param name="rec" select="$rec"/>
              <xsl:with-param name="suffix" select="string(@suffix)"/>
            </xsl:call-template>
            <field type="location">
              <form lang="{$g1}"><text><xsl:value-of select="$col"/></text></form>
            </field>
            <xsl:if test="$pitch and normalize-space($rec/*[name()=$pitch])">
              <field type="tone">
                <form lang="{$tonelang}">
                  <text><xsl:value-of select="normalize-space($rec/*[name()=$pitch])"/></text>
                </form>
              </field>
            </xsl:if>
          </example>
        </xsl:if>
      </xsl:for-each>
    </sense>
  </entry>
</xsl:template>

</xsl:stylesheet>
