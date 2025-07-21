import React, { useState } from 'react';
import { ChevronDownIcon, CodeBracketIcon } from '@heroicons/react/24/outline';

const LANGUAGES = [
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'java', label: 'Java' },
  { value: 'cpp', label: 'C++' }
];

const CodeSubmission = ({ onSubmit, isLoading }) => {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [description, setDescription] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!code.trim()) {
      alert('Please enter some code to review');
      return;
    }
    onSubmit({
      original_code: code,
      language,
      description: description.trim() || null
    });
  };

  return (
    <div className="bg-white shadow-lg rounded-lg p-6">
      <div className="flex items-center mb-6">
        <CodeBracketIcon className="h-6 w-6 text-blue-600 mr-2" />
        <h2 className="text-xl font-semibold text-gray-900">Submit Code for Review</h2>
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
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 appearance-none"
            >
              {LANGUAGES.map(lang => (
                <option key={lang.value} value={lang.value}>{lang.label}</option>
              ))}
            </select>
            <ChevronDownIcon className="absolute right-3 top-2.5 h-4 w-4 text-gray-400 pointer-events-none" />
          </div>
        </div>

        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
            Description (Optional)
          </label>
          <input
            type="text"
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Brief description of what the code does..."
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label htmlFor="code" className="block text-sm font-medium text-gray-700 mb-1">
            Code
          </label>
          <textarea
            id="code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            rows={12}
            placeholder="Paste your code here..."
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
            required
          />
        </div>

        <button
          type="submit"
          disabled={isLoading || !code.trim()}
          className={`w-full py-2 px-4 rounded-md font-medium transition-colors ${
            isLoading || !code.trim()
              ? 'bg-gray-400 cursor-not-allowed text-white'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          {isLoading ? 'Submitting...' : 'Submit for Review'}
        </button>
      </form>
    </div>
  );
};

export default CodeSubmission;