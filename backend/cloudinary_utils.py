import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import current_app
import logging

# Configure Cloudinary
def init_cloudinary():
    """Initialize Cloudinary with credentials from environment variables"""
    try:
        # Cloudinary automatically reads from the CLOUDINARY_URL environment variable
        cloudinary_url = os.environ.get('CLOUDINARY_URL')
        
        if not cloudinary_url:
            # Log warning but don't fail (for local development)
            print("CLOUDINARY_URL not found in environment variables. Image uploads won't work.")
            return False
        
        # Standard format for Cloudinary URL is: cloudinary://api_key:api_secret@cloud_name
        # Let's print explicit initialization info for debugging
        print(f"Initializing Cloudinary with environment variables...")
        
        # This will use CLOUDINARY_URL from the environment automatically
        cloudinary.config()  # No args needed, it reads CLOUDINARY_URL env var by default
        
        # Test that the config worked by retrieving some properties
        config = cloudinary.config()
        print(f"Cloudinary initialized with cloud_name: {config.cloud_name}")
        return True
    except Exception as e:
        logging.error(f"Error initializing Cloudinary: {e}")
        return False

def upload_image(file_to_upload, public_id=None, folder="user_profiles"):
    """
    Upload an image to Cloudinary
    
    Args:
        file_to_upload: File object to upload
        public_id: Optional custom public ID
        folder: Folder in Cloudinary to store the image (default: user_profiles)
        
    Returns:
        Dictionary with upload results including 'secure_url' for the uploaded image
    """
    try:
        # Print debug info
        print(f"Starting image upload to Cloudinary...")
        
        # Verify Cloudinary config
        config = cloudinary.config()
        if not config.cloud_name:
            print("Cloudinary not properly configured - missing cloud_name")
            return {
                "success": False,
                "error": "Cloudinary not properly configured"
            }
        
        # Set up optional parameters
        options = {
            "folder": folder,
            "overwrite": True,
            "resource_type": "image"
        }
        
        # Add public_id if provided
        if public_id:
            options["public_id"] = public_id
        
        print(f"Uploading to Cloudinary with options: {options}")
        
        # For Flask FileStorage objects, we need to read the file data
        # Check if file_to_upload is a FileStorage object (from Flask)
        if hasattr(file_to_upload, 'read') and callable(file_to_upload.read):
            print(f"File appears to be a file-like object, reading data")
            # File is a file-like object (e.g., from Flask's request.files)
            file_data = file_to_upload.read()
            file_to_upload.seek(0)  # Reset file pointer for potential reuse
            # Upload the image as raw data and get the result
            upload_result = cloudinary.uploader.upload(file_data, **options)
        else:
            # Direct upload of the provided data
            upload_result = cloudinary.uploader.upload(file_to_upload, **options)
        
        print(f"Upload successful! Result: {upload_result}")
        
        return {
            "success": True,
            "secure_url": upload_result.get("secure_url"),
            "public_id": upload_result.get("public_id"),
            "version": upload_result.get("version"),
            "format": upload_result.get("format")
        }
    except Exception as e:
        print(f"Error uploading image to Cloudinary: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

def delete_image(public_id):
    """
    Delete an image from Cloudinary
    
    Args:
        public_id: Public ID of the image to delete
        
    Returns:
        Boolean indicating success or failure
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get("result") == "ok"
    except Exception as e:
        logging.error(f"Error deleting image from Cloudinary: {e}")
        return False

def get_user_images(public_ids):
    """
    Get details for multiple images by their public IDs
    
    Args:
        public_ids: List of public IDs to retrieve
        
    Returns:
        List of image details
    """
    if not public_ids:
        return []
        
    try:
        results = []
        for public_id in public_ids:
            if public_id:  # Skip empty IDs
                result = cloudinary.api.resource(public_id)
                results.append({
                    "public_id": result.get("public_id"),
                    "url": result.get("secure_url"),
                    "format": result.get("format"),
                    "version": result.get("version"),
                    "created_at": result.get("created_at")
                })
        return results
    except Exception as e:
        logging.error(f"Error retrieving images from Cloudinary: {e}")
        return []
