"""
Test cases for evaluating MCRAG system performance across different programming languages.
Each test case includes a prompt, expected features, and evaluation criteria.
"""

TEST_CASES = {
    "python": [
        {
            "id": "py_001",
            "prompt": "Create a function to calculate the factorial of a number using recursion",
            "language": "python",
            "requirements": "Include input validation and handle edge cases",
            "expected_features": [
                "recursive function",
                "input validation",
                "base case handling",
                "error handling",
                "docstring or comments"
            ],
            "complexity": "basic",
            "expected_lines": (10, 25)
        },
        {
            "id": "py_002", 
            "prompt": "Implement a binary search algorithm for a sorted list",
            "language": "python",
            "requirements": "Return the index of the target element or -1 if not found",
            "expected_features": [
                "binary search logic",
                "iterative or recursive approach",
                "boundary handling",
                "return correct index",
                "input validation"
            ],
            "complexity": "intermediate",
            "expected_lines": (15, 35)
        },
        {
            "id": "py_003",
            "prompt": "Create a class for managing a simple bank account with deposit, withdraw, and balance methods",
            "language": "python", 
            "requirements": "Include balance validation and transaction history",
            "expected_features": [
                "class definition",
                "constructor method",
                "deposit method",
                "withdraw method",
                "balance validation",
                "transaction history"
            ],
            "complexity": "advanced",
            "expected_lines": (25, 50)
        },
        {
            "id": "py_004",
            "prompt": "Write a function to merge two sorted lists into one sorted list",
            "language": "python",
            "requirements": "Handle empty lists and maintain sorted order",
            "expected_features": [
                "function definition",
                "list merging logic",
                "sorted order maintenance",
                "edge case handling",
                "return statement"
            ],
            "complexity": "intermediate",
            "expected_lines": (15, 30)
        },
        {
            "id": "py_005",
            "prompt": "Implement a decorator that measures execution time of functions",
            "language": "python",
            "requirements": "Use functools.wraps and return timing information",
            "expected_features": [
                "decorator definition",
                "functools usage",
                "time measurement",
                "wrapper function",
                "return timing info"
            ],
            "complexity": "advanced",
            "expected_lines": (15, 35)
        }
    ],
    
    "javascript": [
        {
            "id": "js_001",
            "prompt": "Create a function to reverse a string without using built-in reverse method",
            "language": "javascript",
            "requirements": "Handle empty strings and single characters",
            "expected_features": [
                "function declaration",
                "string manipulation",
                "loop or recursion",
                "edge case handling",
                "return statement"
            ],
            "complexity": "basic",
            "expected_lines": (8, 20)
        },
        {
            "id": "js_002",
            "prompt": "Implement a debounce function that delays execution until after a specified time",
            "language": "javascript",
            "requirements": "Use closures and setTimeout",
            "expected_features": [
                "closure usage",
                "setTimeout function",
                "clearTimeout handling",
                "function composition",
                "proper this binding"
            ],
            "complexity": "intermediate", 
            "expected_lines": (10, 25)
        },
        {
            "id": "js_003",
            "prompt": "Create a simple HTTP request function using fetch API with error handling",
            "language": "javascript",
            "requirements": "Handle different HTTP status codes and network errors",
            "expected_features": [
                "fetch API usage",
                "async/await syntax", 
                "HTTP status handling",
                "error handling",
                "JSON parsing",
                "return response data"
            ],
            "complexity": "advanced",
            "expected_lines": (20, 40)
        },
        {
            "id": "js_004",
            "prompt": "Write a function to flatten a nested array of any depth",
            "language": "javascript",
            "requirements": "Handle arrays with mixed data types and arbitrary nesting",
            "expected_features": [
                "recursive approach",
                "array handling",
                "type checking",
                "nested structure processing",
                "return flattened array"
            ],
            "complexity": "intermediate",
            "expected_lines": (10, 25)
        },
        {
            "id": "js_005",
            "prompt": "Create an event emitter class with subscribe, unsubscribe, and emit methods",
            "language": "javascript",
            "requirements": "Support multiple listeners per event and proper cleanup",
            "expected_features": [
                "class definition",
                "event storage",
                "subscribe method",
                "unsubscribe method",
                "emit method",
                "listener management"
            ],
            "complexity": "advanced",
            "expected_lines": (25, 50)
        }
    ],
    
    "java": [
        {
            "id": "java_001",
            "prompt": "Create a class to represent a student with name, ID, and grades with average calculation",
            "language": "java",
            "requirements": "Include constructors, getters, setters, and validation",
            "expected_features": [
                "class definition",
                "private fields",
                "constructors",
                "getter/setter methods",
                "validation logic",
                "calculation methods"
            ],
            "complexity": "basic", 
            "expected_lines": (25, 45)
        },
        {
            "id": "java_002",
            "prompt": "Implement a thread-safe singleton pattern for a configuration manager",
            "language": "java",
            "requirements": "Use double-checked locking and include configuration loading",
            "expected_features": [
                "singleton pattern",
                "thread safety",
                "double-checked locking",
                "private constructor",
                "static instance",
                "configuration handling"
            ],
            "complexity": "intermediate",
            "expected_lines": (20, 40)
        },
        {
            "id": "java_003",
            "prompt": "Create a simple ArrayList implementation with basic operations",
            "language": "java",
            "requirements": "Include add, remove, get, size methods with dynamic resizing",
            "expected_features": [
                "class definition",
                "array backing",
                "add method",
                "remove method", 
                "get method",
                "dynamic resizing",
                "size tracking"
            ],
            "complexity": "advanced",
            "expected_lines": (40, 80)
        },
        {
            "id": "java_004",
            "prompt": "Write a method to check if a string is a valid palindrome ignoring case and spaces",
            "language": "java",
            "requirements": "Handle null input and special characters efficiently",
            "expected_features": [
                "string processing",
                "case insensitive comparison",
                "space handling",
                "null checking",
                "efficient algorithm",
                "return boolean"
            ],
            "complexity": "basic",
            "expected_lines": (15, 30)
        },
        {
            "id": "java_005",
            "prompt": "Implement a simple cache with LRU eviction policy using HashMap and LinkedList",
            "language": "java",
            "requirements": "Support get, put operations with O(1) complexity",
            "expected_features": [
                "LRU implementation",
                "HashMap usage",
                "LinkedList usage",
                "get method",
                "put method",
                "eviction logic",
                "O(1) complexity"
            ],
            "complexity": "advanced",
            "expected_lines": (50, 100)
        }
    ]
}

# Evaluation criteria weights
EVALUATION_WEIGHTS = {
    "functionality": 0.25,      # Does the code work as expected?
    "code_quality": 0.20,       # Clean, readable, well-structured?
    "completeness": 0.20,       # Includes all required features?
    "efficiency": 0.15,         # Optimal algorithm/approach?
    "error_handling": 0.10,     # Proper error handling?
    "documentation": 0.10       # Comments and clarity?
}

# Language-specific evaluation criteria
LANGUAGE_CRITERIA = {
    "python": {
        "style_guide": "PEP 8",
        "naming_convention": "snake_case", 
        "required_features": ["docstrings", "type_hints"],
        "common_patterns": ["list_comprehensions", "context_managers"]
    },
    "javascript": {
        "style_guide": "Standard JS",
        "naming_convention": "camelCase",
        "required_features": ["proper_scoping", "error_handling"],
        "common_patterns": ["arrow_functions", "destructuring"]
    },
    "java": {
        "style_guide": "Oracle Code Conventions",
        "naming_convention": "camelCase",
        "required_features": ["access_modifiers", "javadoc"],
        "common_patterns": ["encapsulation", "inheritance"]
    }
}
