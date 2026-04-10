#!/bin/bash

echo "========================================="
echo "DIAGNOSTIC PORT FORWARDING"
echo "========================================="
echo ""

PORT=$(cat /run/natpmpc-port 2>/dev/null)

echo "1. Port configuré: $PORT"
echo ""

echo "2. IP publique VPN:"
curl -4 -s ifconfig.me
echo ""
echo ""

echo "3. Service natpmp-client:"
systemctl status natpmp-client --no-pager | head -5
echo ""

echo "4. Logs natpmp (dernières 10 lignes):"
journalctl -u natpmp-client -n 10 --no-pager
echo ""

echo "5. Règles iptables pour le port $PORT:"
sudo iptables -L -n -v | grep -i "$PORT" || echo "Aucune règle trouvée"
echo ""

echo "6. Ports en écoute:"
netstat -tulpn | grep ":$PORT" || echo "Port $PORT pas en écoute"
echo ""

echo "7. Test de connexion locale:"
if [ ! -z "$PORT" ]; then
    timeout 2 nc -zv 10.2.0.2 $PORT 2>&1 || echo "Impossible de se connecter au port local"
fi
echo ""

echo "========================================="
echo "Pour tester depuis l'extérieur:"
echo "https://www.yougetsignal.com/tools/open-ports/"
echo "Port: $PORT"
echo "========================================="
