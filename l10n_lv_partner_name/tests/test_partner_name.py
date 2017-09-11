from odoo.tests import common

class TestServerOnChange(common.TransactionCase):

    def setUp(self):
        super(TestServerOnChange, self).setUp()
        self.Partner = self.env['res.partner']

    #def test_setting_firstname_populates_name(self):
    #    res = self.Partner.create({'firstname': 'John'})
    #    self.assertEqual(res.name, res.firstname)

    def test_setting_fullname_changes_first_last_name(self):
        res = self.Partner.create({'name': 'John Mayer'})
        self.assertEqual('John', res.firstname)
        self.assertEqual('Mayer', res.surname)

    def test_updating_a_recordsets_name_sets_firstname_lastname_on_everything(self):
        res = self.Partner.create({'name': 'John Mayer'})
        res |= self.Partner.create({'name': 'Barbara Straisand'})
        res.write({'name': 'Mass Write'})
        self.assertEqual(len(set(res.mapped('firstname'))), 1)
        self.assertEqual(len(set(res.mapped('surname'))), 1)

    def test_setting_only_firstname_sets_name(self):
        res = self.Partner.create({'firstname': 'Mayer'})
        self.assertEqual(res.firstname, res.name)
