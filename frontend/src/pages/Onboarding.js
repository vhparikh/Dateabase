import React, { useState, useContext } from 'react';
import AuthContext from '../context/AuthContext';
import { API_URL } from '../config';
import axios from 'axios';
import { useCSRFToken } from '../App';

const Onboarding = () => {
  const { user, loadUserProfile, setUser } = useContext(AuthContext);
  const csrfToken = useCSRFToken();
  
  // List of prompts for users to choose from
  const promptOptions = [
    "The way to my heart is...",
    "A life goal of mine is...",
    "I'm looking for someone who...",
    "My ideal first date would be...",
    "I geek out about...",
    "Two truths and a lie...",
    "My most controversial opinion is...",
    "I'm known for...",
    "My simple pleasures are...",
    "My favorite spot on campus is..."
  ];
  
  const [formData, setFormData] = useState({
    name: user?.name || '',
    gender: user?.gender || 'Other',
    sexuality: user?.sexuality || 'Straight',
    height: user?.height || 170,
    location: user?.location || 'Princeton, NJ',
    hometown: user?.hometown || '',
    major: user?.major || '',
    class_year: user?.class_year || 2025,
    prompt1: user?.prompt1 || promptOptions[0],
    answer1: user?.answer1 || '',
    prompt2: user?.prompt2 || promptOptions[1],
    answer2: user?.answer2 || '',
    prompt3: user?.prompt3 || promptOptions[2],
    answer3: user?.answer3 || '',
    phone_number: user?.phone_number || '',
    preferred_email: user?.preferred_email || ''
  });
  
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
        
    // Required fields validation
    const requiredFields = ['name', 'location', 'hometown', 'phone_number', 'major', 'answer1', 'answer2', 'answer3'];
    if (requiredFields.includes(name) && value.trim() === '') {
      const fieldNames = {
        name: 'Name',
        location: 'Current Location',
        hometown: 'Hometown',
        phone_number: 'Phone Number',
        major: 'Major',
        answer1: 'First Prompt',
        answer2: 'Second Prompt',
        answer3: 'Third Prompt'
      };
      
      setError(`${fieldNames[name]} is required.`);
    }
    
    // Specific validation for height input
    if (name === 'height') {
      const height = parseInt(value, 10);
      
      if (isNaN(height) || height < 0 || height > 300) {
        setError('Height must be a number between 0 and 300 cm.');
      } else {
        setError('');
      }
    }
    
    // Validate email
    if (name === 'preferred_email') {
      if (!value) {
        setError('Email address is required.');
      } else {
        const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailRegex.test(value)) {
          setError('Please enter a valid email address.');
        } else {
          setError('');        
        }
      }
    }
    
    // Update form data
    setFormData({
      ...formData,
      [name]: value
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
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const nextStep = () => {
    // Validate height before proceeding to next step if we're on step 1
    if (currentStep === 1) {
      // Check that name isn't empty
      if (!formData.name.trim()) {
        setError('Name is required.');
        return;
      }

      // Validate height
      const heightVal = parseInt(formData.height, 10);
      if (isNaN(heightVal) || heightVal < 0 || heightVal > 300) {
        setError('Height must be a number between 0 and 300 cm.');
        return;
      }
    }
    
    // Validate fields for step 2 (location and education)
    if (currentStep === 2) {
      // Check that required fields aren't empty
      if (!formData.location.trim()) {
        setError('Current Location is required.');
        return;
      }
      
      if (!formData.hometown.trim()) {
        setError('Hometown is required.');
        return;
      }
      
      if (!formData.phone_number.trim()) {
        setError('Phone Number is required.');
        return;
      }
      
      if (!formData.major.trim()) {
        setError('Major is required.');
        return;
      }
      
      // Validate class year
      if (formData.class_year) {
        const classYearNum = parseInt(formData.class_year, 10);
        if (isNaN(classYearNum) || classYearNum < 2000 || classYearNum > 2030) {
          setError('Please enter a valid class year between 2000 and 2030');
          return;
        }
      }
      
      // Validate email
      if (!formData.preferred_email) {
        setError('Email address is required.');
        return;
      }
      
      const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
      if (!emailRegex.test(formData.preferred_email)) {
        setError('Please enter a valid email address.');
        return;
      }
    }
    
    // Validate fields for step 3 (prompts and answers)
    if (currentStep === 3) {
      // Check that none of the answers are empty
      if (!formData.answer1.trim()) {
        setError('First prompt answer is required.');
        return;
      }
      
      if (!formData.answer2.trim()) {
        setError('Second prompt answer is required.');
        return;
      }
      
      if (!formData.answer3.trim()) {
        setError('Third prompt answer is required.');
        return;
      }
    }
    
    setError(''); // Clear any errors when proceeding
    setCurrentStep(prev => prev + 1);
  };
  
  const prevStep = () => {
    setError(''); // Clear any errors when going back
    setCurrentStep(prev => prev - 1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    // Validate step 3 inputs
    if (currentStep === 3) {
      // Validate class year
      if (formData.class_year) {
        const classYearNum = parseInt(formData.class_year, 10);
        if (isNaN(classYearNum) || classYearNum < 2000 || classYearNum > 2030) {
          setError('Please enter a valid class year between 2000 and 2030');
          setLoading(false);
          return;
        }
      }
      // Check that none of the answers are empty
      if (!formData.answer1.trim()) {
        setError('First prompt answer is required.');
        setLoading(false);
        return;
      }     
      if (!formData.answer2.trim()) {
        setError('Second prompt answer is required.');
        setLoading(false);
        return;
      }
            
      if (!formData.answer3.trim()) {
        setError('Third prompt answer is required.');
        setLoading(false);
        return;
      }
      
      // Call the completeOnboarding function to handle server communication
      const success = await completeOnboarding();
      if (!success) {
        // Error handling is done in the completeOnboarding function
        return;
      }
    } else {
      // Move to the next step for steps 1 and 2
      nextStep();
      setLoading(false);
    }
  };

  // Function to complete onboarding with server
  const completeOnboarding = async () => {
    setLoading(true);
    
    try {
      // console.log('Starting onboarding completion process...');
      
      // Validate email
      if (!formData.preferred_email) {
        setError('Email address is required.');
        setLoading(false);
        return false;
      }
      
      const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
      if (!emailRegex.test(formData.preferred_email)) {
        setError('Please enter a valid email address.');
        setLoading(false);
        return false;
      }
      
      // Properly format user data from form fields
      const userData = {
        name: formData.name,
        gender: formData.gender,
        sexuality: formData.sexuality,
        height: parseInt(formData.height, 10) || 170,
        location: formData.location || '',
        hometown: formData.hometown || '',
        major: formData.major || '',
        class_year: parseInt(formData.class_year, 10) || 2025,
        // Ensure prompts are explicitly included
        prompt1: formData.prompt1 || '',
        answer1: formData.answer1 || '',
        prompt2: formData.prompt2 || '',
        answer2: formData.answer2 || '',
        prompt3: formData.prompt3 || '',
        answer3: formData.answer3 || '',
        phone_number: formData.phone_number || '',
        preferred_email: formData.preferred_email
      };
      
      // console.log('Submitting onboarding data:', userData);
      
      // Make API call to complete onboarding
      const response = await axios.post(`${API_URL}/api/users/complete-onboarding`, userData, { withCredentials: true, 
        headers: {
          'Content-Type': 'application/json',
          'X-CsrfToken': csrfToken
        }
      });
      
      if (response.status !== 200) {
        const errorData = response.data;
        // console.error('Onboarding failed with status:', response.status, errorData);
        setError('Failed to complete onboarding. Please try again.');
        setLoading(false);
        return false;
      }
      
      const data = response.data;
      // console.log('Onboarding completed successfully:', data);
        
      // Force reload user profile and wait for it to complete
      const userProfile = await loadUserProfile();
      // console.log('User profile loaded after onboarding:', userProfile);
      
      if (userProfile) {
        // console.log('Updating user context with completed onboarding status');
        setUser({
          ...userProfile,
          onboarding_completed: true
        });
      }
      
      // Navigate to the home/swipe page
      // console.log('Navigating to home page...');
      window.localStorage.setItem('onboardingCompleted', 'true');
      
      window.location.href = '/swipe';
      return true;
    } catch (error) {
      // console.error('Error during onboarding:', error);
      setError('An unexpected error occurred. Please try again.');
      setLoading(false);
      return false;
    }
  };

  // Basic profile info
  const renderStep1 = () => (
    <div className="space-y-6">
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">Name</label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          required
          maxLength={30}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
        />
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="gender" className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
          <select
            id="gender"
            name="gender"
            value={formData.gender}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
          >
            <option value="Male">Male</option>
            <option value="Female">Female</option>
            <option value="Non-Binary">Non-Binary</option>
            <option value="Other">Other</option>
          </select>
        </div>
        
        <div>
          <label htmlFor="sexuality" className="block text-sm font-medium text-gray-700 mb-1">Sexuality</label>
          <select
            id="sexuality"
            name="sexuality"
            value={formData.sexuality}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
          >
            <option value="Straight">Straight</option>
            <option value="Gay">Gay</option>
            <option value="Lesbian">Lesbian</option>
            <option value="Bisexual">Bisexual</option>
            <option value="Pansexual">Pansexual</option>
            <option value="Asexual">Asexual</option>
            <option value="Other">Other</option>
          </select>
        </div>
      </div>
      
      <div>
        <label htmlFor="height" className="block text-sm font-medium text-gray-700 mb-1">Height (cm)</label>
        <input
          type="number"
          id="height"
          name="height"
          min="0"
          max="300"
          value={formData.height}
          onChange={handleChange}
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
        />
        <p className="text-xs text-gray-500 mt-1">
          {Math.floor(formData.height / 30.48)} ft {Math.round(formData.height % 30.48 / 2.54)} in
        </p>
      </div>
    </div>
  );
  
  // Location and education
  const renderStep2 = () => (
    <div className="space-y-6">
      <div>
        <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">Current Location</label>
        <input
          type="text"
          id="location"
          name="location"
          value={formData.location}
          onChange={handleChange}
          required
          maxLength={45}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
        />
      </div>
      
      <div>
        <label htmlFor="hometown" className="block text-sm font-medium text-gray-700 mb-1">Hometown</label>
        <input
          type="text"
          id="hometown"
          name="hometown"
          value={formData.hometown}
          onChange={handleChange}
          required
          maxLength={45}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
        />
      </div>
      
      <div className="mt-6">
        <h3 className="text-lg font-medium text-gray-700 mb-3">Contact Information</h3>
        <p className="text-sm text-gray-500 mb-3">This information will be shared with your matches</p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="phone_number" className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
            <input
              type="tel"
              id="phone_number"
              name="phone_number"
              value={formData.phone_number}
              onChange={handleChange}
              required
              maxLength={15}
              placeholder="(123) 456-7890"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Will only be shared with confirmed matches
            </p>
          </div>
          
          <div>
            <label htmlFor="preferred_email" className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              id="preferred_email"
              name="preferred_email"
              value={formData.preferred_email}
              onChange={handleChange}
              maxLength={45}
              placeholder="Enter your email address"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Your email will only be shared with confirmed matches (required)
            </p>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="major" className="block text-sm font-medium text-gray-700 mb-1">Major</label>
          <input
            type="text"
            id="major"
            name="major"
            value={formData.major}
            onChange={handleChange}
            required
            maxLength={30}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
          />
        </div>
        
        <div>
          <label htmlFor="class_year" className="block text-sm font-medium text-gray-700 mb-1">Class Year</label>
          <select
            id="class_year"
            name="class_year"
            value={formData.class_year}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
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
    </div>
  );
  
  // Get available prompts
  const getAvailablePrompts = (currentField) => {
    const selectedPrompts = [];
    
    if (currentField !== 'prompt1' && formData.prompt1) selectedPrompts.push(formData.prompt1);
    if (currentField !== 'prompt2' && formData.prompt2) selectedPrompts.push(formData.prompt2);
    if (currentField !== 'prompt3' && formData.prompt3) selectedPrompts.push(formData.prompt3);
    
    return promptOptions.filter(prompt => !selectedPrompts.includes(prompt));
  };

  // Prompts and answers
  const renderStep3 = () => (
    <div className="space-y-6">
      <div>
        <label htmlFor="prompt1" className="block text-sm font-medium text-gray-700 mb-1">Prompt 1</label>
        <select
          id="prompt1"
          name="prompt1"
          value={formData.prompt1}
          onChange={handlePromptChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
        >
          {getAvailablePrompts('prompt1').map((prompt, index) => (
            <option key={`prompt1-${index}`} value={prompt}>{prompt}</option>
          ))}
        </select>
        <textarea
          id="answer1"
          name="answer1"
          rows="2"
          value={formData.answer1}
          onChange={handleChange}
          maxLength={150}
          required
          placeholder="Your answer..."
          className="mt-2 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
        />
      </div>
      
      <div>
        <label htmlFor="prompt2" className="block text-sm font-medium text-gray-700 mb-1">Prompt 2</label>
        <select
          id="prompt2"
          name="prompt2"
          value={formData.prompt2}
          onChange={handlePromptChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
        >
          {getAvailablePrompts('prompt2').map((prompt, index) => (
            <option key={`prompt2-${index}`} value={prompt}>{prompt}</option>
          ))}
        </select>
        <textarea
          id="answer2"
          name="answer2"
          rows="2"
          value={formData.answer2}
          required
          maxLength={150}
          onChange={handleChange}
          placeholder="Your answer..."
          className="mt-2 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
        />
      </div>
      
      <div>
        <label htmlFor="prompt3" className="block text-sm font-medium text-gray-700 mb-1">Prompt 3</label>
        <select
          id="prompt3"
          name="prompt3"
          value={formData.prompt3}
          onChange={handlePromptChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
        >
          {getAvailablePrompts('prompt3').map((prompt, index) => (
            <option key={`prompt3-${index}`} value={prompt}>{prompt}</option>
          ))}
        </select>
        <textarea
          id="answer3"
          name="answer3"
          rows="2"
          value={formData.answer3}
          required
          maxLength={150}
          onChange={handleChange}
          placeholder="Your answer..."
          className="mt-2 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
        />
      </div>
    </div>
  );
  
  return (
    <div className="container mx-auto max-w-2xl px-4 py-8">
      <div className="bg-white shadow-lg rounded-lg p-8">
        <h1 className="text-3xl font-bold text-center mb-2">Welcome to DateABase!</h1>
        <h2 className="text-xl text-center mb-8">Let's set up your profile</h2>

        {error && (
          <div className="bg-red-100 text-red-700 p-3 rounded mb-4">
            {error}
          </div>
        )}
        
        {/* Progress steps */}
        <div className="flex justify-between mb-8">
          <div className={`w-1/3 text-center ${currentStep >= 1 ? 'text-orange-600' : 'text-gray-400'}`}>
            <div className={`h-8 w-8 mx-auto rounded-full flex items-center justify-center ${currentStep >= 1 ? 'bg-orange-100 text-orange-600' : 'bg-gray-200 text-gray-500'}`}>1</div>
            <p className="text-xs mt-1">Basic Info</p>
          </div>
          <div className={`w-1/3 text-center ${currentStep >= 2 ? 'text-orange-600' : 'text-gray-400'}`}>
            <div className={`h-8 w-8 mx-auto rounded-full flex items-center justify-center ${currentStep >= 2 ? 'bg-orange-100 text-orange-600' : 'bg-gray-200 text-gray-500'}`}>2</div>
            <p className="text-xs mt-1">Location & Education</p>
          </div>
          <div className={`w-1/3 text-center ${currentStep >= 3 ? 'text-orange-600' : 'text-gray-400'}`}>
            <div className={`h-8 w-8 mx-auto rounded-full flex items-center justify-center ${currentStep >= 3 ? 'bg-orange-100 text-orange-600' : 'bg-gray-200 text-gray-500'}`}>3</div>
            <p className="text-xs mt-1">Prompts</p>
          </div>
        </div>

        <form>
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}

          <div className="mt-8 flex justify-between">
            {currentStep === 1 ? (
              <div></div>
            ) : (
              <button 
                type="button" 
                onClick={prevStep}
                disabled={loading}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 disabled:opacity-50"
              >
                Back
              </button>
            )}
            
            {currentStep < 3 ? (
              <button 
                type="button" 
                onClick={nextStep}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-white bg-orange-600 hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
              >
                Next
              </button>
            ) : (
              <button 
                type="button" 
                onClick={handleSubmit}
                disabled={loading}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-white bg-orange-600 hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 disabled:opacity-50"
              >
                Complete Setup
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};

export default Onboarding;
