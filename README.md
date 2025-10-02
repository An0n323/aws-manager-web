# AWS Manager Web

## Installation sur EC2 Amazon Linux

1. Copier le template des credentials :
   ```bash
   cp aws_creds.env.template aws_creds.env
   # remplir avec vos clés AWS
   
pip3 install -r requirements.txt --user

sudo cp nginx/flask.conf /etc/nginx/conf.d/

sudo rm -f /usr/share/nginx/html/index.html

sudo systemctl restart nginx

sudo cp aws_manager_web_fixed2.service /etc/systemd/system/

sudo systemctl daemon-reload

sudo systemctl enable aws_manager_web_fixed2

sudo systemctl start aws_manager_web_fixed2

sudo journalctl -u aws_manager_web_fixed2 -f

http://TON_IP_PUBLIQUE/
