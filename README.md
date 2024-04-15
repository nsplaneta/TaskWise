
# TaskWise Project Installation Guide

Welcome to the TaskWise project! This comprehensive guide will assist you in downloading, installing, and running this Django project on Windows, macOS, and Linux, ensuring you have all the tools necessary for a successful setup.

## Prerequisites

Before proceeding, ensure Python 3.6 or newer is installed on your system. Python is essential for running the Django framework. If Python is not yet installed, download it from the [official Python website](https://www.python.org/downloads/).

Additionally, this guide will cover the installation of Git, crucial for cloning the project repository.

## Installing Git

Git is necessary for version control and downloading the project from GitHub.

### Windows

- Download and install Git from [Git for Windows](https://git-scm.com/download/win).
- Run the installer, following on-screen instructions, and accept the default options unless you have specific preferences.

### macOS

- Open Terminal.
- Install Git using Homebrew with `brew install git`. If Homebrew isn't installed, run `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`.

### Linux

- Open Terminal.
- Use your distribution's package manager to install Git, e.g., on Ubuntu or Debian, `sudo apt-get install git`.

## Downloading and Setting Up the Project

1. **Clone the Repository**: In your command line interface (CLI), run:
   ```bash
   git clone https://github.com/nsplaneta/TaskWise.git
   ```
   ```bash
   cd TaskWise
   ```

2. **Create and Activate a Virtual Environment**:
   - **Windows**: `python -m venv venv && .\venv\Scripts\activate`
   - **macOS/Linux**: `python3 -m venv venv && source venv/bin/activate`

3. **Install Dependencies**: Ensure your virtual environment is activated and run:
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure the SQLite Database**:
   - **Database Setup:** The default configuration uses a SQLite database named db.sqlite3 located in the base directory of the project. Modify the DATABASES setting in settings.py if a different setup is required.
   - **Database Migrations**: Prepare your database schema by running:
      ```bash
      python manage.py migrate
      ```
      
   **Alternatively, to SQLite you can use MySQL**
   - **Install MySQL Server**: Download and install MySQL from its official page. Follow the installation guide specific to your operating system.
   - **Create a Database**: Use the MySQL command line to create your database:
   ```bash
   CREATE DATABASE taskwise CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
   - **Install MySQL Database Adapter**:
   ```bash
   pip install mysqlclient
   ```
   - **Configure Database Settings in Django**:
      Update the **DATABASES** setting in your **settings.py**:
      ```bash
      DATABASES = {
          'default': {
              'ENGINE': 'django.db.backends.mysql',
              'NAME': 'taskwise',
              'USER': 'your_mysql_username',
              'PASSWORD': 'your_mysql_password',
              'HOST': 'localhost',
              'PORT': '3306',
          }
      }
      ```

6. **Create a Superuser (Optional)**: To access Django’s admin panel, create a superuser with:
   ```bash
   python manage.py createsuperuser
   ```
   and follow the prompts.

## Running the Project

Launch the Django development server using:
```bash
python manage.py runserver
```
Your project will be accessible at `http://127.0.0.1:8000/`.

## Essential Configuration

### Setting Up Categories

Categories and subcategories are critical to the TaskWise webapp's operation. Before using the webapp, populate your database with predefined categories by running:
```bash
python manage.py categories
```
You can customize these categories in `TaskWise\tasks\management\commands\categories.py` to fit your project's needs. This step is mandatory for the webapp to function properly.

### Populating the Database with Sample Data

For demonstration or testing, populate the database with sample data using:
```bash
pip install Faker  # Required only once
```
```bash
python manage.py populate_data
```
This command uses the Faker library to generate random data, enriching your testing environment.

## Important Notes

- **Activation of Categories**: Without setting up the categories, the webapp cannot function normally. Ensure this setup is completed before use.
- **Running Commands**: Always activate your virtual environment before running installation commands or starting the webapp.
- Both `categories` and `populate_data` commands are designed to be idempotent, ensuring safe repeated execution.

Following these steps will ensure a smooth setup and operation of the TaskWise project, allowing for an effective development and testing environment.
