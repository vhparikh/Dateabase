import React, { useState, useEffect, useContext, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { API_URL } from '../config';
import AuthContext from '../context/AuthContext';
import { motion } from 'framer-motion';
import axios from 'axios';
import { useCSRFToken } from '../App';
import { GoogleMap, LoadScript, Marker, Autocomplete } from '@react-google-maps/api';

// Experience card component
const ExperienceCard = ({ experience, onEdit, onDelete, readOnly = false }) => {
  // Function to get a random gradient
  const randomGradient = () => {
    const gradients = [
      'from-orange-500 to-amber-500',
      'from-orange-400 to-orange-600',
      'from-amber-400 to-red-400',
      'from-orange-300 to-orange-500'
    ];
    return gradients[Math.floor(Math.random() * gradients.length)];
  };
  
  // Generate Google Maps Static Map URL for small preview
  const [staticMapUrl, setStaticMapUrl] = useState(null);
  
  useEffect(() => {
    // Only generate map URL if coordinates are available
    if (experience.latitude && experience.longitude) {
      const url = `https://maps.googleapis.com/maps/api/staticmap?center=${experience.latitude},${experience.longitude}&zoom=14&size=400x200&markers=color:orange%7C${experience.latitude},${experience.longitude}&key=${process.env.REACT_APP_GOOGLE_MAPS_API_KEY}`;
      setStaticMapUrl(url);
    } else {
      setStaticMapUrl(null);
    }
  }, [experience]);
  
  // Function to change badge color based on experience type
  const badgeColor = (type) => {
    const colors = {
      'Restaurant': 'bg-red-100 text-red-700',
      'Cafe': 'bg-orange-100 text-orange-700',
      'Bar': 'bg-purple-100 text-purple-700',
      'Park': 'bg-green-100 text-green-700',
      'Museum': 'bg-blue-100 text-blue-700',
      'Theater': 'bg-indigo-100 text-indigo-700',
      'Concert': 'bg-pink-100 text-pink-700',
      'Hiking': 'bg-teal-100 text-teal-700',
      'Beach': 'bg-cyan-100 text-cyan-700',
      'Shopping': 'bg-amber-100 text-amber-700',
      'Sports': 'bg-lime-100 text-lime-700',
      'Festival': 'bg-fuchsia-100 text-fuchsia-700',
      'Class': 'bg-yellow-100 text-yellow-700',
      'Club': 'bg-violet-100 text-violet-700'
    };
    return colors[type] || 'bg-gray-100 text-gray-700';
  };
  
  // Handle image error
  const handleImageError = () => {
    // Fallback to a default image based on the experience type
    return `https://source.unsplash.com/featured/?${encodeURIComponent(experience.experience_type || 'experience')}`;
  };
  
  // Function to open Google Maps directions
  const openDirections = () => {
    if (experience.latitude && experience.longitude) {
      window.open(`https://www.google.com/maps/dir/?api=1&destination=${experience.latitude},${experience.longitude}`);
    } else {
      window.open(`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(experience.location)}`);
    }
  };
  
  return (
    <motion.div 
      className="w-full bg-white rounded-xl shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Card image */}
      <div className="h-48 bg-gray-200 relative overflow-hidden">
        {experience.location_image ? (
          <img 
            src={experience.location_image} 
            alt={experience.location}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = handleImageError();
            }}
          />
        ) : (
          <div className={`w-full h-full bg-gradient-to-r ${randomGradient()} flex items-center justify-center p-4`}>
            <span className="text-white text-xl font-medium text-center">
              {experience.experience_type || 'Experience'}
            </span>
          </div>
        )}
        
        {/* Experience type badge */}
        <div className="absolute top-2 left-2">
          <span className={`inline-block px-3 py-1 text-xs font-medium rounded-full ${experience.experience_type ? badgeColor(experience.experience_type) : 'bg-gray-100 text-gray-800'}`}>
            {experience.experience_type || 'Other'}
          </span>
        </div>
      </div>
      
      <div className="p-4">
        <div className="flex justify-between items-start mb-3">
          <h3 className="text-lg font-bold text-gray-800">{experience.experience_name || experience.place_name || experience.location}</h3>
          
          {!readOnly && (
            <div className="flex items-center space-x-1">
              <button 
                onClick={() => onEdit(experience)}
                className="text-blue-600 hover:text-blue-800 transition-colors"
                aria-label="Edit"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
              <button 
                onClick={() => onDelete(experience.id)}
                className="text-red-600 hover:text-red-800 transition-colors"
                aria-label="Delete"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          )}
        </div>
        
        {/* Location with directions button */}
        <div className="text-sm text-gray-600 mb-3 flex items-center justify-between">
          <div className="flex items-center">
            <svg className="h-4 w-4 text-orange-500 mr-1 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span>{experience.place_name ? experience.location : ''}</span>
          </div>
          <button 
            onClick={openDirections}
            className="text-xs bg-blue-50 hover:bg-blue-100 text-blue-600 px-2 py-1 rounded-md flex items-center transition-colors"
          >
            <svg className="h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
            Directions
          </button>
        </div>
        
        {/* Static map if coordinates available */}
        {staticMapUrl && (
          <div className="mb-3 rounded-lg overflow-hidden border border-gray-200">
            <img 
              src={staticMapUrl} 
              alt={`Map of ${experience.location}`}
              className="w-full h-36 object-cover"
            />
          </div>
        )}
        
        <p className="text-gray-700 text-sm mb-3">
          {experience.description || "No description provided."}
        </p>
        
        {/* Additional details */}
        <div className="border-t border-orange-100 pt-3 mt-3">
          <div className="text-xs text-gray-500">
            Added {new Date(experience.created_at).toLocaleDateString()}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

// Experience modal for adding/editing
const ExperienceModal = ({ isOpen, onClose, onSave, experience = null }) => {
  const [formData, setFormData] = useState({
    experience_type: '',
    experience_name: '',
    location: '',
    description: '',
    latitude: null,
    longitude: null,
    place_id: '',
    place_name: '',
    location_image: '',
    is_active: true
  });
  
  const [errors, setErrors] = useState({});
  const [tagInput, setTagInput] = useState('');
  const autocompleteRef = useRef(null);
  const [mapCenter, setMapCenter] = useState(null);
  
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
  
  // Experience types dropdown options
  const experienceTypes = [
    'Restaurant', 'Cafe', 'Bar', 'Park', 'Museum', 
    'Theater', 'Concert', 'Hiking', 'Beach', 'Shopping',
    'Sports', 'Festival', 'Class', 'Club', 'Other'
  ];
  
  useEffect(() => {
    if (experience) {
      setFormData({
        id: experience.id,
        experience_type: experience.experience_type || '',
        experience_name: experience.experience_name || '',
        location: experience.location || '',
        description: experience.description || '',
        latitude: experience.latitude || null,
        longitude: experience.longitude || null,
        place_id: experience.place_id || '',
        place_name: experience.place_name || '',
        location_image: experience.location_image || '',
        is_active: experience.is_active !== undefined ? experience.is_active : true
      });
      
      // Set map center if coordinates are available
      if (experience.latitude && experience.longitude) {
        setMapCenter({
          lat: experience.latitude,
          lng: experience.longitude
        });
      } else {
        setMapCenter(null);
      }
    } else {
      // Reset form for new experience
      setFormData({
        experience_type: '',
        experience_name: '',
        location: '',
        description: '',
        latitude: null,
        longitude: null,
        place_id: '',
        place_name: '',
        location_image: '',
        is_active: true
      });
      setMapCenter(null);
    }
    
    setErrors({});
    setTagInput('');
  }, [experience, isOpen]);
  
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Clear error for this field if it exists
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };
  
  // Handle place selection from Google Places Autocomplete
  const onPlaceSelected = (place) => {
    if (place && place.geometry && place.geometry.location) {
      const lat = place.geometry.location.lat();
      const lng = place.geometry.location.lng();
      const formattedAddress = place.formatted_address || place.name || '';
      const placeName = place.name || '';
      
      // Create updated form data
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
      
      setFormData(updatedFormData);
      
      setMapCenter({
        lat,
        lng
      });
      
      // Clear location error if it exists
      if (errors.location) {
        setErrors(prev => ({ ...prev, location: '' }));
      }
    }
  };
  
  const validateForm = async () => {
    const newErrors = {};
    
    if (!formData.experience_type) {
      newErrors.experience_type = 'Experience type is required';
    }
    
    if (!formData.location) {
      newErrors.location = 'Location is required';
    }

    if(await isInappropriate(formData.description)) {
      newErrors.description = 'Description contains inappropriate content';
    } 
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log('Form submitted', formData);

    if (await validateForm()) {
      console.log('Form validated, calling onSave');
      onSave(formData);
    } else {
      console.log('Form validation failed', errors);
    }
  };

  const isInappropriate = async (text) => {
    console.log('Checking for inappropriate content:', text);
    try {
      const response = await axios.post(`${API_URL}/api/check-inappropriate`, text, {
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
        credentials: 'include'
      });
      
      if (response.status !== 200) {
        throw new Error(`Server returned ${response.status}`);
      }
      
      const data = response.data;
      return data.is_inappropriate;
    } catch (error) {
      console.error("Error checking inappropriate content:", error);
      // Fallback: if error, assume not inappropriate
      return false;
    }
  };
  
  const handleButtonClick = async () => {
  // Explicitly validate the form and call onSave if valid
  if (await validateForm()) {
    console.log('Submit button clicked, form validated');
    onSave(formData);
  } else {
    console.log('Submit button clicked, validation failed', errors);
  }
};
  
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="border-b border-orange-100 px-6 py-4 flex justify-between items-center sticky top-0 bg-white z-10">
          <h2 className="text-xl font-bold text-gray-800">
            {experience ? 'Edit Experience' : 'Add New Experience'}
          </h2>
          <button 
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6">
          {/* Experience Type */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Experience Type*
            </label>
            <select
              name="experience_type"
              value={formData.experience_type}
              onChange={handleChange}
              className={`w-full px-3 py-2 border ${errors.experience_type ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500`}
            >
              <option value="">Select an experience type</option>
              {experienceTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
            {errors.experience_type && (
              <p className="text-red-500 text-xs mt-1">{errors.experience_type}</p>
            )}
          </div>
          
          {/* Experience Name */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Experience Name
            </label>
            <input
              type="text"
              name="experience_name"
              value={formData.experience_name}
              onChange={handleChange}
              placeholder="Give your experience a memorable name"
              className={`w-full px-3 py-2 border ${errors.experience_name ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500`}
            />
            {errors.experience_name && (
              <p className="text-red-500 text-xs mt-1">{errors.experience_name}</p>
            )}
          </div>
          
          {/* Location with Google Places Autocomplete */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Location*
            </label>
            <LoadScript 
              googleMapsApiKey={process.env.REACT_APP_GOOGLE_MAPS_API_KEY}
              libraries={["places"]}
            >
              <div className="relative">
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
                    type="text"
                    name="location"
                    value={formData.location}
                    onChange={handleChange}
                    placeholder="Search for a location..."
                    className={`w-full px-3 py-2 border ${errors.location ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500`}
                  />
                </Autocomplete>
                {errors.location && (
                  <p className="text-red-500 text-xs mt-1">{errors.location}</p>
                )}
              </div>
              
              {/* Map preview */}
              {mapCenter && (
                <div className="mt-3">
                  <GoogleMap
                    mapContainerStyle={mapContainerStyle}
                    center={mapCenter}
                    zoom={15}
                    options={mapOptions}
                  >
                    <Marker position={mapCenter} />
                  </GoogleMap>
                </div>
              )}
            </LoadScript>
          </div>
          
          {/* Description */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Describe this experience..."
              rows="3"
              className={`w-full px-3 py-2 border ${errors.description ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500`}
            ></textarea>
            {errors.description && (
              <p className="text-red-500 text-xs mt-1">{errors.description}</p>
            )}
          </div>
          
          {/* Location Image */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Location Image URL
            </label>
            <input
              type="text"
              name="location_image"
              value={formData.location_image}
              onChange={handleChange}
              placeholder="https://example.com/image.jpg"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
            />
            <p className="text-xs text-gray-500 mt-1">Leave empty for a color gradient</p>
          </div>
          
          {/* Active Status */}
          <div className="mb-6">
            <label className="flex items-center">
              <input
                type="checkbox"
                name="is_active"
                checked={formData.is_active}
                onChange={handleChange}
                className="rounded text-orange-600 focus:ring-orange-500 h-4 w-4"
              />
              <span className="ml-2 text-sm text-gray-700">Active (visible to others)</span>
            </label>
          </div>
          
          {/* Form actions */}
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="button" /* Changed from 'submit' to 'button' to prevent default form submission */
              onClick={handleButtonClick}
              className="px-4 py-2 bg-gradient-to-r from-orange-start to-orange-end text-white rounded-lg shadow-sm hover:shadow-md transition-all"
            >
              {experience ? 'Save Changes' : 'Add Experience'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Empty state component
const EmptyState = ({ onAddClick }) => (
  <div className="bg-white rounded-xl shadow-card border border-orange-100 p-8 text-center max-w-md mx-auto">
    <div className="inline-flex items-center justify-center w-16 h-16 bg-orange-100 rounded-full mb-4">
      <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    </div>
    <h3 className="text-xl font-bold text-gray-800 mb-2">No experiences added</h3>
    <p className="text-gray-600 mb-6">Add your favorite spots, activities, and places you'd like to share.</p>
    <button 
      onClick={onAddClick}
      className="px-6 py-3 bg-gradient-to-r from-orange-start to-orange-end text-white font-medium rounded-lg shadow-md hover:shadow-lg transition-all inline-block"
    >
      Add Your First Experience
    </button>
  </div>
);

// Delete confirmation modal
const DeleteConfirmationModal = ({ isOpen, onClose, onConfirm, experienceId }) => {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4">Confirm Deletion</h3>
        <p className="text-gray-600 mb-6">Are you sure you want to delete this experience? This action cannot be undone.</p>
        
        <div className="flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={() => onConfirm(experienceId)}
            className="px-4 py-2 bg-red-600 text-white rounded-lg shadow-sm hover:bg-red-700"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
};

const Experiences = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);
  const [experiences, setExperiences] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentExperience, setCurrentExperience] = useState(null);
  const [deleteModal, setDeleteModal] = useState({ isOpen: false, experienceId: null });

  const csrfToken = useCSRFToken();

  // Fetch user's experiences when component mounts
  useEffect(() => {
    const fetchExperiences = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_URL}/api/my-experiences`, { withCredentials: true });
        if (response.status !== 200) {
          throw new Error('Failed to fetch experiences');
        }
        const data = response.data;
        setExperiences(data);
        setError('');
      } catch (err) {
        console.error('Error fetching experiences:', err);
        setError('Failed to fetch experiences. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchExperiences();
  }, []);

  const handleAddExperience = () => {
    setCurrentExperience(null);
    setIsModalOpen(true);
  };

  const handleEditExperience = (experience) => {
    setCurrentExperience(experience);
    setIsModalOpen(true);
  };

  const handleSaveExperience = async (experienceData) => {
    try {
      setLoading(true);
      setError('');
      
      console.log('Attempting to save experience:', experienceData);
      
      // Real API call for saving with session authentication
      if (experienceData.id) {
        // PUT request for updating an experience
        const response = await axios.put(`${API_URL}/api/experiences/${experienceData.id}`, experienceData, {
          withCredentials: true,
          headers: {
            'Content-Type': 'application/json',
            'X-CsrfToken': csrfToken
          }
        });
        
        if (response.status !== 200) {
          const errorData = response.data;
          throw new Error(errorData.detail || 'Failed to update experience');
        }
        
        const data = response.data;
        console.log('Experience updated successfully:', data);
        if (data) {
          setExperiences(prev => prev.map(exp => 
            exp.id === experienceData.id ? data.experience : exp
          ));
        }
      } else {
        // POST request for creating a new experience
        console.log('Creating new experience');
        const response = await axios.post(`${API_URL}/api/experiences`, experienceData, {
          withCredentials: true,
          headers: {
            'Content-Type': 'application/json',
            'X-CsrfToken': csrfToken
          }
        });
        
        if (response.status !== 200) {
          const errorData = response.data;
          throw new Error(errorData.detail || 'Failed to create experience');
        }
        
        const data = response.data;
        console.log('Experience created successfully:', data);
        if (data) {
          setExperiences(prev => [data.experience, ...prev]);
        }
      }
      
      // Refresh experiences after save
      const fetchExperiences = async () => {
        try {
          setLoading(true);
          const response = await axios.get(`${API_URL}/api/my-experiences`, { withCredentials: true });
          if (response.status !== 200) {
            throw new Error('Failed to fetch experiences');
          }
          const data = response.data;
          setExperiences(data);
          setError('');
        } catch (err) {
          console.error('Error fetching experiences:', err);
          setError('Failed to fetch experiences. Please try again later.');
        } finally {
          setLoading(false);
        }
      };
      fetchExperiences();
      
      setIsModalOpen(false);
      setLoading(false);
    } catch (err) {
      console.error('Error saving experience:', err);
      setError('Failed to save experience. Please try again.');
      setLoading(false);
    }
  };

  const handleDeleteExperience = async (experienceId) => {
    try {
      setLoading(true);
      
      // Make DELETE request to delete the experience
      const response = await axios.delete(`${API_URL}/api/experiences/${experienceId}`, { withCredentials: true });
      
      if (response.status !== 200) {
        const errorData = response.data;
        throw new Error(errorData.detail || 'Failed to delete experience');
      }
      
      // Refresh experiences after successful deletion
      const fetchExperiences = async () => {
        try {
          setLoading(true);
          const response = await axios.get(`${API_URL}/api/my-experiences`, { withCredentials: true });
          if (response.status !== 200) {
            throw new Error('Failed to fetch experiences');
          }
          const data = response.data;
          setExperiences(data);
          setError('');
        } catch (err) {
          console.error('Error fetching experiences:', err);
          setError('Failed to fetch experiences. Please try again later.');
        } finally {
          setLoading(false);
        }
      };
      
      fetchExperiences();
      setDeleteModal({ isOpen: false, experienceId: null });
      setLoading(false);
    } catch (err) {
      console.error('Error deleting experience:', err);
      setError('Failed to delete experience. Please try again.');
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">Experiences</h1>

      {/* Add Experience button */}
      <div className="flex justify-end mb-6">
        <button
          onClick={handleAddExperience}
          className="px-4 py-2 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-lg shadow-sm hover:shadow-md transition-all flex items-center"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Add Experience
        </button>
      </div>

      {experiences.length === 0 ? (
        <EmptyState onAddClick={handleAddExperience} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {experiences.map(experience => (
            <ExperienceCard
              key={experience.id}
              experience={experience}
              onEdit={handleEditExperience}
              onDelete={handleDeleteExperience}
            />
          ))}
        </div>
      )}

      {/* Modals */}
      <ExperienceModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveExperience}
        experience={currentExperience}
      />
      
      <DeleteConfirmationModal 
        isOpen={deleteModal.isOpen}
        onClose={() => setDeleteModal({ isOpen: false, experienceId: null })}
        onConfirm={handleDeleteExperience}
        experienceId={deleteModal.experienceId}
      />
    </div>
  );
};

export default Experiences;
