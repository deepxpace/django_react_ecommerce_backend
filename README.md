# Django React E-commerce Backend

Django React E-commerce Frontend can be access at https://github.com/auriorajaa/django_react_ecommerce_frontend

This is the backend repository for Upfront, a multi-vendor e-commerce platform built with Django Rest Framework. This backend provides RESTful APIs to support the e-commerce functionality including user authentication, product management, order processing, and payment integration.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- PostgreSQL (recommended for production)

## Installation

1. Clone the repository
```bash
git clone https://github.com/auriorajaa/django_react_ecommerce_backend.git
cd django_react_ecommerce_backend
```

2. Create and activate a virtual environment
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create `.env` file
Create a `.env` file in the root directory and add the following environment variables:
```
STRIPE_PUBLIC_KEY=your_stripe_public_key
STRIPE_SECRET_KEY=your_stripe_secret_key
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_SECRET_ID=your_paypal_secret_id
MAILERSEND_API_KEY=your_mailersend_api_key
MAILERSEND_SENDER_DOMAIN=your_sender_domain
FROM_EMAIL=your_from_email
EMAIL_BACKEND=anymail.backends.mailersend.EmailBackend
DEFAULT_FROM_EMAIL=your_default_from_email
SERVER_EMAIL=your_server_email
```

5. Run database migrations
```bash
python manage.py migrate
```

6. Create a superuser (admin)
```bash
python manage.py createsuperuser
```

7. Start the development server
```bash
python manage.py runserver
```

The server will start at `http://localhost:8000`

## API Documentation

Once the server is running, you can access the API documentation at:
- Swagger UI: `http://localhost:8000/`

## Payment Integration

This backend integrates with both Stripe and PayPal for payment processing. Make sure to:
1. Set up accounts with Stripe and PayPal
2. Obtain the necessary API keys
3. Add them to your `.env` file

## Email Configuration

The project uses MailerSend for email services. Ensure you:
1. Have a MailerSend account
2. Configure your sender domain
3. Add the API key and domain to your `.env` file

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details
