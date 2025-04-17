import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthContext from '../context/AuthContext';
import { API_URL } from '../config';

const Preferences = () => {
  const navigate = useNavigate();
  const { user, setUser } = useContext(AuthContext);
  
  const [loading, setLoading] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState('');
  
  // Parse JSON strings from user object or use defaults
  const parseUserJson = (jsonString, defaultValue) => {
    if (!jsonString) return defaultValue;
    try {
      return JSON.parse(jsonString);
    } catch (e) {
      console.error("Error parsing JSON:", e);
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
    gender_pref: user?.gender_pref || '',
    experience_type_prefs: parseUserJson(user?.experience_type_prefs, {}),
    class_year_min_pref: user?.class_year_min_pref || 2023,
    class_year_max_pref: user?.class_year_max_pref || 2027,
    interests_prefs: parseUserJson(user?.interests_prefs, {})
  });
  
  // Interest options
  const interestOptions = [
    "Photography",
    "Reading",
    "Writing",
    "Music",
    "Art",
    "Gaming",
    "Sports",
    "Cooking",
    "Travel",
    "Technology",
    "Fashion",
    "Dancing",
    "Movies & TV",
    "Nature",
    "Fitness"
  ];

  useEffect(() => {
    // When user data changes, update form data
    if (user) {
      setFormData({
        gender_pref: user.gender_pref || '',
        experience_type_prefs: parseUserJson(user.experience_type_prefs, {}),
        class_year_min_pref: user.class_year_min_pref || 2023,
        class_year_max_pref: user.class_year_max_pref || 2027,
        interests_prefs: parseUserJson(user.interests_prefs, {})
      });
    }
  }, [user]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
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
      // For interest preferences
      else if (type === 'interests_prefs') {
        const updatedInterestsPrefs = { ...prev.interests_prefs };
        updatedInterestsPrefs[value] = !updatedInterestsPrefs[value];
        return {
          ...prev,
          interests_prefs: updatedInterestsPrefs
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
      // Convert objects to JSON strings for API
      const apiFormData = {
        gender_pref: formData.gender_pref,
        experience_type_prefs: JSON.stringify(formData.experience_type_prefs),
        class_year_min_pref: parseInt(formData.class_year_min_pref, 10),
        class_year_max_pref: parseInt(formData.class_year_max_pref, 10),
        interests_prefs: JSON.stringify(formData.interests_prefs)
      };
      
      const response = await fetch(`${API_URL}/api/me`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(apiFormData)
      });
      
      if (response.ok) {
        const updatedUserData = await response.json();
        // Update the user in context
        setUser(updatedUserData);
        setSaveSuccess(true);
        // Redirect to profile after a short delay
        setTimeout(() => {
          navigate('/profile');
        }, 1200);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to update preferences');
      }
    } catch (err) {
      console.error('Error saving preferences:', err);
      setError('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dating Preferences</h1>
          <p className="text-gray-600 mt-1">
            Customize your matching preferences to find better matches
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
        {/* Gender Preference */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-3 text-gray-800">Gender Preference</h2>
          <div className="flex flex-wrap gap-4">
            {['Male', 'Female', 'Everyone'].map((gender) => (
              <label key={gender} className="flex items-center">
                <input
                  type="radio"
                  name="gender_pref"
                  value={gender}
                  checked={formData.gender_pref === gender}
                  onChange={handleChange}
                  className="h-4 w-4 text-orange-500 focus:ring-orange-400"
                />
                <span className="ml-2 text-gray-700">{gender}</span>
              </label>
            ))}
          </div>
        </div>
        
        {/* Experience Type Preferences */}
        <div className="mb-6">
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
        
        {/* Class Year Preferences */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-3 text-gray-800">Class Year Range</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-700 mb-2">Minimum Class Year</label>
              <select
                name="class_year_min_pref"
                value={formData.class_year_min_pref}
                onChange={handleChange}
                className="w-full p-2 border border-gray-300 rounded focus:ring-orange-500 focus:border-orange-500"
              >
                {Array.from({ length: 9 }, (_, i) => 2020 + i).map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-gray-700 mb-2">Maximum Class Year</label>
              <select
                name="class_year_max_pref"
                value={formData.class_year_max_pref}
                onChange={handleChange}
                className="w-full p-2 border border-gray-300 rounded focus:ring-orange-500 focus:border-orange-500"
              >
                {Array.from({ length: 9 }, (_, i) => 2020 + i).map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
        
        {/* Interests Preferences */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-3 text-gray-800">Interest Preferences</h2>
          <p className="text-gray-500 mb-3 text-sm">Select interests you would like to match on</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {interestOptions.map((interest) => (
              <label key={interest} className="flex items-center">
                <input
                  type="checkbox"
                  checked={!!formData.interests_prefs[interest]}
                  onChange={() => handleCheckboxChange('interests_prefs', interest)}
                  className="h-4 w-4 text-orange-500 focus:ring-orange-400 rounded"
                />
                <span className="ml-2 text-gray-700">{interest}</span>
              </label>
            ))}
          </div>
        </div>
        
        {/* Submit Button */}
        <div className="flex justify-end">
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