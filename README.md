# IT Park Hackathon Rent Platform

A comprehensive office rental platform built with FastAPI, SQLAlchemy, and TailwindCSS for IT Park Uzbekistan. This platform enables property management, rental requests, and multi-level approval workflows.

## 🚀 Features

### Core Functionality
- **Building Management**: Add, edit, and manage office buildings with detailed information
- **Space Management**: Support for both individual rooms and entire floors (open space)
- **Image Gallery**: Multiple image uploads with 360° photo support
- **Amenities System**: Configurable building features and facilities
- **Multi-Region Support**: Geographic organization of properties

### User Management & Authentication
- **Role-Based Access Control**: Superadmin, Admin, Resident, and Signer roles
- **JWT Authentication**: Secure login with cookie-based sessions
- **Automatic User Creation**: Signers get automatic accounts with default passwords
- **Password Security**: Forced password change for default credentials

### Rental Workflow
- **Request Submission**: Residents can select spaces and submit rental requests
- **Multi-Level Approval**: Sequential approval chain (Regional Director → Manager → Accountant → Lawyer → CEO)
- **Contract Generation**: Automatic contract creation upon full approval
- **Notification System**: Real-time updates for all workflow stages

### Admin Dashboard
- **Unified Interface**: Single dashboard for all administrative tasks
- **Tabbed Navigation**: Organized sections for different management areas
- **Responsive Design**: Mobile-friendly interface with collapsible sidebar
- **Real-time Updates**: Success/error messages and status indicators

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python 3.12+)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: Jinja2 templates with TailwindCSS
- **Authentication**: JWT tokens with bcrypt/pbkdf2_sha256
- **File Handling**: Multipart file uploads with static file serving
- **Styling**: IT Park Uzbekistan brand colors and responsive design

## 📋 Prerequisites

- Python 3.12 or higher
- pip (Python package manager)
- Git

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd it_park_rent_platform
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Database
```bash
# The database will be created automatically on first run
python -m app.main
```

### 5. Create Superadmin Account
```bash
python add_super_admin.py
```

### 6. Run the Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at `http://localhost:8000`

## 🔐 Default Login Credentials

- **Email**: `admin@mail.com`
- **Password**: `12345`
- **Role**: Superadmin

⚠️ **Important**: Change the default password after first login!

## 📁 Project Structure

```
it_park_rent_platform/
├── app/
│   ├── __init__.py
│   ├── main.py              # Main FastAPI application
│   ├── models.py            # SQLAlchemy database models
│   ├── schemas.py           # Pydantic schemas
│   ├── database.py          # Database configuration
│   ├── auth.py              # Authentication logic
│   ├── utils.py             # Utility functions
│   ├── routers/             # API route modules
│   │   ├── buildings.py
│   │   ├── contracts.py
│   │   ├── users.py
│   │   ├── regions.py
│   │   ├── rooms.py
│   │   ├── building_photos.py
│   │   ├── approvals.py
│   │   ├── dashboard.py
│   │   ├── amenities.py
│   │   └── signers.py
│   ├── templates/           # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── dashboard.html
│   │   ├── building_detail.html
│   │   ├── resident_panel.html
│   │   ├── signer_panel.html
│   │   ├── login.html
│   │   └── change_password.html
│   ├── static/              # Static assets
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── uploads/             # User uploaded files
├── add_super_admin.py       # Superadmin creation script
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## 🌐 API Endpoints

### Public Routes
- `GET /` - Homepage with building listings
- `GET /building/{id}` - Building detail page
- `GET /login` - Login form

### Protected Routes
- `GET /admin` - Superadmin dashboard
- `GET /residentpanel` - Resident dashboard
- `GET /signerpanel` - Signer approval panel
- `GET /change-password` - Password change form

### Admin Management
- `POST /admin/buildings` - Create building
- `POST /admin/rooms` - Add rooms/spaces
- `POST /admin/signers` - Manage signers
- `POST /admin/amenities` - Manage building features

### Rental Workflow
- `POST /rental-requests` - Submit rental request
- `POST /request-approvals/{id}/approve` - Approve request
- `POST /request-approvals/{id}/decline` - Decline request

## 🎨 Brand Colors

The platform uses IT Park Uzbekistan's official color scheme:
- **Primary Green**: `#7CC223`
- **Dark Green**: `#6AB21C`
- **Dark Blue**: `#003366`

