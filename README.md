# Influenza - Influencer Marketing Platform

Influenza is a comprehensive platform that connects businesses with influencers for marketing campaigns. This platform enables businesses to create campaigns and find suitable influencers, while influencers can discover and apply to campaigns that match their profile.

## Features

### For Businesses
- Create a business profile with company details
- Create and manage marketing campaigns
- Browse and connect with vetted influencers
- Track campaign performance and ROI
- Manage payments to influencers

### For Influencers
- Create an influencer profile with social media accounts
- Showcase your audience and engagement metrics
- Browse and apply to relevant campaigns
- Track your campaign performance
- Receive payments for successful promotions
- **Login with Facebook** to automatically import your profile and follower data

## Getting Started

### Prerequisites
- Python 3.8+
- MySQL database
- Virtual environment (recommended)
- Facebook Developer Account (for Facebook Login)

### Installation

1. Clone the repository
2. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Configure your database settings in `influenza_platform/settings.py`
5. Run migrations:
   ```
   python manage.py migrate
   ```
6. Create a superuser:
   ```
   python manage.py createsuperuser
   ```
7. Run the development server:
   ```
   python manage.py runserver
   ```

## User Workflows

### Business User Workflow

1. **Registration**
   - Visit the homepage and click "Register"
   - Select "I am a Business"
   - Complete the registration form with your email and password
   - Fill out your business profile with company details

2. **Creating a Campaign**
   - Log in to your business dashboard
   - Click "Create Campaign" button
   - Fill out the campaign details including:
     - Campaign title and description
     - Requirements for influencers
     - Budget and timeline
     - Target platforms and audience
   - Submit the campaign

3. **Managing Applications**
   - View influencer applications in your dashboard
   - Review influencer profiles and proposals
   - Accept or reject applications
   - Communicate with approved influencers

4. **Tracking Performance**
   - Monitor campaign metrics in real-time
   - View engagement statistics across platforms
   - Analyze ROI and campaign effectiveness

### Influencer Workflow

1. **Registration**
   - Visit the homepage and click "Register"
   - Select "I am an Influencer"
   - Complete the registration form with your email and password
   - Fill out your influencer profile with social media accounts and audience metrics

2. **Finding Campaigns**
   - Log in to your influencer dashboard
   - Browse available campaigns that match your profile
   - Filter campaigns by industry, platform, or budget

3. **Applying to Campaigns**
   - View campaign details and requirements
   - Submit your proposal including your content ideas and fee

## cPanel Deployment Guide

### Prerequisites
- A cPanel hosting account with Python support
- SSH access to your hosting account (recommended)
- MySQL database access through cPanel

### Step 1: Prepare Your cPanel Account

1. **Create a Python Application**
   - Log in to your cPanel account
   - Navigate to the "Setup Python App" or similar section (may vary by host)
   - Create a new Python application with the following settings:
     - Python version: 3.8 or higher (match your local development version if possible)
     - Application root: The directory where you want to deploy your project (e.g., `influenza`)
     - Application URL: Your domain or subdomain (e.g., `https://influenza.yourdomain.com`)
     - Application startup file: `passenger_wsgi.py` (will be created later)

2. **Create a MySQL Database**
   - Go to the "MySQL Databases" section in cPanel
   - Create a new database (e.g., `yourusername_influenza`)
   - Create a new database user with a strong password
   - Add the user to the database with all privileges
   - Note down the database name, username, and password

### Step 2: Upload Your Project Files

1. **Prepare Your Project for Deployment**
   - Create a production settings file (`production_settings.py`) with appropriate configurations
   - Update `SECRET_KEY`, set `DEBUG = False`, and configure `ALLOWED_HOSTS`
   - Configure database settings to use your cPanel MySQL database

2. **Upload Files to cPanel**
   - Use FTP, SFTP, or cPanel's File Manager to upload your project files
   - Upload to the application root directory you specified earlier
   - Do not upload the `venv` directory or any local environment files

### Step 3: Set Up the Virtual Environment

1. **Create a Virtual Environment**
   - Connect to your server via SSH
   - Navigate to your application directory
   - Create a virtual environment:
     ```
     python3 -m venv venv
     source venv/bin/activate
     ```

2. **Install Dependencies**
   - With the virtual environment activated, install your project dependencies:
     ```
     pip install -r requirements.txt
     ```
   - If you encounter issues with `mysqlclient`, you may need to install it using your host's package manager or contact support

### Step 4: Configure Your Django Project

1. **Create a Passenger WSGI File**
   - Create a file named `passenger_wsgi.py` in your application root with the following content:
     ```python
     import os
     import sys
     
     # Add your project directory to the Python path
     sys.path.insert(0, os.path.dirname(__file__))
     
     # Set environment variables
     os.environ.setdefault("DJANGO_SETTINGS_MODULE", "influenza_platform.settings")
     
     # Import the WSGI application
     from django.core.wsgi import get_wsgi_application
     application = get_wsgi_application()
     ```

