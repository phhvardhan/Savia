import { useLayoutEffect, useState, type DependencyList, type RefObject } from 'react';

/**
 * Where each card in `list` sits, as % of the connector svg's height, so the
 * connector lines can end on the cards however tall or many they are.
 * Returns [] while the connector is hidden (narrow screens).
 */
export function useConnectorEnds(
  list: RefObject<HTMLElement | null>,
  svg: RefObject<SVGSVGElement | null>,
  cardSelector: string,
  deps: DependencyList,
): number[] {
  const [ends, setEnds] = useState<number[]>([]);

  useLayoutEffect(() => {
    const listEl = list.current;
    const svgEl = svg.current;
    if (!listEl || !svgEl) return;
    const measure = () => {
      const box = svgEl.getBoundingClientRect();
      if (!box.height) return;
      const ys = [...listEl.querySelectorAll(cardSelector)].map((card) => {
        const r = card.getBoundingClientRect();
        return ((r.top + r.height / 2 - box.top) / box.height) * 100;
      });
      setEnds((prev) =>
        prev.length === ys.length && prev.every((y, i) => Math.abs(y - ys[i]) < 0.5) ? prev : ys,
      );
    };
    measure();
    // The board as a whole: card or column height changes move the ends.
    const observer = new ResizeObserver(measure);
    observer.observe(listEl);
    observer.observe(svgEl);
    // Reveal animations slide cards with transforms, which ResizeObserver can't see.
    listEl.addEventListener('animationend', measure);
    return () => {
      observer.disconnect();
      listEl.removeEventListener('animationend', measure);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return ends;
}
