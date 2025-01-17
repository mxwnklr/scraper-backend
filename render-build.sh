#!/bin/bash
set -e

echo "🔽 Downloading Google Chrome..."
mkdir -p /opt/chrome
curl -Lo /opt/chrome/chrome-linux.zip https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
unzip /opt/chrome/chrome-linux.zip -d /opt/chrome
chmod +x /opt/chrome/google-chrome

echo "🔽 Downloading ChromeDriver..."
mkdir -p /opt/chromedriver
CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE)
curl -Lo /opt/chromedriver/chromedriver_linux64.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
unzip /opt/chromedriver/chromedriver_linux64.zip -d /opt/chromedriver
chmod +x /opt/chromedriver/chromedriver

echo "✅ Google Chrome & ChromeDriver installed successfully."