# 🔒 Security Policy & Best Practices

## ⚠️ CRITICAL SECURITY ISSUES RESOLVED

### Previously Exposed Secrets
The following credentials were found in version control and have been **REMOVED**:
- ❌ Hardcoded database password: `WHOAMI@4PLACE`
- ❌ Hardcoded SQL Server IP: `192.50.20.15`
- ❌ Hardcoded database name: `HTMS_EPE`
- ❌ Hardcoded username: `admin`

**Status**: ✅ All hardcoded credentials removed and replaced with environment variables

---

## 🔐 Secure Credential Management

### **DO NOT**
```python
# ❌ NEVER DO THIS
DB_PASSWORD = 'WHOAMI@4PLACE'
API_KEY = 'sk-1234567890'
SECRET = 'my-secret-key'
config.db.password = 'admin123'
```

### **DO THIS INSTEAD**
```bash
# 1. Set environment variable (PowerShell)
$env:MSSQL_PASSWORD = 'your_actual_password'

# 2. Or create .env file (local only - add to .gitignore)
MSSQL_PASSWORD=your_actual_password

# 3. Load in Python
import os
db_password = os.getenv('MSSQL_PASSWORD')

if not db_password:
    raise ValueError("MSSQL_PASSWORD not set!")
```

---

## 📋 Setup Instructions

### **Step 1: Create Local .env File**
```bash
# Copy template
cp .env.example .env

# Edit .env with YOUR values (only local, never commit)
# Windows: notepad .env
# Linux: nano .env
```

### **Step 2: Set Environment Variables**

**Windows PowerShell:**
```powershell
$env:MSSQL_SERVER = "your_server_ip"
$env:MSSQL_DATABASE = "your_database"
$env:MSSQL_USERNAME = "your_username"
$env:MSSQL_PASSWORD = "your_password"

# Verify
echo $env:MSSQL_PASSWORD
```

**Linux/Mac Bash:**
```bash
export MSSQL_SERVER="your_server_ip"
export MSSQL_DATABASE="your_database"
export MSSQL_USERNAME="your_username"
export MSSQL_PASSWORD="your_password"

# Verify
echo $MSSQL_PASSWORD
```

### **Step 3: Verify .gitignore**
Confirm these sensitive files are in `.gitignore`:
- ✅ `.env` (local environment variables)
- ✅ `config.local.ini` (local config)
- ✅ `.env.local` (local overrides)
- ✅ `secrets/**` (any secrets folder)
- ✅ `*.key` (private keys)
- ✅ `*.pem` (certificates)

### **Step 4: Start Application**
```bash
# Load .env automatically and start
python scripts/run_api.py
```

---

## 🔑 For Production Deployments

### **GitHub Actions / CI/CD**
Add secrets in GitHub repository settings:

```bash
# Go to: Settings → Secrets and variables → Actions

# Add these secrets:
MSSQL_SERVER
MSSQL_DATABASE
MSSQL_USERNAME
MSSQL_PASSWORD
API_KEY
```

**Use in workflow:**
```yaml
- name: Run tests
  env:
    MSSQL_PASSWORD: ${{ secrets.MSSQL_PASSWORD }}
  run: pytest tests/
```

### **Azure Key Vault**
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

vault_url = "https://<vault-name>.vault.azure.net/"
client = SecretClient(vault_url, DefaultAzureCredential())

db_password = client.get_secret("db-password").value
```

### **Docker Secrets**
```dockerfile
# Never pass secrets as build args
# Use docker secrets or environment files

# ✅ CORRECT: Load from file
COPY .env.prod /app/.env
RUN source /app/.env

# ❌ WRONG: Pass as argument
# ARG DB_PASSWORD=secret
```

---

## 🛡️ Security Checklist

### **Before Committing**
- [ ] No passwords in code
- [ ] No API keys in files
- [ ] No database credentials
- [ ] `.env` file NOT tracked
- [ ] `.gitignore` includes `.env`
- [ ] Run `git diff` to verify

### **Before Deployment**
- [ ] Rotate all old credentials
- [ ] Enable HTTPS/TLS
- [ ] Set up firewall rules
- [ ] Enable audit logging
- [ ] Configure API rate limiting
- [ ] Enable security scanning
- [ ] Set up backups

### **Ongoing**
- [ ] Regularly rotate credentials
- [ ] Review audit logs weekly
- [ ] Monitor for vulnerabilities
- [ ] Keep dependencies updated
- [ ] Run SAST/DAST scans

---

## 🚨 If Credentials Are Exposed

### **IMMEDIATE ACTIONS**
1. **Revoke credentials** (change passwords immediately)
2. **Remove from history**:
   ```bash
   git filter-repo --invert-paths --paths '.env'
   git push origin --force-with-lease
   ```
3. **Verify .gitignore** prevents future leaks
4. **Check audit logs** for unauthorized access
5. **Run security scan** (GitGuardian, Snyk, etc.)

---

## 🔍 Security Scanning

### **Enable on GitHub**
```yaml
# .github/workflows/security.yml
name: Security Scan

on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
```

### **Local Scanning**
```bash
# Install GitGuardian CLI
pip install gitguardian

# Scan repository
ggshield secret scan

# Scan commits
ggshield secret scan --staged
```

---

## 📚 References

- **OWASP**: https://owasp.org/www-project-top-ten/
- **GitGuardian**: https://www.gitguardian.com/
- **Snyk**: https://snyk.io/
- **GitHub Security**: https://docs.github.com/en/code-security
- **12 Factor App**: https://12factor.net/config

---

## 📞 Report Security Issues

If you discover a security vulnerability:
1. **DO NOT** create public GitHub issue
2. Email: `security@yourdomain.com`
3. Provide detailed reproduction steps
4. Include proof of concept (if applicable)
5. Allow 90 days for remediation

---

**Last Updated**: March 18, 2026  
**Status**: ✅ Production Ready  
**Next Review**: March 25, 2026
