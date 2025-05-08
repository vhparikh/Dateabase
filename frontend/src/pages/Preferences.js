import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthContext from '../context/AuthContext';
import { API_URL } from '../config';
import axios from 'axios';
import { useCSRFToken } from '../App';

const Preferences = () => {
  const navigate = useNavigate();
  const { user, setUser } = useContext(AuthContext);
  
  const [loading, setLoading] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState('');

  const csrfToken = useCSRFToken();
  
  // Parse JSON strings from user object
  const parseUserJson = (jsonString, defaultValue) => {
    if (!jsonString) return defaultValue;
    try {
      return JSON.parse(jsonString);
    } catch (e) {
      // console.error("Error parsing JSON:", e);
      return defaultValue;
    }
  };
  
  // Define experience types available
  const experienceTypes = [
    "Dining",
    "Coffee",
    "Hiking",
    "Movies",
    "Museum",
    "Study",
    "Shopping",
    "Workout",
    "Concert",
    "Campus Tour"
  ];
  
  // Form state
  const [formData, setFormData] = useState({
    experience_type_prefs: parseUserJson(user?.experience_type_prefs, {})
  });
  
  useEffect(() => {
    // When user data changes, update form data
    if (user) {
      setFormData({
        experience_type_prefs: parseUserJson(user.experience_type_prefs, {})
      });
    }
  }, [user]);
  
  const handleCheckboxChange = (type, value) => {
    setFormData(prev => {
      // For experience type preferences
      if (type === 'experience_type_prefs') {
        const updatedExpPrefs = { ...prev.experience_type_prefs };
        updatedExpPrefs[value] = !updatedExpPrefs[value];
        return {
          ...prev,
          experience_type_prefs: updatedExpPrefs
        };
      }
      return prev;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSaveSuccess(false);
    
    try {
      // Only send experience_type_prefs to the API
      const apiFormData = {
        // Keep existing user preferences for other fields
        gender_pref: user?.gender_pref || '',
        class_year_min_pref: user?.class_year_min_pref || 2023,
        class_year_max_pref: user?.class_year_max_pref || 2027,
        interests_prefs: user?.interests_prefs || '{}',
        // Update experience type preferences
        experience_type_prefs: JSON.stringify(formData.experience_type_prefs)
      };
      
      const response = await axios.put(`${API_URL}/api/me`, apiFormData, { withCredentials: true, 
        headers: {
          'Content-Type': 'application/json',
          'X-CsrfToken': csrfToken
        },
      });
      
      if (response.status === 200) {
        const updatedUserData = response.data;
        // Update the user in context
        setUser(updatedUserData);
        setSaveSuccess(true);
        // Redirect to profile after a short delay
        setTimeout(() => {
          navigate('/profile');
        }, 1200);
      } else {
        setError('Failed to update preferences');
      }
    } catch (err) {
      // console.error('Error saving preferences:', err);
      setError('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Experience Preferences</h1>
          <p className="text-gray-600 mt-1">
            Select the types of experiences you're interested in
          </p>
        </div>
        <button
          onClick={() => navigate('/profile')}
          className="text-orange-600 hover:text-orange-500 font-medium"
        >
          Back to Profile
        </button>
      </div>
      
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}
      
      {saveSuccess && (
        <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
          Preferences saved successfully!
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-6">
        {/* Experience Type Preferences*/}
        <div>
          <h2 className="text-xl font-semibold mb-3 text-gray-800">Experience Type Preferences</h2>
          <p className="text-gray-500 mb-3 text-sm">Select the types of experiences you're interested in</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {experienceTypes.map((type) => (
              <label key={type} className="flex items-center">
                <input
                  type="checkbox"
                  checked={!!formData.experience_type_prefs[type]}
                  onChange={() => handleCheckboxChange('experience_type_prefs', type)}
                  className="h-4 w-4 text-orange-500 focus:ring-orange-400 rounded"
                />
                <span className="ml-2 text-gray-700">{type}</span>
              </label>
            ))}
          </div>
        </div>
        
        {/* Submit Button */}
        <div className="flex justify-end mt-6">
          <button
            type="submit"
            disabled={loading}
            className={`px-6 py-2 rounded-full text-white font-medium transition-all ${
              loading 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-gradient-to-r from-orange-500 to-orange-600 hover:shadow-md'
            }`}
          >
            {loading ? 'Saving...' : 'Save Preferences'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default Preferences; 