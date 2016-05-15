var _             = require('underscore');
var $             = require('jquery');
var Rest          = require('girder/rest');
var Model         = require('girder/model').Model;
var MetadataMixin = require('girder/model').MetadataMixin;
var FolderModel   = require('girder/models/FolderModel');

var ItemModel = Model.extend({
    resourceName: 'item',

    /**
     * Get the access level of the item if it is set. Takes an optional callback
     * to be called once the access level is fetched (or immediately if it has
     * already been fetched).
     */
    getAccessLevel: function (callback) {
        callback = callback || $.noop;

        if (this.has('_accessLevel')) {
            callback(this.get('_accessLevel'));
            return this.get('_accessLevel');
        }
        if (this.parent && this.parent.getAccessLevel()) {
            this.set('_accessLevel', this.parent.getAccessLevel());
            callback(this.get('_accessLevel'));
            return this.get('_accessLevel');
        } else {
            this.parent = new FolderModel();
            this.parent.set({
                _id: this.get('folderId')
            }).once('g:fetched', function () {
                this.set('_accessLevel', this.parent.getAccessLevel());
                callback(this.get('_accessLevel'));
            }, this).fetch();
        }
    },

    /**
     * Get the path to the root of the hierarchy
     */
    getRootPath: function (callback) {
        Rest.restRequest({
            path: this.resourceName + '/' + this.get('_id') + '/rootpath'
        }).done(_.bind(function (resp) {
            callback(resp);
        }, this)).error(_.bind(function (err) {
            this.trigger('g:error', err);
        }, this));
    }
});

_.extend(ItemModel.prototype, MetadataMixin);

module.exports = ItemModel;
