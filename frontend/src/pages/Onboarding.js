import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthContext from '../context/AuthContext';
import { API_URL } from '../config';

const Onboarding = () => {
  const navigate = useNavigate();
  const { user, loadUserProfile } = useContext(AuthContext);
  
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
    interests: user?.interests || '{"hiking": true, "dining": true, "movies": true, "study": true}',
    prompt1: user?.prompt1 || promptOptions[0],
    answer1: user?.answer1 || '',
    prompt2: user?.prompt2 || promptOptions[1],
    answer2: user?.answer2 || '',
    prompt3: user?.prompt3 || promptOptions[2],
    answer3: user?.answer3 || ''
  });
  
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const nextStep = () => {
    setCurrentStep(prev => prev + 1);
  };
  
  const prevStep = () => {
    setCurrentStep(prev => prev - 1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/api/users/complete-onboarding`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        // Successfully completed onboarding
        const data = await response.json();
        console.log('Onboarding complete response:', data);
        
        try {
          // Ensure we have valid authentication tokens
          const tokenResponse = await fetch(`${API_URL}/api/token/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({})
          });
          
          if (tokenResponse.ok) {
            // Parse and store the tokens
            const tokenData = await tokenResponse.json();
            console.log('Token refresh successful');
            
            // Make sure tokens are properly stored in localStorage (can help with Heroku issues)
            if (tokenData && tokenData.access) {
              localStorage.setItem('authTokens', JSON.stringify(tokenData));
            }
            
            // Force reload user profile and wait for it to complete
            const userProfile = await loadUserProfile();
            console.log('User profile loaded after onboarding:', userProfile);
            
            // Make one more auth check before navigating
            const authCheckResponse = await fetch(`${API_URL}/api/cas/status`, {
              credentials: 'include'
            });
            
            if (authCheckResponse.ok) {
              const authStatus = await authCheckResponse.json();
              console.log('Auth status before navigation:', authStatus);
            }
            
            // Increase the delay to ensure all state updates are processed
            console.log('Preparing to navigate to home page...');
            setTimeout(() => {
              navigate('/');
            }, 1000); // Longer delay for Heroku environment
          } else {
            console.error('Failed to refresh tokens after onboarding');
            setError('Authentication error. Please try logging in again.');
          }
        } catch (tokenErr) {
          console.error('Error during post-onboarding authentication:', tokenErr);
          setError('Authentication error after onboarding. Please try logging in again.');
        }
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to complete onboarding');
      }
    } catch (err) {
      console.error('Error completing onboarding:', err);
      setError('An error occurred while submitting. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const skipOnboarding = async () => {
    setLoading(true);
    
    try {
      const response = await fetch(`${API_URL}/api/users/complete-onboarding`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({})
      });

      if (response.ok) {
        // Successfully completed onboarding
        const data = await response.json();
        
        // Ensure we have valid authentication tokens
        const tokenResponse = await fetch(`${API_URL}/api/token/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({})
        });
            
        if (tokenResponse.ok) {
          console.log('Successfully refreshed authentication tokens after skipping onboarding');
          // Force reload user profile with updated info to ensure authentication state is current
          await loadUserProfile();
          
          // Small delay to ensure state is updated before navigation
          setTimeout(() => {
            navigate('/');
          }, 300);
        } else {
          console.error('Failed to refresh tokens after skipping onboarding');
          setError('Authentication error. Please try logging in again.');
        }
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to complete onboarding');
      }
    } catch (err) {
      console.error('Error skipping onboarding:', err);
      setError('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Render step 1: Basic profile info
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
          min="140"
          max="220"
          value={formData.height}
          onChange={handleChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
        />
        <p className="text-xs text-gray-500 mt-1">{Math.floor(formData.height / 30.48)} ft {Math.round(formData.height % 30.48 / 2.54)} in</p>
      </div>
    </div>
  );
  
  // Render step 2: Location and education
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
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
        />
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
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
          >
            <option value={2023}>2023</option>
            <option value={2024}>2024</option>
            <option value={2025}>2025</option>
            <option value={2026}>2026</option>
            <option value={2027}>2027</option>
          </select>
        </div>
      </div>
    </div>
  );
  
  // Render step 3: Prompts and answers
  const renderStep3 = () => (
    <div className="space-y-6">
      <div>
        <label htmlFor="prompt1" className="block text-sm font-medium text-gray-700 mb-1">Prompt 1</label>
        <select
          id="prompt1"
          name="prompt1"
          value={formData.prompt1}
          onChange={handleChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
        >
          {promptOptions.map((prompt, index) => (
            <option key={`prompt1-${index}`} value={prompt}>{prompt}</option>
          ))}
        </select>
        <textarea
          id="answer1"
          name="answer1"
          rows="2"
          value={formData.answer1}
          onChange={handleChange}
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
          onChange={handleChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
        >
          {promptOptions.map((prompt, index) => (
            <option key={`prompt2-${index}`} value={prompt}>{prompt}</option>
          ))}
        </select>
        <textarea
          id="answer2"
          name="answer2"
          rows="2"
          value={formData.answer2}
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
          onChange={handleChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
        >
          {promptOptions.map((prompt, index) => (
            <option key={`prompt3-${index}`} value={prompt}>{prompt}</option>
          ))}
        </select>
        <textarea
          id="answer3"
          name="answer3"
          rows="2"
          value={formData.answer3}
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
              <button 
                type="button" 
                onClick={skipOnboarding}
                disabled={loading}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 disabled:opacity-50"
              >
                Skip for Now
              </button>
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
