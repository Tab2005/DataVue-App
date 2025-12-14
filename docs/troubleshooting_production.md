# Troubleshooting "Failed to fetch" in Production

## Symptom
When performing an action (e.g., Creating a Team), the UI shows "Failed to fetch".

## Probable Cause
"Failed to fetch" usually indicates the browser cannot connect to the API server at all.
In production deployments (like Zeabur/Vercel), this is most commonly caused by **incorrect API URL configuration**.

If `VITE_API_URL` is not set during the **Build Process**, the frontend defaults to `http://127.0.0.1:8000`, which the user's browser cannot reach.

## Steps to Verify

### 1. Check Network Tab
1. Open your deployed website.
2. Press `F12` to open Developer Tools.
3. Go to the **Network** tab.
4. Try to create a team again.
5. Look for the failed request (red text).
6. Click it and check the **Request URL**.
    - ❌ **Incorrect**: `http://127.0.0.1:8000/api/teams/` (Front-end is trying to call localhost)
    - ✅ **Correct**: `https://your-backend-app.zeabur.app/api/teams/`

### 3. Solution: Set Environment Variable
If the URL is pointing to localhost or is undefined:
1. Go to your Frontend Service settings in Zeabur (or Vercel).
2. Find **Environment Variables**.
3. Add `VITE_API_URL`.
4. Set the value to your **Backend Service URL** (e.g., `https://my-backend.zeabur.app`).
    - *Note: No trailing slash.*
5. **Redeploy the Frontend**. (Build variables only take effect on rebuild).

## Symptom: 500 Internal Server Error
If the Network Tab shows a red request with Status `500` (Internal Server Error):
1. This means the frontend successfully reached the backend, but the backend crashed.
2. Go to **Zeabur Dashboard > Backend Service > Logs**.
3. Scroll down to the bottom to see the latest error.
    - Look for `TypeError: verify_oauth2_token() got an unexpected keyword argument 'clock_skew_in_seconds'`.
    - If you see this, it means the `google-auth` library is too old. I have pushed a fix for this.
    - **Re-deploy the Backend Service** to apply the fix.
