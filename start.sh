echo "Cloning Repo...."
git clone https://github.com/Uablebot/ilovepdf-koyeb
cd /ilovepdf-koyeb
pip3 install -r requirements.txt
echo "Starting Bot...."
python3 pdf.py
