# Streamlit Cloud Deployment Guide

## Step 1: Prepare Your Code ✅
Code is now updated to support Streamlit Cloud secrets. It works both locally and on the cloud.

## Step 2: Local Testing
1. Add your Groq API key to `.streamlit/secrets.toml`:
   ```toml
   GROQ_API_KEY = "gsk_your_actual_key_here"
   ```

2. Run locally to test:
   ```bash
   streamlit run streamlit_app.py
   ```

## Step 3: Prepare for Cloud Deployment
Make sure these files are in your GitHub repo:
- `streamlit_app.py` ✓
- `chat2site_core.py` ✓
- `requirements.txt` ✓
- All other Python modules ✓
- `.gitignore` (should exclude `.streamlit/secrets.toml` and `.env`)

Add to `.gitignore` if not already there:
```
.env
.streamlit/secrets.toml
env/
__pycache__/
*.pyc
```

## Step 4: Deploy to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub account
3. Click **New app**
4. Select your GitHub repo, branch, and `streamlit_app.py` as main file
5. Click **Deploy**

## Step 5: Add Secrets in Streamlit Cloud
After deployment:
1. Go to your app's dashboard at share.streamlit.io
2. Click on your app → **Settings** (gear icon) → **Secrets**
3. Add your secrets in TOML format:
   ```toml
   GROQ_API_KEY = "gsk_your_actual_key_here"
   ```
4. Save - the app will automatically restart

## Done! 🚀
Your app is now deployed and using secrets securely.

## Troubleshooting

**Error: "GROQ_API_KEY is missing"**
- Check that you added the secret in Streamlit Cloud's Secrets panel
- Make sure the key starts with `gsk_`

**Works locally but not on cloud:**
- Verify your `.env` file is in `.gitignore`
- Check that you set the secret in Streamlit Cloud dashboard (not just locally)

**Different secrets for different environments:**
- Local: Use `.streamlit/secrets.toml`
- Cloud: Use Streamlit Cloud dashboard Secrets panel
