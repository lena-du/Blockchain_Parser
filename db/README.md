# Prerequisites
In order for Bitcoin-Sync to work, Kafka and Neo4j need to be installed on the server

# Instructions
1. Download the git repository on your server. 
2. Create a user unit service by placing the `btc.service` file under the `$HOME/.config/systemd/user` directory. `Note that you might need to update the locations of the files in the service file `ExecStart=/usr/bin/python3 /home/btc/db/main.py /home/btc/logs/btc_service.log 2>&1`
3. Enable the service by running `systemctl --user enable btc.service`
