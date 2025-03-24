import React, { useContext } from 'react';
import { Navigate } from 'react-router-dom';
import AuthContext from '../context/AuthContext';

const PrivateRoute = ({ children }) => {
  const { user, authTokens } = useContext(AuthContext);
  
  if (!user || !authTokens) {
    // Redirect to login if user is not authenticated
    return <Navigate to="/login" replace />;
  }
  
  // Render children if user is authenticated
  return children;
};

export default PrivateRoute; 