import React from 'react';
import Header from './Header';

const MainLayout = ({ children }) => {
    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            <Header />
            <main className="flex-1">
                {children}
            </main>
        </div>
    );
};

export default MainLayout;
