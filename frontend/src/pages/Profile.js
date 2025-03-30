import React, { useContext, useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import AuthContext from '../context/AuthContext';
import { getExperiences } from '../services/api';

const Profile = () => {
  const { user, logoutUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const [userExperiences, setUserExperiences] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('profile');
  
  useEffect(() => {
    const fetchUserExperiences = async () => {
      try {
        setLoading(true);
        const response = await getExperiences();
        // Filter experiences created by this user
        const filteredExperiences = response.data.filter(exp => exp.user_id === user.id);
        setUserExperiences(filteredExperiences);
        setLoading(false);
      } catch (err) {
        setError('Failed to load your experiences');
        setLoading(false);
      }
    };
    
    fetchUserExperiences();
  }, [user.id]);
  
  const handleLogout = async () => {
    try {
      const result = await logoutUser();
      if (result && result.logout_url) {
        // Redirect to CAS logout URL which will then redirect back to login page
        window.location.href = result.logout_url;
      } else {
        // Fallback to just redirecting to login page
        navigate('/login');
      }
    } catch (error) {
      console.error('Error during logout:', error);
      // Fallback to just redirecting to login page
      navigate('/login');
    }
  };
  
  // Function to parse and render interest badges
  const renderInterests = () => {
    if (!user?.interests) return null;
    
    let interestsObj = {};
    try {
      // Try to parse if it's a JSON string
      interestsObj = JSON.parse(user.interests);
    } catch (e) {
      // If it's not valid JSON, try a different approach
      try {
        // Try to parse as comma-separated values
        const interests = user.interests.split(',').map(item => item.trim());
        interests.forEach(interest => {
          interestsObj[interest] = true;
        });
      } catch (err) {
        return null;
      }
    }
    
    // Convert to array of interest names - only ones that are true
    const interestNames = Object.keys(interestsObj).filter(key => interestsObj[key] === true);
    
    return (
      <div className="flex flex-wrap gap-2 mt-3">
        {interestNames.map(interest => (
          <span 
            key={interest} 
            className="px-3 py-1 bg-orange-50 text-orange-800 rounded-full text-sm font-medium"
          >
            {interest.charAt(0).toUpperCase() + interest.slice(1)}
          </span>
        ))}
      </div>
    );
  };
  
  // Function to get a random gradient for experience cards
  const getRandomGradient = () => {
    const gradients = [
      'border-t-orange-500',
      'border-t-orange-400',
      'border-t-orange-600',
      'border-t-accent-light',
    ];
    return gradients[Math.floor(Math.random() * gradients.length)];
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100 py-6">
      <div className="max-w-5xl mx-auto px-4 sm:px-6">
        {/* Profile Header */}
        <div className="bg-white rounded-xl shadow-card mb-8 p-6">
          <div className="flex flex-col md:flex-row items-center">
            <div className="w-28 h-28 md:w-32 md:h-32 bg-gradient-to-r from-orange-start to-orange-end rounded-full flex items-center justify-center text-white text-4xl font-bold shadow-md">
              {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="ml-0 md:ml-8 mt-6 md:mt-0 text-center md:text-left">
              <h1 className="text-3xl font-bold text-gray-800">{user?.name || 'User'}</h1>
              
              <div className="mt-4 flex flex-wrap gap-2 justify-center md:justify-start">
                {renderInterests()}
              </div>
              
              <div className="mt-6 flex flex-wrap gap-3 justify-center md:justify-start">
                <button 
                  onClick={handleLogout} 
                  className="px-4 py-2 bg-white text-gray-700 rounded-lg border border-gray-300 shadow-sm hover:bg-gray-50 transition-colors flex items-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
                  </svg>
                  Logout
                </button>
                
                <Link 
                  to="/profile/edit" 
                  className="px-4 py-2 bg-white text-orange-600 border border-orange-300 rounded-lg font-medium shadow-sm hover:bg-orange-50 transition-colors flex items-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                  </svg>
                  Edit Profile
                </Link>
                
                <Link 
                  to="/experiences/add" 
                  className="px-4 py-2 bg-gradient-to-r from-orange-start to-orange-end text-white rounded-lg font-medium shadow-md hover:shadow-lg transition-all flex items-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                  </svg>
                  Create Experience
                </Link>
              </div>
            </div>
          </div>
        </div>
        
        {/* Tabs */}
        <div className="bg-white rounded-xl mb-6 border border-orange-100 p-1 shadow-sm">
          <div className="flex">
            <button 
              onClick={() => setActiveTab('profile')} 
              className={`flex-1 py-3 px-4 rounded-lg text-center transition-colors ${
                activeTab === 'profile' 
                  ? 'bg-gradient-to-r from-orange-start to-orange-end text-white font-medium' 
                  : 'text-gray-700 hover:bg-orange-50'
              }`}
            >
              My Profile
            </button>
            <button 
              onClick={() => setActiveTab('experiences')} 
              className={`flex-1 py-3 px-4 rounded-lg text-center transition-colors ${
                activeTab === 'experiences' 
                  ? 'bg-gradient-to-r from-orange-start to-orange-end text-white font-medium' 
                  : 'text-gray-700 hover:bg-orange-50'
              }`}
            >
              My Experiences
            </button>
          </div>
        </div>
        
        {/* Tab Content */}
        <div className="bg-white rounded-xl shadow-card p-6">
          {activeTab === 'profile' ? (
            <div>
              <h2 className="text-2xl font-bold mb-6 text-gray-800">Profile Information</h2>
              
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-700 mb-2">Name</h3>
                  <p className="bg-orange-50 rounded-lg p-3 border border-orange-100 text-gray-800">{user?.name || 'Not set'}</p>
                </div>
                
                <div>
                  <h3 className="text-lg font-medium text-gray-700 mb-2">Interests</h3>
                  <div className="bg-orange-50 rounded-lg p-4 border border-orange-100">
                    <div className="flex flex-wrap gap-2">
                      {renderInterests() || <p className="text-gray-500">No interests added yet</p>}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div>
              <h2 className="text-2xl font-bold mb-6 text-gray-800">My Experiences</h2>
              
              {loading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-orange-500 mx-auto mb-4"></div>
                </div>
              ) : error ? (
                <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded">
                  <p>{error}</p>
                </div>
              ) : userExperiences.length === 0 ? (
                <div className="text-center py-10">
                  <div className="mx-auto w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mb-4">
                    <svg className="w-8 h-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                    </svg>
                  </div>
                  <p className="text-gray-600 mb-6">You haven't created any experiences yet</p>
                  <Link 
                    to="/create-experience" 
                    className="px-6 py-3 bg-gradient-to-r from-orange-start to-orange-end text-white font-medium rounded-lg shadow-md hover:shadow-lg transition-all inline-flex items-center"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                    </svg>
                    Create Your First Experience
                  </Link>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {userExperiences.map(experience => (
                    <div key={experience.id} className="bg-white rounded-xl shadow-card border border-orange-100 hover:shadow-card-hover transition-shadow overflow-hidden">
                      <div className="h-32 bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center relative">
                        <div className="text-white text-xl font-medium text-center px-4">
                          {experience.location || "Mystery Location"}
                        </div>
                        <div className="absolute top-3 left-3 px-3 py-1 bg-white/90 rounded-full shadow-sm">
                          <span className="text-sm font-medium bg-clip-text text-transparent bg-gradient-to-r from-orange-start to-orange-end">
                            {experience.experience_type}
                          </span>
                        </div>
                      </div>
                      
                      <div className="p-5">
                        <h3 className="text-xl font-bold text-gray-800 mb-2">
                          {experience.experience_type}
                        </h3>
                        
                        <div className="flex items-center text-sm text-orange-600 mb-4">
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                          </svg>
                          {experience.location || 'No location specified'}
                        </div>
                        
                        <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                          {experience.description || 'No description provided'}
                        </p>
                        
                        <div className="flex justify-end">
                          <Link 
                            to={`/experiences/${experience.id}`} 
                            className="text-orange-600 hover:text-orange-500 text-sm font-medium flex items-center"
                          >
                            View Details
                            <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
                            </svg>
                          </Link>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile; 