
# Farmacruz Ecommerce

**Status:** `In Development` 🚧

A private B2B ecommerce platform designed for Farmacruz, a pharmaceutical distributor. This project aims to replace an outdated web application, providing a modern, efficient, and reliable sales channel for its clients (pharmacies) and streamlining the order validation process for its sales team.

The core technical challenge of this project is the integration with a legacy Alpha ERP system that relies on flat-file data exchange, requiring a custom-built data synchronization service.

---

## Core Features

The platform is divided into three main user-facing modules:

* **Admin Panel:**

  * User management (create, edit, delete clients and sellers).
  * Role assignment.
  * Sales and activity dashboards.
* **Seller Portal:**

  * View incoming orders from assigned clients.
  * Validate and approve orders before they are processed by the ERP.
* **Client (Pharmacy) Portal:**

  * Secure login with credentials provided by the admin.
  * Browse product catalog with real-time stock information.
  * Add products to a shopping cart.
  * Place orders for seller validation.
  * View order history and status.

---

## Tech Stack

This project uses a modern, decoupled architecture to ensure scalability and maintainability.

* **Backend:** Python 3.11+ with **Django** & **Django REST Framework**.
  * *Handles all business logic, user authentication, and provides the core API.*
* **Frontend:** JavaScript with **React.js**.
  * *A Single Page Application (SPA) that consumes the Django API to provide a fast and interactive user interface.*
* **Database:** **PostgreSQL**.
  * *Stores all application-specific data such as user profiles, shopping carts, and order history.*
* **Integration Service:** A standalone **Python script** using the **Pandas** library.
  * *Runs on a schedule to parse flat files from the Alpha ERP, synchronize product/stock data, and generate order files for ERP processing.*

---

## Getting Started

*(Instructions to be added as the project develops)*

### Prerequisites

* Git
* Python 3.11+
* Poetry (or pip)
* Node.js 20+
* PostgreSQL Server

### Installation

1. **Clone the repository:**

   ```bash
   git clone [your-repo-url]
   cd farmacruz-ecommerce
   ```
2. **Backend Setup:**
   *(Instructions for setting up the Django environment will be added here)*
3. **Frontend Setup:**
   *(Instructions for setting up the React environment will be added here)*
