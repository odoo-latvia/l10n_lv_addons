odoo.define('web.pk_validate_widget', function (require) {
"use strict";

var core = require('web.core');
var Model = require('web.Model');
var formWidget = require('web.form_widgets');

var _t = core._t;
var Partner = new Model('res.partner');
var Country = new Model('res.country');

// TODO: make parametarized, not dependent on specific fields in the form
// aka. make it a widget type
// TODO: parametarize country field
var FieldRegistry = formWidget.FieldChar.extend({
    init: function (field_manager, node) {
        this._super(field_manager, node);
        this.events.keyup = this.proxy(this.validate);
        this.events.blur = this.proxy(this.validate_blur);
        this.show_error = true;
    },
    show_warning: function() {
        this.trigger('invalid');
        if (this.show_error) {
            this.show_error = false;
            this.do_warn.apply(this, arguments);

            setTimeout((function () {
               this.show_error = true; 
            }).bind(this), 3000);
        }
    }, 
    is_latvia: function() {
        return (this.field_manager.fields.country_id &&
                this.field_manager.fields.country_code.get_value() == 'LV');
    },
    get_pk: function() {
        return this.parse_value(this.$input.val(), '').replace('-', '');
    },
    validate_blur: function() {
        if (this.is_latvia()) {
            var value = this.get_pk();

            if (value.length < 11 && value.length != 0) {
                this.$input.addClass('o_form_invalid');
                this.do_warn(_t('Validation error'), _t('Number too short'));
            }
        }
    },
    validate: function() {
        if (this.is_latvia()) {

            var value = this.get_pk();

            if (value.length > 11) {
                this.$input.addClass('o_form_invalid');
                this.show_warning(_t('Validation error'), _t('Number too long'));

            } else if (value.length == 11) {

                Partner.call('frontend_check', [value]).then((function (valid) {
                    if (!valid) {
                        this.$input.addClass('o_form_invalid');
                        this.show_warning(_t('Validation error'), _t('Invalid registry number'));
                    } else {
                        this.$input.removeClass('o_form_invalid');
                        this.trigger('valid');
                    }
                }).bind(this))

			}
		}
    }
});

core.form_widget_registry
    .add('registry', FieldRegistry);

return FieldRegistry

});
