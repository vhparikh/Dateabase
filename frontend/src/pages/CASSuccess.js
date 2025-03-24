import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const CASSuccess = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Always redirect to home page since we're using demo user auth
    navigate('/');
  }, [navigate]);
  
  return (
    <div className="flex items-center justify-center min-h-screen bg-white-gradient px-4 py-12">
      <div className="w-full max-w-md z-10 text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-orange-500 mx-auto mb-4"></div>
        <p className="text-gray-700 text-lg font-medium">Redirecting you to home page...</p>
      </div>
    </div>
  );
};

export default CASSuccess; 