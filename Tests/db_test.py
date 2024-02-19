import unittest
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db_interface import db_interface, user_entry, calculate_expiration_date_timestamp

class TestDbInterface(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_db.sqlite"
        self.db = db_interface(self.db_name)
        self.uid = 12345
        self.csu_id = 67890
        self.name = "Test User"
        self.is_admin = 0
        self.expiration_date = calculate_expiration_date_timestamp()

    def tearDown(self):
        self.db.close()
        os.remove(self.db_name)

    def test_add_user(self):
        self.db.add_user(self.uid, self.csu_id, self.name)
        user = self.db.get_row_from_uid(self.uid)
        self.assertEqual(user.get_uid(), self.uid)
        self.assertEqual(user.get_csu_id(), self.csu_id)
        self.assertEqual(user.get_name(), self.name)
        self.assertEqual(user.is_admin(), False)

    def test_add_admin(self):
        self.db.add_admin(self.uid, self.csu_id, self.name)
        user = self.db.get_row_from_uid(self.uid)
        self.assertEqual(user.get_uid(), self.uid)
        self.assertEqual(user.get_csu_id(), self.csu_id)
        self.assertEqual(user.get_name(), self.name)
        self.assertEqual(user.is_admin(), True)

    def test_delete_entry(self):
        self.db.add_user(self.uid, self.csu_id, self.name)
        self.db.delete_entry(self.uid)
        user = self.db.get_row_from_uid(self.uid)
        self.assertIsNone(user)

    def test_is_admin(self):
        self.db.add_admin(self.uid, self.csu_id, self.name)
        self.assertTrue(self.db.is_admin(self.uid))

    def test_is_expired(self):
        self.db.add_user(self.uid, self.csu_id, self.name)
        self.assertFalse(self.db.is_expired(self.uid))

if __name__ == "__main__":
    unittest.main()