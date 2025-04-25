import asyncio
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Playwright

async def export_csv(page, csv_folder='csv'):
    download_path = Path(csv_folder)
    download_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Navegar para "Agendamentos de Consultas"
        await page.locator("#popoverId").click()
        await page.get_by_role("img", name="Agendamento").click()
        await page.get_by_text("Agendamentos de Consultas").click()
        print("Navegou para Agendamentos de Consultas")

        # Filtrar por "Data e Horário de Inclusão"
        await page.locator("#O2C2_id-trigger-picker").click()
        await page.get_by_role("option", name="Data e Horário de Inclusão").click()
        print("Selecionou filtro por Data e Horário de Inclusão")

        # Preencher os campos de data com a data atual
        today = datetime.now().strftime('%d/%m/%Y')  # Formato DD/MM/YYYY (ex.: 25/04/2025)
        await page.locator("#O2C8_id-inputEl").click()  # Campo Inicial
        await page.locator("#O2C8_id-inputEl").fill(today)
        print(f"Preencheu campo Inicial com {today}")
        
        await page.locator("#O2CC_id-inputEl").click()  # Campo Final
        await page.locator("#O2CC_id-inputEl").fill(today)
        print(f"Preencheu campo Final com {today}")

        # Clicar em "Incluir"
        await page.get_by_role("button", name=" Incluir").click()
        await page.get_by_role("button", name="Sim").click()
        print("Clicou em Incluir")

        # Exportar o CSV
        await page.get_by_role("button", name=" Exportar").click()
        await page.get_by_label("CSV").check()
        await page.get_by_label("Esconder cabeçalho/rodapé").check()
        async with page.expect_download() as download_info:
            await page.get_by_title("Exporta o relatório para o").click()
        download = await download_info.value
        print("Download iniciado")

        # Gerar nome do arquivo com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        suggested_filename = f"Agendamento de Consulta.csv"
        download_path_full = download_path / suggested_filename

        # Salvar o arquivo
        await download.save_as(download_path_full)
        print(f"CSV salvo em {download_path_full}")

        # Aguardar a página carregar
        await page.wait_for_load_state('load')

    except Exception as e:
        print(f"Erro ao exportar CSV: {e}")

async def run(playwright: Playwright):
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(accept_downloads=True)
    page = await context.new_page()

    try:
        # Fazer login
        await page.goto("https://bebedouro-saude.ids.inf.br/bebedouro/")
        await page.get_by_placeholder("Informe seu operador ou C.P.F.").fill("painel.esf")
        await page.get_by_placeholder("Informe sua senha").fill("painel@123")
        await page.get_by_role("button", name="Acessar").click()
        await page.get_by_role("button", name=" Confirmar").click()
        print("Login realizado com sucesso")
        await page.wait_for_load_state('load')

        while True:
            # Exportar o CSV
            await export_csv(page)
            
            # Obter data e hora atual
            now = datetime.now()
            formatted_time = now.strftime('%Y-%m-%d %H:%M:%S')
            print(f"Exportação realizada com sucesso em {formatted_time}")

            # Aguardar 12 horas antes da próxima execução
            await asyncio.sleep(12 * 60 * 60)

    except Exception as e:
        print(f"Erro no processo principal: {e}")
    finally:
        await context.close()
        await browser.close()

async def main():
    async with async_playwright() as playwright:
        await run(playwright)

if __name__ == '__main__':
    asyncio.run(main())