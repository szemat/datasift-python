"""
Thin wrapper around the requests library.
"""

import json as jsonlib
import requests
import six

from datasift import USER_AGENT
from datasift.output_mapper import outputmapper
from datasift.exceptions import DataSiftApiException, DataSiftApiFailure, AuthException


class PartialRequest(object):
    """ Internal class used to represent a yet-to-be-completed request """

    API_SCHEME = 'https'
    API_HOST = 'api.datasift.com'
    API_VERSION = 'v1.1'
    HEADERS = (
        ('User-Agent', USER_AGENT),
    )

    def __init__(self, auth, prefix=None, headers=None, timeout=None, proxies=None, verify=True):
        self.auth = auth
        self.prefix = prefix
        self.headers = headers
        self.timeout = timeout
        self.proxies = proxies
        self.verify = verify

    def get(self, path, params=None, headers=None):
        return self.build_response(self('get', path, params=params, headers=headers), path=path)

    def post(self, path, params=None, headers=None, data=None):
        return self.build_response(self('post', path, params=params, headers=headers, data=data), path=path)

    def json(self, path, data):
        """Convenience method for posting JSON content."""
        data = data if isinstance(data, six.string_types) else jsonlib.dumps(data)
        return self.post(path, headers={'Content-Type': 'application/json'}, data=data)

    def __call__(self, method, path, params=None, data=None, headers=None):
        url = u'%s://%s' % (self.API_SCHEME, self.path(self.API_HOST, self.API_VERSION, self.prefix, path))
        return requests.request(method, url,
                                params=params, data=data, auth=self.auth,
                                headers=self.dicts(self.headers, headers, dict(self.HEADERS)),
                                timeout=self.timeout,
                                proxies=self.proxies,
                                verify=self.verify)

    ## Builders

    def with_prefix(self, path, *args):
        prefix = '/'.join((path,) + args)
        return PartialRequest(self.auth, prefix, self.headers, self.timeout, self.proxies, self.verify)

    def build_response(self, response, path=None, parser=jsonlib.loads):
        """ Builds a List or Dict response object.

            Wrapper for a response from the DataSift REST API, can be accessed as a list.

            :param response: HTTP response to wrap
            :type response: :class:`~datasift.requests.Response`
            :param parser: optional parser to overload how the data is loaded
            :type parser: func
            :raises: :class:`~datasift.exceptions.DataSiftApiException`, :class:`~datasift.exceptions.DataSiftApiFailure`, :class:`~datasift.exceptions.AuthException`, :class:`requests.exceptions.HTTPError`
        """
        if response.status_code != 204:
            try:
                data = parser(response.text)
            except ValueError as e:
                raise DataSiftApiFailure("Unable to decode returned data.")
            if "error" in data:
                if response.status_code == 401:
                    raise AuthException(data)
                raise DataSiftApiException(Response(response, data))
            response.raise_for_status()
            if isinstance(data, dict):
                return Response(response, data, prefix=self.prefix, endpoint=path)
            elif isinstance(data, (list, map)):
                return ListResponse(response, data)

        else:
            # empty dict
            return Response(response, {})

    ## Helpers

    def path(self, *args):
        return '/'.join(a.strip('/') for a in args if a)

    def dicts(self, *dicts):
        return dict(kv for d in dicts if d for kv in d.items())


class DatasiftAuth(object):
    """ Internal class to represent an authentication pair.

        :ivar user: Stored username
        :type user: str
        :ivar key: Stored API key
        :type key: str
    """

    def __init__(self, user, key):
        self.user, self.key = user, key

    def __call__(self, request):
        request.headers['Authorization'] = '%s:%s' % (self.user, self.key)
        return request


class ListResponse(list):
    """ Wrapper for a response from the DataSift REST API, can be accessed as a list.

        :ivar raw: Raw response
        :type raw: list
        :param response: HTTP response to wrap
        :type response: requests.response
        :param data: data to wrap
        :type data: list
        :raises: :class:`~datasift.exceptions.DataSiftApiException`, :class:`~datasift.exceptions.DataSiftApiFailure`, :class:`~datasift.exceptions.AuthException`, :class:`requests.exceptions.HTTPError`
    """
    def __init__(self, response, data):
        self._response = response
        self.raw = list(data)  # Raw response
        self.extend(data)

    @property
    def status_code(self):
        """ :returns: HTTP Status Code of the Response
            :rtype: int
        """
        return self._response.status_code

    @property
    def headers(self):
        """ :returns: HTTP Headers of the Response
            :rtype: dict
        """
        return dict(self._response.headers)


class Response(dict):
    """ Wrapper for a response from the DataSift REST API, can be accessed as a dict.

        :ivar raw: Raw response
        :type raw: dict
        :param response: HTTP response to wrap
        :type response: requests.response
        :param parser: optional parser to overload how the data is loaded
        :type parser: func
        :raises: :class:`~datasift.exceptions.DataSiftApiException`, :class:`~datasift.exceptions.DataSiftApiFailure`, :class:`~datasift.exceptions.AuthException`, :class:`requests.exceptions.HTTPError`
    """
    def __init__(self, response, data, prefix=None, endpoint=None):
        self._response = response
        self.update(data)
        self.raw = jsonlib.loads(jsonlib.dumps(data))  # Raw response
        outputmapper(self, prefix, endpoint)

    @property
    def status_code(self):
        """ :returns: HTTP Status Code of the Response
            :rtype: int
        """
        return self._response.status_code

    @property
    def headers(self):
        """ :returns: HTTP Headers of the Response
            :rtype: dict
        """
        return dict(self._response.headers)
