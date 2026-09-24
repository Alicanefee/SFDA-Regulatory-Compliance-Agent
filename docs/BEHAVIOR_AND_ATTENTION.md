# SFDA AI Kontrol Ajanı — Davranış, Dikkat ve Refinmanlar

> Bu doküman kullanıcı tarafından sağlanan [`SFDA_Agent_Plan.md`](SFDA_Agent_Plan.md) planına ek olarak hazırlanmıştır.
> İki eksik parçayı doldurur: (1) Ajan davranışı/kimliği, (2) Dikkat öncelik listesi. Ayrıca plana 15 kritik refinman ekler.

---

## BÖLÜM A — Plana 15 Kritik Refinman (eklenti)

Bu maddeler kullanıcı planındaki mimariyi bozmadan, onu daha robust hale getirir.

### A1. Sürüm Kilidi (Version Lock) — Kritik

Her karar verildiğinde, o anki SFDA dokümanlarının **sürüm snapshot'ı** kaydedilmeli. Excel'in `Classification` sheet'ine şu kolonlar eklenmeli:

```
mds_g5_version | mds_g008_version | mds_g010_version | mds_g27_version | decision_date
```

Eğer 6 ay sonra MDS-G010 v2.0 çıkarsa, **eski kararlar hala v1.0'a dayanıyor olarak görülmeli**. Auditor "Bu karar neye dayanıyor?" diye sorduğunda — v1.0 (3 Ocak 2023, yürürlükte).

### A2. Audit Trail Bütünlüğü — Hash Chain

Excel dosyası kolayca değiştirilebilir. Auditor değiştirilmediğini kanıtlayamaz. Çözüm:

- Her log satırı `prev_hash` ve `this_hash` içerir
- `this_hash = sha256(prev_hash + row_content + timestamp)`
- İlk satırın `prev_hash = "GENESIS"`
- Inspector geldiğinde hash chain'i verify eden ayrı bir script çalıştırır

```python
# Audit trail integrity — her satır hash içerir
def log_event(event):
    prev_hash = get_last_hash()
    row_content = json.dumps(event, sort_keys=True)
    timestamp = datetime.now().isoformat()
    this_hash = sha256(f"{prev_hash}{row_content}{timestamp}".encode()).hexdigest()
    write_to_excel(event + {"prev_hash": prev_hash, "this_hash": this_hash})
```

Bu olmadan, Excel log'u "düzeltilebilir belge" olarak görülür, hukuki geçerliliği zayıf.

### A3. Hallucination Defense Spesifikasyonu

Plan "kaynak gösterimi" diyor ama mekanizmayı detaylandırmadı. Üç katmanlı savunma:

| Katman | Ne yapar | Ne engeller |
|---|---|---|
| **L1 Preamble constraint** | LLM'e "sadece retrieved_rules içindeki rule_id'leri cite et" diye hatırlatır | Casual hallucination |
| **L2 Tool-based lookup** | LLM, `lookup_rule(rule_id)` tool'unu çağırarak clause text'ini verify etmeden cite edemez | Orta seviye fabrication |
| **L3 Post-process validator** | LLM'in ürettiği her `rule_id` gerçek retrieved_rules listesinde var mı diye kontrol eder; yoksa finding'i "unverified" işaretiyle düşür | LLM preamble'ı görmezden gelse bile |

Bu zaten [00-flagship/regulatory-precheck-agent](ali-can-efe-portfolio/00-flagship/regulatory-precheck-agent/) içinde uygulandı — SFDA ajanına aynısı taşımalı.

### A4. Class Değişimi Cascade

Eğer kullanıcı sınıflandırmayı değiştirirse (B → C), checklist tamamen değişir. State machine CLASSIFY → CONFIRM_CLASS → CHECKLIST akışında, CONFIRM_CLASS'ta "hayır" yanıtı geldiğinde CLASSIFY'a geri dönmeli.

