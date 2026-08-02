# Amazon Müşteri Deneyimi ve SSS Asistanı (Local RAG)

## Proje Hakkında
Bu uygulamada bir "Amazon Müşteri Deneyimi ve SSS Asistanı" tasarlanmıştır. Asistan, müşteri hizmetleri politikalarını ve ürün yorumlarını (PDF belgelerinden okuyarak) analiz edip soruları yanıtlar. Tamamen çevrimdışı ve gizlilik odaklı çalışır.

Amazon gibi devasa ürün kataloglarına sahip platformlardaki müşteri hizmetleri süreçlerini otomatize etmek; kullanıcılara karmaşık iade/kargo politikaları ve binlerce ürün yorumu hakkında saniyeler içinde doğru, eksiksiz ve yapay zeka destekli yanıtlar sunmak amacıyla geliştirdim. 

Bu asistanın en büyük özelliği; **offline çalışması**, bilgileri rastgele **uydurmaması (halüsinasyon görmemesi)** ve tamamen benim hazırladığım RAG (Retrieval-Augmented Generation) mimarisiyle, kendi sağladığım gerçek dokümanlara dayanarak cevap vermesidir.

Aşağıda bu sistemi baştan sona nasıl tasarladığımı, verisetlerini nasıl hazırladığımı, hangi kütüphaneleri neden kullandığımı ve arka planda dönen tüm detayları bulabilirsiniz.

---

## Veri Seti Hazırlığı: Verileri Nereden Buldum ve Nasıl İşledim?

Bu projenin zekası, beslediğim verilerden geliyor. Veri setimi iki ana kategoriye ayırdım ve sisteme özel bir şekilde hazırladım:

### 1. Amazon Politikaları ve SSS Verileri
Kullanıcıların iade, kargo, Prime abonelik gibi süreçlerdeki sorularına doğru yanıt verebilmek için doğrudan Amazon'un resmi yardım sayfalarını (Customer Service, Return Policies vb.) kaynak aldım. Bu sayfaları PDF formatına dönüştürüp `data/faq/` klasörüne yerleştirdim. Böylece asistan uydurma bilgiler yerine, tamamen resmi metinleri okuyup analiz ederek müşterilere nokta atışı yönergeler sunabiliyor.

### 2. Gerçek Kullanıcı Yorumları Veri Seti
Kullanıcıların "Bu kamera alınır mı?", "Bu hoparlörün sesi nasıl?" gibi spesifik ürün sorularına cevap verebilmek için gerçek incelemelere ihtiyacım vardı. Bunun için **Amazon Açık Veri Platformundan**  Amazon'un İngilizce ürün yorumları (Product Reviews) veri setlerini buldum. Ancak bu ham veriyi doğrudan sisteme vermek işe yaramayacaktı:
*   Verileri temizleyip, sadece en popüler ve detaylı yorumları filtreledim.
*   Her bir yorumu ait olduğu ürün ismi (Title) ve ASIN (Amazon Standard Identification Number) koduyla grupladım.
*   Bu sayede `data/amazon_grouped_reviews.txt` adlı tertemiz, yapılandırılmış bir veri dosyası elde ettim.

---

## Projeyi Nasıl Kurguladım? (Mimari ve İşleyiş)

### 1. Veri İşleme ve Parçalama (Chunking) Stratejim
Yapay zekanın uzun dokümanları sindirebilmesi için onları küçük parçalara bölmem gerekiyordu.`app/chunk.py` ve `app/loader.py` dosyalarında iki farklı algoritma yazdım:
* **SSS ve Politikalar İçin:** Metinleri paragraflara ayırıp **700 karakterlik** parçalara böldüm. Ancak anlamın kopmaması için (Kayan Pencere / Sliding Window mantığıyla) parçaların birbirinin üstüne **150 karakter örtüşmesini (overlap)** sağladım.
* **Ürün Yorumları İçin:** Yorumların rastgele bölünmesi, "Hangi ürünün yorumu bu?" sorusunu doğuruyordu. Bunun önüne geçmek için şu mantığı kurdum: Yorumları **650 karakterlik** gruplara böldüm ama yeni bir parçaya geçerken **en başa mutlaka Ürün İsmi ve ASIN Kodunu**  tekrar yazdırdım. Böylece yapay zeka parçaları bulduğunda hangi ürüne ait olduğunu asla karıştırmıyor.

### 2. Vektörleştirme (Embedding) Motoru
Metinleri yapay zekanın anlayabileceği sayılara (vektörlere) çevirmek için **Foundry Local SDK** üzerinden **Qwen3-Embedding-0.6B** modelini kullandım. Bu sayede verilerimi hiçbir bulut sunucuya göndermeden, tamamen yerel cihazımda devasa uzaysal koordinatlara dönüştürebildim.

