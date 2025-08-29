chmod +x spider_remote_setup.sh
sudo chmod +x spider_remote_setup.sh
exit
sudo chmod +x spider_remote_setup.sh
./spider_remote_setup.sh
sudo -u spider /opt/spider/setup_remote_access.sh
# Test the SSH connection
ssh -i /opt/spider/.ssh/id_rsa abidan@192.168.1.254
ssh -i /opt/spider/.ssh/id_rsa abidan@192.168.1.254
sudo -u spider /opt/spider/venv/bin/python /opt/spider/spider/main.py --test-remote
sudo -u spider /opt/spider/venv/bin/python /opt/spider/spider/main.py --scan --remote
sudo systemctl stop spider
./report.sh
sudo systemctl enable spider-remote
sudo systemctl start spider-remote
sudo systemctl status spider-remote
sudo journalctl -u spider-remote -f
sudo journalctl -u spider-remote -f
sudo journalctl -u spider-remote -f
sudo systemctl status spider-remote
sudo journalctl -u spider-remote -n 50
sudo journalctl -u spider-remote --since "5 minutes ago"
sudo -u spider /opt/spider/venv/bin/python /opt/spider/spider/main.py --scan --remote
./report.sh
sudo -u spider /opt/spider/venv/bin/python /opt/spider/spider/main.py --scan --remote
sudo nano /etc/systemd/system/spider-remote.service
sudo systemctl daemon-reexec
sudo systemctl restart spider-remote
sudo journalctl -u spider-remote -f
sudo nano /etc/systemd/system/spider-remote.service
sudo systemctl daemon-reexec
sudo systemctl restart spider-remote
sudo journalctl -u spider-remote -f
chmod +x spider_llm_setup.sh
exit
lsblk
sudo -u spider /opt/spider/venv/bin/python /opt/spider/spider/main.py --test-llm
sudo -u spider /opt/spider/venv/bin/python /opt/spider/spider/main.py --scan --remote --analyze
cat /opt/spider/logs/reports/llm_analysis_20250819_121506.md
ssh abidan@sanctum
clear
chmod +x spider_zimaos_enhancement.sh
sudo chmod +x spider_zimaos_enhancement.sh
sudo ./spider_zimaos_enhancement.sh
clear
 sudo -u spider /opt/spider/venv/bin/python /opt/spider/spider/main.py --scan --remote --analyze
exit
spider/main.py --test-llm
spider ALL=(root) NOPASSWD: /usr/bin/df, /usr/sbin/lsblk, /usr/sbin/fdisk, /usr/bin/journalctl, /usr/bin/systemctl, /usr/bin/docker, /usr/sbin/iptables, /usr/sbin/ufw, /usr/bin/lshw, /usr/sbin/dmidecode, /usr/bin/powertop, /usr/bin/lsof, /usr/sbin/ip, /usr/bin/ss, /usr/bin/netstat, /usr/bin/ps, /usr/bin/mount, /usr/bin/free, /usr/bin/uptime
spider ALL=(root) NOPASSWD: /usr/bin/df, /usr/sbin/lsblk, /usr/sbin/fdisk, /usr/bin/journalctl, /usr/bin/systemctl, /usr/bin/docker, /usr/sbin/iptables, /usr/sbin/ufw, /usr/bin/lshw, /usr/sbin/dmidecode, /usr/bin/powertop, /usr/bin/lsof, /usr/sbin/ip, /usr/bin/ss, /usr/bin/netstat, /usr/bin/ps, /usr/bin/mount, /usr/bin/free, /usr/bin/uptime
sudo sed -i 's/auditai/spider/g' /etc/systemd/system/spider.service
sudo systemctl daemon-reload
sudo chown -R spider:spider /opt/spider
sudo -u spider /opt/spider/spider/main.py --test-llm
spider/main.py --scan --analyze
spider/main.py --test-remote
spider/main.py --scan --remote --analyze
exit
