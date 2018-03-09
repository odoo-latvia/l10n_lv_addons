odoo.define('l10n_lv_partner_data_load.RegistryCheck', function (require) {
'use strict';

const ajax = require('web.ajax')
const crash_manager = require('web.crash_manager')
const core = require('web.core');
const Dialog = require('web.Dialog')
const Widget = require('web.Widget');
const lv_reg_no = require('web.lv_reg_no');
const widget_registry = require('web.widget_registry');

const QWeb = core.qweb;

// cache
const vendors = Object.create(null)

const RegistryCheckBtn = lv_reg_no.RegNo.include({
    vendors: vendors,
    start: function() {
        this.$btnCheckRegno = this._renderRegnoButton()
        return this._super.apply(this, arguments)
    },
    willStart: function() {
        const def = this._super.apply(this, arguments)
        if (!Object.keys(this.vendors).length) {

            const vendors = ajax.rpc('/l10n_lv_partner_data_load/vendors').then(function(vendors) {
                this.vendors = JSON.parse(vendors)
            }.bind(this))

            return $.when(def, vendors)
        }
        return def
    },
    _renderEdit: function() {
        const def = this._super.apply(this, arguments)
        this._rerenderButtons()
        return def
    },
    _rerenderButtons: function() {
        if (this.partnerFromLatvia() && this.isCompany()) {
            this.$btnCheckRegno.insertAfter(this.$el)
        }
        else if (this.$btnCheckRegno) {
            this.$btnCheckRegno.detach()
        }
    },
    _renderRegnoButton: function() {
        return Object.entries(this.vendors).map(([vendor, params]) => {

            let primaryBtn = $('<button/>', {
                type: 'button',
                text: params.label,
                'class': 'fetch-regno-btn btn btn-default',
                'data-vendor': vendor,
            }).on('click', this.fetch_by_regno.bind(this, vendor))

            let secondaryBtn = $('<button/>', {
                type: 'button',
                'class': 'fetch-regno-btn btn btn-default',
            }).on('click', this.open_website.bind(this, vendor))
                .append($('<i class="fa fa-share-square-o" aria-hidden="true"></i>'))

            return primaryBtn.add(secondaryBtn)

        }).reduce((agg, btn) => {
            return agg.append(btn)
        }, $('<div/>', {'class': 'btn-group', 'role': 'group'}))
    },
    toggleButtons: function(show) {
        const bool = show || !(this.isValid() && this.isCompany())
        this.$btnCheckRegno.find('button')
            .prop('disabled', _ => bool)
    },
    _doAction: function() {
        const res = this._super.apply(this, arguments)
        this.toggleButtons()

        // Set country_id to "Latvia". Delete a character in partner_registry
        // to invalidate the code. Change the country. When the widget is
        // reinitialized _render is not called yet _reset is. As a consequence the buttons ar nether disabled or hidden. To cover this case
        // call btnCheckRegno here.
        this._rerenderButtons()
    },
    fetch_by_regno: function(vendor) {
        const value = this._getValue()
        const self = this
        //ajax.rpc(`/l10n_lv_partner_data_load/${vendor}/${value}`).then(info => {
        this._rpc({
                route: `/l10n_lv_partner_data_load/${vendor}/${value}`
                }).then(info => {
            if (info.error) {
                this.do_warn(this.vendors[vendor].label, info.error)
            }
            else {
                this.trigger_up('field_changed', {
                    dataPointID: self.dataPointID,
                    changes: info,
                })
            }
        }).fail(err => {
            this.do_warn('Request failed. Try again later!')
        })
    },
    open_website: function(vendor) {
        window.open(`/l10n_lv_partner_data_load/goto/${vendor}/${this._getValue()}`)
    },
});

widget_registry.add('check_regno', RegistryCheckBtn); 
});
