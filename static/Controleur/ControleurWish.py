from .ControleurLdap import ControleurLdap
from .ControleurLog import write_log
from datetime import datetime
import uuid

class ControleurWish:
    def __init__(self):
        self.ldap = ControleurLdap()

    def create_wish(self, username, title, wish_type):
        try:
            self.ldap.bind_as_root()
            # Vérifier s'il existe déjà une demande pour le titre
            search_base = self.ldap.config.get_config('LDAP', 'base_dn')
            search_filter = f"(&(objectClass=wish)(plexTitle={title}))"
            existing_wishes = self.ldap.search_entry(search_base, search_filter)
            if (existing_wishes):
                write_log(f"Une demande pour le titre {title} existe déjà", 'ERROR')
                return False

            wish_id = str(uuid.uuid4())
            user_dn = f'uid={username},dmdName=users,{search_base}'
            dn = f'wishId={wish_id},dmdName=wishes,{search_base}'
            attributes = [
                ('objectClass', [b'top', b'wish']),
                ('wishOwner', [user_dn.encode('utf-8')]),
                ('plexTitle', [title.encode('utf-8')]),
                ('requestDate', [datetime.now().strftime('%Y%m%d%H%M%SZ').encode('utf-8')]),
                ('status', [b'pending']),
                ('wishType', [wish_type.encode('utf-8')]),
                ('wishId', [wish_id.encode('utf-8')])
            ]
            self.ldap.add_entry(dn, attributes)
            write_log(f"Demande créée pour l'utilisateur {username} avec le titre {title}")
            return True
        except Exception as e:
            write_log(f"Erreur lors de la création de la demande: {str(e)}", 'ERROR')
            return False
        finally:
            self.ldap.disconnect()

    def modify_wish(self, username, wish_id, new_title=None, new_status=None, new_comments=None):
        try:
            self.ldap.bind_as_root()
            search_base = self.ldap.config.get_config('LDAP', 'base_dn')
            dn = f'wishId={wish_id},dmdName=wishes,{search_base}'
            mod_attrs = []
            if new_title:
                mod_attrs.append(('plexTitle', new_title.encode('utf-8')))
            if new_status:
                mod_attrs.append(('status', new_status.encode('utf-8')))
            if new_comments:
                mod_attrs.append(('comments', new_comments.encode('utf-8')))
            self.ldap.modify_entry(dn, mod_attrs)
            write_log(f"Demande modifiée pour l'utilisateur {username} avec le titre {new_title}")
            return True
        except Exception as e:
            write_log(f"Erreur lors de la modification de la demande: {str(e)}", 'ERROR')
            return False
        finally:
            self.ldap.disconnect()

    def delete_wish(self, username, wish_id):
        try:
            self.ldap.bind_as_root()
            search_base = self.ldap.config.get_config('LDAP', 'base_dn')
            dn = f'wishId={wish_id},dmdName=wishes,{search_base}'
            self.ldap.delete_entry(dn)
            write_log(f"Demande supprimée pour l'utilisateur {username} avec l'ID {wish_id}")
            return True
        except Exception as e:
            write_log(f"Erreur lors de la suppression de la demande: {str(e)}", 'ERROR')
            return False
        finally:
            self.ldap.disconnect()

    def validate_wish(self, username, wish_id):
        try:
            self.ldap.bind_as_root()
            search_base = self.ldap.config.get_config('LDAP', 'base_dn')
            dn = f'wishId={wish_id},dmdName=wishes,{search_base}'
            mod_attrs = [('status', b'validated')]
            self.ldap.modify_entry(dn, mod_attrs)
            write_log(f"Demande validée pour l'utilisateur {username} avec l'ID {wish_id}")
            return True
        except Exception as e:
            write_log(f"Erreur lors de la validation de la demande: {str(e)}", 'ERROR')
            return False
        finally:
            self.ldap.disconnect()

    def get_user_wishes(self, username):
        try:
            self.ldap.bind_as_root()
            search_base = self.ldap.config.get_config('LDAP', 'base_dn')
            user_dn = f'uid={username},dmdName=users,{search_base}'
            search_filter = f"(&(objectClass=wish)(wishOwner={user_dn}))"
            result = self.ldap.search_entry(search_base, search_filter)
            wishes = []
            if result:
                for dn, entry in result:
                    wish = {attr: entry[attr][0].decode('utf-8') for attr in entry}
                    wishes.append(wish)
            write_log(f"Demandes récupérées pour l'utilisateur {username}")
            return wishes
        except Exception as e:
            write_log(f"Erreur lors de la récupération des demandes: {str(e)}", 'ERROR')
            return []
        finally:
            self.ldap.disconnect()

    def get_all_wishes(self):
        try:
            self.ldap.bind_as_root()
            search_base = self.ldap.config.get_config('LDAP', 'base_dn')
            search_filter = "(objectClass=wish)"
            result = self.ldap.search_entry(search_base, search_filter)
            wishes = []
            if result:
                for dn, entry in result:
                    wish = {attr: entry[attr][0].decode('utf-8') for attr in entry}
                    wishes.append(wish)
            write_log("Toutes les demandes récupérées")
            return wishes
        except Exception as e:
            write_log(f"Erreur lors de la récupération de toutes les demandes: {str(e)}", 'ERROR')
            return []
        finally:
            self.ldap.disconnect()

    def get_wish_by_id(self, wish_id):
        try:
            self.ldap.bind_as_root()
            search_base = self.ldap.config.get_config('LDAP', 'base_dn')
            search_filter = f"(wishId={wish_id})"
            result = self.ldap.search_entry(search_base, search_filter)
            if result:
                dn, entry = result[0]
                wish = {attr: entry[attr][0].decode('utf-8') for attr in entry}
                return wish
            return None
        except Exception as e:
            write_log(f"Erreur lors de la récupération de la demande: {str(e)}", 'ERROR')
            return None
        finally:
            self.ldap.disconnect()