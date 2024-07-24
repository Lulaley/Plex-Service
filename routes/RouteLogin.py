from flask import Blueprint, render_template, request, redirect, url_for, flash
from static import ControleurLdap

login = Blueprint('auth', __name__)

@login.route('/login')
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        con = ControleurLdap.__init__()
        # Utilisation de authenticate_user pour vérifier les identifiants
        if con.authenticate_user(username, password):
            # Redirection vers la page d'accueil en cas de succès
            return redirect(url_for('home'))
        else:
            # Affichage d'un message d'erreur en cas d'échec
            flash('Échec de la connexion. Veuillez vérifier vos identifiants et réessayer.')
    # Rendu du formulaire de connexion
    return render_template('login.html')