# Security Standards - Development Guidelines

> Scope: Application security standards. Stable by default; changes require PM/Product Manager approval and must include rationale in `/.claude/memory/standards/CHANGELOG.md`.

## Developer Security Requirements

### MANDATORY: Security Considerations for All Development

When implementing any feature, developers MUST consider these security aspects:

#### 1. **Authentication & Authorization**
```markdown
ALWAYS IMPLEMENT:
- Secure session management
- Proper token validation (JWT/OAuth)
- Role-based access control (RBAC)
- Multi-factor authentication for sensitive operations
- Secure logout functionality

NEVER IMPLEMENT:
- Hardcoded credentials
- Weak password requirements
- Session tokens in URLs
- Unprotected admin endpoints
```

#### 2. **Input Validation & Sanitization**
```javascript
// ✅ CORRECT - Validate and sanitize all inputs
const validateUserInput = (input) => {
    if (!input || typeof input !== 'string') {
        throw new Error('Invalid input');
    }
    return DOMPurify.sanitize(input.trim());
};

// ❌ WRONG - Direct insertion without validation
const unsafeQuery = `SELECT * FROM users WHERE name = '${userInput}'`;
```

#### 3. **SQL Injection Prevention**
```javascript
// ✅ CORRECT - Use parameterized queries
const query = 'SELECT * FROM users WHERE id = ? AND role = ?';
db.query(query, [userId, userRole]);

// ✅ CORRECT - Use ORM with proper escaping
const user = await User.findOne({
    where: { id: userId, role: userRole }
});

// ❌ WRONG - String concatenation
const query = `SELECT * FROM users WHERE id = ${userId}`;
```

#### 4. **XSS (Cross-Site Scripting) Prevention**
```javascript
// ✅ CORRECT - Escape output
const safeHTML = escapeHtml(userContent);
element.textContent = userContent; // DOM automatically escapes

// ✅ CORRECT - Content Security Policy
res.setHeader('Content-Security-Policy', "default-src 'self'");

// ❌ WRONG - Direct HTML insertion
element.innerHTML = userContent;
```

#### 5. **CSRF (Cross-Site Request Forgery) Protection**
```javascript
// ✅ CORRECT - CSRF token validation
app.use(csrf({ cookie: true }));

// ✅ CORRECT - SameSite cookie attribute
app.use(session({
    cookie: { sameSite: 'strict', secure: true }
}));
```

#### 6. **Data Encryption & Storage**
```javascript
// ✅ CORRECT - Hash passwords properly
const bcrypt = require('bcrypt');
const hashedPassword = await bcrypt.hash(password, 12);

// ✅ CORRECT - Encrypt sensitive data
const crypto = require('crypto');
const encrypted = crypto.encrypt(sensitiveData, encryptionKey);

// ❌ WRONG - Plain text storage
const user = { password: plainTextPassword };
```

#### 7. **API Security**
```javascript
// ✅ CORRECT - Rate limiting
app.use('/api/', rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100 // limit each IP to 100 requests per windowMs
}));

// ✅ CORRECT - Input validation middleware
const validateApiInput = (schema) => (req, res, next) => {
    const { error } = schema.validate(req.body);
    if (error) return res.status(400).json({ error: error.details[0].message });
    next();
};

// ✅ CORRECT - Secure headers
app.use(helmet());
```

#### 8. **File Upload Security**
```javascript
// ✅ CORRECT - File type validation
const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
if (!allowedTypes.includes(file.mimetype)) {
    throw new Error('Invalid file type');
}

// ✅ CORRECT - File size limits
const upload = multer({
    limits: { fileSize: 5 * 1024 * 1024 }, // 5MB limit
    fileFilter: (req, file, cb) => {
        if (allowedTypes.includes(file.mimetype)) {
            cb(null, true);
        } else {
            cb(new Error('Invalid file type'), false);
        }
    }
});
```

## Security Review Checklist for Developers

