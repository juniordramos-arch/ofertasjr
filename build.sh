#!/bin/bash

# Instala Chrome
apt-get update
apt-get install -y wget gnupg

# Adiciona repositório do Chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list

# Instala Chrome
apt-get update
apt-get install -y google-chrome-stable

# Instala dependências Python
pip install -r requirements.txt
