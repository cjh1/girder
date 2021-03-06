#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright 2013 Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import datetime

from .model_base import Model, ValidationException
from girder.utility import assetstore_utilities
from girder.utility.filesystem_assetstore_adapter import\
    FilesystemAssetstoreAdapter
from girder.utility.gridfs_assetstore_adapter import GridFsAssetstoreAdapter
from girder.utility.s3_assetstore_adapter import S3AssetstoreAdapter
from girder.constants import AssetstoreType


class Assetstore(Model):
    """
    This model represents an assetstore, an abstract repository of Files.
    """
    def initialize(self):
        self.name = 'assetstore'

    def validate(self, doc):
        # Ensure no duplicate names
        q = {'name': doc['name']}
        if '_id' in doc:
            q['_id'] = {'$ne': doc['_id']}
        duplicates = self.find(q, limit=1, fields=['_id'])
        if duplicates.count() != 0:
            raise ValidationException('An assetstore with that name already '
                                      'exists.', 'name')

        # Name must not be empty
        if not doc['name']:
            raise ValidationException('Name must not be empty.', 'name')

        # Adapter classes validate each type internally
        if doc['type'] == AssetstoreType.FILESYSTEM:
            FilesystemAssetstoreAdapter.validateInfo(doc)
        elif doc['type'] == AssetstoreType.GRIDFS:
            GridFsAssetstoreAdapter.validateInfo(doc)
        elif doc['type'] == AssetstoreType.S3:
            S3AssetstoreAdapter.validateInfo(doc)

        # If no current assetstore exists yet, set this one as the current.
        current = self.find({'current': True}, limit=1, fields=['_id'])
        if current.count() == 0:
            doc['current'] = True
        if 'current' not in doc:
            doc['current'] = False

        # If we are setting this as current, we should unmark all other
        # assetstores that have the current flag.
        if doc['current'] is True:
            self.update({'current': True}, {'$set': {'current': False}})

        return doc

    def remove(self, assetstore):
        """
        Delete an assetstore. If there are any files within this assetstore,
        a validation exception is raised.

        :param assetstore: The assetstore document to delete.
        :type assetstore: dict
        """
        files = self.model('file').find({
            'assetstoreId': assetstore['_id']
        }, limit=1)
        if files.count(True) > 0:
            raise ValidationException('You may not delete an assetstore that '
                                      'contains files.')

        Model.remove(self, assetstore)

    def list(self, limit=50, offset=0, sort=None):
        """
        List all assetstores.

        :param limit: Result limit.
        :param offset: Result offset.
        :param sort: The sort structure to pass to pymongo.
        :returns: List of users.
        """
        cursor = self.find({}, limit=limit, offset=offset, sort=sort)
        assetstores = []
        for assetstore in cursor:
            adapter = assetstore_utilities.getAssetstoreAdapter(assetstore)
            assetstore['capacity'] = adapter.capacityInfo()
            assetstores.append(assetstore)

        return assetstores

    def createFilesystemAssetstore(self, name, root):
        return self.save({
            'type': AssetstoreType.FILESYSTEM,
            'created': datetime.datetime.now(),
            'name': name,
            'root': root
        })

    def createGridFsAssetstore(self, name, db):
        return self.save({
            'type': AssetstoreType.GRIDFS,
            'created': datetime.datetime.now(),
            'name': name,
            'db': db
        })

    def createS3Assetstore(self, name, bucket, accessKeyId, secret, prefix=''):
        return self.save({
            'type': AssetstoreType.S3,
            'created': datetime.datetime.now(),
            'name': name,
            'accessKeyId': accessKeyId,
            'secret': secret,
            'prefix': prefix,
            'bucket': bucket
        })

    def getCurrent(self):
        """
        Returns the current assetstore. If none exists, this will raise a 500
        exception.
        """
        cursor = self.find({'current': True}, limit=1)
        if cursor.count() == 0:
            raise Exception('No current assetstore is set.')

        return cursor.next()
