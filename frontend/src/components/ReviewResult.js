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

  const { submission, coder_feedback, critic_feedbacks, final_recommendations, session } = reviewData;

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
    <div className="space-y-6">
      {/* Original Code */}
      <div className="bg-white shadow-lg rounded-lg p-6">
        <div className="flex items-center mb-4">
          <ClipboardDocumentIcon className="h-5 w-5 text-gray-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">Original Code</h3>
          <span className="ml-auto text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
            {submission.language}
          </span>
        </div>
        {submission.description && (
          <p className="text-sm text-gray-600 mb-3">{submission.description}</p>
        )}
        <div className="bg-gray-900 rounded-md p-4 overflow-x-auto">
          <pre className="text-sm text-gray-100">
            <code>{submission.original_code}</code>
          </pre>
        </div>
      </div>

      {/* Coder Feedback */}
      {coder_feedback && (
        <div className="bg-white shadow-lg rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">LLM Reviews</h3>
          <FeedbackCard
            title="Coder Analysis"
            feedback={coder_feedback}
            icon={<CpuChipIcon className="h-5 w-5 text-blue-600" />}
            llmModel={coder_feedback.llm_model}
          />
        </div>
      )}

      {/* Critic Feedbacks */}
      {critic_feedbacks && critic_feedbacks.length > 0 && (
        <div className="bg-white shadow-lg rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Critic Reviews</h3>
          {critic_feedbacks.map((feedback, index) => (
            <FeedbackCard
              key={index}
              title={`Critic ${index + 1} Analysis`}
              feedback={feedback}
              icon={<UserIcon className="h-5 w-5 text-purple-600" />}
              llmModel={feedback.llm_model}
            />
          ))}
        </div>
      )}

      {/* Final Recommendations */}
      {final_recommendations && (
        <div className="bg-white shadow-lg rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Final Recommendations</h3>
          <div className="prose prose-sm max-w-none">
            <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans leading-relaxed">
              {final_recommendations}
            </pre>
          </div>
          
          {session.consensus_score !== null && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-blue-900">Overall Consensus</span>
                <span className="text-lg font-bold text-blue-600">
                  {(session.consensus_score * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Human Feedback Section */}
      <div className="bg-white shadow-lg rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Human Feedback</h3>
          <button
            onClick={() => setShowHumanFeedback(!showHumanFeedback)}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm"
          >
            <ChatBubbleLeftIcon className="h-4 w-4 inline mr-1" />
            Add Feedback
          </button>
        </div>

        {showHumanFeedback && (
          <form onSubmit={handleSubmitFeedback} className="space-y-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Feedback
              </label>
              <textarea
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                rows={4}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500"
                placeholder="Share your thoughts on the review quality and suggestions..."
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Rating (1-5 stars)
              </label>
              <div className="flex space-x-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    className={`p-1 ${rating >= star ? 'text-yellow-400' : 'text-gray-300'}`}
                  >
                    <StarIcon className="h-5 w-5 fill-current" />
                  </button>
                ))}
              </div>
            </div>
            
            <div className="flex space-x-3">
              <button
                type="submit"
                disabled={submittingFeedback || !feedbackText.trim()}
                className={`px-4 py-2 rounded-md text-sm font-medium ${
                  submittingFeedback || !feedbackText.trim()
                    ? 'bg-gray-400 cursor-not-allowed text-white'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                }`}
              >
                {submittingFeedback ? 'Submitting...' : 'Submit Feedback'}
              </button>
              <button
                type="button"
                onClick={() => setShowHumanFeedback(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Show existing human feedbacks if any */}
        {reviewData.human_feedbacks && reviewData.human_feedbacks.length > 0 && (
          <div className="space-y-3">
            <h4 className="font-medium text-gray-900">Previous Feedback</h4>
            {reviewData.human_feedbacks.map((feedback, index) => (
              <div key={index} className="bg-gray-50 p-3 rounded-md">
                <p className="text-sm text-gray-700">{feedback.feedback_text}</p>
                {feedback.rating && (
                  <div className="flex items-center mt-1">
                    <span className="text-xs text-gray-500 mr-2">Rating:</span>
                    {[...Array(5)].map((_, i) => (
                      <StarIcon
                        key={i}
                        className={`h-3 w-3 ${
                          i < feedback.rating ? 'text-yellow-400' : 'text-gray-300'
                        } fill-current`}
                      />
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReviewResult;