import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthContext from '../context/AuthContext';
import { updateUser } from '../services/api';

const EditProfile = () => {
  const { user, setUser } = useContext(AuthContext);
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    interests: {}
  });
  
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  
  // Interest options
  const interestOptions = [
    'Coffee', 'Dining', 'Study', 'Movies', 'Hiking', 'Music',
    'Art', 'Sports', 'Gaming', 'Reading', 'Travel', 'Photography'
  ];
  
  useEffect(() => {
    if (user) {
      // Parse name into first name and last name
      const nameParts = user.name ? user.name.split(' ') : ['', ''];
      const firstName = nameParts[0] || '';
      const lastName = nameParts.length > 1 ? nameParts.slice(1).join(' ') : '';
      
      // Parse interests
      let interestsObj = {};
      try {
        if (user.interests) {
          // Try to parse if it's a JSON string
          interestsObj = JSON.parse(user.interests);
        }
      } catch (e) {
        // If it's not valid JSON, try a different approach
        try {
          // Try to parse as comma-separated values
          const interests = user.interests?.split(',').map(item => item.trim()) || [];
          interests.forEach(interest => {
            interestsObj[interest] = true;
          });
        } catch (err) {
          // If all fails, initialize with empty object
          interestsObj = {};
        }
      }
      
      // Initialize form with current user data
      setFormData({
        firstName,
        lastName,
        interests: interestsObj
      });
    }
  }, [user]);
  
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };
  
  const handleInterestChange = (interest) => {
    setFormData({
      ...formData,
      interests: {
        ...formData.interests,
        [interest]: !formData.interests[interest]
      }
    });
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess(false);
    
    try {
      // Format the data for API
      const name = `${formData.firstName} ${formData.lastName}`.trim();
      
      // Create a clean interests object with only selected interests
      const cleanInterests = {};
      interestOptions.forEach(interest => {
        // Only include interests that are explicitly set to true
        if (formData.interests[interest] === true) {
          cleanInterests[interest] = true;
        }
      });
      
      const interests = JSON.stringify(cleanInterests);
      
      const userData = {
        name,
        interests
      };
      
      // Make API call to update user
      const response = await updateUser(user.id, userData);
      
      if (response.data) {
        // Update AuthContext with new data
        setUser({
          ...user,
          ...response.data
        });
        
        setSuccess(true);
        setTimeout(() => {
          navigate('/profile');
        }, 2000);
      }
    } catch (err) {
      console.error('Error updating profile:', err);
      setError(err.response?.data?.detail || 'An error occurred while updating your profile');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100 py-8">
      <div className="max-w-2xl mx-auto px-4 sm:px-6">
        <div className="bg-white rounded-xl shadow-card p-6 md:p-8">
          <h1 className="text-2xl font-bold text-gray-800 mb-6">Edit Your Profile</h1>
          
          {success && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 text-green-700 rounded-lg">
              Profile updated successfully! Redirecting to profile page...
            </div>
          )}
          
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">
              {error}
            </div>
          )}
          
          <form onSubmit={handleSubmit}>
            <div className="space-y-6">
              {/* Name Section */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-1">
                    First Name
                  </label>
                  <input
                    type="text"
                    id="firstName"
                    name="firstName"
                    value={formData.firstName}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    placeholder="Enter your first name"
                  />
                </div>
                
                <div>
                  <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-1">
                    Last Name
                  </label>
                  <input
                    type="text"
                    id="lastName"
                    name="lastName"
                    value={formData.lastName}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    placeholder="Enter your last name"
                  />
                </div>
              </div>
              
              {/* Interests */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Interests
                </label>
                <p className="text-sm text-gray-500 mb-3">Select all that apply</p>
                
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {interestOptions.map(interest => (
                    <div 
                      key={interest} 
                      onClick={() => handleInterestChange(interest)}
                      className={`px-4 py-3 rounded-lg border cursor-pointer transition-colors ${formData.interests[interest] 
                        ? 'bg-orange-100 border-orange-300 text-orange-800' 
                        : 'bg-white border-gray-200 text-gray-700 hover:bg-orange-50'}`}
                    >
                      <div className="flex items-center">
                        <input 
                          type="checkbox" 
                          checked={formData.interests[interest] || false}
                          onChange={() => {}} // Controlled by the div onClick
                          className="h-4 w-4 text-orange-600 rounded"
                        />
                        <span className="ml-2">{interest}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Submit Button */}
              <div className="flex items-center justify-end space-x-3 mt-8">
                <button
                  type="button"
                  onClick={() => navigate('/profile')}
                  className="px-5 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                
                <button
                  type="submit"
                  disabled={loading}
                  className={`px-5 py-2 bg-gradient-to-r from-orange-start to-orange-end text-white rounded-lg shadow-md hover:shadow-lg transition-all ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
                >
                  {loading ? (
                    <>
                      <span className="inline-block animate-spin mr-2">⟳</span>
                      Saving...
                    </>
                  ) : 'Save Changes'}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default EditProfile;
