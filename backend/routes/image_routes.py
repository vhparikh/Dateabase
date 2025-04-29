from flask import Blueprint, request, jsonify, current_app
from flask_cors import CORS
from functools import wraps
from datetime import datetime
import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
from ..database import db, User, UserImage

from ..utils.auth_utils import login_required

image_bp = Blueprint('image_bp', __name__)

CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL', '')
if CLOUDINARY_URL:
    cloudinary.config(secure=True)
else:
    print("Warning: CLOUDINARY_URL not set. Image uploads will not work.")

@image_bp.route('/api/users/images', methods=['POST'])
@login_required()
def upload_user_image(current_user_id=None):
    """
    Upload a user profile image to Cloudinary and save the URL to the database.
    Users can have up to 4 images. If a user already has 4 images, the oldest one will be replaced.
    """
    try:
        # Check if the request contains a file
        if 'image' not in request.files:
            return jsonify({'detail': 'No image file provided'}), 400
            
        image_file = request.files['image']
        
        # Check if the file is valid
        if image_file.filename == '':
            return jsonify({'detail': 'No image file selected'}), 400
            
        # Check if the content type is an image
        if not image_file.content_type.startswith('image/'):
            return jsonify({'detail': 'File must be an image'}), 400
            
        # Get user's existing images
        user_images = UserImage.query.filter_by(user_id=current_user_id).order_by(UserImage.created_at).all()
        
        # Calculate position for the new image
        position = request.form.get('position')
        if position is not None:
            try:
                position = int(position)
                if position < 0 or position > 3:
                    return jsonify({'detail': 'Position must be between 0 and 3'}), 400
            except ValueError:
                return jsonify({'detail': 'Position must be a number between 0 and 3'}), 400
        else:
            # If no position provided, use the next available position
            existing_positions = [img.position for img in user_images]
            for pos in range(4):  # Try positions 0-3
                if pos not in existing_positions:
                    position = pos
                    break
            else:
                # If all positions are taken, replace the oldest image
                position = user_images[0].position
                # Delete the oldest image
                old_image = user_images[0]
                
                # Delete from Cloudinary
                try:
                    cloudinary.uploader.destroy(old_image.public_id)
                except Exception as e:
                    print(f"Error deleting image from Cloudinary: {e}")
                
                # Delete from database
                db.session.delete(old_image)
                db.session.commit()
        
        # Upload the file to Cloudinary
        upload_result = cloudinary.uploader.upload(
            image_file,
            folder=f"dateabase/users/{current_user_id}",
            public_id=f"profile_{position}_{datetime.utcnow().timestamp()}"
        )
        
        # Create a new UserImage
        new_image = UserImage(
            user_id=current_user_id,
            image_url=upload_result['secure_url'],
            public_id=upload_result['public_id'],
            position=position
        )
        
        # If this is the first image or position is 0, also set it as the user's primary profile image
        if position == 0 or len(user_images) == 0:
            user = User.query.get(current_user_id)
            user.profile_image = upload_result['secure_url']
        
        db.session.add(new_image)
        db.session.commit()
        
        return jsonify({
            'message': 'Image uploaded successfully',
            'image': {
                'id': new_image.id,
                'url': new_image.image_url,
                'position': new_image.position,
                'created_at': new_image.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        print(f"Error uploading image: {e}")
        db.session.rollback()
        return jsonify({'detail': str(e)}), 500
        
@image_bp.route('/api/users/images', methods=['GET'])
@login_required()
def get_user_images(current_user_id=None):
    """Get all images for the current user."""
    try:
        user_images = UserImage.query.filter_by(user_id=current_user_id).order_by(UserImage.position).all()
        
        images = []
        for img in user_images:
            images.append({
                'id': img.id,
                'url': img.image_url,
                'position': img.position,
                'created_at': img.created_at.isoformat()
            })
            
        return jsonify(images)
    except Exception as e:
        print(f"Error getting user images: {e}")
        return jsonify({'detail': str(e)}), 500
        
@image_bp.route('/api/users/images/<int:image_id>', methods=['DELETE'])
@login_required()
def delete_user_image(image_id, current_user_id=None):
    """Delete a user image."""
    try:
        # Get the image
        image = UserImage.query.get(image_id)
        if not image:
            return jsonify({'detail': 'Image not found'}), 404
            
        # Check if the user owns the image
        if image.user_id != current_user_id:
            return jsonify({'detail': 'You can only delete your own images'}), 403
            
        # Delete from Cloudinary
        try:
            cloudinary.uploader.destroy(image.public_id)
        except Exception as e:
            print(f"Error deleting image from Cloudinary: {e}")
            
        # If this is the primary profile image, clear it
        user = User.query.get(current_user_id)
        if user.profile_image == image.image_url:
            # Find another image to use as the profile image
            other_image = UserImage.query.filter(
                UserImage.user_id == current_user_id,
                UserImage.id != image_id
            ).first()
            
            if other_image:
                user.profile_image = other_image.image_url
            else:
                user.profile_image = None
        
        # Delete from database
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({'message': 'Image deleted successfully'}), 200
    except Exception as e:
        print(f"Error deleting image: {e}")
        db.session.rollback()
        return jsonify({'detail': str(e)}), 500

@image_bp.route('/api/users/images/<int:image_id>/set-position', methods=['PUT'])
@login_required()
def update_image_position(image_id, current_user_id=None):
    """Update the position of a user image."""
    try:
        # Get the position from the request
        data = request.json
        if 'position' not in data:
            return jsonify({'detail': 'Position is required'}), 400
            
        position = data['position']
        if not isinstance(position, int) or position < 0 or position > 3:
            return jsonify({'detail': 'Position must be a number between 0 and 3'}), 400
            
        # Get the image
        image = UserImage.query.get(image_id)
        if not image:
            return jsonify({'detail': 'Image not found'}), 404
            
        # Check if the user owns the image
        if image.user_id != current_user_id:
            return jsonify({'detail': 'You can only update your own images'}), 403
            
        # If there's already an image at the requested position, swap positions
        existing_image = UserImage.query.filter(
            UserImage.user_id == current_user_id,
            UserImage.position == position,
            UserImage.id != image_id
        ).first()
        
        if existing_image:
            existing_image.position = image.position
            
        # Update the position
        image.position = position
        
        # If this is position 0, also set it as the primary profile image
        if position == 0:
            user = User.query.get(current_user_id)
            user.profile_image = image.image_url
            
        db.session.commit()
        
        return jsonify({
            'message': 'Image position updated',
            'image': {
                'id': image.id,
                'url': image.image_url,
                'position': image.position
            }
        })
    except Exception as e:
        print(f"Error updating image position: {e}")
        db.session.rollback()
        return jsonify({'detail': str(e)}), 500