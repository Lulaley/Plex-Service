import ldap
import hashlib
import os
import base64
from .ControleurConf import ControleurConf

class ControleurLdap:
    def __init__(self):
        self.config = ControleurConf()
        self.server = self.config.get_config('LDAP', 'server')
        self.conn = ldap.initialize(self.server)

    def bind_as_root(self):
        try:
            root_dn = self.config.get_config('LDAP', 'root_dn')
            root_password = self.config.get_config('LDAP', 'root_password')
            password_ssha = self.convert_to_ssha(root_password)
            self.conn.simple_bind_s(root_dn, password_ssha)
            print("Connexion en tant que root réussie")
        except ldap.LDAPError as e:
            print("Erreur de connexion en tant que root:", e)

    def convert_to_ssha(self, password):
        salt = os.urandom(4)
        password_bytes = password.encode('utf-8')
        sha = hashlib.sha1(password_bytes)
        sha.update(salt)
        digest = sha.digest()
        password_ssha = base64.b64encode(digest + salt).decode('utf-8')
        return "{SSHA}" + password_ssha

    def authenticate_user(self, username, password):
        try:
            user_dn = self.search_user(username)
            if user_dn:
                password_sha = hashlib.sha1(password.encode()).hexdigest()
                self.conn.simple_bind_s(user_dn, password_sha)
                print("Authentification réussie")
                return True
            else:
                print("Utilisateur non trouvé")
                return False
        except ldap.LDAPError as e:
            print("Erreur d'authentification:", e)
            return False

    def search_user(self, username):
        try:
            search_base = self.config.get_config('LDAP', 'base_dn')
            search_filter = f"(uid={username})"
            result = self.conn.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter)
            if result:
                print("Utilisateur trouvé")
                return result[0][0]
            else:
                print("Utilisateur non trouvé")
                return None
        except ldap.LDAPError as e:
            print("Erreur lors de la recherche de l'utilisateur:", e)

    def add_entry(self, dn, attributes):
        try:
            self.conn.add_s(dn, attributes)
            print("Entrée ajoutée avec succès")
        except ldap.LDAPError as e:
            print("Erreur lors de l'ajout de l'entrée:", e)

    def delete_entry(self, dn):
        try:
            self.conn.delete_s(dn)
            print("Entrée supprimée avec succès")
        except ldap.LDAPError as e:
            print("Erreur lors de la suppression de l'entrée:", e)

    def modify_entry(self, dn, mod_list):
        try:
            self.conn.modify_s(dn, mod_list)
            print("Entrée modifiée avec succès")
        except ldap.LDAPError as e:
            print("Erreur lors de la modification de l'entrée:", e)

    def search_entry(self, search_base, search_filter):
        try:
            result = self.conn.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter)
            if result:
                print("Entrée trouvée")
                return result
            else:
                print("Entrée non trouvée")
                return None
        except ldap.LDAPError as e:
            print("Erreur lors de la recherche de l'entrée:", e)
    
    def disconnect(self):
        try:
            self.conn.unbind_s()
            print("Déconnexion LDAP réussie")
        except ldap.LDAPError as e:
            print("Erreur lors de la déconnexion LDAP:", e)