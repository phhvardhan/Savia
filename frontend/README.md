# SAVIA — J&J Technology

React + TypeScript implementation of the SAVIA agent-platform screens from the
Figma reference exports. Built with Vite and React Router.

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # typecheck + production bundle
npm run lint
```

## Routes

Each primary nav item maps to one reference screen:

| Route       | Nav item          | Screen                                      |
| ----------- | ----------------- | ------------------------------------------- |
| `/work`     | Work (default)    | Every agent, and what it can actually do    |
| `/library`  | Library           | Tell us what you are trying to get done.    |
| `/studio`   | Studio            | The sequences your team runs again and again |
| `/reviews`  | Reviews           | Two things are waiting on people            |
| `/projects` | Projects          | The whole run on one screen                 |
| `/help`     | Help & guidance   | Exactly what crossed between them           |

## Structure

```
src/
  components/layout/   AppShell (top bar, masthead, primary nav), Logo
  components/ui/       Button, Badge, Card, Section, StatusPill, DataTable,
                       StatGrid, Icons
  data/agents.ts       The ten agents: capability sheets and library contract rows
  pages/               One component per screen, each with a CSS module
  styles/globals.css   Design tokens, reset and the shared `.shell` container
```

Colours, spacing and type scale are sampled from the reference exports and
declared as custom properties on `:root` in `styles/globals.css`.

### Typography

The J&J Johnson family is self-hosted from `public/assets/fonts/` as WOFF2:
Johnson Display (`--font-display`, headings) and Johnson Text (`--font-sans`,
everything else), each in Light 300 / Regular 400 / Medium 500 / Bold 700. The
source `.otf` files are kept in `design-assets/fonts/` so they are not served.

## Notes on assets and content

- No icon or photo assets were supplied with the reference, so the interface
  glyphs in `components/ui/Icons.tsx` and the SAVIA mark in
  `components/layout/Logo.tsx` are minimal inline SVGs. The small dashed
  squares in the agent cards are the reference's own icon placeholders.
- `public/assets/stage-*.png` are cropped from the supplied reference exports.
  `public/assets/avatar.png` is the signed-in user's headshot (Mrunal), a
  square head-crop of the supplied `public/assets/mrunal-photo.jpeg`.
- The four "Browse by lifecycle stage" cards are cut off in the reference
  export below their agent counts, so their names are taken from the Stage
  column of the library table (Requirements 3, Design 3, Change & testing 2,
  Release & cutover 2 — matching the counts shown).

## Responsive behaviour

Three breakpoints: 1000px (tablet) and 620/560px (mobile). Wide tables and the
run graph on `/projects` scroll horizontally inside their panel rather than
reflowing, which would reorder the handoffs.
