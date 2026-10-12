/** The filter chips on the test inventory, shared so other pages can deep-link to one. */
export const INVENTORY_FILTERS = [
  'All 62',
  'Needs a decision · 2',
  'Edited by you · 3',
  'Automation candidates · 14',
] as const;

export type InventoryFilter = (typeof INVENTORY_FILTERS)[number];

/** The two open rows — what Coverage calls "the two gaps". */
export const GAPS_FILTER: InventoryFilter = 'Needs a decision · 2';

export const DEFAULT_FILTER: InventoryFilter = INVENTORY_FILTERS[0];
