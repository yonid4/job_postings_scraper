# Supabase Authentication Configuration Guide

## Issue: Email Confirmation Required

The current setup requires users to confirm their email before they can sign in. This is the default behavior in Supabase.

## Solutions

### Option 1: Configure Supabase to Allow Unconfirmed Users (Recommended for Testing)

1. **Go to your Supabase Dashboard**
   - Navigate to your project at https://supabase.com/dashboard
   - Select your project

2. **Navigate to Authentication Settings**
   - Go to **Authentication** → **Settings**
   - Scroll down to **Email Auth** section

3. **Configure Email Confirmation**
   - Find **"Confirm email"** setting
   - Set it to **"No confirmation required"** for testing
   - Or set it to **"Confirm email"** for production

4. **Save Changes**
   - Click **Save** to apply the changes

### Option 2: Use Service Role Key (Current Implementation)

The current implementation uses the service role key to automatically confirm users in testing mode. This requires:

1. **Set the Service Role Key**
   ```bash
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
   ```

2. **Enable Testing Mode**
   ```bash
   TESTING_MODE=true
   ```

### Option 3: Manual Email Confirmation

Users can manually confirm their email by:

1. **Check Email**
   - After registration, users receive a confirmation email
   - Click the confirmation link in the email

2. **Resend Confirmation**
   - Use the "Resend Verification" feature in the app

## Current Implementation

The app currently handles this by:

- **Testing Mode**: Uses service role key to auto-confirm users
- **Production Mode**: Requires manual email confirmation
- **Fallback**: Shows appropriate error messages

## Testing the Fix

1. **With Service Role Key**:
   ```bash
   TESTING_MODE=true
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   python scripts/test_supabase_connection.py
   ```

2. **Without Service Role Key**:
   - Configure Supabase dashboard as described in Option 1
   - Or manually confirm emails

## Troubleshooting

### "Email not confirmed" Error
- **Cause**: User hasn't confirmed their email
- **Solution**: Configure Supabase settings or use service role key

### "User not allowed" Error
- **Cause**: Admin operations with anon key
- **Solution**: Use service role key for admin operations

### "Service role key not found" Error
- **Cause**: Missing SUPABASE_SERVICE_ROLE_KEY
- **Solution**: Add the service role key to your .env file

## Security Notes

- **Service Role Key**: Has admin privileges - keep it secure
- **Testing Mode**: Should only be used in development
- **Production**: Always require email confirmation for security 