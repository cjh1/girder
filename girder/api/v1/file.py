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

import cherrypy

from ..describe import Description
from ..rest import Resource, RestException, loadmodel
from ...constants import AccessType
from girder.models.model_base import AccessException


class File(Resource):
    """
    API Endpoint for files. Includes utilities for uploading and downloading
    them.
    """
    def __init__(self):
        self.resourceName = 'file'
        self.route('DELETE', (':id',), self.deleteFile)
        self.route('GET', ('offset',), self.requestOffset)
        self.route('GET', (':id', 'download'), self.download)
        self.route('GET', (':id', 'download', ':name'), self.download)
        self.route('POST', (), self.initUpload)
        self.route('POST', ('chunk',), self.readChunk)
        self.route('POST', ('completion',), self.finalizeUpload)
        self.route('PUT', (':id',), self.updateFile)
        self.route('PUT', (':id', 'contents'), self.updateFileContents)

    def initUpload(self, params):
        """
        Before any bytes of the actual file are sent, a request should be made
        to initialize the upload. This creates the temporary record of the
        forthcoming upload that will be passed in chunks to the readChunk
        method. If you pass a "linkUrl" parameter, it will make a link file
        in the designated parent.
        """
        self.requireParams(('name', 'parentId', 'parentType'), params)
        user = self.getCurrentUser()

        mimeType = params.get('mimeType', None)
        parentType = params['parentType'].lower()

        if parentType not in ('folder', 'item'):
            raise RestException('The parentType must be "folder" or "item".')

        parent = self.model(parentType).load(id=params['parentId'], user=user,
                                             level=AccessType.WRITE, exc=True)

        if 'linkUrl' in params:
            return self.model('file').createLinkFile(
                url=params['linkUrl'], parent=parent, name=params['name'],
                parentType=parentType, creator=user)
        else:
            self.requireParams('size', params)
            upload = self.model('upload').createUpload(
                user=user, name=params['name'], parentType=parentType,
                parent=parent, size=int(params['size']), mimeType=mimeType)
            if upload['size'] > 0:
                return upload
            else:
                return self.model('upload').finalizeUpload(upload)
    initUpload.description = (
        Description('Start a new upload or create an empty or link file.')
        .responseClass('Upload')
        .param('parentType', 'Type being uploaded into (folder or item).')
        .param('parentId', 'The ID of the parent.')
        .param('name', 'Name of the file being created.')
        .param('size', 'Size in bytes of the file.',
               dataType='integer', required=False)
        .param('mimeType', 'The MIME type of the file.', required=False)
        .param('linkUrl', 'If this is a link file, pass its URL instead'
               'of size and mimeType using this parameter.', required=False)
        .errorResponse()
        .errorResponse('Write access was denied on the parent folder.', 403))

    def finalizeUpload(self, params):
        self.requireParams('uploadId', params)
        user = self.getCurrentUser()

        upload = self.model('upload').load(params['uploadId'], exc=True)

        if upload['userId'] != user['_id']:
            raise AccessException('You did not initiate this upload.')

        return self.model('upload').finalizeUpload(upload)
    finalizeUpload.description = (
        Description('Finalize an upload explicitly if necessary.')
        .notes('This is only required in certain non-standard upload '
               'behaviors. Clients should know which behavior models require '
               'the finalize step to be called in their behavior handlers.')
        .param('uploadId', 'The ID of the upload record.', paramType='form')
        .errorResponse('ID was invalid.')
        .errorResponse('The upload does not require finalization.')
        .errorResponse('You are not the user who initiated the upload.', 403))

    def requestOffset(self, params):
        """
        This should be called when resuming an interrupted upload. It will
        report the offset into the upload that should be used to resume.
        :param uploadId: The _id of the temp upload record being resumed.
        :returns: The offset in bytes that the client should use.
        """
        self.requireParams('uploadId', params)
        upload = self.model('upload').load(params['uploadId'], exc=True)
        offset = self.model('upload').requestOffset(upload)

        if type(offset) is int:
            upload['received'] = offset
            self.model('upload').save(upload)
            return {'offset': offset}
        else:
            return offset

    requestOffset.description = (
        Description('Request required offset before resuming an upload.')
        .param('uploadId', 'The ID of the upload record.')
        .errorResponse("The ID was invalid, or the offset did not match the "
                       "server's record."))

    def readChunk(self, params):
        """
        After the temporary upload record has been created (see initUpload),
        the bytes themselves should be passed up in ordered chunks. The user
        must remain logged in when passing each chunk, to authenticate that
        the writer of the chunk is the same as the person who initiated the
        upload. The passed offset is a verification mechanism for ensuring the
        server and client agree on the number of bytes sent/received.
        """
        self.requireParams(('offset', 'uploadId', 'chunk'), params)
        user = self.getCurrentUser()

        if not user:
            raise AccessException('You must be logged in to upload.')

        upload = self.model('upload').load(params['uploadId'], exc=True)
        offset = int(params['offset'])
        chunk = params['chunk']

        if upload['userId'] != user['_id']:
            raise AccessException('You did not initiate this upload.')

        if upload['received'] != offset:
            raise RestException(
                'Server has received {} bytes, but client sent offset {}.'
                .format(upload['received'], offset))

        if type(chunk) == cherrypy._cpreqbody.Part:
            return self.model('upload').handleChunk(upload, chunk.file)
        else:
            return self.model('upload').handleChunk(upload, chunk)
    readChunk.description = (
        Description('Upload a chunk of a file with multipart/form-data.')
        .consumes('multipart/form-data')
        .param('uploadId', 'The ID of the upload record.', paramType='form')
        .param('offset', 'Offset of the chunk in the file.', dataType='integer',
               paramType='form')
        .param('chunk', 'The actual bytes of the chunk. For external upload '
               'behaviors, this may be set to an opaque string that will be '
               'handled by the assetstore adapter.',
               dataType='File', paramType='body')
        .errorResponse('ID was invalid.')
        .errorResponse('You are not the user who initiated the upload.', 403))

    @loadmodel(map={'id': 'file'}, model='file')
    def download(self, file, params, name=None):
        """
        Defers to the underlying assetstore adapter to stream a file out.
        Requires read permission on the folder that contains the file's item.
        """
        offset = int(params.get('offset', 0))
        user = self.getCurrentUser()

        self.model('item').load(id=file['itemId'], user=user,
                                level=AccessType.READ, exc=True)
        return self.model('file').download(file, offset)
    download.description = (
        Description('Download a file.')
        .param('id', 'The ID of the file.', paramType='path')
        .errorResponse('ID was invalid.')
        .errorResponse('Read access was denied on the parent folder.', 403))

    @loadmodel(map={'id': 'file'}, model='file')
    def deleteFile(self, file, params):
        user = self.getCurrentUser()
        self.model('item').load(id=file['itemId'], user=user,
                                level=AccessType.WRITE, exc=True)
        self.model('file').remove(file)
    deleteFile.description = (
        Description('Delete a file by ID.')
        .param('id', 'The ID of the file.', paramType='path')
        .errorResponse('ID was invalid.')
        .errorResponse('Write access was denied on the parent folder.', 403))

    @loadmodel(map={'id': 'file'}, model='file')
    def updateFile(self, file, params):
        self.model('item').load(id=file['itemId'], user=self.getCurrentUser(),
                                level=AccessType.WRITE, exc=True)
        file['name'] = params.get('name', file['name']).strip()
        file['mimeType'] = params.get('mimeType', file['mimeType']).strip()
        return self.model('file').save(file)
    updateFile.description = (
        Description('Change file metadata such as name or MIME type.')
        .param('id', 'The ID of the file.', paramType='path')
        .param('name', 'The name to set on the file.', required=False)
        .param('mimeType', 'The MIME type of the file.', required=False)
        .errorResponse('ID was invalid.')
        .errorResponse('Write access was denied on the parent folder.', 403))

    @loadmodel(map={'id': 'file'}, model='file')
    def updateFileContents(self, file, params):
        self.requireParams('size', params)
        self.model('item').load(id=file['itemId'], user=self.getCurrentUser(),
                                level=AccessType.WRITE, exc=True)

        # Create a new upload record into the existing file
        upload = self.model('upload').createUploadToFile(
            file=file, user=self.getCurrentUser(), size=int(params['size']))

        if upload['size'] > 0:
            return upload
        else:
            return self.model('upload').finalizeUpload(upload)
    updateFileContents.description = (
        Description('Change the contents of an existing file.')
        .param('id', 'The ID of the file.', paramType='path')
        .param('size', 'Size in bytes of the new file.', dataType='integer')
        .notes('After calling this, send the chunks just like you would with a '
               'normal file upload.'))
