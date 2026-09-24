# SFDA AI Kontrol Ajanı — Nihai Detaylı Plan (kullanıcı tarafından sağlandı)

> Bu plan kullanıcının kendi tasarımıdır. Mühendislik seviyesinde uygulanabilir olmak üzere yazılmıştır.
> Kaydedilme tarihi: 2026-09-24

---

## 1. Genel Mimari ve Katmanlı Yaklaşım

Dört ana katman:

| Katman | Görev | Çıktı |
|---|---|---|
| **Katman 1: Doküman Alım ve Standartlaştırma** | Yüklenen dokümanları OCR/parse eder, yapısal JSON'a çevirir, metadata çıkarır | Standart chunk'lar |
| **Katman 2: Sabit Vektör ve Retrieval** | Chunk'ları sabit embedding modeliyle vektörleştirir, koleksiyonlara ayırır, hibrit retrieval yapar | İlgili chunk'lar |
| **Katman 3: Deterministik Ajan Grafiği** | State machine tarafından yönetilen sabit ajan rolleri | Sınıflandırma, doğrulama, checklist |
| **Katman 4: Arayüz ve Yerel Kayıt** | Web arayüzü, Excel loglama, süreç takibi | Kullanıcı etkileşimi, denetim izi |

## 2. Sabit Ajan Grafiği (Background Agentization)

LLM ajan seçmez. State machine neyi söylerse o ajan çalışır. Ajan rolleri, girdi/çıktıları ve geçiş koşulları YAML'da sabittir.

### Ajan Rolleri

| Ajan | Görev | Girdi | Çıktı | Model Tipi |
|---|---|---|---|---|
| **Orchestrator** | Durum makinesini yönetir, kullanıcıya mesaj üretir | State, Context Packet | Sonraki state, kullanıcı mesajı | Güçlü model (opsiyonel) |
| **Ingest Agent** | Dokümanı OCR/parse eder, chunk'lar, metadata çıkarır | Yüklenen dosya | Standart JSON chunk'lar | Kural tabanlı + hafif LLM |
| **Classifier Agent** | MDS-G008 + MDS-G5 kurallarına göre sınıf belirler | Intended use, yasal kurallar | Sınıf + gerekçe + kaynak | Güçlü model |
| **Evidence Validator** | Kullanıcı evrakını yasal gereksinimle karşılaştırır | Evrak metni, ilgili yasal madde | Uygun / eksik / belirsiz | Orta model |
| **Checklist Agent** | Sınıfa göre evrak listesi çıkarır | Sınıf | Evrak listesi + kaynak kurum | Kural tabanlı |
| **Excel Logger** | Tüm adımları yerel Excel'e yazar | Olay verisi | `.xlsx` güncellemesi | Tool call |
| **Regulatory Watcher** | SFDA sitesini tarar, sürüm kontrolü yapar | URL listesi | Yeni sürüm bildirimi | Hafif model + diff |

### State Machine

```
UPLOAD → INGEST → CLASSIFY → CONFIRM_CLASS → CHECKLIST → COLLECT → VALIDATE → REPORT → DONE
```

Her state'in giriş koşulu, çalışacak ajanı, çıkış koşulu ve hata durumu (fallback) vardır.

**Kritik:** LLM'e "hangi ajanı çağırayım?" diye sorulmaz. State machine karar verir.

## 3. Sabit Vektör Katmanı ve Retrieval

### Sabit Şema

| Alan | Değer |
|---|---|
| Embedding modeli | `BGE-M3` (çok dilli, 1024 boyut) |
| Vektör boyutu | 1024 (model değişirse yeniden indeksleme zorunlu) |
| Normalizasyon | L2 normalize |
| Chunking | Başlık + madde numarası sınırları; max 512 token, overlap 50 |
| Koleksiyonlar | `sfda_regulations`, `user_documents`, `templates`, `faq` |
| Metadata | `source_type`, `doc_id`, `section`, `version_date`, `effective_date`, `language` |
| Retrieval | Hybrid: BM25 + vector, top_k=5, filtre zorunlu |
| Kaynak gösterimi | Her chunk'ta `source_type` ve `doc_id` taşınır |

### Retrieval Kuralları

- Yasal kural koleksiyonu (`sfda_regulations`) ile kullanıcı dokümanı koleksiyonu (`user_documents`) **asla karışmaz**.
- Sınıflandırma sırasında yalnızca `source_type = sfda_regulations` filtresiyle arama yapılır.
- Kullanıcı dokümanı yalnızca kanıt olarak kullanılır, kural kaynağı olamaz.
- Her çıktı, hangi SFDA dokümanının hangi maddesine dayandığını belirtir.

## 4. Büyük Doküman Stratejisi (1024k Token Aşımı)

Bazı dokümanlar (özellikle teknik dosyalar, klinik değerlendirme raporları) 1024k token'ı aşabilir.

### Hiyerarşik Özetleme

