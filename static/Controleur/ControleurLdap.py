import ldap
from .ControleurConf import ControleurConf
from .ControleurLog import write_log

class ControleurLdap:
    def __init__(self):
        self.config = ControleurConf()
        self.server = self.config.get_config('LDAP', 'server')
        self.conn = ldap.initialize(self.server)
        self.conn.start_tls_s()
        self.conn.set_option(ldap.OPT_PROTOCOL_VERSION, 3)

    def bind_as_root(self):
        try:
            root_dn = self.config.get_config('LDAP', 'root_dn')
            root_password = self.config.get_config('LDAP', 'root_password')
            self.conn.bind_s(root_dn, root_password)
            write_log("Connexion en tant que root réussie")
        except ldap.LDAPError as e:
            write_log("Erreur de connexion en tant que root: " + str(e), 'ERROR')

    def authenticate_user(self, username, password):
        try:
            self.bind_as_root()
            search_base = self.config.get_config('LDAP', 'base_dn')
            search_filter = f"(uid={username})"
            result = self.conn.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter)

            if not result:
                write_log("Utilisateur non trouvé: " + username, 'ERROR')
                return False

            user_dn = result[0][0]
            self.conn.bind_s(user_dn, password)
            write_log("Authentification réussie de l'utilisateur: " + username)
            return True
        except ldap.INVALID_CREDENTIALS:
            write_log("Les informations d'identification sont incorrectes pour l'utilisateur: " + username, 'ERROR')
            return False
        except ldap.LDAPError as e:
            write_log("Erreur d'authentification pour l'utilisateur: " + username + " - " + str(e), 'ERROR')
            return False

    def search_user(self, username):
        try:
            self.bind_as_root()
            search_base = self.config.get_config('LDAP', 'base_dn')
            search_filter = f"(uid={username})"
            result = self.conn.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter)
            if result:
                write_log("Utilisateur trouvé")
                return result
            else:
                write_log("Utilisateur non trouvé", 'ERROR')
                return None
        except ldap.LDAPError as e:
            write_log("Erreur lors de la recherche de l'utilisateur: " + str(e), 'ERROR')
            return None

    def add_entry(self, dn, attributes):
        try:
            result = self.conn.add_s(dn, attributes)
            if result:
                write_log("Entrée " + dn + " ajoutée avec succès")
                return True
            else:
                write_log("Erreur lors de l'ajout de l'entrée: " + dn, 'ERROR')
                return None
        except ldap.LDAPError as e:
            write_log("Erreur lors de l'ajout de l'entrée: " + str(e), 'ERROR')

    def delete_entry(self, dn):
        try:
            self.bind_as_root()
            self.conn.delete_s(dn)
            write_log("Entrée supprimée avec succès")
            return True
        except ldap.LDAPError as e:
            write_log("Erreur lors de la suppression de l'entrée: " + str(e), 'ERROR')
            return False

    def modify_entry(self, dn, mod_list):
        try:
            self.bind_as_root()
            write_log(f"Modification de l'entrée {dn} avec les attributs {mod_list}")
            self.conn.modify_s(dn, mod_list)
            write_log("Entrée modifiée avec succès")
            return True
        except ldap.LDAPError as e:
            write_log("Erreur lors de la modification de l'entrée: " + str(e), 'ERROR')
            return False

    def search_entry(self, search_base, search_filter):
        try:
            self.bind_as_root()
            result = self.conn.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter)
            if result:
                write_log("Entrée trouvée")
                return result
            else:
                write_log("Entrée non trouvée", 'ERROR')
                return None
        except ldap.LDAPError as e:
            write_log("Erreur lors de la recherche de l'entrée: " + str(e), 'ERROR')

    def add_attribute(self, username, attribute, value):
        try:
            self.bind_as_root()
            base_dn = self.config.get_config('LDAP', 'base_dn')
            dn = f'uid={username},dmdName=users,{base_dn}'
            mod_attrs = [(ldap.MOD_ADD, attribute, value.encode('utf-8'))]
            self.conn.modify_s(dn, mod_attrs)
            write_log(f"Attribut {attribute} ajouté pour l'utilisateur {username}")
            return True
        except ldap.LDAPError as e:
            write_log(f"Erreur lors de l'ajout de l'attribut LDAP: {e}", 'ERROR')
            return False

    def replace_attribute(self, username, attribute, value):
        try:
            self.bind_as_root()
            base_dn = self.config.get_config('LDAP', 'base_dn')
            dn = f'uid={username},dmdName=users,{base_dn}'
            mod_attrs = [(ldap.MOD_REPLACE, attribute, value.encode('utf-8'))]
            self.conn.modify_s(dn, mod_attrs)
            write_log(f"Attribut {attribute} remplacer pour l'utilisateur {username}")
            return True
        except ldap.LDAPError as e:
            write_log(f"Erreur lors du remplacement de l'attribut LDAP: {e}", 'ERROR')
            return False

    def validate_wish(self, dn):
        try:
            self.bind_as_root()
            mod_attrs = [(ldap.MOD_REPLACE, 'status', b'validated')]
            self.conn.modify_s(dn, mod_attrs)
            write_log(f"Demande validée pour l'entrée {dn}")
            return True
        except ldap.LDAPError as e:
            write_log(f"Erreur lors de la validation de la demande: {e}", 'ERROR')
            return False

    def delete_user(self, username):
        try:
            self.bind_as_root()
            base_dn = self.config.get_config('LDAP', 'base_dn')
            dn = f'uid={username},{base_dn}'
            self.conn.delete_s(dn)
            write_log(f"Utilisateur {username} supprimé de la base LDAP")
            return True
        except ldap.LDAPError as e:
            write_log(f"Erreur lors de la suppression de l'utilisateur LDAP: {e}", 'ERROR')
            return False

    def get_all_users(self):
        try:
            self.bind_as_root()
            base_dn = self.config.get_config('LDAP', 'base_dn')
            search_filter = "(objectClass=inetOrgPerson)"
            result = self.conn.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter)
            users = []
            for dn, entry in result:
                user = {attr: entry[attr][0].decode('utf-8') for attr in entry}
                users.append(user)
            write_log("Liste des utilisateurs récupérée")
            return users
        except ldap.LDAPError as e:
            write_log(f"Erreur lors de la récupération des utilisateurs LDAP: {e}", 'ERROR')
            return []

    def disconnect(self):
        try:
            self.conn.unbind()
            write_log("Déconnexion LDAP réussie")
        except ldap.LDAPError as e:
            write_log("Erreur lors de la déconnexion LDAP: " + str(e), 'ERROR')
