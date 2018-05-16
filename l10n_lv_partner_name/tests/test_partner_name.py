from odoo.tests import common

# Start server with `-i l10n_lv_partner_name --test-enable` look for output

class TestServerOnChange(common.TransactionCase):

    def setUp(self):
        super(TestServerOnChange, self).setUp()
        self.Partner = self.env['res.partner']

    def test_setting_fullname_changes_first_last_name(self):
        res = self.Partner.create({'name': 'John Mayer', 'is_company': False})
        self.assertEqual('John', res.firstname)
        self.assertEqual('Mayer', res.surname)

    def test_updating_a_recordsets_name_sets_firstname_lastname_on_all_records(self):
        res = self.Partner.create({'name': 'John Mayer', 'is_company': False})
        res |= self.Partner.create({'name': 'Barbara Straisand'})
        res.write({'name': 'Mass Write'})
        self.assertEqual(len(set(res.mapped('firstname'))), 1)
        self.assertEqual(len(set(res.mapped('surname'))), 1)

    def test_setting_only_firstname_sets_name(self):
        res = self.Partner.create({'firstname': 'Mayer', 'is_company': False})
        self.assertEqual(res.firstname, res.name)
