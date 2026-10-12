# Original static content

Every hard-coded array and string that was replaced when the pages were wired
to the backend. This project is not a git repository, so there is no history to
recover these from — they live here instead.

They are kept as **real exported constants**, not comments, so TypeScript keeps
checking them. A commented-out block silently rots the moment a type changes;
this way a compile error tells you if a shape has drifted.

## Restoring a page

1. Open the matching file, e.g. `readingPage.static.ts`.
2. Copy the constants back into the page.
3. Delete the API call (`useEffect`) and the state it feeds, and point the JSX
   back at the constants.

Nothing here is imported by the app. Deleting this folder changes no behaviour.
