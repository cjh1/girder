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


class AbstractAssetstoreAdapter(object):
    def initUpload(self, upload):
        """
        This must be called before any chunks are uploaded to do any
        additional behavior and optionally augment the upload document. The
        method must return the upload document. Default behavior is to
        simply return the upload document unmodified.
        :param upload: The upload document to optionally augment.
        :type upload: dict
        """
        return upload

    def uploadChunk(self, upload, chunk):
        """
        Call this method to process each chunk of an upload.
        :param upload: The upload document to update.
        :type upload: dict
        :param chunk: The file object representing the chunk that was uploaded.
        :type chunk: file
        :returns: Must return the upload document with any optional changes.
        """
        raise Exception('Must override processChunk in %s.'
                        % self.__class__.__name__)  # pragma: no cover

    def finalizeUpload(self, upload, file):
        """
        Call this once the last chunk has been processed. This method does not
        need to delete the upload document as that will be deleted by the
        caller afterward. This method may augment the File document, and must
        return the File document.
        :param upload: The upload document.
        :type upload: dict
        :param file: The file document that was created.
        :type file: dict
        :returns: The file document with optional modifications.
        """
        raise Exception('Must override finalizeUpload in %s.'
                        % self.__class__.__name__)  # pragma: no cover

    def deleteFile(self, file):
        """
        This is called when a File is deleted to allow the adapter to remove
        the data from within the assetstore. This method should not modify
        or delete the file object, as the caller will delete it afterward.
        :param file: The File document about to be deleted.
        :type file: dict
        """
        raise Exception('Must override deleteFile in %s.'
                        % self.__class__.__name__)  # pragma: no cover

    def downloadFile(self, file):
        """
        Downloads a file to the user.
        :param file: The file document being downloaded.
        :type file: dict
        """
        raise Exception('Must override downloadFile in %s.'
                        % self.__class__.__name__)  # pragma: no cover
