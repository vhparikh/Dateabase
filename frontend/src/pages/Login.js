import React, { useState, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import AuthContext from '../context/AuthContext';

const Login = () => {
  const [error, setError] = useState('');
  const [demoLoading, setDemoLoading] = useState(false);
  
  const { setAuthTokens, setUser } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleDemoLogin = async () => {
    setDemoLoading(true);
    setError('');
    
    console.log('Demo login initiated');
    
    try {
      // Demo login credentials
      const credentials = {
        username: 'demo_user',
        password: 'demo123'
      };
      
      console.log('Sending demo login request');
      
      // Direct API call without using fetch
      const response = await fetch('http://localhost:5001/api/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(credentials),
        credentials: 'include'
      });
      
      console.log('Response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Login successful');
        
        // Set auth tokens in context and localStorage
        setAuthTokens(data);
        setUser(data);
        localStorage.setItem('authTokens', JSON.stringify(data));
        
        // Navigate to home page
        navigate('/');
      } else {
        const errorData = await response.text();
        console.error('Login failed:', errorData);
        setError('Demo login failed. Please try again.');
      }
    } catch (err) {
      console.error('Demo login error:', err);
      setError(`Error: ${err.message}`);
    } finally {
      setDemoLoading(false);
    }
  };
  
  return (
    <div className="flex items-center justify-center min-h-screen bg-white-gradient px-4 py-12 relative">
      {/* Animated background elements with softer opacity */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute left-1/4 top-1/3 w-64 h-64 bg-orange-200 rounded-full mix-blend-multiply filter blur-xl animate-blob opacity-30"></div>
        <div className="absolute right-1/4 top-1/2 w-72 h-72 bg-orange-300 rounded-full mix-blend-multiply filter blur-xl animate-blob animation-delay-2000 opacity-30"></div>
        <div className="absolute left-1/3 bottom-1/4 w-80 h-80 bg-orange-100 rounded-full mix-blend-multiply filter blur-xl animate-blob animation-delay-4000 opacity-30"></div>
      </div>
      
      <div className="w-full max-w-md z-10">
        <div className="text-center mb-10">
          <h1 className="text-5xl font-bold mb-3 text-gray-800">DateABase</h1>
          <p className="text-gray-600 text-lg">Connect through experiences, not just profiles</p>
        </div>
        
        <div className="bg-white rounded-2xl shadow-md p-8 border border-gray-100">
          <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">Welcome to DateABase</h2>
          
          {error && (
            <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded-md" role="alert">
              <p>{error}</p>
            </div>
          )}
          
          <div className="space-y-4">
            <p className="text-gray-600 text-center mb-4">
              Experience the application with our demo account
            </p>
            
            <button
              onClick={handleDemoLogin}
              className="w-full px-4 py-3 flex items-center justify-center bg-indigo-500 text-white rounded-lg font-medium hover:bg-indigo-600 transition-colors"
              disabled={demoLoading}
            >
              {demoLoading ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Loading...
                </span>
              ) : (
                <span className="flex items-center">
                  <svg className="mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                  Continue as Demo User
                </span>
              )}
            </button>
            
            <div className="text-center mt-4">
              <Link to="/" className="text-orange-600 hover:text-orange-500 font-medium">
                Back to Home
              </Link>
            </div>
          </div>
        </div>
        
        <div className="text-center mt-8">
          <p className="text-gray-500 text-sm">
            &copy; {new Date().getFullYear()} DateABase · Princeton's Experience-Based Dating
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login; 