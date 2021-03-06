from trakt.interfaces.base import Interface
from trakt.mapper.summary import SummaryMapper


class MoviesInterface(Interface):
    path = 'movies'

    def get(self, id):
        response = self.http.get(
            str(id)
        )

        # Parse response
        return SummaryMapper.movie(
            self.client,
            self.get_data(response)
        )

    def trending(self):
        response = self.http.get(
            'trending'
        )

        return SummaryMapper.movies(
            self.client,
            self.get_data(response)
        )
