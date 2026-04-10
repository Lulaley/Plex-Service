#!/bin/bash

echo "========================================="
echo "DIAGNOSTIC VPN/LIBTORRENT"
echo "========================================="
echo ""

# 1. Vérifier le fichier de port natpmpc
echo "1. Port natpmpc configuré :"
if [ -f /run/natpmpc-port ]; then
    PORT=$(cat /run/natpmpc-port)
    echo "   Port: $PORT"
else
    echo "   ❌ Fichier /run/natpmpc-port introuvable !"
fi
echo ""

# 2. Vérifier que le port est ouvert localement
echo "2. Port en écoute localement :"
if [ ! -z "$PORT" ]; then
    netstat -tulpn | grep ":$PORT" || echo "   ❌ Port $PORT pas en écoute !"
else
    echo "   ⚠️ Pas de port à vérifier"
fi
echo ""

# 3. Vérifier l'interface VPN
echo "3. Interface VPN (10.2.0.2) :"
ip addr show | grep "10.2.0.2" || echo "   ❌ Interface 10.2.0.2 introuvable !"
echo ""

# 4. Vérifier la connexion du service libtorrent
echo "4. Service libtorrent actif :"
systemctl status libtorrent_service | grep -E "Active:|Main PID:"
echo ""

# 5. Vérifier le port d'écoute du service
echo "5. Ports ouverts par libtorrent :"
lsof -i -P -n | grep "libtorrent\|python" | grep "LISTEN"
echo ""

# 6. Test de connectivité externe (vérifier si le port est accessible de l'extérieur)
echo "6. Test de connectivité du port via VPN :"
if [ ! -z "$PORT" ]; then
    echo "   ⚠️ Testez manuellement depuis l'extérieur :"
    echo "   nc -zv <IP_PUBLIQUE_VPN> $PORT"
else
    echo "   ⚠️ Pas de port à tester"
fi
echo ""

# 7. Routes VPN
echo "7. Routes réseau (vérifier que le trafic passe par le VPN) :"
ip route | grep "10.2.0"
echo ""

# 8. Logs récents du service
echo "8. Derniers logs libtorrent_service :"
journalctl -u libtorrent_service -n 20 --no-pager
echo ""

echo "========================================="
echo "FIN DU DIAGNOSTIC"
echo "========================================="
