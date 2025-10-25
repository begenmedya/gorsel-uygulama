from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
import os
import io
import base64
from werkzeug.utils import secure_filename
from main import create_visual
import tempfile
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import time
import requests
from io import BytesIO
import re
import uuid
from flask import send_from_directory
import shutil
import warnings
import logging

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Temp ve output klasörleri için /tmp kullan (Render.com için)
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/uploads')
OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER', '/tmp/outputs')

# Geçici klasörleri temizle ve yeniden oluştur
def setup_folders():
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception as e:
            warnings.warn(f"Klasör yönetimi hatası {folder}: {e}")

# Uygulama başlatıldığında çalışacak kod
def setup_app():
    try:
        # Asset dosyalarının varlığını kontrol et
        base_dir = os.path.dirname(os.path.abspath(__file__))
        required_files = [
            "Montserrat-Bold.ttf",
            "Montserrat-Regular.ttf",
            "template.png",
            "begentemplate.png",
            "logo.png",
            "BEGEN HABER.png"
        ]
        
        missing_files = []
        for file in required_files:
            file_path = os.path.join(base_dir, file)
            if not os.path.exists(file_path):
                missing_files.append(file)
        
        if missing_files:
            logger.warning(f"Gerekli dosyalar eksik: {', '.join(missing_files)}")
            
        # Geçici klasörleri temizle ve yeniden oluştur
        setup_folders()
        
    except Exception as e:
        logger.error(f"Uygulama başlatma hatası: {str(e)}")

# Uygulama başlatılırken setup'ı çalıştır
with app.app_context():
    setup_app()
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Font dosyasının yolu
FONT_PATH = os.path.join(os.path.dirname(__file__), "Montserrat-Bold.ttf")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def slugify(value):
    value = str(value)
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[-\s]+', '-', value)
    return value

def render_image(title, image_url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(image_url, headers=headers)
        print("IMAGE RESPONSE STATUS:", response.status_code)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
    except Exception as e:
        print("Görsel alınamadı veya okunamadı:", str(e))
        return jsonify({"error": f"Görsel alınamadı veya okunamadı: {str(e)}"}), 400
    image = img.convert("RGB")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("Montserrat-Bold.ttf", 36)
    except:
        font = ImageFont.load_default()
    draw.text((50, 50), title, font=font, fill="white")
    output_path = f"outputs/{slugify(title)}.jpg"
    image.save(output_path)
    print(f"Oluşturulan görsel: {output_path}")

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

@app.route('/outputs/<path:filename>')
def serve_file(filename):
    return send_from_directory('outputs', filename)

# Alternatif ve sorunsuz download endpoint
@app.route('/get-image/<filename>')
def get_generated_image(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename), mimetype='image/png')

@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json(force=True)
        title = data.get("title")
        image_url = data.get("image_url")
        brand = (data.get("brand") or "gazeteilke").lower()

        if not title or not image_url:
            return jsonify({"status": "error", "error": "Title ve image_url gerekli"}), 400

        # Firma tipini belirle
        company_type = "begen" if brand == "begenhaber" else "gazete"

        # Geçici dosyaları oluştur
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        temp_input_path = temp_input.name
        temp_input.close()

        # Görseli indir
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(image_url, headers=headers, timeout=10, verify=False)
            response.raise_for_status()
            
            # Görsel içeriğini kontrol et
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                raise ValueError(f"Geçersiz içerik türü: {content_type}")
            
            # Görseli kaydet
            with open(temp_input_path, 'wb') as f:
                f.write(response.content)
                
            # Görsel dosyasını kontrol et
            try:
                with Image.open(temp_input_path) as img:
                    img.verify()
            except Exception as e:
                raise ValueError(f"İndirilen dosya geçerli bir görsel değil: {str(e)}")
                
        except Exception as e:
            logger.error(f"Görsel indirme hatası: {str(e)}")
            if os.path.exists(temp_input_path):
                os.unlink(temp_input_path)
            return jsonify({"status": "error", "error": f"Görsel indirilemedi: {str(e)}"}), 400

        # Benzersiz çıktı dosyası adı oluştur
        filename = f"IMG_{int(time.time())}_{uuid.uuid4().hex[:8]}.png"
        output_path = os.path.join(OUTPUT_FOLDER, filename)

        try:
            # Önce dosyaların var olduğundan emin ol
            if not os.path.exists(temp_input_path):
                raise FileNotFoundError("Kaynak görsel bulunamadı")

            # Çıktı klasörünün var olduğundan emin ol
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # create_visual() fonksiyonunu kullan
            success = create_visual(temp_input_path, output_path, title, company_type)
            if not success:
                raise Exception("Görsel oluşturulamadı")

            # Çıktı dosyasının oluştuğunu kontrol et
            if not os.path.exists(output_path):
                raise FileNotFoundError("Çıktı dosyası oluşturulamadı")

            print("✅ Dosya kaydedildi:", output_path)
            return jsonify({
                "status": "ok",
                "file_path": f"/get-image/{filename}"
            })
        except Exception as e:
            print("❌ HATA:", str(e))
            return jsonify({"status": "error", "error": str(e)}), 500
        finally:
            # Geçici dosyaları temizle
            if os.path.exists(temp_input_path):
                try:
                    os.unlink(temp_input_path)
                except:
                    pass
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500
