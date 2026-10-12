/**
 * Original button destinations, before the click-through chain was wired.
 * Each entry is: page → button label → where it used to go.
 */
export const ORIGINAL_NAVIGATION = [
  { page: 'CoveragePage', button: 'Look at the two gaps', to: '/gaps' },
  { page: 'InventoryPage', button: 'Approve and assign', to: '/approve' },
  { page: 'GapsPage', button: 'Accept and move on', to: null },
  { page: 'ExecutionPage', button: 'Raise it against the design', to: null },
  { page: 'ProjectsPage', button: 'Go to the approval', to: null },
  { page: 'ProjectsPage', button: 'See the full history', to: null },
  { page: 'HomePage', button: 'Find my agents', to: null },
  { page: 'PlanPage', button: 'Change the plan', to: null },
] as const;

/** InventoryPage filter chips were decorative — they never filtered the rows. */
export const INVENTORY_FILTERS_WERE_DECORATIVE = true;

/** StalePage ("The BRD changed…") did not exist; it was added for this flow. */
export const STALE_PAGE_WAS_ADDED = true;
