import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * On navigation, land at the top of the page content rather than the very top
 * of the document — the top strip, masthead and nav scroll out of the way.
 * Measured from <main> so it stays correct as the header resizes per breakpoint.
 */
export function ScrollToContent() {
  const { pathname } = useLocation();

  useEffect(() => {
    const main = document.querySelector('main');
    window.scrollTo({ top: main ? main.offsetTop : 0, left: 0 });
  }, [pathname]);

  return null;
}
