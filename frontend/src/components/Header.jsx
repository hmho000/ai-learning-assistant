import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { User, LogOut, BookOpen, ChevronDown } from 'lucide-react';
import { fetchMe } from '../api';

const Header = () => {
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    useEffect(() => {
        const loadUser = async () => {
            try {
                const userData = await fetchMe();
                setUser(userData);
            } catch (err) {
                console.error("Failed to fetch user info", err);
                // If fetching user fails, token might be invalid
                localStorage.removeItem('token');
                navigate('/login');
            }
        };
        loadUser();
    }, [navigate]);

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };

    return (
        <header className="bg-white border-b border-gray-100 sticky top-0 z-40">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16 items-center">
                    {/* Logo/Home Link */}
                    <Link to="/" className="flex items-center gap-2 group">
                        <div className="bg-indigo-600 p-2 rounded-lg text-white group-hover:bg-indigo-700 transition-colors">
                            <BookOpen size={20} />
                        </div>
                        <span className="text-xl font-bold text-gray-900 tracking-tight">AI Learning Assistant</span>
                    </Link>

                    {/* User Info & Logout */}
                    <div className="relative">
                        <button
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                            className="flex items-center gap-2 p-2 rounded-xl hover:bg-gray-50 transition-colors border border-transparent hover:border-gray-200 group"
                        >
                            <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600">
                                <User size={18} />
                            </div>
                            <div className="hidden sm:block text-left">
                                <p className="text-sm font-medium text-gray-900 leading-none">
                                    {user ? user.username : '加载中...'}
                                </p>
                                {user?.is_guest && (
                                    <p className="text-[10px] text-gray-500 mt-1 uppercase tracking-wider">临时访客</p>
                                )}
                            </div>
                            <ChevronDown size={14} className={`text-gray-400 transition-transform ${isMenuOpen ? 'rotate-180' : ''}`} />
                        </button>

                        {/* Dropdown Menu */}
                        {isMenuOpen && (
                            <>
                                <div
                                    className="fixed inset-0 z-10"
                                    onClick={() => setIsMenuOpen(false)}
                                />
                                <div className="absolute right-0 mt-2 w-48 bg-white rounded-2xl shadow-xl border border-gray-100 py-2 z-20 overflow-hidden transform origin-top-right transition-all">
                                    <div className="px-4 py-2 border-b border-gray-50">
                                        <p className="text-xs text-gray-400">登录身份</p>
                                        <p className="text-sm font-semibold text-gray-900 truncate">{user?.username}</p>
                                    </div>
                                    <button
                                        onClick={handleLogout}
                                        className="w-full flex items-center gap-3 px-4 py-3 text-sm text-red-600 hover:bg-red-50 transition-colors"
                                    >
                                        <LogOut size={16} />
                                        <span>退出登录</span>
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
