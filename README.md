# Amazon Müşteri Deneyimi ve SSS Asistanı (Local RAG)

Merhaba! Ben bu projeyi, Amazon müşteri hizmetleri süreçlerini otomatize etmek, kullanıcılara Amazon ürünleri ve karmaşık iade/kargo politikaları hakkında saniyeler içinde doğru, eksiksiz ve yapay zeka destekli yanıtlar sunmak amacıyla geliştirdim. 

Bu asistanın en büyük özelliği; **tamamen yerel (offline) çalışması**, internetteki rastgele bilgileri **uydurmaması (halüsinasyon görmemesi)** ve tamamen benim hazırladığım RAG (Retrieval-Augmented Generation) mimarisiyle, kendi sağladığım gerçek dokümanlara dayanarak cevap vermesidir.

Aşağıda bu sistemi baştan sona nasıl tasarladığımı, hangi kütüphaneleri neden kullandığımı ve arka planda dönen tüm mühendislik detaylarını bulabilirsiniz.

---

## Projeyi Nasıl Kurguladım? (Mimari ve İşleyiş)

Sistemi birkaç farklı akıllı katmana böldüm. Kullanıcı Türkçe soru sorduğunda arka planda mükemmel bir orkestra çalışıyor:

### 1. Veri İşleme ve Parçalama (Chunking) Stratejim
Yapay zekanın uzun dokümanları sindirebilmesi için onları küçük parçalara bölmem gerekiyordu. Bunun için `app/chunk.py` ve `app/loader.py` dosyalarında iki farklı algoritma yazdım:
* **SSS ve Politikalar İçin:** Metinleri paragraflara ayırıp **700 karakterlik** parçalara böldüm. Ancak anlamın kopmaması için (Kayan Pencere / Sliding Window mantığıyla) parçaların birbirinin üstüne **150 karakter örtüşmesini (overlap)** sağladım.
* **Ürün Yorumları İçin:** Yorumların rastgele bölünmesi, "Hangi ürünün yorumu bu?" sorusunu doğuruyordu. Bunun önüne geçmek için harika bir mantık kurdum: Yorumları **650 karakterlik** gruplara böldüm ama yeni bir parçaya geçerken **en başa mutlaka Ürün İsmi ve ASIN Kodunu** otomatik olarak tekrar yazdırdım. Böylece yapay zeka parçaları bulduğunda hangi ürüne ait olduğunu asla karıştırmıyor.

### 2. Vektörleştirme (Embedding) Motoru
Metinleri yapay zekanın anlayabileceği sayılara (vektörlere) çevirmek için **Foundry Local SDK** üzerinden **Qwen3-Embedding-0.6B** modelini kullandım. Bu sayede verilerimi hiçbir bulut sunucuya göndermeden, tamamen yerel cihazımda devasa uzaysal koordinatlara dönüştürebildim.

### 3. Işık Hızında Vektör Veritabanı (SQLite + sqlite-vec)
Arama işlemlerini yapmak için Pinecone veya Milvus gibi ağır sunucu tabanlı veritabanları kurmak yerine, inanılmaz hafif ama çok güçlü olan **SQLite** ve onun C ile yazılmış **`sqlite-vec`** uzantısını projeye entegre ettim.
Kullanıcı soru sorduğunda, soru anında vektöre çevriliyor ve veritabanımdaki binlerce parça arasından (Kosinüs Benzerliği - Cosine Similarity matematiği ile) eşleşen dokümanlar milisaniyeler içinde bulunup getiriliyor.

### 4. Çeviri Katmanı (Real-time Translation Bridge)
Verilerim ve kullandığım LLM modeli (Qwen3) en verimli **İngilizce** çalışıyor. Ancak kullanıcılar soruları Türkçe soruyordu. Aradaki bu uçurumu kapatmak için **`deep-translator`** kütüphanesiyle dinamik bir köprü yazdım:
* Kullanıcının Türkçe sorusu anında İngilizceye çevrilip veritabanında aranıyor.
* En can alıcı nokta ise üretilen cevabın çevirisi: LLM cevabı kelime kelime (streaming) üretirken, araya yazdığım `translate_stream_en_to_tr` fonksiyonu sayesinde gelen kelimeler bir havuzda (buffer) toplanıyor. Sistem bir nokta (.), soru işareti (?) veya ünlem (!) görene kadar bekliyor; **tamamlanmış, mantıklı bir cümle elde ettiğinde** bunu Türkçeye çevirip ekrana öyle basıyor. (Böyle yapmasaydım yarım kelimeler çevrilip anlamsız cümleler çıkacaktı).