**Loop önlemi**: max 1 geri dönüş. İkinci geri dönüşte → MANUAL_REVIEW state'ine düş.

### A5. UDI DI vs PI ayrımı

UDI tek başına bir kavram değil — iki segmentten oluşur:

- **DI (Device Identifier)**: üretici + ürün kodu. Paket üzerinde olmalı.
- **PI (Production Identifier)**: lot, seri, üretim tarihi, son kullanma. Ürün üzerinde olmalı.

Checklist şu maddeleri içermeli:
- DI paket etiketinde var mı?
- PI ürün etiketinde var mı?
- DI formatı GS1 veya HIBC uyumlu mu?
- GUDID veritabanına kayıt yapıldı mı?
- PI için son kullanma tarihi mi, lot mu yoksa ikisi birden mi?

### A6. AR Lisansı Doğrulama

Plan AR zorunluluğunu anıyor ama **checklist'te "AR lisansı geçerli mi"** maddesi lazım. SFDA'nın ARL lookup tool'u var: https://www.sfda.gov.sa/en/medical-devices/registered

Agent bu URL'i periyodik tarayıp "Bu AR'ın lisansı süresi dolmuş" uyarısı vermeli.

### A7. Arabic IFU Translation Verification Mekaniği

Dil gereksinimlerini anıyor ama şu mekanik kontroller lazım:

1. **RTL detection**: Arabic IFU gerçekten right-to-left mi (charakter-range check)
2. **Tıbbi terminoloji uygunluğu**: certified Arabic medical translator kullanıldı mı (belge iste)
3. **English ile cross-consistency**: aynı prosedür hem EN hem AR'de tarif ediliyor mu

```python
def verify_arabic_ifu(ar_text, en_text):
    # 1. RTL check
    if not is_rtl_dominant(ar_text):
        return Finding(severity='critical', msg='Arabic IFU appears to be Latin-script')
    # 2. Translation certificate
    if not has_translator_certificate(ar_text):
        return Finding(severity='critical', msg='No certified Arabic medical translator stamp')
    # 3. Cross-language consistency
    return cross_validate_sections(ar_text, en_text)
```

### A8. Pre-submission Meeting Önerisi

Class C/D cihazlar için SFDA pre-submission meeting önerir. Checklist'e şu madde eklenmeli:

> "Class C/D cihazlar için SFDA pre-submission meeting önerilir. Talep için sfda.gov.sa üzerinden form doldurun. Ortalama cevap süresi: 4-6 hafta."

Agent bunu otomatik olarak bir "önerilen aksiyon" olarak işaretlemeli — kritik değil ama yüksek değerli.

### A9. CER (Clinical Evaluation Report) Sınıf Bazlı Derinlik

Plan "CER lazım" diyor ama derinlik class'a göre değişir:

| Class | CER derinliği | Min gereksinim |
|---|---|---|
| **A** | Genelde gerekmez | (yalnızca literature review yeterli) |
| **B** | Equivalence justification | Predicate device + literature review |
| **C** | Klinik veri + literature | MEDDEV 2.7/1 rev.4 metodolojisi |
| **D** | Klinik deney + PMCF | Tam CER + PMCF plan |

Classifier bunu ayırt etmeli.

### A10. PSUR (Periodic Safety Update Report) Sıklığı

| Class | Sıklık |
|---|---|
| **A** | Yıllık |
| **B** | İlk 2 yıl yıllık, sonra 2 yılda bir |
| **C** | İlk 2 yıl yıllık, sonra 2 yılda bir |
| **D** | Yıllık |

Checklist'te "PSUR planı var mı" maddesi class'a göre farklı soru sormalı.

### A11. Risk Management File Derinliği (ISO 14971:2019)

Tüm sınıflar için zorunlu ama derinlik farklı:

- **Class A**: Basic hazard analysis
- **Class B**: Full risk management file + residual risk assessment
- **Class C/D**: Full RMF + benefit-risk analysis + post-production information

