# 🛍️ Online Shopping API - Django REST Framework

![Django REST Framework](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=JSON%20web%20tokens)

A complete e-commerce backend API built with Django REST Framework, featuring JWT authentication, product management, shopping cart functionality, and order processing.

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
