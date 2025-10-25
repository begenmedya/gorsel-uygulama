#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from main import create_visual
import os

def test_all_companies():
    """Tüm firma tiplerini test et"""
    
    # Test verileri
    test_image = "images/person1.jpg" if os.path.exists("images/person1.jpg") else "template.png"
    test_text = "Test Haberi: Yeni Firmalar Eklendi!"
    
    companies = [
        ("gazete", "Gazete İlkeni"),
        ("begen", "Begen Haber"), 
        ("begenmedya", "Begen Medya"),
        ("begenfilm", "Begen Film"),
        ("begentv", "Begen TV")
    ]
    
    print("=== Firma Test Başlıyor ===")
    
    for company_code, company_name in companies:
        print(f"\n🧪 Test ediliyor: {company_name} ({company_code})")
        
        output_file = f"test_output_{company_code}.png"
        
        try:
            result = create_visual(test_image, output_file, test_text, company_code)
            if result:
                print(f"✅ {company_name} - Başarılı!")
            else:
                print(f"❌ {company_name} - Başarısız!")
        except Exception as e:
            print(f"❌ {company_name} - Hata: {e}")
    
    print("\n=== Test Tamamlandı ===")

if __name__ == "__main__":
    test_all_companies()