### A12. Cybersecurity Documentation Class Bazlı

Plan cybersecurity'ı anıyor ama derinlik class'a göre:

| Class | Cyber gereksinim |
|---|---|
| **A** (non-connected) | Genelde yok |
| **B** (connected) | IEC 81001-5-1 self-attestation |
| **C** (connected) | Threat model + SBOM + IEC 81001-5-1 |
| **D** (connected) | Full penetration test report + SBOM + threat model + IEC 81001-5-1 |

### A13. Change Notification (Post-Market)

MDMA alındıktan sonra cihaz değişirse SFDA'ya "change notification" gerekiyor. Agent post-market phase'i de takip etmeli — yalnızca pre-submission değil.

Change types:
- **Notable change** (yeni risk) → SFDA onayı gerekir
- **Non-notable change** (form değişikliği) → only notification
- **Administrative change** (firma adı) → log only

### A14. Post-Market Vigilance Reporting Timelines

| Event | Timeline | Recipient |
|---|---|---|
| Adverse event (death/serious injury) | 10 gün | SFDA |
| Field Safety Corrective Action (FSCA) | 5 gün | SFDA |
| Trend report | Quarterly (Class C/D) | SFDA |
| PSUR | Class'a göre (A10) | SFDA |

Agent hatırlatma alarmları kurmalı.

### A15. Multi-Jurisdiction Flag

Cihaz Saudi + UAE + Türkiye'ye gidiyorsa, her jurisdiction için **ayrı checklist**. Plan şu an Saudi-odaklı ama agent "multi-jurisdiction mode" desteklemeli.

```python
class Jurisdiction(Enum):
    SAUDI = "sfda"
    UAE = "mohap"
    TURKEY = "titck"

# Cross-jurisdiction flag
if submission.jurisdictions_count > 1:
    checklist = build_unified_checklist(submission.jurisdictions)
    # → her madde için "common" vs "specific" işareti
```

---

## BÖLÜM B — Ajan Davranışı ve Kimliği

> Ajan bir fonksiyon değil; bir karakter. Auditörün raporu okurken "bu ajan dikkatli, tutarlı ve güvenilir" demesi lazım.

### B1. Kişilik (Persona)

Ajan **"Mukim bir regülatuvar asistanı"** olmalı:

- **Tutarlı**: Aynı girdi → aynı çıktı (temperature=0)
- **Süssüz**: "Süper", "harika", "mükemmel" gibi kelimeler yok. Sadece bulgu + kaynak + öneri.
- **Kısa**: Bir bulgu = 2 cümle max. Uzun açıklama = auditor yorar.
- **Sayısal**: "Eksik" yerine "3 madde eksik (SFDA-MDS-G008-R5.2, R5.3, R5.7)" gibi.
- **Kaynaklı**: Her bulgu `rule_id` + `doc_id` + `page` ile.

### B2. Davranış Kuralları (Behavior Rules)

| # | Kural | Neden |
|---|---|---|
| 1 | **"Bilmiyorum" demeyi bilmeli** | Borderline durumda "karar verilemiyor — insan review" demek, yanlış karardan iyi |
| 2 | **Conservative by design** | Borderline class B/C'de C'ye çek. SFDA safety-first ile uyumlu |
| 3 | **Pre-check citation** | LLM returnden ettiği `rule_id` gerçekten retrieved_rules içinde var mı diye verify etmeden output verme |
| 4 | **Time-aware** | Bugün 2026-09-24. MDS-G27 (Aug 2025) → etkili. MDS-G010 v2 çıkmadı → v1.0 hala geçerli. Yeni sürüm geldi → "eski kararları gözden geçir" uyarısı |
| 5 | **Disclaimer mandatory** | Her output'ta "Bu agent resmi SFDA tavsiyesi değildir; resmi onay için SFDA'ya başvurun" yazmalı |
| 6 | **Audit-ready** | Her karar "Bu neye dayanıyor?" sorusuna yanıt verebilmeli (hash chain + version snapshot) |
| 7 | **Reverse-check translation** | Arabic + English dokümanlar aynı bulguyu üretmeli. Tutarlılık testi |
| 8 | **Lexical vs semantic distinction** | "ISO 13485" → exact match (lexical). "Klinik değerlendirme" → semantic. İkisini karıştırma |
| 9 | **No silent fallback** | Bir agent fail ederse, kullanıcıya göster: "Classifier agent LLM error — falling back to MANUAL_REVIEW" |
| 10 | **One finding = one source** | Bir bulgu, bir kural kaynağına dayanmalı. "İki kurala dayanıyor" = iki ayrı bulgu olmalı |

