import React from 'react';
import { Link } from 'react-router-dom';

const AddExperience = () => {
  return (
    <div className="py-6">
      <div className="flex items-center mb-6">
        <Link to="/experiences" className="text-orange-500 hover:text-orange-600 mr-2">
          ← Back to Experiences
        </Link>
        <h1 className="text-2xl font-bold">Add New Experience</h1>
      </div>
      
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600">Adding experiences is available in demo mode.</p>
        <p className="mt-2 text-gray-600">You are automatically logged in as the demo user.</p>
      </div>
    </div>
  );
};

export default AddExperience;
