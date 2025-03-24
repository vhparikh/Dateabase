import React, { useState, useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthContext from '../context/AuthContext';
import { API_URL } from '../config';

const CompleteProfile = () => {
  const navigate = useNavigate();
  const { user, authTokens } = useContext(AuthContext);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    gender: 'Other',
    class_year: new Date().getFullYear(),
    interests: JSON.stringify({
      dining: false,
      hiking: false,
      movies: false,
      study: false,
      sports: false,
      music: false,
      art: false,
      travel: false
    })
  });

  useEffect(() => {
    // If user is not authenticated, redirect to login
    if (!authTokens) {
      navigate('/login');
    }
  }, [authTokens, navigate]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleInterestChange = (interest) => {
    try {
      let currentInterests;
      
      try {
        currentInterests = JSON.parse(formData.interests);
      } catch (parseError) {
        console.error("Error parsing interests:", parseError);
        currentInterests = {
          dining: false,
          hiking: false,
          movies: false,
          study: false,
          sports: false,
          music: false,
          art: false,
          travel: false
        };
      }
      
      const updatedInterests = {
        ...currentInterests,
        [interest]: !currentInterests[interest]
      };
      
      setFormData({
        ...formData,
        interests: JSON.stringify(updatedInterests)
      });
    } catch (err) {
      console.error("Error handling interest change:", err);
      setFormData({
        ...formData,
        interests: JSON.stringify({
          dining: false,
          hiking: false,
          movies: false,
          study: false,
          sports: false,
          music: false,
          art: false,
          travel: false
        })
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      setError('Name is required');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      // Update user profile
      const response = await fetch(`${API_URL}/api/users/${user.sub}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authTokens.access}`
        },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      
      if (response.status === 200) {
        navigate('/');
      } else {
        setError(data.detail || 'Failed to update profile. Please try again.');
      }
    } catch (err) {
      console.error('Profile update error:', err);
      setError('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderInterests = () => {
    const interests = {
      dining: "Dining",
      hiking: "Hiking",
      movies: "Movies",
      study: "Study",
      sports: "Sports",
      music: "Music",
      art: "Art",
      travel: "Travel"
    };
    
    try {
      const parsedInterests = JSON.parse(formData.interests);
      
      return Object.keys(interests).map(key => (
        <div 
          key={key}
          onClick={() => handleInterestChange(key)}
          className={`p-4 border rounded-lg cursor-pointer transition-colors text-center
            ${parsedInterests[key] 
              ? 'border-orange-500 bg-orange-50 text-orange-700' 
              : 'border-gray-200 hover:border-orange-300 text-gray-600 hover:bg-orange-50/50'
            }`}
        >
          {interests[key]}
        </div>
      ));
    } catch (err) {
      console.error("Error rendering interests:", err);
      return null;
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-white-gradient px-4 py-12 relative">
      {/* Animated background elements with softer opacity */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute left-1/4 top-1/3 w-64 h-64 bg-orange-200 rounded-full mix-blend-multiply filter blur-xl animate-blob opacity-30"></div>
        <div className="absolute right-1/4 top-1/2 w-72 h-72 bg-orange-300 rounded-full mix-blend-multiply filter blur-xl animate-blob animation-delay-2000 opacity-30"></div>
        <div className="absolute left-1/3 bottom-1/4 w-80 h-80 bg-orange-100 rounded-full mix-blend-multiply filter blur-xl animate-blob animation-delay-4000 opacity-30"></div>
      </div>
      
      <div className="w-full max-w-2xl z-10">
        <div className="text-center mb-10">
          <h1 className="text-5xl font-bold mb-3 text-gray-800">DateABase</h1>
          <p className="text-gray-600 text-lg">Complete your profile to get started</p>
        </div>
        
        <div className="bg-white rounded-2xl shadow-md p-8 border border-gray-100">
          <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">Tell us about yourself</h2>
          
          {error && (
            <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded-md" role="alert">
              <p>{error}</p>
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-gray-700 mb-2 font-medium" htmlFor="name">
                Your Name
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                placeholder="Enter your name"
                required
              />
            </div>
            
            <div>
              <label className="block text-gray-700 mb-2 font-medium" htmlFor="gender">
                Gender
              </label>
              <select
                id="gender"
                name="gender"
                value={formData.gender}
                onChange={handleChange}
                className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
                <option value="Prefer not to say">Prefer not to say</option>
              </select>
            </div>
            
            <div>
              <label className="block text-gray-700 mb-2 font-medium" htmlFor="class_year">
                Class Year
              </label>
              <select
                id="class_year"
                name="class_year"
                value={formData.class_year}
                onChange={handleChange}
                className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              >
                {Array.from({ length: 8 }, (_, i) => {
                  const year = new Date().getFullYear() - 3 + i;
                  return <option key={year} value={year}>{year}</option>;
                })}
              </select>
            </div>
            
            <div>
              <label className="block text-gray-700 mb-2 font-medium">
                Your Interests
              </label>
              <p className="text-gray-500 text-sm mb-4">Select all that apply</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {renderInterests()}
              </div>
            </div>
            
            <button
              type="submit"
              className="w-full px-4 py-3 bg-orange-500 text-white rounded-lg font-medium hover:bg-orange-600 transition-colors"
              disabled={loading}
            >
              {loading ? 'Saving...' : 'Complete Your Profile'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CompleteProfile; 