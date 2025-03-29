import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

// This component now automatically redirects to the Experiences page
// and passes a query parameter to open the add experience modal
const AddExperience = () => {
  const navigate = useNavigate();
  
  useEffect(() => {
    // Redirect to experiences page with a query parameter to open the modal
    navigate('/experiences?openAddModal=true');
  }, [navigate]);
  
  // This component won't actually render as it immediately redirects
  return (
    <div className="py-6">
      <div className="flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-orange-500"></div>
        <p className="ml-3 text-gray-600">Redirecting to experiences...</p>
      </div>
    </div>
  );
};

export default AddExperience;
