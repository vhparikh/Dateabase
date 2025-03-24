import React, { useEffect, useState, useContext } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import AuthContext from '../context/AuthContext';

const CASCallback = () => {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const location = useLocation();
  const navigate = useNavigate();
  const { handleCASCallback } = useContext(AuthContext);

  useEffect(() => {
    const processCallback = async () => {
      try {
        // Get the ticket from the URL query parameters
        const params = new URLSearchParams(location.search);
        const ticket = params.get('ticket');

        if (!ticket) {
          setError('No CAS ticket found in the URL');
          setLoading(false);
          return;
        }

        // Process the CAS callback
        const result = await handleCASCallback(ticket);
        
        if (!result.success) {
          setError(result.message || 'CAS authentication failed');
        }
      } catch (err) {
        console.error('Error processing CAS callback:', err);
        setError('An error occurred during CAS authentication');
      } finally {
        setLoading(false);
      }
    };

    processCallback();
  }, [location, handleCASCallback, navigate]);

  // If there's an error, show it and provide a way to return to login
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-white-gradient px-4 py-12">
        <div className="w-full max-w-md z-10">
          <div className="bg-white rounded-2xl shadow-md p-8 border border-gray-100">
            <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">Authentication Error</h2>
            <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded-md" role="alert">
              <p>{error}</p>
            </div>
            <button 
              onClick={() => navigate('/login')} 
              className="w-full px-4 py-2 bg-orange-500 text-white rounded-lg font-medium hover:bg-orange-600 transition-colors"
            >
              Return to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Show loading indicator while processing
  return (
    <div className="flex items-center justify-center min-h-screen bg-white-gradient px-4 py-12">
      <div className="w-full max-w-md z-10 text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-orange-500 mx-auto mb-4"></div>
        <p className="text-gray-700 text-lg font-medium">Authenticating with Princeton CAS...</p>
      </div>
    </div>
  );
};

export default CASCallback; 