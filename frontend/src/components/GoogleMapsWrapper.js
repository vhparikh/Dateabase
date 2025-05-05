import React from 'react';
import { LoadScript } from '@react-google-maps/api';

// Define libraries array outside component to prevent recreation on each render
const libraries = ["places"];

/**
 * Google Maps API wrapper component
 * This component loads the Google Maps script only once,
 * preventing the "LoadScript has been reloaded unintentionally" warning
 */
const GoogleMapsWrapper = ({ children }) => {
  return (
    <LoadScript 
      googleMapsApiKey={process.env.REACT_APP_GOOGLE_MAPS_API_KEY || ""}
      libraries={libraries}
    >
      {children}
    </LoadScript>
  );
};

export default GoogleMapsWrapper; 