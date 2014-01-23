
from exceptions import HistoricSourcesRequired


class HistoricsPreview(object):
    """ Represents the DataSift Historics Preview REST API and provides the ability to query it.
        Internal class instantiated as part of the Client object."""
    def __init__(self, request):
        self.request = request.with_prefix('preview')

    def create(self, stream, start, parameters, sources, end=None):
        """ Create a hitorics preview job.

            http://dev.datasift.com/docs/api/1/previewcreate

            :param stream: hash of the CSDL filter to create the job for
            :type stream: str
            :param start: Unix timestamp for the start of the period
            :type start: int
            :param parameters: list of historics preview parameters, can be found at http://dev.datasift.com/docs/api/1/previewcreate
            :type parameters: list
            :param sources: list of sources to include, eg. ['twitter','facebook']
            :type sources: list
            :param end: (optional) Unix timestamp for the end of the period, defaults to min(start+24h, now-1h)
            :type end: int
            :return: dict of REST API output with headers attached
            :rtype: :py:class:`request.Response`
            :raises: HistoricSourcesRequired, DataSiftApiException, requests.exceptions.HTTPError
        """
        if len(sources) == 0:
            raise HistoricSourcesRequired()

        params = {'hash': stream, 'start': start, 'sources': ','.join(sources), 'parameters': ','.join(parameters)}
        if end:
            params['end'] = end
        return self.request.json('create', params)

    def get(self, preview_id):
        """ Retrieve a Historics preview job.

            Warning: previews expire after 24 hours.

            http://dev.datasift.com/docs/api/1/previewget

            :param preview_id: historics preview job hash of the job to retrieve
            :type preview_id: str
            :return: dict of REST API output with headers attached
            :rtype: :py:class:`request.Response`
            :raises: DataSiftApiException, requests.exceptions.HTTPError
        """
        return self.request.get('get', params=dict(id=preview_id))