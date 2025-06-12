import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from statistics import mean, median
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware pour surveiller et enregistrer les performances de l'API."""
    
    def __init__(self, app, stats_interval: int = 100):
        super().__init__(app)
        self.request_times = {}
        self.endpoints_stats = {}
        self.stats_interval = stats_interval
        self.requests_count = 0
        self.stats_dir = "data/performance_stats"
        os.makedirs(self.stats_dir, exist_ok=True)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Tracking du temps de début de requête
        start_time = time.time()
        
        # Traiter la requête
        response = await call_next(request)
        
        # Calculer le temps d'exécution de la requête
        process_time = time.time() - start_time
        
        # Récupérer l'endpoint
        endpoint = request.url.path
        method = request.method
        endpoint_key = f"{method}:{endpoint}"
        
        # Si RAG est utilisé, on l'identifie dans les logs
        is_rag_endpoint = "query" in endpoint or "chat" in endpoint
        
        # Enregistrer les statistiques
        if endpoint_key not in self.endpoints_stats:
            self.endpoints_stats[endpoint_key] = {
                "times": [],
                "count": 0,
                "total_time": 0,
                "min_time": float('inf'),
                "max_time": 0
            }
            
        stats = self.endpoints_stats[endpoint_key]
        stats["times"].append(process_time)
        stats["count"] += 1
        stats["total_time"] += process_time
        stats["min_time"] = min(stats["min_time"], process_time)
        stats["max_time"] = max(stats["max_time"], process_time)
        
        # Limiter la taille de la liste pour éviter une utilisation excessive de mémoire
        if len(stats["times"]) > 1000:
            stats["times"] = stats["times"][-1000:]
            
        # Log la durée de la requête
        performance_category = "SLOW" if process_time > 2 else "NORMAL"
        if process_time > 5:
            performance_category = "VERY_SLOW"
        
        log_message = f"API {performance_category}: {method} {endpoint} completed in {process_time:.3f}s"
        if is_rag_endpoint:
            log_message += " [RAG]"
            
        if process_time > 2:
            logger.warning(log_message)
        else:
            logger.info(log_message)
            
        # Incrémenter le compteur de requêtes
        self.requests_count += 1
        
        # Générer des statistiques périodiques
        if self.requests_count % self.stats_interval == 0:
            self._generate_stats_report()
        
        # Ajouter le temps de traitement dans les en-têtes de réponse
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    def _generate_stats_report(self):
        """Génère un rapport de performance basé sur les statistiques collectées."""
        
        stats_summary = {}
        
        for endpoint_key, stats in self.endpoints_stats.items():
            if stats["count"] > 0:
                # Calculer les statistiques
                avg_time = stats["total_time"] / stats["count"]
                
                # Calculer la médiane et le 95e percentile si nous avons assez d'échantillons
                percentiles = {}
                if stats["times"]:
                    sorted_times = sorted(stats["times"])
                    median_time = median(sorted_times)
                    p95_index = int(len(sorted_times) * 0.95)
                    p95_time = sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
                    
                    percentiles = {
                        "median": median_time,
                        "p95": p95_time
                    }
                
                stats_summary[endpoint_key] = {
                    "count": stats["count"],
                    "avg_time": avg_time,
                    "min_time": stats["min_time"],
                    "max_time": stats["max_time"],
                    "percentiles": percentiles
                }
        
        # Enregistrer les statistiques dans un fichier
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.stats_dir}/api_stats_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(stats_summary, f, indent=2)
            
        logger.info(f"Performance statistics generated: {filename}")
        
        # Log des endpoints les plus lents
        slow_endpoints = sorted(
            [(k, v["avg_time"]) for k, v in stats_summary.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        logger.warning("Top 5 des endpoints les plus lents:")
        for endpoint, avg_time in slow_endpoints:
            logger.warning(f"{endpoint}: {avg_time:.3f}s en moyenne")
