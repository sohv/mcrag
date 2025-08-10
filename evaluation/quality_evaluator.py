import re
import ast
import keyword
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class QualityMetrics:
    # Container for code quality metrics.
    functionality_score: float
    code_quality_score: float  
    completeness_score: float
    efficiency_score: float
    error_handling_score: float
    documentation_score: float
    overall_score: float
    detailed_feedback: Dict[str, Any]


class CodeQualityEvaluator:
    # Evaluates code quality across multiple dimensions.
    
    def __init__(self):
        self.language_evaluators = {
            'python': self._evaluate_python,
            'javascript': self._evaluate_javascript, 
            'java': self._evaluate_java
        }
    
    def evaluate(self, code: str, language: str, expected_features: List[str], 
                 test_case: Dict[str, Any]) -> QualityMetrics:
        if language not in self.language_evaluators:
            raise ValueError(f"Unsupported language: {language}")
        
        # Get language-specific evaluator
        evaluator = self.language_evaluators[language]
        
        # Perform evaluation
        metrics = evaluator(code, expected_features, test_case)
        
        return metrics
    
    def _evaluate_python(self, code: str, expected_features: List[str], 
                        test_case: Dict[str, Any]) -> QualityMetrics:
        # Evaluate Python code quality.
        feedback = {"language": "python", "checks": {}}
        
        # Functionality Score
        functionality_score = self._check_python_functionality(code, test_case, feedback)
        
        # Code Quality Score
        code_quality_score = self._check_python_code_quality(code, feedback)
        
        # Completeness Score
        completeness_score = self._check_feature_completeness(code, expected_features, feedback)
        
        # Efficiency Score
        efficiency_score = self._check_python_efficiency(code, test_case, feedback)
        
        # Error Handling Score
        error_handling_score = self._check_python_error_handling(code, feedback, test_case)
        
        # Documentation Score
        documentation_score = self._check_python_documentation(code, feedback)
        
        # Calculate overall score
        from evaluation.test_cases import EVALUATION_WEIGHTS
        overall_score = (
            functionality_score * EVALUATION_WEIGHTS['functionality'] +
            code_quality_score * EVALUATION_WEIGHTS['code_quality'] +
            completeness_score * EVALUATION_WEIGHTS['completeness'] +
            efficiency_score * EVALUATION_WEIGHTS['efficiency'] +
            error_handling_score * EVALUATION_WEIGHTS['error_handling'] +
            documentation_score * EVALUATION_WEIGHTS['documentation']
        )
        
        return QualityMetrics(
            functionality_score=functionality_score,
            code_quality_score=code_quality_score,
            completeness_score=completeness_score,
            efficiency_score=efficiency_score,
            error_handling_score=error_handling_score,
            documentation_score=documentation_score,
            overall_score=overall_score,
            detailed_feedback=feedback
        )
    
    def _check_python_functionality(self, code: str, test_case: Dict[str, Any], 
                                   feedback: Dict[str, Any]) -> float:
        # Check if Python code has correct functionality.
        checks = []
        
        # Check for syntax validity
        try:
            ast.parse(code)
            checks.append(("syntax_valid", True, "Code has valid syntax"))
        except SyntaxError as e:
            checks.append(("syntax_valid", False, f"Syntax error: {e}"))
            feedback["checks"]["syntax"] = {"valid": False, "error": str(e)}
            return 0.0
        
        # Check for expected function/class definitions
        prompt_lower = test_case['prompt'].lower()
        if 'function' in prompt_lower:
            if 'def ' in code:
                checks.append(("has_function", True, "Contains function definition"))
            else:
                checks.append(("has_function", False, "Missing function definition"))
        
        if 'class' in prompt_lower:
            if 'class ' in code:
                checks.append(("has_class", True, "Contains class definition"))
            else:
                checks.append(("has_class", False, "Missing class definition"))
        
        # Check for return statements where expected
        if 'return' in prompt_lower and 'def ' in code:
            if 'return ' in code:
                checks.append(("has_return", True, "Contains return statement"))
            else:
                checks.append(("has_return", False, "Missing return statement"))
        
        feedback["checks"]["functionality"] = checks
        return sum(1 for _, passed, _ in checks) / len(checks) if checks else 0.5
    
    def _check_python_code_quality(self, code: str, feedback: Dict[str, Any]) -> float:
        # Function documentation.
        checks = []
        
        # Check naming conventions (snake_case for functions/variables)
        snake_case_pattern = re.compile(r'^[a-z_][a-z0-9_]*$')
        functions = re.findall(r'def\s+(\w+)', code)
        variables = re.findall(r'^\s*(\w+)\s*=', code, re.MULTILINE)
        
        good_names = sum(1 for name in functions + variables if snake_case_pattern.match(name))
        total_names = len(functions + variables)
        if total_names > 0:
            naming_score = good_names / total_names
            checks.append(("naming_convention", naming_score > 0.8, 
                          f"Naming convention score: {naming_score:.2f}"))
        
        # Check for appropriate line length (< 80 chars)
        lines = code.split('\n')
        long_lines = sum(1 for line in lines if len(line) > 79)
        line_length_score = max(0, 1 - (long_lines / len(lines)))
        checks.append(("line_length", line_length_score > 0.9, 
                      f"Line length score: {line_length_score:.2f}"))
        
        # Check for proper indentation (4 spaces)
        indented_lines = [line for line in lines if line.startswith(' ')]
        proper_indent = sum(1 for line in indented_lines if len(line) - len(line.lstrip()) % 4 == 0)
        if indented_lines:
            indent_score = proper_indent / len(indented_lines)
            checks.append(("indentation", indent_score > 0.9, 
                          f"Indentation score: {indent_score:.2f}"))
        
        feedback["checks"]["code_quality"] = checks
        return sum(1 for _, passed, _ in checks) / len(checks) if checks else 0.5
    
    def _check_feature_completeness(self, code: str, expected_features: List[str], 
                                   feedback: Dict[str, Any]) -> float:
        # Function documentation.
        checks = []
        
        feature_patterns = {
            'recursive function': r'def\s+\w+.*:\s*.*\1\(',
            'input validation': r'(if.*isinstance|if.*type|if.*not|raise.*Error)',
            'base case handling': r'if.*return',
            'error handling': r'(try:|except:|raise)',
            'docstring or comments': r'(# Function documentation.|\'\'\'.*\'\'\'|#)',
            'binary search logic': r'(while.*<|for.*range.*//)',
            'class definition': r'class\s+\w+',
            'constructor method': r'def\s+__init__',
            'loop or recursion': r'(for\s+|while\s+|def\s+\w+.*\w+\()',
            'return statement': r'return\s+',
            'function declaration': r'def\s+\w+',
            'string manipulation': r'(\[.*\]|\.join|\.split|\.replace)',
        }
        
        for feature in expected_features:
            pattern = feature_patterns.get(feature.lower())
            if pattern:
                if re.search(pattern, code, re.IGNORECASE | re.DOTALL):
                    checks.append((feature, True, f"Found {feature}"))
                else:
                    checks.append((feature, False, f"Missing {feature}"))
            else:
                # Simple keyword check
                if feature.lower() in code.lower():
                    checks.append((feature, True, f"Found {feature}"))
                else:
                    checks.append((feature, False, f"Missing {feature}"))
        
        feedback["checks"]["completeness"] = checks
        return sum(1 for _, passed, _ in checks) / len(checks) if checks else 0.5
    
    def _check_python_efficiency(self, code: str, test_case: Dict[str, Any], 
                                feedback: Dict[str, Any]) -> float:
        # Function documentation.
        checks = []
        
        # Check for appropriate data structures
        if 'binary search' in test_case['prompt'].lower():
            if 'while' in code or 'for' in code:
                checks.append(("efficient_search", True, "Uses iterative approach"))
            else:
                checks.append(("efficient_search", False, "May not be efficient"))
        
        # Check for list comprehensions where appropriate
        if re.search(r'for\s+\w+\s+in.*:\s*.*\.append', code):
            checks.append(("list_comprehension_opportunity", False, 
                          "Could use list comprehension"))
        elif '[' in code and 'for' in code and 'in' in code:
            checks.append(("uses_list_comprehension", True, "Uses list comprehension"))
        
        # Check for unnecessary loops
        if code.count('for ') > 2:
            checks.append(("multiple_loops", False, "Multiple loops may indicate inefficiency"))
        
        feedback["checks"]["efficiency"] = checks
        return sum(1 for _, passed, _ in checks) / len(checks) if checks else 0.7
    
    def _check_python_error_handling(self, code: str, feedback: Dict[str, Any], 
                                     test_case: Dict[str, Any] = None) -> float:
        # Function documentation.
        checks = []
        
        # Check for try-except blocks
        if 'try:' in code and 'except' in code:
            checks.append(("has_try_except", True, "Contains try-except blocks"))
        elif test_case and 'error' in test_case.get('requirements', '').lower():
            checks.append(("missing_try_except", False, "Missing error handling"))
        
        # Check for input validation
        if re.search(r'if.*not.*:|if.*is.*None:|if.*isinstance', code):
            checks.append(("input_validation", True, "Contains input validation"))
        
        # Check for appropriate exceptions
        if 'raise' in code:
            checks.append(("raises_exceptions", True, "Raises appropriate exceptions"))
        
        feedback["checks"]["error_handling"] = checks
        return sum(1 for _, passed, _ in checks) / len(checks) if checks else 0.5
    
    def _check_python_documentation(self, code: str, feedback: Dict[str, Any]) -> float:
        # Function documentation.
        checks = []
        
        # Check for docstrings
        if '"""' in code or "'''" in code:
            checks.append(("has_docstring", True, "Contains docstring"))
        else:
            checks.append(("missing_docstring", False, "Missing docstring"))
        
        # Check for comments
        comment_lines = len([line for line in code.split('\n') if line.strip().startswith('#')])
        total_lines = len([line for line in code.split('\n') if line.strip()])
        
        if total_lines > 0:
            comment_ratio = comment_lines / total_lines
            if comment_ratio > 0.1:
                checks.append(("good_comments", True, f"Good comment ratio: {comment_ratio:.2f}"))
            else:
                checks.append(("few_comments", False, f"Low comment ratio: {comment_ratio:.2f}"))
        
        feedback["checks"]["documentation"] = checks
        return sum(1 for _, passed, _ in checks) / len(checks) if checks else 0.5

    def _evaluate_javascript(self, code: str, expected_features: List[str], 
                           test_case: Dict[str, Any]) -> QualityMetrics:
        # Function documentation.
        feedback = {"language": "javascript", "checks": {}}
        
        # Basic JavaScript evaluation (simplified)
        functionality_score = self._check_js_functionality(code, test_case, feedback)
        code_quality_score = self._check_js_code_quality(code, feedback)
        completeness_score = self._check_feature_completeness(code, expected_features, feedback)
        efficiency_score = 0.7  # Default for now
        error_handling_score = self._check_js_error_handling(code, feedback)
        documentation_score = self._check_js_documentation(code, feedback)
        
        from evaluation.test_cases import EVALUATION_WEIGHTS
        overall_score = (
            functionality_score * EVALUATION_WEIGHTS['functionality'] +
            code_quality_score * EVALUATION_WEIGHTS['code_quality'] +
            completeness_score * EVALUATION_WEIGHTS['completeness'] +
            efficiency_score * EVALUATION_WEIGHTS['efficiency'] +
            error_handling_score * EVALUATION_WEIGHTS['error_handling'] +
            documentation_score * EVALUATION_WEIGHTS['documentation']
        )
        
        return QualityMetrics(
            functionality_score=functionality_score,
            code_quality_score=code_quality_score,
            completeness_score=completeness_score,
            efficiency_score=efficiency_score,
            error_handling_score=error_handling_score,
            documentation_score=documentation_score,
            overall_score=overall_score,
            detailed_feedback=feedback
        )
    
    def _check_js_functionality(self, code: str, test_case: Dict[str, Any], 
                               feedback: Dict[str, Any]) -> float:
        # Function documentation.
        checks = []
        
        # Check for function declarations
        if 'function' in code or '=>' in code:
            checks.append(("has_function", True, "Contains function"))
        else:
            checks.append(("has_function", False, "Missing function"))
        
        # Check for return statements
        if 'return' in code:
            checks.append(("has_return", True, "Contains return statement"))
        
        feedback["checks"]["functionality"] = checks
        return sum(1 for _, passed, _ in checks) / len(checks) if checks else 0.5
    
    def _check_js_code_quality(self, code: str, feedback: Dict[str, Any]) -> float:
        # Function documentation.
        checks = []
        
        # Check for modern syntax
        if '=>' in code:
            checks.append(("modern_syntax", True, "Uses arrow functions"))
        
        # Check for proper variable declarations
        if 'const ' in code or 'let ' in code:
            checks.append(("modern_declarations", True, "Uses const/let"))
        elif 'var ' in code:
            checks.append(("old_declarations", False, "Uses var instead of const/let"))
        
        feedback["checks"]["code_quality"] = checks
        return sum(1 for _, passed, _ in checks) / len(checks) if checks else 0.5
    
    def _check_js_error_handling(self, code: str, feedback: Dict[str, Any]) -> float:
        # Function documentation.
        checks = []
        
        if 'try' in code and 'catch' in code:
            checks.append(("has_try_catch", True, "Contains try-catch"))
        
        if 'throw' in code:
            checks.append(("throws_errors", True, "Throws errors appropriately"))
        
        feedback["checks"]["error_handling"] = checks
        return sum(1 for _, passed, _ in checks) / len(checks) if checks else 0.5
    
    def _check_js_documentation(self, code: str, feedback: Dict[str, Any]) -> float:
        # Function documentation.
        checks = []
        
        comment_lines = len([line for line in code.split('\n') if '//' in line or '/*' in line])
        total_lines = len([line for line in code.split('\n') if line.strip()])
        
        if total_lines > 0:
            comment_ratio = comment_lines / total_lines
            checks.append(("comments", comment_ratio > 0.1, f"Comment ratio: {comment_ratio:.2f}"))
        
        feedback["checks"]["documentation"] = checks
        return sum(1 for _, passed, _ in checks) / len(checks) if checks else 0.5

    def _evaluate_java(self, code: str, expected_features: List[str], 
                      test_case: Dict[str, Any]) -> QualityMetrics:
        # Function documentation.
        feedback = {"language": "java", "checks": {}}
        
        functionality_score = self._check_java_functionality(code, test_case, feedback)
        code_quality_score = self._check_java_code_quality(code, feedback)
        completeness_score = self._check_feature_completeness(code, expected_features, feedback)
        efficiency_score = 0.7  # Default
        error_handling_score = self._check_java_error_handling(code, feedback)
        documentation_score = self._check_java_documentation(code, feedback)
        
        from evaluation.test_cases import EVALUATION_WEIGHTS
        overall_score = (
            functionality_score * EVALUATION_WEIGHTS['functionality'] +
            code_quality_score * EVALUATION_WEIGHTS['code_quality'] +
            completeness_score * EVALUATION_WEIGHTS['completeness'] +
            efficiency_score * EVALUATION_WEIGHTS['efficiency'] +
            error_handling_score * EVALUATION_WEIGHTS['error_handling'] +
            documentation_score * EVALUATION_WEIGHTS['documentation']
        )
        
        return QualityMetrics(
            functionality_score=functionality_score,
            code_quality_score=code_quality_score,
            completeness_score=completeness_score,
            efficiency_score=efficiency_score,
            error_handling_score=error_handling_score,
            documentation_score=documentation_score,
            overall_score=overall_score,
            detailed_feedback=feedback
        )
    
    def _check_java_functionality(self, code: str, test_case: Dict[str, Any], 
                                 feedback: Dict[str, Any]) -> float:
        # Function documentation.
        checks = []
        
        # Check for class definition
        if 'class ' in code:
            checks.append(("has_class", True, "Contains class definition"))
        
        # Check for main method if needed
        if 'public static void main' in code:
            checks.append(("has_main", True, "Contains main method"))
        
        feedback["checks"]["functionality"] = checks
        return sum(1 for _, passed, _ in checks) / len(checks) if checks else 0.5
    
    def _check_java_code_quality(self, code: str, feedback: Dict[str, Any]) -> float:
        # Function documentation.
        checks = []
        
        # Check for proper access modifiers
        if 'private ' in code:
            checks.append(("encapsulation", True, "Uses private fields"))
        
        # Check for camelCase naming
        methods = re.findall(r'public\s+\w+\s+(\w+)\s*\(', code)
        camel_case_pattern = re.compile(r'^[a-z][a-zA-Z0-9]*$')
        good_names = sum(1 for name in methods if camel_case_pattern.match(name))
        if methods:
            naming_score = good_names / len(methods)
            checks.append(("naming_convention", naming_score > 0.8, 
                          f"Naming score: {naming_score:.2f}"))
        
        feedback["checks"]["code_quality"] = checks
        return sum(1 for _, passed, _ in checks) / len(checks) if checks else 0.5
    
    def _check_java_error_handling(self, code: str, feedback: Dict[str, Any]) -> float:
        # Function documentation.
        checks = []
        
        if 'try' in code and 'catch' in code:
            checks.append(("has_try_catch", True, "Contains exception handling"))
        
        if 'throws' in code:
            checks.append(("declares_exceptions", True, "Declares thrown exceptions"))
        
        feedback["checks"]["error_handling"] = checks
        return sum(1 for _, passed, _ in checks) / len(checks) if checks else 0.5
    
    def _check_java_documentation(self, code: str, feedback: Dict[str, Any]) -> float:
        # Function documentation.
        checks = []
        
        if '/**' in code and '*/' in code:
            checks.append(("javadoc", True, "Contains Javadoc comments"))
        
        comment_lines = len([line for line in code.split('\n') if '//' in line or '/*' in line])
        total_lines = len([line for line in code.split('\n') if line.strip()])
        
        if total_lines > 0:
            comment_ratio = comment_lines / total_lines
            checks.append(("comments", comment_ratio > 0.1, f"Comment ratio: {comment_ratio:.2f}"))
        
        feedback["checks"]["documentation"] = checks
        return sum(1 for _, passed, _ in checks) / len(checks) if checks else 0.5
