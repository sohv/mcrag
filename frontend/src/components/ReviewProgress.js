import React from 'react';
import { 
  ClockIcon, 
  CheckCircleIcon, 
  XCircleIcon, 
  CogIcon,
  UserIcon,
  CpuChipIcon
} from '@heroicons/react/24/outline';

const ReviewProgress = ({ status, reviewDetails }) => {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'in_progress':
        return <CogIcon className="h-5 w-5 text-blue-500 animate-spin" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'completed':
        return 'Review Completed';
      case 'failed':
        return 'Review Failed';
      case 'in_progress':
        return 'Review in Progress';
      case 'pending':
        return 'Pending Review';
      default:
        return 'Unknown Status';
    }
  };

  const getProgressSteps = () => {
    if (!reviewDetails) return [];

    return [
      {
        name: 'Coder Analysis',
        icon: <CpuChipIcon className="h-4 w-4" />,
        completed: reviewDetails.has_coder_feedback,
        llm: 'Gemini'
      },
      {
        name: 'Critic 1 Review',
        icon: <UserIcon className="h-4 w-4" />,
        completed: reviewDetails.has_critic1_feedback,
        llm: 'GPT-4'
      },
      {
        name: 'Critic 2 Review',
        icon: <UserIcon className="h-4 w-4" />,
        completed: reviewDetails.has_critic2_feedback,
        llm: 'DeepSeek R1'
      }
    ];
  };

  const progressSteps = getProgressSteps();

  return (
    <div className="bg-white shadow-lg rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Review Progress</h3>
        <div className="flex items-center">
          {getStatusIcon(status)}
          <span className="ml-2 text-sm font-medium text-gray-700">
            {getStatusText(status)}
          </span>
        </div>
      </div>

      {progressSteps.length > 0 && (
        <div className="space-y-3">
          {progressSteps.map((step, index) => (
            <div key={index} className="flex items-center">
              <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${
                step.completed 
                  ? 'bg-green-100 text-green-600' 
                  : 'bg-gray-100 text-gray-400'
              }`}>
                {step.completed ? (
                  <CheckCircleIcon className="h-4 w-4" />
                ) : (
                  step.icon
                )}
              </div>
              <div className="ml-3 flex-1">
                <div className="flex items-center justify-between">
                  <p className={`text-sm font-medium ${
                    step.completed ? 'text-green-900' : 'text-gray-500'
                  }`}>
                    {step.name}
                  </p>
                  <span className="text-xs text-gray-400">{step.llm}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {reviewDetails?.consensus_score !== null && reviewDetails?.consensus_score !== undefined && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Consensus Score</span>
            <span className="text-sm font-semibold text-blue-600">
              {(reviewDetails.consensus_score * 100).toFixed(1)}%
            </span>
          </div>
          <div className="mt-2 bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${reviewDetails.consensus_score * 100}%` }}
            />
          </div>
        </div>
      )}

      {reviewDetails?.human_feedback_count > 0 && (
        <div className="mt-3 text-sm text-gray-600">
          <span className="font-medium">{reviewDetails.human_feedback_count}</span> human feedback(s) received
        </div>
      )}
    </div>
  );
};

export default ReviewProgress;