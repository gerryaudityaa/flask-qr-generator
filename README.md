# Flask QR Code Generator

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey.svg)](https://flask.palletsprojects.com/)
[![QR Code](https://img.shields.io/badge/QR_Code-Generator-green.svg)](https://pypi.org/project/qrcode/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## About The Project

This is a **Flask web application** designed for generating highly customizable **QR codes**. Whether you need a simple QR for a URL, detailed contact information, or Wi-Fi network credentials, this tool provides an intuitive interface to create them with various aesthetic options.

The project emphasizes ease of use, allowing users to control aspects like foreground/background colors, size, error correction, and even add a custom logo to their QR codes. It supports common QR code types and includes basic history tracking (per user IP) and management features.

---

## Features

* **Multiple QR Code Types**: Generate QR codes for:
    * Plain Text
    * URLs
    * Phone Numbers
    * Email Addresses
    * **Wi-Fi Network Credentials** (SSID, Password, Encryption)
    * **vCard (Contact Information)** with fields for name, organization, phone, email, address, website, and optional profile photo URL and notes.
* **Customization Options**:
    * Adjust **Foreground and Background Colors**.
    * Control **Size** and **Border** thickness.
    * Select **Error Correction Level** (L, M, Q, H).
    * Option for **Rounded Modules**.
    * Choose **Output Format** (PNG or SVG).
    * **Add Custom Logo** to the center of the QR code (for PNG output).
* **User-Friendly Interface**: Simple and responsive form for quick generation.
* **QR Code Preview**: Instantly see your generated QR code.
* **Download Options**: Easily download the generated QR code.
* **History Tracking**: View a list of QR codes generated from your IP address.
* **Database Integration**: Stores QR code generation details using SQLite.
* **Automatic Database Schema Updates**: Handles adding new columns to the SQLite database automatically on startup if they don't exist.

---

## Getting Started

Follow these steps to get a local copy of the project up and running.

### Prerequisites

* Python 3.x installed on your system.
* `pip` (Python package installer).

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/gerryaudityaa/flask-qr-generator.git](https://github.com/gerryaudityaa/flask-qr-generator.git)
    cd flask-qr-generator
    ```

2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv venv
    ```
    * On Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    * On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

3.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```
    *If you don't have `requirements.txt` yet, create one by running `pip freeze > requirements.txt` after installing Flask, qrcode, Pillow, and Werkzeug.*
    ```bash
    pip install Flask qrcode Pillow Werkzeug
    ```
    Then run `pip freeze > requirements.txt` to generate the file for future use.

4.  **Configure your application:**
    Create a `config.py` file in the root directory if it doesn't exist.
    ```python
    # config.py
    import os

    class Config:
        SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_super_secret_key_here'
        UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'images', 'uploads')
        QR_FOLDER = os.path.join(os.getcwd(), 'static', 'qr_codes')
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
        MAX_CONTENT_LENGTH = 2 * 1024 * 1024 # 2 Megabytes
    ```
    *Replace `'your_super_secret_key_here'` with a strong, random string for production environments.*

5.  **Run the application:**
    ```bash
    flask run
    ```
    The application should now be running at `http://127.0.0.1:5000/`.

---

## Usage

1.  **Select QR Code Type**: Choose from `Text`, `URL`, `Phone Number`, `Email`, `Wi-Fi`, or `vCard`.
2.  **Enter Content**: Fill in the relevant details based on the selected type. For `Wi-Fi` and `vCard`, specific fields will appear.
3.  **Customize (Optional)**: Adjust colors, size, border, error correction, rounded modules, and output format. You can also upload a logo image to be embedded in the center of the QR code (PNG format only).
4.  **Generate**: Click the "Generate QR Code" button. The QR code preview will appear on the right.
5.  **Download**: Use the "Download" button to save your QR code image.
6.  **History**: Visit the `/history` endpoint to see all QR codes generated from your IP address and manage them.

### Important Notes on vCard Photo and Styling

* **vCard Profile Photo**: When generating a vCard, you can provide a "Profile Photo URL." This URL points to an image hosted online. Not all contact applications will automatically fetch or display this image when the vCard is imported. The size of the QR code increases with more data, so linking to an external image URL is more practical than embedding raw image data directly.
* **vCard Styling**: The visual style (fonts, layout, colors, etc.) of the vCard after it's scanned and imported into a contact app is determined by the *receiving device's operating system and contact application*, not by the QR code itself. We only provide the structured data.

---

## Contributing

Contributions are welcome! If you have suggestions for improvements, new features, or bug fixes, please open an issue or submit a pull request.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

## Contact

Gerry Auditya - [gerryauditya@gmail.com](mailto:gerryauditya@gmail.com)

## Live Demo
[flask-qr-generator](https://gerryauditya.pythonanywhere.com/)
