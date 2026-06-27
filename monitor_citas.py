#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

BOOKITIT_URL = 'https://www.citaconsular.es/es/hosteds/widgetdefault/2517d2c8d726687ab7f770d8c3c4a7c7f'
EMAIL_TO = 'juanmas86@gmail.com'
EMAIL_FROM = 'juanmas86@gmail.com'
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')

def log(mensaje):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] {mensaje}', flush=True)

def enviar_email(asunto, cuerpo):
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_FROM, GMAIL_PASSWORD)
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        msg['Subject'] = asunto
        msg.attach(MIMEText(cuerpo, 'plain'))
        server.send_message(msg)
        server.quit()
        log('✅ Email enviado correctamente')
        return True
    except Exception as e:
        log(f'❌ Error al enviar email: {e}')
        return False

def abrir_navegador():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        log(f'❌ Error al abrir navegador: {e}')
        return None

def chequear_disponibilidad():
    driver = None
    try:
        log('🔄 Abriendo navegador...')
        driver = abrir_navegador()
        if not driver:
            return False
        
        log('🌐 Navegando a la página...')
        driver.set_page_load_timeout(30)
        try:
            driver.get(BOOKITIT_URL)
        except:
            log('⚠️  Timeout en navegación, continuando')
        
        log('⏳ Esperando 15 segundos para que cargue JavaScript...')
        time.sleep(15)
        
        log('🔘 Intentando clickear Aceptar...')
        try:
            btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))
            )
            btn.click()
            log('   ✅ Botón Aceptar clickeado')
            time.sleep(2)
        except:
            log('   ⚠️  Botón Aceptar no encontrado')
        
        log('🔘 Buscando botón Continuar (90 segundos)...')
        boton_encontrado = False
        tiempo_inicio = time.time()
        
        while time.time() - tiempo_inicio < 90:
            try:
                xpath = "//button[contains(text(), 'Continuar')] | //button[contains(text(), 'Continue')]"
                botones = driver.find_elements(By.XPATH, xpath)
                for btn in botones:
                    if btn.is_displayed():
                        log('   ✅ ¡Botón Continuar encontrado! Clickeando...')
                        driver.execute_script("arguments[0].click();", btn)
                        boton_encontrado = True
                        time.sleep(3)
                        break
                if boton_encontrado:
                    break
            except:
                pass
            
            time.sleep(2)
        
        if not boton_encontrado:
            log('   ⚠️  Botón Continuar no encontrado después de 90 segundos')
        
        log('🔍 Analizando disponibilidad...')
        time.sleep(3)
        html = driver.page_source
        
        # Criterios POSITIVOS (debe contener alguno de estos)
        indicadores_citas = [
            'timeSlots',           # Bookitit típicamente usa timeSlots
            'Available',           # Horarios disponibles en inglés
            'Disponible',          # Horarios disponibles en español
            'appointment',         # Cita disponible
            'cita',                # Cita en español
            '08:',                 # Hora específica
            '09:',
            '10:',
            '11:',
            '12:',
            '13:',
            '14:',
            '15:',
            '16:',
            '17:',
        ]
        
        # Criterios NEGATIVOS (indica definitivamente que NO hay)
        indicadores_sin_citas = [
            'No hay horas disponibles',
            'no available',
            'sin disponibilidad',
            'No appointments available',
            'Currently unavailable',
        ]
        
        # Primero: verificar definitivamente que NO hay
        tiene_negativo = any(texto in html for texto in indicadores_sin_citas)
        if tiene_negativo:
            log('❌ Página confirma: NO HAY CITAS')
            return False
        
        # Segundo: buscar indicadores positivos
        tiene_positivo = any(texto in html for texto in indicadores_citas)
        
        if tiene_positivo:
            log('✅ ¡¡HAY CITAS DISPONIBLES!!')
            return True
        else:
            log('⚠️  Página no contiene indicadores claros (probablemente sin citas)')
            return False
        
    except Exception as e:
        log(f'❌ Error general: {e}')
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def main():
    log('=' * 70)
    log('MONITOR DE CITAS - CONSULADO ESPAÑA CÓRDOBA')
    log(f'Email: {EMAIL_TO}')
    log('=' * 70)
    
    try:
        log('\n🔍 CHEQUEANDO DISPONIBILIDAD...')
        hay_citas = chequear_disponibilidad()
        
        if hay_citas:
            log('\n📧 ¡¡ENVIANDO EMAIL DE ALERTA!!')
            enviar_email(
                '🚨 ¡¡CITAS DISPONIBLES!! Consulado España - Córdoba',
                f'¡¡HAY CITAS DISPONIBLES EN EL CONSULADO!!\n\nEntra urgente:\n{BOOKITIT_URL}'
            )
            log('=' * 70)
            log('✅ ¡¡CITAS ENCONTRADAS!! EMAIL ENVIADO')
            log('=' * 70)
        else:
            log('\n❌ Sin citas en este momento')
        
    except Exception as e:
        log(f'❌ Error en main: {e}')

if __name__ == '__main__':
    main()
