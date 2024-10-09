import asyncio
from playwright.async_api import async_playwright, expect
import PSWMTR as psw   # Библиотека с паролем, сид фразой и путь до манифеста

DEFAULT_DELAY = 300
page_url = 'https://app.meteora.ag/'
swap_url = 'https://jup.ag/'

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            '',
            headless=False,
            args=[
                f'--disable-extensions-except={psw.METAMASK_EXTENSION_PATH}',
                f'--load-extension={psw.METAMASK_EXTENSION_PATH}',
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

        my_wallet_btn = mm_page.locator('//*[@id="root"]/div/div[2]/div/div[2]/div[2]/button')  # Уже есть кошелёк
        await my_wallet_btn.click()


        for i in range(len(psw.seed)):

            await mm_page.locator(f'//*[@id="mnemonic-input-{i}"]').fill(psw.seed[i])  # перебор полей для seed
        print('Залогинились в кошельке')

        continue_btn = mm_page.locator('//*[@id="root"]/div/div[2]/div/div[2]/form/div[2]/button[2]')   # кнопка далее
        await continue_btn.click()
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
        seed_field = mm_page.locator('//*[@id="root"]/div/div[2]/div/div[2]/div[2]/div/button[1]')  # Импортировтать
        await seed_field.click()
        seed_field2 = mm_page.locator('//*[@id="root"]/div/div[1]/div[2]/div[2]/button/span')       # Продолжить
        await seed_field2.click()
        seed_field3 = mm_page.locator('//*[@id="root"]/div/div[2]/div/div[2]/button[2]/span')       # Вход
        await seed_field3.click()



        # -------------------- Идём на другую страницу --------------------
        mm_page_0 = context.pages[0]

        await asyncio.sleep(5)


        # Идём на юпитер и конектим кошелёк
        async def ballance_wallet(page):
            await page.bring_to_front()
            await page.goto(swap_url)
            walconect = page.locator('//*[@id="__next"]/div[2]/div[1]/div/div[4]/div[3]/div/button[2]/div/span[2]')   # Подключить кошелёк
            await walconect.click()
            butnconect = page.get_by_text('Solflare')
            await butnconect.click()
            await asyncio.sleep(4)
            pages = page.context.pages
            solflare_popup = None
            for p in pages:
                if 'confirm_popup.html' in p.url and p.url != page.url:
                    solflare_popup = p
                    break
            if solflare_popup:
                await solflare_popup.bring_to_front()
                conect_jup = solflare_popup.locator('//html/body/div[2]/div[2]/div/div[3]/div/button[2]')   # Подтвердить
                await conect_jup.click()
            else:
                print("Не удалось найти всплывающее окно solflare.")
            await asyncio.sleep(5)


            # Проверяем баланс соланы

            token_1 = page.locator('//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div[1]/div[1]/div[2]/div/button/div[2]')  # первое поле для токена
            await token_1.click()
            await page.locator('//*[@id="__next"]/div[3]/div[1]/div/div/div[1]/input').fill('Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB')    # первое поле для токена вводится адрес usdt
            await page.locator('//*[@id="__next"]/div[3]/div[1]/div/div/div[4]/div/div/div/li/div[2]/div[2]/div[1]').click()                   # клик по usdt
            token_2 = page.locator('//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div[1]/div[3]/div[2]/div/button/div[2]')  # второе поле для токена
            await token_2.click()
            await page.locator('//*[@id="__next"]/div[3]/div[1]/div/div/div[1]/input').fill('So11111111111111111111111111111111111111112')     # во второе поле для токена вводится адрес sol
            await page.locator('//*[@id="__next"]/div[3]/div[1]/div/div/div[4]/div/div/div/li/div[2]/div[2]/div[1]').click()                   # клик по sol

            ballance_sol_1 = page.locator('//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div[1]/div[3]/div[1]/div/div[2]/span[1]')  # Парсим баланс sol
            ballance_sol_2 = await ballance_sol_1.inner_text()
            ballance_sol = (float(ballance_sol_2.replace(',','.')))

            ballance_usdt_1 = page.locator(
                '//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div[1]/div[1]/div[1]/div/div[1]/div[2]/span[1]')                     # Парсим баланс usdt
            ballance_usdt_2 = await ballance_usdt_1.inner_text()
            ballance_usdt = (float(ballance_usdt_2.replace(',', '.')))

            print(ballance_sol)
            print(ballance_usdt)

            # Если соланы меньше 0.09 и usdt > 2, то докупаем sol на 2$

            if ballance_sol < 0.09 and ballance_usdt > 2:
                await page.locator('//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div[1]/div[1]/div[2]/span/div/input').fill('2')
                but_swp = page.locator('//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div[4]/button')
                await expect(but_swp).to_be_visible()
                await but_swp.click()
                await asyncio.sleep(3)
                pages = page.context.pages
                solflare_popup = None
                for p in pages:
                    if 'confirm_popup.html' in p.url and p.url != page.url:
                        solflare_popup = p
                        break
                if solflare_popup:
                    await solflare_popup.bring_to_front()
                    await asyncio.sleep(3)
                    tranz_yes = solflare_popup.locator('//html/body/div[2]/div[2]/div/div[2]/div/div[2]/div[2]/div[2]/button[2]')
                    await tranz_yes.click()
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

            ballance_jlp_1 = page.locator(
                '//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div[1]/div[3]/div[1]/div/div[2]/span[1]')
            ballance_jlp_2 = await ballance_jlp_1.inner_text()
            ballance_jlp = (float(ballance_jlp_2.replace(',', '.')))

            ballance_usdt_1 = page.locator(
                '//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div[1]/div[1]/div[1]/div/div[1]/div[2]/span[1]')
            ballance_usdt_2 = await ballance_usdt_1.inner_text()
            ballance_usdt = (float(ballance_usdt_2.replace(',', '.')))

            print(ballance_jlp)

            # Если jlp меньше 5 и usdt > 2, то докупаем jlp на 2$

            if ballance_jlp < 5 and ballance_usdt > 2:
                await page.locator(
                    '//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div[1]/div[1]/div[2]/span/div/input').fill(
                    '2')
                butn_swp = page.locator('//*[@id="__next"]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]/form/div[4]/button')
                await expect(butn_swp).to_be_visible()
                await butn_swp.click()
                await asyncio.sleep(3)
                pages = page.context.pages
                solflare_popup = None
                for p in pages:
                    if 'confirm_popup.html' in p.url and p.url != page.url:
                        solflare_popup = p
                        break
                if solflare_popup:
                    await solflare_popup.bring_to_front()
                    await asyncio.sleep(3)
                    tranz_yes = solflare_popup.locator(
                        '//html/body/div[2]/div[2]/div/div[2]/div/div[2]/div[2]/div[2]/button[2]')  # Кнопка подтверждения транзы
                    await tranz_yes.click()
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
            butnconect = page.locator('//button[contains(@class, "bg-[#191C32]")]')
            await butnconect.click()
            await asyncio.sleep(5)
            walletconect = page.locator('//span[@class ="css-1wq1rs1" and text()="Solflare"]')
            await walletconect.click()
            await asyncio.sleep(5)


            # Ждем всплывающее окно Solflare и подтверждаем подключение

            await asyncio.sleep(2)
            pages = page.context.pages
            solflare_popup = None
            for p in pages:
                if 'confirm_popup.html' in p.url and p.url != page.url:
                    solflare_popup = p
                    break
            if solflare_popup:
                await solflare_popup.bring_to_front()
                await solflare_popup.locator('//html/body/div[2]/div[2]/div/div[3]/div/button[2]').click()
                await solflare_popup.close()
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
        my_pool = page3.locator('//*[@id="__next"]/div[1]/div[5]/div/div[2]/div[2]/div/div[4]/div/div[1]/div/div/div[3]/div[2]/div/a[1]')   # Первый пул
        await my_pool.click()
        add_pos = page3.locator('//*[@id="__next"]/div[1]/div[5]/div/div[2]/div/div[2]/div[2]/div[1]/div[1]/div[2]/span')                   # Кнопка создать позицию
        await add_pos.click()
        auto_fill = page3.locator('//*[@id="__next"]/div[1]/div[5]/div/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[1]/div/div/button')
        await auto_fill.click()
        jlp_lykv = page3.locator('//*[@id="__next"]/div[1]/div[5]/div/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[1]/div[1]/input')
        await jlp_lykv.click()
        max_btn = page3.locator('//*[@id="__next"]/div[1]/div[5]/div/div[2]/div/div[2]/div[2]/div[2]/form/div[1]/div[2]/div[1]/div[2]/div[2]/div[2]')
        await max_btn.click()

        await asyncio.sleep(5555555)
        await context.close()
        print('ОК!!!')

if __name__ == '__main__':
    asyncio.run(main())


