# -*- coding: utf-8 -*-
import traceback
import logging
from selenium.common import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from urllib.parse import urljoin

from dotenv import load_dotenv

from random import randint
import time
import os
import logging
import requests


load_dotenv()



SEARCH_BTN = '//*[@id="frmQuickSearch"]/div[3]/div[2]/button'
INPUT_OGRN = '//div[@class = "u3-field__input"]/input'
DIV_BTN = '/html/body/main/section[2]/div/div/div[2]/div/div/div[2]/div[2]/div[1]/div'

proxy_username = os.getenv('PROXY_USERNAME')
proxy_password = os.getenv('PROXY_PASSWORD')
proxy_port = os.getenv('PROXY_PORT')


def get_proxy_ip():
    with open('../../Proxies.txt', 'r') as file:
        data = file.read().split()
        return data[randint(0, len(data)-1)]


def create_browser():
    proxy_ip = get_proxy_ip()
    print(f'using {proxy_ip}')
    proxy_options = {
        'proxy': {
            'https': f'http://{proxy_username}:{proxy_password}@{proxy_ip}:{proxy_port}'
        }
    }
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    browser = webdriver.Chrome(seleniumwire_options=proxy_options, options=chrome_options)
    browser.set_window_size(1280, 11000)
    #browser.get('chrome://settings/')
    #browser.execute_script('chrome.settingsPrivate.setDefaultZoom(0.25);')

    return browser


def get_wait(browser):
    return WebDriverWait(browser, 60)

def enter_ogrn(browser, OGRN, INPUT_OGRN):
    input_field = browser.find_element(By.XPATH, INPUT_OGRN)

    input_field.clear()

    input_field.send_keys(OGRN)


def to_click(btn, browser):
    find_button = browser.find_element(By.XPATH, btn)

    # Нажатие на кнопку
    find_button.click()


def get_info_ogrn(browser, wait, ogrn):
    data = {}
    try:
        browser.get(f'https://pb.nalog.ru/search.html#t=1718002842355&mode=search-all&queryAll={ogrn}&page=1&pageSize=10')
        enter_ogrn(browser, ogrn, INPUT_OGRN)
        to_click(DIV_BTN, browser)
        wait.until(
            EC.visibility_of_all_elements_located(
                (By.XPATH, '//*[@id="pnlCompanyLeftCol"]/div[3]/div/div[2]/a')))

        labels_and_xpaths = {
            "status": "//span[@class='pb-subject-status pb-subject-status--active']",
            "inn": "//*[contains(text(), 'ИНН:')]/following-sibling::*[1]",
            "short_name": "//*[contains(text(), 'Сокращенное наименование:')]/following-sibling::*[1]",
            "full_name": "//*[contains(text(), 'Полное наименование:')]/following-sibling::*[1]",
            "kpp": "//*[contains(text(), 'КПП:')]/following-sibling::*[1]",
            "address": "//*[contains(text(), 'Адрес организации:')]/following-sibling::*[1]",
            "registration_date": "//*[contains(text(), 'Дата регистрации:')]/following-sibling::*[1]",
            "okved": "//*[contains(text(), 'Основной вид деятельности (ОКВЭД):')]/following-sibling::*[1]",
            "ogrn": "//*[contains(text(), 'ОГРН:')]/following-sibling::*[1]"
        }

        for key, xpath in labels_and_xpaths.items():
            element = browser.find_element(By.XPATH, xpath)
            data[key] = element.text

        boss_label = browser.find_element(By.XPATH,
                                          "//*[contains(text(), 'Сведения о лице, имеющем право без доверенности действовать от имени юридического лица')]")
        boss_name_number = boss_label.find_element(By.XPATH,
                                                   ".//following::div[@class='pb-company-field-value']/span[@class='font-weight-bold']")
        data["boss_name"] = boss_name_number.text
        boss_post_element = boss_label.find_element(By.XPATH,
                                                    ".//following::div[@class='pb-company-field-name' and contains(text(), 'Должность руководителя:')]/following-sibling::div[@class='pb-company-field-value']")
        data["boss_post"] = boss_post_element.text
    except Exception as e:
        print(f"Exception occurred: {e}")
        return None
    return data


def scrape_ogrn_info(ogrn):
    max_retries = 3
    retry_delay = 5
    data = None

    for attempt in range(max_retries):
        try:
            browser = create_browser()
            wait = get_wait(browser)
            data = get_info_ogrn(browser, wait, ogrn)
            if data:
                break  # Если успешно, выйти из цикла
        except Exception as e:
            print(f"Exception in main: {e}")
        finally:
            browser.quit()

        if attempt < max_retries - 1:
            print(f"Retrying in {retry_delay} seconds... ({attempt + 1}/{max_retries})")
            time.sleep(retry_delay)
        else:
            print("Failed to retrieve info after multiple attempts.")
    return data
