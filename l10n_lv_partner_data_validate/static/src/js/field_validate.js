odoo.define('web.pk_validate_widget', function (require) {
"use strict";

var core = require('web.core');
var Model = require('web.Model');
var formWidget = require('web.form_widgets');

var _t = core._t;
var Partner = new Model('res.partner');
var Country = new Model('res.country');

var FieldRegistry = formWidget.FieldChar.extend({
    init: function (field_manager, node) {
        this._super(field_manager, node);
        this.events.input = this.proxy(this.validate);
        this.show_error = true;
    },
    show_warning: function() {
        if (this.show_error) {
            this.show_error = false;
            this.do_warn.apply(this, arguments);

            setTimeout((function () {
               this.show_error = true; 
            }).bind(this), 3000);
        }
    }, 
    get_pk: function() {
        return this.parse_value(this.$input.val(), '').replace('-', '');
    },
    validate: function() {
        // FIXME: hack around bug
        if (!this.$input) return false;

        var value = this.get_pk();

        if (value.length != 11) {
            this.$input.addClass('o_form_invalid');
            this.set('valid', false);
        }
        else {

            Partner.call('frontend_check', [value]).then((function (valid) {
                if (!valid) {
                    this.$input.addClass('o_form_invalid');
                    this.show_warning(_t('Validation error'), _t('Invalid registry number'));
                    this.set('valid', false);
                } else {
                    this.$input.removeClass('o_form_invalid');
                    this.set('valid', true);
                }

            }).bind(this))

        }

    }
});

core.form_widget_registry
    .add('registry', FieldRegistry);

return FieldRegistry

});
