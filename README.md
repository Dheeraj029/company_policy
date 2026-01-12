

---

## ✅ STEP 1 — Install Azure CLI (Windows)

### 🔹 Method 1 (RECOMMENDED – easiest)

1. Open this link in your browser:
   👉 [https://aka.ms/installazurecliwindows](https://aka.ms/installazurecliwindows)

2. Download **AzureCLI.msi**

3. Double-click → Install (Next → Next → Finish)

4. **CLOSE all terminals** (very important)

---

### 🔹 Method 2 (PowerShell – optional)

Open **PowerShell as Administrator** and run:

```powershell
winget install -e --id Microsoft.AzureCLI
```

---

## ✅ STEP 2 — Verify installation

Open **NEW PowerShell window** (not the old one) and run:

```powershell
az --version
```

You should see output like:

```
azure-cli                         2.xx.x
```

If you see this → ✅ Installed correctly

---

## ✅ STEP 3 — Login to Azure

Now run:

```powershell
az login
```

What will happen:

* Browser opens
* Login with your **company email**
* After success, PowerShell shows your subscription info

This replaces **API keys**.

---

## ⚠️ VERY IMPORTANT (intern setup gotcha)

If you have **multiple Microsoft accounts** in your browser:

* Use **InPrivate / Incognito**
* Or explicitly choose your **company account**

Otherwise Azure CLI logs into the wrong tenant.

---

## ✅ STEP 4 — Confirm correct subscription

After login:

```powershell
az account show
```

Confirm:

* Subscription name = **Azure subscription 1**
* Tenant = company tenant

If not:

```powershell
az account set --subscription "Azure subscription 1"
```

---

## ✅ STEP 5 — Test Python auth works

Create `test_auth.py`:

```python
from azure.identity import DefaultAzureCredential

cred = DefaultAzureCredential()
token = cred.get_token("https://management.azure.com/.default")
print("Token acquired successfully")
```

Run:

```powershell
python test_auth.py
```

If you see:

```
Token acquired successfully
```

🎉 You are authenticated correctly.

---

## ❌ If this still fails

Tell me:

1. Windows version (10/11)
2. Are you using **PowerShell** or **CMD**
3. Output of:

   ```powershell
   where az
   ```

I’ll fix it fast.

---

## 🔑 Why this matters

Once `az login` works:

* Your RAG code will authenticate automatically
* No API keys needed
* You’re unblocked

You’re doing great — this is exactly how enterprise Azure works.