2. **Update Your Settings**
   - Modify your `settings.py` file or create a separate `production_settings.py`:
     ```python
     # Security settings
     DEBUG = False
     ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
     
     # Database settings
     DATABASES = {
         'default': {
             'ENGINE': 'django.db.backends.mysql',
             'NAME': 'yourusername_influenza',
             'USER': 'yourusername_dbuser',
             'PASSWORD': 'your_db_password',
             'HOST': 'localhost',
             'PORT': '3306',
         }
     }
     
     # Static and media files
     STATIC_URL = '/static/'
     STATIC_ROOT = os.path.join(BASE_DIR, 'static')
     
     MEDIA_URL = '/media/'
     MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
     ```

### Step 5: Set Up Static and Media Files

1. **Collect Static Files**
   - Run the following command to collect all static files:
     ```
     python manage.py collectstatic
     ```

2. **Configure .htaccess**
   - Create an `.htaccess` file in your application root with the following content:
     ```
     # Serve static files directly
     <IfModule mod_rewrite.c>
         RewriteEngine On
         RewriteRule ^static/(.*)$ static/$1 [L]
         RewriteRule ^media/(.*)$ media/$1 [L]
     </IfModule>
     ```

### Step 6: Run Migrations and Create Superuser

1. **Apply Migrations**
   - With your virtual environment activated, run:
     ```
     python manage.py migrate
     ```

2. **Create a Superuser**
   - Create an admin user:
     ```
     python manage.py createsuperuser
     ```

### Step 7: Configure cPanel for Your Django Application

1. **Set Up Application URL**
   - In cPanel, make sure your domain or subdomain points to your application directory

2. **Restart the Application**
   - In the Python App interface, restart your application
   - Some hosts may require you to touch the `tmp/restart.txt` file:
     ```
     mkdir -p tmp
     touch tmp/restart.txt
     ```

### Step 8: Verify Deployment

1. **Test Your Website**
   - Visit your domain in a web browser
   - Check if the site loads correctly
   - Test login functionality and other features

2. **Check Error Logs**
   - If you encounter issues, check the error logs in cPanel
   - Common issues include database connection problems, path issues, or permission errors

### Troubleshooting

1. **500 Internal Server Error**
   - Check your application's error log in cPanel
   - Verify database connection settings
   - Ensure all required packages are installed
   - Check file permissions (directories should be 755, files 644)

2. **Static Files Not Loading**
   - Verify that `STATIC_ROOT` is correctly set
   - Make sure you've run `collectstatic`
   - Check the `.htaccess` file configuration

3. **Database Connection Issues**
   - Verify database credentials in settings
   - Check if your database user has the correct permissions
   - Some hosts require specific host settings (e.g., `127.0.0.1` instead of `localhost`)

4. **Module Not Found Errors**
   - Ensure all dependencies are installed in your virtual environment
   - Check if your host supports all required Python packages

### Maintenance

1. **Updating Your Application**
   - Pull the latest code from your repository
   - Activate the virtual environment
   - Install any new dependencies
   - Apply migrations if needed
   - Collect static files if they've changed
   - Restart the application

2. **Backup Strategy**
   - Regularly backup your database through cPanel
   - Keep a backup of your media files
   - Consider setting up automated backups

3. **Security Considerations**
   - Keep your Django and all dependencies updated
   - Regularly change database and admin passwords
   - Consider implementing HTTPS if not already enabled
   - Review Django's deployment checklist: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
   - Wait for business approval

4. **Campaign Execution**
   - Receive notification of approved applications
   - Create and publish content according to campaign guidelines
   - Submit links to your posts for verification
   - Track engagement metrics

5. **Receiving Payment**
   - View payment status in your dashboard
   - Receive payments for completed campaigns

## Authentication

The platform supports multiple authentication methods:

- Email and password login
- Facebook OAuth login
- Google OAuth login

After login, users are automatically redirected to their appropriate dashboard based on their account type (business or influencer).

### Facebook Login Configuration

The platform is configured to use Facebook Login for influencers. This allows influencers to quickly sign up and automatically import their profile data and follower counts.

#### Facebook API Credentials

The following credentials are configured in the application:

- **App ID**: 1210454147373721
- **App Secret**: f9cf819235cde673123f04ead7c12d6a
- **Page ID**: 354214138121990

#### How Facebook Login Works

1. When an influencer clicks the "Login with Facebook" button, they are redirected to Facebook for authentication
2. After successful authentication, Facebook returns user data and an access token
3. The platform automatically:
   - Creates a user account with the 'influencer' type
   - Creates an influencer profile with data from Facebook
   - Fetches and stores the user's follower count (when available)
   - Stores the Facebook access token for future API calls

#### Implementation Details

The Facebook login integration uses the `social-auth-app-django` package with a custom pipeline that:

- Sets the user type to 'influencer'
- Creates an influencer profile with data from Facebook
- Stores the Facebook access token for later use
- Fetches follower counts using the Facebook Graph API

## Technical Details

- Built with Django web framework
- Bootstrap for responsive UI
- MySQL database for data storage
- Social authentication via social-auth-app-django
- Modern UI with animations and toast notifications

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For support or inquiries, please contact support@influenza-platform.com