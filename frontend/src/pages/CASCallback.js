import React, { useEffect, useState, useContext } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import AuthContext from '../context/AuthContext';

const CASCallback = () => {
  const [error, setError] = useState('');
  const location = useLocation();
  const navigate = useNavigate();
  const { handleCASCallback } = useContext(AuthContext);

  useEffect(() => {
    const processCallback = async () => {
      try {
        // Get the ticket from the URL query parameters
        const params = new URLSearchParams(location.search);
        const ticket = params.get('ticket');
        const callbackUrl = params.get('callback_url') || '/';
        const needsOnboarding = params.get('needs_onboarding') === 'true';
        const casSuccess = params.get('cas_success') === 'true';

        console.log('CASCallback params:', {
          ticket: ticket ? 'present' : 'missing',
          callbackUrl,
          needsOnboarding,
          casSuccess
        });

        // If ticket is present, we're coming directly from CAS
        // If no ticket but needs_onboarding is set, we're coming from backend redirect
        // If cas_success is true, we're coming from backend redirect
        if (!ticket && !casSuccess) {
          console.error('No CAS ticket or success parameters found in URL');
          setError('Authentication information missing. Please try logging in again.');
          return;
        }

        // Process the CAS callback
        console.log('Processing CAS callback...');
        const result = await handleCASCallback(ticket, params);
        console.log('CAS callback result:', result);
        
        if (result && result.success) {
          console.log('CAS authentication successful');
          // Check if user needs to complete onboarding
          if (result.needs_onboarding) {
            console.log('User needs onboarding, navigating to /onboarding');
            navigate('/onboarding');
          } else {
            // Navigate to the callback URL or home page
            console.log(`Navigating to ${result.callback_url || callbackUrl || '/'}`);
            navigate(result.callback_url || callbackUrl || '/');
          }
        } else {
          console.error('CAS callback unsuccessful:', result);
          setError(result?.message || 'CAS authentication failed');
        }
      } catch (err) {
        console.error('Error processing CAS callback:', err);
        setError('An error occurred during CAS authentication. Please try again.');
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