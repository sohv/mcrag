import React, { useState } from 'react';
import { 
  UserIcon, 
  CpuChipIcon, 
  ClipboardDocumentIcon,
  ChatBubbleLeftIcon,
  StarIcon
} from '@heroicons/react/24/outline';

const ReviewResult = ({ reviewData, onHumanFeedback }) => {
  const [showHumanFeedback, setShowHumanFeedback] = useState(false);
  const [feedbackText, setFeedbackText] = useState('');
  const [rating, setRating] = useState(5);
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

  if (!reviewData) {
    return (
      <div className="bg-white shadow-lg rounded-lg p-6 text-center">
        <p className="text-gray-500">No review results available yet.</p>
      </div>
    );
  }

  // Handle the actual backend data structure
  const { session, request, generated_codes, critic_reviews, final_code, generation_summary } = reviewData;
  
  // Map to expected format for compatibility with existing component logic
  const submission = request;
  const coder_feedback = generated_codes?.[generated_codes.length - 1]; // Latest version
  const critic_feedbacks = critic_reviews || [];
  const final_recommendations = generation_summary;

  const handleSubmitFeedback = async (e) => {
    e.preventDefault();
    if (!feedbackText.trim()) return;

    setSubmittingFeedback(true);
    try {
      await onHumanFeedback({
        feedback_text: feedbackText,
        rating: rating
      });
      setFeedbackText('');
      setRating(5);
      setShowHumanFeedback(false);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      alert('Failed to submit feedback. Please try again.');
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const FeedbackCard = ({ title, feedback, icon, llmModel }) => (
    <div className="bg-gray-50 rounded-lg p-4 mb-4">
      <div className="flex items-center mb-3">
        {icon}
        <h4 className="text-md font-semibold text-gray-800 ml-2">{title}</h4>
        <span className="ml-auto text-xs text-gray-500 bg-white px-2 py-1 rounded">
          {llmModel}
        </span>
      </div>
      <div className="prose prose-sm max-w-none">
        <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans leading-relaxed">
          {feedback.feedback_text}
        </pre>
      </div>
      {feedback.suggested_code && (
        <div className="mt-3 p-3 bg-gray-800 rounded-md">
          <p className="text-xs text-gray-300 mb-2">Suggested Code:</p>
          <pre className="text-sm text-green-400 overflow-x-auto">
            <code>{feedback.suggested_code}</code>
          </pre>
        </div>
      )}
      {feedback.processing_time && (
        <div className="mt-2 text-xs text-gray-500">
          Processing time: {feedback.processing_time.toFixed(2)}s
        </div>
      )}
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="bg-white shadow-lg rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Code Generation Complete</h2>
          <div className="text-sm text-gray-500">
            {session?.refinement_iterations !== undefined ? session.refinement_iterations + 1 : 1} iteration{(session?.refinement_iterations || 0) !== 0 ? 's' : ''}
          </div>
        </div>

        {/* Final Code Display */}
        {final_code && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-800">Final Generated Code</h3>
              <button
                onClick={() => navigator.clipboard.writeText(final_code)}
                className="flex items-center px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
              >
                <ClipboardDocumentIcon className="h-4 w-4 mr-1" />
                Copy Code
              </button>
            </div>
            <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
              <pre className="text-green-400 text-sm">
                <code>{final_code}</code>
              </pre>
            </div>
          </div>
        )}

        {/* Generation Summary */}
        {generation_summary && (
          <div className="mb-6 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-semibold text-blue-900 mb-2">Generation Summary</h4>
            <p className="text-blue-800 text-sm">{generation_summary}</p>
          </div>
        )}

        {/* Request Details */}
        {submission && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-semibold text-gray-900 mb-2">Original Request</h4>
            <p className="text-gray-700 text-sm mb-2"><strong>Prompt:</strong> {submission.user_prompt}</p>
            <p className="text-gray-700 text-sm mb-2"><strong>Language:</strong> {submission.language}</p>
            {submission.requirements && (
              <p className="text-gray-700 text-sm"><strong>Requirements:</strong> {submission.requirements}</p>
            )}
          </div>
        )}
      </div>

      {/* Code Evolution */}
      {generated_codes && generated_codes.length > 1 && (
        <div className="bg-white shadow-lg rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Code Evolution</h3>
          <div className="space-y-4">
            {generated_codes.map((code, index) => (
              <div key={code.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">Version {code.version}</h4>
                  <span className="text-xs text-gray-500">
                    {new Date(code.created_at).toLocaleString()}
                  </span>
                </div>
                {code.explanation && (
                  <p className="text-sm text-gray-600 mb-3">{code.explanation}</p>
                )}
                <div className="bg-gray-900 rounded p-3 overflow-x-auto">
                  <pre className="text-green-400 text-xs">
                    <code>{code.generated_code}</code>
                  </pre>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Critic Reviews */}
      {critic_feedbacks && critic_feedbacks.length > 0 && (
        <div className="bg-white shadow-lg rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Critic Reviews</h3>
          <div className="space-y-4">
            {critic_feedbacks.map((review, index) => (
              <div key={review.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">
                    {review.critic_type === 'CRITIC1' ? 'Critic 1' : 'Critic 2'} Review
                  </h4>
                  <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                    {review.llm_model}
                  </span>
                </div>
                <div className="text-sm text-gray-700 mb-3">
                  {review.review_text}
                </div>
                {review.suggestions && review.suggestions.length > 0 && (
                  <div className="bg-yellow-50 rounded p-3">
                    <h5 className="font-medium text-yellow-900 mb-2">Suggestions:</h5>
                    <ul className="text-sm text-yellow-800 space-y-1">
                      {review.suggestions.map((suggestion, idx) => (
                        <li key={idx} className="flex items-start">
                          <span className="mr-2">•</span>
                          <span>{suggestion}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
                  <span>Severity: {review.severity_rating}/5</span>
                  <span>Confidence: {(review.confidence_score * 100).toFixed(0)}%</span>
                  {review.processing_time && <span>Time: {review.processing_time.toFixed(2)}s</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reset Button */}
      <div className="text-center">
        <button
          onClick={() => window.location.reload()}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Generate New Code
        </button>
      </div>
    </div>
  );
};

export default ReviewResult;