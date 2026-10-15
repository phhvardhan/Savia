import { useRef, type DependencyList, type RefObject, type SVGProps } from 'react';
import { useConnectorEnds } from '../../hooks/useConnectorEnds';

interface FanConnectorProps {
  className: string;
  /** The column of cards, and the cards in it. */
  cards: RefObject<HTMLElement | null>;
  cardSelector: string;
  /** The one box every line meets (the agent / recommender box). */
  hub: RefObject<HTMLElement | null>;
  /** Which side of the svg the hub is on. */
  hubSide: 'left' | 'right';
  /** Per-line overrides (colour, dash) on top of the default grey line. */
  line?: (index: number) => SVGProps<SVGPathElement>;
  deps: DependencyList;
}

/**
 * Lines from each card to the hub box, measured from where both actually sit,
 * so they meet the boxes however tall the board or however many cards.
 */
export function FanConnector({ className, cards, cardSelector, hub, hubSide, line, deps }: FanConnectorProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const cardYs = useConnectorEnds(cards, svgRef, cardSelector, deps);
  // The hub's own rows (head and steps); the lines meet it spread across them.
  const hubYs = useConnectorEnds(hub, svgRef, ':scope > *', deps);
  const top = Math.min(...hubYs);
  const bottom = Math.max(...hubYs);

  return (
    <svg ref={svgRef} className={className} viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
      {hubYs.length > 0 &&
        cardYs.map((cardY, i) => {
          const hubY = cardYs.length === 1 ? (top + bottom) / 2 : top + ((bottom - top) * (i + 0.5)) / cardYs.length;
          const [y0, y1] = hubSide === 'left' ? [hubY, cardY] : [cardY, hubY];
          return (
            <path
              key={i}
              d={`M0 ${y0} C 50 ${y0}, 50 ${y1}, 100 ${y1}`}
              fill="none"
              stroke="#C3C4C5"
              strokeWidth="1.2"
              // px, not viewBox units: the svg is stretched far more tall than wide
              vectorEffect="non-scaling-stroke"
              {...line?.(i)}
            />
          );
        })}
    </svg>
  );
}
