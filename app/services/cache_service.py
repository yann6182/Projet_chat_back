# app/services/cache_service.py
from collections import OrderedDict
from typing import Any, Dict, Optional, Tuple, List
import time
import logging
import threading
import json
import os

logger = logging.getLogger(__name__)

class CacheItem:
    """Classe représentant un élément en cache avec TTL"""
    def __init__(self, value: Any, ttl: int = 3600):
        self.value = value
        self.timestamp = time.time()
        self.ttl = ttl
        
    def is_expired(self) -> bool:
        """Vérifie si l'élément est expiré"""
        return (time.time() - self.timestamp) > self.ttl
        
    def touch(self):
        """Met à jour le timestamp de l'élément"""
        self.timestamp = time.time()

class CacheService:
    """
    Service de cache centralisé avec plusieurs niveaux:
    - Mémoire (LRU)
    - Disque (persistant)
    """
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CacheService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, memory_cache_size: int = 1000, disk_cache_dir: str = "data/cache"):
        # Singleton - éviter l'initialisation multiple
        if getattr(self, "_initialized", False):
            return
            
        self.memory_cache: Dict[str, CacheItem] = OrderedDict()
        self.memory_cache_size = memory_cache_size
        self.disk_cache_dir = disk_cache_dir
        
        # Créer le dossier de cache
        os.makedirs(disk_cache_dir, exist_ok=True)
        
        # Compteurs pour les statistiques
        self.stats = {
            "memory_hits": 0,
            "disk_hits": 0,
            "misses": 0,
            "memory_stores": 0,
            "disk_stores": 0
        }
        
        # Initialiser le thread de nettoyage
        self.cleanup_thread = None
        self.is_running = True
        self._start_cleanup_thread()
        
        self._initialized = True
        logger.info(f"Service de cache initialisé (mémoire: {memory_cache_size} items, disque: {disk_cache_dir})")
        
    def _start_cleanup_thread(self):
        """Démarre le thread de nettoyage"""
        def cleanup_routine():
            while self.is_running:
                self._cleanup_expired()
                time.sleep(60)  # Nettoyage toutes les minutes
                
        self.cleanup_thread = threading.Thread(target=cleanup_routine, daemon=True)
        self.cleanup_thread.start()
        
    def _cleanup_expired(self):
        """Nettoie les éléments expirés du cache mémoire"""
        with self._lock:
            # Copie des clés pour éviter l'erreur "dictionary changed size during iteration"
            keys = list(self.memory_cache.keys())
            expired_count = 0
            
            for key in keys:
                if key in self.memory_cache and self.memory_cache[key].is_expired():
                    del self.memory_cache[key]
                    expired_count += 1
                    
            # Nettoyer le cache disque moins fréquemment (1 fois sur 10)
            if expired_count > 0:
                logger.debug(f"Nettoyage cache mémoire: {expired_count} éléments supprimés")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Récupère un élément du cache (mémoire ou disque)
        """
        # 1. Vérifier d'abord le cache mémoire (plus rapide)
        with self._lock:
            if key in self.memory_cache:
                item = self.memory_cache[key]
                if not item.is_expired():
                    # Déplacer en fin de liste (LRU policy)
                    self.memory_cache.move_to_end(key)
                    self.stats["memory_hits"] += 1
                    return item.value
                else:
                    # Supprimer l'élément expiré
                    del self.memory_cache[key]
        
        # 2. Vérifier le cache disque (plus lent)
        disk_path = os.path.join(self.disk_cache_dir, f"{key}.json")
        if os.path.exists(disk_path):
            try:
                with open(disk_path, 'r') as f:
                    data = json.load(f)
                    # Vérifier l'expiration
                    if data.get("timestamp", 0) + data.get("ttl", 3600) > time.time():
                        # Déplacer en mémoire pour un accès plus rapide la prochaine fois
                        self.set(key, data["value"], data["ttl"])
                        self.stats["disk_hits"] += 1
                        return data["value"]
                    else:
                        # Supprimer le fichier expiré
                        os.remove(disk_path)
            except Exception as e:
                logger.warning(f"Erreur lors de la lecture du cache disque: {str(e)}")
                
        # Élément non trouvé
        self.stats["misses"] += 1
        return default
        
    def set(self, key: str, value: Any, ttl: int = 3600, persist: bool = False) -> None:
        """
        Ajoute/met à jour un élément dans le cache
        
        Args:
            key: Clé de l'élément
            value: Valeur à stocker
            ttl: Durée de vie en secondes (défaut: 1 heure)
            persist: Si True, l'élément est aussi stocké sur disque
        """
        # Stocker en mémoire
        with self._lock:
            self.memory_cache[key] = CacheItem(value, ttl)
            self.memory_cache.move_to_end(key)
            
            # Appliquer la politique LRU
            if len(self.memory_cache) > self.memory_cache_size:
                self.memory_cache.popitem(last=False)
                
            self.stats["memory_stores"] += 1
                
        # Stocker sur disque si demandé
        if persist:
            try:
                disk_path = os.path.join(self.disk_cache_dir, f"{key}.json")
                with open(disk_path, 'w') as f:
                    json.dump({
                        "value": value,
                        "timestamp": time.time(),
                        "ttl": ttl
                    }, f)
                    
                self.stats["disk_stores"] += 1
            except Exception as e:
                logger.warning(f"Erreur lors de l'écriture dans le cache disque: {str(e)}")
                
    def delete(self, key: str) -> bool:
        """
        Supprime un élément du cache
        
        Args:
            key: Clé de l'élément à supprimer
            
        Returns:
            True si l'élément a été supprimé, False sinon
        """
        deleted = False
        
        # Supprimer de la mémoire
        with self._lock:
            if key in self.memory_cache:
                del self.memory_cache[key]
                deleted = True
                
        # Supprimer du disque
        disk_path = os.path.join(self.disk_cache_dir, f"{key}.json")
        if os.path.exists(disk_path):
            try:
                os.remove(disk_path)
                deleted = True
            except Exception as e:
                logger.warning(f"Erreur lors de la suppression du cache disque: {str(e)}")
                
        return deleted
        
    def clear(self) -> None:
        """Vide tout le cache"""
        with self._lock:
            self.memory_cache.clear()
            
        # Supprimer les fichiers de cache disque
        for filename in os.listdir(self.disk_cache_dir):
            if filename.endswith(".json"):
                try:
                    os.remove(os.path.join(self.disk_cache_dir, filename))
                except Exception as e:
                    logger.warning(f"Erreur lors de la suppression du fichier de cache: {str(e)}")
                    
    def get_stats(self) -> Dict[str, int]:
        """Retourne les statistiques du cache"""
        with self._lock:
            # Calculer le taux de hit
            total_requests = self.stats["memory_hits"] + self.stats["disk_hits"] + self.stats["misses"]
            hit_rate = (self.stats["memory_hits"] + self.stats["disk_hits"]) / max(1, total_requests) * 100
            
            return {
                **self.stats,
                "memory_size": len(self.memory_cache),
                "hit_rate": hit_rate,
                "total_requests": total_requests
            }
            
    def __del__(self):
        """Arrête le thread de nettoyage lors de la destruction de l'objet"""
        self.is_running = False
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=1)
            
# Interface fonctionnelle pour faciliter l'utilisation
_cache_service = None

def get_cache() -> CacheService:
    """Retourne l'instance du service de cache"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
