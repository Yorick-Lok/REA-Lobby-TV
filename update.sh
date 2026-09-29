systemctl stop reatv
git pull
sudo systemctl start reatv
sleep 10
sudo -u pi /home/pi/scripts/refresh
