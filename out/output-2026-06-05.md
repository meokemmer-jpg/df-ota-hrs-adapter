# df-ota-hrs-adapter — Output [CRUX-MK]
*Autonom aktiviert 2026-06-05T15:48:53.700914+00:00 | ollama-local/qwen2.5:14b-instruct*

# df-ota-hrs-adapter [CRUX-MK]

## **Zweck**
Der `df-ota-hrs-adapter` dient als Connector für HRS OTA, speziell für Gesc
Geschäftsfahrten im deutschsprachigen Raum (DACH).

### **Funktionen:**

1. **Inventory-Abfrage:** Verfuegbarkeit von Zimmern via HRS-Connect-API.
2. **Rate-Push und Tarifverhandlung:** Tarife aktualisieren und verhandeln,
verhandeln, einschließlich eines 13%-Kommissions-Tackers pro Buchung.
3. **Buchungs-Benachrichtigungen:** Notifications über Webhooks mit HMAC-SH
HMAC-SHA256-Verifikation.

### **API-Pattern:**
- Nutzung des HRS-Connect-APIs für Inventar und Tarife, sowie Buchungsverfo
Buchungsverfolgung.
- Verwendung eines Token-Services zur Authentifizierung statt direkter API-
API-Tokens.
- Implementierung von Webhooks für Benachrichtigungen mit HMAC-Verifikation
HMAC-Verifikation.

### **Betriebsmodus:**
Standardmäßig läuft in Sandbox-Modus, Mock-Daten werden verwendet (`DF_OTA_
(`DF_OTA_HRS_REAL_ENABLED=false`). Um den Real-Mode zu aktivieren, müssen d
die ENV-Variablen `DF_OTA_HRS_REAL_ENABLED`, `HRS_HOTELIER_ID` und `HRS_API
`HRS_API_KEY` gesetzt sein.

### **Module:**
1. **hrs_adapter.py:** Implementiert Verbindung zum HRS-Connect-API, Tarifv
Tarifverhandlung und Kommissions-Tacker.
2. **hrs_auth.py:** Authentifizierungsservice für Hotelier und Token-Dienst
Token-Dienst.
3. **hrs_webhook.py:** Empfänger für Buchungsbenachrichtigungen mit HMAC-Si
HMAC-Signaturverifikation.
4. **commission_tracker.py:** Erstellt Kommissions-Records pro Buchung und 
aggregiert Berichte.

### **Tests:**
27+ Tests sind implementiert, um die Korrektheit der Adapter-, Auth-, Webho
Webhook-, Tracker- sowie AuditLogger-Funktionen zu gewährleisten.

### **LaunchAgent:**
Die Datei `com.kemmer.df-ota-hrs-adapter.plist` wird kopiert und in das Lau
LaunchAgent-Verzeichnis geladen. Der Agent läuft bei jedem Start mit einer 
Intervallzeit von 2 Stunden (7200 Sekunden).

### **K11-K16 Compliance:**
Die Dark Factory folgt streng den Sicherheitsrichtlinien (Cascade-Containme
(Cascade-Containment, Provenance, PAV), ist überwacht und bereit für Überar
Überarbeitungen.

### **LC1-LC5 Compliance:**
Gewährleistung der Verfügbarkeit mit Fallbacks, Zerstörungsfreundlicher Des
Design (Mock-Daten), Fehlerisolierung durch State-Externalization sowie ide
idempotente Operationen sind implementiert.

Diese Dark Factory ist vollständig kompatibel mit den spezifischen Anforder
Anforderungen und Richtlinien der Kemmer-Familie.