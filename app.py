import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
import qrcode.image.svg as svg
from io import BytesIO
import sqlite3
from config import Config
from PIL import Image

app = Flask(__name__)
app.config.from_object(Config)

# Setup database
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        conn = get_db_connection()
        
        # 1. Pastikan tabel qr_codes ada
        conn.execute('''
            CREATE TABLE IF NOT EXISTS qr_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_ip TEXT,
                content TEXT,
                qr_type TEXT,
                foreground_color TEXT,
                background_color TEXT,
                size INTEGER,
                error_correction TEXT,
                border INTEGER,
                logo_path TEXT,
                qr_filename TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. Periksa dan tambahkan kolom 'qr_filename' jika belum ada
        cursor = conn.execute("PRAGMA table_info(qr_codes)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'qr_filename' not in columns:
            try:
                conn.execute("ALTER TABLE qr_codes ADD COLUMN qr_filename TEXT")
                app.logger.info("Kolom 'qr_filename' berhasil ditambahkan ke tabel 'qr_codes'.")
            except sqlite3.OperationalError as e:
                app.logger.error(f"Gagal menambahkan kolom 'qr_filename': {e}")
        
        # Tambahkan kolom untuk URL foto profil jika belum ada
        if 'profile_photo_url' not in columns:
            try:
                conn.execute("ALTER TABLE qr_codes ADD COLUMN profile_photo_url TEXT")
                app.logger.info("Kolom 'profile_photo_url' berhasil ditambahkan ke tabel 'qr_codes'.")
            except sqlite3.OperationalError as e:
                app.logger.error(f"Gagal menambahkan kolom 'profile_photo_url': {e}")
                
        # Tambahkan kolom untuk notes jika belum ada
        if 'notes' not in columns:
            try:
                conn.execute("ALTER TABLE qr_codes ADD COLUMN notes TEXT")
                app.logger.info("Kolom 'notes' berhasil ditambahkan ke tabel 'qr_codes'.")
            except sqlite3.OperationalError as e:
                app.logger.error(f"Gagal menambahkan kolom 'notes': {e}")

        conn.commit()
        conn.close()

init_db()

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_qr_code(data, qr_type, options):
    error_correction_map = {
        'L': qrcode.constants.ERROR_CORRECT_L,
        'M': qrcode.constants.ERROR_CORRECT_M,
        'Q': qrcode.constants.ERROR_CORRECT_Q,
        'H': qrcode.constants.ERROR_CORRECT_H
    }
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=error_correction_map.get(options['error_correction'], qrcode.constants.ERROR_CORRECT_H),
        box_size=options['size'],
        border=options['border']
    )
    
    qr.add_data(data)
    qr.make(fit=True)
    
    if options['format'] == 'svg':
        factory = svg.SvgPathImage
        img = qr.make_image(
            image_factory=factory,
            fill_color=options['foreground_color'],
            back_color=options['background_color']
        )
    else:
        img = qr.make_image(
            image_factory=StyledPilImage,
            fill_color=options['foreground_color'],
            back_color=options['background_color'],
            module_drawer=RoundedModuleDrawer() if options.get('rounded', False) else None
        )
        
        if options.get('logo_path') and os.path.exists(options['logo_path']):
            try:
                logo = Image.open(options['logo_path'])
                if not isinstance(img, Image.Image):
                    img = img.get_image()

                logo_size = min(img.size) // 4 
                logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                
                pos = ((img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2)
                img.paste(logo, pos, logo if logo.mode == 'RGBA' else None)
            except Exception as e:
                app.logger.error(f"Error adding logo: {str(e)}")
    
    return img

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route('/')
def index():
    default_form_data = {
        'content': '',
        'ssid': '',
        'password': '',
        'encryption': 'WPA',
        'first_name': '',
        'last_name': '',
        'organization': '',
        'title': '',
        'phone': '',
        'email': '',
        'address': '',
        'website': '',
        'profile_photo_url': '',
        'notes': ''
    }
    default_options = {
        'foreground_color': '#000000',
        'background_color': '#FFFFFF',
        'size': 10,
        'error_correction': 'H',
        'border': 4,
        'rounded': False,
        'format': 'png',
        'logo_path': None
    }
    return render_template('index.html', 
                           form_data=default_form_data, 
                           qr_type='text',
                           options=default_options)

@app.route('/generate', methods=['POST'])
def generate():
    qr_code = None
    form_data = request.form
    qr_type = request.form.get('qr_type', 'text')
    options = {
        'foreground_color': request.form.get('foreground_color', '#000000'),
        'background_color': request.form.get('background_color', '#FFFFFF'),
        'size': int(request.form.get('size', 10)),
        'error_correction': request.form.get('error_correction', 'H'),
        'border': int(request.form.get('border', 4)),
        'rounded': request.form.get('rounded', 'false') == 'true',
        'format': request.form.get('format', 'png'),
        'logo_path': None
    }
    
    data_to_encode = ""
    content_for_db = ""

    try:
        if 'logo' in request.files:
            file = request.files['logo']
            if file.filename != '' and allowed_file(file.filename):
                try:
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    filename = secure_filename(file.filename)
                    logo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(logo_path)
                    options['logo_path'] = logo_path
                except Exception as e:
                    app.logger.error(f"Error saving logo: {str(e)}")
                    flash(f"Error uploading logo: {str(e)}", 'warning')

        if qr_type == 'wifi':
            ssid = request.form.get('ssid', '').strip()
            password = request.form.get('password', '').strip()
            encryption = request.form.get('encryption', 'WPA')

            if not ssid:
                flash('SSID is required for WiFi QR code', 'danger')
                return render_template('index.html', 
                                       form_data=form_data,
                                       qr_type=qr_type,
                                       options=options)

            ssid_escaped = ssid.replace(';', '\\;')
            password_escaped = password.replace(';', '\\;')

            data_to_encode = f"WIFI:T:{encryption};S:{ssid_escaped};P:{password_escaped};;"
            content_for_db = f"SSID: {ssid}, Encryption: {encryption}, Password: {'*' * len(password) if password else 'None'}"

        elif qr_type == 'vcard':
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            organization = request.form.get('organization', '').strip()
            title = request.form.get('title', '').strip()
            phone = request.form.get('phone', '').strip()
            email = request.form.get('email', '').strip()
            address = request.form.get('address', '').strip()
            website = request.form.get('website', '').strip()
            profile_photo_url = request.form.get('profile_photo_url', '').strip()
            notes = request.form.get('notes', '').strip()
            
            if not first_name and not last_name:
                flash('At least first name or last name is required for vCard', 'danger')
                return render_template('index.html', 
                                       form_data=form_data,
                                       qr_type=qr_type,
                                       options=options)

            vcard_lines = [
                "BEGIN:VCARD",
                "VERSION:3.0",
                f"N:{last_name};{first_name};;;", 
                f"FN:{first_name} {last_name}".strip(),
            ]
            if organization:
                vcard_lines.append(f"ORG:{organization}")
            if title:
                vcard_lines.append(f"TITLE:{title}")
            if phone:
                vcard_lines.append(f"TEL;TYPE=WORK,VOICE:{phone}")
            if email:
                vcard_lines.append(f"EMAIL;TYPE=PREF,INTERNET:{email}")
            if address:
                vcard_lines.append(f"ADR;TYPE=WORK:;;{address};;;;")
            if website:
                vcard_lines.append(f"URL:{website}")
            if profile_photo_url:
                vcard_lines.append(f"PHOTO;VALUE=uri:{profile_photo_url}")
            if notes:
                vcard_lines.append(f"NOTE:{notes}")
            
            vcard_lines.append("END:VCARD")
            data_to_encode = "\n".join(vcard_lines)
            content_for_db = f"Name: {first_name} {last_name}, Org: {organization}, Phone: {phone}, Email: {email}, Photo: {profile_photo_url}, Notes: {notes}"

        else:
            data_to_encode = request.form.get('content', '').strip()
            if not data_to_encode:
                flash('Content is required', 'danger')
                return render_template('index.html', 
                                       form_data=form_data,
                                       qr_type=qr_type,
                                       options=options)

            if qr_type == 'url' and not data_to_encode.startswith(('http://', 'https://')):
                data_to_encode = 'http://' + data_to_encode
            elif qr_type == 'phone':
                data_to_encode = f'tel:{data_to_encode}'
            elif qr_type == 'email':
                data_to_encode = f'mailto:{data_to_encode}'
            
            content_for_db = data_to_encode

        img = generate_qr_code(data_to_encode, qr_type, options)

        os.makedirs(app.config['QR_FOLDER'], exist_ok=True)
        qr_filename = f"qr_{datetime.now().strftime('%Y%m%d%H%M%S_%f')}.{options['format']}"
        qr_path = os.path.join(app.config['QR_FOLDER'], qr_filename)

        if options['format'] == 'svg':
            with open(qr_path, 'wb') as f:
                img.save(f)
        else:
            img.save(qr_path)
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO qr_codes (user_ip, content, qr_type, foreground_color, background_color, size, error_correction, border, logo_path, qr_filename, profile_photo_url, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.remote_addr,
            content_for_db,
            qr_type,
            options['foreground_color'],
            options['background_color'],
            options['size'],
            options['error_correction'],
            options['border'],
            options['logo_path'],
            qr_filename,
            form_data.get('profile_photo_url', ''),
            form_data.get('notes', '')
        ))
        conn.commit()
        conn.close()

        flash('QR Code generated successfully!', 'success')
        return render_template('index.html', 
                               qr_code=qr_filename,
                               form_data=form_data,
                               qr_type=qr_type,
                               options=options)

    except Exception as e:
        app.logger.error(f"Error generating QR code: {str(e)}")
        flash(f'An error occurred while generating QR code: {str(e)}', 'danger')
        return render_template('index.html', 
                               form_data=form_data,
                               qr_type=qr_type,
                               options=options)


@app.route('/qr_codes/<filename>')
def serve_qr_code(filename):
    return send_from_directory(app.config['QR_FOLDER'], filename)

@app.route('/history')
def history():
    conn = get_db_connection()
    qr_codes = conn.execute('''
        SELECT * FROM qr_codes 
        WHERE user_ip = ? 
        ORDER BY created_at DESC
    ''', (request.remote_addr,)).fetchall()
    conn.close()
    return render_template('history.html', qr_codes=qr_codes)

@app.route('/delete/<int:id>')
def delete_qr_code(id):
    conn = get_db_connection()
    qr_code = conn.execute('SELECT * FROM qr_codes WHERE id = ?', (id,)).fetchone()
    
    if qr_code and qr_code['user_ip'] == request.remote_addr:
        # Periksa apakah qr_filename ada dan bukan None sebelum mencoba menghapusnya
        if qr_code['qr_filename']:
            qr_file_to_delete = os.path.join(app.config['QR_FOLDER'], qr_code['qr_filename'])
            if os.path.exists(qr_file_to_delete):
                try:
                    os.remove(qr_file_to_delete)
                    app.logger.info(f"Deleted QR file: {qr_file_to_delete}")
                except OSError as e:
                    app.logger.error(f"Error deleting QR file {qr_file_to_delete}: {e}")
            else:
                app.logger.warning(f"QR file not found: {qr_file_to_delete}")
        else:
            app.logger.warning(f"qr_filename for QR ID {id} is None. File not deleted.")
        
        # Hapus logo jika ada dan path-nya valid
        if qr_code['logo_path'] and os.path.exists(qr_code['logo_path']):
            try:
                os.remove(qr_code['logo_path'])
                app.logger.info(f"Deleted logo file: {qr_code['logo_path']}")
            except OSError as e:
                app.logger.error(f"Error deleting logo file {qr_code['logo_path']}: {e}")
        
        # Hapus dari database terlepas dari apakah file fisik ditemukan/dihapus
        conn.execute('DELETE FROM qr_codes WHERE id = ?', (id,))
        conn.commit()
        flash('QR code deleted successfully', 'success')
    else:
        flash('QR code not found or unauthorized', 'danger')
    
    conn.close()
    return redirect(url_for('history'))

if __name__ == '__main__':
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.QR_FOLDER, exist_ok=True)
    app.run(debug=True)