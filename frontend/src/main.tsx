import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
// AUTH DISABLED — restore by wrapping <App /> in <AuthProvider> again.
// import { AuthProvider } from './auth/AuthProvider';
import { AttachmentProvider } from './state/AttachmentProvider';
import { RunProvider } from './state/RunProvider';
import './styles/globals.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AttachmentProvider>
        <RunProvider>
          <App />
        </RunProvider>
      </AttachmentProvider>
    </BrowserRouter>
  </StrictMode>,
);
