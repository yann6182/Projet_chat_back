# app/utils/async_utils.py
import threading
import functools
import asyncio
import logging
from typing import Any, Callable, TypeVar, cast, Optional
import concurrent.futures
import time

logger = logging.getLogger(__name__)

# Pool d'exécuteurs pour les tâches asynchrones
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix="async_task_")

def run_async(func: Callable) -> Callable:
    """
    Décorateur pour exécuter une fonction de manière asynchrone dans un thread séparé.
    Utile pour les opérations non critiques qui ne doivent pas bloquer le traitement principal.
    
    Args:
        func: La fonction à exécuter de manière asynchrone
        
    Returns:
        Une fonction wrapper qui lance l'exécution asynchrone
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return thread_pool.submit(func, *args, **kwargs)
    return wrapper

def run_async_with_timeout(timeout: int = 5) -> Callable:
    """
    Décorateur pour exécuter une fonction de manière asynchrone avec un timeout.
    
    Args:
        timeout: Timeout en secondes (défaut: 5)
        
    Returns:
        Un décorateur qui prend une fonction et retourne une fonction wrapper
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            future = thread_pool.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                logger.warning(f"Timeout ({timeout}s) atteint pour la fonction {func.__name__}")
                return None
        return wrapper
    return decorator

async def run_in_executor(func: Callable, *args, **kwargs) -> Any:
    """
    Exécute une fonction synchrone dans un pool d'exécuteurs pour éviter le blocage.
    
    Args:
        func: La fonction à exécuter
        *args, **kwargs: Arguments à passer à la fonction
        
    Returns:
        Le résultat de la fonction
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, 
        lambda: func(*args, **kwargs)
    )

class TaskQueue:
    """
    Une file d'attente pour exécuter des tâches en arrière-plan.
    Utile pour les opérations non critiques qui peuvent être exécutées ultérieurement.
    """
    def __init__(self, max_workers: int = 5):
        self.queue = []
        self.running = False
        self.worker_thread = None
        self.max_workers = max_workers
        self.current_workers = 0
        self._lock = threading.Lock()
        
    def start(self):
        """Démarre le traitement des tâches"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.worker_thread.start()
            
    def stop(self):
        """Arrête le traitement des tâches"""
        self.running = False
        
    def add_task(self, func: Callable, *args, **kwargs) -> None:
        """
        Ajoute une tâche à la file d'attente
        
        Args:
            func: La fonction à exécuter
            *args, **kwargs: Arguments à passer à la fonction
        """
        with self._lock:
            self.queue.append((func, args, kwargs))
            
        # Démarrer le traitement si ce n'est pas encore fait
        if not self.running or not self.worker_thread or not self.worker_thread.is_alive():
            self.start()
            
    def _process_queue(self):
        """Traite les tâches en file d'attente"""
        while self.running:
            # Attendre s'il y a trop de workers en cours
            while self.current_workers >= self.max_workers:
                time.sleep(0.1)
                
            # Vérifier s'il y a des tâches
            with self._lock:
                if not self.queue:
                    time.sleep(0.1)
                    continue
                    
                # Récupérer la prochaine tâche
                func, args, kwargs = self.queue.pop(0)
                
            # Exécuter la tâche dans un thread séparé
            self.current_workers += 1
            worker = threading.Thread(
                target=self._execute_task, 
                args=(func, args, kwargs),
                daemon=True
            )
            worker.start()
                
    def _execute_task(self, func: Callable, args, kwargs):
        """Exécute une tâche et gère les exceptions"""
        try:
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            logger.debug(f"Tâche {func.__name__} exécutée en {elapsed_time:.3f}s")
            return result
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la tâche {func.__name__}: {str(e)}")
        finally:
            self.current_workers -= 1

# Créer une instance globale de TaskQueue
background_tasks = TaskQueue()
background_tasks.start()
