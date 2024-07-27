from flask import Flask, request, redirect, render_template
import ldap

app = Flask(__name__)

class ControleurLdap:
    def __init__(self, config):
        self.config = config
        self.conn = ldap.initialize(self.config.get_config('ldap', 'url'))
        self.conn.simple_bind_s(self.config.get_config('ldap', 'bind_dn'), self.config.get_config('ldap', 'bind_password'))

    # Méthodes existantes...

    def add_entry(self, dn, attributes):
        try:
            self.conn.add_s(dn, attributes)
            print("Entrée ajoutée avec succès")
        except ldap.LDAPError as e:
            print("Erreur lors de l'ajout de l'entrée:", e)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Construire le DN et les attributs de l'utilisateur
        dn = f"uid={username},ou=users,dc=blaze-world,dc=fr"
        attributes = [
            ('objectClass', [b'inetOrgPerson']),
            ('uid', [username.encode('utf-8')]),
            ('sn', [username.encode('utf-8')]),  # Nom de famille
            ('cn', [username.encode('utf-8')]),  # Nom complet
            ('userPassword', [password.encode('utf-8')]),
            ('mail', [email.encode('utf-8')])
        ]

        # Créer une instance de ControleurLdap et ajouter l'utilisateur
        config = ...  # Charger votre configuration LDAP
        controleur_ldap = ControleurLdap(config)
        controleur_ldap.add_entry(dn, attributes)

        return redirect('/')

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)