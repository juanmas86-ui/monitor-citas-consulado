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
INTERVALO_MINUTOS = 5

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
        log('✅ Email enviado')
        return True
    except Exception as e:
        log(f'❌ Error email: {e}')
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
        
        log('⏳ Paso 1: Esperando 2.10 minutos para Cloudflare...')
        time.sleep(130)
        log('✅ Cloudflare completado')
        
        log('🔘 Paso 2: Intentando clickear Aceptar...')
        try:
            btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))
            )
            btn.click()
            log('   ✅ Botón Aceptar clickeado')
            time.sleep(2)
        except Exception as e:
            log(f'   ⚠️  Botón Aceptar no encontrado: {str(e)[:40]}')
        
        log('🔘 Paso 3: Monitoreando por botón Continuar (hasta 1 minuto)...')
        boton_encontrado = False
        tiempo_inicio = time.time()
        timeout_busqueda = 60
        
        while time.time() - tiempo_inicio < timeout_busqueda:
            try:
                xpath = "//button[contains(text(), 'Continuar')] | //button[contains(text(), 'Continue')]"
                btn = driver.find_element(By.XPATH, xpath)
                if btn.is_displayed():
                    log('   ✅ ¡Botón Continuar encontrado! Clickeando...')
                    btn.click()
                    boton_encontrado = True
                    time.sleep(3)
                    break
            except:
                pass
            
            time.sleep(1)
        
        if not boton_encontrado:
            log('   ⚠️  Botón no encontrado en 1 minuto, continuando')
        
        log('🔍 Paso 4: Analizando disponibilidad...')
        time.sleep(2)
        html = driver.page_source
        
        # CRITERIOS NEGATIVOS: Definitivamente sin citas
        sin_citas_textos = [
            'No hay horas disponibles',
            'no available',
            'sin disponibilidad',
            'No appointments',
            'Currently unavailable',
            'no hay citas',
        ]
        
        tiene_sin_citas = any(texto.lower() in html.lower() for texto in sin_citas_textos)
        if tiene_sin_citas:
            log('❌ Sin citas disponibles (confirmado)')
            return False
        
        # CRITERIOS POSITIVOS: Hay citas disponibles
        con_citas_textos = [
            '08:',
            '09:',
            '10:',
            '11:',
            '12:',
            '13:',
            '14:',
            '15:',
            '16:',
            '17:',
            'timeSlots',
            'available',
            'disponible',
            'appointment',
        ]
        
        tiene_con_citas = any(texto in html for texto in con_citas_textos)
        
        if tiene_con_citas:
            log('✅ ¡¡HAY CITAS DISPONIBLES!!')
            return True
        else:
            log('❌ Sin citas detectadas (página incompleta o sin disponibilidad)')
            return False
        
    except Exception as e:
        log(f'❌ Error general: {e}')
        return False
    finally:
        if driver:
            log('🔒 Cerrando navegador')
            try:
                driver.quit()
            except:
                pass

def monitorear():
    log('=' * 70)
    log('MONITOR DE CITAS - CONSULADO ESPAÑA CÓRDOBA')
    log(f'Email: {EMAIL_TO}')
    log(f'Intervalo: {INTERVALO_MINUTOS} minutos')
    log('=' * 70)
    
    primer_chequeo = True
    
    while True:
        try:
            log('\n🔍 CHEQUEANDO DISPONIBILIDAD...')
            hay_citas = chequear_disponibilidad()
            
            if hay_citas:
                log('\n📧 Enviando email de alerta...')
                enviar_email('🚨 ¡CITAS DISPONIBLES! Consulado España - Córdoba', f'Entra acá: {BOOKITIT_URL}')
                log('\n' + '=' * 70)
                log('✅ CITAS ENCONTRADAS - SCRIPT PAUSADO')
                log('=' * 70)
                break
            
            if not primer_chequeo:
                log(f'\n⏰ Próximo chequeo en {INTERVALO_MINUTOS} minutos')
                time.sleep(INTERVALO_MINUTOS * 60)
            
            primer_chequeo = False
            
        except KeyboardInterrupt:
            log('\n⏹️  Script detenido por usuario')
            break
        except Exception as e:
            log(f'❌ Error en loop principal: {e}')
            log(f'⏰ Reintentando en {INTERVALO_MINUTOS} minutos')
            time.sleep(INTERVALO_MINUTOS * 60)

if __name__ == '__main__':
    monitorear()
