USER_DATA_POSTGRES = '''#!/bin/bash
cd /
sudo apt update
sudo apt install postgresql postgresql-contrib -y
sudo -u postgres createuser cloud
sudo -u postgres createdb tasks -O cloud
sudo sed -i s/"^#listen_addresses = 'localhost'"/"listen_addresses = '*'"/g  /etc/postgresql/12/main/postgresql.conf
sudo sed -i '$a host all all 0.0.0.0/0 trust' /etc/postgresql/12/main/pg_hba.conf
sudo ufw allow 5432/tcp
sudo systemctl restart postgresql
'''