### Before Code Submission
- [ ] All user inputs are validated and sanitized
- [ ] SQL queries use parameterized statements
- [ ] XSS prevention measures implemented
- [ ] CSRF protection in place for state-changing operations
- [ ] Passwords are properly hashed
- [ ] Sensitive data is encrypted at rest
- [ ] Authentication/authorization checks present
- [ ] Rate limiting implemented for APIs
- [ ] Secure headers configured
- [ ] No hardcoded secrets or credentials
- [ ] File uploads properly validated
- [ ] Error messages don't leak sensitive information

### Database Security
```sql
-- ✅ CORRECT - Principle of least privilege
GRANT SELECT, INSERT, UPDATE ON app_data TO app_user;

-- ✅ CORRECT - Prepared statements
PREPARE stmt FROM 'SELECT * FROM users WHERE id = ?';

-- ❌ WRONG - Over-privileged access
GRANT ALL PRIVILEGES ON *.* TO app_user;
```

### Environment Variables
```javascript
// ✅ CORRECT - Environment-based secrets
const dbPassword = process.env.DB_PASSWORD;
const jwtSecret = process.env.JWT_SECRET;

// ❌ WRONG - Hardcoded secrets
const dbPassword = 'hardcoded_password_123';
```

### Security Headers
```javascript
// ✅ CORRECT - Security headers
app.use((req, res, next) => {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('X-Frame-Options', 'DENY');
    res.setHeader('X-XSS-Protection', '1; mode=block');
    res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
    next();
});
```

## Security Testing Requirements

### Unit Tests Must Include:
```javascript
// Security test examples
describe('Authentication', () => {
    it('should reject invalid JWT tokens', async () => {
        const response = await request(app)
            .get('/protected')
            .set('Authorization', 'Bearer invalid_token')
            .expect(401);
    });
    
    it('should prevent SQL injection', async () => {
        const maliciousInput = "'; DROP TABLE users; --";
        const response = await request(app)
            .post('/search')
            .send({ query: maliciousInput })
            .expect(400); // Should reject, not crash
    });
});
```

### Integration Tests Must Cover:
- Authentication flow security
- Authorization boundary testing
- Input validation edge cases
- Rate limiting functionality
- CSRF protection mechanisms

## Common Security Anti-Patterns to Avoid

### ❌ **Never Do This:**
```javascript
// Don't trust client-side validation only
if (clientSideValid) { /* unsafe */ }

// Don't expose sensitive data in client code
const config = { 
    apiKey: 'secret_key_123',
    dbPassword: 'password'
};

// Don't use weak randomization
const sessionId = Math.random().toString(36);

// Don't ignore HTTPS in production
app.listen(80, () => console.log('HTTP server running'));
```

### ✅ **Always Do This:**
```javascript
// Always validate server-side
const isValid = validateOnServer(input);

// Keep secrets on server-side only
const config = {
    apiKey: process.env.API_KEY,
    publicSetting: 'safe_to_expose'
};

// Use cryptographically secure random
const sessionId = crypto.randomBytes(32).toString('hex');

// Enforce HTTPS in production
if (process.env.NODE_ENV === 'production') {
    app.use(enforceHTTPS);
}
```

## Incident Response

### If Security Vulnerability Discovered:
1. **IMMEDIATE**: Update TODO with `healthCheck: "critical"`
2. **ESCALATE**: Flag for immediate security review
3. **DOCUMENT**: Create detailed security incident report
4. **COORDINATE**: Work with @security agent for remediation
5. **VALIDATE**: Ensure fix doesn't break functionality
6. **VERIFY**: Confirm vulnerability is resolved

## Security Knowledge Resources

### Required Reading:
- OWASP Top 10 Web Application Security Risks
- Framework-specific security guides (React, Node.js, etc.)
- Database security best practices
- API security guidelines

### Tools Integration:
- Static Application Security Testing (SAST)
- Dynamic Application Security Testing (DAST)
- Dependency vulnerability scanning
- Code quality security rules

This document serves as the baseline security standard that all developers must follow. The @security agent will use these standards as the foundation for all security reviews and assessments.
