#!/bin/bash
echo "🚀 VailGo Tech Starting..."

# Session 1 - angel_proxy.py background मध्ये
cd ~
python angel_proxy.py &
PROXY_PID=$!
echo "✅ Proxy चालू (PID: $PROXY_PID)"

# 10 seconds wait
sleep 10

# Cloudflared चालू करा आणि URL capture करा
echo "🌐 Cloudflared चालू होतंय..."
cloudflared tunnel --url http://localhost:5000 2>&1 | while read line; do
    echo "$line"
    if echo "$line" | grep -q "trycloudflare.com"; then
        NEW_URL=$(echo "$line" | grep -o 'https://[a-z-]*.trycloudflare.com')
        if [ ! -z "$NEW_URL" ]; then
            echo "🔗 नवीन URL: $NEW_URL"
            # URL update करा
            cd ~/VAlgo--pro-V23
            OLD_URL=$(grep -o 'https://[a-z-]*.trycloudflare.com' index.html | head -1)
            sed -i "s|$OLD_URL|$NEW_URL|g" index.html
            git add index.html
            git commit -m "auto proxy url update"
            git push
            echo "✅ GitHub Update झालं!"
            cd ~
        fi
    fi
done
