from typing import List, Any

from abc import abstractmethod, ABC


class Loader(ABC):
    """
    Abstract class for ETL pipeline
    
    Loader must implement extract, transform and load methods.
    """

    @abstractmethod
    def extract(self, *args, **kwargs) -> List[Any]:
        raise NotImplementedError

    @abstractmethod
    def transform(self, data: List[Any], *args, **kwargs) -> List[Any]:
        raise NotImplementedError

    @abstractmethod
    def load(self, data: List[Any], *args, **kwargs) -> None:
        raise NotImplementedError
