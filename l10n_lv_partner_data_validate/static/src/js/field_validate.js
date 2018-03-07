odoo.define('web.lv_reg_no', function (require) {
"use strict"

var core = require('web.core')
var registry = require('web.field_registry')
var basic_fields = require('web.basic_fields')

var _t = core._t

// TODO ability to add country field constraint
var FieldRegNo = basic_fields.FieldChar.extend({
    DEBOUNCE: 100,
    resetOnAnyFieldChange: true, // Have to listen to country changes
    _parseValue: function (value) {
        const parsed_value = this._super.apply(this, arguments)

        if (! this.validate(parsed_value)) {
            throw Exception('Invalid registry')
        }
        return value
    },
    // revalidate regno on country change
    reset: function() {
        const def = this._super.apply(this, arguments)
        this._doAction()
        return def
    },
    _doAction: function() {
        const res = this._super.apply(this, arguments)
        this.toggleValid(this.isValid())
        return res
    },
    toggleValid: function(valid) {
        this.$el.toggleClass('o_field_invalid', !valid)
    },
    isCompany: function() {
        return this.record.data[this.nodeOptions.is_company_field]
    },
    checksum: function(number) {
        const weights = [9, 1, 4, 8, 3, 10, 2, 5, 7, 6, 1]
        return number.split('').map(Number).reduce((acc, n, i) => {
            return acc + (n * weights[i])
        }, 0) % 11
    },
    partnerFromLatvia: function() {
        return (this.nodeOptions.country_code_field
            && this.record.data[this.nodeOptions.country_code_field] == 'LV')
    },
    validate: function(value) {
        if (this.partnerFromLatvia()) {
            if (! value.match(/\d{11}/)) {
                return false
            }
            else {
                return this.checksum(value) === 3
            }
        }
        else {
            return true
        }
    }
})

registry.add('regno', FieldRegNo)

return {
    RegNo: FieldRegNo,
}

})
