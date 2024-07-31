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
            self.conn.bind_s(root_dn, root_password)
            write_log("Connexion en tant que root réussie")
        except ldap.LDAPError as e:
            write_log("Erreur de connexion en tant que root: " + str(e))

    def authenticate_user(self, username, password):
        try:
            # Rechercher l'utilisateur dans la base LDAP
            self.bind_as_root()
            search_base = self.config.get_config('LDAP', 'base_dn')
            search_filter = f"(uid={username})"
            result = self.conn.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter)

            if not result:
                write_log("Utilisateur non trouvé: " + username)
                return False

            # Si l'utilisateur existe, tenter de l'authentifier
            user_dn = result[0][0]
            self.conn.bind_s(user_dn, password)
            write_log("Authentification réussie de l'utilisateur: " + username)
            return True
        except ldap.INVALID_CREDENTIALS:
            write_log("Les informations d'identification sont incorrectes pour l'utilisateur: " + username)
            return False
        except ldap.LDAPError as e:
            write_log("Erreur d'authentification pour l'utilisateur: " + username + " - " + str(e))
            return False

    def search_user(self, username):
        try:
            self.conn.bind_as_root()
            search_base = self.config.get_config('LDAP', 'base_dn')
            search_filter = f"(uid={username})"
            result = self.conn.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter)
            if result:
                write_log("Utilisateur trouvé")
                return True
            else:
                write_log("Utilisateur non trouvé")
                return False
        except ldap.LDAPError as e:
            write_log("Erreur lors de la recherche de l'utilisateur: " + str(e))
            return False

    def add_entry(self, dn, attributes):
        write_log("Tentative d'ajout de l'entrée: " + dn)
        try:
            result = self.conn.add_s(dn, attributes)
            write_log("Résultat de l'ajout: " + str(result))
            if result:
                write_log("Entrée " + dn + " ajoutée avec succès")
                return True
            else:
                write_log("Erreur lors de l'ajout de l'entrée: " + dn)
                return None
        except ldap.LDAPError as e:
            write_log("Erreur lors de l'ajout de l'entrée: " + str(e))

    def delete_entry(self, dn):
        try:
            self.conn.bind_as_root()
            self.conn.delete_s(dn)
            write_log("Entrée supprimée avec succès")
            return True
        except ldap.LDAPError as e:
            write_log("Erreur lors de la suppression de l'entrée: " + str(e))
            return False

    def modify_entry(self, dn, mod_list):
        try:
            self.conn.bind_as_root()
            self.conn.modify_s(dn, mod_list)
            write_log("Entrée modifiée avec succès")
            return True
        except ldap.LDAPError as e:
            write_log("Erreur lors de la modification de l'entrée: " + str(e))
            return False

    def search_entry(self, search_base, search_filter):
        try:
            self.conn.bind_as_root()
            result = self.conn.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter)
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
        