import ldap
from .ControleurConf import ControleurConf

class ControleurLdap:
    def __init__(self):
        self.config = ControleurConf()
        self.server = self.config.get_config('ldap', 'server')
        self.conn = ldap.initialize(self.server)

    def bind_as_root(self):
        try:
            root_dn = self.config.get_config('ldap', 'root_dn')
            root_password = self.config.get_config('ldap', 'root_password')
            self.conn.simple_bind_s(root_dn, root_password)
            print("Connexion en tant que root réussie")
        except ldap.LDAPError as e:
            print("Erreur de connexion en tant que root:", e)

    def authenticate_user(self, username, password):
        try:
            user_dn = self.search_user(username)
            if user_dn:
                self.conn.simple_bind_s(user_dn, password)
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
            search_base = self.config.get_config('ldap', 'search_base')
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