### B3. İletişim Şablonları

Ajan kullanıcıya şu şekilde konuşmalı:

**Sınıflandırma sonrası (CONFIRM_CLASS):**
```
[Classification Result]
Device: Canon VITRAE MRI System (1.5T)
Intended use: Diagnostic imaging via magnetic resonance
Risk class: **C** (per MDS-G008, Rule 13 — diagnostic imaging with non-ionizing radiation)

Cited clause: MDS-G008 §13.2
Justification: "Active diagnostic devices using non-ionizing radiation for diagnosis 
fall under Class C unless they are intended for monitoring of vital physiological 
parameters where the nature of variations could result in immediate danger."

Confirm class? [Yes / No (re-classify) / Manual review]
```

**Validation sonrası (REPORT):**
```
[Validation Findings — Class C submission]

🔴 Critical (2):
  1. Cybersecurity documentation missing (MDS-G27 §4.2)
     Source: MDS-G27, page 14, clause 4.2.1
     Suggested fix: Prepare threat model + SBOM per IEC 81001-5-1
     
  2. Arabic IFU not certified-translator stamped (MDS-G5 §6.1)
     Source: MDS-G5, page 22, clause 6.1.3
     Suggested fix: Engage certified Arabic medical translator; stamp + sign

🟡 Warning (1):
  3. Risk management file incomplete (ISO 14971 §5.4)
     Source: ISO 14971:2019, clause 5.4
     Suggested fix: Add benefit-risk analysis section (Class C requirement)

🔵 Info (1):
  4. Pre-submission meeting recommended for Class C devices
     Source: SFDA MDMA process overview, step 3
     Suggested fix: Submit pre-submission request via sfda.gov.sa

Audit hash: 7f3a9b...e4c2 (chain verification OK)
Version snapshot: MDS-G5 v5.0 / MDS-G008 (current) / MDS-G27 Aug 2025
```

### B4. Sessiz Durumlar (Silent failure modes — kaçınılacak)

Ajanın düşmemesi gereken davranışlar:

| Kötü davranış | Neden kötü | Doğru davranış |
|---|---|---|
| "Bulgu yok" yazıp geçmek | Belki de yanılmıştır | "Retrieved kurallarda eksiklik saptanmadı; ancak bu, compliancy anlamına gelmez. İnsan review önerilir" |
| Birden fazla bulguyu tek satırda yazmak | Auditor trace zor | Her bulgu ayrı satır, ayrı kaynak |
| Source vermeden tavsiye vermek | Auditör verify edemez | "Pre-submission meeting önerilir (kaynak: SFDA MDMA Process Overview, step 3)" |
| Belirsizlikte tahmin etmek | Yanlış class = 6 ay gecikme | "Bu cihaz sınıflandırması belirsiz — MDS-G008 §13 ile §14 arasında. İnsan review'a gönderildi" |
| Türkçe response vermek | Auditing İngilizce olacak | Tüm output İngilizce (auditörler genelde İngilizce okur) |
| Geçmiş bulguyu sessizce overwrite etmek | Hukuki olarak riskli | Yeni bulgu + "Previous finding #X superseded" işareti |

### B5. Versiyon Yönetimi Davranışı

