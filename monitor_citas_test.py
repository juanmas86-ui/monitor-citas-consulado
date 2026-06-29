#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import smtplib
from datetime import datetime, timedelta
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
HEARTBEAT_HORAS = 12
HEARTBEAT_FILE = '/tmp/last_heartbeat.txt'
SCREENSHOTS_DIR = './screenshots'

def log(mensaje):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] {mensaje}', flush=True)

def crear_directorio_screenshots():
    """Crea el directorio para screenshots si no existe"""
    if not os.path.exists(SCREENSHOTS_DIR):
        os.makedirs(SCREENSHOTS_DIR)
        log(f'📁 Directorio {SCREENSHOTS_DIR} creado')

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

def deberia_enviar_heartbeat():
    """Verifica si deben pasar 12 horas desde el último heartbeat"""
    if not os.path.exists(HEARTBEAT_FILE):
        return True
    
    try:
        with open(HEARTBEAT_FILE, 'r') as f:
            last_time_str = f.read().strip()
        last_time = datetime.fromisoformat(last_time_str)
        ahora = datetime.now()
        
        if (ahora - last_time) >= timedelta(hours=HEARTBEAT_HORAS):
            return True
    except:
        return True
    
    return False

def guardar_heartbeat():
    """Guarda el timestamp del último heartbeat"""
    try:
        with open(HEARTBEAT_FILE, 'w') as f:
            f.write(datetime.now().isoformat())
        log('💾 Heartbeat guardado')
    except Exception as e:
        log(f'⚠️  No se pudo guardar heartbeat: {e}')

def enviar_heartbeat():
    """Envía email de confirmación de que el script está funcionando"""
    ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    asunto = '✅ Monitor de Citas - Sistema Funcionando Correctamente'
    cuerpo = f"""Hola Juan,

Tu monitor de citas del Consulado de España está funcionando correctamente.

Estado: ✅ ACTIVO
Última verificación: {ahora}
Intervalo de chequeos: {INTERVALO_MINUTOS} minutos
Email: {EMAIL_TO}

El script sigue monitoreando la disponibilidad de citas. 
Cuando encuentre citas, recibirás una alerta inmediata.

Próximo aviso de estado: en {HEARTBEAT_HORAS} horas

---
Monitor de Citas - Consulado España Córdoba
"""
    
    if enviar_email(asunto, cuerpo):
        guardar_heartbeat()
        log(f'💚 HEARTBEAT: Confirmación de funcionamiento enviada')
        return True
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
        crear_directorio_screenshots()
        
        log('🔄 Abriendo navegador...')
        driver = abrir_navegador()
        if not driver:
            return False
        
        log('🌐 Navegando a la página...')
        driver.set_page_load_timeout(30)
        try:
            driver.get(BOOKITIT_URL)
        except:
            log('⚠️  Timeout en navegación')
        
        log('⏳ Esperando 2.10 minutos para Cloudflare...')
        time.sleep(130)
        log('✅ Cloudflare completado')
        
        # SCREENSHOT 1: Después de Cloudflare
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot1 = f'{SCREENSHOTS_DIR}/01_despues_cloudflare_{timestamp}.png'
        driver.save_screenshot(screenshot1)
        log(f'📸 Screenshot 1 guardado')
        
        # ACEPTAR ALERT
        log('🔘 Aceptando ALERT (Welcome / Bienvenido)...')
        try:
            alert = driver.switch_to.alert
            alert.accept()
            log('   ✅ ALERT aceptado')
            time.sleep(2)
        except Exception as e:
            log(f'   ⚠️  No hay ALERT o error: {str(e)[:50]}')
        
        # SCREENSHOT 2: Después de aceptar alert
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot2 = f'{SCREENSHOTS_DIR}/02_despues_alert_{timestamp}.png'
        driver.save_screenshot(screenshot2)
        log(f'📸 Screenshot 2 guardado')
        
        log('🔘 Clickeando botón Continuar (verde)...')
        try:
            xpath = "//button[contains(text(), 'Continuar')] | //button[contains(text(), 'Continue')]"
            btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            btn.click()
            log('   ✅ Botón Continuar clickeado')
            time.sleep(3)
        except Exception as e:
            log(f'   ⚠️  Botón Continuar no encontrado: {str(e)[:50]}')
        
        # SCREENSHOT 3: Después de continuar
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot3 = f'{SCREENSHOTS_DIR}/03_despues_continuar_{timestamp}.png'
        driver.save_screenshot(screenshot3)
        log(f'📸 Screenshot 3 guardado')
        
        log('⏳ Esperando 5 segundos para que cargue calendario...')
        time.sleep(5)
        
        # SCREENSHOT 4: Antes de analizar
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot4 = f'{SCREENSHOTS_DIR}/04_antes_analizar_{timestamp}.png'
        driver.save_screenshot(screenshot4)
        log(f'📸 Screenshot 4 guardado')
        
        log('🔍 Analizando disponibilidad...')
        html = driver.page_source
        
        # Sin citas DEFINITIVO
        sin_citas = [
            'No hay horas disponibles',
            'no available',
            'no appointments',
        ]
        
        if any(texto.lower() in html.lower() for texto in sin_citas):
            log('❌ Sin citas disponibles')
            return False
        
        # Con citas: buscar indicadores
        con_citas = [
            '08:', '09:', '10:', '11:', '12:', '13:', '14:', '15:', '16:', '17:',
            'timeSlot', 'available', 'disponible',
        ]
        
        if any(texto in html for texto in con_citas):
            log('✅ ¡¡HAY CITAS DISPONIBLES!!')
            return True
        
        log('❌ Sin citas detectadas')
        return False
        
    except Exception as e:
        log(f'❌ Error: {e}')
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def monitorear():
    log('=' * 70)
    log('MONITOR DE CITAS - CONSULADO ESPAÑA CÓRDOBA')
    log(f'Email: {EMAIL_TO}')
    log(f'Heartbeat cada: {HEARTBEAT_HORAS} horas')
    log(f'Screenshots: {SCREENSHOTS_DIR}/')
    log('=' * 70)
    
    # Chequear si necesita enviar heartbeat al iniciar
    if deberia_enviar_heartbeat():
        log('\n💚 Enviando heartbeat de inicio...')
        enviar_heartbeat()
    
    primer_chequeo = True
    
    while True:
        try:
            log('\n🔍 CHEQUEANDO DISPONIBILIDAD...')
            hay_citas = chequear_disponibilidad()
            
            if hay_citas:
                log('\n📧 Enviando email de CITAS DISPONIBLES...')
                enviar_email('🚨 ¡CITAS DISPONIBLES! Consulado España - Córdoba', f'Entra acá: {BOOKITIT_URL}')
                guardar_heartbeat()
                log('=' * 70)
                log('✅ CITAS ENCONTRADAS')
                log('=' * 70)
                break
            
            # Chequear si es hora del heartbeat
            if deberia_enviar_heartbeat():
                log('\n💚 Es hora del HEARTBEAT (cada 12 horas)')
                enviar_heartbeat()
            
            if not primer_chequeo:
                log(f'\n⏰ Próximo chequeo en {INTERVALO_MINUTOS} minutos')
                time.sleep(INTERVALO_MINUTOS * 60)
            
            primer_chequeo = False
            
        except KeyboardInterrupt:
            log('\n⏹️  Script detenido')
            break
        except Exception as e:
            log(f'❌ Error: {e}')
            time.sleep(INTERVALO_MINUTOS * 60)

if __name__ == '__main__':
    monitorear()
