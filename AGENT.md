# Django Influencer Marketing Platform Agent Guide

## Commands
- **Run server**: `python manage.py runserver`
- **Run all tests**: `python manage.py test`
- **Run single test**: `python manage.py test app.tests.TestClassName.test_method_name`
- **Migrations**: `python manage.py makemigrations` then `python manage.py migrate`
- **Static files**: `python manage.py collectstatic`
- **Superuser**: `python manage.py createsuperuser`
- **Database**: Uses PyMySQL with MySQL backend
- **Build**: `bash build_files.sh` (for Vercel deployment)

## Architecture
- **Django 4.2** web framework with custom User model (`accounts.User`)
- **Apps**: accounts (user management), campaigns (business campaigns), messaging (communications)
- **Database**: MySQL via PyMySQL, hosted on external service (filess.io)
- **Authentication**: Social auth with Facebook/Google OAuth2 using `social-auth-app-django`
- **Deployment**: Vercel serverless with static files, also supports cPanel hosting
- **Media**: File uploads stored in media/ directory

## Code Style
- **Imports**: Django imports first, then third-party, then local apps
- **Models**: Use `BigAutoField` for primary keys, custom User model extends AbstractUser
- **Settings**: Sensitive data uses environment variables (secrets marked as [REDACTED])
- **Templates**: Bootstrap for styling, organized by app in templates/appname/
- **Static files**: App-specific static files in app/static/appname/
- **Error handling**: Standard Django patterns, custom pipeline for social auth
