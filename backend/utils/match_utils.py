import json

def get_match_reason(user, experience, metadata):
    """Generate a human-readable reason why this experience might be a good match for the user"""
    
    # Only check for experience type match - simplify the matching
    if user.experience_type_prefs and experience.experience_type:
        try:
            # Try as JSON object
            exp_prefs = json.loads(user.experience_type_prefs)
            if isinstance(exp_prefs, dict) and exp_prefs.get(experience.experience_type, False):
                return f"Matches your preference for {experience.experience_type} experiences"
        except (json.JSONDecodeError, TypeError):
            # Try as string (fallback)
            if isinstance(user.experience_type_prefs, str):
                if experience.experience_type in user.experience_type_prefs:
                    return f"Matches your preference for {experience.experience_type} experiences"
    
    # Default reason
    return "Experience you might like"