#!/data/data/com.termux/files/usr/bin/bash

clear
echo "======================================"
echo "     🚀 RAJ VISHAL KE LODE PE"
echo "======================================"

sleep 1

echo "[1/6] Updating Termux..."
pkg update -y && pkg upgrade -y

echo "[2/6] Installing dependencies..."
pkg install python curl git -y

echo "[3/6] Upgrading pip..."
pip install --upgrade pip

echo "[4/6] Installing Python packages..."
pip install requests urllib3 tldextract beautifulsoup4 colorama

echo "[5/6] Installing BTX tool..."

mkdir -p $HOME/BTX
cd $HOME/BTX

curl -L -o real_script.py https://raw.githubusercontent.com/rajmerelodepe/Raj-mere-lode_pe/refs/heads/main/real_script.py

echo "[6/6] Creating command..."

cat << 'EOF' > $PREFIX/bin/Raj
#!/data/data/com.termux/files/usr/bin/bash
python $HOME/BTX/real_script.py
EOF

chmod +x $PREFIX/bin/Raj

echo ""
echo "======================================"
echo "✅ INSTALLATION COMPLETE"
echo "Type: Raj"
echo "======================================"
