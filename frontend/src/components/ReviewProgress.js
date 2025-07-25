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
      case 'generating':
      case 'reviewing':
      case 'refining':
        return <CogIcon className="h-5 w-5 text-purple-500 animate-spin" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'completed':
        return 'Code Generation Completed';
      case 'failed':
        return 'Generation Failed';
      case 'generating':
        return 'Generating Code...';
      case 'reviewing':
        return 'Critics Reviewing Code...';
      case 'refining':
        return 'Refining Based on Feedback...';
      case 'pending':
        return 'Pending Generation';
      default:
        return 'Processing...';
    }
  };

  const getProgressSteps = () => {
    if (!reviewDetails) return [];

    const steps = [
      {
        name: 'Code Generation',
        icon: <CpuChipIcon className="h-4 w-4" />,
        completed: reviewDetails.status !== 'pending',
        inProgress: reviewDetails.status === 'generating',
        llm: 'Gemini 2.5 Flash'
      }
    ];

    // Add review steps if we've started reviewing
    if (reviewDetails.status !== 'pending' && reviewDetails.status !== 'generating') {
      steps.push(
        {
          name: 'Critic 1 Review',
          icon: <UserIcon className="h-4 w-4" />,
          completed: reviewDetails.status === 'completed' || reviewDetails.status === 'refining',
          inProgress: reviewDetails.status === 'reviewing',
          llm: 'GPT-4o'
        },
        {
          name: 'Critic 2 Review',
          icon: <UserIcon className="h-4 w-4" />,
          completed: reviewDetails.status === 'completed' || reviewDetails.status === 'refining',
          inProgress: reviewDetails.status === 'reviewing',
          llm: 'DeepSeek R1'
        }
      );
    }

    // Add refinement step if we're refining
    if (reviewDetails.status === 'refining' || reviewDetails.status === 'completed') {
      steps.push({
        name: 'Code Refinement',
        icon: <CogIcon className="h-4 w-4" />,
        completed: reviewDetails.status === 'completed',
        inProgress: reviewDetails.status === 'refining',
        llm: 'Gemini 2.5 Flash'
      });
    }

    return steps;
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
                  : step.inProgress
                  ? 'bg-purple-100 text-purple-600'
                  : 'bg-gray-100 text-gray-400'
              }`}>
                {step.completed ? (
                  <CheckCircleIcon className="h-4 w-4" />
                ) : step.inProgress ? (
                  <CogIcon className="h-4 w-4 animate-spin" />
                ) : (
                  step.icon
                )}
              </div>
              <div className="ml-3 flex-1">
                <div className="flex items-center justify-between">
                  <p className={`text-sm font-medium ${
                    step.completed ? 'text-green-900' : 
                    step.inProgress ? 'text-purple-900' : 'text-gray-500'
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

      {reviewDetails?.current_iteration !== undefined && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Iteration Progress</span>
            <span className="text-sm font-semibold text-purple-600">
              {reviewDetails.current_iteration + 1} / {reviewDetails.max_iterations || 3}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReviewProgress;