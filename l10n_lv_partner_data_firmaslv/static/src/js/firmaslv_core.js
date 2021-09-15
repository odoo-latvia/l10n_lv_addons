odoo.define('l10n_lv_partner_data_firmaslv.Mixin', function (require) {
'use strict';

var concurrency = require('web.concurrency');

var core = require('web.core');
var Qweb = core.qweb;

/**
 * This mixin only works with classes having EventDispatcherMixin in 'web.mixins'
 */
var FirmasLVMixin = {
    _dropPreviousFirmasLV: new concurrency.DropPrevious(),

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Get list of companies via firmas.lv API
     *
     * @param {string} value
     * @returns {Promise}
     * @private
     */
    _firmaslv: function (value) {
        var self = this;
        value = value.trim();
        var FirmasLVSuggestions = [];
        return new Promise(function (resolve, reject) {
            var FirmasLVPromise = self._getFirmasLVSuggestions(value).then(function (suggestions){
                FirmasLVSuggestions = suggestions;
            });

            var concatResults = function () {

                FirmasLVSuggestions = _.filter(FirmasLVSuggestions, function (suggestion) {
                    return !suggestion.ignored;
                });
                _.each(FirmasLVSuggestions, function(suggestion){
                delete suggestion.ignored;
                });
                return resolve(FirmasLVSuggestions);
            };

            self._whenAll([FirmasLVPromise]).then(concatResults, concatResults);
        });

    },

    /**
     * Get enrichment data
     *
     * @param {Object} company
     * @param {string} company.website
     * @param {string} company.partner_gid
     * @param {string} company.vat
     * @returns {Promise}
     * @private
     */
    _loadFirmasLVData: function (company) {
        var virtualid = company.virtualid;
        company.street = company.address;
        delete company.virtualid;
        delete company.address;
        delete company.status;
        delete company.src;
        return this._rpc({
            model: 'res.partner',
            method: 'load_firmaslv_data',
            args: [virtualid],
        });
    },

    /**
     * Get the company logo as Base 64 image from url
     *
     * @param {string} url
     * @returns {Promise}
     * @private
     */
    _getCompanyLogo: function (url) {
        return this._getBase64Image(url).then(function (base64Image) {
            // base64Image equals "data:" if image not available on given url
            return base64Image ? base64Image.replace(/^data:image[^;]*;base64,?/, '') : false;
        }).catch(function () {
            return false;
        });
    },

    /**
     * Get enriched data + logo before populating partner form
     *
     * @param {Object} company
     * @returns {Promise}
     */
    _getCreateData: function (company) {
        var self = this;

        var removeUselessFields = function (company) {
            var fields = 'label,description,domain,logo,legal_name,ignored,email'.split(',');
            fields.forEach(function (field) {
                delete company[field];
            });

            var notEmptyFields = "country_id,state_id".split(',');
            notEmptyFields.forEach(function (field) {
                if (!company[field]) delete company[field];
            });
        };

        return new Promise(function (resolve) {
            // Fetch additional company info via Firmas.lv API
            var enrichPromise = self._loadFirmasLVData(company);

            // Get logo
            var logoPromise = company.logo ? self._getCompanyLogo(company.logo) : false;
            self._whenAll([enrichPromise, logoPromise]).then(function (result) {
                var company_data = result[0];
                var logo_data = result[1];
 
                if (company_data.error && company_data.vat) {
                    company.vat = company_data.vat;
                }

                if (company_data.error) {
                    self.do_notify(false, company_data.error_message);
                    company_data = company;
                }

                if (_.isEmpty(company_data)) {
                    company_data = company;
                }

                // Delete attribute to avoid "Field_changed" errors
                removeUselessFields(company_data);

                // Assign VAT coming from parent VIES VAT query
                if (company.vat) {
                    company_data.vat = company.vat;
                }
                resolve({
                    company: company_data,
                    logo: logo_data
                });
            });
        });
    },

    /**
     * Check connectivity
     *
     * @returns {boolean}
     */
    _isOnline: function () {
        return navigator && navigator.onLine;
    },

    /**
     * Validate: Not empty and length > 1
     *
     * @param {string} search_val
     * @param {string} onlyVAT : Only valid VAT Number search
     * @returns {boolean}
     * @private
     */
    _validateSearchTerm: function (search_val, onlyVAT) {
        if (onlyVAT) return this._isVAT(search_val);
        else return search_val && search_val.length > 2;
    },

    /**
     * Use FirmasLV API to return suggestions
     *
     * @param {string} value
     * @returns {Promise}
     * @private
     */
    _getFirmasLVSuggestions: function (value) {
        var self = this;
        var def = this._rpc({
            model: 'res.partner',
            method: 'load_firmaslv_suggestions',
            args: [value, this.name],
        }, {
            shadow: true,
        }).then(function (suggestions) {
            var rem_ind = -1;
            suggestions.map(function (suggestion) {
                if (suggestion.error) {
                    self.do_notify(false, suggestion.error_message);
                    rem_ind = suggestions.indexOf(suggestion);
                }
                suggestion.logo = suggestion.logo || '';
                suggestion.label = suggestion.legal_name || suggestion.name;
                if (suggestion.vat) suggestion.description = suggestion.vat;
                else if (suggestion.website) suggestion.description = suggestion.website;

                if (suggestion.country_id && suggestion.country_id.display_name) {
                    if (suggestion.description) suggestion.description += _.str.sprintf(' (%s)', suggestion.country_id.display_name);
                    else suggestion.description += suggestion.country_id.display_name;
                }

                return suggestion;
            });
            if (rem_ind > -1) {
                suggestions.splice(rem_ind, 1);
            }
            return suggestions;
        });

        return this._dropPreviousFirmasLV.add(def);
    },

    /**
     * Utility to wait for multiple promises
     * Promise.all will reject all promises whenever a promise is rejected
     * This utility will continue
     *
     * @param {Promise[]} promises
     * @returns {Promise}
     * @private
     */
    _whenAll: function (promises) {
        return Promise.all(promises.map(function (p) {
            return Promise.resolve(p);
        }));
    },

};

return FirmasLVMixin;

});
