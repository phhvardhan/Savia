import { useEffect, useState, type CSSProperties } from 'react';
import { brandFontUrl, getBrandDocument, type BrandDocument, type BrandRole } from '../lib/savia';

/**
 * Read-only J&J-branded view of an agent's output, laid out like the Word
 * download: red cover band, red section headings, records as labelled blocks.
 * Every font, size and colour comes from the backend's brand tokens; no brand
 * values live in the frontend.
 */
export function BrandPreview({ artifactId }: { artifactId: string }) {
  const [data, setData] = useState<BrandDocument | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    setData(null);
    setError('');
    getBrandDocument(artifactId)
      .then(setData)
      .catch((e: Error) => setError(e.message));
  }, [artifactId]);

  if (error) return <p role="alert" style={{ whiteSpace: 'pre-wrap' }}>Brand preview failed: {error}</p>;
  if (!data) return <p>Loading the brand preview…</p>;

  const { document: doc, styles, fonts, page_background, rule_color } = data;
  const role = (r: BrandRole, margin = `0 0 ${styles[r].size_pt * 0.5}pt`): CSSProperties => ({
    fontFamily: `'${styles[r].font_family}', Arial, sans-serif`,
    fontSize: `${styles[r].size_pt}pt`,
    fontWeight: styles[r].bold ? 700 : 400,
    color: `#${styles[r].color}`,
    textAlign: 'left',
    textTransform: 'none', // brand: no all-caps, no effects, even if inherited from the page
    textShadow: 'none',
    letterSpacing: 'normal',
    lineHeight: 1.35,
    margin,
    whiteSpace: 'pre-line',
  });
  const fontFaces = fonts
    .map((f) => `@font-face{font-family:'${f.family}';font-weight:${f.weight};src:url('${brandFontUrl(f.file)}');}`)
    .join('\n');
  const gutter = '56px';

  return (
    <article style={{ background: `#${page_background}`, maxWidth: 860, boxShadow: '0 1px 4px rgba(0,0,0,0.12)' }}>
      {fontFaces && <style>{fontFaces}</style>}

      <header style={{ background: `#${styles.headline.background}`, padding: `44px ${gutter} 36px` }}>
        {doc.eyebrow && <p style={role('eyebrow')}>{doc.eyebrow}</p>}
        <h1 style={role('headline', '0 0 10px')}>{doc.headline}</h1>
        {doc.subhead && <p style={role('subhead', '0')}>{doc.subhead}</p>}
      </header>

      <div style={{ padding: `8px ${gutter} 40px` }}>
        {doc.sections.map((section) => (
          <section key={section.heading}>
            <h2 style={role('section_heading', '28px 0 10px')}>{section.heading}</h2>
            {section.body.length > 1 ? (
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {section.body.map((text, i) => (
                  <li key={i} style={role('body', '0 0 4px')}>{text}</li>
                ))}
              </ul>
            ) : (
              section.body.map((text, i) => <p key={i} style={role('body')}>{text}</p>)
            )}
            {section.items.map((item, i) => (
              <div key={i} style={{ borderTop: i ? `1px solid #${rule_color}` : 'none', paddingTop: i ? 12 : 0, marginTop: 12 }}>
                {item.title && <p style={role('item_title', '0 0 6px')}>{item.title}</p>}
                {item.fields.map((field) => (
                  <div key={field.label} style={{ display: 'grid', gridTemplateColumns: '1.9in 1fr', marginBottom: 3 }}>
                    <span style={{ ...role('body', '0'), fontWeight: 700 }}>{field.label}</span>
                    <span style={role('body', '0')}>{field.value}</span>
                  </div>
                ))}
              </div>
            ))}
          </section>
        ))}
        <footer style={role('footer', '40px 0 0')}>{doc.footer}</footer>
      </div>
    </article>
  );
}
