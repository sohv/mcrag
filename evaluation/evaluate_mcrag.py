import asyncio
import json
import time
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import asdict

from test_cases import TEST_CASES
from quality_evaluator import CodeQualityEvaluator


class MCRAGEvaluator:
    # Main evaluator for MCRAG system performance.
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.api_url = f"{backend_url}/api"
        self.quality_evaluator = CodeQualityEvaluator()
        self.results = []
    
    def check_system_availability(self) -> bool:
        # Check if MCRAG backend is available.
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    async def run_evaluation(self, languages: List[str] = None) -> Dict[str, Any]:
        if not self.check_system_availability():
            raise RuntimeError("MCRAG backend is not available. Please start the server.")
        
        # Use all languages if none specified
        if languages is None:
            languages = list(TEST_CASES.keys())
        
        print(f"Starting MCRAG evaluation for languages: {languages}")
        print(f"Total test cases: {sum(len(TEST_CASES[lang]) for lang in languages)}")
        print("=" * 60)
        
        # Run tests for each language
        for language in languages:
            if language not in TEST_CASES:
                print(f"Warning: No test cases found for language '{language}'")
                continue
            
            print(f"\nTesting {language.upper()} ({len(TEST_CASES[language])} test cases)")
            print("-" * 40)
            
            for i, test_case in enumerate(TEST_CASES[language], 1):
                print(f"  [{i}/{len(TEST_CASES[language])}] Running {test_case['id']}...")
                
                try:
                    result = await self._run_single_test(test_case)
                    self.results.append(result)
                    
                    # Print summary
                    if result['success']:
                        score = result['quality_metrics']['overall_score']
                        print(f"      Completed - Overall Score: {score:.2f}")
                    else:
                        print(f"      Failed - {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    error_result = {
                        'test_case_id': test_case['id'],
                        'language': test_case['language'],
                        'success': False,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                    self.results.append(error_result)
                    print(f"      Exception - {str(e)}")
                
                # Small delay between tests
                await asyncio.sleep(2)
        
        # Calculate aggregate metrics
        aggregate_metrics = self._calculate_aggregate_metrics()
        
        # Save detailed results
        self._save_results(aggregate_metrics)
        
        # Print summary
        self._print_summary(aggregate_metrics)
        
        return aggregate_metrics
    
    async def _run_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        # Run a single test case and evaluate the result.
        start_time = time.time()
        
        # Submit code generation request
        generation_request = {
            "user_prompt": test_case['prompt'],
            "language": test_case['language'],
            "requirements": test_case.get('requirements', '')
        }
        
        response = requests.post(f"{self.api_url}/generate-code", json=generation_request)
        if response.status_code != 200:
            raise Exception(f"Failed to submit request: {response.status_code}")
        
        request_data = response.json()
        request_id = request_data['id']
        
        # Poll for completion
        session_id = await self._poll_for_completion(request_id)
        
        # Get final result
        result_response = requests.get(f"{self.api_url}/generation-result/{session_id}")
        if result_response.status_code != 200:
            raise Exception(f"Failed to get result: {result_response.status_code}")
        
        generation_data = result_response.json()
        final_code = generation_data['final_code']['generated_code']
        
        # Evaluate code quality
        quality_metrics = self.quality_evaluator.evaluate(
            code=final_code,
            language=test_case['language'],
            expected_features=test_case['expected_features'],
            test_case=test_case
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Collect iteration data
        iterations_data = []
        for iteration in generation_data.get('iterations', []):
            iterations_data.append({
                'version': iteration.get('version', 0),
                'code_length': len(iteration.get('generated_code', '')),
                'explanation_length': len(iteration.get('explanation', '')),
                'has_reviews': len(iteration.get('reviews', [])) > 0,
                'review_count': len(iteration.get('reviews', []))
            })
        
        return {
            'test_case_id': test_case['id'],
            'language': test_case['language'],
            'complexity': test_case['complexity'],
            'success': True,
            'processing_time': processing_time,
            'session_id': session_id,
            'quality_metrics': asdict(quality_metrics),
            'code_stats': {
                'final_code_length': len(final_code),
                'final_code_lines': len(final_code.split('\n')),
                'iterations_count': len(iterations_data),
                'total_reviews': sum(iter_data['review_count'] for iter_data in iterations_data)
            },
            'iterations_data': iterations_data,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _poll_for_completion(self, request_id: str, timeout: int = 1200) -> str:
        # Poll for request completion and return session_id.
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = requests.get(f"{self.api_url}/generation-status/{request_id}")
            if response.status_code != 200:
                raise Exception(f"Failed to check status: {response.status_code}")
            
            status_data = response.json()
            status = status_data.get('status')
            
            if status == 'completed':
                return status_data.get('session_id')
            elif status == 'failed':
                raise Exception(f"Generation failed: {status_data.get('error', 'Unknown error')}")
            
            await asyncio.sleep(5)  # Poll every 5 seconds
        
        raise Exception(f"Request timed out after {timeout} seconds")
    
    def _calculate_aggregate_metrics(self) -> Dict[str, Any]:
        successful_results = [r for r in self.results if r.get('success', False)]
        
        if not successful_results:
            return {
                'summary': {
                    'total_tests': len(self.results),
                    'successful_tests': 0,
                    'success_rate': 0.0,
                    'average_processing_time': 0.0
                },
                'quality_metrics': {},
                'language_breakdown': {},
                'complexity_breakdown': {},
                'detailed_results': self.results
            }
        
        # Overall metrics
        total_tests = len(self.results)
        successful_tests = len(successful_results)
        success_rate = successful_tests / total_tests
        
        # Processing time metrics
        processing_times = [r['processing_time'] for r in successful_results]
        avg_processing_time = sum(processing_times) / len(processing_times)
        
        # Quality metrics aggregation
        quality_scores = {
            'functionality': [r['quality_metrics']['functionality_score'] for r in successful_results],
            'code_quality': [r['quality_metrics']['code_quality_score'] for r in successful_results],
            'completeness': [r['quality_metrics']['completeness_score'] for r in successful_results],
            'efficiency': [r['quality_metrics']['efficiency_score'] for r in successful_results],
            'error_handling': [r['quality_metrics']['error_handling_score'] for r in successful_results],
            'documentation': [r['quality_metrics']['documentation_score'] for r in successful_results],
            'overall': [r['quality_metrics']['overall_score'] for r in successful_results]
        }
        
        quality_metrics = {}
        for metric, scores in quality_scores.items():
            quality_metrics[metric] = {
                'mean': sum(scores) / len(scores),
                'min': min(scores),
                'max': max(scores),
                'std': self._calculate_std(scores)
            }
        
        # Language breakdown
        language_breakdown = {}
        for language in set(r['language'] for r in successful_results):
            lang_results = [r for r in successful_results if r['language'] == language]
            language_breakdown[language] = {
                'test_count': len(lang_results),
                'success_rate': len(lang_results) / len([r for r in self.results if r.get('language') == language]),
                'avg_quality_score': sum(r['quality_metrics']['overall_score'] for r in lang_results) / len(lang_results),
                'avg_processing_time': sum(r['processing_time'] for r in lang_results) / len(lang_results)
            }
        
        # Complexity breakdown
        complexity_breakdown = {}
        for complexity in set(r['complexity'] for r in successful_results):
            comp_results = [r for r in successful_results if r['complexity'] == complexity]
            complexity_breakdown[complexity] = {
                'test_count': len(comp_results),
                'avg_quality_score': sum(r['quality_metrics']['overall_score'] for r in comp_results) / len(comp_results),
                'avg_processing_time': sum(r['processing_time'] for r in comp_results) / len(comp_results)
            }
        
        return {
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'success_rate': success_rate,
                'average_processing_time': avg_processing_time
            },
            'quality_metrics': quality_metrics,
            'language_breakdown': language_breakdown,
            'complexity_breakdown': complexity_breakdown,
            'detailed_results': self.results,
            'evaluation_timestamp': datetime.now().isoformat()
        }
    
    def _calculate_std(self, scores: List[float]) -> float:
        # Calculate standard deviation.
        if len(scores) < 2:
            return 0.0
        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / (len(scores) - 1)
        return variance ** 0.5
    
    def _save_results(self, aggregate_metrics: Dict[str, Any]):
        # Save results to files.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed JSON results
        json_filename = f"mcrag_evaluation_{timestamp}.json"
        with open(json_filename, 'w') as f:
            json.dump(aggregate_metrics, f, indent=2)
        
        # Save summary CSV
        csv_filename = f"mcrag_summary_{timestamp}.csv"
        summary_data = []
        
        for result in aggregate_metrics['detailed_results']:
            if result.get('success', False):
                summary_data.append({
                    'test_id': result['test_case_id'],
                    'language': result['language'],
                    'complexity': result['complexity'],
                    'processing_time': result['processing_time'],
                    'overall_score': result['quality_metrics']['overall_score'],
                    'functionality_score': result['quality_metrics']['functionality_score'],
                    'code_quality_score': result['quality_metrics']['code_quality_score'],
                    'completeness_score': result['quality_metrics']['completeness_score'],
                    'iterations_count': result['code_stats']['iterations_count'],
                    'total_reviews': result['code_stats']['total_reviews']
                })
        
        if summary_data:
            df = pd.DataFrame(summary_data)
            df.to_csv(csv_filename, index=False)
        
        print(f"\nResults saved:")
        print(f"  - Detailed: {json_filename}")
        print(f"  - Summary: {csv_filename}")
    
    def _print_summary(self, metrics: Dict[str, Any]):
        # Print evaluation summary.
        print("\n" + "=" * 60)
        print("MCRAG EVALUATION SUMMARY")
        print("=" * 60)
        
        summary = metrics['summary']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Successful: {summary['successful_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Avg Processing Time: {summary['average_processing_time']:.1f}s")
        
        print("\nQUALITY METRICS")
        print("-" * 30)
        quality = metrics['quality_metrics']
        for metric, stats in quality.items():
            print(f"{metric.title():15} {stats['mean']:.3f} (±{stats['std']:.3f})")
        
        print("\nLANGUAGE BREAKDOWN")
        print("-" * 30)
        for lang, stats in metrics['language_breakdown'].items():
            print(f"{lang.title():12} {stats['test_count']:2d} tests, "
                  f"Score: {stats['avg_quality_score']:.3f}, "
                  f"Time: {stats['avg_processing_time']:.1f}s")
        
        print("\nCOMPLEXITY BREAKDOWN")
        print("-" * 30)
        for complexity, stats in metrics['complexity_breakdown'].items():
            print(f"{complexity.title():12} {stats['test_count']:2d} tests, "
                  f"Score: {stats['avg_quality_score']:.3f}, "
                  f"Time: {stats['avg_processing_time']:.1f}s")


async def main():
    # Main execution function.
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate MCRAG system performance')
    parser.add_argument('--languages', nargs='+', 
                       choices=['python', 'javascript', 'java'],
                       help='Languages to test (default: all)')
    parser.add_argument('--backend-url', default='http://localhost:8000',
                       help='MCRAG backend URL')
    
    args = parser.parse_args()
    
    evaluator = MCRAGEvaluator(backend_url=args.backend_url)
    
    try:
        results = await evaluator.run_evaluation(languages=args.languages)
        return results
    except KeyboardInterrupt:
        print("\nEvaluation interrupted by user")
        return None
    except Exception as e:
        print(f"\nEvaluation failed: {e}")
        return None


if __name__ == "__main__":
    # Run the evaluation
    results = asyncio.run(main())
    
    if results:
        print("\nEvaluation completed successfully!")
    else:
        print("\nEvaluation failed or was interrupted.")
        exit(1)
