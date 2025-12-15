import { useState, useEffect } from 'react';
import { AuthScreen } from './components/AuthScreen';
import { Dashboard } from './components/Dashboard';
import { Toaster } from 'react-hot-toast';

export default function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));

  // Simple auth persistence
  useEffect(() => {
    if (token) localStorage.setItem('token', token);
    else localStorage.removeItem('token');
  }, [token]);

  return (
    <div className="min-h-screen bg-gray-50 font-sans text-gray-900 selection:bg-purple-200">
      <Toaster position="top-center" />
      <div className="max-w-md mx-auto min-h-screen bg-white shadow-2xl overflow-hidden relative border-x border-gray-100">
        {!token ? (
          <AuthScreen onLogin={setToken} />
        ) : (
          <Dashboard token={token} onLogout={() => setToken(null)} />
        )}
      </div>
    </div>
  );
}