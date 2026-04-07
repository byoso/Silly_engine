from abc import ABC, abstractmethod

class BaseConnector(ABC):
    """Interface pour tout backend DB"""

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def execute(self, query: str, params=None):
        """Exécute une requête SQL (INSERT, UPDATE, DELETE, etc.)"""
        pass

    @abstractmethod
    def fetchone(self):
        """Récupère un seul résultat"""
        pass

    @abstractmethod
    def fetchall(self):
        """Récupère tous les résultats"""
        pass

    @abstractmethod
    def commit(self):
        """Valide les changements"""
        pass

    @abstractmethod
    def rollback(self):
        """Annule les changements non validés"""
        pass

    @abstractmethod
    def close(self):
        pass