### 3.Veritabanı (SQLite + sqlite-vec)
**SQLite** ve onun C ile yazılmış **`sqlite-vec`** uzantısını projeye entegre ettim.
Kullanıcı soru sorduğunda, soru anında vektöre çevriliyor ve veritabanımdaki binlerce parça arasından (Kosinüs Benzerliği - Cosine Similarity matematiği ile) eşleşen dokümanlar milisaniyeler içinde bulunup getiriliyor.

### 4. Çeviri Katmanı (Real-time Translation Bridge)
Verilerim ve kullandığım LLM modeli (Qwen3) en verimli **İngilizce** çalışıyor. Ancak kullanıcılar soruları Türkçe soruyordu. Aradaki bu durumu kapatmak için **`deep-translator`** kütüphanesiyle dinamik bir köprü yazdım:
* Kullanıcının Türkçe sorusu anında İngilizceye çevrilip veritabanında aranıyor.
* En can alıcı nokta ise üretilen cevabın çevirisi: LLM cevabı kelime kelime (streaming) üretirken, araya yazdığım `translate_stream_en_to_tr` fonksiyonu sayesinde gelen kelimeler bir havuzda (buffer) toplanıyor. Sistem bir nokta (.), soru işareti (?) veya ünlem (!) görene kadar bekliyor; **tamamlanmış, mantıklı bir cümle elde ettiğinde** bunu Türkçeye çevirip ekrana öyle basıyor.

### 5. Beyin (Qwen3-1.7B ve RAG Orkestrası)
Bağlamdan kopmayan cevaplar üretmek için yine Foundry Local SDK üzerinden **Qwen3-1.7B** modelini entegre ettim. Sistemin zeki olmasını sağlayan yer, yazdığım **System Prompt** (Sistem Talimatları) kurallarıdır:
* Modele kesin bir dille *"Sadece bulduğum belgelere bak, kendi bilgini asla kullanma, bilmiyorsan bilmiyorum de"* kuralını koydum (Anti-Halüsinasyon).
* Ürün yorumları isteniyorsa; kullanıcının kararını kolaylaştırmak için modelin cümlenin sonuna *"Alınır mı: Evet/Hayır"* tavsiyesi ile birlikte otomatik olarak yıldız puanı vermesini zorunlu kıldım.
*Kullanıcının sisteme sorduğu soru tipine göre belirli sistem promptuyla çalışmasını sağladım.
### 6. RAM Dostu "Tembel Yükleme" (Lazy Loading)
Uygulama açılır açılmaz yapay zeka modelleri RAM'i doldurup bilgisayarı kilitlemesin diye modeller sadece kullanıcı ilk sorusunu sorduğu anda yüklenir ve sonraki sorularda RAM'de hazır beklediği için akıcı bir deneyim sunar.

### 7. Modern Arayüz (Streamlit)
Kullanıcı deneyimini en üst seviyeye çıkarmak için **Streamlit** kullandım. Orijinal Amazon renklerine ve modern tasarım dillerine uygun, şık CSS kodları yazdım. Arayüze "Temel Sorular" ve "Ürün Hakkında" şeklinde filtreler koyarak arama performansını noktasal atışa çevirdim.

---

## Hangi Teknolojileri Kullandım?

*   **Python:**
*   **Foundry Local SDK:** Yapay zeka modellerini cihazımda offline ve güvenli çalıştırmak için.
*   **Qwen3-1.7B:** Dil modelim
*   **Qwen3-Embedding-0.6B:** Metinleri sayılara (vektörlere) dönüştüren modelim.
*   **sqlite3 & sqlite-vec:** Sunucusuz, hızlı vektör veritabanı.
*   **streamlit:** Şık, modern sohbet arayüzü (UI).
*   **deep-translator:** Google Çeviri altyapısı ile anlık dil köprüsü.

---

## Nasıl Çalıştırılır? (Kurulum)

1. Gerekli kütüphaneleri (eğer sisteminizde eksikse) kurun:
   ```bash
   pip install -r requirements.txt
   ```
2. Foundry Local SDK'nın kurulu ve aktif olduğundan emin olun (Modellerin çalışması için zorunludur).
3. (Opsiyonel) İlk kurulumda verisetindeki metinleri (PDF ve TXT'leri) vektör veritabanına işlemek için ingest scriptini çalıştırın. Bu sayede `database` klasörü dolacaktır:
   ```bash
   python ingest.py
   ```
4. Uygulamayı başlatın:
   ```bash
   streamlit run streamlit_app.py
   ```

