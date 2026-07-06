from abc import ABC, abstractmethod


class HotelProvider(ABC):

    @abstractmethod
    def search(
        self,
        destination,
        check_in=None,
        check_out=None,
        guests=2
    ):
        raise NotImplementedError
