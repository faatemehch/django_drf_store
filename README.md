# 🛍️ Online Shopping API - Django REST Framework

![Django REST Framework](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray)
![MySQL](https://img.shields.io/badge/MySQL-316192?style=for-the-badge&logo=mysql&logoColor=white)

A complete e-commerce backend API built with Django REST Framework, product management, shopping cart functionality, and order processing.

## ✨ Features

- **User System**:
  - User profiles with order history
  - Admin dashboard

- **Product Management**:
  - CRUD operations for products
  - Category system
  - Advanced search & filtering

- **Shopping Flow**:
  - Cart management
  - Checkout process
  - Order tracking

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- MySql
- pip

### Installation
```bash
# Clone the repository
git clone https://github.com/your-username/online-shop-api.git
cd online-shop-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Run development server
python manage.py runserver
```


## 🏗️ Project Structure
.
├── config/               # Project configuration
│   ├── settings/       # Split settings
│   └── urls.py         # Main URLs
├── apps/
│   ├── core/          # Authentication         
│   └── store/           # Product Order Cart models/views
├── manage.py
└── requirements.txt


## 🤝 Contributing
Contributions are welcome! Please follow these steps:

Fork the project

Create your feature branch (git checkout -b feature/AmazingFeature)

Commit your changes (git commit -m 'Add some amazing feature')

Push to the branch (git push origin feature/AmazingFeature)

Open a Pull Request
