from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import os
import io
import base64
from werkzeug.utils import secure_filename
from main import create_visual
import tempfile
from PIL import Image
from datetime import datetime
import time

app = Flask(__name__, static_url_path='/outputs', static_folder='outputs')
app.secret_key = 'your-secret-key-here'

# Upload klasörü
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Klasörleri oluştur
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        flash('Dosya seçilmedi!')
        return redirect(request.url)
    
    file = request.files['image']
    text = request.form.get('text', '')
    company_type = request.form.get('company_type', 'gazete')  # Firma seçimi
    
    if file.filename == '':
        flash('Dosya seçilmedi!')
        return redirect(request.url)
    
    if text.strip() == '':
        flash('Metin girin!')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Geçici dosya oluştur ve dosya yolu al
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        temp_input_path = temp_input.name
        temp_input.close()  # Dosyayı hemen kapat
        
        # Dosyayı geçici konuma kaydet
        file.save(temp_input_path)
        
        # Çıktı dosyası için benzersiz isim oluştur
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"visual_{timestamp}.png"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        try:
            # Görseli oluştur
            success = create_visual(temp_input_path, output_path, text, company_type)
            
            if success:
                # Görseli base64'e çevir (web'de göstermek için)
                with open(output_path, "rb") as img_file:
                    img_data = base64.b64encode(img_file.read()).decode()
                
                return render_template('result.html', 
                                     image_data=img_data, 
                                     filename=output_filename,
                                     text=text,
                                     company_type=company_type)
            else:
                flash('Görsel oluşturulurken hata oluştu!')
                return redirect(url_for('index'))
                
        except Exception as e:
            flash(f'Hata: {str(e)}')
            return redirect(url_for('index'))
        finally:
            # Geçici dosyayı güvenli şekilde temizle
            try:
                if os.path.exists(temp_input_path):
                    os.unlink(temp_input_path)
            except PermissionError:
                # Windows'ta dosya hala kullanımdaysa, biraz bekle ve tekrar dene
                time.sleep(0.1)
                try:
                    if os.path.exists(temp_input_path):
                        os.unlink(temp_input_path)
                except:
                    # Silinmezse sessizce geç, sistem otomatik temizleyecek
                    pass
    
    flash('Geçersiz dosya formatı!')
    return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
