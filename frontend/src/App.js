import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import CodeSubmission from "./components/CodeSubmission";
import ReviewProgress from "./components/ReviewProgress";
import ReviewResult from "./components/ReviewResult";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
const API = `${BACKEND_URL}/api`;

const CodeGenerationApp = () => {
  const [currentStep, setCurrentStep] = useState('generate'); // generate, process, results
  const [requestId, setRequestId] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [generationStatus, setGenerationStatus] = useState(null);
  const [generationData, setGenerationData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Check generation status periodically
  useEffect(() => {
    let interval;
    if (requestId && currentStep === 'process') {
      interval = setInterval(async () => {
        try {
          const response = await axios.get(`${API}/generation-status/${requestId}`);
          setGenerationStatus(response.data);
          
          if (response.data.status === 'completed') {
            // Get full generation result
            if (response.data.session_id) {
              const resultResponse = await axios.get(`${API}/generation-result/${response.data.session_id}`);
              setGenerationData(resultResponse.data);
              setSessionId(response.data.session_id);
              setCurrentStep('results');
            }
            clearInterval(interval);
          } else if (response.data.status === 'failed') {
            setError('Code generation failed. Please try again.');
            clearInterval(interval);
          }
        } catch (err) {
          console.error('Error checking generation status:', err);
        }
      }, 3000); // Check every 3 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [requestId, currentStep]);

  const handleCodeGeneration = async (generationRequest) => {
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('Sending generation request:', generationRequest);
      const response = await axios.post(`${API}/generate-code`, generationRequest);
      
      console.log('Generation request created:', response.data);
      setRequestId(response.data.id);
      setCurrentStep('process');
      
    } catch (err) {
      console.error('Error submitting generation request:', err);
      const errorMsg = err.response?.data?.detail || 'Failed to submit generation request. Please try again.';
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const resetApp = () => {
    setCurrentStep('generate');
    setRequestId(null);
    setSessionId(null);
    setGenerationStatus(null);
    setGenerationData(null);
    setIsLoading(false);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-6xl mx-auto py-8 px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Multi Code Review and Generation (MCRAG)
          </h1>
          <ul className="text-left max-w-2xl mx-auto mb-4 text-gray-700 list-disc list-inside space-y-1">
            <li><span className="font-semibold">GAN-Inspired Design:</span> The system is conceptually inspired by Generative Adversarial Networks (GANs), featuring a collaborative dynamic between a generator and critics.</li>
            <li><span className="font-semibold">Two-Part System:</span> <span className="underline">Generator</span> produces code based on user prompts. <span className="underline">Critics</span> review the generated code, providing detailed feedback and suggestions for improvement.</li>
            <li><span className="font-semibold">Iterative Refinement:</span> The generator incorporates critic feedback to refine its code. This process is repeated for three iterations: <span className="italic">Generate → Review → Refine</span>. This loop helps minimize errors and bugs in the final code.</li>
            <li><span className="font-semibold">Multi-Critic Setup:</span> For higher code quality, the system uses one generator and two critics: <span className="underline">Generator</span>: Gemini 2.5-Flash, <span className="underline">Critic 1</span>: GPT-4o Mini, <span className="underline">Critic 2</span>: DeepSeek R1.</li>
            <li><span className="font-semibold">Feedback Ranking:</span> After each review, the generator evaluates and ranks the feedback from both critics, prioritizing the most valuable suggestions for incorporation. This ensures that the most impactful improvements are made in each refinement cycle.</li>
            <li><span className="font-semibold">Outcome:</span> After three cycles, the system outputs code that has undergone multiple rounds of expert review and refinement, resulting in robust, high-quality code with minimal chances of errors or bugs.</li>
          </ul>
          <div className="text-center mb-4">
            <a
              href="/project-details.html"
              className="text-blue-600 hover:underline font-medium"
              target="_blank"
              rel="noopener noreferrer"
            >
              For more details, click here
            </a>
          </div>
          {currentStep !== 'generate' && (
            <button
              onClick={resetApp}
              className="mt-4 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
            >
              Generate New Code
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
            <div className={`flex items-center ${currentStep === 'generate' ? 'text-purple-600 font-semibold' : 'text-gray-400'}`}>
              <span className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium mr-2 ${
                currentStep === 'generate' ? 'bg-purple-600 text-white' : 'bg-gray-300 text-gray-600'
              }`}>1</span>
              Describe Code
            </div>
            <div className="w-8 h-0.5 bg-gray-300"></div>
            <div className={`flex items-center ${currentStep === 'process' ? 'text-purple-600 font-semibold' : 'text-gray-400'}`}>
              <span className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium mr-2 ${
                currentStep === 'process' ? 'bg-purple-600 text-white' : 'bg-gray-300 text-gray-600'
              }`}>2</span>
              AI Generation & Review
            </div>
            <div className="w-8 h-0.5 bg-gray-300"></div>
            <div className={`flex items-center ${currentStep === 'results' ? 'text-purple-600 font-semibold' : 'text-gray-400'}`}>
              <span className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium mr-2 ${
                currentStep === 'results' ? 'bg-purple-600 text-white' : 'bg-gray-300 text-gray-600'
              }`}>3</span>
              Final Code
            </div>
          </div>
        </div>

        {/* Main content */}
        {currentStep === 'generate' && (
          <CodeSubmission 
            onSubmit={handleCodeGeneration} 
            isLoading={isLoading} 
          />
        )}

        {currentStep === 'process' && (
          <ReviewProgress 
            status={generationStatus?.status || 'pending'} 
            reviewDetails={generationStatus} 
          />
        )}

        {currentStep === 'results' && (
          <ReviewResult 
            reviewData={generationData} 
            onReset={resetApp}
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

  return <CodeGenerationApp />;
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
