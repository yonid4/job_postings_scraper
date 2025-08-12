import time
import logging
import psutil
import functools
from typing import Dict, Any, Callable
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmergencyPerformanceProfiler:
    """Emergency performance profiler to identify bottlenecks causing 7-10 second load times."""
    
    def __init__(self):
        self.timings = {}
        self.memory_usage = []
        self.slow_queries = []
        self.start_time = None
        
    def start_profiling(self, operation_name: str):
        """Start profiling an operation."""
        self.start_time = time.time()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.memory_usage.append({
            'operation': operation_name,
            'memory_mb': initial_memory,
            'timestamp': datetime.now()
        })
        logger.info(f"🚨 EMERGENCY PROFILING START: {operation_name}")
        
    def end_profiling(self, operation_name: str, details: str = ""):
        """End profiling an operation and log results."""
        if self.start_time is None:
            return
            
        duration = time.time() - self.start_time
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        self.timings[operation_name] = {
            'duration': duration,
            'memory_mb': current_memory,
            'details': details,
            'timestamp': datetime.now()
        }
        
        # CRITICAL ALERT for slow operations
        if duration > 1.0:
            logger.error(f"🚨 CRITICAL SLOW OPERATION: {operation_name} took {duration:.3f}s - {details}")
        elif duration > 0.5:
            logger.warning(f"⚠️ SLOW OPERATION: {operation_name} took {duration:.3f}s - {details}")
        else:
            logger.info(f"✅ FAST OPERATION: {operation_name} took {duration:.3f}s - {details}")
            
        self.start_time = None
        
    def profile_database_query(self, query_name: str):
        """Decorator to profile database queries."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    if duration > 0.2:  # Alert for queries taking >200ms
                        logger.error(f"🚨 SLOW DATABASE QUERY: {query_name} took {duration:.3f}s")
                        self.slow_queries.append({
                            'query_name': query_name,
                            'duration': duration,
                            'timestamp': datetime.now()
                        })
                    
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(f"🚨 DATABASE QUERY ERROR: {query_name} failed after {duration:.3f}s - {e}")
                    raise
            return wrapper
        return decorator
        
    def profile_route(self, route_name: str):
        """Decorator to profile Flask routes."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
                
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    final_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    memory_diff = final_memory - initial_memory
                    
                    # CRITICAL ALERT for slow routes
                    if duration > 2.0:
                        logger.error(f"🚨 CRITICAL SLOW ROUTE: {route_name} took {duration:.3f}s (memory: +{memory_diff:.1f}MB)")
                    elif duration > 1.0:
                        logger.warning(f"⚠️ SLOW ROUTE: {route_name} took {duration:.3f}s (memory: +{memory_diff:.1f}MB)")
                    else:
                        logger.info(f"✅ FAST ROUTE: {route_name} took {duration:.3f}s (memory: +{memory_diff:.1f}MB)")
                    
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(f"🚨 ROUTE ERROR: {route_name} failed after {duration:.3f}s - {e}")
                    raise
            return wrapper
        return decorator
        
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate emergency performance report."""
        report = {
            'summary': {
                'total_operations': len(self.timings),
                'slow_operations': len([t for t in self.timings.values() if t['duration'] > 1.0]),
                'critical_operations': len([t for t in self.timings.values() if t['duration'] > 2.0]),
                'total_slow_queries': len(self.slow_queries)
            },
            'slowest_operations': sorted(
                self.timings.items(), 
                key=lambda x: x[1]['duration'], 
                reverse=True
            )[:10],
            'slow_queries': self.slow_queries,
            'memory_usage': self.memory_usage
        }
        
        return report
        
    def log_emergency_report(self):
        """Log emergency performance report."""
        report = self.get_performance_report()
        
        logger.error("🚨 EMERGENCY PERFORMANCE REPORT 🚨")
        logger.error(f"Total operations: {report['summary']['total_operations']}")
        logger.error(f"Slow operations (>1s): {report['summary']['slow_operations']}")
        logger.error(f"Critical operations (>2s): {report['summary']['critical_operations']}")
        logger.error(f"Slow database queries: {report['summary']['total_slow_queries']}")
        
        if report['slowest_operations']:
            logger.error("🚨 TOP 5 SLOWEST OPERATIONS:")
            for i, (op_name, details) in enumerate(report['slowest_operations'][:5], 1):
                logger.error(f"{i}. {op_name}: {details['duration']:.3f}s - {details['details']}")
                
        if report['slow_queries']:
            logger.error("🚨 SLOW DATABASE QUERIES:")
            for query in report['slow_queries'][:5]:
                logger.error(f"- {query['query_name']}: {query['duration']:.3f}s")

# Global profiler instance
emergency_profiler = EmergencyPerformanceProfiler()

def profile_operation(operation_name: str):
    """Decorator to profile any operation."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            emergency_profiler.start_profiling(operation_name)
            try:
                result = func(*args, **kwargs)
                emergency_profiler.end_profiling(operation_name, "Success")
                return result
            except Exception as e:
                emergency_profiler.end_profiling(operation_name, f"Error: {e}")
                raise
        return wrapper
    return decorator 