### 5. Beyin (Qwen3-1.7B ve RAG Orkestrası)
Bağlamdan kopmayan cevaplar üretmek için yine Foundry Local SDK üzerinden **Qwen3-1.7B** modelini entegre ettim. Sistemin zeki olmasını sağlayan yer, yazdığım **System Prompt** (Sistem Talimatları) kurallarıdır:
* Modele kesin bir dille *"Sadece bulduğum belgelere bak, kendi bilgini asla kullanma, bilmiyorsan bilmiyorum de"* kuralını koydum (Anti-Halüsinasyon).
* Ürün yorumları isteniyorsa; kullanıcının kararını kolaylaştırmak için modelin cümlenin sonuna *"Alınır mı: Evet/Hayır"* tavsiyesi ile birlikte otomatik olarak yıldız (⭐⭐⭐⭐) vermesini zorunlu kıldım.
* **Anti-Döngü Algoritması:** Küçük modellerin bazen takılıp aynı cümleyi sonsuza kadar tekrar etme huyu vardır. `rag.py` içerisine, her üretilen yeni cümleyi bir öncekiyle kıyaslayan ve tekrar başladığı an üretimi otomatik kesen özel bir güvenlik algoritması yazdım.
* **Akıllı Hafıza:** Sorulan son 1000 karakterlik geçmişi prompt'un içine gömerek modelin bağlamı ("peki iade süresi nedir?" sorusundaki ana objeyi) hatırlamasını sağladım.

### 6. RAM Dostu "Tembel Yükleme" (Lazy Loading)
Uygulama açılır açılmaz yapay zeka modelleri RAM'i doldurup bilgisayarı kilitlemesin diye özel bir Lazy Loading mimarisi kurdum. Modeller sadece kullanıcı **ilk sorusunu sorduğu anda** yüklenir ve sonraki sorularda RAM'de hazır beklediği için akıcı bir deneyim sunar.

### 7. Modern ve Akıcı Arayüz (Streamlit)
Kullanıcı deneyimini en üst seviyeye çıkarmak için **Streamlit** kullandım. Orijinal Amazon renklerine ve modern tasarım dillerine uygun, şık CSS kodları yazdım. Arayüze "Temel Sorular" ve "Ürün Hakkında" şeklinde filtreler koyarak arama performansını noktasal atışa çevirdim.

---

## Hangi Teknolojileri ve Verileri Kullandım?

*   **Python:** Projenin omurgası.
*   **Foundry Local SDK:** Yapay zeka modellerini cihazımda offline ve güvenli çalıştırmak için.
*   **Qwen3-1.7B:** Dil modelimiz (Metin üretimi).
*   **Qwen3-Embedding-0.6B:** Metinleri sayılara (vektörlere) dönüştüren modelimiz.
*   **sqlite3 & sqlite-vec:** Sunucusuz, hızlı vektör veritabanımız.
*   **streamlit:** Şık, modern sohbet arayüzü (UI).
*   **deep-translator:** Google Çeviri altyapısı ile anlık dil köprüsü.
*   **Kullandığım Veriler:** `data` klasörünün altında topladığım; Amazon'un resmi iade, teslimat ve kampanya politikaları (faq ve pdf dosyaları) ile Kaggle/Açık veri setlerinden toplanan gerçek, İngilizce Amazon ürün yorumları (`amazon_grouped_reviews.txt`).

---

## Nasıl Çalıştırılır?

1. Gerekli kütüphaneleri (eğer sisteminizde eksikse) kurun:
   ```bash
   pip install streamlit deep-translator
   ```
2. Foundry Local SDK'nın kurulu ve aktif olduğundan emin olun (Modellerin çalışması için zorunludur).
3. (Opsiyonel) İlk kurulumda metinleri vektör veritabanına işlemek için ingest scriptini çalıştırın:
   ```bash
   python ingest.py
   ```
4. Uygulamayı başlatın:
   ```bash
   streamlit run streamlit_app.py
   ```

Aylarca süren denemeler, küçük dil modellerinin kaprisleriyle boğuşmalar, kelime kelime çeviri senkronizasyonu dertleri derken, tamamen offline ortamda profesyonel bir Amazon temsilcisi kalitesinde cevap verebilen bu sistemi yazmak müthiş keyifliydi. Umarız denerken siz de benim kadar etkilenirsiniz! 🚀
