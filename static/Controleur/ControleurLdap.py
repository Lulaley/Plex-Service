import ldap
from .ControleurConf import ControleurConf
from .ControleurLog import write_log
from .ControleurCache import cache

class ControleurLdap:
    def __init__(self):
        self.config = ControleurConf()
        self.server = self.config.get_config('LDAP', 'server')
        self.conn = ldap.initialize(self.server)
        self.conn.start_tls_s()
        self.conn.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        write_log(f"Initialisation de la connexion LDAP avec le serveur: {self.server}")
    
    def __enter__(self):
        """Support pour context manager (with statement)"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ferme proprement la connexion LDAP à la sortie du context"""
        self.disconnect()
        return False  # Ne pas supprimer les exceptions

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
            write_log(f"Recherche de l'utilisateur {username} dans LDAP avec le filtre: {search_filter}")
            result = self.conn.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter, ['uid'])

            if not result:
                write_log(f"Utilisateur non trouvé: {username}", 'ERROR')
                return False

            user_dn = result[0][0]
            write_log(f"Utilisateur trouvé: {user_dn}. Tentative de connexion avec le mot de passe fourni.")
            try:
                self.conn.bind_s(user_dn, password)
                write_log(f"Authentification réussie de l'utilisateur: {username}")
                return True
            except ldap.INVALID_CREDENTIALS:
                write_log(f"Mot de passe incorrect pour l'utilisateur: {username}", 'ERROR')
                return False
        except ldap.LDAPError as e:
            write_log(f"Erreur d'authentification pour l'utilisateur: {username} - {str(e)}", 'ERROR')
            return False

    def search_user(self, username):
        # Essayer de récupérer depuis le cache (TTL 5 min)
        cache_key = f"user:{username}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        try:
            self.bind_as_root()
            search_base = self.config.get_config('LDAP', 'base_dn')
            search_filter = f"(uid={username})"
            result = self.conn.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter, ['uid', 'RightsAgreement'])
            if result:
                write_log("Utilisateur trouvé")
                # Mettre en cache pour 5 minutes
                cache.set(cache_key, result, ttl=300)
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
            write_log(f"Attribut {attribute} remplacé pour l'utilisateur {username}")
            
            # Invalider le cache pour cet utilisateur et la liste complète
            cache.delete(f"user:{username}")
            cache.delete("users:all")
            
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
            write_log(f"Suppression de l'utilisateur LDAP: {username}")
            base_dn = self.config.get_config('LDAP', 'base_dn')
            
            # Chercher l'utilisateur pour obtenir son vrai DN
            search_filter = f"(uid={username})"
            result = self.conn.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter, ['uid'])
            
            if not result:
                write_log(f"L'utilisateur {username} n'existe pas dans LDAP, suppression ignorée", 'WARNING')
                return True  # Considérer comme succès car l'utilisateur n'existe plus
            
            # Utiliser le DN retourné par la recherche
            dn = result[0][0]
            write_log(f"DN réel de l'utilisateur à supprimer: {dn}")
            
            # Tenter la suppression avec le vrai DN
            self.conn.delete_s(dn)
            write_log(f"Utilisateur {username} supprimé de la base LDAP")
            
            # Invalider le cache pour cet utilisateur et la liste complète
            cache.delete(f"user:{username}")
            cache.delete("users:all")
            
            return True
        except ldap.NO_SUCH_OBJECT:
            write_log(f"L'utilisateur {username} n'existe pas dans LDAP (NO_SUCH_OBJECT)", 'WARNING')
            return True  # Considérer comme succès car l'utilisateur n'existe plus
        except ldap.LDAPError as e:
            write_log(f"Erreur lors de la suppression de l'utilisateur LDAP: {e}", 'ERROR')
            return False

    def get_all_users(self):
        # Essayer de récupérer depuis le cache (TTL 2 min car change souvent)
        cache_key = "users:all"
        cached_users = cache.get(cache_key)
        if cached_users is not None:
            return cached_users
        
        try:
            self.bind_as_root()
            base_dn = self.config.get_config('LDAP', 'base_dn')
            search_filter = "(&(objectClass=inetOrgPerson)(RightsAgreement=PlexService::*))"
            result = self.conn.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter, ['uid', 'cn', 'mail', 'RightsAgreement'])
            users = []
            for dn, entry in result:
                user = {attr: entry[attr][0].decode('utf-8') for attr in entry}
                users.append(user)
            write_log("Liste des utilisateurs récupérée")
            # Mettre en cache pour 2 minutes
            cache.set(cache_key, users, ttl=120)
            return users
        except ldap.LDAPError as e:
            write_log(f"Erreur lors de la récupération des utilisateurs LDAP: {e}", 'ERROR')
            return []

    def disconnect(self):
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.unbind()
                write_log("Déconnexion LDAP réussie")
        except ldap.LDAPError as e:
            write_log("Erreur lors de la déconnexion LDAP: " + str(e), 'ERROR')