1. **Yapısal Bölme:** Doküman başlıklara, maddelere ve eklerine göre bölünür.
2. **Bölüm Özeti:** Her bölüm ayrı ayrı özetlenir (map adımı).
3. **Doküman Haritası:** Özetler bir "doküman haritası" oluşturur (reduce adımı).
4. **Sorguya Göre Retrieval:** Kullanıcının görevi doğrultusunda ilgili bölümler vektör retrieval ile bulunur.
5. **Seçici Gönderim:** Yalnızca ilgili bölümler ve özetleri modele gönderilir.

### Map-Reduce ve Refine Zincirleri

- **Map-Reduce:** Tüm dokümanı parça parça işleyip sonuçları birleştirir.
- **Refine:** Parça parça işleyip her adımda önceki sonucu iyileştirir.
- **Sliding Window:** Uzun metinlerde pencere kaydırarak özet çıkarır.

## 5. Bağlam ve Dikkat Mekanizması

Her ajan çağrısında tüm geçmiş gönderilmez. **Context Packet** denilen sabit bir JSON gönderilir:

```json
{
  "step": "CLASSIFY",
  "device_intended_use": "...",
  "retrieved_rules": [
    {"rule_id": "MDS-G008-R1", "text": "...", "source": "MDS-G008", "version": "2023"}
  ],
  "user_evidence": [
    {"doc_id": "IFU-001", "page": 4, "text": "..."}
  ],
  "previous_state": "INGEST"
}
```

Bu paket, LLM'in dikkatini yalnızca ilgili yasal kurala ve kullanıcı kanıtına yönlendirir. "Lost-in-the-middle" sorunu bu şekilde aşılır.

## 6. Yerel Excel Kaydı

Veritabanı yok. Tüm süreç `.xlsx` dosyasında tutulur. 6 sheet: Process, Documents, Classification, Validation, API_Log, (5. sheet önerisi: Audit)

## 7. Web Arayüzü ve Model/API Seçimi

- Süreç Panosu, Sınıflandırma Kartı, Evrak Listesi, Model Seçimi, Excel İndir.
- Kullanıcı kendi API anahtarını girer; her ajan için model seçebilir.
- `UnifiedLLMClient` ile OpenAI, Anthropic, Gemini ve yerel API'ler desteklenir.

## 8. Güncel SFDA Mevzuatı

| Doküman | Açıklama | Sürüm |
|---|---|---|
| **MDS-G5** | Medical Device Listing and Marketing Authorization | v5.0, 22/06/2020 |
| **MDS-G008** | Classification Guidance | Sınıflandırma kuralları |
| **MDS-G010** | AI/ML-Enabled Medical Devices | v1.0, 03/01/2023 |
| **MDS-G27** | Digital Health Products Guidance | Ağustos 2025 |
| **MDS-REQ9** | Licensing of Medical Devices Establishments | v2, 11/06/2024 |
| **MDS-REQ5** | Importation and Shipments Clearance | v6.0, 19/07/2023 |

**MDMA Zorunluluğu**: Ocak 2022'den itibaren her tıbbi cihaz için zorunlu.
**AR Zorunluluğu**: Yabancı üreticiler doğrudan başvuramaz; Suudi ikametgli AR lazım.
**UDI**: 2025 itibarıyla 460.745 cihaz + 1.782 üretici kayıtlı.
**Siber Güvenlik**: İki ayrı rehber (sağlayıcılar ve üreticiler için).

## 9. Veri Güvenliği ve Güncellik Kontrolü

- Otomatik tarama, sürüm karşılaştırma, kullanıcı bildirimi, sertifika hatırlatma, MDSAP kabulü.

## 10. Teknoloji Yığını

| Bileşen | Öneri |
|---|---|
| Ajan orkestrasyonu | LangGraph veya özel Python state machine |
| Vektör store | ChromaDB persistent / FAISS + SQLite |
| Embedding | BGE-M3 (sabit) |
| LLM erişimi | UnifiedLLMClient |
| Excel | openpyxl veya MCP Excel server |
| Web | React / Vue / sade HTML+JS |
| Doküman işleme | `unstructured`, `pypdf`, Tesseract OCR |
| Özetleme | LangChain `load_summarize_chain` |

## 11. Kritik Kurallar (8 madde)

1. LLM ajan seçmez; state machine seçer.
2. Yasal kural koleksiyonu ile kullanıcı dokümanı koleksiyonu asla karışmaz.
3. Her çıktı kaynak gösterir; kaynaksız çıktı üretilmez.
4. Vektör modeli ve boyutu sabittir; değişirse yeniden indeksleme yapılır.
5. Excel tek gerçek log kaynağıdır; veritabanı yoktur.
6. Kullanıcı modeli değiştirebilir; ajan rolleri değişmez.
7. Class C ve D için insan onayı zorunludur.
8. 1024k token aşan dokümanlar hiyerarşik özetleme + seçici retrieval ile işlenir.
