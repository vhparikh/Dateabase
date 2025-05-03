import React, { useState, useEffect } from 'react';
import { API_URL } from '../config';
import axios from 'axios';
import { useCSRFToken } from '../App';


const ProfileImageUpload = ({ userId, onImageUploaded, maxImages = 4 }) => {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const csrfToken = useCSRFToken()

  // Fetch user's images on component mount
  useEffect(() => {
    fetchUserImages();
  }, [userId]);

  const fetchUserImages = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get(`${API_URL}/api/users/images`, {
        withCredentials: true,
        headers: {
          'X-CsrfToken': csrfToken
        }
      });
      
      if (response.status !== 200) {
        throw new Error('Failed to fetch images');
      }
      
      const data = response.data;
      setImages(data);
    } catch (err) {
      console.error('Error fetching user images:', err);
      setError('Failed to load images. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    // Check if file is an image
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file (PNG, JPG, etc.)');
      return;
    }
    
    // Check file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError('Image must be less than 5MB');
      return;
    }
    
    try {
      setUploading(true);
      setError(null);
      
      // Create form data
      const formData = new FormData();
      formData.append('image', file);
      
      // Determine position (if we have fewer than maxImages, use the next available position)
      if (images.length < maxImages) {
        // Find the lowest unused position
        const usedPositions = images.map(img => img.position);
        let nextPosition = 0;
        while (usedPositions.includes(nextPosition) && nextPosition < maxImages) {
          nextPosition++;
        }
        formData.append('position', nextPosition);
      }
      // If we already have maxImages, the backend will replace the oldest one
      
      // Upload the image
      const response = await axios.post(`${API_URL}/api/users/images`, formData, {
        withCredentials: true,
        headers: {
          'X-CsrfToken': csrfToken
        }});
      
      if (response.status !== 200 && response.status !== 201) {
        throw new Error(response.data.detail || 'Failed to upload image');

      }
      
      const data = response.data;
      
      // Update the images state with the new image
      setImages(prevImages => {
        // If we already have an image at this position, replace it
        const newImages = prevImages.filter(img => img.position !== data.image.position);
        return [...newImages, data.image];
      });
      
      // If this is going to be the main profile image (position 0), update the profile_image field
      if (data.image.position === 0) {
        try {
          const updateProfileResponse = await axios.put(`${API_URL}/api/me`, { profile_image: data.image.url }, {
            withCredentials: true,
            headers: {
              'Content-Type': 'application/json',
              'X-CsrfToken': csrfToken
            },
          });
          
          if (updateProfileResponse !== 200) {
            console.error('Failed to update profile image URL');
          }
        } catch (err) {
          console.error('Error updating profile image URL:', err);
        }
      }
      
      // Notify parent component
      if (onImageUploaded) {
        onImageUploaded(data.image);
      }
      
      // Reset file input
      event.target.value = null;
    } catch (err) {
      console.error('Error uploading image:', err);
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };
  
  const handleDeleteImage = async (imageId) => {
    if (!window.confirm('Are you sure you want to delete this image?')) {
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.delete(`${API_URL}/api/users/images/${imageId}`, {
        withCredentials: true,
        headers: {
          'X-CsrfToken': csrfToken
        }
      });
      
      if (response.status !== 200) {
        throw new Error(response.data.detail || 'Failed to delete image');
      }
      
      // Remove the deleted image from state
      setImages(prevImages => prevImages.filter(img => img.id !== imageId));
      
      // Refetch images to ensure we have the latest data
      fetchUserImages();
    } catch (err) {
      console.error('Error deleting image:', err);
      setError(err.message || 'Failed to delete image. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleSetAsProfile = async (imageId) => {
    const image = images.find(img => img.id === imageId);
    if (!image) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.put(`${API_URL}/api/users/images/${imageId}/set-position`, { position: 0 }, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
          'X-CsrfToken': csrfToken
        }
      });
      
      if (response.status !== 200) {
        throw new Error(response.data.detail || 'Failed to update image position');
      }
      
      // Also update the user's profile_image field to use this as the main profile image
      try {
        const updateProfileResponse = await axios.put(`${API_URL}/api/me`, { profile_image: image.url }, {
          withCredentials: true,
          headers: {
            'Content-Type': 'application/json',
            'X-CsrfToken': csrfToken
          },
        });
        
        if (updateProfileResponse.status !== 200) {
          console.error('Failed to update profile image URL, but position was updated');
        }
      } catch (err) {
        console.error('Error updating profile image URL:', err);
      }
      
      // If the parent component needs to know about this change
      if (onImageUploaded) {
        onImageUploaded({...image, position: 0});
      }
      
      // Refetch images to ensure we have the latest data
      fetchUserImages();
    } catch (err) {
      console.error('Error updating image position:', err);
      setError(err.message || 'Failed to update image position. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="profile-image-upload">
      <h3 className="text-lg font-semibold mb-4">Profile Images</h3>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
        {images.sort((a, b) => a.position - b.position).map(image => (
          <div key={image.id} className="relative group">
            <img 
              src={image.url} 
              alt={`Profile ${image.position + 1}`} 
              className="w-full h-40 object-cover rounded-lg"
            />
            <div className="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center">
              <button
                onClick={() => handleSetAsProfile(image.id)}
                disabled={image.position === 0}
                className={`px-2 py-1 bg-blue-500 text-white rounded mr-2 text-xs ${image.position === 0 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-600'}`}
              >
                {image.position === 0 ? 'Main Photo' : 'Set as Main'}
              </button>
              <button
                onClick={() => handleDeleteImage(image.id)}
                className="px-2 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600"
              >
                Delete
              </button>
            </div>
            {image.position === 0 && (
              <div className="absolute top-0 left-0 bg-blue-500 text-white text-xs px-2 py-1 rounded-br">
                Main
              </div>
            )}
          </div>
        ))}
        
        {/* Empty placeholder slots */}
        {Array.from({ length: Math.max(0, maxImages - images.length) }).map((_, index) => (
          <div key={`empty-${index}`} className="border-2 border-dashed border-gray-300 rounded-lg h-40 flex items-center justify-center">
            <span className="text-gray-400">No Image</span>
          </div>
        ))}
      </div>
      
      <div className="mb-4">
        <input
          type="file"
          id="image-upload"
          className="hidden"
          accept="image/*"
          onChange={handleImageUpload}
          disabled={uploading}
        />
        <label
          htmlFor="image-upload"
          className={`inline-block px-4 py-2 bg-orange-500 text-white rounded cursor-pointer hover:bg-orange-600 ${uploading ? 'opacity-50 cursor-wait' : ''}`}
        >
          {uploading ? 'Uploading...' : `Upload ${images.length >= maxImages ? 'New' : 'Image'}`}
        </label>
        <p className="text-sm text-gray-500 mt-2">
          {images.length >= maxImages 
            ? `You have reached the maximum of ${maxImages} images. Uploading a new image will replace the oldest one.` 
            : `You can upload up to ${maxImages} images. ${maxImages - images.length} slots remaining.`}
        </p>
      </div>
    </div>
  );
};

export default ProfileImageUpload; 