###############################################################################
#
# Copyright (C) 2019 Tom Kralidis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import logging
from urllib.parse import urlparse

from elasticsearch import Elasticsearch, exceptions

from geomet_weather.tileindex.base import BaseTileIndex, TileIndexError

LOGGER = logging.getLogger(__name__)

INDEX_SETTINGS = {
    'settings': {
        'number_of_shards': 1,
        'number_of_replicas': 0
    },
    'mappings': {
        'FeatureCollection': {
            'properties': {
                'type': {
                    'type': 'text'
                },
                'properties': {
                    'properties': {
                        'identifier': {
                            'type': 'text',
                            'fields': {
                                'raw': {
                                    'type': 'keyword'
                                }
                            }
                        },
                        'layer': {
                            'type': 'text',
                            'fields': {
                                'raw': {
                                    'type': 'keyword'
                                }
                            }
                        },
                        'filepath': {
                            'type': 'text',
                            'fields': {
                                'raw': {
                                    'type': 'keyword'
                                }
                            }
                        },
                        'datetime': {
                            'type': 'date',
                            'format': "YYYY-MM-DD'T'HH:mm:ssZ"
                        },
                        'reference_datetime': {
                            'type': 'date',
                            'format': "YYYY-MM-DD'T'HH:mm:ssZ"
                        },
                        'elevation': {
                            'type': 'text',
                            'fields': {
                                 'raw': {
                                     'type': 'keyword'
                                 }
                             }
                        },
                        'members': {
                            'type': 'integer'
                        }
                    }
                },
                'geometry': {
                    'type': 'geo_shape'
                }
            }
        }
    }
}


class ElasticsearchTileIndex(BaseTileIndex):
    """Elasticsearch TileIndex"""

    def __init__(self, provider_def):
        """
        Initialize object

        :param provider_def: provider definition dict

        :returns: `geomet_weather.tileindex.elasticsearch_.ElasticsearchTileIndex`  # noqa
        """

        BaseTileIndex.__init__(self, provider_def)

        self.url_parsed = urlparse(self.url)
        self.type_name = 'FeatureCollection'

        LOGGER.debug('Connecting to Elasticsearch')

        if self.url_parsed.path is not None:
            self.es = Elasticsearch(self.url_parsed.netloc,
                                    url_prefix=self.url_parsed.path)
        else:
            self.es = Elasticsearch(self.url_parsed.netloc)

        if not self.es.ping():
            msg = 'Cannot connect to Elasticsearch'
            LOGGER.error(msg)
            raise TileIndexError(msg)

    def create(self):
        """
        Create the tileindex

        :returns: boolean of process status
        """

        if self.es.indices.exists(self.name):
            msg = 'Index exists'
            LOGGER.error(msg)
            raise TileIndexError(msg)

        LOGGER.info('Creating index {}'.format(self.name))
        self.es.indices.create(index=self.name, body=INDEX_SETTINGS)
        return True

    def delete(self):
        """
        Delete the tileindex

        :returns: boolean of process status
        """

        LOGGER.info('Deleting index {}'.format(self.name))
        try:
            self.es.indices.delete(index=self.name)
        except exceptions.NotFoundError as err:
            msg = err
            LOGGER.error(msg)
            raise TileIndexError(msg)

        return True

    def add(self, identifier, data):
        """
        Add an item to the tileindex

        :param identifier: tileindex item id
        :param data: GeoJSON dict

        :returns: boolean of process status
        """

        LOGGER.info('Indexing {}'.format(identifier))
        try:
            self.es.index(index=self.name, doc_type=self.type_name,
                          id=identifier, body=data)
        except Exception as err:
            LOGGER.exception('Error indexing {}: {}'.format(identifier, err))
            return False

        return True

    def __repr__(self):
        return '<ElasticsearchTileIndex> {}'.format(self.url)
