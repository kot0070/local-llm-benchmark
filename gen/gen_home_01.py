"""Generator for HOME-01 multilingual intent (owner: TASK_B2). Seeded, self-verifying."""
from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path

TEST_ID = "HOME-01"
SEED = 10101
INTENTS = ["order_status", "refund", "complaint", "delivery_change", "account_access",
           "technical_issue", "billing_error", "cancellation"]
URGENCIES = ["low", "medium", "high", "critical"]

URGENCY_RUBRIC = (
    "critical = service/production down NOW or safety/fraud/unauthorized-access risk NOW; "
    "high = money already lost or wrongly charged, or deadline within 24 hours / by tomorrow; "
    "medium = problem affecting use but workaround exists, or deadline in a few days / beyond 24 hours; "
    "low = general question or information request only, no problem."
)

# (lang, tier, message, intent, urgency, entity_ids, amount, date, cue)
# cue must appear verbatim (casefold) in message; urgency strictly follows URGENCY_RUBRIC.
CASES: list[tuple] = [
("en", "easy",
 "Hello support team, I am writing to check the status of my order ORD-48213 placed on 2026-09-02. "
 "The tracking page has not updated for five days and I am worried because it is a birthday gift. "
 "A workaround exists with the gift receipt, so please reply in a few days when convenient. "
 "Could you please confirm the current location of the parcel and the estimated delivery date? Thank you kindly for your help.",
 "order_status", "medium", ["ORD-48213"], None, "2026-09-02", "workaround exists"),
("en", "hard",
 "Hi, I do NOT want to cancel, I just want to change the delivery address for order ORD-48214 before it ships. "
 "The amount of forty-two euros fifty was already charged on 2026-08-28 and the deadline is within 24 hours. "
 "Please confirm you will NOT charge me again and will deliver to the new address I emailed yesterday morning. "
 "My old address is wrong, so update it by tomorrow morning. Thank you for the quick confirmation.",
 "delivery_change", "high", ["ORD-48214"], 42.5, "2026-08-28", "within 24 hours"),
("uk", "medium",
 "Добрий день, прошу перевірити статус мого замовлення ORD-77101 від 2026-09-05. "
 "Це подарунок для мами, тому хвилююся, бо трекінг не оновлюється вже чотири дні. "
 "Є обхідний варіант із чеком, тож прошу відповісти за кілька днів, коли буде зручно. "
 "Підкажіть, будь ласка, де зараз посилка і коли орієнтовно її доставлять. Щиро дякую за допомогу та швидку відповідь.",
 "order_status", "medium", ["ORD-77101"], None, "2026-09-05", "за кілька днів"),
("uk", "hard",
 "Вітаю, я НЕ хочу скасовувати підписку, а лише змінити адресу доставки для ORD-77102, про що писав ще 2026-09-01. "
 "Сума сто двадцять гривень уже списана, код помилки BILL-2201 теж світиться в кабінеті, гроші вже списано. "
 "Строк до завтра вранці, бо їду з міста, прошу оновити адресу саме зараз. "
 "Switching to English for the support team: please do not refund, just update the address. Дякую за розуміння ситуації.",
 "delivery_change", "high", ["ORD-77102", "BILL-2201"], 120.0, "2026-09-01", "гроші вже списано"),
("de", "easy",
 "Guten Tag, ich möchte mich nach dem Status meiner Bestellung ORD-31055 vom 2026-08-29 erkundigen. "
 "Die Sendungsverfolgung zeigt seit sechs Tagen keine Aktualisierung, und das Paket ist ein Geburtstagsgeschenk. "
 "Ein Workaround mit der Geschenkquittung ist vorhanden, daher antworten Sie bitte in wenigen Tagen, wenn es Ihnen passt. "
 "Bitte teilen Sie mir den aktuellen Standort und das voraussichtliche Lieferdatum mit. Vielen Dank für Ihre Unterstützung.",
 "order_status", "medium", ["ORD-31055"], None, "2026-08-29", "in wenigen Tagen"),
("de", "medium",
 "Hallo, ich will NICHT kündigen, sondern nur die Rechnungsadresse für Rechnung INV-90311 ändern, Betrag einhundertfünfzehn Euro. "
 "Die Abbuchung vom 2026-09-03 war doppelt und wurde bereits abgebucht, daher ist die Frist innerhalb von 24 Stunden. "
 "Bitte NICHT erneut abbuchen, sondern die Differenz erstatten und mir eine korrigierte Rechnung per E-Mail bis morgen früh schicken. Danke schön für die schnelle Klärung.",
 "billing_error", "high", ["INV-90311"], 115.0, "2026-09-03", "innerhalb von 24 Stunden"),
("fr", "medium",
 "Bonjour, je vous contacte au sujet de ma commande ORD-55021 passée le 2026-09-04. "
 "Le suivi n'a pas été mis à jour depuis cinq jours et ce colis est un cadeau d'anniversaire important. "
 "Une solution de contournement avec le reçu existe, donc répondez dans quelques jours quand cela vous conviendra. "
 "Pourriez-vous me confirmer l'emplacement actuel du colis ainsi que la date de livraison estimée ? Merci beaucoup pour votre aide précieuse.",
 "order_status", "medium", ["ORD-55021"], None, "2026-09-04", "dans quelques jours"),
("fr", "hard",
 "Bonjour, je ne veux PAS annuler, je veux seulement signaler un problème technique avec le routeur RT-7710 depuis le 2026-08-30. "
 "Le voyant reste rouge, montant de soixante-dix-neuf euros déjà facturé, et le délai est sous 24 heures car je télétravaille. "
 "Merci de ne pas clôturer le ticket TCK-1188 avant la résolution complète et de confirmer par courriel d'ici demain matin. Je reste disponible pour un test à distance.",
 "technical_issue", "high", ["RT-7710", "TCK-1188"], 79.0, "2026-08-30", "sous 24 heures"),
("es", "easy",
 "Hola, escribo para consultar el estado de mi pedido ORD-66034 realizado el 2026-09-01. "
 "¿Podrían confirmarme dónde se encuentra el paquete y la fecha estimada de entrega? Es solo una pregunta, solo para información, no hay ningún problema urgente. "
 "El seguimiento no se actualiza desde hace cuatro días y es un regalo para mi madre. Muchas gracias por su ayuda y ¡que tengan un buen día!",
 "order_status", "low", ["ORD-66034"], None, "2026-09-01", "solo una pregunta"),
("es", "medium",
 "Hola, NO quiero cancelar, solo cambiar la fecha de entrega del pedido ORD-66035 cobrado el 2026-09-06 por sesenta y tres euros. "
 "El repartidor vino ayer y no estábamos, el intento falló. Existe una alternativa con el vecino, así que respondan en unos días cuando les convenga. "
 "Por favor NO lo devuelvan al almacén, reprogramen para el viernes por la mañana y confirmen por correo electrónico. Gracias.",
 "delivery_change", "medium", ["ORD-66035"], 63.0, "2026-09-06", "en unos días"),
("it", "easy",
 "Buongiorno, vi scrivo per conoscere lo stato del mio ordine ORD-41087 effettuato il 2026-08-27. "
 "Il tracciamento non si aggiorna da cinque giorni e si tratta di un regalo di compleanno. "
 "Esiste una soluzione temporanea con la ricevuta, quindi rispondete pure tra qualche giorno quando vi è possibile. "
 "Potreste confermarmi dove si trova il pacco e la data di consegna prevista? Grazie mille per il vostro aiuto.",
 "order_status", "medium", ["ORD-41087"], None, "2026-08-27", "tra qualche giorno"),
("it", "hard",
 "Salve, NON voglio cancellare, voglio solo un rimborso per l'addebito doppio di novantanove euro del 2026-09-02, fattura INV-51200. "
 "L'importo è già addebitato due volte e la scadenza è entro 24 ore perché parte il mutuo domani mattina. "
 "Ho già chiamato due volte, il ticket TCK-4410 è ancora aperto. Per favore NON addebitatemi di nuovo, stornate il secondo pagamento e inviatemi conferma scritta entro domani. Grazie per la collaborazione.",
 "refund", "high", ["INV-51200", "TCK-4410"], 99.0, "2026-09-02", "entro 24 ore"),
("pl", "medium",
 "Dzień dobry, proszę o sprawdzenie statusu mojego zamówienia ORD-22071 z dnia 2026-09-03. "
 "Przesyłka to prezent urodzinowy, a śledzenie nie aktualizuje się od czterech dni, więc się martwię. "
 "Istnieje rozwiązanie tymczasowe z paragonem, dlatego proszę odpowiedzieć za kilka dni, kiedy będzie to wygodne. "
 "Czy mogą Państwo potwierdzić, gdzie jest paczka i kiedy mniej więcej dotrze? Bardzo dziękuję za pomoc.",
 "order_status", "medium", ["ORD-22071"], None, "2026-09-03", "za kilka dni"),
("pl", "hard",
 "Witam, NIE chcę anulować konta, tylko odzyskać dostęp do konta ACC-99120, bo logowanie z 2026-08-31 nie działa. "
 "Kod błędu AUTH-5518, kwota dwadzieścia złotych za weryfikację SMS została już pobrana. "
 "To jest krytyczne: usługa nie działa teraz i istnieje ryzyko oszustwa teraz, bo widzę nieznane próby logowania. "
 "Proszę NIE blokować konta, tylko zresetować hasło i wysłać link na nowy e-mail, który podałem wczoraj. Z góry dziękuję za szybką pomoc.",
 "account_access", "critical", ["ACC-99120", "AUTH-5518"], 20.0, "2026-08-31", "usługa nie działa teraz"),
("cs", "easy",
 "Dobrý den, píši kvůli stavu své objednávky ORD-33012 ze dne 2026-09-06. "
 "Zásilka je dárek k narozeninám a sledování se už pět dní neaktualizuje, takže mám obavy. "
 "Existuje náhradní řešení s dárkovou účtenkou, proto prosím odpovězte během několika dní, až se vám to bude hodit. "
 "Můžete mi prosím potvrdit, kde se balík nachází a kdy přibližně dorazí? Moc děkuji za vaši pomoc a odpověď.",
 "order_status", "medium", ["ORD-33012"], None, "2026-09-06", "během několika dní"),
("cs", "medium",
 "Dobrý den, nechci rušit objednávku, chci jen nahlásit reklamaci k faktuře INV-73301 na částku dva tisíce korun ze dne 2026-08-25. "
 "Částka byla účtována dvakrát a je již stržena, lhůta je do 24 hodin, protože účetní uzávěrka je zítra ráno. "
 "Prosím NESTRÁVEJTE platbu znovu, ale vraťte rozdíl a pošlete opravený doklad na můj e-mail do zítřka. Děkuji za pochopení a rychlé vyřízení.",
 "billing_error", "high", ["INV-73301"], 2000.0, "2026-08-25", "do 24 hodin"),
("tr", "easy",
 "Merhaba, 2026-09-04 tarihli ORD-88012 numaralı siparişimin durumunu öğrenmek istiyorum. "
 "Kargo takibi dört gündür güncellenmiyor ve bu paket bir doğum günü hediyesi olduğu için çok endişeliyim. "
 "Geçici çözüm olarak hediye fişi var, bu yüzden birkaç gün içinde, size uygun olduğunda yanıt verirseniz sevinirim. "
 "Paketin şu an nerede olduğunu ve tahmini teslim tarihini paylaşır mısınız? Yardımınız için çok teşekkür ederim.",
 "order_status", "medium", ["ORD-88012"], None, "2026-09-04", "birkaç gün içinde"),
("tr", "hard",
 "Merhaba, iptal istemiyorum, yalnızca 2026-08-29 tarihli doksan lira tutarındaki teknik sorunu çözmenizi istiyorum, cihaz DEV-5510 sürekli bağlantıyı kesiyor. "
 "Ücret zaten alındı ve süre 24 saat içinde doluyor, çünkü evden çalışıyorum ve yarın sabah sunumum var. "
 "Ticket TCK-9021 açık, lütfen bileti çözmeden kapatmayın ve yarın sabaha kadar e-posta ile bilgi verin. İlginiz için teşekkürler.",
 "technical_issue", "high", ["DEV-5510", "TCK-9021"], 90.0, "2026-08-29", "24 saat içinde"),
("ar", "medium",
 "مرحبا، أكتب إليكم للاستفسار عن حالة الطلب ORD-99031 المؤرخ في 2026-09-02. "
 "صفحة التتبع لم تتحدث منذ خمسة أيام وهذا الطرد هدية عيد ميلاد مهمة. "
 "يوجد حل مؤقت مع إيصال الهدية، لذا يرجى الرد خلال بضعة أيام عندما يكون ذلك مناسبا. "
 "هل يمكنكم تأكيد مكان الطرد الحالي وموعد التسليم المتوقع؟ شكرا جزيلا لكم على المساعدة والاهتمام.",
 "order_status", "medium", ["ORD-99031"], None, "2026-09-02", "خلال بضعة أيام"),
("ar", "hard",
 "مرحبا، أنا لا أريد إلغاء الحساب بل استعادة الوصول إلى ACC-77012 بعد مشكلة تسجيل الدخول بتاريخ 2026-08-28. "
 "رمز الخطأ AUTH-3300 والمبلغ خمسون دولارا معلق، الخدمة متوقفة الآن ويوجد خطر احتيال الآن بسبب محاولات غريبة. "
 "Switching to English for the team: please do NOT close the account, just reset the password. "
 "فقط أعيدوا تعيين كلمة المرور وأرسلوا الرابط إلى بريدي الجديد. شكرا لتفهمكم وسرعة الاستجابة.",
 "account_access", "critical", ["ACC-77012", "AUTH-3300"], 50.0, "2026-08-28", "الخدمة متوقفة الآن"),
("zh", "easy",
 "您好，我想查询 2026-09-05 下单的 ORD-61045 订单状态。物流跟踪已经五天没有更新，这是一个生日礼物，我很担心。 "
 "有临时解决办法，我保留了礼品小票，所以请在几天内方便时回复即可。请确认包裹目前的位置和预计送达日期。非常感谢您的帮助，期待您的回复，祝工作顺利，谢谢你们的客服支持。",
 "order_status", "medium", ["ORD-61045"], None, "2026-09-05", "几天内"),
("zh", "medium",
 "你好，我不是要取消订单 ORD-61046，而是要投诉 2026-08-30 重复扣款三百元的问题，账单 INV-61046 显示重复收费。 "
 "款项已经扣款，问题很急迫，请在24小时内回复并在明天早上前处理。 "
 "请不要再次扣款，尽快退还多收部分，并把更正后的账单发到我的邮箱。已经等了三天，请今天内回复，谢谢。",
 "complaint", "high", ["ORD-61046", "INV-61046"], 300.0, "2026-08-30", "24小时内"),
("ja", "easy",
 "こんにちは、2026-09-01 に注文した ORD-72055 の配送状況を確認したくご連絡しました。 "
 "追跡情報が五日間更新されておらず、誕生日プレゼントなので心配しています。 "
 "代替手段がありますので、数日以内にご都合のよいときにご返信いただければ幸いです。 "
 "現在の荷物の場所と配達予定日を教えていただけますでしょうか。お手数ですがよろしくお願いいたします。",
 "order_status", "medium", ["ORD-72055"], None, "2026-09-01", "数日以内"),
("ja", "hard",
 "こんにちは、解約ではなく 2026-09-07 請求の千円の二重請求 INV-72056 について返金を希望します。 "
 "金額は既に請求済みで、期限は24時間以内ですので明日午前中までに対応してください。 "
 "サポートには既に二度連絡し、チケット TCK-7201 は未解決です。どうか再度請求しないでください、差額を返金し、確認メールを明日までに送ってください。よろしくお願いいたします。",
 "refund", "high", ["INV-72056", "TCK-7201"], 1000.0, "2026-09-07", "24時間以内"),
]


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_cases() -> list[dict]:
    rng = random.Random(SEED)
    out = []
    for idx, (lang, tier, msg, intent, urg, eids, amt, date, cue) in enumerate(CASES):
        assert intent in INTENTS, intent
        assert urg in URGENCIES, urg
        for eid in eids:
            assert eid in msg, f"id {eid} not verbatim in case {idx}"
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", date), date
        # urgency cue must be present (objective rubric grounding)
        assert cue.casefold() in msg.casefold(), f"cue {cue!r} missing in case {idx}"
        wc = len(msg.split())
        if lang not in ("zh", "ja", "ar"):
            assert 40 <= wc <= 120, f"case {idx} words={wc}"
        else:
            assert len(msg) >= 100, f"case {idx} too short"
        cid = f"H01-{idx+1:03d}"
        out.append({
            "id": cid, "test_id": TEST_ID, "tier": tier, "lang": lang,
            "input": {"message": msg},
            "expected": {"intent": intent, "urgency": urg, "entity_ids": sorted(eids),
                         "amount": amt, "date": date, "language": lang},
            "meta": {"source": "authored-b2", "seed": SEED, "urgency_cue": cue,
                     "urgency_rubric": URGENCY_RUBRIC},
        })
    # code-mixing check: only 2 hard cases may mix scripts (uk H01-004, ar H01-020)
    allowed_mix = {"H01-004", "H01-020"}
    latin_re = re.compile(r"[A-Za-z]")
    for c in out:
        if c["tier"] == "hard" and c["id"] in allowed_mix:
            continue
        msg = c["input"]["message"]
        lang = c["lang"]
        if lang in ("uk", "ar", "zh", "ja"):
            # non-latin scripts should not contain latin words except IDs/dates/brand tokens
            tmp = re.sub(r"(ORD|ACC|INV|TCK|EMP|DEV|BILL|AUTH)-\d+", " ", msg)
            tmp = re.sub(r"\d{4}-\d{2}-\d{2}", " ", tmp)
            tmp = re.sub(r"TCK|ORD|INV|SMS|E-Mail|E-mail", " ", tmp, flags=re.IGNORECASE)
            # allow the word "Ticket" in tr hard (product term)? tr is latin-script so skip
            if lang in ("uk", "ar", "zh", "ja"):
                latin_words = re.findall(r"[A-Za-z]{3,}", tmp)
                # filter single technical tokens that are unavoidable product names
                filtered = [w for w in latin_words if w.lower() not in ("sms", "email")]
                assert not filtered, f"unexpected latin mixing in {c['id']}: {filtered}"
        elif lang in ("de", "fr", "es", "it", "pl", "cs", "tr"):
            # latin-script languages: no english-only fragments; check known english phrases absent
            low = msg.casefold()
            for phrase in ("do not charge again", "double charge", "delivery attempt",
                           "livraison change", "reboot", "switching to english"):
                assert phrase not in low, f"english mixing in {c['id']}: {phrase}"
    # stratified interleave easy/medium/hard
    by_tier: dict[str, list] = {"easy": [], "medium": [], "hard": []}
    for c in out:
        by_tier[c["tier"]].append(c)
    for v in by_tier.values():
        rng.shuffle(v)
    ordered: list[dict] = []
    for i in range(max(len(v) for v in by_tier.values())):
        for t in ("easy", "medium", "hard"):
            if i < len(by_tier[t]):
                ordered.append(by_tier[t][i])
    return ordered


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    dest = root / "fixtures" / TEST_ID
    assets = dest / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    cases = build_cases()
    for c in cases:
        for eid in c["expected"]["entity_ids"]:
            if eid not in c["input"]["message"]:
                raise ValueError(f"verify failed for {c['id']}")
    with open(dest / "cases.jsonl", "w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n")
    files: dict[str, str] = {}
    files["cases.jsonl"] = _sha256_file(dest / "cases.jsonl")
    for p in sorted(assets.rglob("*")):
        if p.is_file():
            files["assets/" + p.relative_to(assets).as_posix()] = _sha256_file(p)
    manifest = {"test_id": TEST_ID, "version": "n1", "seed": SEED, "files": files}
    with open(dest / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
