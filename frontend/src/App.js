import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import CodeSubmission from "./components/CodeSubmission";
import ReviewProgress from "./components/ReviewProgress";
import ReviewResult from "./components/ReviewResult";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
const API = `${BACKEND_URL}/api`;

const CodeReviewApp = () => {
  const [currentStep, setCurrentStep] = useState('submit'); // submit, review, results
  const [submissionId, setSubmissionId] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [reviewStatus, setReviewStatus] = useState(null);
  const [reviewData, setReviewData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Check review status periodically
  useEffect(() => {
    let interval;
    if (sessionId && currentStep === 'review') {
      interval = setInterval(async () => {
        try {
          const response = await axios.get(`${API}/review-status/${sessionId}`);
          setReviewStatus(response.data);
          
          if (response.data.status === 'completed') {
            // Get full review result
            const resultResponse = await axios.get(`${API}/review-result/${sessionId}`);
            setReviewData(resultResponse.data);
            setCurrentStep('results');
            clearInterval(interval);
          } else if (response.data.status === 'failed') {
            setError('Review failed. Please try again.');
            clearInterval(interval);
          }
        } catch (err) {
          console.error('Error checking review status:', err);
        }
      }, 3000); // Check every 3 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [sessionId, currentStep]);

  const handleCodeSubmission = async (codeData) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Submit code
      const submitResponse = await axios.post(`${API}/submit-code`, codeData);
      const submission = submitResponse.data;
      setSubmissionId(submission.id);
      
      // Start review
      const reviewResponse = await axios.post(`${API}/start-review/${submission.id}`);
      setSessionId(reviewResponse.data.session_id);
      setCurrentStep('review');
      
    } catch (err) {
      console.error('Error submitting code:', err);
      setError(err.response?.data?.detail || 'Failed to submit code for review');
    } finally {
      setIsLoading(false);
    }
  };

  const handleHumanFeedback = async (feedbackData) => {
    try {
      await axios.post(`${API}/human-feedback/${sessionId}`, feedbackData);
      // Refresh review data to include new feedback
      const resultResponse = await axios.get(`${API}/review-result/${sessionId}`);
      setReviewData(resultResponse.data);
    } catch (err) {
      console.error('Error submitting human feedback:', err);
      throw err;
    }
  };

  const resetApp = () => {
    setCurrentStep('submit');
    setSubmissionId(null);
    setSessionId(null);
    setReviewStatus(null);
    setReviewData(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-6xl mx-auto py-8 px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Multi-LLM Code Review System
          </h1>
          <p className="text-lg text-gray-600">
            Get your code reviewed by Gemini, GPT-4o, and DeepSeek R1
          </p>
          {currentStep !== 'submit' && (
            <button
              onClick={resetApp}
              className="mt-4 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
            >
              Start New Review
            </button>
          )}
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Progress indicator */}
        <div className="flex justify-center mb-8">
          <div className="flex items-center space-x-4">
            <div className={`flex items-center ${currentStep === 'submit' ? 'text-blue-600 font-semibold' : 'text-gray-400'}`}>
              <span className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium mr-2 ${
                currentStep === 'submit' ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-600'
              }`}>1</span>
              Submit Code
            </div>
            <div className="w-8 h-0.5 bg-gray-300"></div>
            <div className={`flex items-center ${currentStep === 'review' ? 'text-blue-600 font-semibold' : 'text-gray-400'}`}>
              <span className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium mr-2 ${
                currentStep === 'review' ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-600'
              }`}>2</span>
              Review in Progress
            </div>
            <div className="w-8 h-0.5 bg-gray-300"></div>
            <div className={`flex items-center ${currentStep === 'results' ? 'text-blue-600 font-semibold' : 'text-gray-400'}`}>
              <span className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium mr-2 ${
                currentStep === 'results' ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-600'
              }`}>3</span>
              Review Results
            </div>
          </div>
        </div>

        {/* Main content */}
        {currentStep === 'submit' && (
          <CodeSubmission 
            onSubmit={handleCodeSubmission} 
            isLoading={isLoading} 
          />
        )}

        {currentStep === 'review' && (
          <ReviewProgress 
            status={reviewStatus?.status || 'pending'} 
            reviewDetails={reviewStatus} 
          />
        )}

        {currentStep === 'results' && (
          <ReviewResult 
            reviewData={reviewData} 
            onHumanFeedback={handleHumanFeedback}
          />
        )}
      </div>
    </div>
  );
};

const Home = () => {
  const helloWorldApi = async () => {
    try {
      const response = await axios.get(`${API}/`);
      console.log(response.data.message);
    } catch (e) {
      console.error(e, `errored out requesting / api`);
    }
  };

  useEffect(() => {
    helloWorldApi();
  }, []);

  return <CodeReviewApp />;
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />}>
            <Route index element={<Home />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
