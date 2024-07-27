from flask import Blueprint, render_template, request, redirect, url_for, flash
from static.Controleur.ControleurLdap import ControleurLdap
from app import app

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
        ds=ControleurLdap.__init__()
        ds.add_entry(dn, attributes)
        ds.disconnect()

        return redirect('/')

    return render_template('register.html')