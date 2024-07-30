import ldap
from .ControleurConf import ControleurConf
from .ControleurLog import write_log
class ControleurLdap:
    def __init__(self):
        self.config = ControleurConf()
        self.server = self.config.get_config('LDAP', 'server')
        self.conn = ldap.initialize(self.server)
        self.conn.set_option(ldap.OPT_PROTOCOL_VERSION, 3)

    def bind_as_root(self):
        try:
            root_dn = self.config.get_config('LDAP', 'root_dn')
            root_password = self.config.get_config('LDAP', 'root_password')
            self.conn.bind(root_dn, root_password)
            write_log("Connexion en tant que root réussie")
        except ldap.LDAPError as e:
            write_log("Erreur de connexion en tant que root: " + str(e))

    def authenticate_user(self, username, password):
        try:
            self.conn.bind(username, password)
            write_log("Authentification réussie de l'utilisateur: " + username)
            return True
        except ldap.LDAPError as e:
            write_log("Erreur d'authentification: " + str(e))
            return False

    def search_user(self, username):
        try:
            self.conn.bind_as_root()
            search_base = self.config.get_config('LDAP', 'base_dn')
            search_filter = f"(uid={username})"
            result = self.conn.search(search_base, ldap.SCOPE_SUBTREE, search_filter)
            if result:
                write_log("Utilisateur trouvé")
                return result[0][0]
            else:
                write_log("Utilisateur non trouvé")
                return None
        except ldap.LDAPError as e:
            write_log("Erreur lors de la recherche de l'utilisateur: " + str(e))

    def add_entry(self, dn, attributes):
        try:
            self.conn.add(dn, attributes)
            write_log("Entrée " + dn + " ajoutée avec succès")
        except ldap.LDAPError as e:
            write_log("Erreur lors de l'ajout de l'entrée: " + str(e))

    def delete_entry(self, dn):
        try:
            self.conn.bind_as_root()
            self.conn.delete(dn)
            write_log("Entrée supprimée avec succès")
        except ldap.LDAPError as e:
            write_log("Erreur lors de la suppression de l'entrée: " + str(e))

    def modify_entry(self, dn, mod_list):
        try:
            self.conn.bind_as_root()
            self.conn.modify(dn, mod_list)
            write_log("Entrée modifiée avec succès")
        except ldap.LDAPError as e:
            write_log("Erreur lors de la modification de l'entrée: " + str(e))

    def search_entry(self, search_base, search_filter):
        try:
            self.conn.bind_as_root()
            result = self.conn.search(search_base, ldap.SCOPE_SUBTREE, search_filter)
            if result:
                write_log("Entrée trouvée")
                return result
            else:
                write_log("Entrée non trouvée")
                return None
        except ldap.LDAPError as e:
            write_log("Erreur lors de la recherche de l'entrée: " + str(e))
    
    def disconnect(self):
        try:
            self.conn.unbind()
            write_log("Déconnexion LDAP réussie")
        except ldap.LDAPError as e:
            write_log("Erreur lors de la déconnexion LDAP: " + str(e))
