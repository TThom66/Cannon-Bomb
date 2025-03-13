# This is the installer for the Linux version of "Cannon-Bomb", and also serves as a test for some of my knowledge of shell scripting

# Install dependencies
sudo apt install python3-pygame python3-numpy python3-pyinstaller

# Pyinstaller builds the binary executable
pyinstaller main.py --onefile --noconsole --add-data="sounds/*:sounds/" --add-data="sprites/*:sprites/"

# Clean-up
rm -rf build
mv dist/main Cannon-Bomb
rm -rf dist
rm -f main.spec
echo "All done!"
