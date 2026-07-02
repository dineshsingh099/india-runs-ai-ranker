import re

def compute_location_score(candidate, jd_location):
    """
    Computes a location score in [0, 1] comparing candidate location against JD location.
    Handles relocation willingness and country match fallbacks.
    """
    profile = candidate.get("profile", {})
    cand_loc = profile.get("location", "")
    cand_country = profile.get("country", "")
    
    # If no JD location or remote/any location is preferred, everyone gets full credit
    if not jd_location or jd_location.lower() in ["remote", "any", "hybrid", "flexible", "onsite"]:
        return 1.0
        
    cand_loc_clean = cand_loc.lower().strip()
    jd_loc_clean = jd_location.lower().strip()
    
    # Check for direct city matching (exact or substring)
    if jd_loc_clean in cand_loc_clean or cand_loc_clean in jd_loc_clean:
        return 1.0
        
    # Check if candidate is willing to relocate
    willing_relocate = candidate.get("redrob_signals", {}).get("willing_to_relocate", False)
    if willing_relocate:
        return 0.80
        
    # Check for country-level compatibility dynamically
    if cand_country:
        if cand_country.lower() in jd_loc_clean:
            return 0.50
            
    # Fallback to check if both are in India
    india_cities = ["pune", "noida", "bangalore", "bengaluru", "chennai", "hyderabad", "mumbai", "delhi", "gurgaon"]
    if cand_country.lower() == "india" and any(c in jd_loc_clean for c in india_cities):
        return 0.50
            
    # Default case (completely different country/location and not willing to relocate)
    return 0.20
