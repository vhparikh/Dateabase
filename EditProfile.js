import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthContext from '../context/AuthContext';
import { updateUser } from '../services/api';

const EditProfile = () => {
  const { user, setUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    interests: ''
  });

  useEffect(() => {
    if (user) {
      // Parse name into first and last name if available
      let firstName = '';
      let lastName = '';
      if (user.name) {
        const nameParts = user.name.split(' ');
        firstName = nameParts[0] || '';
        lastName = nameParts.slice(1).join(' ') || '';
      }

      // Format interests for display in textarea
      let interestsText = '';
      if (user.interests) {
        try {
          // Try to parse if it's a JSON string
          const interestsObj = JSON.parse(user.interests);
          interestsText = Object.keys(interestsObj)
            .filter(key => interestsObj[key])
            .join(', ');
        } catch (e) {
          // If it's not valid JSON, use as is
          interestsText = user.interests;
        }
      }

      setFormData({
        firstName: firstName,
        lastName: lastName,
        email: user.email || '',
        interests: interestsText
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess(false);

    try {
      // Format interests as JSON object
      const interestsArray = formData.interests.split(',').map(item => item.trim());
      const interestsObj = {};
      interestsArray.forEach(interest => {
        if (interest) interestsObj[interest] = true;
      });

      // Create full name from first and last name
      const fullName = `${formData.firstName} ${formData.lastName}`.trim();

      const userData = {
        name: fullName,
        interests: JSON.stringify(interestsObj)
      };

      const response = await updateUser(user.id, userData);
      
      // Update user context with new data
      setUser({
        ...user,
        ...response.data
      });

      setSuccess(true);
      setTimeout(() => {
        navigate('/profile');
      }, 2000);
    } catch (err) {
      console.error('Error updating profile:', err);
      
      // Check if the error has a response with detailed error message
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Failed to update profile. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100 py-8">
      <div className="max-w-2xl mx-auto px-4 sm:px-6">
        <div className="bg-white rounded-xl shadow-card p-6 mb-6">
          <h1 className="text-2xl font-bold text-gray-800 mb-6">Edit Profile</h1>
          
          {success && (
            <div className="mb-6 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
              Profile updated successfully! Redirecting to profile page...
            </div>
          )}
          
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}
          
          <form onSubmit={handleSubmit}>
            <div className="space-y-5">

              {/* First Name field */}
              <div>
                <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-1">
                  First Name
                </label>
                <input
                  type="text"
                  id="firstName"
                  name="firstName"
                  value={formData.firstName}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-orange-500 focus:border-orange-500"
                  required
                />
              </div>
              
              {/* Last Name field */}
              <div>
                <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-1">
                  Last Name
                </label>
                <input
                  type="text"
                  id="lastName"
                  name="lastName"
                  value={formData.lastName}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-orange-500 focus:border-orange-500"
                  required
                />
              </div>
              
              {/* Email field (read-only) */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                  Email (Princeton CAS)
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  className="w-full px-4 py-2 bg-gray-100 border border-gray-300 rounded-lg text-gray-500"
                  disabled
                />
                <p className="mt-1 text-xs text-gray-500">Email is set automatically based on your Princeton CAS netID</p>
              </div>
              
              {/* Interests field */}
              <div>
                <label htmlFor="interests" className="block text-sm font-medium text-gray-700 mb-1">
                  Interests (comma-separated)
                </label>
                <textarea
                  id="interests"
                  name="interests"
                  value={formData.interests}
                  onChange={handleChange}
                  rows="4"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-orange-500 focus:border-orange-500"
                  placeholder="e.g. hiking, reading, travel, cooking"
                ></textarea>
              </div>
              
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => navigate('/profile')}
                  className="px-4 py-2 bg-white text-gray-700 rounded-lg border border-gray-300 shadow-sm hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-2 bg-gradient-to-r from-orange-start to-orange-end text-white rounded-lg font-medium shadow-md hover:shadow-lg transition-all flex items-center justify-center"
                >
                  {loading ? (
                    <>
                      <span className="animate-spin h-4 w-4 mr-2 border-t-2 border-b-2 border-white rounded-full"></span>
                      Saving...
                    </>
                  ) : (
                    'Save Changes'
                  )}
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
