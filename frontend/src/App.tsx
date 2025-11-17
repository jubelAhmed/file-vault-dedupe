import React from 'react';
import { UserIdProvider, useUserId } from './contexts/UserIdContext';
import UserIdSelector from './components/UserIdSelector';
import StatsPanel from './components/StatsPanel';
import { FileUpload } from './components/FileUpload';
import { FileList } from './components/FileList';

const AppContent: React.FC = () => {
  const { userId } = useUserId();
  
  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">File Vault Dedupe</h1>
          <p className="mt-1 text-sm text-gray-500">
            File management system with deduplication
          </p>
        </div>
      </header>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="space-y-6">
            <UserIdSelector />
            <StatsPanel />
            <div className="bg-white shadow sm:rounded-lg">
              <FileUpload />
            </div>
            <div className="bg-white shadow sm:rounded-lg">
              <FileList key={userId} />
            </div>
          </div>
        </div>
      </main>
      <footer className="bg-white shadow mt-8">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-500">
            © 2024 File Vault Dedupe. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

function App() {
  return (
    <UserIdProvider>
      <AppContent />
    </UserIdProvider>
  );
}

export default App;
