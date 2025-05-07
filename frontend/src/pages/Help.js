import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useCSRFToken } from '../App';
import { API_URL } from '../config';

const Help = () => {
  const [helpData, setHelpData] = useState(null);
  const [faqData, setFaqData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const csrfToken = useCSRFToken();

  useEffect(() => {
    const fetchHelpData = async () => {
      try {
        setLoading(true);
        setError(false);
        
        // Fetch help content from the API
        const helpResponse = await axios.get(`${API_URL}/api/help`, {
          headers: {
            'X-CSRFToken': csrfToken
          },
          withCredentials: true
        });
        
        if (helpResponse.data) {
          setHelpData(helpResponse.data);
        }
        
        try {
          // Also fetch FAQ data - in a nested try/catch to not fail the whole component
          const faqResponse = await axios.get(`${API_URL}/api/help/faq`, {
            headers: {
              'X-CSRFToken': csrfToken
            },
            withCredentials: true
          });
          
          if (faqResponse.data) {
            setFaqData(faqResponse.data);
          }
        } catch (faqError) {
          console.error('Error fetching FAQ data:', faqError);
          // Don't set the main error state, just continue without FAQ data
        }
      } catch (error) {
        console.error('Error fetching help data:', error);
        setError(true);
        // If API fails, we'll fall back to static content (already in the render)
      } finally {
        setLoading(false);
      }
    };

    if (csrfToken) {
      fetchHelpData();
    } else {
      // If no CSRF token is available yet, just stop loading
      setLoading(false);
    }
  }, [csrfToken]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-orange-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading help content...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6 max-w-4xl">
      <h1 className="text-3xl font-bold text-orange-600 mb-6">Help & User Guide</h1>
      
      {error && (
        <div className="bg-orange-50 border border-orange-300 text-orange-700 px-4 py-3 rounded mb-6" role="alert">
          <p>We're having trouble loading the help content. Showing static content instead.</p>
        </div>
      )}
      
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-2xl font-semibold text-orange-500 mb-4">Getting Started</h2>
        <p className="mb-4">
          {helpData?.sections?.[0]?.content || 
            "Welcome to DateABase! This application helps Princeton students find and match with others based on shared experiences. Here's how to get the most out of the platform:"}
        </p>
        
        <ol className="list-decimal pl-5 space-y-2 mb-4">
          {helpData?.sections?.[0]?.steps && helpData.sections[0].steps.length > 0 ? 
            helpData.sections[0].steps.map((step, index) => (
              <li key={index}>
                <strong>{step.split('-')[0]}</strong>
                {step.includes('-') ? '- ' + step.split('-')[1] : ''}
              </li>
            )) : (
            <>
              <li><strong>Complete Your Profile</strong> - Make sure your profile is complete with your preferences and images to get better matches.</li>
              <li><strong>Add Experiences</strong> - Share the places and activities you've enjoyed around Princeton.</li>
              <li><strong>Swipe</strong> - Discover experiences from other users and express interest.</li>
              <li><strong>Connect</strong> - Check your matches and start conversations with people who share your interests.</li>
            </>
          )}
        </ol>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Map through section data from API if available, otherwise use static content */}
        {helpData?.sections && helpData.sections.length > 1 ? 
          helpData.sections.slice(1).map((section, index) => (
            <div className="bg-white rounded-lg shadow-md p-6" key={index}>
              <h2 className="text-xl font-semibold text-orange-500 mb-3">
                <span className="inline-block w-8 h-8 bg-orange-100 text-orange-600 rounded-full text-center leading-8 mr-2">{index + 1}</span>
                {section.title}
              </h2>
              <p className="mb-3">{section.content}</p>
              <ul className="list-disc pl-5 space-y-1">
                {section.steps.map((step, stepIndex) => (
                  <li key={stepIndex}>{step}</li>
                ))}
              </ul>
            </div>
          )) : (
          <>
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-orange-500 mb-3">
                <span className="inline-block w-8 h-8 bg-orange-100 text-orange-600 rounded-full text-center leading-8 mr-2">1</span>
                Experiences
              </h2>
              <p className="mb-3">Create and manage your experiences:</p>
              <ul className="list-disc pl-5 space-y-1">
                <li>Click on "Experiences" in the navigation</li>
                <li>Add new experiences with the "Add Experience" button</li>
                <li>Fill in details like location, type, and description</li>
                <li>Edit or delete your experiences as needed</li>
              </ul>
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-orange-500 mb-3">
                <span className="inline-block w-8 h-8 bg-orange-100 text-orange-600 rounded-full text-center leading-8 mr-2">2</span>
                Swiping
              </h2>
              <p className="mb-3">Discover experiences from other users:</p>
              <ul className="list-disc pl-5 space-y-1">
                <li>Go to the "Swipe" tab to see experiences</li>
                <li>Swipe right or click the heart to like an experience</li>
                <li>Swipe left or click X to pass</li>
                <li>Click on the card to see more details</li>
              </ul>
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-orange-500 mb-3">
                <span className="inline-block w-8 h-8 bg-orange-100 text-orange-600 rounded-full text-center leading-8 mr-2">3</span>
                Matches
              </h2>
              <p className="mb-3">Connect with your matches:</p>
              <ul className="list-disc pl-5 space-y-1">
                <li>Visit the "Matches" tab to see your connections</li>
                <li>Matches are grouped by user and shared experiences</li>
                <li>View contact information for your matches</li>
                <li>Reach out to start a conversation!</li>
              </ul>
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-orange-500 mb-3">
                <span className="inline-block w-8 h-8 bg-orange-100 text-orange-600 rounded-full text-center leading-8 mr-2">4</span>
                Profile
              </h2>
              <p className="mb-3">Manage your profile:</p>
              <ul className="list-disc pl-5 space-y-1">
                <li>Access your profile from the navigation menu</li>
                <li>Add or update your profile pictures</li>
                <li>Edit your personal information</li>
                <li>Update your preferences in the settings</li>
              </ul>
            </div>
          </>
        )}
      </div>
      
      <div className="bg-white rounded-lg shadow-md p-6 mt-6">
        <h2 className="text-2xl font-semibold text-orange-500 mb-4">Tips & Best Practices</h2>
        <ul className="list-disc pl-5 space-y-2">
          {helpData?.tips && helpData.tips.length > 0 ? 
            helpData.tips.map((tip, index) => (
              <li key={index}>
                <strong>{tip.split('-')[0]}</strong>
                {tip.includes('-') ? '- ' + tip.split('-')[1] : ''}
              </li>
            )) : (
            <>
              <li><strong>Add Detailed Experiences</strong> - The more information you provide about your experiences, the better your matches will be.</li>
              <li><strong>Upload Clear Photos</strong> - Having good profile images helps other users connect with you.</li>
              <li><strong>Check Regularly</strong> - New users and experiences are added all the time!</li>
              <li><strong>Be Respectful</strong> - When reaching out to matches, remember to be courteous and respectful.</li>
            </>
          )}
        </ul>
      </div>
      
      {/* FAQ Section - only show if data is available */}
      {faqData && faqData.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6 mt-6">
          <h2 className="text-2xl font-semibold text-orange-500 mb-4">Frequently Asked Questions</h2>
          <div className="space-y-4">
            {faqData.map((faq, index) => (
              <div key={index} className="border-b border-orange-100 pb-4 last:border-0">
                <h3 className="font-medium text-lg text-orange-600 mb-2">{faq.question}</h3>
                <p className="text-gray-700">{faq.answer}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Help; 