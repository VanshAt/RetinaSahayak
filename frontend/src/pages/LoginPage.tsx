import React, { useState } from 'react';
import { Eye, Shield, Stethoscope, ArrowRight, Activity, Cpu } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleManualLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const success = await login(email, password);
    if (!success) {
      setError('Invalid login credentials. Please check your email and password.');
    }
    setLoading(false);
  };

  const handleQuickLogin = async (roleEmail: string, rolePass: string) => {
    setLoading(true);
    setError(null);
    const success = await login(roleEmail, rolePass);
    if (!success) {
      setError('Failed to log in with demo account. Ensure backend server is running.');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background Glows */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-xl shadow-blue-500/25 mb-4">
          <Eye className="w-8 h-8" />
        </div>
        <h2 className="text-3xl font-extrabold text-white tracking-tight">RetinaSahayak</h2>
        <p className="mt-2 text-sm text-slate-400">
          Explainable AI for Diabetic Retinopathy Screening in Rural India
        </p>
        <div className="mt-2 inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-900/60 text-blue-300 border border-blue-700/50">
          <Cpu className="w-3.5 h-3.5" />
          Smart India Hackathon 2026 • SIH26038
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-4">
        <div className="bg-slate-800/80 backdrop-blur-md py-8 px-6 shadow-2xl rounded-2xl border border-slate-700 sm:px-10">
          {/* Quick Demo Switcher Cards */}
          <div className="mb-6">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 text-center">
              1-Click Demo Personas
            </label>
            <div className="grid grid-cols-1 gap-2.5">
              <button
                type="button"
                onClick={() => handleQuickLogin('worker.ramnagar@retinasahayak.in', 'WorkerDemo123!')}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-700/50 hover:bg-slate-700 text-left border border-slate-600/60 hover:border-blue-500/50 transition group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">
                    <Activity className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-white group-hover:text-blue-300">
                      PHC Health Worker
                    </div>
                    <div className="text-xs text-slate-400">Ramnagar PHC, Varanasi</div>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-blue-400 group-hover:translate-x-0.5 transition" />
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('dr.verma@retinasahayak.in', 'DoctorDemo123!')}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-700/50 hover:bg-slate-700 text-left border border-slate-600/60 hover:border-indigo-500/50 transition group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold">
                    <Stethoscope className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-white group-hover:text-indigo-300">
                      Tele-Ophthalmologist
                    </div>
                    <div className="text-xs text-slate-400">District Eye Hospital Cockpit</div>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-400 group-hover:translate-x-0.5 transition" />
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('admin@retinasahayak.in', 'AdminDemo123!')}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-700/50 hover:bg-slate-700 text-left border border-slate-600/60 hover:border-amber-500/50 transition group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold">
                    <Shield className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-white group-hover:text-amber-300">
                      District Public Health Admin
                    </div>
                    <div className="text-xs text-slate-400">Analytics & Audit Inspection</div>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-amber-400 group-hover:translate-x-0.5 transition" />
              </button>
            </div>
          </div>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-700" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-slate-800 px-3 text-slate-500 font-semibold tracking-wider">
                Or Sign In With Password
              </span>
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
              {error}
            </div>
          )}

          <form onSubmit={handleManualLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300">Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@retinasahayak.in"
                className="mt-1 block w-full px-3 py-2 bg-slate-900/60 border border-slate-700 rounded-lg text-white text-sm focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-slate-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="mt-1 block w-full px-3 py-2 bg-slate-900/60 border border-slate-700 rounded-lg text-white text-sm focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-slate-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2.5 px-4 rounded-lg shadow-sm text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 focus:outline-hidden focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition"
            >
              {loading ? 'Authenticating...' : 'Sign In to Portal'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