SFDA dokümanları zamanla değişir. Agent'ın zamanla nasıl davranacağı:

```
T0 (2026-09-24): MDS-G010 v1.0 (current)
T1 (2027-03-01): MDS-G010 v2.0 yayınlandı
T2 (2027-03-02): Agent tetiklenir →
  "Yeni MDS-G010 sürümü tespit edildi (v2.0, 1 Mart 2027). 
   Önceki kararlardan 47 tanesi MDS-G010 v1.0'a dayanıyor.
   [ ] Kararları v2.0 ile re-validate et
   [ ] Sadece etkilenen kararları göster
   [ ] Daha sonra hatırlat"
```

---

## BÖLÜM C — Dikkat Öncelik Listesi (Attention Priority)

> Ajan'ın neye dikkat edeceği — öncelik sırasıyla. Bu liste state machine'in her state'inde agent'ın prompt'una hangi maddelerin inject edileceğini belirler.

### C1. P0 — Kritik (yanlış karar = submission rejection + 6 ay gecikme)

1. **Class C/D tespiti** — her cihaz için doğru risk class belirlenmeli. MDS-G008 + intended use + technology combination
2. **AR lisansı geçerliliği** — süresi dolmuş AR = otomatik reject. SFDA ARL lookup tool ile verify
3. **MDMA zorunluluğu** — CE/FDA onayı olsa bile MDMA şart. Ocak 2022'den beri
4. **UDI DI + PI formatı** — GUDID uyumlu, doğru segment etiketleri
5. **IFU Arabic + English** — yalnızca İngilizce = reject. RTL + certified translator
6. **Clinical Evaluation Report varlığı** — Class C/D için zorunlu (MEDDEV 2.7/1 rev.4)
7. **Risk Management File** — ISO 14971:2019, tüm sınıflar için (derinlik class'a göre)
8. **QMS sertifikası** — ISO 13485:2016 (MDSAP tercihen)
9. **Cybersecurity documentation** — connected cihazlar için (IEC 81001-5-1 + SBOM + threat model)
10. **Saudi-specific labeling** — Arabic + English + Suudi FDA logo/format gereksinimleri

### C2. P1 — Yüksek (yanlış karar = 1-2 ay gecikme)

11. **AR notarization + apostille** — yabancı ülkede legalization eksikse
12. **TFA (Technical File Assessment) derinliği** — class'a göre (B = self-declaration, C = review, D = clinical)
13. **Conformity assessment route** — Annex II vs Annex III seçimi doğru mu
14. **IFU Arabic translation quality** — machine translation değil, certified Arabic medical translator
15. **SBOM completeness** — tüm bağımlılıklar (deps + transitive deps) listeli mi
16. **Threat model coverage** — STRIDE veya PASTA metodolojisi kullanıldı mı
17. **Penetration test report** — Class D connected cihazlar için
18. **Pre-submission meeting önerisi** — Class C/D cihazlar için SFDA önerir

### C3. P2 — Orta (yanlış karar = iteratif düzeltme)

19. **Post-market surveillance plan formatı** (PMSP) — class'a göre sıklık
20. **Periodic Safety Update Report** sıklığı — Class A yıllık, C/D yıllık, B 2 yılda
21. **Vigilance reporting timeline** — adverse event 10 gün, FSCA 5 gün
22. **Clinical literature search strategy** — MEDDEV 2.7/1 rev.4 reproducible search
23. **Equivalence justification rigor** — predicate device + biological/technical/clinical equivalence
24. **Software documentation level** — IEC 62304 class A/B/C
25. **Usability engineering file** — IEC 62366-1

### C4. P3 — Düşük (iyileştirme)

26. **Best practice tip'leri** — çalışma grupları, kongreler, ICF benchmarking
27. **Glossary access** — terim açıklamaları
28. **Cross-reference validation** — internal doc tutarlılığı
29. **Document formatting checks** — sayfa numarası, header/footer, font
30. **Translation quality alerts** — terminology consistency flag

### C5. Hangi state hangi P seviyesini dikkate almalı?

| State | Dikkat seviyesi |
|---|---|
| INGEST | P3 (formatting) + P1 (translation quality) |
| CLASSIFY | P0 (#1 class detection) |
| CONFIRM_CLASS | P0 (#1) — human review'a yönelt |
| CHECKLIST | P0 (1-10) + P1 (11-18) |
| COLLECT | P1 (12-18) — eksik evrak tespiti |
| VALIDATE | P0 (4-10) + P1 (11-18) + P2 (19-25) |
| REPORT | Tüm seviyeler — auditor-ready çıktı |
| (Post-market) | P2 (19-21) — vigilance + PSUR + change notification |

---

## BÖLÜM D — Uygulama Fazları (Implementation Phases)

### D1. MVP (v0.1) — 2 hafta — "Pre-check Class B"
**Scope:**
- 4 agent: Orchestrator, Ingest, Classifier, Checklist (Evidence Validator + Regulatory Watcher yok)
- 1 jurisdiction (Saudi SFDA)
- 3 doc type: IFU, Technical File, Risk Management File
- ChromaDB (Excel değil — henüz yok)
- CLI only (web yok)
- Output: Class detection (MDS-G008) + class-bazlı checklist
- P0 maddelerinin 5'i kontrol edilir (#1, #2, #5, #6, #7)

### D2. v0.2 — +2 hafta — "Validation + Excel Log"
- Evidence Validator agent (gerçek clause-level validation)
- Excel logger (openpyxl + hash chain)
- Web arayüzü (Streamlit — hızlı)
- 5 doc type (yukarıdakiler + QMS certificate + AR letter)
- 2 jurisdiction (Saudi + UAE MoHAP — A15 multi-jurisdiction flag)
- P0 (1-10) tam kontrol

### D3. v0.3 — +2 hafta — "Regulatory Watcher + Audit Hardening"
- Regulatory Watcher (SFDA sitesi tarama + RSS)
- Version lock + snapshot (A1)
- Audit hash chain (A2)
- Pre-submission meeting önerisi (A8)
- Periodic safety update reminders (A14)
- P1 (11-18) kontrol

### D4. v1.0 — +4 hafta — "Production"
- Multi-jurisdiction cross-validation (Saudi + UAE + Turkey)
- Arabic NLP pipeline (CAMeL Tools — RTL detection, terminology)
- LangGraph migration (special state machine → LangGraph)
- Production hardening: auth, rate limit, monitoring, error recovery
- P2 (19-25) + P3 (26-30) kontrol

---

## BÖLÜM E — Sonraki Adım

Bu doküman Saudi için planı tamamlar. **Sonraki adım**:

- **Implementasyon öncesi** — bu planı ** UAE MoHAP** için de hazırlamak
- UAE için farklar:
  - Yasa: Federal Law No. 8 of 2023 (Medical Devices)
  - Regulatory body: MoHAP (Saudi'de SFDA)
  - MDMA eşdeğeri: MoHAP Device Registration Certificate
  - AR: Local Authorized Representative (LAR) — UAE-ikametli
  - Cybersecurity: Article 2.4'te zorunlu (IEC 81001-5-1 + SBOM + threat model + PMCP)
  - Data protection: UAE PDPL (Federal Decree-Law No. 45 of 2021)
  - Vigilance timeline: FSCA 10 gün (Saudi'de 5)
  - PSUR: Class IIa 2 yılda, IIb/III yıllık

Sonraki mesajında UAE planını paylaş; o plana da aynı "ajan davranışı + dikkat listesi + refinmanlar" ekini hazırlayacağım. Daha sonra her ikisini karşılaştırıp **ortak çekirdek** + **jurisdiction-spesifik modüller** olarak ayırabiliriz (A15 multi-jurisdiction flag'in temeli).
