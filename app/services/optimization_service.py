# app/services/optimization_service.py
import logging
import time
import threading
import asyncio
import functools
import concurrent.futures
from typing import Callable, Any, Optional, Dict, List, Tuple
from collections import OrderedDict

logger = logging.getLogger(__name__)

# Thread pool for background tasks
_thread_pool = concurrent.futures.ThreadPoolExecutor(
    max_workers=10, 
    thread_name_prefix="optimization_worker_"
)

class OptimizationService:
    """
    Service centralisé pour les optimisations de performance.
    Fournit des outils pour:
    - Mise en cache des requêtes et réponses
    - Exécution asynchrone de tâches non critiques
    - Surveillance des performances
    """
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(OptimizationService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, cache_size: int = 1000):
        """
        Initialise le service d'optimisation avec un cache de taille spécifiée.
        
        Args:
            cache_size: Taille maximale du cache en nombre d'éléments
        """
        if getattr(self, "_initialized", False):
            return
            
        # Cache pour les réponses et autres données
        self.cache = OrderedDict()
        self.cache_size = cache_size
        self.cache_stats = {"hits": 0, "misses": 0}
        
        # Métriques de performance
        self.performance_metrics = {}
        self.perf_samples = 100  # Nombre d'échantillons à conserver
        
        # Tâches en arrière-plan
        self.tasks = []
        
        self._initialized = True
        logger.info(f"Service d'optimisation initialisé (cache: {cache_size} éléments)")
    
    def get_from_cache(self, key: str) -> Optional[Any]:
        """
        Récupère une valeur du cache.
        
        Args:
            key: La clé de l'élément à récupérer
            
        Returns:
            La valeur associée à la clé ou None si non trouvée
        """
        with self._lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                self.cache_stats["hits"] += 1
                return self.cache[key]
            self.cache_stats["misses"] += 1
            return None
    
    def put_in_cache(self, key: str, value: Any) -> None:
        """
        Ajoute ou met à jour une valeur dans le cache.
        
        Args:
            key: La clé de l'élément
            value: La valeur à associer à la clé
        """
        with self._lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.cache_size:
                self.cache.popitem(last=False)
    
    def clear_cache(self) -> None:
        """
        Vide le cache.
        """
        with self._lock:
            self.cache.clear()
            
    def run_async(self, func: Callable, *args, **kwargs) -> concurrent.futures.Future:
        """
        Exécute une fonction de manière asynchrone.
        
        Args:
            func: La fonction à exécuter
            *args, **kwargs: Arguments à passer à la fonction
            
        Returns:
            Un objet Future représentant l'exécution de la fonction
        """
        return _thread_pool.submit(func, *args, **kwargs)
        
    def measure_performance(self, name: str) -> Callable:
        """
        Décorateur pour mesurer les performances d'une fonction.
        
        Args:
            name: Un nom pour identifier la métrique
            
        Returns:
            Un décorateur qui enregistre le temps d'exécution
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    execution_time = time.time() - start_time
                    self._record_performance(name, execution_time)
            return wrapper
        return decorator
        
    def _record_performance(self, name: str, execution_time: float) -> None:
        """
        Enregistre une métrique de performance.
        
        Args:
            name: Le nom de la métrique
            execution_time: Le temps d'exécution en secondes
        """
        with self._lock:
            if name not in self.performance_metrics:
                self.performance_metrics[name] = {
                    "times": [],
                    "min": float('inf'),
                    "max": 0,
                    "avg": 0,
                    "count": 0,
                    "total": 0
                }
                
            metrics = self.performance_metrics[name]
            metrics["times"].append(execution_time)
            metrics["min"] = min(metrics["min"], execution_time)
            metrics["max"] = max(metrics["max"], execution_time)
            metrics["count"] += 1
            metrics["total"] += execution_time
            metrics["avg"] = metrics["total"] / metrics["count"]
            
            # Limiter le nombre d'échantillons
            if len(metrics["times"]) > self.perf_samples:
                oldest = metrics["times"].pop(0)
                # Ajuster le total pour conserver une moyenne précise
                metrics["total"] -= oldest
                metrics["avg"] = metrics["total"] / len(metrics["times"])
                
    def get_performance_metrics(self) -> Dict[str, Dict]:
        """
        Récupère toutes les métriques de performance.
        
        Returns:
            Un dictionnaire des métriques par nom
        """
        with self._lock:
            return {k: v.copy() for k, v in self.performance_metrics.items()}
            
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Récupère les statistiques du cache.
        
        Returns:
            Un dictionnaire des statistiques du cache
        """
        with self._lock:
            stats = self.cache_stats.copy()
            stats["size"] = len(self.cache)
            stats["capacity"] = self.cache_size
            total = stats["hits"] + stats["misses"]
            stats["hit_rate"] = stats["hits"] / max(1, total) * 100
            return stats

# Interface fonctionnelle pour accéder au service d'optimisation
_optimization_service = None

def get_optimization_service() -> OptimizationService:
    """
    Récupère l'instance unique du service d'optimisation.
    
    Returns:
        L'instance du service d'optimisation
    """
    global _optimization_service
    if _optimization_service is None:
        _optimization_service = OptimizationService()
    return _optimization_service

# Fonctions utilitaires pour faciliter l'utilisation
def cache_result(key_prefix: str = "", ttl: int = 3600):
    """
    Décorateur pour mettre en cache le résultat d'une fonction.
    
    Args:
        key_prefix: Préfixe pour la clé de cache
        ttl: Durée de vie en secondes (non utilisée pour l'instant)
        
    Returns:
        Un décorateur qui met en cache le résultat
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Générer une clé de cache basée sur les arguments
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Vérifier le cache
            service = get_optimization_service()
            cached_result = service.get_from_cache(cache_key)
            if cached_result is not None:
                return cached_result
                
            # Exécuter la fonction et mettre en cache le résultat
            result = func(*args, **kwargs)
            service.put_in_cache(cache_key, result)
            return result
        return wrapper
    return decorator

def run_in_background(func: Callable) -> Callable:
    """
    Décorateur pour exécuter une fonction en arrière-plan.
    
    Args:
        func: La fonction à exécuter en arrière-plan
        
    Returns:
        Une fonction wrapper qui lance l'exécution en arrière-plan
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        service = get_optimization_service()
        return service.run_async(func, *args, **kwargs)
    return wrapper

def measure(name: str) -> Callable:
    """
    Décorateur pour mesurer les performances d'une fonction.
    
    Args:
        name: Un nom pour identifier la métrique
        
    Returns:
        Un décorateur qui enregistre le temps d'exécution
    """
    service = get_optimization_service()
    return service.measure_performance(name)
