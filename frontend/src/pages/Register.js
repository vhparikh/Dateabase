import React, { useState, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import AuthContext from '../context/AuthContext';

const Register = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    password2: '',
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
  
  const { registerUser, loginUser } = useContext(AuthContext);
  
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
      
      // First, try parsing the current interests
      try {
        currentInterests = JSON.parse(formData.interests);
      } catch (parseError) {
        console.error("Error parsing interests:", parseError);
        // If there's a parsing error, set default interests
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
      
      // Toggle the selected interest
      const updatedInterests = {
        ...currentInterests,
        [interest]: !currentInterests[interest]
      };
      
      // Update the form data with the new interests
      setFormData({
        ...formData,
        interests: JSON.stringify(updatedInterests)
      });
    } catch (err) {
      console.error("Error handling interest change:", err);
      // Set default interests if there's any error
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
  
  const validateStep1 = () => {
    if (!formData.username.trim()) return 'Username is required';
    if (formData.username.length < 3) return 'Username must be at least 3 characters';
    if (formData.password.length < 6) return 'Password must be at least 6 characters';
    if (formData.password !== formData.password2) return 'Passwords do not match';
    return '';
  };
  
  const validateStep2 = () => {
    if (!formData.name.trim()) return 'Name is required';
    if (formData.name.length < 2) return 'Name must be at least 2 characters';
    if (!formData.gender) return 'Gender is required';
    if (!formData.class_year) return 'Class year is required';
    return '';
  };
  
  const validateStep3 = () => {
    try {
      const interests = JSON.parse(formData.interests);
      const selectedInterests = Object.keys(interests).filter(key => interests[key]);
      if (selectedInterests.length === 0) return 'Please select at least one interest';
      return '';
    } catch (err) {
      console.error("Error validating interests:", err);
      return 'Error processing interests, please try again';
    }
  };
  
  const nextStep = () => {
    let validationError = '';
    if (step === 1) validationError = validateStep1();
    if (step === 2) validationError = validateStep2();
    
    if (validationError) {
      setError(validationError);
      return;
    }
    
    setError('');
    setStep(step + 1);
  };
  
  const prevStep = () => {
    setError('');
    setStep(step - 1);
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const validationError = validateStep3();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      // Ensure interests is a valid JSON string before submitting
      try {
        JSON.parse(formData.interests);
      } catch (parseError) {
        // Reset interests to default if not valid
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
      
      // Register the user
      const registrationResult = await registerUser(formData);
      
      if (!registrationResult.success) {
        setError(registrationResult.message || 'Registration failed. Please try again.');
        setLoading(false);
        return;
      }
      
      // Auto login after successful registration
      const loginResult = await loginUser(formData.username, formData.password);
      
      if (loginResult.success) {
        navigate('/');
      } else {
        setError('Registration successful, but login failed. Please try logging in manually.');
        setTimeout(() => navigate('/login'), 3000);
      }
    } catch (err) {
      console.error('Registration error:', err);
      setError('An error occurred during registration. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const renderStep1 = () => (
    <>
      <h2 className="text-2xl font-bold mb-6 text-center text-white">Create Account</h2>
      
      <div className="mb-4">
        <label className="block text-gray-200 mb-2" htmlFor="username">
          Username
        </label>
        <input
          type="text"
          id="username"
          name="username"
          value={formData.username}
          onChange={handleChange}
          className="w-full px-4 py-2 rounded-lg bg-white/10 border border-gray-300/20 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          placeholder="Choose a username"
        />
      </div>
      
      <div className="mb-4">
        <label className="block text-gray-200 mb-2" htmlFor="password">
          Password
        </label>
        <input
          type="password"
          id="password"
          name="password"
          value={formData.password}
          onChange={handleChange}
          className="w-full px-4 py-2 rounded-lg bg-white/10 border border-gray-300/20 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          placeholder="Create a password"
        />
      </div>
      
      <div className="mb-4">
        <label className="block text-gray-200 mb-2" htmlFor="password2">
          Confirm Password
        </label>
        <input
          type="password"
          id="password2"
          name="password2"
          value={formData.password2}
          onChange={handleChange}
          className="w-full px-4 py-2 rounded-lg bg-white/10 border border-gray-300/20 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          placeholder="Confirm your password"
        />
      </div>
    </>
  );
  
  const renderStep2 = () => (
    <>
      <h2 className="text-2xl font-bold mb-6 text-center text-white">Your Profile</h2>
      
      <div className="mb-4">
        <label className="block text-gray-200 mb-2" htmlFor="name">
          Full Name
        </label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          className="w-full px-4 py-2 rounded-lg bg-white/10 border border-gray-300/20 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          placeholder="Your full name"
        />
      </div>
      
      <div className="mb-4">
        <label className="block text-gray-200 mb-2" htmlFor="gender">
          Gender
        </label>
        <select
          id="gender"
          name="gender"
          value={formData.gender}
          onChange={handleChange}
          className="w-full px-4 py-2 rounded-lg bg-white/10 border border-gray-300/20 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        >
          <option value="Male">Male</option>
          <option value="Female">Female</option>
          <option value="Non-binary">Non-binary</option>
          <option value="Other">Other</option>
        </select>
      </div>
      
      <div className="mb-4">
        <label className="block text-gray-200 mb-2" htmlFor="class_year">
          Class Year
        </label>
        <select
          id="class_year"
          name="class_year"
          value={formData.class_year}
          onChange={handleChange}
          className="w-full px-4 py-2 rounded-lg bg-white/10 border border-gray-300/20 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        >
          {[...Array(10)].map((_, i) => {
            const year = new Date().getFullYear() + i - 4;
            return (
              <option key={year} value={year}>
                {year}
              </option>
            );
          })}
        </select>
      </div>
    </>
  );
  
  const renderStep3 = () => {
    let interests = {};
    
    try {
      interests = JSON.parse(formData.interests);
    } catch (err) {
      console.error("Error parsing interests in renderStep3:", err);
      // Create default interests object if parsing fails
      interests = {
        dining: false,
        hiking: false,
        movies: false,
        study: false,
        sports: false,
        music: false,
        art: false,
        travel: false
      };
      
      // Update the formData with the default interests
      setTimeout(() => {
        setFormData({
          ...formData,
          interests: JSON.stringify(interests)
        });
      }, 0);
    }
    
    // Count selected interests for validation feedback
    const selectedCount = Object.values(interests).filter(Boolean).length;
    
    return (
      <>
        <h2 className="text-2xl font-bold mb-6 text-center text-white">Your Interests</h2>
        
        <div className="mb-6">
          <label className="block text-gray-200 mb-3">
            Select your interests (click to toggle)
          </label>
          {selectedCount === 0 && (
            <p className="text-amber-400 mb-3 text-sm">Please select at least one interest</p>
          )}
          <div className="grid grid-cols-2 gap-3">
            {Object.keys(interests).map((interest) => (
              <button
                key={interest}
                type="button"
                onClick={() => handleInterestChange(interest)}
                className={`px-4 py-3 rounded-lg transition-all duration-200 capitalize text-left ${
                  interests[interest]
                    ? 'bg-orange-600 text-white'
                    : 'bg-white/5 border border-gray-300/20 text-gray-300'
                }`}
              >
                {interest}
              </button>
            ))}
          </div>
        </div>
      </>
    );
  };
  
  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-900 via-indigo-900 to-purple-900 px-4 py-12 overflow-hidden relative">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden opacity-10">
        <div className="absolute left-1/4 top-1/3 w-64 h-64 bg-purple-400 rounded-full mix-blend-multiply filter blur-xl animate-blob"></div>
        <div className="absolute right-1/4 top-1/2 w-72 h-72 bg-indigo-400 rounded-full mix-blend-multiply filter blur-xl animate-blob animation-delay-2000"></div>
        <div className="absolute left-1/3 bottom-1/4 w-80 h-80 bg-blue-400 rounded-full mix-blend-multiply filter blur-xl animate-blob animation-delay-4000"></div>
      </div>
      
      <div className="w-full max-w-md z-10">
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold mb-3 text-white">DateABase</h1>
          <p className="text-gray-300 text-lg">Connect through experiences, not just profiles</p>
        </div>
        
        <div className="bg-white/10 backdrop-blur-lg p-8 rounded-2xl shadow-2xl border border-white/20">
          {/* Progress steps */}
          <div className="flex items-center justify-between mb-8">
            {[1, 2, 3].map((stepNumber) => (
              <div key={stepNumber} className="flex flex-col items-center">
                <div
                  className={`rounded-full h-10 w-10 flex items-center justify-center text-sm font-medium ${
                    stepNumber === step
                      ? 'bg-purple-600 text-white'
                      : stepNumber < step
                      ? 'bg-green-500 text-white'
                      : 'bg-white/10 text-gray-400'
                  }`}
                >
                  {stepNumber < step ? (
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"></path>
                    </svg>
                  ) : (
                    stepNumber
                  )}
                </div>
                <span className="text-xs mt-1 text-gray-300">
                  {stepNumber === 1 ? 'Account' : stepNumber === 2 ? 'Profile' : 'Interests'}
                </span>
              </div>
            ))}
          </div>
          
          {error && (
            <div className="bg-red-900/50 backdrop-blur-sm border-l-4 border-red-500 text-red-100 p-4 mb-6 rounded-md" role="alert">
              <p>{error}</p>
            </div>
          )}
          
          <form onSubmit={handleSubmit}>
            {step === 1 && renderStep1()}
            {step === 2 && renderStep2()}
            {step === 3 && renderStep3()}
            
            <div className="flex justify-between mt-8">
              {step > 1 ? (
                <button
                  type="button"
                  onClick={prevStep}
                  className="px-4 py-2 bg-transparent border border-gray-300/30 text-gray-300 rounded-lg transition-all duration-200 hover:bg-white/5"
                >
                  Back
                </button>
              ) : (
                <div></div>
              )}
              
              {step < 3 ? (
                <button
                  type="button"
                  onClick={nextStep}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg transition-all duration-200 hover:bg-purple-700"
                >
                  Next
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={loading}
                  className={`px-4 py-2 bg-purple-600 text-white rounded-lg transition-all duration-200 hover:bg-purple-700 ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
                >
                  {loading ? (
                    <span className="flex items-center">
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Creating Account...
                    </span>
                  ) : (
                    'Create Account'
                  )}
                </button>
              )}
            </div>
          </form>
          
          <div className="mt-6 text-center">
            <p className="text-gray-300">
              Already have an account?{' '}
              <Link to="/login" className="text-purple-400 hover:text-purple-300 font-medium transition-colors duration-200">
                Sign In
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register; 