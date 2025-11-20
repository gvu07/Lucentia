import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { PlaidLink } from 'react-plaid-link';
import api, { authAPI, plaidAPI, dashboardAPI } from './api';
import Dashboard from './components/Dashboard';
import Insights from './components/Insights';
import Transactions from './components/Transactions';
import Accounts from './components/Accounts';
import Login from './components/Login';
import Register from './components/Register';
import Navigation from './components/Navigation';
import './index.css';

function App() {
  const [user, setUser] = useState(null);
  const [linkToken, setLinkToken] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.localStorage.getItem('plaid_link_token');
    }
    return null;
  });
  const [isConnected, setIsConnected] = useState(false);
  const [linkError, setLinkError] = useState(null);
  const [linkLoading, setLinkLoading] = useState(false);
  const isOauthRedirect =
    typeof window !== 'undefined' &&
    window.location.href.includes('oauth_state_id=');


  const fetchLinkToken = useCallback(async (userId, options = {}) => {
    if (!userId) {
      setLinkError('Unable to start Plaid Link without user information.');
      return;
    }
    const { force = false } = options;
    if (!force && typeof window !== 'undefined') {
      const existingToken = window.localStorage.getItem('plaid_link_token');
      if (existingToken) {
        setLinkToken(existingToken);
        return;
      }
    }
    setLinkError(null);
    setLinkLoading(true);
    try {
      const response = await plaidAPI.createLinkToken();
      setLinkToken(response.link_token);
      if (typeof window !== 'undefined') {
        window.localStorage.setItem('plaid_link_token', response.link_token);
      }
    } catch (error) {
      setLinkToken(null);
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem('plaid_link_token');
      }
      setLinkError(error.response?.data?.detail || 'Unable to start Plaid Link. Please try again.');
      console.warn('Plaid link token failed:', error?.response?.data || error);
    } finally {
      setLinkLoading(false);
    }
  }, []);

  const checkConnectionStatus = useCallback(
    async (userId) => {
      if (!userId) {
        setIsConnected(false);
        return false;
      }
      try {
        const accounts = await dashboardAPI.getAccounts();
        const connected = Array.isArray(accounts) && accounts.length > 0;
        setIsConnected(connected);
        if (!connected) {
          await fetchLinkToken(userId);
        } else {
          setLinkToken(null);
        }
        return connected;
      } catch (error) {
        console.warn('Unable to verify connected accounts', error);
        setIsConnected(false);
        return false;
      }
    },
    [fetchLinkToken]
  );

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const storedEmail = localStorage.getItem('user_email');
    const storedId = localStorage.getItem('user_id');
    const parsedId = storedId ? parseInt(storedId, 10) : null;
    if (token && storedEmail) {
      api.get('/dashboard')
        .then(() => {
          setUser({ email: storedEmail, id: parsedId });
          checkConnectionStatus(parsedId);
        })
        .catch(() => {
          localStorage.removeItem('access_token');
          localStorage.removeItem('user_email');
          localStorage.removeItem('user_id');
          setUser(null);
          setIsConnected(false);
        });
    }
  }, [checkConnectionStatus]);

  const handleLogin = async (email, password) => {
    const response = await authAPI.login(email, password);
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('user_email', email);
    localStorage.setItem('user_id', response.user_id);
    setUser({ email, id: response.user_id });

    await checkConnectionStatus(response.user_id);
  };

  const handleRegister = async (email, password) => {
    try {
      await authAPI.register(email, password);
      await handleLogin(email, password);
    } catch (error) {
      throw error;
    }
  };

  const handlePlaidSuccess = async (publicToken) => {
    try {
      await plaidAPI.exchangeToken(publicToken);
      setIsConnected(true);
      setLinkToken(null);
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem('plaid_link_token');
      }
      setLinkError(null);
    } catch (error) {
      console.error('Plaid connection error:', error);
      setLinkError(error.response?.data?.detail || 'Unable to complete Plaid Link. Please try again.');
    }
  };

  const handleRefreshLinkToken = () => {
    if (linkLoading) {
      return;
    }
    const confirmed = window.confirm(
      'Refreshing the Plaid link will trigger a new data import and may incur usage charges. Continue?'
    );
    if (confirmed) {
      fetchLinkToken(user?.id, { force: true });
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_email');
    localStorage.removeItem('user_id');
    setUser(null);
    setLinkToken(null);
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem('plaid_link_token');
    }
    setIsConnected(false);
    setLinkError(null);
    setLinkLoading(false);
  };

  if (!user) {
    return (
      <Router>
        <div className="min-h-screen bg-[#E0E3F3] flex flex-col justify-center py-12 sm:px-6 lg:px-8">
          <div className="sm:mx-auto sm:w-full sm:max-w-md">
            <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-[#1F2330]">
              Welcome to Lucentia
            </h2>
            <p className="mt-2 text-center text-sm text-[#505869]">
              Your personal financial insights platform
            </p>
          </div>

          <Routes>
            <Route path="/login" element={<Login onLogin={handleLogin} />} />
            <Route path="/register" element={<Register onRegister={handleRegister} />} />
            <Route path="*" element={<Navigate to="/login" />} />
          </Routes>
        </div>
      </Router>
    );
  }

  return (
    <Router>
      <div className="min-h-screen bg-[#E0E3F3]">
        <Navigation user={user} onLogout={handleLogout} />
        
        <main className="py-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            {!isConnected && (
              <div className="mb-6 rounded-lg border border-dashed border-[#C8CCE5] bg-white/80 p-6">
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="text-sm font-semibold text-[#1F2330]">
                      Connect a bank account to unlock live balances and transactions.
                    </p>
                    <p className="text-xs text-[#6F7385] mt-1">
                      You can continue exploring with demo data, or link Plaid whenever you&apos;re ready.
                    </p>
                    {linkError && (
                      <p className="mt-2 text-xs text-red-600">
                        {linkError}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
                    {linkToken ? (
                      <PlaidLink
                        token={linkToken}
                        onSuccess={handlePlaidSuccess}
                        receivedRedirectUri={isOauthRedirect ? window.location.href : undefined}
                        className="btn-primary w-full sm:w-auto flex justify-center disabled:opacity-70"
                        style={{
                          backgroundColor: '#4F46E5',
                          color: '#FFFFFF',
                          borderRadius: '0.5rem',
                        }}
                      >
                        Connect Bank Account
                      </PlaidLink>
                    ) : (
                      <button
                        type="button"
                        onClick={() => fetchLinkToken(user?.id)}
                        disabled={linkLoading}
                        className="btn-primary w-full sm:w-auto disabled:opacity-70"
                      >
                        {linkLoading ? 'Preparing Plaid Link...' : 'Generate Plaid Link'}
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={handleRefreshLinkToken}
                      disabled={linkLoading}
                      className="btn-secondary w-full sm:w-auto disabled:opacity-70"
                    >
                      Refresh Token
                    </button>
                  </div>
                </div>
              </div>
            )}
            <Routes>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/insights" element={<Insights />} />
              <Route path="/transactions" element={<Transactions />} />
              <Route path="/accounts" element={<Accounts />} />
              <Route path="*" element={<Navigate to="/dashboard" />} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
}

export default App;
