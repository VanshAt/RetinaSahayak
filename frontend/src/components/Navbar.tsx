import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Eye, Shield, UserCheck, Stethoscope, LogOut } from 'lucide-react';

interface NavbarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, onSelectTab }) => {
  const { user, logout, switchDemoRole } = useAuth();

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          {/* Logo & Project Title */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-700 to-indigo-900 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
              <Eye className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg text-slate-900 tracking-tight">RetinaSahayak</span>
                <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                  SIH26038
                </span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">
                Explainable AI for Diabetic Retinopathy Screening in Rural India
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          {user && (
            <div className="hidden md:flex items-center space-x-1 bg-slate-100/80 p-1 rounded-xl border border-slate-200">
              <button
                onClick={() => onSelectTab('worker')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  currentTab === 'worker'
                    ? 'bg-white text-blue-700 shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <UserCheck className="w-4 h-4" />
                PHC Worker
              </button>

              <button
                onClick={() => onSelectTab('doctor')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  currentTab === 'doctor'
                    ? 'bg-white text-blue-700 shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Stethoscope className="w-4 h-4" />
                Doctor Cockpit
              </button>

              <button
                onClick={() => onSelectTab('admin')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  currentTab === 'admin'
                    ? 'bg-white text-blue-700 shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Shield className="w-4 h-4" />
                Analytics & Logs
              </button>
            </div>
          )}

          {/* Role Switcher & User Profile */}
          <div className="flex items-center gap-3">
            {user ? (
              <div className="flex items-center gap-3">
                {/* 1-Click Role Switcher */}
                <div className="hidden lg:flex items-center gap-1.5 text-xs text-slate-600 border border-slate-200 rounded-lg p-1 bg-slate-50">
                  <span className="font-semibold text-slate-400 pl-1">Role:</span>
                  <button
                    onClick={() => { switchDemoRole('PHC_WORKER'); onSelectTab('worker'); }}
                    className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
                      user.role === 'PHC_WORKER' ? 'bg-blue-600 text-white shadow-xs' : 'hover:bg-slate-200 text-slate-700'
                    }`}
                  >
                    Worker
                  </button>
                  <button
                    onClick={() => { switchDemoRole('OPHTHALMOLOGIST'); onSelectTab('doctor'); }}
                    className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
                      user.role === 'OPHTHALMOLOGIST' ? 'bg-blue-600 text-white shadow-xs' : 'hover:bg-slate-200 text-slate-700'
                    }`}
                  >
                    Doctor
                  </button>
                  <button
                    onClick={() => { switchDemoRole('ADMIN'); onSelectTab('admin'); }}
                    className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
                      user.role === 'ADMIN' ? 'bg-blue-600 text-white shadow-xs' : 'hover:bg-slate-200 text-slate-700'
                    }`}
                  >
                    Admin
                  </button>
                </div>

                <div className="text-right hidden sm:block">
                  <div className="text-xs font-bold text-slate-800">{user.email.split('@')[0]}</div>
                  <div className="text-[10px] text-slate-500 font-medium">{user.role}</div>
                </div>

                <button
                  onClick={logout}
                  title="Logout"
                  className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </header>
  );
};
