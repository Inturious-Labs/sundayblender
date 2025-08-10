<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="html" encoding="UTF-8" />
  <xsl:template match="/">
    <html>
      <head>
        <meta charset="UTF-8"/>
        <title><xsl:value-of select="/rss/channel/title"/></title>
        <style>
          body { font-family: system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; margin: 2rem; line-height: 1.5; }
          h1 { margin-bottom: .25rem; }
          .desc { color: #555; margin-bottom: 1rem; }
          li { margin: .4rem 0; }
          small { color:#666; }
        </style>
      </head>
      <body>
        <h1><xsl:value-of select="/rss/channel/title"/></h1>
        <div class="desc"><xsl:value-of select="/rss/channel/description"/></div>
        <ol>
          <xsl:for-each select="/rss/channel/item">
            <li>
              <a>
                <xsl:attribute name="href"><xsl:value-of select="link"/></xsl:attribute>
                <xsl:value-of select="title"/>
              </a>
              <br/>
              <small><xsl:value-of select="pubDate"/></small>
            </li>
          </xsl:for-each>
        </ol>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
