import { Link, useLocation } from 'react-router-dom';
import { Activity } from 'lucide-react';

export default function Navbar() {
  const location = useLocation();

  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center">
                <Activity className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-xl tracking-tight text-slate-900">UrbanFlow</span>
            </Link>
          </div>
          <div className="flex items-center gap-6">
            <Link 
              to="/" 
              className={`text-sm font-medium ${location.pathname === '/' ? 'text-emerald-600' : 'text-slate-500 hover:text-slate-900'}`}
            >
              Inicio
            </Link>
            <Link 
              to="/dashboard" 
              className={`text-sm font-medium ${location.pathname === '/dashboard' ? 'text-emerald-600' : 'text-slate-500 hover:text-slate-900'}`}
            >
              Dashboard
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}