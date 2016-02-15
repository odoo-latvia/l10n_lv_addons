# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2016 ITS-1 (<http://www.its1.lv/>)
#                       E-mail: <info@its1.lv>
#                       Address: <Vienibas gatve 109 LV-1058 Riga Latvia>
#                       Phone: +371 66116534
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError
from operator import itemgetter

class ResPartner(models.Model):
    _inherit = "res.partner"

    allow_creation = fields.Boolean('Allow similar Partner creation')

    @api.model
    def _form_name(self, name):
        new_name = name.upper()
        replace_list = ['SIA', 'IU', 'I/U', 'AS', 'A/S', u'SABIEDRĪBA', 'LTD', 'CORP', 'INC']
        for value in replace_list:
            new_name_l = new_name.split(" ")
            for v in new_name_l:
                v1 = v.replace(",","").replace(" ","").replace('"',"").replace("'","")
                if value == v1:
                    new_name_l.remove(v)
            new_name = " ".join(new_name_l)
            new_name = new_name.strip().strip(",").replace('"',"").replace("'","")
        return new_name

    @api.model
    def test_partners(self, name, company_registry, identification_id, parent_id, partner_id=False):
        test_name = False
        parent_name = ''
        if name:
            test_name = self._form_name(name)
            test_name = test_name.encode('utf-8')
        partner_domain = []
        ename = _("partner")
        enames = _("partners")
        if parent_id:
            ename = _("contact")
            enames = _("contacts")
            partner_domain.append(('parent_id','=',parent_id))
            parent = self.browse(parent_id)
            if parent:
                parent_name = parent.name
        if partner_id:
            partner_domain.append(('id','!=',partner_id))
        partner_ids = []
        err_text = ""
        if test_name:
            partner_name_domain = partner_domain[:]
            self._cr.execute("""CREATE OR REPLACE FUNCTION array_remove_txtfromlst(inputarr TEXT[], inputtxt TEXT)
RETURNS text[] AS $outputarr$
DECLARE
    outputarr text[];
BEGIN
    FOR i IN array_lower(inputarr, 1) .. array_upper(inputarr, 1)
    LOOP
        IF inputarr[i] != inputtxt THEN
            outputarr = array_append(outputarr, inputarr[i]);
        END IF;
    END LOOP;
    RETURN outputarr;
END;
$outputarr$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION form_name_fromtxt(srcname TEXT)
RETURNS text AS $resname$
DECLARE
    new_srcname text;
    textlist text[];
    replacelist text[];
    rpl int;
    rplval text;
    t int;
    tval text;
    t1 text;
    resname text;
BEGIN
    replacelist =  array['SIA', 'IU', 'I/U', 'AS', 'A/S', 'SABIEDRĪBA', 'LTD', 'CORP', 'INC'];
    new_srcname = upper(srcname);
    FOR rpl IN array_lower(replacelist, 1) .. array_upper(replacelist, 1)
    LOOP
        rplval = replacelist[rpl];
        textlist = string_to_array(new_srcname, ' ');
        IF array_lower(textlist, 1) != NULL THEN
            FOR t IN array_lower(textlist, 1) .. array_upper(textlist, 1)
            LOOP
                tval = textlist[t];
                t1 = replace(replace(replace(replace(tval,',',''),' ',''),'"',''),'''','');
                IF rplval = t1 THEN
                    textlist = array_remove_txtfromlst(textlist, tval);
                END IF;
            END LOOP;
            new_srcname = array_to_string(textlist, ' ');
            new_srcname = replace(replace((trim(both ',' from (trim(both ' ' from new_srcname)))),'"',''),'''','');
        END IF;
    END LOOP;
    resname = new_srcname;
    RETURN resname;
END;
$resname$ LANGUAGE plpgsql;

select id from res_partner
where char_length(form_name_fromtxt(name)) > 1 and (convert_from(convert_to(form_name_fromtxt(name),'utf-8'),'utf-8') like concat('%%','%s','%%') or '%s' like concat('%%',convert_from(convert_to(form_name_fromtxt(name),'utf-8'),'utf-8'),'%%'));""" % (test_name, test_name))
            sp_ids = map(itemgetter(0), self._cr.fetchall())
            partner_name_domain.append(('id','in',sp_ids))
            partner_name_ids = self.search(partner_name_domain)
            partner_ids += partner_name_ids
            pname_count = len(partner_name_ids)
            inp_text = "."
            if pname_count != 0:
                inp_text = ""
                if parent_id:
                    inp_text += _(" for partner %s") % parent_name
                pn_ids = partner_name_ids
                if pname_count > 6:
                    pn_ids = pn_ids[:6]
                p_names = [p.name for p in pn_ids]
                p_names = ", ".join(p_names)
                inp_text += ": %s" % p_names
                inp_text += (pname_count > 6 and "..." or ".")
            err_text += _("%s %s found with similar name%s") % (pname_count, enames, inp_text)
        if company_registry:
            partner_reg_domain = partner_domain[:]
            partner_reg_domain.append(('is_company','=',True))
            partner_reg_domain.append(('company_registry','=',company_registry))
            partner_reg_ids = self.search(partner_reg_domain)
            partner_ids += partner_reg_ids
            preg_count = len(partner_reg_ids)
            inp_text = "."
            if preg_count != 0:
                pr_ids = partner_reg_ids
                if preg_count > 6:
                    pr_ids = pr_ids[:6]
                p_names = [p.name for p in pr_ids]
                p_names = ", ".join(p_names)
                inp_text = ": %s" % p_names
                inp_text += (preg_count > 6 and "..." or ".")
            err_text += _("%s %s found with the same company registry%s") % (preg_count, enames, inp_text)
        if identification_id:
            partner_id_domain = partner_domain[:]
            partner_id_domain.append(('is_company','=',False))
            partner_id_domain.append(('identification_id','=',identification_id))
            partner_id_ids = self.search(partner_id_domain)
            partner_ids += partner_id_ids
            pid_count = len(partner_id_ids)
            inp_text = "."
            if pid_count != 0:
                inp_text = ""
                if parent_id:
                    inp_text += _(" for partner %s") % parent_name
                pi_ids = partner_id_ids
                if pid_count > 6:
                    pi_ids = pi_ids[:6]
                p_names = [p.name for p in pi_ids]
                p_names = ", ".join(p_names)
                inp_text += ": %s" % p_names
                inp_text += (pid_count > 6 and "..." or ".")

            err_text += _("%s %s found with the same identification ID%s") % (pid_count, enames, inp_text)
        if partner_ids:
            err_text2 = _("Check the 'Allow similar Partner creation' box and try again if you want to save the %s anyway.") % ename
            error_text = "%s %s" % (err_text, err_text2)
            raise ValidationError(error_text)
        return False

    @api.model
    def create(self, vals):
        if 'allow_creation' not in vals or vals['allow_creation'] == False:
            name = vals.get('name',False)
            company_registry = vals.get('company_registry',False)
            identification_id = vals.get('identification_id',False)
            parent_id = vals.get('parent_id',False)
            self.test_partners(name, company_registry, identification_id, parent_id)
        return super(ResPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        partner_obj = self.env['res.partner']
        for partner in self:            
            if ('allow_creation' in vals and vals['allow_creation'] == False) or ('allow_creation' not in vals and partner.allow_creation == False):
                name = 'name' in vals and vals['name'] or partner.name
                company_registry = 'company_registry' in vals and vals['company_registry'] or partner.company_registry
                identification_id = 'identification_id' in vals and vals['identification_id'] or partner.identification_id
                parent_id = 'parent_id' in vals and vals['parent_id'] or (partner.parent_id and partner.parent_id.id or False)
                if name or company_registry or identification_id or parent_id:
                    self.test_partners(name, company_registry, identification_id, parent_id, partner_id=partner.id)
        return super(ResPartner, self).write(vals)

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({'allow_creation': True})
        return super(ResPartner, self).copy(cr, uid, id, default, context)

class ResUsers(models.Model):
    _inherit = "res.users"

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({'allow_creation': True})
        return super(ResUsers, self).copy(cr, uid, id, default, context)

    @api.model
    def create(self, vals):
        self = self.with_context(self._context, default_allow_creation=True)
        return super(ResUsers, self).create(vals)

class ResCompany(models.Model):
    _inherit = "res.company"

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({'allow_creation': True})
        return super(ResCompany, self).copy(cr, uid, id, default, context)

    @api.model
    def create(self, vals):
        self = self.with_context(self._context, default_allow_creation=True)
        return super(ResCompany, self).create(vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: