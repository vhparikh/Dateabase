import React, { useState, useEffect, useRef } from 'react';
import { getProfileImages, uploadProfileImage, deleteProfileImage } from '../services/api';

const ProfileImageGallery = ({ userProfile, onImagesUpdated }) => {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [currentSlide, setCurrentSlide] = useState(0);
  const fileInputRef = useRef(null);

  // Fetch profile images when component mounts
  useEffect(() => {
    fetchProfileImages();
  }, []);

  const fetchProfileImages = async () => {
    try {
      setLoading(true);
      const response = await getProfileImages();
      if (response.data.profile_images) {
        setImages(response.data.profile_images);
      }
      setLoading(false);
    } catch (err) {
      setError('Failed to load profile images');
      setLoading(false);
      console.error('Error loading profile images:', err);
    }
  };

  const handleUploadClick = () => {
    // Trigger file input click
    fileInputRef.current.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Check if file is an image
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file');
      return;
    }

    // Check file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError('Image must be less than 5MB');
      return;
    }

    try {
      setUploading(true);
      setError('');

      console.log('Creating FormData with file:', file.name, file.type, file.size);
      const formData = new FormData();
      formData.append('image', file);

      console.log('Sending request to upload profile image...');
      const response = await uploadProfileImage(formData);
      console.log('Upload response received:', response);
      
      // Add new image to state
      if (response.data) {
        console.log('Upload successful, refreshing images...');
        await fetchProfileImages(); // Refresh images from the server
        
        // Notify parent component
        if (onImagesUpdated) {
          onImagesUpdated();
        }
      }
      
      setUploading(false);
    } catch (err) {
      console.error('Error uploading image:', err);
      console.error('Error details:', err.response ? err.response.data : 'No response data');
      console.error('Error status:', err.response ? err.response.status : 'No status');
      setError(`Upload failed: ${err.response?.data?.detail || err.message || 'Unknown error'}`);
      setUploading(false);
    }
  };

  const handleDeleteImage = async (imageId) => {
    if (!window.confirm('Are you sure you want to delete this image?')) {
      return;
    }

    try {
      setLoading(true);
      await deleteProfileImage(imageId);
      
      // Remove image from state
      setImages(images.filter(img => img.public_id !== imageId));
      
      // Adjust current slide if needed
      if (currentSlide >= images.length - 1) {
        setCurrentSlide(Math.max(0, images.length - 2));
      }
      
      // Notify parent component
      if (onImagesUpdated) {
        onImagesUpdated();
      }
      
      setLoading(false);
    } catch (err) {
      setError('Failed to delete image');
      setLoading(false);
      console.error('Error deleting image:', err);
    }
  };

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev === images.length - 1 ? 0 : prev + 1));
  };

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev === 0 ? images.length - 1 : prev - 1));
  };

  return (
    <div className="mb-8">
      <h3 className="text-lg font-medium text-gray-700 mb-2">Profile Photos</h3>
      
      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm">
          {error}
        </div>
      )}
      
      <div className="bg-orange-50 rounded-lg p-4 border border-orange-100">
        {loading ? (
          <div className="flex justify-center items-center h-48">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-orange-500"></div>
          </div>
        ) : images.length > 0 ? (
          <div className="relative">
            {/* Image carousel */}
            <div className="relative h-64 overflow-hidden rounded-lg">
              {images.map((image, index) => (
                <div
                  key={image.public_id}
                  className={`absolute w-full h-full transition-opacity duration-300 ${
                    index === currentSlide ? 'opacity-100' : 'opacity-0'
                  }`}
                  style={{ display: index === currentSlide ? 'block' : 'none' }}
                >
                  <img
                    src={image.url}
                    alt={`Profile ${index + 1}`}
                    className="w-full h-full object-cover"
                  />
                  <button
                    onClick={() => handleDeleteImage(image.public_id)}
                    className="absolute top-2 right-2 bg-white rounded-full p-1 shadow-md hover:bg-red-50"
                    title="Delete image"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
            
            {/* Navigation arrows - only if more than one image */}
            {images.length > 1 && (
              <>
                <button
                  onClick={prevSlide}
                  className="absolute left-0 top-1/2 transform -translate-y-1/2 bg-white/70 p-2 rounded-r-lg shadow-md hover:bg-white"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
                <button
                  onClick={nextSlide}
                  className="absolute right-0 top-1/2 transform -translate-y-1/2 bg-white/70 p-2 rounded-l-lg shadow-md hover:bg-white"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </>
            )}
            
            {/* Indicator dots */}
            <div className="flex justify-center mt-4 space-x-2">
              {images.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentSlide(index)}
                  className={`w-2 h-2 rounded-full ${
                    index === currentSlide ? 'bg-orange-500' : 'bg-gray-300'
                  }`}
                />
              ))}
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-48 bg-gray-50 rounded-lg border border-dashed border-gray-300">
            <p className="text-gray-500 mb-4">No profile photos yet</p>
          </div>
        )}
        
        {/* Upload button */}
        <div className="mt-4 flex justify-center">
          <button
            onClick={handleUploadClick}
            disabled={uploading || images.length >= 4}
            className={`flex items-center px-4 py-2 rounded-lg shadow-sm font-medium ${
              uploading || images.length >= 4
                ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-orange-start to-orange-end text-white hover:from-orange-600 hover:to-orange-500'
            }`}
          >
            {uploading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white mr-2"></div>
                Uploading...
              </>
            ) : (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0l-4 4m4-4v12" />
                </svg>
                {images.length >= 4 ? 'Maximum 4 photos' : 'Upload Photo'}
              </>
            )}
          </button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/*"
            className="hidden"
          />
        </div>
        
        {/* Image counter */}
        <div className="text-center mt-2 text-sm text-gray-500">
          {images.length}/4 photos
        </div>
      </div>
    </div>
  );
};

export default ProfileImageGallery;
