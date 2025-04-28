import React, { useState, useContext, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import AuthContext from '../context/AuthContext';
import { API_URL } from '../config';
import { GoogleMap, LoadScript, Marker } from '@react-google-maps/api';
import { Autocomplete } from '@react-google-maps/api';


// Define common experience types
const experienceTypes = [
  'Coffee',
  'Study Session',
  'Dinner',
  'Movie',
  'Hiking',
  'Concert',
  'Museum',
  'Sports',
  'Shopping',
  'Volunteering',
  'Other'
];

// Common locations around Princeton
const suggestedLocations = [
  'Small World Coffee',
  'Frist Campus Center',
  'Firestone Library',
  'Princeton Art Museum',
  'Nassau Street',
  'Palmer Square',
  'Princeton Stadium',
  'Forbes College',
  'Mathey College',
  'Whitman College',
  'Princeton Garden Theatre',
  'Institute Woods'
];

const CreateExperience = () => {
  // Check if user is authenticated
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  
  // We'll let the server's session authentication redirect if needed
  
  const autocompleteRef = useRef(null);
  
  const [formData, setFormData] = useState({
    experience_type: '',
    location: '',
    description: '',
    latitude: null,
    longitude: null,
    place_id: null,
    location_image: '',
  });
  const [customType, setCustomType] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [showLocationSuggestions, setShowLocationSuggestions] = useState(false);
  const [backgroundImage, setBackgroundImage] = useState('');
  const [userProfileImage, setUserProfileImage] = useState(null);
  const [mapCenter, setMapCenter] = useState({
    lat: 40.3431, // Default to Princeton's latitude
    lng: -74.6551, // Default to Princeton's longitude
  });
  
  // Map configuration
  const mapContainerStyle = {
    width: '100%',
    height: '200px',
    borderRadius: '8px',
    marginTop: '10px',
  };
  
  const mapOptions = {
    disableDefaultUI: true,
    zoomControl: true,
  };
  
  // Fetch user profile image when component mounts
  useEffect(() => {
    const fetchUserProfile = async () => {
      if (user?.id || user?.sub) {
        try {
          const userId = user?.id || user?.sub;
          // Use fetch instead of axios directly
          const response = await fetch(`${API_URL}/users/${userId}`);
          const data = await response.json();
          
          if (data && data.profile_image) {
            setUserProfileImage(data.profile_image);
          } else {
            // Use placeholder or generated avatar if no profile image
            setUserProfileImage(`https://ui-avatars.com/api/?name=${user.username || 'User'}&background=orange&color=fff`);
          }
        } catch (err) {
          console.error('Error fetching user profile:', err);
          setUserProfileImage(`https://ui-avatars.com/api/?name=${user.username || 'User'}&background=orange&color=fff`);
        }
      }
    };
    
    fetchUserProfile();
  }, [user]);
  
  // Fetch a location image when location changes
  useEffect(() => {
    // Only fetch a new image if we have a location and don't already have an image
    if (formData.location && formData.location.length > 3 && !formData.location_image && !backgroundImage) {
      const fetchLocationImage = async () => {
        // Create a consistent image URL based on the location
        const locationForImage = formData.location.split(',')[0].trim();
        const imageUrl = `https://source.unsplash.com/random/800x600/?${locationForImage.replace(/\s+/g, '+')}`;
        
        // Store the image URL both in the UI state and the form data for submission
        setBackgroundImage(imageUrl);
        setFormData(prevData => ({
          ...prevData,
          location_image: imageUrl
        }));
      };
      
      fetchLocationImage();
    }
  }, [formData.location, formData.location_image, backgroundImage]);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
    
    if (name === 'location' && !autocompleteRef.current) {
      setShowLocationSuggestions(value.length > 0);
    }
  };
  
  // Handle place selection from Google Places Autocomplete
  const onPlaceSelected = (place) => {
    if (place && place.geometry && place.geometry.location) {
      const lat = place.geometry.location.lat();
      const lng = place.geometry.location.lng();
      const formattedAddress = place.formatted_address || place.name || '';
      const placeName = place.name || '';
      
      // Setup initial form data with location info
      const updatedFormData = {
        ...formData,
        location: formattedAddress,
        place_name: placeName,
        latitude: lat,
        longitude: lng,
        place_id: place.place_id || null
      };
      
      // Get a location image and add it to the form data
      let imageUrl = '';
      let shouldFetchImage = true;
      
      // First try to get a Google Maps photo if available
      if (place.photos && place.photos.length > 0) {
        try {
          imageUrl = place.photos[0].getUrl({ maxWidth: 800, maxHeight: 600 });
          shouldFetchImage = false;
        } catch (error) {
          console.error('Error getting place photo:', error);
          shouldFetchImage = true;
        }
      }
      
      // If we couldn't get a Google photo, fetch from Unsplash
      if (shouldFetchImage) {
        const locationForImage = placeName || formattedAddress.split(',')[0].trim();
        imageUrl = `https://source.unsplash.com/random/800x600/?${locationForImage.replace(/\s+/g, '+')}`;
      }
      
      // Set the location image in form data for submission
      updatedFormData.location_image = imageUrl;
      setBackgroundImage(imageUrl);
      
      setFormData(updatedFormData);
      setMapCenter({
        lat,
        lng
      });
      
      setShowLocationSuggestions(false);
    }
  };
  
  const handleTypeChange = (e) => {
    const value = e.target.value;
    if (value === 'Other') {
      setFormData({
        ...formData,
        experience_type: 'Other'
      });
    } else {
      setFormData({
        ...formData,
        experience_type: value
      });
    }
  };
  
  const handleCustomTypeChange = (e) => {
    setCustomType(e.target.value);
  };
  
  const selectSuggestedLocation = (location) => {
    setFormData({
      ...formData,
      location
    });
    setShowLocationSuggestions(false);
  };
  
  const createExperience = async (experienceData) => {
    try {
      // Use fetch directly with credentials: 'include' to ensure cookies are sent
      const response = await fetch(`${API_URL}/api/experiences`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(experienceData)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create experience');
      }
      
      return await response.json();
    } catch (error) {
      console.error('API error creating experience:', error);
      throw error;
    }
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      // Let the session authentication handle authorization
      const finalFormData = {
        ...formData,
        experience_type: formData.experience_type === 'Other' ? customType : formData.experience_type
      };
      
      if (!finalFormData.experience_type) {
        throw new Error('Please select or enter an experience type');
      }
      
      if (!finalFormData.location) {
        throw new Error('Please enter a location');
      }
      
      console.log('Submitting experience:', finalFormData);
      
      try {
        const result = await createExperience(finalFormData);
        console.log('Experience created successfully:', result);
        setSuccess(true);
        
        // Redirect after a short delay to show success message
        setTimeout(() => {
          navigate('/experiences');
        }, 1500);
      } catch (submitError) {
        console.error('Experience creation failed:', submitError);
        setError(submitError.message || 'Failed to create experience');
      }
    } catch (err) {
      console.error('Create experience error:', err);
      setError(err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to create experience');
    } finally {
      setLoading(false);
    }
  };
  
  // Filter location suggestions based on input
  const filteredLocations = suggestedLocations.filter(location => 
    location.toLowerCase().includes(formData.location.toLowerCase())
  );
  
  return (
    <div className="container mx-auto mt-10 px-4 pb-20 max-w-4xl">
      <h1 className="text-3xl font-bold text-center text-gray-800 mb-2">Create New Experience</h1>
      <p className="text-center text-gray-600 mb-8">Share an experience you'd like to enjoy with someone</p>
      
      <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
        <div className="grid md:grid-cols-2">
          {/* Preview Panel */}
          <div className="bg-slate-900 text-white">
            <div className="h-full relative min-h-[400px]">
              {/* Background image or gradient */}
              {backgroundImage ? (
                <div 
                  className="absolute inset-0 bg-cover bg-center opacity-15" 
                  style={{ backgroundImage: `url('${backgroundImage}')` }}
                />
              ) : (
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-800 to-purple-900 opacity-50" />
              )}
              
              {/* Solid overlay to improve text readability */}
              <div className="absolute inset-0 bg-gradient-to-b from-slate-900/80 via-slate-800/80 to-slate-900/90"></div>
              
              {/* Content container */}
              <div className="relative h-full flex flex-col p-8 z-10">
                {/* Preview badge */}
                <div className="mb-6">
                  <span className="inline-block px-3 py-1 rounded-full bg-orange-600 text-xs font-semibold text-white">
                    PREVIEW
                  </span>
                </div>
                
                {/* Header section */}
                <div className="mb-8">
                  {/* Experience type heading */}
                  <h2 className="text-3xl font-bold mb-3 text-white drop-shadow-sm">
                    {formData.experience_type === 'Other' 
                      ? (customType || 'Custom Experience Type') 
                      : (formData.experience_type || 'Select an Experience Type')}
                  </h2>
                  
                  {/* Location with better background */}
                  <div className="inline-flex items-center bg-slate-800/90 px-3 py-2 rounded-lg">
                    <svg className="w-5 h-5 mr-2 text-orange-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" 
                        d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" 
                        d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <span className="text-orange-100 font-medium">
                      {formData.location || 'Location'}
                    </span>
                  </div>
                </div>
                
                {/* Location image if available */}
                {backgroundImage && (
                  <div className="mb-4 rounded-lg overflow-hidden shadow-lg">
                    <img 
                      src={backgroundImage} 
                      alt={formData.location || 'Location'} 
                      className="w-full h-32 object-cover"
                    />
                  </div>
                )}
                
                {/* Description section with solid background */}
                <div className="mt-auto">
                  <div className="bg-slate-800/95 backdrop-blur-sm rounded-xl p-5 mb-4">
                    <p className="text-gray-100 line-clamp-4">
                      {formData.description || 'Add a description of your experience here...'}
                    </p>
                  </div>
                  
                  {/* Creator profile display */}
                  <div className="flex items-center justify-between mt-4">
                    <div className="flex items-center">
                      {userProfileImage && (
                        <div className="w-10 h-10 rounded-full overflow-hidden mr-3">
                          <img 
                            src={userProfileImage} 
                            alt={user?.username || 'User'} 
                            className="w-full h-full object-cover"
                          />
                        </div>
                      )}
                      <div>
                        <p className="text-sm font-medium text-white">{user?.username || 'User'}</p>
                        <p className="text-xs text-gray-400">Creator</p>
                      </div>
                    </div>
                    
                    {/* Category tag */}
                    <span className="bg-orange-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium shadow-sm">
                      {formData.experience_type === 'Other' 
                        ? (customType || 'Custom Type') 
                        : (formData.experience_type || 'Category')}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Form Panel */}
          <div className="p-8">
            {error && (
              <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded" role="alert">
                <p className="font-bold">Error</p>
                <p>{error}</p>
              </div>
            )}
            
            {success && (
              <div className="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-6 rounded" role="alert">
                <p className="font-bold">Success!</p>
                <p>Your experience has been created. Redirecting...</p>
              </div>
            )}
            
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-gray-700 text-sm font-semibold mb-2" htmlFor="experience_type">
                  Experience Type
                </label>
                <select
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-colors"
                  id="experience_type"
                  name="experience_type"
                  value={formData.experience_type}
                  onChange={handleTypeChange}
                  required
                >
                  <option value="">Select an experience type</option>
                  {experienceTypes.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>
              
              {formData.experience_type === 'Other' && (
                <div>
                  <label className="block text-gray-700 text-sm font-semibold mb-2" htmlFor="custom_type">
                    Custom Experience Type
                  </label>
                  <input
                    className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-colors"
                    type="text"
                    id="custom_type"
                    name="custom_type"
                    value={customType}
                    onChange={handleCustomTypeChange}
                    placeholder="Enter your custom experience type"
                    required
                  />
                </div>
              )}
              
              <div className="relative">
                <label className="block text-gray-700 text-sm font-semibold mb-2" htmlFor="location">
                  Location
                </label>
                
                <LoadScript 
                  googleMapsApiKey={process.env.REACT_APP_GOOGLE_MAPS_API_KEY}
                  libraries={["places"]}
                >
                  <Autocomplete
                    onLoad={autocomplete => {
                      autocompleteRef.current = autocomplete;
                    }}
                    onPlaceChanged={() => {
                      if (autocompleteRef.current) {
                        onPlaceSelected(autocompleteRef.current.getPlace());
                      }
                    }}
                    options={{
                      types: ["establishment", "geocode"],
                      fields: ["place_id", "formatted_address", "geometry", "name", "photos"]
                    }}
                  >
                    <input
                      className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-colors"
                      type="text"
                      id="location"
                      name="location"
                      value={formData.location}
                      onChange={handleChange}
                      placeholder="Search for a location..."
                      required
                    />
                  </Autocomplete>
                  
                  {/* Map display when location is selected */}
                  {formData.latitude && formData.longitude && (
                    <div className="mt-3">
                      <GoogleMap
                        mapContainerStyle={mapContainerStyle}
                        center={mapCenter}
                        zoom={15}
                        options={mapOptions}
                      >
                        <Marker position={mapCenter} />
                      </GoogleMap>
                      {formData.place_id && (
                        <p className="text-xs text-gray-500 mt-1">
                          Selected location: {formData.location}
                        </p>
                      )}
                    </div>
                  )}
                </LoadScript>
                
                {/* Legacy location suggestions as fallback */}
                {!autocompleteRef.current && showLocationSuggestions && filteredLocations.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {filteredLocations.map(location => (
                      <div
                        key={location}
                        className="px-4 py-2 hover:bg-orange-50 cursor-pointer"
                        onClick={() => selectSuggestedLocation(location)}
                      >
                        {location}
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              <div>
                <label className="block text-gray-700 text-sm font-semibold mb-2" htmlFor="description">
                  Description
                </label>
                <textarea
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-colors"
                  id="description"
                  name="description"
                  rows="4"
                  value={formData.description}
                  onChange={handleChange}
                  placeholder="Describe your experience"
                ></textarea>
              </div>
              
              <div className="flex items-center justify-end space-x-4 pt-4">
                <Link
                  to="/"
                  className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
                >
                  Cancel
                </Link>
                <button
                  type="submit"
                  className={`px-6 py-3 bg-orange-gradient text-white rounded-lg font-medium transition-colors ${
                    loading ? 'opacity-70 cursor-not-allowed' : ''
                  }`}
                  disabled={loading}
                >
                  {loading ? (
                    <div className="flex items-center">
                      <div className="w-5 h-5 border-t-2 border-white border-solid rounded-full animate-spin mr-2"></div>
                      Creating...
                    </div>
                  ) : 'Create Experience'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateExperience; 