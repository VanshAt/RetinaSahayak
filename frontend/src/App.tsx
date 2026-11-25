import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { LoginPage } from './pages/LoginPage';
import { WorkerWorkspace } from './pages/WorkerWorkspace';
import { DoctorCockpit } from './pages/DoctorCockpit';
import { AdminAnalytics } from './pages/AdminAnalytics';

const AppContent: React.FC = () => {
  const { user, loading } = useAuth();
  const [currentTab, setCurrentTab] = useState<string>('worker');

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center text-white">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <div className="text-sm font-semibold text-slate-300">Loading RetinaSahayak Portal...</div>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Navbar currentTab={currentTab} onSelectTab={setCurrentTab} />

      <main className="flex-1 pb-16">
        {currentTab === 'worker' && <WorkerWorkspace />}
        {currentTab === 'doctor' && <DoctorCockpit />}
        {currentTab === 'admin' && <AdminAnalytics />}
      </main>

      {/* Prominent CDSS Disclaimer Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 px-4 text-center text-xs text-slate-500">
        <div className="max-w-5xl mx-auto">
          <span className="font-bold text-slate-700">Notice:</span> RetinaSahayak is an assistive clinical decision support system designed for rural screening triage. It does not provide autonomous diagnostic declarations. Final care decisions must be verified by a registered ophthalmologist.
        </div>
      </footer>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
