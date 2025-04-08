import React, { useState, useEffect, useContext } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { getExperiences } from '../services/api';
import { API_URL } from '../config';
import AuthContext from '../context/AuthContext';
import { motion } from 'framer-motion';

// Experience card component with orange gradient theme
const ExperienceCard = ({ experience, onEdit, onDelete, readOnly = false }) => {
  const cardVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 }
  };

  // Generate a random gradient for the background if no image
  const randomGradient = () => {
    const gradients = [
      'from-orange-400 to-red-500',
      'from-orange-300 to-orange-600',
      'from-amber-400 to-orange-500', 
      'from-yellow-400 to-orange-500',
      'from-orange-400 to-pink-500',
    ];
    return gradients[Math.floor(Math.random() * gradients.length)];
  };

  const [gradient] = useState(randomGradient());

  return (
    <motion.div 
      className="rounded-xl overflow-hidden shadow-card bg-white"
      variants={cardVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration: 0.3 }}
    >
      {/* Image or gradient header */}
      <div className="relative h-48">
        {experience.location_image ? (
          <img 
            src={experience.location_image}
            alt={experience.location}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className={`w-full h-full bg-gradient-to-r ${gradient} flex items-center justify-center`}>
            <span className="text-white text-2xl font-bold px-4 text-center">{experience.experience_type}</span>
          </div>
        )}
        
        {/* Overlay with location and type */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent text-white p-4">
          <span className="bg-orange-500/80 text-white text-xs px-2 py-1 rounded-full uppercase tracking-wide font-semibold backdrop-blur-sm">
            {experience.experience_type}
          </span>
          <h3 className="text-xl font-bold mt-2">{experience.location}</h3>
        </div>
      </div>
      
      {/* Content section */}
      <div className="p-4">
        <div className="flex justify-between items-start mb-4">
          <div>
            <p className="text-sm text-gray-500 mb-1">Added on {new Date(experience.created_at).toLocaleDateString()}</p>
            {experience.is_active ? (
              <span className="inline-flex items-center bg-green-100 text-green-800 text-xs px-2 py-0.5 rounded-full">
                <span className="w-1.5 h-1.5 bg-green-600 rounded-full mr-1"></span>
                Active
              </span>
            ) : (
              <span className="inline-flex items-center bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full">
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-1"></span>
                Inactive
              </span>
            )}
          </div>
          
          {/* Only show these controls if not in read-only mode */}
          {!readOnly && (
            <div className="flex space-x-2">
              <button 
                onClick={() => onEdit(experience)}
                className="p-1.5 bg-orange-100 text-orange-700 rounded-full hover:bg-orange-200 transition-colors"
                aria-label="Edit experience"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
              </button>
              <button 
                onClick={() => onDelete(experience.id)}
                className="p-1.5 bg-red-100 text-red-700 rounded-full hover:bg-red-200 transition-colors"
                aria-label="Delete experience"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          )}
        </div>
        
        {/* Description */}
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-1">Description</h4>
          <p className="text-gray-600">
            {experience.description || 'No description provided.'}
          </p>
        </div>
        
        {/* Additional details */}
        <div className="border-t border-orange-100 pt-3 mt-3">
          <div className="flex flex-wrap gap-2">
            {experience.tags && experience.tags.map((tag, index) => (
              <span key={index} className="bg-orange-50 text-orange-800 rounded-full px-2 py-0.5 text-xs">
                {tag}
              </span>
            ))}
            {(!experience.tags || experience.tags.length === 0) && (
              <span className="text-sm text-gray-500">No tags</span>
            )}
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
    location: '',
    description: '',
    is_active: true,
    tags: [],
    location_image: ''
  });
  
  const [errors, setErrors] = useState({});
  const [tagInput, setTagInput] = useState('');
  
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
        location: experience.location || '',
        description: experience.description || '',
        is_active: experience.is_active !== undefined ? experience.is_active : true,
        tags: experience.tags || [],
        location_image: experience.location_image || ''
      });
    } else {
      // Reset form for new experience
      setFormData({
        experience_type: '',
        location: '',
        description: '',
        is_active: true,
        tags: [],
        location_image: ''
      });
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
  
  const addTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, tagInput.trim()]
      }));
      setTagInput('');
    }
  };
  
  const removeTag = (tagToRemove) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };
  
  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.experience_type) {
      newErrors.experience_type = 'Experience type is required';
    }
    
    if (!formData.location) {
      newErrors.location = 'Location is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Form submitted', formData);
    
    if (validateForm()) {
      console.log('Form validated, calling onSave');
      onSave(formData);
    } else {
      console.log('Form validation failed', errors);
    }
  };
  
  const handleButtonClick = () => {
    // Explicitly validate the form and call onSave if valid
    if (validateForm()) {
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
          
          {/* Location */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Location*
            </label>
            <input
              type="text"
              name="location"
              value={formData.location}
              onChange={handleChange}
              placeholder="e.g., Central Park, New York"
              className={`w-full px-3 py-2 border ${errors.location ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500`}
            />
            {errors.location && (
              <p className="text-red-500 text-xs mt-1">{errors.location}</p>
            )}
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
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
            ></textarea>
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
          
          {/* Tags */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tags
            </label>
            <div className="flex">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                placeholder="Add a tag"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
              <button
                type="button"
                onClick={addTag}
                className="px-3 py-2 bg-gradient-to-r from-orange-start to-orange-end text-white rounded-r-lg"
              >
                Add
              </button>
            </div>
            
            {/* Tag list */}
            <div className="flex flex-wrap gap-2 mt-2">
              {formData.tags.map((tag, index) => (
                <span 
                  key={index} 
                  className="inline-flex items-center bg-orange-100 text-orange-800 rounded-full px-2 py-1 text-sm"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => removeTag(tag)}
                    className="ml-1 text-orange-600 hover:text-orange-800"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </span>
              ))}
              {formData.tags.length === 0 && (
                <span className="text-sm text-gray-500">No tags added yet</span>
              )}
            </div>
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
  
  // We'll let the server's session authentication handle redirects
  
  const fetchExperiences = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Use the session-based API service
      const response = await getExperiences();
      
      if (response.data) {
        setExperiences(response.data);
      }
      
      setLoading(false);
    } catch (err) {
      console.error('Error fetching experiences:', err);
      setError('Failed to load experiences. Please try again.');
      setLoading(false);
    }
  };
  
  useEffect(() => {
    if (location.state?.shouldCallAddExperience) {
      handleAddExperience();
    }
  }, [location.state]);
  
  useEffect(() => {
    fetchExperiences();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Call once on component mount
  
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
        const response = await fetch(`${API_URL}/api/experiences/${experienceData.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          credentials: 'include',
          body: JSON.stringify(experienceData)
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to update experience');
        }
      } else {
        // POST request for creating a new experience
        console.log('Creating new experience');
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
        
        const data = await response.json();
        console.log('Experience created successfully:', data);
        if (data) {
          setExperiences(prev => [data.experience, ...prev]);
        }
      }
      
      // Refresh experiences after save
      fetchExperiences();
      
      setIsModalOpen(false);
      setLoading(false);
    } catch (err) {
      console.error('Error saving experience:', err);
      setError('Failed to save experience. Please try again.');
      setLoading(false);
    }
  };
  
  const openDeleteConfirmation = (experienceId) => {
    setDeleteModal({ isOpen: true, experienceId });
  };
  
  const handleDeleteExperience = async (experienceId) => {
    try {
      setLoading(true);
      
      // Session will handle authentication
      
      // Real API call with session authentication
      await fetch(`${API_URL}/api/experiences/${experienceId}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      
      fetchExperiences();
      setDeleteModal({ isOpen: false, experienceId: null });
      setLoading(false);
    } catch (err) {
      console.error('Error deleting experience:', err);
      setError('Failed to delete experience. Please try again.');
      setLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100 py-6">
      <div className="max-w-5xl mx-auto px-4 sm:px-6">
        
        {/* Header */}
        <div className="mb-6">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-800">Your Experiences</h1>
          </div>
          <p className="text-gray-600 mt-2">Share your favorite places and activities</p>
        </div>
        
        {/* Add Experience button */}
        <div className="flex justify-end mb-6">
          <button
            onClick={handleAddExperience}
            className="px-4 py-2 bg-gradient-to-r from-orange-start to-orange-end text-white rounded-lg shadow-sm hover:shadow-md transition-all flex items-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Add Experience
          </button>
        </div>
        
        {/* Content */}
        {loading && experiences.length === 0 ? (
          <div className="text-center py-16">
            <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-orange-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading your experiences...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center max-w-md mx-auto">
            <p className="text-red-600 mb-2">{error}</p>
            <button 
              onClick={fetchExperiences}
              className="px-4 py-2 bg-white border border-red-300 rounded-md text-red-600 text-sm hover:bg-red-50"
            >
              Try Again
            </button>
          </div>
        ) : experiences.length === 0 ? (
          <EmptyState onAddClick={handleAddExperience} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {experiences.map(experience => (
              <ExperienceCard 
                key={experience.id} 
                experience={experience}
                onEdit={handleEditExperience}
                onDelete={openDeleteConfirmation}
              />
            ))}
          </div>
        )}
      </div>
      
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
