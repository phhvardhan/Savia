import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { ScrollToContent } from './components/layout/ScrollToContent';
import { RunTheme } from './components/layout/RunTheme';
import { RequireAuth } from './auth/RequireAuth';
import { AUTH_REQUIRED } from './auth/context';
import { LoginPage } from './pages/LoginPage';
import { ChangePage } from './pages/ChangePage';
import { DecidePage } from './pages/DecidePage';
import { DocumentPage } from './pages/DocumentPage';
import { HelpPage } from './pages/HelpPage';
import { HomePage } from './pages/HomePage';
import { LibraryPage } from './pages/LibraryPage';
import { ProjectsPage } from './pages/ProjectsPage';
import { WritingPage } from './pages/WritingPage';
import { SharingPage } from './pages/SharingPage';
import { PublishPage } from './pages/PublishPage';
import { HandoffPage } from './pages/HandoffPage';
import { TestReadyPage } from './pages/TestReadyPage';
import { TestWritingPage } from './pages/TestWritingPage';
import { CoveragePage } from './pages/CoveragePage';
import { GapsPage } from './pages/GapsPage';
import { InventoryPage } from './pages/InventoryPage';
import { ApprovePage } from './pages/ApprovePage';
import { ExecutionPage } from './pages/ExecutionPage';
import { ReadingPage } from './pages/ReadingPage';
import { ReviewsPage } from './pages/ReviewsPage';
import { SuggestionsPage } from './pages/SuggestionsPage';
import { StalePage } from './pages/StalePage';
import { RefreshPlanPage } from './pages/RefreshPlanPage';
import { ChainPage } from './pages/ChainPage';
import { IntakePage } from './pages/IntakePage';
import { MissingInfoPage } from './pages/MissingInfoPage';
import { StudioPage } from './pages/StudioPage';
import { WorkPage } from './pages/WorkPage';

/** Everything behind the session: the masthead, nav and the app's own routes. */
function AppRoutes() {
  return (
    <AppShell>
      <ScrollToContent />
      <RunTheme>
      <Routes>
        <Route path="/" element={<Navigate to="/work" replace />} />
        <Route path="/work" element={<HomePage />} />
        <Route path="/agents" element={<WorkPage />} />
        <Route path="/intake" element={<IntakePage />} />
        <Route path="/reading" element={<ReadingPage />} />
        <Route path="/writing" element={<WritingPage />} />
        <Route path="/document" element={<DocumentPage />} />
        <Route path="/change" element={<ChangePage />} />
        <Route path="/stale" element={<StalePage />} />
        <Route path="/refresh-plan" element={<RefreshPlanPage />} />
        <Route path="/chain" element={<ChainPage />} />
        <Route path="/missing-info" element={<MissingInfoPage />} />
        <Route path="/suggestions" element={<SuggestionsPage />} />
        <Route path="/decide" element={<DecidePage />} />
        <Route path="/sharing" element={<SharingPage />} />
        <Route path="/publish" element={<PublishPage />} />
        <Route path="/handoff" element={<HandoffPage />} />
        <Route path="/test-ready" element={<TestReadyPage />} />
        <Route path="/test-writing" element={<TestWritingPage />} />
        <Route path="/coverage" element={<CoveragePage />} />
        <Route path="/gaps" element={<GapsPage />} />
        <Route path="/inventory" element={<InventoryPage />} />
        <Route path="/approve" element={<ApprovePage />} />
        <Route path="/execution" element={<ExecutionPage />} />
        <Route path="/library" element={<LibraryPage />} />
        <Route path="/studio" element={<StudioPage />} />
        <Route path="/reviews" element={<ReviewsPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/help" element={<HelpPage />} />
        <Route path="*" element={<Navigate to="/work" replace />} />
      </Routes>
      </RunTheme>
    </AppShell>
  );
}

export default function App() {
  if (!AUTH_REQUIRED) return <AppRoutes />;
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="*"
        element={
          <RequireAuth>
            <AppRoutes />
          </RequireAuth>
        }
      />
    </Routes>
  );
}
