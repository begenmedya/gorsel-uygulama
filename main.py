from PIL import Image, ImageDraw, ImageFont
import os

def create_visual(person_i            font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue
        
        if font is None:
            font = ImageFont.load_default(), output_path, name_text, company_type="gazete"):
    try:
        # Firma tipine göre şablon ve logo dosyalarını seç
        if company_type == "begen":
            template_path = os.path.join(os.path.dirname(__file__), "begentemplate.png")
            logo_path = os.path.join(os.path.dirname(__file__), "BEGEN HABER.png")
        else:  # varsayılan gazete
            template_path = os.path.join(os.path.dirname(__file__), "template.png")
            logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        
        # Görüntüleri güvenli şekilde aç
        with Image.open(template_path) as template_img:
            template = template_img.convert("RGBA")
        with Image.open(logo_path) as logo_img:
            logo = logo_img.convert("RGBA")
        with Image.open(person_image_path) as person_img_file:
            person_img = person_img_file.convert("RGBA")

        # Şablon boyutlarını al
        template_width, template_height = template.size
        print(f"Şablon boyutu: {template_width}x{template_height}")

        # Kişi fotoğrafını daha büyük bir alana yerleştir
        target_width = 1200  # Hedef genişlik arttırıldı
        target_height = 1000  # Hedef yükseklik arttırıldı
        
        # En-boy oranını koru
        width_ratio = target_width / person_img.width
        height_ratio = target_height / person_img.height
        ratio = min(width_ratio, height_ratio)
        
        # Yeni boyutları hesapla
        new_width = int(person_img.width * ratio)
        new_height = int(person_img.height * ratio)
        
        # Görseli yeniden boyutlandır
        person_img = person_img.resize((new_width, new_height), Image.LANCZOS)
        
        # Görseli konumlandır (biraz daha yukarı)
        paste_x = 50  # Sol kenardan başla
        paste_y = 600  # Üstten başlangıç noktası (yukarı çekildi)
        
        template.paste(person_img, (paste_x, paste_y), person_img)

        # Logo ekle (sağ alt köşe)
        # Logo'yu uygun boyuta getir
        logo_max_size = 300  # Maksimum logo boyutu
        logo_width, logo_height = logo.size
        
        # Logo'yu orantılı olarak küçült
        if logo_width > logo_max_size or logo_height > logo_max_size:
            ratio = min(logo_max_size / logo_width, logo_max_size / logo_height)
            new_width = int(logo_width * ratio)
            new_height = int(logo_height * ratio)
            logo = logo.resize((new_width, new_height), Image.LANCZOS)
            logo_width, logo_height = new_width, new_height
        
        logo_x = template_width - logo_width - 40  # 10px sağdan boşluk
        logo_y = template_height - logo_height - 0  # 0px alttan boşluk
        template.paste(logo, (logo_x, logo_y), logo)
        print(f"Logo eklendi: ({logo_x}, {logo_y}) konumuna, boyut: {logo_width}x{logo_height}")

        # Metin ekle
        draw = ImageDraw.Draw(template)
        
        # Montserrat Bold font kullan
        font_size = 72
        font = None
        font_paths = [
            os.path.join(os.path.dirname(__file__), "Montserrat-Bold.ttf"),    # Aynı klasördeki Montserrat Bold
            os.path.join(os.path.dirname(__file__), "Montserrat-Regular.ttf"), # Yedek Montserrat Regular
            "C:/Windows/Fonts/arialbd.ttf",   # Arial Bold
            "C:/Windows/Fonts/calibrib.ttf",  # Calibri Bold
            "C:/Windows/Fonts/arial.ttf",     # Arial Regular
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
            "/System/Library/Fonts/Arial.ttf",  # macOS
            "arial.ttf"
        ]
        
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, font_size)
                print(f"Font yüklendi: {font_path}")
                break
            except:
                continue
        
        if font is None:
            font = ImageFont.load_default()
            print("Varsayılan font kullanılıyor")
        
        # Metin alanı tanımla (şablonun SAĞ ÜST kısmındaki mor alan)
        text_area = {
            'x': 550,          # Sağ boşluğu artır
            'y': 0,           # Daha yukarıdan başla
            'width': 700,      # Genişliği azalt (kenarlardan daha fazla boşluk)
            'height': 700      # Mor kutunun yüksekliği
        }
        
        # Font boyutunu metin uzunluğuna göre hızlı bir şekilde ayarla
        text_len = len(name_text)
        if text_len > 100:
            font_size = 40
        elif text_len > 50:
            font_size = 50
        else:
            font_size = 72

        font = ImageFont.truetype(font_paths[0], font_size)
        test_lines = wrap_text(name_text, font, text_area['width'], draw)
        
        # Eğer metin sığmazsa, font boyutunu azalt
        while len(test_lines) * (font_size + 6) > text_area['height'] and font_size > 30:
            font_size -= 5
            font = ImageFont.truetype(font_paths[0], font_size)
            test_lines = wrap_text(name_text, font, text_area['width'], draw)
        
        line_height = font_size + 6  # Satır arası boşluk
        lines = test_lines  # Zaten hesapladığımız satırları kullan
        
        print(f"Metin {len(lines)} satıra bölündü")
        
        # Her satırı merkeze hizala ve yaz
        total_text_height = len(lines) * line_height
        start_y = text_area['y'] + (text_area['height'] - total_text_height) // 2  # Tam ortada
        
        for i, line in enumerate(lines):
            y_position = start_y + (i * line_height)
            
            # Satırı merkeze hizala
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x_position = text_area['x'] + (text_area['width'] - text_width) // 2
            
            # Gölge efekti (daha yumuşak)
            draw.text((x_position + 2, y_position + 2), line, font=font, fill=(0, 0, 0, 180))
            # Ana metin (beyaz)
            draw.text((x_position, y_position), line, font=font, fill="white")
            
            print(f"Satır yazıldı: '{line}' konumda ({x_position}, {y_position})")

        # Sonucu kaydet
        template.save(output_path)
        print(f"Görsel başarıyla oluşturuldu: {output_path}")
        return True
        
    except Exception as e:
        print(f"Hata: {e}")
        return False

