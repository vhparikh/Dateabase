import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthContext from '../context/AuthContext';
import { updateCurrentUser } from '../services/api';

const EditProfile = () => {
  const { user, setUser } = useContext(AuthContext);
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    gender: '',
    sexuality: '',
    height: '',
    location: '',
    hometown: '',
    major: '',
    class_year: '',
    interests: {},
    prompt1: '',
    answer1: '',
    prompt2: '',
    answer2: '',
    prompt3: '',
    answer3: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  
  // Interest options
  const interestOptions = [
    'Coffee', 'Dining', 'Study', 'Movies', 'Hiking', 'Music',
    'Art', 'Sports', 'Gaming', 'Reading', 'Travel', 'Photography'
  ];
  
  // Gender options
  const genderOptions = [
    'Male', 'Female', 'Non-binary', 'Other', 'Prefer not to say'
  ];
  
  // Sexuality options
  const sexualityOptions = [
    'Straight', 'Gay', 'Lesbian', 'Bisexual', 'Pansexual', 'Asexual', 'Other', 'Prefer not to say'
  ];
  
  // Prompt options
  const promptOptions = [
    'My favorite spot on campus is...',
    'Two truths and a lie...',
    'You should match with me if...',
    'My typical Friday night...',
    'I get way too excited about...',
    'Best travel story...',
    'My most controversial opinion...',
    'My favorite class at Princeton...',
    'The way to my heart is...',
    'A life goal of mine is...',
    'I\'m looking for someone who...',
    'My ideal first date would be...',
    'I geek out about...',
    'I\'m known for...',
    'My simple pleasures are...'
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
        gender: user.gender || '',
        sexuality: user.sexuality || '',
        height: user.height || '',
        location: user.location || '',
        hometown: user.hometown || '',
        major: user.major || '',
        class_year: user.class_year || '',
        interests: interestsObj,
        prompt1: user.prompt1 || '',
        answer1: user.answer1 || '',
        prompt2: user.prompt2 || '',
        answer2: user.answer2 || '',
        prompt3: user.prompt3 || '',
        answer3: user.answer3 || ''
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
  
  // Handle prompt selection with duplicate prevention
  const handlePromptChange = (e) => {
    const { name, value } = e.target;
    const otherPrompts = [];
    
    // Collect the other prompt values
    if (name !== 'prompt1' && formData.prompt1) otherPrompts.push(formData.prompt1);
    if (name !== 'prompt2' && formData.prompt2) otherPrompts.push(formData.prompt2);
    if (name !== 'prompt3' && formData.prompt3) otherPrompts.push(formData.prompt3);
    
    // Check if the selected prompt is already used
    if (otherPrompts.includes(value)) {
      setError(`You've already selected "${value}" for another prompt. Please choose a different prompt.`);
      return;
    }
    
    setError(''); // Clear error if selection is valid
    setFormData({ ...formData, [name]: value });
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess(false);
    
    // Validate that prompts are not duplicated
    const selectedPrompts = [formData.prompt1, formData.prompt2, formData.prompt3].filter(Boolean);
    const uniquePrompts = [...new Set(selectedPrompts)];
    
    if (selectedPrompts.length !== uniquePrompts.length) {
      setError('You have selected the same prompt multiple times. Please choose different prompts.');
      setLoading(false);
      return;
    }
    
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
      
      // Convert height to number if it's provided
      const height = formData.height ? parseInt(formData.height, 10) : null;
      const class_year = formData.class_year ? parseInt(formData.class_year, 10) : null;
      
      const userData = {
        name,
        gender: formData.gender,
        sexuality: formData.sexuality,
        height,
        location: formData.location,
        hometown: formData.hometown,
        major: formData.major,
        class_year,
        interests,
        prompt1: formData.prompt1,
        answer1: formData.answer1,
        prompt2: formData.prompt2,
        answer2: formData.answer2,
        prompt3: formData.prompt3,
        answer3: formData.answer3
      };
      
      // Make API call to update user using updateCurrentUser
      const response = await updateCurrentUser(userData);
      
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
  
  // Function to get available prompts (excluding already selected ones except the current field)
  const getAvailablePrompts = (currentField) => {
    const selectedPrompts = [];
    
    if (currentField !== 'prompt1' && formData.prompt1) selectedPrompts.push(formData.prompt1);
    if (currentField !== 'prompt2' && formData.prompt2) selectedPrompts.push(formData.prompt2);
    if (currentField !== 'prompt3' && formData.prompt3) selectedPrompts.push(formData.prompt3);
    
    return promptOptions.filter(prompt => !selectedPrompts.includes(prompt));
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
              
              {/* Gender and Sexuality */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                <div>
                  <label htmlFor="gender" className="block text-sm font-medium text-gray-700 mb-1">
                    Gender
                  </label>
                  <select
                    id="gender"
                    name="gender"
                    value={formData.gender}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                  >
                    <option value="">Select Gender</option>
                    {genderOptions.map(option => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label htmlFor="sexuality" className="block text-sm font-medium text-gray-700 mb-1">
                    Sexuality
                  </label>
                  <select
                    id="sexuality"
                    name="sexuality"
                    value={formData.sexuality}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                  >
                    <option value="">Select Sexuality</option>
                    {sexualityOptions.map(option => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              {/* Height and Class Year */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                <div>
                  <label htmlFor="height" className="block text-sm font-medium text-gray-700 mb-1">
                    Height (cm)
                  </label>
                  <input
                    type="number"
                    id="height"
                    name="height"
                    value={formData.height}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    placeholder="Enter your height in cm"
                  />
                </div>
                
                <div>
                  <label htmlFor="class_year" className="block text-sm font-medium text-gray-700 mb-1">
                    Class Year
                  </label>
                  <input
                    type="number"
                    id="class_year"
                    name="class_year"
                    value={formData.class_year}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    placeholder="Enter your graduation year"
                  />
                </div>
              </div>
              
              {/* Location and Hometown */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                <div>
                  <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
                    Current Location
                  </label>
                  <input
                    type="text"
                    id="location"
                    name="location"
                    value={formData.location}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    placeholder="Where you currently live"
                  />
                </div>
                
                <div>
                  <label htmlFor="hometown" className="block text-sm font-medium text-gray-700 mb-1">
                    Hometown
                  </label>
                  <input
                    type="text"
                    id="hometown"
                    name="hometown"
                    value={formData.hometown}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    placeholder="Where you're from"
                  />
                </div>
              </div>
              
              {/* Major */}
              <div className="mt-6">
                <label htmlFor="major" className="block text-sm font-medium text-gray-700 mb-1">
                  Major
                </label>
                <input
                  type="text"
                  id="major"
                  name="major"
                  value={formData.major}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                  placeholder="Your field of study"
                />
              </div>
              
              {/* Interests */}
              <div className="mt-6">
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
              
              {/* Prompts and Answers Section */}
              <div className="mt-8">
                <h2 className="text-xl font-bold text-gray-800 mb-4">About You</h2>
                <p className="text-sm text-gray-600 mb-4">
                  Answer a few prompts to help others get to know you better. Choose different prompts for each answer.
                </p>
                
                {/* Prompt 1 */}
                <div className="mb-6">
                  <label htmlFor="prompt1" className="block text-sm font-medium text-gray-700 mb-1">
                    Prompt 1
                  </label>
                  <select
                    id="prompt1"
                    name="prompt1"
                    value={formData.prompt1}
                    onChange={handlePromptChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 mb-2"
                  >
                    <option value="">Select a prompt</option>
                    {getAvailablePrompts('prompt1').map(prompt => (
                      <option key={prompt} value={prompt}>{prompt}</option>
                    ))}
                  </select>
                  <textarea
                    id="answer1"
                    name="answer1"
                    value={formData.answer1}
                    onChange={handleInputChange}
                    placeholder="Your answer..."
                    rows="3"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    disabled={!formData.prompt1}
                  ></textarea>
                </div>
                
                {/* Prompt 2 */}
                <div className="mb-6">
                  <label htmlFor="prompt2" className="block text-sm font-medium text-gray-700 mb-1">
                    Prompt 2
                  </label>
                  <select
                    id="prompt2"
                    name="prompt2"
                    value={formData.prompt2}
                    onChange={handlePromptChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 mb-2"
                  >
                    <option value="">Select a prompt</option>
                    {getAvailablePrompts('prompt2').map(prompt => (
                      <option key={prompt} value={prompt}>{prompt}</option>
                    ))}
                  </select>
                  <textarea
                    id="answer2"
                    name="answer2"
                    value={formData.answer2}
                    onChange={handleInputChange}
                    placeholder="Your answer..."
                    rows="3"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    disabled={!formData.prompt2}
                  ></textarea>
                </div>
                
                {/* Prompt 3 */}
                <div className="mb-6">
                  <label htmlFor="prompt3" className="block text-sm font-medium text-gray-700 mb-1">
                    Prompt 3
                  </label>
                  <select
                    id="prompt3"
                    name="prompt3"
                    value={formData.prompt3}
                    onChange={handlePromptChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 mb-2"
                  >
                    <option value="">Select a prompt</option>
                    {getAvailablePrompts('prompt3').map(prompt => (
                      <option key={prompt} value={prompt}>{prompt}</option>
                    ))}
                  </select>
                  <textarea
                    id="answer3"
                    name="answer3"
                    value={formData.answer3}
                    onChange={handleInputChange}
                    placeholder="Your answer..."
                    rows="3"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    disabled={!formData.prompt3}
                  ></textarea>
                </div>
              </div>
              
              {/* Form submission buttons */}
              <div className="flex items-center justify-end space-x-4 mt-8">
                <button
                  type="button"
                  onClick={() => navigate('/profile')}
                  className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-2 border border-transparent rounded-lg text-white bg-gradient-to-r from-orange-start to-orange-end shadow-sm hover:shadow-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 disabled:opacity-50"
                >
                  {loading ? 'Saving...' : 'Save Changes'}
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
