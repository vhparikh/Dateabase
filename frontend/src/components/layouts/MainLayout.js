import React, { useContext, Suspense, useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import AuthContext from '../../context/AuthContext';

const MainLayout = () => {
  const location = useLocation();
  const { loading } = useContext(AuthContext);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  const isActive = (path) => {
    if (path === '/' && (location.pathname === '/' || location.pathname === '/swipe')) {
      return true;
    }
    return location.pathname.startsWith(path);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-orange-50 to-orange-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-orange-500 mx-auto mb-4"></div>
          <p className="text-orange-800 text-lg font-medium">Loading DateABase...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-br from-orange-50 via-white to-orange-50">
      <header className="bg-white/80 backdrop-blur-md shadow-sm sticky top-0 z-50 border-b border-orange-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="flex items-center">
                <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-orange-500 to-orange-600">
                  DateABase
                </span>
              </Link>
            </div>
            
            {/* Desktop navigation */}
            <nav className="hidden md:flex items-center space-x-1">
              <Link 
                to="/swipe" 
                className={`px-3 py-2 rounded-full text-sm font-medium transition-all ${
                  isActive('/swipe') 
                    ? 'text-white bg-gradient-to-r from-orange-500 to-orange-600 shadow-md' 
                    : 'text-gray-700 hover:bg-orange-50'
                }`}
              >
                Swipe
              </Link>
              <Link 
                to="/experiences" 
                className={`px-3 py-2 rounded-full text-sm font-medium transition-all ${
                  isActive('/experiences') 
                    ? 'text-white bg-gradient-to-r from-orange-500 to-orange-600 shadow-md' 
                    : 'text-gray-700 hover:bg-orange-50'
                }`}
              >
                Experiences
              </Link>
              <Link 
                to="/matches" 
                className={`px-3 py-2 rounded-full text-sm font-medium transition-all ${
                  isActive('/matches') 
                    ? 'text-white bg-gradient-to-r from-orange-500 to-orange-600 shadow-md' 
                    : 'text-gray-700 hover:bg-orange-50'
                }`}
              >
                Matches
              </Link>
              <Link 
                to="/profile" 
                className={`ml-2 p-2 rounded-full transition-all ${
                  isActive('/profile') 
                    ? 'bg-gradient-to-r from-orange-500 to-orange-600 shadow-md' 
                    : 'text-gray-700 hover:bg-orange-50'
                }`}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className={`h-5 w-5 ${isActive('/profile') ? 'text-white' : 'text-gray-700'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </Link>
              <Link 
                to="/help" 
                className={`ml-2 p-2 rounded-full transition-all ${
                  isActive('/help') 
                    ? 'bg-gradient-to-r from-orange-500 to-orange-600 shadow-md' 
                    : 'text-gray-700 hover:bg-orange-50'
                }`}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className={`h-5 w-5 ${isActive('/help') ? 'text-white' : 'text-gray-700'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </Link>
            </nav>
            
            {/* Mobile menu button */}
            <div className="flex items-center md:hidden">
              <button
                type="button"
                className="p-2 rounded-md text-gray-700 hover:bg-orange-50"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
        
        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-white border-t border-orange-100 shadow-lg animate-scale-in">
            <div className="px-2 pt-2 pb-3 space-y-1">
              <Link
                to="/swipe"
                className={`block px-3 py-2 rounded-lg text-base font-medium ${
                  isActive('/swipe') 
                    ? 'text-white bg-gradient-to-r from-orange-500 to-orange-600' 
                    : 'text-gray-700 hover:bg-orange-50'
                }`}
                onClick={() => setMobileMenuOpen(false)}
              >
                Swipe
              </Link>
              <Link
                to="/experiences"
                className={`block px-3 py-2 rounded-lg text-base font-medium ${
                  isActive('/experiences') 
                    ? 'text-white bg-gradient-to-r from-orange-500 to-orange-600' 
                    : 'text-gray-700 hover:bg-orange-50'
                }`}
                onClick={() => setMobileMenuOpen(false)}
              >
                Experiences
              </Link>
              <Link
                to="/matches"
                className={`block px-3 py-2 rounded-lg text-base font-medium ${
                  isActive('/matches') 
                    ? 'text-white bg-gradient-to-r from-orange-500 to-orange-600' 
                    : 'text-gray-700 hover:bg-orange-50'
                }`}
                onClick={() => setMobileMenuOpen(false)}
              >
                Matches
              </Link>
              <Link
                to="/profile"
                className={`block px-3 py-2 rounded-lg text-base font-medium ${
                  isActive('/profile') 
                    ? 'text-white bg-gradient-to-r from-orange-500 to-orange-600' 
                    : 'text-gray-700 hover:bg-orange-50'
                }`}
                onClick={() => setMobileMenuOpen(false)}
              >
                Profile
              </Link>
              <Link
                to="/help"
                className={`block px-3 py-2 rounded-lg text-base font-medium ${
                  isActive('/help') 
                    ? 'text-white bg-gradient-to-r from-orange-500 to-orange-600' 
                    : 'text-gray-700 hover:bg-orange-50'
                }`}
                onClick={() => setMobileMenuOpen(false)}
              >
                Help
              </Link>
            </div>
          </div>
        )}
      </header>
      
      <main className="flex-grow">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 w-full">
          <Suspense fallback={
            <div className="flex items-center justify-center min-h-[60vh]">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-orange-500 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading...</p>
              </div>
            </div>
          }>
            <Outlet />
          </Suspense>
        </div>
      </main>
      
      <footer className="bg-white/80 backdrop-blur-md border-t border-orange-100 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-gray-500 text-sm">
            &copy; {new Date().getFullYear()} DateABase · Made with 🧡 · <Link to="/help" className="text-orange-500 hover:text-orange-600">Help & Guide</Link>
          </p>
        </div>
      </footer>
    </div>
  );
};

export default MainLayout; 