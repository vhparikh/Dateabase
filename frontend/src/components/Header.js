import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  // Check if the current path is active
  const isActive = (path) => {
    return location.pathname === path ? 'text-orange-500 font-semibold' : 'text-gray-600 hover:text-orange-500';
  };

  return (
    <header className="bg-white shadow-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* logo */}
          <div className="flex items-center">
            <Link to="/" className="flex-shrink-0 flex items-center">
              <span className="text-2xl font-bold text-orange-500">DateABase</span>
            </Link>
          </div>

          {/* desktop */}
          <nav className="hidden md:flex space-x-8">
            <Link to="/" className={`px-3 py-2 rounded-md text-sm ${isActive('/')}`}>
              Home
            </Link>
            <Link to="/experiences" className={`px-3 py-2 rounded-md text-sm ${isActive('/experiences')}`}>
              Experiences
            </Link>
            <Link to="/swipe" className={`px-3 py-2 rounded-md text-sm ${isActive('/swipe')}`}>
              Swipe
            </Link>
            <Link to="/matches" className={`px-3 py-2 rounded-md text-sm ${isActive('/matches')}`}>
              Matches
            </Link>
            <Link to="/profile" className={`px-3 py-2 rounded-md text-sm ${isActive('/profile')}`}>
              Profile
            </Link>
          </nav>

          {/* Mobile */}
          <div className="md:hidden">
            <button
              onClick={toggleMenu}
              className="bg-white p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
              aria-expanded={isMenuOpen}
            >
              <span className="sr-only">Open main menu</span>
              <svg
                className="h-6 w-6"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d={isMenuOpen ? 'M6 18L18 6M6 6l12 12' : 'M4 6h16M4 12h16M4 18h16'}
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation  */}
      {isMenuOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
            <Link 
              to="/"
              className={`block px-3 py-2 rounded-md text-base ${isActive('/') ? 'bg-orange-50 text-orange-500' : 'text-gray-600 hover:bg-orange-50 hover:text-orange-500'}`}
              onClick={() => setIsMenuOpen(false)}
            >
              Home
            </Link>
            <Link 
              to="/experiences"
              className={`block px-3 py-2 rounded-md text-base ${isActive('/experiences') ? 'bg-orange-50 text-orange-500' : 'text-gray-600 hover:bg-orange-50 hover:text-orange-500'}`}
              onClick={() => setIsMenuOpen(false)}
            >
              Experiences
            </Link>
            <Link 
              to="/swipe"
              className={`block px-3 py-2 rounded-md text-base ${isActive('/swipe') ? 'bg-orange-50 text-orange-500' : 'text-gray-600 hover:bg-orange-50 hover:text-orange-500'}`}
              onClick={() => setIsMenuOpen(false)}
            >
              Swipe
            </Link>
            <Link 
              to="/matches"
              className={`block px-3 py-2 rounded-md text-base ${isActive('/matches') ? 'bg-orange-50 text-orange-500' : 'text-gray-600 hover:bg-orange-50 hover:text-orange-500'}`}
              onClick={() => setIsMenuOpen(false)}
            >
              Matches
            </Link>
            <Link 
              to="/profile"
              className={`block px-3 py-2 rounded-md text-base ${isActive('/profile') ? 'bg-orange-50 text-orange-500' : 'text-gray-600 hover:bg-orange-50 hover:text-orange-500'}`}
              onClick={() => setIsMenuOpen(false)}
            >
              Profile
            </Link>
          </div>
        </div>
      )}
    </header>
  );
};

export default Header; 