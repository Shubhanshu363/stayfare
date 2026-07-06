from abc import ABC, abstractmethod


class HotelProvider(ABC):

    name = "Base Provider"

    @abstractmethod
    def search(
        self,
        destination,
        check_in=None,
        check_out=None,
        adults=2,
        rooms=1,
    ):
        raise NotImplementedError
