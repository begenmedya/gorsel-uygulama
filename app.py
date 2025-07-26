import sys
import time
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QLineEdit, QFileDialog, QVBoxLayout, QHBoxLayout, QMessageBox, QTextEdit, QRadioButton, QButtonGroup
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtCore import Qt
from main import create_visual
import os

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Görsel Oluşturucu")
        self.setGeometry(100, 100, 650, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial, sans-serif;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QLineEdit, QTextEdit {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #4CAF50;
            }
            QLabel {
                color: #333;
                font-size: 12px;
            }
        """)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # Başlık
        title_label = QLabel("Görsel Oluşturucu")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin-bottom: 20px;")
        layout.addWidget(title_label)

        # Görsel önizleme alanı
        self.img_label = QLabel("Görsel seçmek için 'Görsel Seç' butonuna tıklayın")
        self.img_label.setFixedHeight(200)
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet("""
            border: 2px dashed #bdc3c7;
            border-radius: 10px;
            background-color: white;
            color: #7f8c8d;
            font-size: 14px;
        """)
        layout.addWidget(self.img_label)

        # Görsel seçme butonu
        btn_select_img = QPushButton("📁 Görsel Seç")
        btn_select_img.clicked.connect(self.select_image)
        btn_select_img.setFixedHeight(45)
        layout.addWidget(btn_select_img)

        # Firma seçimi
        company_label = QLabel("Firma Seçin:")
        company_label.setStyleSheet("font-weight: bold; margin-top: 15px;")
        layout.addWidget(company_label)
        
        # Radio button grubu için horizontal layout
        company_layout = QHBoxLayout()
        company_layout.setSpacing(20)
        
        # Radio button grubu oluştur
        self.company_group = QButtonGroup()
        
        self.radio_gazete = QRadioButton("Gazete İlkeni")
        self.radio_gazete.setChecked(True)  # Varsayılan seçim
        self.radio_gazete.setStyleSheet("font-size: 14px; color: #2c3e50;")
        
        self.radio_begen = QRadioButton("Begen Haber")
        self.radio_begen.setStyleSheet("font-size: 14px; color: #2c3e50;")
        
        # Radio buttonları gruba ekle
        self.company_group.addButton(self.radio_gazete, 0)
        self.company_group.addButton(self.radio_begen, 1)
        
        # Layout'a ekle
        company_layout.addWidget(self.radio_gazete)
        company_layout.addWidget(self.radio_begen)
        company_layout.addStretch()  # Sağ tarafa boşluk ekle
        
        layout.addLayout(company_layout)

        # Metin girişi
        text_label = QLabel("Metninizi girin:")
        text_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(text_label)
        
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Görsel üzerine eklenecek metni buraya yazın...")
        self.text_input.setFixedHeight(80)
        layout.addWidget(self.text_input)

        # Oluşturma butonu
        btn_create = QPushButton("🎨 Görseli Oluştur")
        btn_create.clicked.connect(self.create_image)
        btn_create.setFixedHeight(50)
        btn_create.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        layout.addWidget(btn_create)

        # Durum etiketi
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold; margin-top: 10px;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.selected_img = None

    def select_image(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, 
            "Görsel Seç", 
            "", 
            "Görsel Dosyaları (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if fname:
            self.selected_img = fname
            pixmap = QPixmap(fname)
            scaled_pixmap = pixmap.scaled(
                self.img_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.img_label.setPixmap(scaled_pixmap)
            self.status_label.setText(f"Seçilen görsel: {os.path.basename(fname)}")
            self.status_label.setStyleSheet("color: #3498db; font-weight: bold;")

    def create_image(self):
        if not self.selected_img:
            QMessageBox.warning(self, "Uyarı", "Önce bir görsel seçmelisiniz!")
            return
            
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Uyarı", "Lütfen metin girin!")
            return
        
        # Firma tipini belirle
        company_type = "gazete" if self.radio_gazete.isChecked() else "begen"
            
        try:
            # Çıktı dosyasının konumunu belirle
            base_dir = os.path.dirname(self.selected_img)
            timestamp = int(time.time())
            output_filename = f"gorsel_output_{timestamp}.png"
            output_path = os.path.join(base_dir, output_filename)
            
            # Görseli oluştur (firma tipi ile)
            create_visual(self.selected_img, output_path, text, company_type)
            
            # Başarı mesajı
            self.status_label.setText(f"✅ Görsel başarıyla oluşturuldu!")
            self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            
            # Kullanıcıya dosyayı açma seçeneği sun
            reply = QMessageBox.question(
                self, 
                "Başarılı", 
                f"Görsel oluşturuldu!\n{output_path}\n\nDosyayı şimdi açmak ister misiniz?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                os.startfile(output_path)
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Görsel oluşturulurken hata: {str(e)}")
            self.status_label.setText("❌ Hata oluştu!")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
