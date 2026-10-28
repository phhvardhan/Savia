/**
 * Where each destination opens. Set VITE_<NAME>_URL in frontend/.env to point at your own
 * tenant (for example https://yourteam.atlassian.net/wiki); the defaults open the product's site.
 */
const env = import.meta.env as Record<string, string | undefined>;

export const PLATFORMS = {
  confluence: {
    name: 'Confluence',
    logo: '/assets/logos/confluence.svg',
    url: env.VITE_CONFLUENCE_URL || 'https://www.atlassian.com/software/confluence',
  },
  jira: {
    name: 'Jira',
    logo: '/assets/logos/jira.png',
    url: env.VITE_JIRA_URL || 'https://www.atlassian.com/software/jira',
  },
  sharepoint: {
    name: 'SharePoint',
    logo: '/assets/logos/sharepoint.svg',
    url: env.VITE_SHAREPOINT_URL || 'https://www.microsoft.com/microsoft-365/sharepoint/collaboration',
  },
  teams: {
    name: 'Teams',
    logo: '/assets/logos/teams.svg',
    url: env.VITE_TEAMS_URL || 'https://teams.microsoft.com',
  },
  word: { name: 'Word', logo: '/assets/logos/word.svg', url: '' },
  powerpoint: { name: 'PowerPoint', logo: '/assets/logos/powerpoint.svg', url: '' },
} as const;
