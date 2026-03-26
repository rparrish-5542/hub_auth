# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: 

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the following information in your report:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

## Security Best Practices

When using `hub-auth-client`:

### 1. **Azure AD Configuration**
- Always use HTTPS for redirect URIs in production
- Rotate client secrets regularly (recommend: every 90 days)
- Use certificate-based authentication where possible
- Limit token lifetime to minimum required duration

### 2. **Token Handling**
- Never log JWT tokens or sensitive user data
- Store tokens securely (encrypted at rest)
- Implement proper token expiration handling
- Clear tokens on logout

### 3. **Database**
- Use encrypted connections to PostgreSQL
- Implement row-level security (RLS) policies
- Follow principle of least privilege for DB users
- Regularly backup AzureADConfiguration data

### 4. **Django Settings**
```python
# Security headers (add to settings.py)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
```

### 5. **Dependencies**
- Keep all dependencies up to date
- Monitor security advisories for packages
- Use Dependabot for automated updates
- Run `pip-audit` regularly

### 6. **HIPAA Compliance**
This package is used in HIPAA-regulated environments:
- Enable audit logging for all authentication events
- Log all role/permission changes
- Implement secure session management
- Ensure PHI is never logged or exposed

## Security Features

This package includes:

- ✅ MSAL JWT validation with Entra ID
- ✅ Role-based access control (RBAC)
- ✅ Row-level security (RLS) policies
- ✅ Claim-based authorization
- ✅ Audit logging capabilities
- ✅ Secure session management
- ✅ CSRF protection
- ✅ SQL injection prevention (via Django ORM)

## Automated Security Scanning

Our CI/CD pipeline includes:

- **Bandit**: Python security linter
- **Safety**: Dependency vulnerability scanner
- **pip-audit**: Package audit for CVEs
- **CodeQL**: Static application security testing (SAST)
- **TruffleHog**: Secret scanning
- **Dependabot**: Automated dependency updates

## Known Vulnerabilities

No known vulnerabilities at this time.

CVEs will be listed here once discovered and fixed.

## Security Updates

Security updates are released as patch versions (e.g., 1.0.45 → 1.0.46).

Subscribe to [GitHub Security Advisories](https://github.com/<your-org>/hub_auth/security/advisories) for notifications.

## Hall of Fame

We recognize security researchers who responsibly disclose vulnerabilities:

- (None yet - be the first!)

## Contact

- Security Email: 
- General Questions: 
- Project Maintainer: Ryan Parrish

---

**Last Updated**: March 25, 2026
