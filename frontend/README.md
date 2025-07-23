# Multi-LLM Code Review System - Frontend

A React-based frontend for the Multi-LLM Code Review System that enables users to submit code for review by multiple AI models.

## Features

### 🚀 Core Functionality
- **Code Submission**: Submit code in multiple programming languages (Python, JavaScript, Java, C++)
- **Real-time Progress Tracking**: Monitor the review process across multiple LLM stages
- **Comprehensive Results**: View detailed feedback from all LLMs with suggestions and analysis
- **Human Feedback Integration**: Add your own feedback and ratings to improve the system

### 🤖 Multi-LLM Review Process
1. **Coder Analysis** (Gemini 2.0 Flash): Primary code analysis and improvement suggestions
2. **Critic 1 Review** (GPT-4o): Technical accuracy validation and critical feedback
3. **Critic 2 Review** (DeepSeek R1): Maintainability and practical considerations with advanced reasoning
4. **Consensus Generation**: Automatic conflict resolution and final recommendations

### 🎨 User Experience
- **Clean, Modern UI**: Built with React and Tailwind CSS
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Updates**: Automatic status polling during review process
- **Progressive Interface**: Step-by-step workflow with clear progress indicators

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Backend server running (see backend README)

### Installation

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment**:
   ```bash
   # Edit .env file to point to your backend
   REACT_APP_BACKEND_URL=http://localhost:8000
   ```

3. **Start development server**:
   ```bash
   npm start
   ```

4. **Open in browser**:
   Navigate to `http://localhost:3000`

## Usage Guide

### 1. Submit Code for Review
- Select programming language from dropdown
- Add optional description of what your code does
- Paste your code in the text area
- Click "Submit for Review"

### 2. Monitor Review Progress
- Watch real-time progress as each LLM analyzes your code
- See completion status for each review stage
- View consensus score as it's calculated

### 3. Review Results
- **Original Code**: See your submitted code with syntax highlighting
- **Coder Analysis**: Primary improvement suggestions and code snippets
- **Critic Reviews**: Critical analysis from two different perspectives
- **Final Recommendations**: Synthesized recommendations with consensus scoring
- **Suggested Code**: Improved code versions when available

### 4. Provide Human Feedback
- Add your own feedback on the review quality
- Rate the overall review (1-5 stars)
- Help improve the system with your insights