## 🔄 Database Schema

### Core Tables
- **users**: System users with role-based access
- **regions**: Geographic regions for organization
- **buildings**: Office building information
- **rooms**: Individual rooms and floor spaces
- **building_photos**: Building image gallery
- **amenities**: Building features and facilities
- **signers**: Approval workflow participants
- **rental_requests**: Tenant rental applications
- **request_approvals**: Multi-level approval tracking
- **contracts**: Finalized rental agreements
- **notifications**: System-wide notifications

## 🚀 Usage Guide

### For Superadmins
1. **Login** with default credentials
2. **Change password** when prompted
3. **Access dashboard** at `/admin`
4. **Manage** buildings, users, signers, and amenities
5. **Monitor** rental requests and approval workflows

### For Residents
1. **Browse** available buildings on homepage
2. **Select** desired spaces (rooms or floors)
3. **Submit** rental request with space selection
4. **Track** request status in resident panel
5. **View** approved contracts and notifications

### For Signers
1. **Login** with assigned credentials
2. **Access** signer panel at `/signerpanel`
3. **Review** pending rental requests
4. **Approve/Decline** with optional comments
5. **Monitor** approval workflow progress

## 🔧 Configuration

### Environment Variables
The application uses default configurations suitable for development. For production, consider setting:

```bash
export SECRET_KEY="your-secure-secret-key"
export DATABASE_URL="your-database-url"
export UPLOAD_DIR="path/to/upload/directory"
```

### Database
- **Development**: SQLite (auto-created)
- **Production**: PostgreSQL/MySQL recommended
- **Migrations**: Lightweight schema updates via `ensure_sqlite_schema()`

## 🧪 Testing

### Manual Testing
1. **Login Flow**: Test role-based redirects
2. **Building Creation**: Add buildings with images and amenities
3. **Rental Request**: Complete end-to-end workflow
4. **Approval Chain**: Test multi-level signer workflow

### API Testing
Use FastAPI's automatic documentation at `/docs` for API testing and exploration.

## 🚨 Security Features

- **JWT Authentication**: Secure token-based sessions
- **Password Hashing**: bcrypt/pbkdf2_sha256 with salt
- **Role-Based Access**: Granular permission control
- **Input Validation**: Pydantic schema validation
- **SQL Injection Protection**: SQLAlchemy ORM
- **File Upload Security**: Type and size validation

## 🔮 Future Enhancements

- **Email Notifications**: Automated workflow updates
- **PDF Generation**: Contract and invoice creation
- **Payment Integration**: Online rent payment processing
- **Mobile App**: React Native mobile application
- **Advanced Analytics**: Dashboard metrics and reporting
- **Multi-language Support**: Uzbek, Russian, English

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

## 📄 License

This project is developed for IT Park Uzbekistan hackathon purposes.

## 🆘 Support

For technical support or questions:
- **Repository Issues**: Create GitHub issues
- **Documentation**: Check this README and code comments
- **Development**: Review FastAPI and SQLAlchemy documentation

## 🎯 Project Goals

- **MVP Development**: Rapid prototype for hackathon
- **User Experience**: Intuitive interface for all user types
- **Workflow Automation**: Streamlined rental approval process
- **Scalability**: Foundation for production deployment
- **Brand Integration**: IT Park Uzbekistan visual identity

---

**Built with ❤️ for IT Park Uzbekistan Hackathon**

*Last updated: December 2024*
