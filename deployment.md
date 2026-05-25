# 🚀 AURA Deployment Guide (100% Free Cloud & Tunnel Deployment)

This document provides a step-by-step guide to deploying AURA for free. It details how to host the stunning 3D frontend interface on a global cloud network and secure a public tunnel to your home PC's FastAPI server, allowing you to voice-control your desktop machine from anywhere on any device (such as your smartphone).

---

## 🏗️ Deployment Architecture

Since AURA controls your physical desktop (mouse, keyboard, applications), the **automation backend must run locally** on your computer. However, we can deploy the system so it is accessible from the web:

```
[ Smartphone / Remote Device ] 
             │
             ▼ (Global HTTPS Request)
 ┌──────────────────────┐
 │   Cloud Frontend     │ (Hosted for free on Netlify or Vercel)
 │   (3D holographic)   │
 └───────────┬──────────┘
             │ (Communicates via public HTTPS Tunnel)
             ▼
 ┌──────────────────────┐
 │ Secure Tunnel Server │ (Managed by ngrok or Localtunnel)
 └───────────┬──────────┘
             │ (Forwards request to local port 8000)
             ▼
 ┌──────────────────────┐
 │  Local FastAPI App   │ (Running on your Windows Desktop)
 └───────────┬──────────┘
             │ (Executes plans)
             ▼
 [ Windows OS & Apps ]
```

---

## 🌐 Phase 1: Deploying the 3D Frontend for Free

Hosting your frontend in the cloud lets you open the dashboard on your phone, tablet, or another computer.

### Option A: Deploying on Netlify (Recommended)
Netlify offers a fast, zero-configuration global CDN that is free forever.

#### 1. Manual Drop Deployment (No Command Line Needed)
1. Go to [Netlify App](https://app.netlify.com/) and log in (or create a free account).
2. Go to the **Sites** tab.
3. Scroll down to the bottom where you see **"Want to deploy a new site without connecting to Git? Drag and drop your site folder here"**.
4. Drag and drop the `frontend` folder from your local workspace directly onto that target box.
5. Your site is deployed! Netlify will provide a public URL like `https://gorgeous-holo-12345.netlify.app`.

#### 2. Netlify CLI Deployment
If you prefer deploying via terminal:
1. Install Netlify CLI:
   ```bash
   npm install -g netlify-cli
   ```
2. Navigate to your frontend directory:
   ```bash
   cd "d:\Chandu Project\AURA – Voice Controlled Autonomous Desktop AI Assistant\aura-ai-assistant\frontend"
   ```
3. Authenticate and deploy:
   ```bash
   netlify login
   netlify deploy --dir=. --prod
   ```

---

### Option B: Deploying on Vercel
Vercel is another premium global hosting provider.

1. Install the Vercel CLI tool:
   ```bash
   npm install -g vercel
   ```
2. Navigate to the `frontend` folder and deploy:
   ```bash
   cd "d:\Chandu Project\AURA – Voice Controlled Autonomous Desktop AI Assistant\aura-ai-assistant\frontend"
   vercel --prod
   ```
3. Follow the CLI wizard (select default options). Vercel will build and output your production domain (e.g., `https://aura-assistant.vercel.app`).

---

## 🛡️ Phase 2: Exposing the Local Backend via Secure Tunnel

To allow your cloud-hosted frontend (from Phase 1) to securely contact your local computer's FastAPI backend, you need a secure public tunnel. This bypasses home router firewalls without exposing your computer's IP address.

### Option A: Tunneling with ngrok (Highly Stable & Reliable)
1. Create a free account at [ngrok.com](https://ngrok.com/).
2. Download ngrok for Windows from the dashboard.
3. Open a terminal and configure your authentication token:
   ```bash
   ngrok config add-authtoken YOUR_NGROK_AUTHTOKEN
   ```
4. Start a secure tunnel forwarding to local port 8000:
   ```bash
   ngrok http 8000
   ```
5. Copy the secure forwarding URL (which will look like `https://xxxx-xx-xxx.ngrok-free.app`).

---

### Option B: Tunneling with Localtunnel (No Accounts Required)
If you do not want to sign up for an account, you can use `localtunnel` via Node.js.

1. Ensure you have Node.js installed.
2. Run localtunnel to expose port 8000:
   ```bash
   npx localtunnel --port 8000
   ```
3. Copy the generated URL (e.g., `https://heavy-cats-run.loca.lt`).

---

## 🔗 Phase 3: Linking the Frontend and Backend

Once you have your secure tunnel URL from Phase 2:

1. Open `frontend/main.js` on your computer.
2. Find line 1:
   ```javascript
   const API_BASE = "http://127.0.0.1:8000/api";
   ```
3. Replace `http://127.0.0.1:8000/api` with your secure tunnel public URL:
   ```javascript
   const API_BASE = "https://xxxx-xx-xxx.ngrok-free.app/api";
   ```
4. If you used Git to deploy, commit and push the change to automatically rebuild your site. If you used Netlify's manual drop, drag and drop the modified `frontend` folder to Netlify again to update the site.

Now, whenever you open your public Netlify/Vercel URL, it will securely relay voice and text commands directly to your home computer!

---

## ⚡ Phase 4: Production Best Practices & Windows Automation

To make AURA run continuously in the background on your host desktop:

### 1. Configure the Local Environment variables (`.env`)
Create a `.env` file in `aura-ai-assistant/` to store your API keys:
```ini
GEMINI_API_KEY=your_google_studio_developer_key
PORT=8000
HOST=127.0.0.1
DEBUG=False
```

### 2. Create a One-Click Windows Startup Script (`run_aura_remote.bat`)
Create a file named `run_aura_remote.bat` in your project root folder so you can start AURA and your tunnel with a single double-click:

```batch
@echo off
title AURA Assistant & Tunnel
echo Starting AURA Backend...
start cmd /k "venv\Scripts\activate && python run_aura.py"
echo.
echo Starting secure tunnel...
timeout /t 3
start cmd /k "ngrok http 8000"
echo AURA is running and exposed to the web!
pause
```

### 3. Autostart AURA on Windows Startup
If you want AURA to run as soon as you boot your PC:
1. Press `Win + R`, type `shell:startup`, and press Enter. This opens the Windows Startup folder.
2. Right-click inside the folder, select **New > Shortcut**.
3. Point the shortcut to your `run_aura_remote.bat` file.
4. Now, whenever you turn on your PC, AURA launches in the background, ready to receive remote commands!

---

## 🔍 Troubleshooting

* **CORS Block Errors:**
  If you host the frontend on Netlify and your browser blocks requests, verify that the FastAPI CORS middleware allows all origins. This is enabled by default in `backend/main.py`:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      ...
  )
  ```
* **"Failed to connect to local backend" / Timeout:**
  Make sure your `run_aura.py` is actively running on port 8000, and that your `ngrok` tunnel state is labeled **Online**.
* **PyAutoGUI failsafe error:**
  If you are running the backend remotely and the mouse cursor gets accidentally nudged to one of the four screen corners, PyAutoGUI triggers a failsafe and halts the current action sequence to prevent runaway scripts. Keep the mouse clear while commands are executing.
