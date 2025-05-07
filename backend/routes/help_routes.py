from flask import Blueprint, jsonify
from ..utils.auth_utils import login_required

help_bp = Blueprint('help', __name__, url_prefix='/api/help')

# Sample help data - this can be expanded or modified as needed
help_data = {
    "sections": [
        {
            "title": "Getting Started",
            "content": "Welcome to DateABase! This application helps Princeton students find and match with others based on shared experiences.",
            "steps": [
                "Complete your profile with your preferences and images to get better matches.",
                "Add experiences - Share the places and activities you've enjoyed around Princeton.",
                "Swipe - Discover experiences from other users and express interest.",
                "Connect - Check your matches and start conversations with people who share your interests."
            ]
        },
        {
            "title": "Experiences",
            "content": "Create and manage your experiences:",
            "steps": [
                "Click on 'Experiences' in the navigation",
                "Add new experiences with the 'Add Experience' button",
                "Fill in details like location, type, and description",
                "Edit or delete your experiences as needed"
            ]
        },
        {
            "title": "Swiping",
            "content": "Discover experiences from other users:",
            "steps": [
                "Go to the 'Swipe' tab to see experiences",
                "Swipe right or click the heart to like an experience",
                "Swipe left or click X to pass",
                "Click on the card to see more details"
            ]
        },
        {
            "title": "Matches",
            "content": "Connect with your matches:",
            "steps": [
                "Visit the 'Matches' tab to see your connections",
                "Matches are grouped by user and shared experiences",
                "View contact information for your matches",
                "Reach out to start a conversation!"
            ]
        },
        {
            "title": "Profile",
            "content": "Manage your profile:",
            "steps": [
                "Access your profile from the navigation menu",
                "Add or update your profile pictures",
                "Edit your personal information",
                "Update your preferences in the settings"
            ]
        }
    ],
    "tips": [
        "Add detailed experiences - The more information you provide about your experiences, the better your matches will be.",
        "Upload clear photos - Having good profile images helps other users connect with you.",
        "Check regularly - New users and experiences are added all the time!",
        "Be respectful - When reaching out to matches, remember to be courteous and respectful."
    ],
    "contact": {
        "email": "support@dateabase.princeton.edu",
        "message": "If you have any questions or encounter any issues while using DateABase, please reach out to our support team."
    }
}

# FAQ data
faq_data = [
    {
        "question": "How does matching work?",
        "answer": "When you 'like' an experience, the system checks if the owner of that experience has also liked one of your experiences. If so, it's a match! You'll be able to see each other's contact information."
    },
    {
        "question": "Can I edit my experiences after creating them?",
        "answer": "Yes! Go to the 'Experiences' tab, find the experience you want to edit, and click the edit (pencil) icon."
    },
    {
        "question": "How many experiences can I create?",
        "answer": "There's no hard limit on the number of experiences you can create. However, we recommend focusing on quality over quantity."
    },
    {
        "question": "How can I delete my account?",
        "answer": "Please contact support at support@dateabase.princeton.edu to request account deletion."
    },
    {
        "question": "What information is shared when I match with someone?",
        "answer": "When you match, both users can see each other's profile information, including name, profile pictures, and contact details you've provided."
    }
]

@help_bp.route('', methods=['GET'])
@login_required()
def get_help_content(current_user_id):
    """Get help content for the application"""
    return jsonify(help_data)

@help_bp.route('/faq', methods=['GET'])
@login_required()
def get_faq(current_user_id):
    """Get frequently asked questions"""
    return jsonify(faq_data)

# Additional route that can handle any id
@help_bp.route('/<path:path>', methods=['GET'])
@login_required()
def get_help_fallback(path, current_user_id):
    """Fallback route for any help related requests"""
    # Just return the main help data for any path
    return jsonify(help_data) 