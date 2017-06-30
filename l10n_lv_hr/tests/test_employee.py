from odoo.tests.common import TransactionCase

class TestHrEmployee(TransactionCase):

    def test_create_gets_name_from_fistname_suname(self):
        record = self.env['hr.employee'].create({'firstname': 'firstname', 'surname': 'surname'})
        self.assertEqual(record.name, 'firstname surname')

    def test_create_recieves_name_and_firstname(self):
        record = self.env['hr.employee'].create({'name': 'fullname', 'firstname': 'firstname'})
        self.assertEqual(record.name, 'fullname')

    def test_create_with_no_fullname(self):
        record = self.env['hr.employee'].create({'surname': 'surname', 'firstname': 'firstname'})
        self.assertEqual(record.name, 'firstname surname')

    def test_write_drop_firstname_surname_if_name_in_values(self):
        record = self.env['hr.employee'].create({'name': 'f'})
        record.write({'name': 'full name', 'firstname': 'firstname'})
        self.assertEqual(record.name, 'full name')

    def test_write_firstname_surname_changes_fullname(self):
        record = self.env['hr.employee'].create({'surname': 's', 'firstname': 'f'})
        record.write({'surname': 'surname', 'firstname': 'firstname'})
        self.assertEqual(record.name, 'firstname surname')
