import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User } from '../types';
import { apiRequest, getStoredToken, setStoredToken } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, role?: string) => Promise<boolean>;
  logout: () => void;
  switchDemoRole: (role: 'PHC_WORKER' | 'OPHTHALMOLOGIST' | 'ADMIN') => Promise<void>;
}

const DEMO_CREDENTIALS: Record<string, { email: string; pass: string }> = {
  ADMIN: { email: 'admin@retinasahayak.in', pass: 'AdminDemo123!' },
  PHC_WORKER: { email: 'worker.ramnagar@retinasahayak.in', pass: 'WorkerDemo123!' },
  OPHTHALMOLOGIST: { email: 'dr.verma@retinasahayak.in', pass: 'DoctorDemo123!' },
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(getStoredToken());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      const stored = getStoredToken();
      if (!stored) {
        setLoading(false);
        return;
      }
      const res = await apiRequest<User>('/auth/me');
      if (res.success && res.data) {
        setUser(res.data);
      } else {
        setStoredToken(null);
        setToken(null);
        setUser(null);
      }
      setLoading(false);
    }
    loadUser();
  }, []);

  const login = async (email: string, passwordInput?: string) => {
    setLoading(true);
    let pass = passwordInput;
    if (!pass) {
      if (email.includes('admin')) pass = 'AdminDemo123!';
      else if (email.includes('worker')) pass = 'WorkerDemo123!';
      else pass = 'DoctorDemo123!';
    }

    const res = await apiRequest<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password: pass }),
    });

    if (res.success && res.data) {
      setStoredToken(res.data.access_token);
      setToken(res.data.access_token);
      setUser(res.data.user);
      setLoading(false);
      return true;
    }

    setLoading(false);
    return false;
  };

  const logout = () => {
    setStoredToken(null);
    setToken(null);
    setUser(null);
  };

  const switchDemoRole = async (role: 'PHC_WORKER' | 'OPHTHALMOLOGIST' | 'ADMIN') => {
    const creds = DEMO_CREDENTIALS[role];
    if (creds) {
      await login(creds.email, creds.pass);
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, switchDemoRole }}>
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
