var girder       = require('girder/init');
var Auth         = require('girder/auth');
var Events       = require('girder/events');
var UserModel    = require('girder/models/UserModel');
var DialogHelper = require('girder/utilities/DialogHelper');
var View         = require('girder/view');

/**
 * This view shows a register modal dialog.
 */
var RegisterView = View.extend({
    events: {
        'submit #g-register-form': function (e) {
            e.preventDefault();

            this.$('.form-group').removeClass('has-error');

            if (this.$('#g-password').val() !== this.$('#g-password2').val()) {
                this.$('#g-group-password,#g-group-password2').addClass('has-error');
                this.$('#g-password').focus();
                this.$('.g-validation-failed-message').text('Passwords must match.');
                return;
            }

            var user = new UserModel({
                login: this.$('#g-login').val(),
                password: this.$('#g-password').val(),
                email: this.$('#g-email').val(),
                firstName: this.$('#g-firstName').val(),
                lastName: this.$('#g-lastName').val()
            });
            user.on('g:saved', function () {
                if (Auth.getCurrentUser()) {
                    this.trigger('g:userCreated', {
                        user: user
                    });
                } else {
                    var authToken = user.get('authToken') || {};

                    Auth.setCurrentUser(user);
                    Auth.setCurrentToken(authToken.token);

                    if (Auth.corsAuth) {
                        document.cookie = 'girderToken=' + Auth.getCurrentToken();
                    }

                    DialogHelper.handleClose('register', {replace: true});
                    Events.trigger('g:login');
                }

                this.$el.modal('hide');
            }, this).on('g:error', function (err) {
                var resp = err.responseJSON;
                this.$('.g-validation-failed-message').text(resp.message);
                if (resp.field) {
                    this.$('#g-group-' + resp.field).addClass('has-error');
                    this.$('#g-' + resp.field).focus();
                }
                this.$('#g-register-button').removeClass('disabled');
            }, this).save();

            this.$('#g-register-button').addClass('disabled');
            this.$('.g-validation-failed-message').text('');
        },

        'click a.g-login-link': function () {
            Events.trigger('g:loginUi');
        }
    },

    render: function () {
        var view = this;
        this.$el.html(girder.templates.registerDialog({
            currentUser: Auth.getCurrentUser(),
            title: Auth.getCurrentUser() ? 'Create new user' : 'Sign up'
        })).girderModal(this)
            .on('shown.bs.modal', function () {
                view.$('#g-login').focus();
            }).on('hidden.bs.modal', function () {
                DialogHelper.handleClose('register', {replace: true});
            });
        this.$('#g-login').focus();

        DialogHelper.handleOpen('register', {replace: true});

        return this;
    }

});

module.exports = RegisterView;
