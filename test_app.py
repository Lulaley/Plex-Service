import unittest
from app import app

class TestLogin(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_login_success(self):
        response = self.app.post('/index', data=dict(
            username='chimea',
            password='S@r@h!Love78'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Connexion réussie!'.encode(), response.data)

    def test_login_failure(self):
        response = self.app.post('/index', data=dict(
            username='wronguser',
            password='wrongpassword'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Échec de la connexion'.encode(), response.data)

if __name__ == '__main__':
    unittest.main()