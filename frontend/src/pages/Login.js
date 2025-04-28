import React, { useState, useContext } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import AuthContext from '../context/AuthContext';

const Login = () => {
  const [error, setError] = useState('');
  const [casLoading, setCasLoading] = useState(false);
  const [showPrivacyModal, setShowPrivacyModal] = useState(false);
  
  const { loginWithCAS } = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get the callback URL from state or default to home
  const callbackUrl = location.state?.from?.pathname || '/';

  // Initiate Princeton CAS login
  const handleCASLogin = async () => {
    setCasLoading(true);
    setError('');
    
    try {
      console.log('Initiating Princeton CAS login');
      const success = await loginWithCAS(callbackUrl);
      
      if (!success) {
        setError('Failed to initiate CAS login. Please try again.');
      }
      // No need to navigate - the loginWithCAS function redirects to CAS
    } catch (err) {
      console.error('CAS login error:', err);
      setError(`Error: ${err.message}`);
    } finally {
      setCasLoading(false);
    }
  };
  
  // Toggle privacy policy modal
  const togglePrivacyModal = () => {
    setShowPrivacyModal(!showPrivacyModal);
  };
  
  // Only Princeton CAS login is available now
  
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
              Sign in with your Princeton account to continue
            </p>
            
            {/* Princeton CAS Login Button */}
            <button
              onClick={handleCASLogin}
              className="w-full px-4 py-3 flex items-center justify-center bg-orange-500 text-white rounded-lg font-medium hover:bg-orange-600 transition-colors"
              disabled={casLoading}
            >
              {casLoading ? (
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
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  Sign in with Princeton CAS
                </span>
              )}
            </button>
            
            {/* Only Princeton CAS login is available */}
            
            <div className="text-center mt-4">
              <button 
                onClick={togglePrivacyModal}
                className="text-orange-600 hover:text-orange-500 font-medium"
              >
                Privacy Policy
              </button>
            </div>
          </div>
        </div>
        
        <div className="text-center mt-8">
          <p className="text-gray-500 text-sm">
            &copy; {new Date().getFullYear()} DateABase · Princeton's Experience-Based Dating
          </p>
        </div>
      </div>

      {/* Privacy Policy Modal */}
      {showPrivacyModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 relative">
            <button 
              onClick={togglePrivacyModal}
              className="absolute top-4 right-4 text-gray-500 hover:text-gray-700"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            
            <h3 className="text-xl font-bold mb-4 text-gray-800">Privacy Policy</h3>
            
            <div className="text-gray-700">
              <p className="mb-4">
                By enrolling in this application, you acknowledge that you are a Princeton undergraduate student. 
                Other members of the Princeton community are not permitted to use this application, to ensure a safe environment. 
                Violations of this policy may result in serious consequences with Princeton administration.
              </p>
            </div>
            
            <button
              onClick={togglePrivacyModal}
              className="mt-6 w-full px-4 py-2 bg-orange-500 text-white rounded-lg font-medium hover:bg-orange-600 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Login; 