#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import sys
import mysql.connector
from typing import Dict, List, Optional, Any

# Veritabanı bağlantı ayarları
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root", 
    "database": "uzmanSistemDB"
}

def metni_normalize_et(text: str) -> str:
    """
    Metni veritabanı/sözlük aramaları için normalleştirir (küçük harf, Türkçe karakterler, boşluklar).
    None veya non-string girdileri boş string'e çevirir.
    """
    if not isinstance(text, str):
        return '' # String olmayan veya None girdiler için boş string döndür
    text = text.lower() # Tüm harfleri küçült
    replacements = {
        'ö': 'o', 'ç': 'c', 'ş': 's', 'ı': 'i', 'ğ': 'g', 'ü': 'u', # Türkçe karakter dönüşümleri
        ' ': '_', '+': 'plus', '-': '', '.': '', ',': '', "'": '' # Boşlukları ve bazı noktalama işaretlerini dönüştür/kaldır
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def fetch_oneri_from_db_by_kriter(conn, kriter: str) -> Optional[Dict]:
    """
    Veritabanındaki oneriler tablosundan belirli bir kritere ait öneriyi çeker.
    'random_pool' kriterli olanları çekmez.
    """
    try:
        cursor = conn.cursor(dictionary=True)
        # Sadece spesifik kriterlere sahip olanları çek ('random_pool' olanlar hariç)
        # Kriterin boş olmaması ve 'random_pool' olmaması koşulunu ekliyoruz.
        sorgu = "SELECT oneri_metni AS text, aciklama FROM oneriler WHERE kriter = %s AND kriter IS NOT NULL AND kriter != 'random_pool' LIMIT 1"
        normalized_kriter = metni_normalize_et(kriter) # Arama yapmadan önce kriter adını normalize et
        cursor.execute(sorgu, (normalized_kriter,))
        result = cursor.fetchone()
        cursor.close()

        if result:
            # Veritabanından gelen oneri_metni ve aciklama'yı kullan
            return {"text": result.get("text", f"Öneri metni ('{kriter}') veritabanında bulunamadı."),
                    "aciklama": result.get("aciklama", f"Bu öneri, '{kriter.replace('_', ' ')}' faktörüne göre verilmiştir.")}
        else:
            return None # Hiçbir öneri bulunamazsa None döndür

    except mysql.connector.Error as e:
        print(f"Veritabanı hatası (fetch_oneri_from_db_by_kriter sorgusu): {e}", file=sys.stderr)
        # Hata durumunda da None döndürerek üst fonksiyonda yakalanmasını veya atlanmasını sağlar
        return None
    except Exception as e:
        print(f"Kriter bazlı öneri çekilirken genel hata oluştu: {e}", file=sys.stderr)
        return None
def kritere_gore_oneri_getir(user_inputs: Dict, conn) -> List[Dict]:
    suggestions: List[Dict] = []
    processed_criteria = set()
    normalized_inputs = {key: metni_normalize_et(value) for key, value in user_inputs.items()}

    print(f"Spesifik kriterlere göre öneriler aranıyor (normalize girdiler: {normalized_inputs}) - Önceliklendirme Sırası: Mood -> ... -> Free Time", file=sys.stderr)

    if normalized_inputs.get("mood") in ["mutsuz", "endiseli", "stresli"] and normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("free_time") == "1_saatten_az":
        if "mood_dusuk_living_yalniz_freetime_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_dusuk_living_yalniz_freetime_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_dusuk_living_yalniz_freetime_low")
    elif normalized_inputs.get("mood") in ["mutsuz", "endiseli", "stresli"] and normalized_inputs.get("living") in ["arkadaslarla", "aileyle"] and normalized_inputs.get("free_time") in ["2-4_saat", "4_saat_uzeri"]:
        if "mood_dusuk_living_others_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_dusuk_living_others_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_dusuk_living_others_freetime_high")
    elif normalized_inputs.get("mood") == "stresli" and normalized_inputs.get("age") == "25_ve_uzeri" and normalized_inputs.get("free_time") == "1_saatten_az":
        if "mood_stresli_yas_yetiskin_freetime_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_stresli_yas_yetiskin_freetime_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_stresli_yas_yetiskin_freetime_low")
    elif normalized_inputs.get("mood") == "mutsuz" and normalized_inputs.get("living") == "aileyle" and normalized_inputs.get("social_interaction") == "ice_donuk":
        if "mood_mutsuz_living_aile_social_ice" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_mutsuz_living_aile_social_ice")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_mutsuz_living_aile_social_ice")
    elif normalized_inputs.get("mood") == "endiseli" and normalized_inputs.get("health") == "evet" and normalized_inputs.get("medication") == "evet":
        if "mood_endiseli_health_medication" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_endiseli_health_medication")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_endiseli_health_medication")
    elif normalized_inputs.get("mood") == "mutsuz" and normalized_inputs.get("age") == "18-25":
        if "mood_mutsuz_yas_genc" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_mutsuz_yas_genc")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_mutsuz_yas_genc")
    elif normalized_inputs.get("mood") == "mutsuz" and normalized_inputs.get("age") == "25_ve_uzeri":
        if "mood_mutsuz_yas_yetiskin" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_mutsuz_yas_yetiskin")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_mutsuz_yas_yetiskin")
    elif normalized_inputs.get("mood") in ["mutsuz", "endiseli", "stresli"] and normalized_inputs.get("living") == "yalniz":
        if "mood_dusuk_living_yalniz" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_dusuk_living_yalniz")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_dusuk_living_yalniz")
    elif normalized_inputs.get("mood") in ["mutsuz", "endiseli", "stresli"] and normalized_inputs.get("living") in ["arkadaslarla", "aileyle"]:
        if "mood_dusuk_living_aile" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_dusuk_living_aile")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_dusuk_living_aile")
    elif normalized_inputs.get("mood") in ["mutsuz", "endiseli", "stresli"] and normalized_inputs.get("free_time") == "1_saatten_az":
        if "mood_dusuk_freetime_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_dusuk_freetime_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_dusuk_freetime_low")
    elif normalized_inputs.get("mood") in ["mutsuz", "endiseli", "stresli"] and normalized_inputs.get("free_time") in ["1-2_saat", "2-4_saat", "4_saat_uzeri"]:
        if "mood_dusuk_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_dusuk_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_dusuk_freetime_high")
    elif normalized_inputs.get("mood") == "endiseli" and normalized_inputs.get("health") == "evet":
        if "mood_endiseli_health_evet" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_endiseli_health_evet")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_endiseli_health_evet")
    elif normalized_inputs.get("mood") == "stresli" and normalized_inputs.get("free_time") in ["1-2_saat", "2-4_saat", "4_saat_uzeri"]:
        if "mood_stresli_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_stresli_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_stresli_freetime_high")
    elif normalized_inputs.get("mood") == "stresli" and normalized_inputs.get("social_interaction") == "ice_donuk":
        if "mood_stresli_social_ice" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_stresli_social_ice")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_stresli_social_ice")
    elif normalized_inputs.get("mood") in ["mutsuz", "endiseli", "stresli"] and normalized_inputs.get("health") == "evet":
        if "mood_dusuk_health_evet" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_dusuk_health_evet")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_dusuk_health_evet")
    elif normalized_inputs.get("mood") in ["mutsuz", "endiseli", "stresli"] and normalized_inputs.get("medication") == "evet":
        if "mood_dusuk_medication_evet" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_dusuk_medication_evet")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_dusuk_medication_evet")
    elif normalized_inputs.get("mood") == "stresli" and normalized_inputs.get("living") == "aileyle":
        if "mood_stresli_living_aile" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_stresli_living_aile")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_stresli_living_aile")
    elif normalized_inputs.get("mood") == "mutsuz" and normalized_inputs.get("social_interaction") == "disa_donuk":
        if "mood_mutsuz_social_disa" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_mutsuz_social_disa")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_mutsuz_social_disa")
    elif normalized_inputs.get("mood") == "mutsuz":
        if "mood_mutsuz_genel" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_mutsuz_genel")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_mutsuz_genel")
        elif "mood" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood")
    elif normalized_inputs.get("mood") == "endiseli":
        if "mood_endiseli_genel" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_endiseli_genel")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_endiseli_genel")
        elif "mood" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood")
    elif normalized_inputs.get("mood") == "stresli":
        if "mood_stresli_genel" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_stresli_genel")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_stresli_genel")
        elif "mood" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood")
    elif normalized_inputs.get("mood") == "mutlu":
        if "mood_mutlu" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_mutlu")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_mutlu")
    elif normalized_inputs.get("mood") == "diger":
        if "mood_diger" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_diger")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_diger")
    elif normalized_inputs.get("age") == "25_ve_uzeri" and normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("free_time") in ["2-4_saat", "4_saat_uzeri"]:
        if "yas_yetiskin_living_yalniz_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "yas_yetiskin_living_yalniz_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("yas_yetiskin_living_yalniz_freetime_high")
    elif normalized_inputs.get("age") == "18-25" and normalized_inputs.get("social_interaction") == "ice_donuk" and normalized_inputs.get("family_visits") == "hic":
        if "yas_genc_social_ice_family_hic" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "yas_genc_social_ice_family_hic")
            if oneri: suggestions.append(oneri); processed_criteria.add("yas_genc_social_ice_family_hic")
    elif normalized_inputs.get("age") == "18-25" and normalized_inputs.get("social_interaction") == "ice_donuk":
        if "yas_genc_ice_donuk_sosyal" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "yas_genc_ice_donuk_sosyal")
            if oneri: suggestions.append(oneri); processed_criteria.add("yas_genc_ice_donuk_sosyal")
    elif normalized_inputs.get("age") == "25_ve_uzeri" and normalized_inputs.get("living") == "yalniz":
        if "yas_yetiskin_yalniz_yasam" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "yas_yetiskin_yalniz_yasam")
            if oneri: suggestions.append(oneri); processed_criteria.add("yas_yetiskin_yalniz_yasam")
    elif normalized_inputs.get("age") == "18-25" and normalized_inputs.get("health") == "evet":
        if "yas_genc_saglik_evet" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "yas_genc_saglik_evet")
            if oneri: suggestions.append(oneri); processed_criteria.add("yas_genc_saglik_evet")
    elif normalized_inputs.get("age") == "25_ve_uzeri" and normalized_inputs.get("free_time") == "1_saatten_az":
        if "yas_yetiskin_freetime_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "yas_yetiskin_freetime_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("yas_yetiskin_freetime_low")
    elif normalized_inputs.get("age") == "18-25" and normalized_inputs.get("living") == "aileyle":
        if "yas_genc_living_aileyle" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "yas_genc_living_aileyle")
            if oneri: suggestions.append(oneri); processed_criteria.add("yas_genc_living_aileyle")
    elif normalized_inputs.get("age") == "25_ve_uzeri" and normalized_inputs.get("social_interaction") == "ice_donuk":
        if "yas_yetiskin_social_ice_donuk" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "yas_yetiskin_social_ice_donuk")
            if oneri: suggestions.append(oneri); processed_criteria.add("yas_yetiskin_social_ice_donuk")
    elif normalized_inputs.get("age") == "18-25" and normalized_inputs.get("freetime") in ["2-4_saat", "4_saat_uzeri"]:
        if "yas_genc_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "yas_genc_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("yas_genc_freetime_high")
    elif normalized_inputs.get("age") == "25_ve_uzeri" and normalized_inputs.get("family_visits") == "her_zamana":
        if "yas_yetiskin_family_her_zamana" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "yas_yetiskin_family_her_zamana")
            if oneri: suggestions.append(oneri); processed_criteria.add("yas_yetiskin_family_her_zamana")
    elif normalized_inputs.get("age") == "18-25" and normalized_inputs.get("living") == "arkadaslarla":
        if "living_arkadaslarla_yas_genc" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_arkadaslarla_yas_genc")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_arkadaslarla_yas_genc")
    elif normalized_inputs.get("age") == "25_ve_uzeri" and normalized_inputs.get("living") == "aileyle":
        if "living_aileyle_yas_yetiskin" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_aileyle_yas_yetiskin")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_aileyle_yas_yetiskin")
    elif normalized_inputs.get("age") == "18-25":
        if "age_18-25" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "age_18-25")
            if oneri: suggestions.append(oneri); processed_criteria.add("age_18-25")
    elif normalized_inputs.get("age") == "25_ve_uzeri":
        if "age_25_ve_uzeri_genel" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "age_25_ve_uzeri_genel")
            if oneri: suggestions.append(oneri); processed_criteria.add("age_25_ve_uzeri_genel")
    elif normalized_inputs.get("age") in ["18-25", "25_ve_uzeri"]: 
        if "age" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "age")
            if oneri: suggestions.append(oneri); processed_criteria.add("age")
    elif normalized_inputs.get("medication") == "evet" and normalized_inputs.get("health") == "evet" and normalized_inputs.get("mood") in ["mutsuz", "endiseli", "stresli"]:
        if "health_evet_medication_evet_mood_dusuk" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_medication_evet_mood_dusuk")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_medication_evet_mood_dusuk")
    elif normalized_inputs.get("medication") == "evet" and normalized_inputs.get("health") == "evet":
        if "health_evet_medication_evet" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_medication_evet")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_medication_evet")
    elif normalized_inputs.get("medication") == "sadece_destek_aldim" and normalized_inputs.get("health") == "evet":
        if "health_evet_medication_support" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_medication_support")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_medication_support")
    elif normalized_inputs.get("medication") == "evet" and normalized_inputs.get("living") == "yalniz":
        if "medication_evet_living_yalniz" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "medication_evet_living_yalniz")
            if oneri: suggestions.append(oneri); processed_criteria.add("medication_evet_living_yalniz")
    elif normalized_inputs.get("medication") == "evet" and normalized_inputs.get("free_time") == "1_saatten_az":
        if "medication_evet_freetime_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "medication_evet_freetime_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("medication_evet_freetime_low")
    elif normalized_inputs.get("medication") == "evet" and normalized_inputs.get("social_interaction") == "disa_donuk":
        if "medication_evet_social_disa_donuk" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "medication_evet_social_disa_donuk")
            if oneri: suggestions.append(oneri); processed_criteria.add("medication_evet_social_disa_donuk")
    elif normalized_inputs.get("medication") == "hayir" and normalized_inputs.get("health") == "evet":
        if "health_evet_medication_hayir" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_medication_hayir")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_medication_hayir")
    elif normalized_inputs.get("medication") == "evet":
        if "medication_evet_doktor_iletisim" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "medication_evet_doktor_iletisim")
            if oneri: suggestions.append(oneri); processed_criteria.add("medication_evet_doktor_iletisim")
        elif "medication" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "medication")
            if oneri: suggestions.append(oneri); processed_criteria.add("medication")
    elif normalized_inputs.get("medication") == "sadece_destek_aldim":
        if "medication_support_devam" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "medication_support_devam")
            if oneri: suggestions.append(oneri); processed_criteria.add("medication_support_devam")
        elif "medication_support" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "medication_support")
            if oneri: suggestions.append(oneri); processed_criteria.add("medication_support")
    elif normalized_inputs.get("medication") == "hayir":
        if "medication_hayir_saglikli_yasam" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "medication_hayir_saglikli_yasam")
            if oneri: suggestions.append(oneri); processed_criteria.add("medication_hayir_saglikli_yasam")
        elif "medication_hayir" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "medication_hayir")
            if oneri: suggestions.append(oneri); processed_criteria.add("medication_hayir")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("free_time") == "1_saatten_az":
        if "health_evet_living_yalniz_freetime_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_living_yalniz_freetime_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_living_yalniz_freetime_low")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("social_interaction") == "ice_donuk" and normalized_inputs.get("family_visits") == "hic":
        if "health_evet_social_ice_family_hic" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_social_ice_family_hic")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_social_ice_family_hic")
    elif normalized_inputs.get("health") == "hayir" and normalized_inputs.get("living") in ["arkadaslarla", "aileyle"] and normalized_inputs.get("freetime") in ["2-4_saat", "4_saat_uzeri"]:
        if "health_hayir_living_others_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_hayir_living_others_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_hayir_living_others_freetime_high")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("living") == "yalniz":
        if "health_evet_living_yalniz" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_living_yalniz")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_living_yalniz")
    elif normalized_inputs.get("health") == "hayir" and normalized_inputs.get("living") == "arkadaslarla":
        if "health_hayir_living_arkadaslarla" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_hayir_living_arkadaslarla")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_hayir_living_arkadaslarla")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("free_time") == "1_saatten_az":
        if "health_evet_freetime_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_freetime_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_freetime_low")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("social_interaction") == "ice_donuk":
        if "health_evet_social_ice" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_social_ice")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_social_ice")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("free_time") in ["2-4_saat", "4_saat_uzeri"]:
        if "health_evet_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_freetime_high")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("living") in ["arkadaslarla", "aileyle"]:
        if "health_evet_living_others" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_living_others")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_living_others")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("family_visits") != "her_zamana":
        if "health_evet_family_not_always" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_family_not_always")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_family_not_always")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("beslenme") == "kötü":
        if "health_evet_beslenme" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_beslenme")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_beslenme")
    elif normalized_inputs.get("health") == "hayir" and normalized_inputs.get("beslenme") == "iyi":
        if "health_hayir_beslenme_iyi" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_hayir_beslenme_iyi")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_hayir_beslenme_iyi")
    elif normalized_inputs.get("health") == "evet":
        if "health_evet_yonetim" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_yonetim")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_yonetim")
        elif "health_evet_spor" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_spor")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_spor")
        elif "health" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health")
            if oneri: suggestions.append(oneri); processed_criteria.add("health")
    elif normalized_inputs.get("health") == "hayir":
        if "health_hayir_spor_basla" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_hayir_spor_basla")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_hayir_spor_basla")
        elif "health_hayir_beslenme" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_hayir_beslenme")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_hayir_beslenme")
        elif "health_hayir" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_hayir")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_hayir")
    elif normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("social_interaction") == "ice_donuk" and normalized_inputs.get("family_visits") == "hic":
        if "living_yalniz_social_ice_family_hic" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_yalniz_social_ice_family_hic")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_yalniz_social_ice_family_hic")
    elif normalized_inputs.get("living") == "arkadaslarla" and normalized_inputs.get("freetime") in ["2-4_saat", "4_saat_uzeri"] and normalized_inputs.get("social_interaction") == "disa_donuk":
        if "living_arkadaslarla_freetime_high_social_disa" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_arkadaslarla_freetime_high_social_disa")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_arkadaslarla_freetime_high_social_disa")
    elif normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("family_visits") == "hic":
        if "living_yalniz_family_hic" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_yalniz_family_hic")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_yalniz_family_hic")
    elif normalized_inputs.get("living") == "arkadaslarla" and normalized_inputs.get("family_visits") == "bazen":
        if "living_arkadaslarla_family_bazen" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_arkadaslarla_family_bazen")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_arkadaslarla_family_bazen")
    elif normalized_inputs.get("living") == "aileyle" and normalized_inputs.get("family_visits") == "her_zamana":
        if "living_aileyle_family_her_zamana" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_aileyle_family_her_zamana")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_aileyle_family_her_zamana")
    elif normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("free_time") in ["2-4_saat", "4_saat_uzeri"]:
        if "living_yalniz_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_yalniz_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_yalniz_freetime_high")
    elif normalized_inputs.get("living") == "arkadaslarla" and normalized_inputs.get("free_time") in ["2-4_saat", "4_saat_uzeri"]:
        if "living_arkadaslarla_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_arkadaslarla_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_arkadaslarla_freetime_high")
    elif normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("social_interaction") == "ice_donuk":
        if "living_yalniz_social_ice" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_yalniz_social_ice")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_yalniz_social_ice")
    elif normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("freetime") == "1_saatten_az":
        if "living_yalniz_freetime_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_yalniz_freetime_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_yalniz_freetime_low")
    elif normalized_inputs.get("living") == "aileyle" and normalized_inputs.get("social_interaction") == "disa_donuk":
        if "living_aileyle_social_disa" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_aileyle_social_disa")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_aileyle_social_disa")
    elif normalized_inputs.get("living") == "yalniz":
        if "living_yalniz_aktivite" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_yalniz_aktivite")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_yalniz_aktivite")
        elif "living" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living")
            if oneri: suggestions.append(oneri); processed_criteria.add("living")
    elif normalized_inputs.get("living") == "arkadaslarla":
        if "living_arkadaslarla_sinir" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_arkadaslarla_sinir")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_arkadaslarla_sinir")
        elif "living_arkadaslarla" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_arkadaslarla")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_arkadaslarla")
    elif normalized_inputs.get("living") == "aileyle":
        if "living_aileyle_bireysellik" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_aileyle_bireysellik")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_aileyle_bireysellik")
        elif "living_aileyle_iletisim" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_aileyle_iletisim")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_aileyle_iletisim")
        elif "living_aileyle" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_aileyle")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_aileyle")
    elif normalized_inputs.get("social_interaction") == "ice_donuk" and normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("freetime") == "1_saatten_az":
        if "social_ice_living_yalniz_freetime_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_ice_living_yalniz_freetime_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_ice_living_yalniz_freetime_low")
    elif normalized_inputs.get("social_interaction") == "ice_donuk" and normalized_inputs.get("family_visits") == "hic":
        if "social_ice_donuk_family_hic" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_ice_donuk_family_hic")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_ice_donuk_family_hic")
    elif normalized_inputs.get("social_interaction") == "disa_donuk" and normalized_inputs.get("family_visits") == "her_zamana":
        if "social_disa_donuk_family_always" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_disa_donuk_family_always")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_disa_donuk_family_always")
    elif normalized_inputs.get("social_interaction") == "ice_donuk" and normalized_inputs.get("yas_genc") == "18-25":
        if "social_ice_donuk_yas_genc" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_ice_donuk_yas_genc")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_ice_donuk_yas_genc")
    elif normalized_inputs.get("social_interaction") == "disa_donuk" and normalized_inputs.get("yas_yetiskin") == "25_ve_uzeri":
        if "social_disa_donuk_yas_yetiskin" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_disa_donuk_yas_yetiskin")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_disa_donuk_yas_yetiskin")
    elif normalized_inputs.get("social_interaction") == "ice_donuk" and normalized_inputs.get("health") == "evet":
        if "health_evet_social_ice" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_social_ice")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_social_ice")
    elif normalized_inputs.get("social_interaction") == "disa_donuk" and normalized_inputs.get("freetime") in ["2-4_saat", "4_saat_uzeri"]:
        if "freetime_high_social_disa_donuk" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "freetime_high_social_disa_donuk")
            if oneri: suggestions.append(oneri); processed_criteria.add("freetime_high_social_disa_donuk")
    elif normalized_inputs.get("social_interaction") == "disa_donuk" and normalized_inputs.get("living") == "yalniz":
        if "social_disa_living_yalniz" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_disa_living_yalniz")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_disa_living_yalniz")
    elif normalized_inputs.get("social_interaction") == "ice_donuk":
        if "social_ice_donuk_kucuk_adim" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_ice_donuk_kucuk_adim")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_ice_donuk_kucuk_adim")
        elif "social_ice_donuk_konfor" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_ice_donuk_konfor")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_ice_donuk_konfor")
        elif "social_interaction" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_interaction")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_interaction")
    elif normalized_inputs.get("social_interaction") == "disa_donuk":
        if "social_disa_donuk_zaman_yonetimi" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_disa_donuk_zaman_yonetimi")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_disa_donuk_zaman_yonetimi")
        elif "social_interaction_disa_donuk" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_interaction_disa_donuk")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_interaction_disa_donuk")
    elif normalized_inputs.get("family_visits") == "hic" and normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("social_interaction") == "ice_donuk":
        if "family_hic_living_yalniz_social_ice" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_hic_living_yalniz_social_ice")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_hic_living_yalniz_social_ice")
    elif normalized_inputs.get("family_visits") == "hic" and normalized_inputs.get("yas_genc") == "18-25":
        if "family_hic_yas_genc" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_hic_yas_genc")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_hic_yas_genc")
    elif normalized_inputs.get("family_visits") == "her_zamana" and normalized_inputs.get("yas_yetiskin") == "25_ve_uzeri":
        if "family_her_zamana_yas_yetiskin" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_her_zamana_yas_yetiskin")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_her_zamana_yas_yetiskin")
    elif normalized_inputs.get("family_visits") == "bazen" and normalized_inputs.get("freetime") in ["2-4_saat", "4_saat_uzeri"]:
        if "family_bazen_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_bazen_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_bazen_freetime_high")
    elif normalized_inputs.get("family_visits") == "hic" and normalized_inputs.get("freetime") in ["2-4_saat", "4_saat_uzeri"]:
        if "family_hic_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_hic_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_hic_freetime_high")
    elif normalized_inputs.get("family_visits") == "her_zamana" and normalized_inputs.get("living") == "aileyle":
        if "living_aileyle_family_her_zamana" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_aileyle_family_her_zamana")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_aileyle_family_her_zamana")
    elif normalized_inputs.get("family_visits") == "hic":
        if "family_hic_iletisim_kurma" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_hic_iletisim_kurma")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_hic_iletisim_kurma")
        elif "family_visits_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_visits_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_visits_low")
        elif "family_visits" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_visits")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_visits")
    elif normalized_inputs.get("family_visits") == "her_zamana":
        if "family_her_zamana_destek_farkli" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_her_zamana_destek_farkli")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_her_zamana_destek_farkli")
        elif "family_visits_her_zamana" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_visits_her_zamana")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_visits_her_zamana")
    elif normalized_inputs.get("family_visits") == "bazen":
        if "family_bazen_kalite" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_bazen_kalite")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_bazen_kalite")
        elif "family_visits_bazen" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_visits_bazen")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_visits_bazen")
    elif normalized_inputs.get("free_time") == "1_saatten_az" and normalized_inputs.get("mood") in ["mutsuz", "endiseli", "stresli"] and normalized_inputs.get("living") == "yalniz":
        if "freetime_low_mood_dusuk_living_yalniz" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "freetime_low_mood_dusuk_living_yalniz")
            if oneri: suggestions.append(oneri); processed_criteria.add("freetime_low_mood_dusuk_living_yalniz")
    elif normalized_inputs.get("free_time") == "1_saatten_az" and normalized_inputs.get("social_interaction") == "ice_donuk":
        if "freetime_low_social_ice" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "freetime_low_social_ice")
            if oneri: suggestions.append(oneri); processed_criteria.add("freetime_low_social_ice")
    elif normalized_inputs.get("free_time") == "1_saatten_az" and normalized_inputs.get("mood") in ["mutsuz", "endiseli", "stresli"]:
        if "freetime_low_mood_dusuk" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "freetime_low_mood_dusuk")
            if oneri: suggestions.append(oneri); processed_criteria.add("freetime_low_mood_dusuk")
    elif normalized_inputs.get("free_time") == "1_saatten_az" and normalized_inputs.get("health") == "evet":
        if "freetime_low_health_evet" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "freetime_low_health_evet")
            if oneri: suggestions.append(oneri); processed_criteria.add("freetime_low_health_evet")
    elif normalized_inputs.get("free_time") in ["2-4_saat", "4_saat_uzeri"] and normalized_inputs.get("health") == "hayir":
        if "freetime_high_health_hayir" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "freetime_high_health_hayir")
            if oneri: suggestions.append(oneri); processed_criteria.add("freetime_high_health_hayir")
    elif normalized_inputs.get("free_time") == "1_saatten_az":
        if "free_time_low_oncelik" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "free_time_low_oncelik")
            if oneri: suggestions.append(oneri); processed_criteria.add("free_time_low_oncelik")
        elif "free_time_low_kisa_mola" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "free_time_low_kisa_mola")
            if oneri: suggestions.append(oneri); processed_criteria.add("free_time_low_kisa_mola")
        elif "free_time_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "free_time_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("free_time_low")
        elif "free_time" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "free_time")
            if oneri: suggestions.append(oneri); processed_criteria.add("free_time")
    elif normalized_inputs.get("free_time") == "1-2_saat":
        if "free_time_medium_cesitlilik" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "free_time_medium_cesitlilik")
            if oneri: suggestions.append(oneri); processed_criteria.add("free_time_medium_cesitlilik")
        elif "free_time_medium" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "free_time_medium")
            if oneri: suggestions.append(oneri); processed_criteria.add("free_time_medium")

    elif normalized_inputs.get("free_time") in ["2-4_saat", "4_saat_uzeri"]:
        if "free_time_high_yeni_sey" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "free_time_high_yeni_sey")
            if oneri: suggestions.append(oneri); processed_criteria.add("free_time_high_yeni_sey")
        elif "free_time_high_dusunme" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "free_time_high_dusunme")
            if oneri: suggestions.append(oneri); processed_criteria.add("free_time_high_dusunme")
        elif "free_time_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "free_time_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("free_time_high")
    elif normalized_inputs.get("mood") in ["mutsuz", "endiseli", "stresli"] and normalized_inputs.get("health") == "evet":
        if "mood_dusuk_health_evet" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_dusuk_health_evet")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_dusuk_health_evet")
    elif normalized_inputs.get("mood") in ["mutsuz", "endiseli", "stresli"] and normalized_inputs.get("medication") == "evet":
        if "mood_dusuk_medication_evet" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_dusuk_medication_evet")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_dusuk_medication_evet")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("living") in ["arkadaslarla", "aileyle"]:
        if "health_evet_living_others" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_living_others")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_living_others")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("family_visits") != "her_zamana": # Sağlık sorunu ve aileyle iletişimde eksiklik/yokluk
        if "health_evet_family_not_always" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_family_not_always")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_family_not_always")
    elif normalized_inputs.get("medication") == "evet" and normalized_inputs.get("living") == "yalniz":
        if "medication_evet_living_yalniz" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "medication_evet_living_yalniz")
            if oneri: suggestions.append(oneri); processed_criteria.add("medication_evet_living_yalniz")
    elif normalized_inputs.get("medication") == "evet" and normalized_inputs.get("freetime") == "1_saatten_az":
        if "medication_evet_freetime_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "medication_evet_freetime_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("medication_evet_freetime_low")
    elif normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("social_interaction") == "ice_donuk":
        if "living_yalniz_social_ice" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_yalniz_social_ice")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_yalniz_social_ice")
    elif normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("freetime") == "1_saatten_az":
        if "living_yalniz_freetime_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_yalniz_freetime_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_yalniz_freetime_low")
    elif normalized_inputs.get("living") == "arkadaslarla" and normalized_inputs.get("freetime") in ["2-4_saat", "4_saat_uzeri"]:
        if "living_arkadaslarla_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_arkadaslarla_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_arkadaslarla_freetime_high")
    elif normalized_inputs.get("social_interaction") == "ice_donuk" and normalized_inputs.get("family_visits") == "hic":
        if "social_ice_donuk_family_hic" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_ice_donuk_family_hic")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_ice_donuk_family_hic")
    elif normalized_inputs.get("social_interaction") == "disa_donuk" and normalized_inputs.get("family_visits") == "her_zamana":
        if "social_disa_donuk_family_always" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_disa_donuk_family_always")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_disa_donuk_family_always")
    elif normalized_inputs.get("family_visits") == "bazen" and normalized_inputs.get("freetime") in ["2-4_saat", "4_saat_uzeri"]:
        if "family_bazen_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_bazen_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_bazen_freetime_high")
    elif normalized_inputs.get("family_visits") == "hic" and normalized_inputs.get("freetime") in ["2-4_saat", "4_saat_uzeri"]:
        if "family_hic_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_hic_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_hic_freetime_high")
    elif normalized_inputs.get("mood") in ["mutsuz", "endiseli", "stresli"] and normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("free_time") == "1_saatten_az":
        if "mood_dusuk_living_yalniz_freetime_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_dusuk_living_yalniz_freetime_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_dusuk_living_yalniz_freetime_low")
    elif normalized_inputs.get("mood") in ["mutsuz", "endiseli", "stresli"] and normalized_inputs.get("living") in ["arkadaslarla", "aileyle"] and normalized_inputs.get("free_time") in ["2-4_saat", "4_saat_uzeri"]:
        if "mood_dusuk_living_others_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_dusuk_living_others_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_dusuk_living_others_freetime_high")
    elif normalized_inputs.get("mood") == "stresli" and normalized_inputs.get("age") == "25_ve_uzeri" and normalized_inputs.get("free_time") == "1_saatten_az":
        if "mood_stresli_yas_yetiskin_freetime_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_stresli_yas_yetiskin_freetime_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_stresli_yas_yetiskin_freetime_low")
    elif normalized_inputs.get("mood") == "mutsuz" and normalized_inputs.get("living") == "aileyle" and normalized_inputs.get("social_interaction") == "ice_donuk":
        if "mood_mutsuz_living_aile_social_ice" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_mutsuz_living_aile_social_ice")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_mutsuz_living_aile_social_ice")
    elif normalized_inputs.get("mood") == "endiseli" and normalized_inputs.get("health") == "evet" and normalized_inputs.get("medication") == "evet":
        if "mood_endiseli_health_medication" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "mood_endiseli_health_medication")
            if oneri: suggestions.append(oneri); processed_criteria.add("mood_endiseli_health_medication")
    elif normalized_inputs.get("age") == "25_ve_uzeri" and normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("free_time") in ["2-4_saat", "4_saat_uzeri"]:
        if "yas_yetiskin_living_yalniz_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "yas_yetiskin_living_yalniz_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("yas_yetiskin_living_yalniz_freetime_high")
    elif normalized_inputs.get("age") == "18-25" and normalized_inputs.get("social_interaction") == "ice_donuk" and normalized_inputs.get("family_visits") == "hic":
        if "yas_genc_social_ice_family_hic" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "yas_genc_social_ice_family_hic")
            if oneri: suggestions.append(oneri); processed_criteria.add("yas_genc_social_ice_family_hic")
    elif normalized_inputs.get("medication") == "evet" and normalized_inputs.get("health") == "evet" and normalized_inputs.get("mood") in ["mutsuz", "endiseli", "stresli"]:
        if "health_evet_medication_evet_mood_dusuk" not in processed_criteria: 
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_medication_evet_mood_dusuk")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_medication_evet_mood_dusuk")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("free_time") == "1_saatten_az":
        if "health_evet_living_yalniz_freetime_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_living_yalniz_freetime_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_living_yalniz_freetime_low")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("social_interaction") == "ice_donuk" and normalized_inputs.get("family_visits") == "hic":
        if "health_evet_social_ice_family_hic" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_social_ice_family_hic")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_social_ice_family_hic")
    elif normalized_inputs.get("health") == "hayir" and normalized_inputs.get("living") in ["arkadaslarla", "aileyle"] and normalized_inputs.get("freetime") in ["2-4_saat", "4_saat_uzeri"]:
        if "health_hayir_living_others_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_hayir_living_others_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_hayir_living_others_freetime_high")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("social_interaction") == "disa_donuk" and normalized_inputs.get("freetime") == "1_saatten_az":
        if "health_evet_social_disa_freetime_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_social_disa_freetime_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_social_disa_freetime_low")
    elif normalized_inputs.get("health") == "hayir" and normalized_inputs.get("family_visits") == "hic" and normalized_inputs.get("freetime") in ["2-4_saat", "4_saat_uzeri"]:
        if "health_hayir_family_hic_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_hayir_family_hic_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_hayir_family_hic_freetime_high")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("living") == "yalniz":
        if "health_evet_living_yalniz" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_living_yalniz")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_living_yalniz")
    elif normalized_inputs.get("health") == "hayir" and normalized_inputs.get("living") == "arkadaslarla":
        if "health_hayir_living_arkadaslarla" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_hayir_living_arkadaslarla")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_hayir_living_arkadaslarla")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("free_time") == "1_saatten_az":
        if "health_evet_freetime_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_freetime_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_freetime_low")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("social_interaction") == "ice_donuk":
        if "health_evet_social_ice" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_social_ice")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_social_ice")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("free_time") in ["2-4_saat", "4_saat_uzeri"]:
        if "health_evet_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_freetime_high")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("living") in ["arkadaslarla", "aileyle"]:
        if "health_evet_living_others" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_living_others")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_living_others")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("family_visits") != "her_zamana":
        if "health_evet_family_not_always" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_family_not_always")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_family_not_always")
    elif normalized_inputs.get("health") == "evet" and normalized_inputs.get("beslenme") == "kötü":
        if "health_evet_beslenme" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_beslenme")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_beslenme")
    elif normalized_inputs.get("health") == "hayir" and normalized_inputs.get("beslenme") == "iyi":
        if "health_hayir_beslenme_iyi" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_hayir_beslenme_iyi")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_hayir_beslenme_iyi")
    elif normalized_inputs.get("health") == "evet":
        if "health_evet_yonetim" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_yonetim")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_yonetim")
        elif "health_evet_spor" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_spor")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_spor")
        elif "health" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health")
            if oneri: suggestions.append(oneri); processed_criteria.add("health")
    elif normalized_inputs.get("health") == "hayir":
        if "health_hayir_spor_basla" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_hayir_spor_basla")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_hayir_spor_basla")
        elif "health_hayir_beslenme" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_hayir_beslenme")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_hayir_beslenme")
        elif "health_hayir" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_hayir")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_hayir")
    elif normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("social_interaction") == "ice_donuk" and normalized_inputs.get("family_visits") == "hic":
        if "living_yalniz_social_ice_family_hic" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_yalniz_social_ice_family_hic")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_yalniz_social_ice_family_hic")
    elif normalized_inputs.get("living") == "arkadaslarla" and normalized_inputs.get("freetime") in ["2-4_saat", "4_saat_uzeri"] and normalized_inputs.get("social_interaction") == "disa_donuk":
        if "living_arkadaslarla_freetime_high_social_disa" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_arkadaslarla_freetime_high_social_disa")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_arkadaslarla_freetime_high_social_disa")
    elif normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("family_visits") == "hic":
        if "living_yalniz_family_hic" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_yalniz_family_hic")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_yalniz_family_hic")
    elif normalized_inputs.get("living") == "arkadaslarla" and normalized_inputs.get("family_visits") == "bazen":
        if "living_arkadaslarla_family_bazen" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_arkadaslarla_family_bazen")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_arkadaslarla_family_bazen")
    elif normalized_inputs.get("living") == "aileyle" and normalized_inputs.get("family_visits") == "her_zamana":
        if "living_aileyle_family_her_zamana" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_aileyle_family_her_zamana")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_aileyle_family_her_zamana")
    elif normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("free_time") in ["2-4_saat", "4_saat_uzeri"]:
        if "living_yalniz_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_yalniz_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_yalniz_freetime_high")
    elif normalized_inputs.get("living") == "arkadaslarla" and normalized_inputs.get("free_time") in ["2-4_saat", "4_saat_uzeri"]:
        if "living_arkadaslarla_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_arkadaslarla_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_arkadaslarla_freetime_high")
    elif normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("social_interaction") == "ice_donuk":
        if "living_yalniz_social_ice" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_yalniz_social_ice")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_yalniz_social_ice")
    elif normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("freetime") == "1_saatten_az":
        if "living_yalniz_freetime_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_yalniz_freetime_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_yalniz_freetime_low")
    elif normalized_inputs.get("living") == "aileyle" and normalized_inputs.get("social_interaction") == "disa_donuk":
        if "living_aileyle_social_disa" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_aileyle_social_disa")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_aileyle_social_disa")
    elif normalized_inputs.get("living") == "yalniz":
        if "living_yalniz_aktivite" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_yalniz_aktivite")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_yalniz_aktivite")
        elif "living" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living")
            if oneri: suggestions.append(oneri); processed_criteria.add("living")
    elif normalized_inputs.get("living") == "arkadaslarla":
        if "living_arkadaslarla_sinir" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_arkadaslarla_sinir")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_arkadaslarla_sinir")
        elif "living_arkadaslarla" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_arkadaslarla")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_arkadaslarla")
    elif normalized_inputs.get("living") == "aileyle":
        if "living_aileyle_bireysellik" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_aileyle_bireysellik")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_aileyle_bireysellik")
        elif "living_aileyle_iletisim" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_aileyle_iletisim")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_aileyle_iletisim")
        elif "living_aileyle" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_aileyle")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_aileyle")
    elif normalized_inputs.get("social_interaction") == "ice_donuk" and normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("freetime") == "1_saatten_az":
        if "social_ice_living_yalniz_freetime_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_ice_living_yalniz_freetime_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_ice_living_yalniz_freetime_low")
    elif normalized_inputs.get("social_interaction") == "ice_donuk" and normalized_inputs.get("family_visits") == "hic":
        if "social_ice_donuk_family_hic" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_ice_donuk_family_hic")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_ice_donuk_family_hic")
    elif normalized_inputs.get("social_interaction") == "disa_donuk" and normalized_inputs.get("family_visits") == "her_zamana":
        if "social_disa_donuk_family_always" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_disa_donuk_family_always")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_disa_donuk_family_always")
    elif normalized_inputs.get("social_interaction") == "ice_donuk" and normalized_inputs.get("yas_genc") == "18-25":
        if "social_ice_donuk_yas_genc" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_ice_donuk_yas_genc")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_ice_donuk_yas_genc")
    elif normalized_inputs.get("social_interaction") == "disa_donuk" and normalized_inputs.get("yas_yetiskin") == "25_ve_uzeri":
        if "social_disa_donuk_yas_yetiskin" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_disa_donuk_yas_yetiskin")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_disa_donuk_yas_yetiskin")
    elif normalized_inputs.get("social_interaction") == "ice_donuk" and normalized_inputs.get("health") == "evet":
        if "health_evet_social_ice" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "health_evet_social_ice")
            if oneri: suggestions.append(oneri); processed_criteria.add("health_evet_social_ice")
    elif normalized_inputs.get("social_interaction") == "disa_donuk" and normalized_inputs.get("freetime") in ["2-4_saat", "4_saat_uzeri"]:
        if "freetime_high_social_disa_donuk" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "freetime_high_social_disa_donuk")
            if oneri: suggestions.append(oneri); processed_criteria.add("freetime_high_social_disa_donuk")
    elif normalized_inputs.get("social_interaction") == "disa_donuk" and normalized_inputs.get("living") == "yalniz":
        if "social_disa_living_yalniz" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_disa_living_yalniz")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_disa_living_yalniz")
    elif normalized_inputs.get("social_interaction") == "ice_donuk":
        if "social_ice_donuk_kucuk_adim" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_ice_donuk_kucuk_adim")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_ice_donuk_kucuk_adim")
        elif "social_ice_donuk_konfor" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_ice_donuk_konfor")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_ice_donuk_konfor")
        elif "social_interaction" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_interaction")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_interaction")
    elif normalized_inputs.get("social_interaction") == "disa_donuk":
        if "social_disa_donuk_zaman_yonetimi" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_disa_donuk_zaman_yonetimi")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_disa_donuk_zaman_yonetimi")
        elif "social_interaction_disa_donuk" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "social_interaction_disa_donuk")
            if oneri: suggestions.append(oneri); processed_criteria.add("social_interaction_disa_donuk")
    elif normalized_inputs.get("family_visits") == "hic" and normalized_inputs.get("living") == "yalniz" and normalized_inputs.get("social_interaction") == "ice_donuk":
        if "family_hic_living_yalniz_social_ice" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_hic_living_yalniz_social_ice")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_hic_living_yalniz_social_ice")
    elif normalized_inputs.get("family_visits") == "hic" and normalized_inputs.get("yas_genc") == "18-25":
        if "family_hic_yas_genc" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_hic_yas_genc")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_hic_yas_genc")
    elif normalized_inputs.get("family_visits") == "her_zamana" and normalized_inputs.get("yas_yetiskin") == "25_ve_uzeri":
        if "family_her_zamana_yas_yetiskin" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_her_zamana_yas_yetiskin")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_her_zamana_yas_yetiskin")
    elif normalized_inputs.get("family_visits") == "bazen" and normalized_inputs.get("freetime") in ["2-4_saat", "4_saat_uzeri"]:
        if "family_bazen_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_bazen_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_bazen_freetime_high")
    elif normalized_inputs.get("family_visits") == "hic" and normalized_inputs.get("freetime") in ["2-4_saat", "4_saat_uzeri"]:
        if "family_hic_freetime_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_hic_freetime_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_hic_freetime_high")
    elif normalized_inputs.get("family_visits") == "her_zamana" and normalized_inputs.get("living") == "aileyle":
        if "living_aileyle_family_her_zamana" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "living_aileyle_family_her_zamana")
            if oneri: suggestions.append(oneri); processed_criteria.add("living_aileyle_family_her_zamana")
    elif normalized_inputs.get("family_visits") == "hic":
        if "family_hic_iletisim_kurma" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_hic_iletisim_kurma")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_hic_iletisim_kurma")
        elif "family_visits_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_visits_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_visits_low")
        elif "family_visits" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_visits")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_visits")
    elif normalized_inputs.get("family_visits") == "her_zamana":
        if "family_her_zamana_destek_farkli" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_her_zamana_destek_farkli")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_her_zamana_destek_farkli")
        elif "family_visits_her_zamana" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_visits_her_zamana")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_visits_her_zamana")
    elif normalized_inputs.get("family_visits") == "bazen":
        if "family_bazen_kalite" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_bazen_kalite")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_bazen_kalite")
        elif "family_visits_bazen" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "family_visits_bazen")
            if oneri: suggestions.append(oneri); processed_criteria.add("family_visits_bazen")
    elif normalized_inputs.get("free_time") == "1_saatten_az" and normalized_inputs.get("mood") in ["mutsuz", "endiseli", "stresli"] and normalized_inputs.get("living") == "yalniz":
        if "freetime_low_mood_dusuk_living_yalniz" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "freetime_low_mood_dusuk_living_yalniz")
            if oneri: suggestions.append(oneri); processed_criteria.add("freetime_low_mood_dusuk_living_yalniz")
    elif normalized_inputs.get("free_time") == "1_saatten_az" and normalized_inputs.get("social_interaction") == "ice_donuk":
        if "freetime_low_social_ice" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "freetime_low_social_ice")
            if oneri: suggestions.append(oneri); processed_criteria.add("freetime_low_social_ice")
    elif normalized_inputs.get("free_time") == "1_saatten_az" and normalized_inputs.get("mood") in ["mutsuz", "endiseli", "stresli"]:
        if "freetime_low_mood_dusuk" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "freetime_low_mood_dusuk")
            if oneri: suggestions.append(oneri); processed_criteria.add("freetime_low_mood_dusuk")
    elif normalized_inputs.get("free_time") == "1_saatten_az" and normalized_inputs.get("health") == "evet":
        if "freetime_low_health_evet" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "freetime_low_health_evet")
            if oneri: suggestions.append(oneri); processed_criteria.add("freetime_low_health_evet")
    elif normalized_inputs.get("free_time") in ["2-4_saat", "4_saat_uzeri"] and normalized_inputs.get("health") == "hayir":
        if "freetime_high_health_hayir" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "freetime_high_health_hayir")
            if oneri: suggestions.append(oneri); processed_criteria.add("freetime_high_health_hayir")
    elif normalized_inputs.get("free_time") == "1_saatten_az":
        if "free_time_low_oncelik" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "free_time_low_oncelik")
            if oneri: suggestions.append(oneri); processed_criteria.add("free_time_low_oncelik")
        elif "free_time_low_kisa_mola" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "free_time_low_kisa_mola")
            if oneri: suggestions.append(oneri); processed_criteria.add("free_time_low_kisa_mola")
        elif "free_time_low" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "free_time_low")
            if oneri: suggestions.append(oneri); processed_criteria.add("free_time_low")
        elif "free_time" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "free_time")
            if oneri: suggestions.append(oneri); processed_criteria.add("free_time")
    elif normalized_inputs.get("free_time") == "1-2_saat":
        if "free_time_medium_cesitlilik" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "free_time_medium_cesitlilik")
            if oneri: suggestions.append(oneri); processed_criteria.add("free_time_medium_cesitlilik")
        elif "free_time_medium" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "free_time_medium")
            if oneri: suggestions.append(oneri); processed_criteria.add("free_time_medium")
    elif normalized_inputs.get("free_time") in ["2-4_saat", "4_saat_uzeri"]:
        if "free_time_high_yeni_sey" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "free_time_high_yeni_sey")
            if oneri: suggestions.append(oneri); processed_criteria.add("free_time_high_yeni_sey")
        elif "free_time_high_dusunme" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "free_time_high_dusunme")
            if oneri: suggestions.append(oneri); processed_criteria.add("free_time_high_dusunme")
        elif "free_time_high" not in processed_criteria:
            oneri = fetch_oneri_from_db_by_kriter(conn, "free_time_high")
            if oneri: suggestions.append(oneri); processed_criteria.add("free_time_high")
    return suggestions

