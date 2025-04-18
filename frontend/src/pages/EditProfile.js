import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthContext from '../context/AuthContext';
import { updateCurrentUser } from '../services/api';
import axios from 'axios';
import { API_URL } from '../config';
import ProfileImageUpload from '../components/ProfileImageUpload';

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
    answer3: '',
    phone_number: '',
    preferred_email: ''
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
        answer3: user.answer3 || '',
        phone_number: user.phone_number || '',
        preferred_email: user.preferred_email || ''
      });
    }
  }, [user]);
  
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    // Special validation for height field
    if (name === 'height') {
      // Check if height is a valid number within the acceptable range
      const heightVal = parseInt(value, 10);
      if (isNaN(heightVal) || heightVal < 0 || heightVal > 300) {
        setError('Height must be a number between 0 and 300 cm.');
        // Still update the form value for UX purposes, but it won't pass submission validation
      } else {
        setError(''); // Clear error if height is valid
      }
    }
    
    // Validate email field
    if (name === 'preferred_email' && value) {
      const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
      if (!emailRegex.test(value)) {
        setError('Please enter a valid email address.');
        // Still update the form value for UX purposes
      } else {
        setError(''); // Clear error if email is valid
      }
    }
    
    // Validate phone number field
    if (name === 'phone_number' && value) {
      // Basic phone validation - allows various formats with optional country code
      const phoneRegex = /^(\+\d{1,3}[- ]?)?\(?(\d{3})\)?[- ]?(\d{3})[- ]?(\d{4})$/;
      if (!phoneRegex.test(value)) {
        setError('Please enter a valid phone number.');
        // Still update the form value for UX purposes
      } else {
        setError(''); // Clear error if phone is valid
      }
    }
    
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
    
    // Validate height before submission
    const heightVal = parseInt(formData.height, 10);
    if (isNaN(heightVal) || heightVal < 0 || heightVal > 300) {
      setError('Height must be a number between 0 and 300 cm.');
      setLoading(false);
      return;
    }
    
    // Validate email if provided
    if (formData.preferred_email) {
      const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
      if (!emailRegex.test(formData.preferred_email)) {
        setError('Please enter a valid email address.');
        setLoading(false);
        return;
      }
    }
    
    // Validate phone number if provided
    if (formData.phone_number) {
      const phoneRegex = /^(\+\d{1,3}[- ]?)?\(?(\d{3})\)?[- ]?(\d{3})[- ]?(\d{4})$/;
      if (!phoneRegex.test(formData.phone_number)) {
        setError('Please enter a valid phone number.');
        setLoading(false);
        return;
      }
    }
    
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
      
      // Convert height to number if it's provided, with validation
      const height = formData.height ? heightVal : null;
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
        answer3: formData.answer3,
        phone_number: formData.phone_number,
        preferred_email: formData.preferred_email
      };
      
      console.log('Submitting profile update with data:', userData);
      
      // Construct full API URL - ensure it ends with /api/me
      const fullUrl = `${API_URL}/api/me`;
      console.log('Request URL:', fullUrl);
      
      try {
        // Make direct API call to update user using axios instead of the service
        const response = await axios({
          method: 'PUT', 
          url: fullUrl,
          data: userData,
          withCredentials: true,
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        console.log('Profile update response:', response);
        
        if (response.data) {
          console.log('Profile updated successfully:', response.data);
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
      } catch (axiosError) {
        console.error('Axios error details:', {
          message: axiosError.message,
          status: axiosError.response?.status,
          statusText: axiosError.response?.statusText,
          data: axiosError.response?.data
        });
        
        if (axiosError.response) {
          setError(axiosError.response.data?.detail || `Server error: ${axiosError.response.status}`);
        } else if (axiosError.request) {
          console.error('No response received:', axiosError.request);
          setError('No response from server. Please check your internet connection.');
        } else {
          setError(`Error setting up request: ${axiosError.message}`);
        }
      }
    } catch (err) {
      console.error('Error in form submission:', err);
      setError('Form processing error. Please verify your inputs and try again.');
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
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100 py-10">
      <div className="max-w-3xl mx-auto bg-white rounded-xl shadow-card p-8">
        <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">Edit Your Profile</h1>
        
        {error && (
          <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded">
            <p>{error}</p>
          </div>
        )}
        
        {success && (
          <div className="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-6 rounded">
            <p>Profile updated successfully!</p>
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          {/* Profile Images */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4 text-gray-700">Profile Photos</h2>
            <ProfileImageUpload 
              userId={user?.id} 
              onImageUploaded={(image) => {
                // No need to do anything special here since we'll refresh the profile after save
                console.log('Image uploaded:', image);
              }}
            />
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-700">Basic Information</h2>
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
                    required
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
                    required
                  >
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
                    required
                  >
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
                    min="0"
                    max="300"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    placeholder="Enter your height in cm"
                  />
                  {formData.height && (
                    <p className="text-xs text-gray-500 mt-1">
                      {Math.floor(formData.height / 30.48)} ft {Math.round(formData.height % 30.48 / 2.54)} in
                    </p>
                  )}
                </div>
                
                <div>
                  <label htmlFor="class_year" className="block text-sm font-medium text-gray-700 mb-1">
                    Class Year
                  </label>
                  <select
                    id="class_year"
                    name="class_year"
                    value={formData.class_year}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    required
                  >
                    <option value="2024">2024</option>
                    <option value="2025">2025</option>
                    <option value="2026">2026</option>
                    <option value="2027">2027</option>
                    <option value="2028">2028</option>
                    <option value="2029">2029</option>
                    <option value="2030">2030</option>
                  </select>
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
            </div>
          </div>
          
          {/* Contact Information */}
          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-700">Contact Information</h2>
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="phone_number" className="block text-sm font-medium text-gray-700 mb-1">
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    id="phone_number"
                    name="phone_number"
                    value={formData.phone_number}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    placeholder="Enter your phone number (optional)"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Will be shown to your matches for contact purposes
                  </p>
                </div>
                
                <div>
                  <label htmlFor="preferred_email" className="block text-sm font-medium text-gray-700 mb-1">
                    Preferred Email
                  </label>
                  <input
                    type="email"
                    id="preferred_email"
                    name="preferred_email"
                    value={formData.preferred_email}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    placeholder="Enter preferred email (optional)"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    If different from your Princeton email
                  </p>
                </div>
              </div>
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
                required
              >
                <option value="">Select a prompt...</option>
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
                required
              >
                <option value="">Select a prompt...</option>
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
                required
              >
                <option value="">Select a prompt...</option>
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
              ></textarea>
            </div>
          </div>
          
          <div className="mt-8 flex justify-between">
            <button
              type="button"
              onClick={() => navigate('/profile')}
              className="px-6 py-2 bg-gray-50 text-gray-700 rounded-lg border border-gray-300 hover:bg-gray-100 transition-colors"
            >
              Cancel
            </button>
            
            <button
              type="submit"
              disabled={loading}
              className={`px-6 py-2 bg-orange-500 text-white rounded-lg shadow hover:bg-orange-600 transition-colors ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditProfile;
