# Microsoft Staj Programı - Aşama 1: Yerel RAG Asistanı (Amazon Müşteri Deneyimi & SSS)

Selamlar! Ben Microsoft 40 Günlük Proje Tabanlı Staj Programı kapsamında 1. Aşama (Gün 1-20) görevimi tamamladım ve bu repoda geliştirdiğim projeyi paylaşıyorum. 

Projemi tasarlarken standart bir soru-cevap botu yapmak yerine, çok daha gerçekçi bir senaryo seçmek istedim. Bu yüzden "Amazon Müşteri Deneyimi ve SSS Asistanı" adı altında, kargo ve iade politikalarını bilen, aynı zamanda da gerçek müşteri ürün yorumlarını analiz edebilen bir RAG (Retrieval-Augmented Generation) sistemi kodladım.

Üstelik tüm bu sistem **tamamen yerel (offline)** çalışıyor. Dışarıdan hiçbir bulut servisine veya API'ye veri göndermiyoruz.

## 🛠 Neler Kullandım? Mimari Detaylar

Staj yönergesindeki gereksinimleri birebir karşılamak adına mimariyi şu şekilde kurguladım:

* **Microsoft Foundry Local:** Projenin kalbi burada atıyor. Hem yerel LLM (Qwen) çalıştırılması hem de metinlerin vektörlere (embedding) dönüştürülmesi için ana motor olarak bunu kullandım. 
* **RAG (Retrieval-Augmented Generation):** Asistanın kafasına göre bilgi uydurmasını engellemek için kurduğum ana yapı. Kullanıcı bir şey sorduğunda asistan kendi iç bilgisini kullanmıyor; önce veritabanındaki PDF dokümanlarını ve yorumları tarayıp, sadece bulduğu metinlere dayanarak cevap üretiyor.
* **SQLite:** Vektör veritabanı olarak çok ağır ve karmaşık çözümler yerine pratik ve hafif olan SQLite'ı tercih ettim. Parçalanan dokümanlar ve bunların vektör karşılıkları `Musteri_Deneyimi.db` dosyasında yerel olarak saklanıyor.
* **Streamlit:** "Orta Düzey Web Arayüzü (Seçenek B)" isterini karşılamak için arayüzü Streamlit ile yazdım. Konsepte uygun olsun diye de ufak bir Amazon teması kattım.

## ⚙️ Nasıl Çalıştırılır?

Projeyi kendi bilgisayarınızda ayağa kaldırmak oldukça basit:

1. Önce gerekli kütüphaneleri kurun:
```bash
pip install -r requirements.txt
```

2. Microsoft Foundry Local'in arka planda açık ve çalışır durumda olduğundan emin olun.

3. PDF'leri ve yorum metinlerini parçalayıp (chunking), vektörlere (embedding) çevirmek ve SQLite veritabanına kaydetmek için şu dosyayı çalıştırın:
```bash
python ingest.py
```

4. Veritabanımız hazır olduğuna göre asistanla konuşmaya başlayabiliriz:
```bash
streamlit run streamlit_app.py
```

## 🧠 Karşılaştığım Zorluklar ve Çözümlerim

Bu projeyi geliştirirken en çok vaktimi alan ve üzerine kafa yorduğum kısım **"İstem Mühendisliği (Prompt Engineering)"** ve **"Vektör Arama Optimizasyonu"** oldu. 

- **Halüsinasyonu (Uydurmayı) Engellemek:** Asistana dışarıdan bilgi getirmesini kesin bir dille yasakladım. Eğer sorulan soru veritabanında (örneğin Amazon SSS dosyasında) yoksa asistanın zorlanıp yalan söylemesi yerine **"Bunun hakkında bir bilgi bulunamadı"** diyerek dürüstçe reddetmesini sağladım.
- **Çapraz Dil (Cross-lingual) ve Benzerlik Bariyeri:** İngilizce yorumların içinde Türkçe arama yaptırdığım için, asistan bazen soyut kelimelerde (örneğin "tasarım") yorumları getirmekte zorlanıyordu. Başlangıçta cosine similarity (benzerlik oranı) sınırını 0.55 olarak belirlemiştim ancak bu çok katı olduğu için asistan yorumları bulamıyordu. Bu sınırı 0.40'a indirerek sistemin esnekliğini artırdım ve dolaylı yorumları bile yakalamasını sağladım.
- **Marka Karışıklığı:** Başta asistan, iPhone sorulduğunda gidip Canon kamerasının yorumlarını bulup uydurmaya çalışıyordu. Bunu çözmek için sistem talimatına (system prompt) çok katı bir "Marka eşleşmiyorsa kesinlikle cevap verme" kuralı ekleyerek prompt injection ve halüsinasyon riskini sıfırladım. Proje içine yazdığım `run_test_v2.py` isimli otomatik test script'i ile de bunu kanıtladım.

Okuduğunuz ve incelediğiniz için teşekkürler! Herhangi bir sorunuz olursa iletişime geçebilirsiniz.
