
# Frontend Registration System Usage Example

## 1. Environment Setup

```bash
# Set required environment variables
export SUPABASE_URL="your_supabase_url"
export NEXT_PUBLIC_SUPABASE_ANON_KEY="your_anon_key"
export SUPABASE_SERVICE_ROLE_KEY="your_service_role_key"
```

## 2. Flask Routes

Add these routes to your Flask application:

```python
from flask import render_template

@app.route('/auth/register-supabase')
def register_supabase():
    return render_template('auth/register_supabase.html')

@app.route('/auth/login-supabase')
def login_supabase():
    return render_template('auth/login_supabase.html')
```

## 3. Template Integration

The templates automatically:
- Load Supabase JavaScript client
- Handle form validation
- Show loading states
- Display error messages
- Redirect after success

## 4. Testing the System

### Manual Testing:
1. Navigate to `/auth/register-supabase`
2. Fill out the registration form
3. Submit and check for success message
4. Verify email verification works
5. Test login at `/auth/login-supabase`

### Automated Testing:
```bash
python scripts/test_frontend_templates.py
```

## 5. Customization

### Styling:
- Modify CSS in the `<style>` section of templates
- Update color schemes and gradients
- Adjust responsive breakpoints

### Validation:
- Modify JavaScript validation functions
- Add custom validation rules
- Update error messages

### Integration:
- Add additional form fields
- Customize success/error handling
- Modify redirect URLs

## 6. Production Deployment

### Checklist:
- [ ] Set all environment variables
- [ ] Configure Supabase email templates
- [ ] Test email verification flow
- [ ] Verify database triggers work
- [ ] Set up error monitoring
- [ ] Configure SSL certificate
- [ ] Test on multiple devices

### Security:
- [ ] Use HTTPS in production
- [ ] Validate all inputs
- [ ] Implement rate limiting
- [ ] Monitor for suspicious activity
- [ ] Regular security audits