def wrap_text(text, font, max_width, draw):
    """Metni belirtilen genişliğe göre satırlara böl"""
    lines = []
    
    # Önce manuel satır geçişlerini kontrol et
    paragraphs = text.split('\n')
    
    for paragraph in paragraphs:
        words = paragraph.split(' ')
        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]
            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    # Tek kelime çok uzunsa, belirli aralıklarla böl
                    temp_word = word
                    while temp_word:
                        for i in range(1, len(temp_word)+1):
                            part = temp_word[:i]
                            bbox = draw.textbbox((0, 0), part, font=font)
                            part_width = bbox[2] - bbox[0]
                            if part_width > max_width:
                                if i == 1:
                                    # Harf bile sığmıyorsa
                                    lines.append(part)
                                    temp_word = temp_word[i:]
                                else:
                                    lines.append(temp_word[:i-1])
                                    temp_word = temp_word[i-1:]
                                break
                        else:
                            lines.append(temp_word)
                            temp_word = ""
                    current_line = ""
        if current_line:
            lines.append(current_line)
    return lines

# Kullanım örneği
if __name__ == "__main__":
    print("=== Görsel Oluşturucu ===")
    print("Lütfen firma tipini seçin:")
    print("1. Gazete İlkeni")
    print("2. Begen Haber")
    
    while True:
        choice = input("Seçiminizi yapın (1 veya 2): ").strip()
        if choice == "1":
            company_type = "gazete"
            print("Gazete İlkeni seçildi.")
            break
        elif choice == "2":
            company_type = "begen"
            print("Begen Haber seçildi.")
            break
        else:
            print("Geçersiz seçim! Lütfen 1 veya 2 girin.")
    
    # Görsel oluştur
    create_visual("images/person1.jpg", "output1.png", "Belçika Savunma Bakanı Francken'den Atatürk'e Övgü: 'Büyük Bir Devlet Adamıydı'", company_type)