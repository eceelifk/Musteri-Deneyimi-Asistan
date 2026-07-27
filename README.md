# Amazon Müşteri Deneyimi ve SSS Asistanı (Local RAG)

Merhaba! Bu projede, müşteri hizmetleri süreçlerini otomatize etmek ve kullanıcılara Amazon ürünleri hakkında yapay zeka destekli, hızlı ve doğru yanıtlar sunmak için **RAG (Retrieval-Augmented Generation)** tabanlı yerel bir yapay zeka asistanı geliştirdim. 

Amacım; hem ürün yorumlarını analiz edip özetleyen hem de Amazon'un iade, kargo, Prime gibi karmaşık politikalarına anında cevap verebilen akıllı bir destek botu oluşturmaktı. Üstelik tüm bunları internetteki rastgele bilgileri uydurmadan, sadece kendi veritabanımızdaki gerçek verileri kullanarak yaptık!

## Neler Yaptım? Hangi Özellikleri Ekledim?

1. **RAG (Retrieval-Augmented Generation) Altyapısı:** 
   Modelin halüsinasyon görmesini (bilgi uydurmasını) engellemek için, sorulan soruya önce kendi veritabanımızdan cevap arayan bir yapı kurdum. Sistem sadece bulduğu belgeleri kullanarak cevap üretiyor, bilgi yoksa "Bilmiyorum" diyerek dürüstçe reddediyor.
2. **Çeviri Katmanı (Translation Layer):** 
   Veritabanımızdaki ürün yorumları ve Amazon politikaları orijinal dili olan **İngilizce**'ydi. Ancak kullanıcılar Türkçe soru soruyor. Araya `deep-translator` ile bir katman yazdım: Türkçe soru -> İngilizce arama -> İngilizce YZ cevabı -> Türkçe çıktı şeklinde kusursuz ve gerçek zamanlı bir köprü kurdum.
3. **Akıllı Hafıza (Context Memory):** 
   Kullanıcının bir önceki sorusunu hatırlayarak bağlamdan kopmayan bir hafıza sistemi entegre ettim. Böylece sohbette "peki iade süresi nedir?" dendiğinde neyden bahsedildiğini anlıyor.
4. **Anti-Döngü (Loop Detection) Algoritması:** 
   Küçük parametreli yerel modellerin kronik sorunu olan "aynı kelimeleri / paragrafları tekrar etme" sorununu çözmek için özel bir algoritma yazdım. Model kendini tekrar etmeye başladığı an (100 kelimeye kadar), bunu fark edip üretimi anında kesiyor.
5. **Modern ve Hızlı Arayüz (UI):** 
   Streamlit kullanarak Amazon'un orijinal renk ve fontlarına benzeyen, şık, temiz ve "Sohbeti Temizle" özellikli modern bir chat arayüzü tasarladım.
6. **Gerçek Zamanlı Akış (Streaming):** 
   Cevabın tamamlanmasını beklemeden, kelime kelime ekrana dökülmesini sağlayan Streaming yapısını kurdum.
7. **Performans ve Hız Optimizasyonu:** 
   Veri getirme sayısını (`TOP_K`) optimize ederek ve promptları sadeleştirerek modelin tepki süresini saniyelere indirdim.
8. **Test Otomasyonu:** 
   `run_test_v3.py` isimli bir script ile 20 farklı zorlayıcı soru (yorum, SSS ve uydurma tuzak sorular) hazırlayarak sistemin %100 doğrulukla çalıştığını kanıtladım.

## Hangi Teknolojileri ve Kütüphaneleri Kullandım?

* **Python:** Projenin ana omurgası.
* **Streamlit (`streamlit`):** Modern, hızlı ve etkileşimli web arayüzünü oluşturmak için.
* **Qdrant (`qdrant-client`):** Belgelerimizi semantik (anlamsal) olarak arayabildiğimiz, inanılmaz hızlı yerel vektör veritabanımız.
* **Foundry Local SDK:** Yapay zeka modellerini bilgisayarda yerel (offline) olarak çalıştırmak için kullandığım altyapı.
* **Qwen3-1.7B Modeli:** Çok hafif ama mantık yürütme kabiliyeti yüksek olan yerel LLM (Büyük Dil Modeli) motorumuz.
* **Qwen3-Embedding-0.6B:** Metinleri vektörlere (sayılara) çevirip veritabanına kaydetmemizi ve benzerlik araması yapmamızı sağlayan embedding modeli.
* **Deep Translator (`deep-translator`):** Araya koyduğum gerçek zamanlı İngilizce-Türkçe çeviri motoru (Google Translator altyapısı).

## Verileri Nereden Bulduk?

Sistemi eğitmek (daha doğrusu veritabanına eklemek) için gerçek ve güvenilir veriler kullanmam gerekiyordu:
1. **Ürün Yorumları (`amazon_grouped_reviews.txt`):** İnternetteki açık kaynaklı Amazon Müşteri İncelemeleri veri setlerinden (örneğin Kaggle'daki Amazon Customer Reviews dataset) derlediğimiz gerçek İngilizce müşteri yorumları. (Örn: Canon fotoğraf makineleri, Philips hoparlörler, kitaplar vb.)
2. **SSS ve Politikalar (`amazon_faq.txt`, `amazon_policies.txt`, `amazon_prime.txt` vb.):** Amazon'un kendi resmi yardım sayfalarından, iade politikalarından ve Prime sözleşmelerinden alınmış gerçek metin dosyaları.

## Nasıl Çalıştırılır?

1. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install streamlit qdrant-client deep-translator
   ```
2. Foundry Local SDK'nın kurulu ve aktif olduğundan emin olun.
3. İlk kurulumda verileri vektör veritabanına işlemek için ingest scriptini (eğer ayrıysa) çalıştırın.
4. Arayüzü başlatmak için:
   ```bash
   streamlit run streamlit_app.py
   ```

Geliştirme sürecinde küçük modellerin kaprislerinden UI tasarımlarına kadar birçok zorlukla karşılaştım ama sonunda ortaya %100 başarı oranına sahip, tamamen yerel çalışan harika bir asistan çıktı! Umarız denerken siz de benim kadar keyif alırsınız.
