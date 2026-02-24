import React from 'react';
import { LayoutGrid, User, BookOpen, CreditCard, Settings, Menu } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';

const navItems = [
    { icon: LayoutGrid, path: '/dashboard' },
    { icon: BookOpen, path: '/courses' },
    { icon: CreditCard, path: '/billing' },
    { icon: Settings, path: '/settings' },
];

const Sidebar = () => {
    const navigate = useNavigate();
    const location = useLocation();

    return (
        <div className="w-[84px] bg-white border-r border-[#eef2f6] flex flex-col items-center py-6 h-screen fixed left-0 top-0 z-50">
            <button onClick={() => navigate('/')} className="mb-10 text-blue-600 hover:text-blue-700">
                <Menu className="w-7 h-7" strokeWidth={2.5} />
            </button>
            <nav className="flex-1 flex flex-col gap-6">
                {navItems.map((item, idx) => {
                    // Treat root and dashboard as active for dashboard icon
                    const isActive = location.pathname === item.path || (item.path === '/dashboard' && location.pathname === '/');
                    return (
                        <button
                            key={idx}
                            onClick={() => navigate(item.path)}
                            className={`p-3.5 rounded-2xl transition-all ${isActive
                                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
                                    : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50'
                                }`}
                        >
                            <item.icon className="w-6 h-6" strokeWidth={isActive ? 2.5 : 2} />
                        </button>
                    );
                })}
            </nav>
        </div>
    );
};

export default Sidebar;
