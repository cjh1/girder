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

from girder import events
from girder.utility import assetstore_utilities
from .model_base import Model, ValidationException
from ..constants import AccessType


class Upload(Model):
    """
    This model stores temporary records for uploads that have been approved
    but are not yet complete, so that they can be uploaded in chunks of
    arbitrary size. The chunks must be uploaded in order.
    """
    def initialize(self):
        self.name = 'upload'

    def validate(self, doc):
        if doc['size'] < 0:
            raise ValidationException('File size must not be negative.')
        if doc['received'] > doc['size']:
            raise ValidationException('Received bytes must not be larger than '
                                      'the total size of the upload.')

        doc['updated'] = datetime.datetime.now()

        return doc

    def handleChunk(self, upload, chunk):
        """
        When a chunk is uploaded, this should be called to process the chunk.
        If this is the final chunk of the upload, this method will finalize
        the upload automatically.
        :param upload: The upload document to update.
        :type upload: dict
        :param chunk: The file object representing the chunk that was uploaded.
        :type chunk: file
        """
        assetstore = self.model('assetstore').load(upload['assetstoreId'])
        adapter = assetstore_utilities.getAssetstoreAdapter(assetstore)

        upload = self.save(adapter.uploadChunk(upload, chunk))

        # If upload is finished, we finalize it
        if upload['received'] == upload['size']:
            return self.finalizeUpload(upload, assetstore)
        else:
            return upload

    def requestOffset(self, upload):
        """
        Requests the offset that should be used to resume uploading. This
        makes the request from the assetstore adapter.
        """
        assetstore = self.model('assetstore').load(upload['assetstoreId'])
        adapter = assetstore_utilities.getAssetstoreAdapter(assetstore)
        return adapter.requestOffset(upload)

    def finalizeUpload(self, upload, assetstore=None):
        """
        This should only be called manually in the case of creating an
        empty file, i.e. one that has no chunks.
        """
        if assetstore is None:
            assetstore = self.model('assetstore').load(upload['assetstoreId'])

        if 'fileId' in upload:  # Updating an existing file's contents
            file = self.model('file').load(upload['fileId'])

            # Delete the previous file contents from the containing assetstore
            assetstore_utilities.getAssetstoreAdapter(
                self.model('assetstore').load(
                    file['assetstoreId'])).deleteFile(file)

            item = self.model('item').load(file['itemId'], force=True)
            self.model('file').propagateSizeChange(
                item, upload['size'] - file['size'])

            # Update file info
            file['creatorId'] = upload['userId']
            file['created'] = datetime.datetime.now()
            file['assetstoreId'] = assetstore['_id']
            file['size'] = upload['size']
            self.model('file').save(file)
        else:  # Creating a new file record
            if upload['parentType'] == 'folder':
                # Create a new item with the name of the file.
                item = self.model('item').createItem(
                    name=upload['name'], creator={'_id': upload['userId']},
                    folder={'_id': upload['parentId']})
            else:
                item = self.model('item').load(id=upload['parentId'],
                                               objectId=True,
                                               user={'_id': upload['userId']},
                                               level=AccessType.WRITE)

            file = self.model('file').createFile(
                item=item, name=upload['name'], size=upload['size'],
                creator={'_id': upload['userId']}, assetstore=assetstore,
                mimeType=upload['mimeType'])

        adapter = assetstore_utilities.getAssetstoreAdapter(assetstore)
        file = adapter.finalizeUpload(upload, file)
        self.model('file').save(file)
        self.remove(upload)

        # Add an async event for handlers that wish to process this file.
        events.daemon.trigger('data.process', {
            'file': file,
            'assetstore': assetstore
        })

        return file

    def createUploadToFile(self, file, user, size):
        """
        Creates a new upload record into a file that already exists. This should
        be used when updating the contents of a file. Deletes any previous
        file content from the assetstore it was in. This will upload
        into the current assetstore rather than assetstore the file was
        previously contained in.

        :param file: The file record to update.
        :param user: The user performing this upload.
        :param size: The size of the new file contents.
        """
        assetstore = self.model('assetstore').getCurrent()
        adapter = assetstore_utilities.getAssetstoreAdapter(assetstore)
        now = datetime.datetime.now()

        upload = {
            'created': now,
            'updated': now,
            'userId': user['_id'],
            'fileId': file['_id'],
            'assetstoreId': assetstore['_id'],
            'size': size,
            'name': file['name'],
            'mimeType': file['mimeType'],
            'received': 0
        }
        upload = adapter.initUpload(upload)
        return self.save(upload)

    def createUpload(self, user, name, parentType, parent, size, mimeType):
        """
        Creates a new upload record, and creates its temporary file
        that the chunks will be written into. Chunks should then be sent
        in order using the _id of the upload document generated by this method.

        :param user: The user performing the upload.
        :type user: dict
        :param name: The name of the file being uploaded.
        :type name: str
        :param parentType: The type of the parent being uploaded into.
        :type parentType: str ('folder' or 'item')
        :param parent: The document representing the parent.
        :type parentId: dict
        :param size: Total size in bytes of the whole file.
        :type size: int
        :param mimeType: The mimeType of the file.
        :type mimeType: str
        :returns: The upload document that was created.
        """
        assetstore = self.model('assetstore').getCurrent()
        adapter = assetstore_utilities.getAssetstoreAdapter(assetstore)
        now = datetime.datetime.now()

        upload = {
            'created': now,
            'updated': now,
            'userId': user['_id'],
            'parentType': parentType.lower(),
            'parentId': parent['_id'],
            'assetstoreId': assetstore['_id'],
            'size': size,
            'name': name,
            'mimeType': mimeType,
            'received': 0
        }
        upload = adapter.initUpload(upload)
        return self.save(upload)
