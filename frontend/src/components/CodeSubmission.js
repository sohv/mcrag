import React, { useState } from 'react';
import { ChevronDownIcon, SparklesIcon } from '@heroicons/react/24/outline';

const LANGUAGES = [
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'java', label: 'Java' },
  { value: 'cpp', label: 'C++' }
];

const CodeSubmission = ({ onSubmit, isLoading }) => {
  const [prompt, setPrompt] = useState('');
  const [language, setLanguage] = useState('python');
  const [requirements, setRequirements] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!prompt.trim()) {
      alert('Please enter a description of what code you want to generate');
      return;
    }
    onSubmit({
      user_prompt: prompt,
      language,
      requirements: requirements.trim() || null
    });
  };

  return (
    <div className="bg-white shadow-lg rounded-lg p-6">
      <div className="flex items-center mb-6">
        <SparklesIcon className="h-6 w-6 text-purple-600 mr-2" />
        <h2 className="text-xl font-semibold text-gray-900">Generate Code with AI</h2>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-1">
            Programming Language
          </label>
          <div className="relative">
            <select
              id="language"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 appearance-none"
            >
              {LANGUAGES.map(lang => (
                <option key={lang.value} value={lang.value}>{lang.label}</option>
              ))}
            </select>
            <ChevronDownIcon className="h-5 w-5 text-gray-400 absolute right-3 top-2.5 pointer-events-none" />
          </div>
        </div>

        <div>
          <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-1">
            Describe what you want to build *
          </label>
          <textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g., 'Create a function that calculates the factorial of a number recursively' or 'Build a simple web scraper for product prices'"
            rows={4}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500"
            disabled={isLoading}
          />
          <p className="mt-1 text-xs text-gray-500">
            Be specific about what you want the code to do. The AI will generate code and then critics will review it automatically.
          </p>
        </div>

        <div>
          <label htmlFor="requirements" className="block text-sm font-medium text-gray-700 mb-1">
            Additional Requirements (Optional)
          </label>
          <textarea
            id="requirements"
            value={requirements}
            onChange={(e) => setRequirements(e.target.value)}
            placeholder="e.g., 'Use type hints', 'Handle edge cases', 'Include error handling', 'Follow PEP 8 style'"
            rows={2}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500"
            disabled={isLoading}
          />
        </div>

        <button
          type="submit"
          disabled={isLoading || !prompt.trim()}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Generating Code...
            </>
          ) : (
            'Generate Code with AI'
          )}
        </button>
      </form>
    </div>
  );
};

export default CodeSubmission;
