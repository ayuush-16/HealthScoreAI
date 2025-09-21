# HealthScoreAI - Deployment Guide

## Step 1: Upload to GitHub

1. Create a new repository on GitHub:
   - Repository name: `healthscoreai`
   - Visibility: **Public** (required for free deployment)
   - Don't initialize with README

2. Connect your local repository:
```bash
git remote add origin https://github.com/YOUR_USERNAME/healthscoreai.git
git push -u origin main
```

## Step 2: Deploy for Free (Choose One)

### Option A: Render (Recommended)
1. Go to https://render.com
2. Sign up with GitHub account
3. Click "New +" → "Web Service"
4. Connect repository: `healthscoreai`
5. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py`
6. Deploy!

### Option B: Railway
1. Go to https://railway.app
2. Sign up with GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Select `healthscoreai`
5. Auto-deploys!

### Option C: Heroku (With Student Pack Credits)
1. Install Heroku CLI: `winget install Heroku.CLI`
2. Commands:
```bash
heroku login
heroku create your-app-name
git push heroku main
```

## Important Notes:
- Repository must be **PUBLIC** for free deployment
- All deployment files are already included
- App is configured for cloud hosting
- Image processing requires Tesseract on the server

## GitHub Student Pack Benefits:
- Heroku: $13/month credits
- DigitalOcean: $100 credits
- Microsoft Azure: $100 credits
- AWS: $10-100 credits

Your app is production-ready! 🚀