def rastgele_oneri_getir(conn) -> Optional[Dict[str, Any]]:
    """Rastgele 'random_pool' kriterinden bir öneri alır"""
    try:
        imlec = conn.cursor(dictionary=True)
        sql = (
            "SELECT oneri_metni AS text, aciklama AS aciklama "
            "FROM oneriler WHERE kriter = 'random_pool' ORDER BY RAND() LIMIT 1"
        )
        imlec.execute(sql)
        satir = imlec.fetchone()
        imlec.close()
        if satir:
            return {"text": satir['text'], "aciklama": satir['aciklama']}
    except Exception as e:
        print(f"rastgele_oneri_getir hatası: {e}", file=sys.stderr)
    return None

def main():
    # Girdiler phpdeki inputlar ile eşleşmeli
    alanlar = ['mood','age','medication','health','living','social_interaction','family_visits','free_time']
    if len(sys.argv) != len(alanlar) + 1:
        # Argüman sayısı alanlar listesinin boyutundan 1 fazla olmalı (script adı dahil)
        hata = {"error": "Yanlış argüman sayısı", "details": f"Beklenen {len(alanlar)} girdi, gelen {len(sys.argv)-1}. Lütfen tüm alanları doldurun."}
        print(json.dumps(hata, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    # sys.argv[0] script adıdır, sys.argv[1:] gerçek argümanlardır.
    girdiler = dict(zip(alanlar, sys.argv[1:]))
    print(f"Alınan girdiler: {girdiler}", file=sys.stderr) 

    conn = None
    try:
        # Veritabanı bağlantısı
        conn = mysql.connector.connect(**DB_CONFIG)
        print("Veritabanı bağlantısı başarılı.", file=sys.stderr) 
        spesifik_oneriler = kritere_gore_oneri_getir(girdiler, conn)

        if spesifik_oneriler:
            sonuc = spesifik_oneriler
            print(f"Spesifik öneri bulundu: {len(sonuc)} adet.", file=sys.stderr)
        else:
            print("Spesifik öneri bulunamadı, rastgele aranıyor.", file=sys.stderr)
            rnd = rastgele_oneri_getir(conn)
            if rnd:
                # Rastgele öneri bulunduysa onu kullan
                sonuc = [rnd]
                print("Rastgele öneri bulundu.", file=sys.stderr)
            else:
                # Ne spesifik ne de rastgele öneri bulunamadıysa genel bir mesaj döndür
                sonuc = [{
                    "text": "Girdiğiniz bilgilere uyan özel bir öneri bulunamadı.",
                    "aciklama": "Lütfen farklı kombinasyonlarla tekrar deneyin veya genel önerilere göz atın."
                }]
                print("Ne spesifik ne de rastgele öneri bulunamadı.", file=sys.stderr)

    except mysql.connector.Error as e:
        print(f"Veritabanı bağlantı veya sorgu hatası: {e}", file=sys.stderr)
        sonuc = [{"text": "Veritabanı hatası", "aciklama": str(e) + ". Lütfen veritabanı ayarlarını kontrol edin."}]
    except Exception as e:
        print(f"Genel hata oluştu: {e}", file=sys.stderr)
        sonuc = [{"text": "Beklenmedik bir hata oluştu", "aciklama": str(e)}]
    finally:
        # Veritabanı bağlantısını kapatıyoruz
        if conn is not None and conn.is_connected():
            conn.close()
            print("Veritabanı bağlantısı kapatıldı.", file=sys.stderr) 
    print(json.dumps(sonuc, ensure_ascii=False))

if __name__ == '__main__':
    main()