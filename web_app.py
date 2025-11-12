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
            "begenmedyatemplate.png",
            "begenfilmtemplate.png",
            "begentvtemplate.png",
            "logo.png",
            "BEGEN HABER.png",
            "BEGEN MEDYA.png",
            "BEGEN FILM.png",
            "BEGEN TV.png"
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
        # Content-Type kontrolü
        if not request.is_json and not request.form:
            return jsonify({"status": "error", "error": "JSON veya form verisi gerekli"}), 400
            
        # JSON veya form verilerini al
        if request.is_json:
            data = request.get_json(force=True)
        else:
            data = request.form.to_dict()
            
        title = data.get("title", "").strip()
        image_url = data.get("image_url", "").strip()
        brand = (data.get("brand", "gazeteilke") or "gazeteilke").lower().strip()

        # Zorunlu alanları kontrol et
        if not title:
            return jsonify({"status": "error", "error": "Title alanı gerekli ve boş olamaz"}), 400
        if not image_url:
            return jsonify({"status": "error", "error": "image_url alanı gerekli ve boş olamaz"}), 400

        # URL formatını kontrol et
        if not image_url.startswith(('http://', 'https://')):
            return jsonify({"status": "error", "error": "Geçersiz image_url formatı. http:// veya https:// ile başlamalı"}), 400

        # Firma tipini belirle
        company_type_map = {
            "begenhaber": "begen",
            "begen": "begen", 
            "begenmedya": "begenmedya",
            "begenfilm": "begenfilm", 
            "begentv": "begentv",
            "gazeteilke": "gazete",
            "gazete": "gazete"
        }
        company_type = company_type_map.get(brand, "gazete")
        
        print(f"📝 İstek detayları: title='{title}', brand='{brand}', company_type='{company_type}'")
        print(f"🖼 Image URL: {image_url}")

        # Geçici dosyaları oluştur
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_input_path = temp_input.name
        temp_input.close()

        print(f"📂 Geçici dosya: {temp_input_path}")

        # Görseli indir
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"
        }
        
        try:
            print("🔽 Görsel indiriliyor...")
            response = requests.get(image_url, headers=headers, timeout=30, verify=False, stream=True)
            print(f"📡 HTTP Status: {response.status_code}")
            response.raise_for_status()
            
            # Content-Type kontrolü
            content_type = response.headers.get('content-type', '').lower()
            print(f"📋 Content-Type: {content_type}")
            
            if not any(img_type in content_type for img_type in ['image/', 'jpeg', 'png', 'gif', 'bmp', 'webp']):
                raise ValueError(f"Geçersiz içerik türü: {content_type}")
            
            # Görsel içeriğini kaydet
            with open(temp_input_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            print(f"💾 Görsel kaydedildi: {os.path.getsize(temp_input_path)} bytes")
                
            # Görsel dosyasını doğrula
            try:
                with Image.open(temp_input_path) as img:
                    img.verify()
                print("✅ Görsel doğrulandı")
            except Exception as e:
                raise ValueError(f"İndirilen dosya geçerli bir görsel değil: {str(e)}")
                
        except requests.exceptions.Timeout:
            logger.error("Görsel indirme timeout hatası")
            if os.path.exists(temp_input_path):
                os.unlink(temp_input_path)
            return jsonify({"status": "error", "error": "Görsel indirme zaman aşımına uğradı (30 saniye)"}), 408
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Görsel indirme hatası: {str(e)}")
            if os.path.exists(temp_input_path):
                os.unlink(temp_input_path)
            return jsonify({"status": "error", "error": f"Görsel indirilemedi: {str(e)}"}), 400
            
        except Exception as e:
            logger.error(f"Genel görsel indirme hatası: {str(e)}")
            if os.path.exists(temp_input_path):
                os.unlink(temp_input_path)
            return jsonify({"status": "error", "error": f"Görsel işleme hatası: {str(e)}"}), 400

        # Benzersiz çıktı dosyası adı oluştur
        safe_title = re.sub(r'[^\w\s-]', '', title)[:50]  # İlk 50 karakter, güvenli karakterler
        timestamp = int(time.time())
        random_id = uuid.uuid4().hex[:8]
        filename = f"IMG_{timestamp}_{random_id}.png"
        output_path = os.path.join(OUTPUT_FOLDER, filename)
        
        print(f"📁 Çıktı dosyası: {output_path}")

        try:
            # Önce dosyaların var olduğundan emin ol
            if not os.path.exists(temp_input_path):
                raise FileNotFoundError("Kaynak görsel dosyası bulunamadı")

            # Çıktı klasörünün var olduğundan emin ol
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            print("🎨 Görsel oluşturuluyor...")
            # create_visual() fonksiyonunu kullan
            success = create_visual(temp_input_path, output_path, title, company_type)
            if not success:
                raise Exception("create_visual fonksiyonu False döndü")

            # Çıktı dosyasının oluştuğunu kontrol et
            if not os.path.exists(output_path):
                raise FileNotFoundError("Çıktı dosyası oluşturulamadı")
                
            # Dosya boyutunu kontrol et
            file_size = os.path.getsize(output_path)
            if file_size == 0:
                raise Exception("Oluşturulan dosya boş")

            print(f"✅ Dosya başarıyla oluşturuldu: {output_path} ({file_size} bytes)")
            
            # Tam URL'yi oluştur (Instagram için)
            base_url = request.url_root.rstrip('/')
            full_image_url = f"{base_url}/get-image/{filename}"
            
            return jsonify({
                "status": "ok",
                "message": "Görsel başarıyla oluşturuldu",
                "file_path": f"/get-image/{filename}",
                "image_url": full_image_url,  # Instagram için tam URL
                "filename": filename,
                "file_size": file_size
            })
            
        except Exception as e:
            error_msg = f"Görsel oluşturma hatası: {str(e)}"
            print(f"❌ HATA: {error_msg}")
            logger.error(error_msg)
            return jsonify({"status": "error", "error": error_msg}), 500
            
        finally:
            # Geçici dosyaları temizle
            if os.path.exists(temp_input_path):
                try:
                    os.unlink(temp_input_path)
                    print("🗑 Geçici dosya temizlendi")
                except Exception as e:
                    print(f"⚠ Geçici dosya silinemedi: {e}")
                    
    except Exception as e:
        error_msg = f"Beklenmeyen hata: {str(e)}"
        print(f"💥 KRITIK HATA: {error_msg}")
        logger.error(error_msg)
        return jsonify({"status": "error", "error": error_msg}), 500

# Debug ve sağlık kontrol endpoint'leri
@app.route('/health', methods=['GET'])
def health_check():
    """API'nin çalışır durumda olduğunu kontrol eden endpoint"""
    return jsonify({
        "status": "ok", 
        "message": "API çalışıyor",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/test-files', methods=['GET'])
def test_files():
    """Gerekli dosyaların varlığını kontrol eden endpoint"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    required_files = [
        "Montserrat-Bold.ttf",
        "Montserrat-Regular.ttf", 
        "template.png",
        "begentemplate.png",
        "begenmedyatemplate.png",
        "begenfilmtemplate.png", 
        "begentvtemplate.png",
        "logo.png",
        "BEGEN HABER.png",
        "BEGEN MEDYA.png",
        "BEGEN FILM.png",
        "BEGEN TV.png"
    ]
    
    file_status = {}
    all_exists = True
    
    for file in required_files:
        file_path = os.path.join(base_dir, file)
        exists = os.path.exists(file_path)
        file_status[file] = {
            "exists": exists,
            "path": file_path,
            "size": os.path.getsize(file_path) if exists else 0
        }
        if not exists:
            all_exists = False
    
    return jsonify({
        "status": "ok" if all_exists else "warning",
        "all_files_exist": all_exists,
        "files": file_status,
        "base_directory": base_dir
    })

@app.route('/debug-generate', methods=['POST'])
def debug_generate():
    """Debug için detaylı log içeren generate endpoint'i"""
    debug_info = []
    
    try:
        debug_info.append("🔍 Debug generate başlatıldı")
        
        # Request analizi
        debug_info.append(f"Content-Type: {request.content_type}")
        debug_info.append(f"Method: {request.method}")
        debug_info.append(f"Headers: {dict(request.headers)}")
        debug_info.append(f"URL Root: {request.url_root}")
        
        if request.is_json:
            data = request.get_json(force=True)
            debug_info.append(f"JSON data: {data}")
        else:
            data = request.form.to_dict()
            debug_info.append(f"Form data: {data}")
            
        # Gerekli alanları kontrol et
        title = data.get("title", "").strip()
        image_url = data.get("image_url", "").strip() 
        brand = (data.get("brand", "gazeteilke") or "gazeteilke").lower().strip()
        
        debug_info.append(f"Parsed - title: '{title}', image_url: '{image_url}', brand: '{brand}'")
        
        # Instagram için örnek response
        base_url = request.url_root.rstrip('/')
        sample_response = {
            "status": "ok",
            "message": "Görsel başarıyla oluşturuldu",
            "file_path": f"/get-image/sample_filename.png",
            "image_url": f"{base_url}/get-image/sample_filename.png", # Instagram için tam URL
            "filename": "sample_filename.png",
            "file_size": 1234567
        }
        
        return jsonify({
            "status": "debug",
            "debug_info": debug_info,
            "parsed_data": {
                "title": title,
                "image_url": image_url,
                "brand": brand
            },
            "sample_success_response": sample_response
        })
        
    except Exception as e:
        debug_info.append(f"❌ Debug hatası: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "debug_info": debug_info
        }), 500

if __name__ == '__main__':
    # Geliştirme ortamında çalıştırmak için
    app.run(host='0.0.0.0', port=5000, debug=True)
