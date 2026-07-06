from .base import HotelProvider


class DemoProvider(HotelProvider):

    def search(
        self,
        destination,
        check_in=None,
        check_out=None,
        guests=2
    ):
        return []
