odoo.define('l10n_lv_check_company_registry.RegistryCheck', function (require) {
'use strict';

var core = require('web.core');
var data = require('web.data');
var session = require('web.session');
var SystrayMenu = require('web.SystrayMenu');
var Widget = require('web.Widget');
var form_common = require('web.form_common');
var Model = require('web.DataModel');

var ResPartner = new Model('res.partner');

var QWeb = core.qweb;

var RegistryCheckBtn = form_common.FormWidget.extend(form_common.ReinitializeWidgetMixin, {
    template:'l10n_lv_check_company_registry.RegistryCheck',
    init: function(parent, name) {
        this._super(parent, name);
    },
    start: function() {
        this._super.apply(this, arguments);
        this.$btns = this.$('button');
        this.$valid = this.$el.find('.valid');
        this.$('.source').text('Luresoft ');
        this.field_manager.on('field_changed:partner_registry', this, this.render_button);
        //this.field_manager.on('field_changed:individual_registry', this, this.render_button);
        this.on("change:effective_readonly", this, function() {
            this.render_button();
        });
        this.render_button()
    },
    events: {
        'click .btn-validate': 'fetch_registry',
        'click .btn-open-website': 'open_website',
    },
    render_button: function() {
        if (this.field_manager.get_field_value('registry_valid')) {
            this.$valid.show();
        } else {
            this.$valid.hide();
        }

        if (this.buttons_enabled()) {
            this.$btns.removeClass('disabled');
        } else {
            this.$btns.addClass('disabled');
        }
    },
    fetch_registry: function() {
        if (this.buttons_enabled()) {
            var registry = this.field_manager.get_field_value('partner_registry');
            var self = this;
            this.request = ResPartner.call('check_registry', [[], registry]).then(function(res) {
                self.field_manager.set_values($.extend(res, {'registry_valid': true}));
                self.render_button()
            });
        }
    },
    open_website: function(btn) {
        if (this.buttons_enabled()) {
            var registry = this.field_manager.get_field_value('partner_registry');
            window.open('http://company.lursoft.lv/'+registry, '_blank');
        }
    },
    buttons_enabled: function() {
        var pr = this.field_manager.get_field_value('partner_registry')
        return (!this.get('effective_readonly') && pr.length == 11)
    },
    //start: function() {
    //    this._super();
    //    //this.field_manager.on("field_changed:provider_latitude", this, this.display_map);
    //    //this.field_manager.on("field_changed:provider_longitude", this, this.display_map);
    //    //this.display_map();
    //},
    //display_map: function() {
    //    this.$el.html(QWeb.render("WidgetCoordinates", {
    //        "latitude": this.field_manager.get_field_value("provider_latitude") || 0,
    //        "longitude": this.field_manager.get_field_value("provider_longitude") || 0,
    //    }));
    //} 
});

core.form_custom_registry.add('registry_check_btn', RegistryCheckBtn);

});
