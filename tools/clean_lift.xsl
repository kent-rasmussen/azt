<?xml version="1.0" encoding="UTF-8"?>
<!--
  clean_lift.xsl — de-pollute a LIFT file that has accreted duplicates and
  empty/redundant forms over time.

  Rules (as requested):
    1. Duplicates reduced to one (keep the FIRST): trait, sense, gloss,
       lexical-unit, and any duplicate <form> (by lang) within a parent.
    2. Empty content removed: <form> with no text and no annotation; <gloss>
       with no text; <definition> whose forms are all empty.
    3. A lexical-unit <form lang="L"> is removed when L also appears as a
       <gloss> language or a <definition>/<form> language in the same entry
       (i.e. the lexical-unit form is really an LWC gloss, not object-language
       data — this is what mis-drives analang detection).

  Run (writes a NEW file — always keep the original):
    xsltproc tools/clean_lift.xsl DIRTY.lift > CLEAN.lift
  or, with Python + lxml:
    python -c "from lxml import etree as E; \
      t=E.XSLT(E.parse('tools/clean_lift.xsl')); \
      open('CLEAN.lift','wb').write(E.tostring(t(E.parse('DIRTY.lift')), \
      xml_declaration=True, encoding='UTF-8'))"

  Then diff DIRTY.lift CLEAN.lift and eyeball before replacing.
-->
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="yes" encoding="UTF-8"/>
  <xsl:strip-space elements="*"/>

  <!-- Identity: copy everything not matched by a rule below. -->
  <xsl:template match="@*|node()">
    <xsl:copy><xsl:apply-templates select="@*|node()"/></xsl:copy>
  </xsl:template>

  <!-- ==== Rule 1: de-duplicate, keeping the first occurrence ==== -->

  <!-- duplicate trait: an earlier sibling has the same name AND value -->
  <xsl:template priority="3"
      match="trait[preceding-sibling::trait[@name=current()/@name
                                            and @value=current()/@value]]"/>

  <!-- duplicate sense: an earlier sibling has the same id. NB: XSLT 1.0 can't
       deep-compare subtrees, so this assumes a repeated sense id is a true
       duplicate (ids should be unique); it keeps the first. Same-id with
       DIFFERENT content is malformed — review those by hand. -->
  <xsl:template priority="3"
      match="sense[@id and preceding-sibling::sense[@id=current()/@id]]"/>

  <!-- extra lexical-unit: an entry carries one; keep the first. -->
  <xsl:template priority="3"
      match="lexical-unit[preceding-sibling::lexical-unit]"/>

  <!-- ==== Rule 2 (gloss/definition) ==== -->

  <!-- gloss: drop when empty, OR an identical duplicate (same lang AND same
       text) of an earlier sibling. A same-lang gloss with DIFFERENT text is a
       conflict, not a duplicate, and is LEFT for a human to resolve. -->
  <xsl:template priority="3" match="gloss[
        not(normalize-space(text))
        or preceding-sibling::gloss[@lang=current()/@lang
              and normalize-space(text)=normalize-space(current()/text)]]"/>

  <!-- definition: drop when all of its forms are empty -->
  <xsl:template priority="3" match="definition[not(normalize-space(.))]"/>

  <!-- B (safety net; per you, should never happen): a sense with no meaningful
       content at all — no glossed text, no definition text, no
       grammatical-info, example, illustration, field text, or trait. -->
  <xsl:template priority="3" match="sense[
        not(gloss[normalize-space(text)])
        and not(definition[normalize-space(.)])
        and not(grammatical-info)
        and not(example)
        and not(illustration)
        and not(field[normalize-space(.)])
        and not(trait)]"/>

  <!-- ==== Rule 3: lexical-unit form that duplicates a gloss/definition lang ==== -->
  <!-- higher priority than the generic form rule, so it wins when both match -->
  <xsl:template priority="4" match="lexical-unit/form[
        @lang = ancestor::entry//gloss/@lang
        or @lang = ancestor::entry//definition/form/@lang]"/>

  <!-- ==== Rule 1 (forms) + Rule 2 (empty forms), any parent ==== -->
  <!-- drop a form when it is empty (no text and no annotation), OR an identical
       duplicate (same lang AND same text) of an earlier sibling. A same-lang
       form with DIFFERENT text is a conflict, not a duplicate, and is LEFT. -->
  <xsl:template priority="2" match="form[
        (not(normalize-space(text)) and not(annotation))
        or preceding-sibling::form[@lang=current()/@lang
              and normalize-space(text)=normalize-space(current()/text)]]"/>

</xsl:stylesheet>
