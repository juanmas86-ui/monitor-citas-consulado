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

def deberia_enviar_heartbeat():
    if not os.path.exists(HEARTBEAT_FILE):
        return True
    try:
        with open(HEARTBEAT_FILE, 'r') as f:
            last_time_str = f.read().strip()
        last_time = datetime.fromisoformat(last_time_str)
        if (datetime.now() - last_time) >= timedelta(hours=HEARTBEAT_HORAS):
            return True
    except:
        return True
    return False

def guardar_heartbeat():
    try:
        with open(HEARTBEAT_FILE, 'w') as f:
            f.write(datetime.now().isoformat())
    except:
        pass

def enviar_heartbeat():
    ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    asunto = '✅ Monitor de Citas - Sistema Funcionando'
    cuerpo = f'Monitor activo a las {ahora}. Sin citas aún.'
    if enviar_email(asunto, cuerpo):
        guardar_heartbeat()
        log('💚 Heartbeat enviado')

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
        log(f'❌ Error navegador: {e}')
        return None

def chequear_disponibilidad():
    driver = None
    try:
        log('🔄 Abriendo navegador...')
        driver = abrir_navegador()
        if not driver:
            return False
        
        log('🌐 Navegando...')
        driver.set_page_load_timeout(30)
        try:
            driver.get(BOOKITIT_URL)
        except:
            pass
        
        log('⏳ Esperando 2.10 minutos para Cloudflare...')
        time.sleep(130)
        log('✅ Cloudflare completado')
        
        # ACEPTAR ALERT
        log('🔔 Aceptando ALERT (Welcome)...')
        try:
            alert = driver.switch_to.alert
            alert.accept()
            log('✅ ALERT ACEPTADO CORRECTAMENTE')
            time.sleep(2)
        except Exception as e:
            log(f'❌ Error al aceptar alert: {str(e)[:60]}')
            return False
        
        # CLICKEAR CONTINUAR
        log('🔘 Clickeando botón CONTINUAR (verde)...')
        try:
            xpath = "//button[contains(text(), 'Continuar')] | //button[contains(text(), 'Continue')]"
            btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            btn.click()
            log('✅ BOTÓN CONTINUAR CLICKEADO CORRECTAMENTE')
            time.sleep(3)
        except Exception as e:
            log(f'❌ Error al clickear continuar: {str(e)[:60]}')
            return False
        
        # ESPERAR Y ANALIZAR
        log('⏳ Esperando 5 segundos para que cargue...')
        time.sleep(5)
        log('🔍 Analizando página...')
        
        html = driver.page_source
        
        # Verificar sin citas
        if 'No hay horas disponibles' in html:
            log('❌ SIN CITAS DISPONIBLES')
            return False
        
        # Verificar con citas
        horarios = ['08:', '09:', '10:', '11:', '12:', '13:', '14:', '15:', '16:', '17:']
        if any(h in html for h in horarios):
            log('✅ ¡¡HAY CITAS DISPONIBLES!!')
            return True
        
        log('❌ Sin citas detectadas')
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

def monitorear():
    log('=' * 70)
    log('MONITOR DE CITAS - CONSULADO ESPAÑA')
    log('=' * 70)
    
    if deberia_enviar_heartbeat():
        enviar_heartbeat()
    
    primer_chequeo = True
    
    while True:
        try:
            log('\n🔍 CHEQUEANDO DISPONIBILIDAD...')
            hay_citas = chequear_disponibilidad()
            
            if hay_citas:
                log('\n📧 ENVIANDO EMAIL...')
                enviar_email('🚨 ¡CITAS DISPONIBLES! Consulado', f'Entra: {BOOKITIT_URL}')
                guardar_heartbeat()
                break
            
            if debiera_enviar_heartbeat():
                enviar_heartbeat()
            
            if not primer_chequeo:
                log(f'⏰ Próximo en {INTERVALO_MINUTOS} min')
                time.sleep(INTERVALO_MINUTOS * 60)
            
            primer_chequeo = False
            
        except KeyboardInterrupt:
            log('⏹️  Detenido')
            break
        except Exception as e:
            log(f'❌ Error: {e}')
            time.sleep(INTERVALO_MINUTOS * 60)

if __name__ == '__main__':
    monitorear()
