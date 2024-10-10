import asyncio
from playwright.async_api import async_playwright, expect
import PSWMTR as psw   # файл с паролем, сид фразой и путь до манифеста

DEFAULT_DELAY = 300
page_url = 'https://app.meteora.ag/'
jup_swap_url = 'https://jup.ag/'

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            '',
            headless=False,
            args=[
                f'--disable-extensions-except={psw.SOLFLARE_EXTENSION_PATH}',
                f'--load-extension={psw.SOLFLARE_EXTENSION_PATH}',
                '--disable-blink-features=AutomationControlled',
            ],
        )


        titles = [await p.title() for p in context.pages]
        while 'Solflare' not in titles:
            titles = [await p.title() for p in context.pages]

        # Логинимся в кошельке

        mm_page = context.pages[1]
        await mm_page.wait_for_load_state()
        await asyncio.sleep(5)
        await mm_page.locator('//*[@id="root"]/div/div[2]/div/div[2]/div[2]/button').click()  # Уже есть кошелёк

        for i in range(len(psw.seed)):
            await mm_page.locator(f'//*[@id="mnemonic-input-{i}"]').fill(psw.seed[i])  # перебор полей для seed

        print('Залогинились в кошельке')

        await mm_page.locator('//*[@id="root"]/div/div[2]/div/div[2]/form/div[2]/button[2]').click()   # кнопка далее
        await asyncio.sleep(3)
        # -------------------- ввести пароль --------------------
        passwd_1 = mm_page.locator('//*[@id=":r1:"]')     # Введите пароль
        passwd_2 = mm_page.locator('//*[@id=":r2:"]')     # Повторите пароль
        checkbox = mm_page.locator('//*[@id="root"]/div/div[2]/div/div[2]/form/div[2]/button[2]')  # Продолжить
        await expect(passwd_1).to_be_attached()
        await passwd_1.fill(psw.MM_PASSWORD)
        await passwd_2.fill(psw.MM_PASSWORD)
        await checkbox.click()

        # -------------------- подтвердить секретную фразу --------------------
        await mm_page.locator('//*[@id="root"]/div/div[2]/div/div[2]/div[2]/div/button[1]').click()  # Импортировтать
        await mm_page.locator('//*[@id="root"]/div/div[1]/div[2]/div[2]/button/span').click()        # Продолжить
        await mm_page.locator('//*[@id="root"]/div/div[2]/div/div[2]/button[2]/span').click()        # Вход


        # -------------------- Идём на другую страницу --------------------
        mm_page_0 = context.pages[0]

           Идём на юпитер и конектим кошелёк
        async def ballance_wallet(page):
            await page.bring_to_front()
            await page.goto(jup_swap_url)
            walconect = page.locator('//*[@id="__next"]/div[2]/div[1]/div/div[4]/div[3]/div/button[2]/div/span[2]')   # Подключить кошелёк
            await walconect.click()
            butnconect = page.get_by_text('Solflare')
            await butnconect.click()
            await asyncio.sleep(4)
            pages = page.context.pages
            solflare_page = None
            for p in pages:
                if 'confirm_popup.html' in p.url:
                    solflare_page = p
                    break
            if solflare_page:
                await solflare_page.bring_to_front()
                await solflare_page.locator('//html/body/div[2]/div[2]/div/div[3]/div/button[2]').click()   # Подтвердить
            else:
                print("Не удалось найти всплывающее окно solflare.")
            await asyncio.sleep(5)
            # Проверяем баланс соланы
            token_1 = page.locator('//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div[1]/div['
                                   '1]/div[2]/div/button/div[2]')  # первое поле для токена
            await token_1.click()
            await page.locator('//*[@id="__next"]/div[3]/div[1]/div/div/div[1]/input').fill('Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB')    # первое поле для токена вводится адрес usdt
            await page.locator('//*[@id="__next"]/div[3]/div[1]/div/div/div[4]/div/div/div/li/div[2]/div[2]/div[1]').click()                   # клик по usdt
            token_2 = page.locator('//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div[1]/div['
                                   '3]/div[2]/div/button/div[2]')  # второе поле для токена
            await token_2.click()
            await page.locator('//*[@id="__next"]/div[3]/div[1]/div/div/div[1]/input').fill('So11111111111111111111111111111111111111112')     # во второе поле для токена вводится адрес sol
            await page.locator('//*[@id="__next"]/div[3]/div[1]/div/div/div[4]/div/div/div/li/div[2]/div[2]/div[1]').click()                   # клик по sol

            ballance_sol_1 =await page.locator('//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div['
                                               '1]/div[3]/div[1]/div/div[2]/span[1]').inner_text()  # Парсим баланс sol
            ballance_sol = (float(ballance_sol_1.replace(',','.')))

            ballance_usdt_1 = await page.locator(
                '//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div[1]/div[1]/div[1]/div/div['
                '1]/div[2]/span[1]').inner_text()                    # Парсим баланс usdt
            ballance_usdt = (float(ballance_usdt_1.replace(',', '.')))

            print(ballance_sol)
            print(ballance_usdt)
            # Если соланы меньше 0.09 и usdt > 2, то докупаем sol на 2$
            if ballance_sol < 0.09 and ballance_usdt > 2:
                await page.locator('//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div[1]/div['
                                   '1]/div[2]/span/div/input').fill('2')
                but_swp = page.locator('//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div[4]/button')
                await expect(but_swp).to_be_visible()
                await but_swp.click()
                await asyncio.sleep(3)
                pages = page.context.pages
                solflare_page = None
                for p in pages:
                    if 'confirm_popup.html' in p.url:
                        solflare_page = p
                        break
                if solflare_page:
                    await solflare_page.bring_to_front()
                    await asyncio.sleep(3)
                    await solflare_page.locator('//html/body/div[2]/div[2]/div/div[2]/div/div[2]/div[2]/div[2]/button[2]').click()   # Подтвердить транзу
                else:
                    print("Не удалось найти всплывающее окно solflare.")
                await asyncio.sleep(5)

            # Проверяем баланс jlp

            token_1 = page.locator(
                '//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div[1]/div[1]/div[2]/div/button/div[2]')
            await token_1.click()
            await page.locator('//*[@id="__next"]/div[3]/div[1]/div/div/div[1]/input').fill(
                'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB')
            await page.locator(
                '//*[@id="__next"]/div[3]/div[1]/div/div/div[4]/div/div/div/li/div[2]/div[2]/div[1]').click()
            token_2 = page.locator(
                '//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div[1]/div[3]/div[2]/div/button/div[2]')
            await token_2.click()
            await page.locator('//*[@id="__next"]/div[3]/div[1]/div/div/div[1]/input').fill(
                '27G8MtK7VtTcCHkpASjSDdkWWYfoqT6ggEuKidVJidD4')
            await page.locator(
                '//*[@id="__next"]/div[3]/div[1]/div/div/div[4]/div/div/div/li/div[2]/div[2]/div[1]').click()

            ballance_jlp_1 =  page.locator(
                '//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div[1]/div[3]/div[1]/div/div[2]/span[1]')
            ballance_jlp_2 = await ballance_jlp_1.inner_text()
            ballance_jlp = (float(ballance_jlp_2.replace(',', '.')))
            print(ballance_jlp)

            # Если jlp меньше 5 и usdt > 2, то докупаем jlp на 2$

            if ballance_jlp < 5 and ballance_usdt > 2:
                await page.locator(
                    '//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div[1]/div[1]/div['
                    '2]/span/div/input').fill('2')
                butn_swp = page.locator('//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div[4]/button')
                await expect(butn_swp).to_be_visible()
                await butn_swp.click()
                await asyncio.sleep(3)
                pages = page.context.pages
                solflare_page = None
                for p in pages:
                    if 'confirm_popup.html' in p.url:
                        solflare_page = p
                        break
                if solflare_page:
                    await solflare_page.bring_to_front()
                    await asyncio.sleep(3)
                    await solflare_page.locator(
                        '//html/body/div[2]/div[2]/div/div[2]/div/div[2]/div[2]/div[2]/button[2]').click(click_count=2)  # Кнопка подтверждения транзы
                else:
                    print("Не удалось найти всплывающее окно solflare.")
                await asyncio.sleep(5)

        page = mm_page_0
        await ballance_wallet(page)


        # Идём на метеору и Подключаем кошелёк
        page3 = await context.new_page()
        await page3.wait_for_load_state()
        async def connect_wallet(page):
            await page.bring_to_front()
            await page.goto(page_url)
            await asyncio.sleep(10)
            await page.locator('//button[contains(@class, "bg-[#191C32]")]').click()   # кнопка подключить кошелёк
            await asyncio.sleep(5)
            await page.locator('//span[@class ="css-1wq1rs1" and text()="Solflare"]').click()  # Выбираем Solflare
            await asyncio.sleep(5)

            # Ждем всплывающее окно Solflare и подтверждаем подключение
            await asyncio.sleep(3)
            pages = page.context.pages
            solflare_page = None
            for p in pages:
                if 'confirm_popup.html' in p.url:
                    solflare_page = p
                    break
            if solflare_page:
                await solflare_page.bring_to_front()
                await asyncio.sleep(4)
                yes_button = solflare_page.locator('//html/body/div[2]/div[2]/div/div[3]/div/button[2]')
                await expect(yes_button).to_be_visible(timeout=20000)
                await yes_button.click(click_count=2)
                await asyncio.sleep(2)
                # await solflare_page.close()
            else:
                print("Не удалось найти всплывающее окно solflare.")
            await asyncio.sleep(3)


        await connect_wallet(page3)


        # ТЕСТОВАЯ работа с сайтом, поиск пула
        inputs = page3.locator('//*[@id="__next"]/div[1]/div[5]/div/div[2]/div[2]/div/div[1]/div/div/input')
        await expect(inputs.first).to_be_visible(timeout=20000)
        await inputs.first.type('jlp', delay=DEFAULT_DELAY)
        await asyncio.sleep(2)
        try:
            inputs2 = page3.get_by_text('JLP-USDT', exact=True)
            await expect(inputs2.first).to_be_visible()
            await inputs2.first.scroll_into_view_if_needed()
            await inputs2.first.click()
        except Exception as e:
            print(f'Искомой пары нет: {e}')
            await context.close()
        await page3.locator('//*[@id="__next"]/div[1]/div[5]/div/div[2]/div[2]/div/div[4]/div/div[1]/div/div/div['
                                '3]/div[2]/div/a[1]').click()                          # Первый пул
        await page3.locator('//*[@id="__next"]/div[1]/div[5]/div/div[2]/div/div[2]/div[2]/div[1]/div[1]/div[2]/span').click()  # Кнопка создать позицию
        await page3.locator('//*[@id="__next"]/div[1]/div[5]/div/div[2]/div/div[2]/div[2]/div[2]/form/div['
                                  '1]/div[1]/div/div/button').click()                  # Отключить auto_fill
        await page3.locator('//*[@id="__next"]/div[1]/div[5]/div/div[2]/div/div[2]/div[2]/div[2]/form/div['
                                    '1]/div[2]/div[1]/div[2]/div[2]/div[2]').click()   # Клик на ввод max jlp
        max_price = page3.locator('//*[@id="__next"]/div[1]/div[5]/div/div[2]/div/div[2]/div[2]/div[2]/form/div['
                                  '3]/div[2]/div/div[3]/div[2]/div/input[2]')  # Максимальный процент
        await max_price.click(click_count=2)
        await max_price.press('Backspace')
        await max_price.fill('2.5')
        await asyncio.sleep(5)
        min_price = page3.locator('//*[@id="__next"]/div[1]/div[5]/div/div[2]/div/div[2]/div[2]/div[2]/form/div['
                                  '3]/div[2]/div/div[3]/div[1]/div/input[2]')          # Минимальный процент
        await min_price.click()
        await asyncio.sleep(1)
        for i in range(6):
            await min_price.press('Backspace')
        await min_price.type('0', delay=DEFAULT_DELAY)
        await asyncio.sleep(5)
        await page3.locator('//*[@id="__next"]/div[1]/div[5]/div/div[2]/div/div[2]/div[2]/div[2]/form/div[3]/div[2]/div/div[4]/div[1]').click()   #Проверка сколько транзакций
        await asyncio.sleep(4)
        await page3.locator('//*[@id="__next"]/div[1]/div[5]/div/div[2]/div/div[2]/div[2]/div[2]/form/button').click()  # Клик на кнопку создать ликвидность
        await asyncio.sleep(2)
        pages = page3.context.pages
        solflare_page = None
        for p in pages:
            if 'confirm_popup.html' in p.url:
                solflare_page = p
                break
        if solflare_page:
            await solflare_page.bring_to_front()
            yes_button = solflare_page.locator(
                '//html/body/div[2]/div[2]/div/div[2]/div/div[2]/div[2]/div[2]/button[2]')  # Кнопка подтверждения транзы
            await expect(yes_button).to_be_visible()
            await yes_button.click(click_count=2)
        else:
            print("Не удалось найти всплывающее окно solflare.")
        await asyncio.sleep(30)

        # Закрываем позицию
        close_pos = page3.get_by_text('USDT per JLP')
        await expect(close_pos.first).to_be_visible(timeout=20000)
        await close_pos.first.click()  # Раскрываем позицию
        await asyncio.sleep(10)
        widrought_btn = page3.locator('//*[@id="radix-:r0:"]/div[2]/div[1]/div/div[2]')   # Раздел вывода ликвидности
        await expect(widrought_btn).to_be_attached(timeout=20000)
        await widrought_btn.click()
        await asyncio.sleep(3)
        await page3.locator('//*[@id="radix-:r0:"]/div[2]/div[2]/form/div[3]/div/button').click()    # Кнопка закрыть позицию
        await asyncio.sleep(2)
        pages = page3.context.pages
        solflare_page = None
        for p in pages:
            if 'confirm_popup.html' in p.url:
                solflare_page = p
                break
        if solflare_page:
            await solflare_page.bring_to_front()
            yes_button = solflare_page.locator(
                '//html/body/div[2]/div[2]/div/div[2]/div/div[2]/div[2]/div[2]/button[2]')  # Кнопка подтверждения транзы
            await expect(yes_button).to_be_visible(timeout=20000)
            await yes_button.click(click_count=2)
        else:
            print("Не удалось найти всплывающее окно solflare.")
        await asyncio.sleep(10)



        print('ОК!!!')
        await asyncio.sleep(5555555)
        await context.close()
if __name__ == '__main__':
    asyncio.run(main())


